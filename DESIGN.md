# Design Note

## MVP scope

One learner, one practice loop, three problems (Parking Lot, Vending Machine, Elevator),
no login/auth (a single hardcoded demo learner). The point of the two days is the domain
design and evaluation approach, not account management or a diagram canvas.

## User flow

```
Home (problem list)
  -> Problem detail (requirements + past attempts)
      -> Start attempt -> Attempt workspace
                              - add classes/interfaces (name, fields, methods)
                              - add relationships (source, target, kind)
                              - optional free-text code/pseudo-code
                              -> Submit
                                  -> Submission result page
                                       - status (pending/evaluating/completed/failed)
                                       - checklist (deterministic, explainable)
                                       - narrative feedback (qualitative)
                                       -> Retry (if failed) or Try again (new attempt)
      -> History -> list of past attempts + their submissions/scores
```

## Core classes / interfaces

Domain objects (`app/domain.py`) are kept independent of the DB and the web framework on
purpose — this is the part of the assignment that's actually being graded, so it should be
testable with zero HTTP/DB involved.

- **`ClassSpec`** — one class/interface the learner defined: name, kind (class/interface),
  fields, methods.
- **`RelationshipSpec`** — a declared relationship between two classes (association,
  composition, inheritance, implements).
- **`ProblemSpec`** — the evaluation-relevant shape of a problem: requirements, the
  entities it expects to see, and hints about which behavior is expected to vary by type
  (used to check for abstraction/interface usage).
- **`DesignSubmission`** — what the learner handed in: classes + relationships + free-text
  code.
- **`EvaluationResult`** — score, checklist (list of `ChecklistItem`), narrative feedback,
  and which evaluator produced it.
- **`Evaluator` (abstract)** — the single interface every evaluation approach implements:
  `evaluate(problem, submission) -> EvaluationResult`.

Persistence (`app/models/orm.py`) mirrors these with SQLAlchemy models:
`Problem`, `Attempt` (a learner's in-progress or submitted draft), `Submission` (an
immutable snapshot of a design at submit time, with its own status and result).

Splitting `Attempt` from `Submission` was a deliberate LLD choice: an attempt is a mutable
workspace the learner keeps coming back to; a submission is a point-in-time snapshot that
should never change after evaluation, so that re-opening old feedback later is trustworthy
and stable even if the learner keeps editing the attempt.

## Evaluation approach

This is the main design bet of the assignment, so it gets its own explanation.

**Split into two evaluators, merged by a third:**

1. **`DeterministicEvaluator`** — no AI, fully explainable, same input always gives the
   same output. Checks:
   - Submission isn't empty
   - The problem's expected entities are represented (by class name or in free-text code)
   - If the problem has behavior that varies by type, an interface/abstraction signal is
     present (structured `interface` kind, or a keyword like "interface"/"abstract"/
     "strategy" in the free-text code)
   - No single class is overloaded (a simple field+method count threshold, not a real
     static analyzer — see limitations)
   - If more than one class is declared, at least one relationship connects them

2. **`MockLLMEvaluator`** — reads the *same* deterministic findings plus the actual class
   names, and produces narrative feedback: what's working, where to focus, one alternative
   design angle relevant to that specific problem, and one open trade-off question. It's
   rule-based, but it genuinely reads the submission — two different submissions get
   different feedback, which is unit tested (`test_narrative_differs_between_good_and_bad_submissions`).
   This exists so the whole app runs offline/demo-safe with zero API key required.

3. **`RealLLMEvaluator`** — same interface, but sends the problem + submission to Google
   Gemini for narrative feedback instead of generating it with rules. Behind a flag
   (`USE_REAL_LLM=1` + `GEMINI_API_KEY`) so the default experience never depends on
   network access or a paid key.

4. **`CompositeEvaluator`** — the only evaluator the rest of the app talks to. Takes the
   score + checklist from the deterministic evaluator and the narrative from whichever
   narrative evaluator is configured (mock or real), and returns one `EvaluationResult`.

**Why this split, specifically:**
- *What should be deterministic:* facts about the submission that have a right answer —
  did they model the entities the problem needs, is there an obvious god-class, is there
  an abstraction where the problem varies by type. These don't need a model call, are
  instant, free, and testable exactly like any other function.
- *What benefits from an LLM:* everything that has more than one reasonable answer —
  which alternative design would also work, what trade-off is worth thinking about, how
  to phrase feedback so it's specific rather than generic. This is exactly where "there's
  no single right LLD answer" lives, so a rules engine alone would either be too rigid
  (penalizing valid alternative designs) or too shallow (a fixed checklist can't discuss
  trade-offs).

**Extensibility - adding a new evaluation approach or submission format:**
- New evaluation approach (e.g. a static-analysis tool, a different LLM provider, a
  rubric grader) → implement `Evaluator`, wire it into `CompositeEvaluator`. Nothing in
  `main.py`, the templates, or the DB models changes.
- New submission format (e.g. an actual diagram/canvas, or a full code file upload) →
  `DesignSubmission` and `ClassSpec`/`RelationshipSpec` are the seam. A new input format
  just needs to produce these same objects before handing them to an `Evaluator` — the
  evaluator layer doesn't know or care whether the classes came from a form, a parsed
  code file, or an uploaded diagram's node list.

## What happens if evaluation takes time or fails

Kept intentionally simple, per the assignment's own guidance not to turn this into a
distributed-systems exercise:

- **Status is a real, persisted state machine**: `pending -> evaluating -> completed |
  failed`. The learner always sees which state a submission is in.
- **Evaluation currently runs synchronously** inside the submit request, because the mock
  evaluator is effectively instant and a real LLM call is a few seconds — acceptable for a
  practice tool where the learner is already sitting there waiting for feedback, and far
  simpler than standing up a queue/worker for a 2-day prototype.
- **If evaluation throws for any reason** (a bad LLM response, a malformed submission, a
  network error against the real API) — the exception is caught, the submission is marked
  `failed` with a human-readable `error_message`, and the learner gets a **Retry** button
  that re-runs evaluation without losing their submitted design. This is unit tested
  (`test_evaluation_failure_is_recoverable_via_retry`) — a real bug (constructing domain
  objects outside the try/except) was actually caught by this exact test path during
  development, see AI_USAGE.md.
- **If evaluation were to become slow** (e.g. always using a real LLM, or a heavier static
  analysis pass), the natural next step — without changing the domain model — is to return
  `pending` immediately from the submit endpoint and run `_run_evaluation` in a background
  task (FastAPI's `BackgroundTasks`, or a simple job table polled by a worker later). The
  state machine already supports this; only the "when do we flip to evaluating" wiring
  would move.

## Key trade-offs

- **Structured form + free text, not a diagram canvas** — faster to build, still gives the
  deterministic evaluator real structure, and a learner who thinks in code can just paste
  code instead of filling in the form. Trade-off: no visual UML rendering.
- **Rule-based mock LLM by default** — the whole assignment can be reviewed and run without
  an API key or network access, and the narrative logic is unit-testable and deterministic
  for grading purposes. Trade-off: the "AI" feedback is templated rather than fully
  generative unless `USE_REAL_LLM=1` is set.
- **Synchronous evaluation** — simpler code, no worker/queue, good enough for the target
  latency. Trade-off: a slower real LLM call blocks the submit request; acceptable for an
  MVP, called out above as the seam to change first if that stops being true.
- **God-class check is a field/method count threshold**, not real static analysis of
  cohesion. It's an intentionally simple, explainable heuristic rather than a made-up
  "AI-detects-bad-code" claim — see README for limitations.
