import json
from datetime import datetime
from fastapi import FastAPI, Depends, Request, Form, HTTPException
from fastapi.responses import RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session

from app.db import Base, engine, get_db
from app.models.orm import Problem, Attempt, Submission
from app.seed import seed_problems
from app.domain import ProblemSpec, DesignSubmission, ClassSpec, RelationshipSpec
from app.evaluators.composite import CompositeEvaluator

Base.metadata.create_all(bind=engine)

from contextlib import asynccontextmanager


@asynccontextmanager
async def lifespan(app: FastAPI):
    db = next(get_db())
    seed_problems(db)
    yield


app = FastAPI(title="LLD Practice Platform", lifespan=lifespan)
app.mount("/static", StaticFiles(directory="app/static"), name="static")
templates = Jinja2Templates(directory="app/templates")

DEMO_LEARNER = "demo-learner"


# ---------------------------------------------------------------- Problems

@app.get("/")
def home(request: Request, db: Session = Depends(get_db)):
    problems = db.query(Problem).all()
    return templates.TemplateResponse(request, "index.html", {"problems": problems})


@app.get("/problems/{slug}")
def problem_detail(slug: str, request: Request, db: Session = Depends(get_db)):
    problem = db.query(Problem).filter(Problem.slug == slug).first()
    if not problem:
        raise HTTPException(404, "Problem not found")
    past_attempts = (
        db.query(Attempt)
        .filter(Attempt.problem_id == problem.id, Attempt.learner_id == DEMO_LEARNER)
        .order_by(Attempt.created_at.desc())
        .all()
    )
    return templates.TemplateResponse(
        request,
        "problem_detail.html",
        {"problem": problem, "past_attempts": past_attempts},
    )


@app.post("/problems/{slug}/attempts")
def start_attempt(slug: str, db: Session = Depends(get_db)):
    problem = db.query(Problem).filter(Problem.slug == slug).first()
    if not problem:
        raise HTTPException(404, "Problem not found")
    attempt = Attempt(problem_id=problem.id, learner_id=DEMO_LEARNER)
    db.add(attempt)
    db.commit()
    db.refresh(attempt)
    return RedirectResponse(f"/attempts/{attempt.id}", status_code=303)


# ---------------------------------------------------------------- Attempts

@app.get("/attempts/{attempt_id}")
def attempt_workspace(attempt_id: int, request: Request, db: Session = Depends(get_db)):
    attempt = db.query(Attempt).filter(Attempt.id == attempt_id).first()
    if not attempt:
        raise HTTPException(404, "Attempt not found")
    return templates.TemplateResponse(
        request,
        "attempt_workspace.html",
        {
            "attempt": attempt,
            "problem": attempt.problem,
            "classes_json": json.dumps(attempt.draft_classes or []),
            "relationships_json": json.dumps(attempt.draft_relationships or []),
        },
    )


@app.post("/attempts/{attempt_id}/submit")
def submit_attempt(
    attempt_id: int,
    classes_json: str = Form(...),
    relationships_json: str = Form(...),
    code: str = Form(""),
    db: Session = Depends(get_db),
):
    attempt = db.query(Attempt).filter(Attempt.id == attempt_id).first()
    if not attempt:
        raise HTTPException(404, "Attempt not found")

    try:
        classes_raw = json.loads(classes_json or "[]")
        relationships_raw = json.loads(relationships_json or "[]")
    except json.JSONDecodeError:
        raise HTTPException(400, "Malformed design data submitted")

    # Save the draft back onto the attempt too, so re-opening it shows the latest work.
    attempt.draft_classes = classes_raw
    attempt.draft_relationships = relationships_raw
    attempt.draft_code = code
    attempt.status = "submitted"

    submission = Submission(
        attempt_id=attempt.id,
        classes=classes_raw,
        relationships=relationships_raw,
        code=code,
        status="pending",
    )
    db.add(submission)
    db.commit()
    db.refresh(submission)

    _run_evaluation(submission, attempt.problem, db)

    return RedirectResponse(f"/submissions/{submission.id}", status_code=303)


# ---------------------------------------------------------------- Submissions

def _run_evaluation(submission: Submission, problem: Problem, db: Session):
    """
    Runs evaluation and updates the submission's status accordingly.
    Kept synchronous and simple on purpose (see DESIGN.md for why) - the
    important part is that the status transitions are explicit and a failure
    doesn't crash the request or corrupt the submission.
    """
    submission.status = "evaluating"
    db.commit()

    try:
        # Building the domain objects is part of "evaluation" from the
        # learner's point of view too - if their submitted data is malformed
        # (e.g. a hand-crafted request, or a future submission format bug),
        # it should surface as a failed submission they can retry, not a
        # crashed request.
        problem_spec = ProblemSpec(
            slug=problem.slug,
            title=problem.title,
            requirements=problem.requirements,
            expected_entities=problem.expected_entities,
            hints_for_variation=problem.hints_for_variation or [],
        )
        design = DesignSubmission(
            classes=[ClassSpec(**{k: v for k, v in c.items() if k in ("name", "kind", "fields", "methods")})
                     for c in submission.classes],
            relationships=[RelationshipSpec(**{k: v for k, v in r.items() if k in ("source", "target", "kind")})
                           for r in submission.relationships],
            code=submission.code or "",
        )

        evaluator = CompositeEvaluator()
        result = evaluator.evaluate(problem_spec, design)
        submission.score = result.score
        submission.checklist = [c.__dict__ for c in result.checklist]
        submission.narrative_feedback = result.narrative_feedback
        submission.status = "completed"
        submission.error_message = None
    except Exception as e:  # evaluator failure shouldn't crash the request
        submission.status = "failed"
        submission.error_message = str(e)
    db.commit()


@app.get("/submissions/{submission_id}")
def submission_detail(submission_id: int, request: Request, db: Session = Depends(get_db)):
    submission = db.query(Submission).filter(Submission.id == submission_id).first()
    if not submission:
        raise HTTPException(404, "Submission not found")
    return templates.TemplateResponse(
        request,
        "submission_detail.html",
        {"submission": submission, "problem": submission.attempt.problem},
    )


@app.post("/submissions/{submission_id}/retry")
def retry_submission(submission_id: int, db: Session = Depends(get_db)):
    submission = db.query(Submission).filter(Submission.id == submission_id).first()
    if not submission:
        raise HTTPException(404, "Submission not found")
    _run_evaluation(submission, submission.attempt.problem, db)
    return RedirectResponse(f"/submissions/{submission.id}", status_code=303)


# ---------------------------------------------------------------- History

@app.get("/problems/{slug}/history")
def problem_history(slug: str, request: Request, db: Session = Depends(get_db)):
    problem = db.query(Problem).filter(Problem.slug == slug).first()
    if not problem:
        raise HTTPException(404, "Problem not found")
    attempts = (
        db.query(Attempt)
        .filter(Attempt.problem_id == problem.id, Attempt.learner_id == DEMO_LEARNER)
        .order_by(Attempt.created_at.desc())
        .all()
    )
    return templates.TemplateResponse(
        request, "history.html", {"problem": problem, "attempts": attempts}
    )
