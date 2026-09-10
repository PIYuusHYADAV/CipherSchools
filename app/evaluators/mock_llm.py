"""
A stand-in for an LLM call, used by default so the app runs offline and the
demo never depends on an API key or network access. It genuinely reads the
submission (class names, missing entities, structure) rather than returning
canned text, so the feedback still changes based on what was submitted.

Swap this for RealLLMEvaluator (see llm.py) by setting USE_REAL_LLM=1 and an
API key — both implement the same Evaluator interface, so nothing else in
the app changes.
"""
from app.domain import Evaluator, ProblemSpec, DesignSubmission, EvaluationResult, ChecklistItem
from app.evaluators.deterministic import DeterministicEvaluator


class MockLLMEvaluator(Evaluator):
    name = "mock-llm"

    def __init__(self):
        # reuse the deterministic checks as "facts" to reason over, instead
        # of re-deriving them - this is the kind of thing a real LLM prompt
        # would also be handed as context.
        self._facts_evaluator = DeterministicEvaluator()

    def evaluate(self, problem: ProblemSpec, submission: DesignSubmission) -> EvaluationResult:
        facts = self._facts_evaluator.evaluate(problem, submission)
        narrative = self._build_narrative(problem, submission, facts.checklist)
        return EvaluationResult(
            score=facts.score,  # narrative evaluator doesn't re-score; it explains
            checklist=[],       # checklist already shown from the deterministic pass
            narrative_feedback=narrative,
            evaluator_name=self.name,
        )

    def _build_narrative(self, problem: ProblemSpec, submission: DesignSubmission,
                          checklist: list[ChecklistItem]) -> str:
        class_names = [c.name for c in submission.classes]
        lines = []

        # Opening: acknowledge what they actually built
        if class_names:
            lines.append(
                f"You modeled this with {len(class_names)} class(es): {', '.join(class_names)}."
            )
        else:
            lines.append("No structured classes were declared — feedback below is based on the free-text code.")

        # Strengths: cite passed checks
        passed = [c for c in checklist if c.passed]
        if passed:
            lines.append("What's working: " + " ".join(f"{c.detail}" for c in passed[:2]))

        # Gaps: cite failed checks
        failed = [c for c in checklist if not c.passed]
        if failed:
            lines.append("Where to focus next:")
            for c in failed:
                lines.append(f"- {c.detail}")

        # One alternative design angle, tailored per problem via hints
        if problem.hints_for_variation:
            varying = problem.hints_for_variation[0]
            lines.append(
                f"One thing worth thinking through: {varying}. If you handled this with conditionals, "
                "consider whether a Strategy/Interface-based approach would make adding a new case "
                "a matter of adding a class, not editing existing ones."
            )

        # A trade-off question - the kind of thing that has no single right answer
        lines.append(
            "Trade-off to consider: how would your design change if this needed to support "
            "concurrent access from multiple users at once? You don't need to redesign for it now, "
            "but it's worth knowing which of your classes would need to change."
        )

        return "\n".join(lines)
