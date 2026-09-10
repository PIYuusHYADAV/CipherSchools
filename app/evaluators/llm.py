"""
Real LLM-backed evaluator, using Google's Gemini API. Only used if
GEMINI_API_KEY is set and USE_REAL_LLM=1 - otherwise the app falls back to
MockLLMEvaluator so it always runs in a demo/offline environment. Implements
the same Evaluator interface, so CompositeEvaluator doesn't know or care
which one it's using.
"""
import os
from app.domain import Evaluator, ProblemSpec, DesignSubmission, EvaluationResult


class RealLLMEvaluator(Evaluator):
    name = "gemini"

    def __init__(self, model: str = "gemini-2.5-flash"):
        self.model = model
        self.api_key = os.environ.get("GEMINI_API_KEY")

    def evaluate(self, problem: ProblemSpec, submission: DesignSubmission) -> EvaluationResult:
        if not self.api_key:
            raise RuntimeError("GEMINI_API_KEY not set - cannot use RealLLMEvaluator")

        prompt = self._build_prompt(problem, submission)

        # Plain HTTP call (via requests) so this file has no hard dependency
        # on a Gemini SDK being installed for the default mock-evaluator path.
        import requests

        url = f"https://generativelanguage.googleapis.com/v1beta/models/{self.model}:generateContent"
        response = requests.post(
            url,
            headers={"content-type": "application/json"},
            params={"key": self.api_key},
            json={"contents": [{"parts": [{"text": prompt}]}]},
            timeout=20,
        )
        response.raise_for_status()
        data = response.json()

        try:
            text = data["candidates"][0]["content"]["parts"][0]["text"]
        except (KeyError, IndexError):
            raise RuntimeError(f"Unexpected Gemini response shape: {data}")

        return EvaluationResult(
            score=0,           # the real LLM is used only for narrative feedback here;
            checklist=[],      # scoring stays with the deterministic evaluator (see CompositeEvaluator)
            narrative_feedback=text.strip(),
            evaluator_name=self.name,
        )

    def _build_prompt(self, problem: ProblemSpec, submission: DesignSubmission) -> str:
        classes_desc = "\n".join(
            f"- {c.name} ({c.kind}): fields={c.fields}, methods={c.methods}"
            for c in submission.classes
        ) or "(no structured classes provided)"
        rels_desc = "\n".join(
            f"- {r.source} {r.kind} {r.target}" for r in submission.relationships
        ) or "(none declared)"

        return f"""You are reviewing a Low-Level Design practice submission.

Problem: {problem.title}
Requirements:
{chr(10).join('- ' + r for r in problem.requirements)}

Learner's classes:
{classes_desc}

Learner's declared relationships:
{rels_desc}

Learner's free-text code/notes:
{submission.code or '(none)'}

Give feedback in this shape, briefly:
1. What's good about this design (1-2 sentences, specific to their classes).
2. The most important gap or risk (1-2 sentences).
3. One alternative approach they could have taken, and the trade-off vs theirs.
4. One follow-up question to make them think, not to be answered right away.

Be specific to what they actually submitted. Do not give generic LLD advice."""
