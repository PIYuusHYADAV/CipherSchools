"""
Combines the deterministic evaluator (score + checklist) with a narrative
evaluator (mock or real LLM) into one EvaluationResult. This is the only
evaluator the rest of the app talks to - adding a third evaluation approach
later just means adding it here without touching submission/attempt code.
"""
import os
from app.domain import Evaluator, ProblemSpec, DesignSubmission, EvaluationResult
from app.evaluators.deterministic import DeterministicEvaluator
from app.evaluators.mock_llm import MockLLMEvaluator


class CompositeEvaluator(Evaluator):
    name = "composite"

    def __init__(self):
        self.deterministic = DeterministicEvaluator()
        self.narrative = self._pick_narrative_evaluator()

    def _pick_narrative_evaluator(self) -> Evaluator:
        use_real = os.environ.get("USE_REAL_LLM") == "1" and os.environ.get("GEMINI_API_KEY")
        if use_real:
            from app.evaluators.llm import RealLLMEvaluator
            return RealLLMEvaluator()
        return MockLLMEvaluator()

    def evaluate(self, problem: ProblemSpec, submission: DesignSubmission) -> EvaluationResult:
        facts = self.deterministic.evaluate(problem, submission)
        narrative_result = self.narrative.evaluate(problem, submission)

        return EvaluationResult(
            score=facts.score,
            checklist=facts.checklist,
            narrative_feedback=narrative_result.narrative_feedback,
            evaluator_name=f"{self.deterministic.name}+{narrative_result.evaluator_name}",
        )
