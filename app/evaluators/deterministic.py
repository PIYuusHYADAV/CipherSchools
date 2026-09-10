"""
Deterministic checks. These don't need an LLM and are 100% explainable -
same input always gives the same output. This is intentionally the first
evaluator to run: it catches objective gaps before we spend an LLM call on
subjective feedback.
"""
from app.domain import Evaluator, ProblemSpec, DesignSubmission, EvaluationResult, ChecklistItem

GOD_CLASS_MEMBER_THRESHOLD = 8  # fields + methods above this -> flag as doing too much


class DeterministicEvaluator(Evaluator):
    name = "deterministic"

    def evaluate(self, problem: ProblemSpec, submission: DesignSubmission) -> EvaluationResult:
        checklist: list[ChecklistItem] = []

        checklist.append(self._check_not_empty(submission))
        checklist.append(self._check_expected_entities(problem, submission))
        if problem.hints_for_variation:
            checklist.append(self._check_abstraction_for_variation(problem, submission))
        checklist.append(self._check_no_god_class(submission))
        checklist.append(self._check_relationships_declared(submission))

        passed_count = sum(1 for c in checklist if c.passed)
        score = round(100 * passed_count / len(checklist)) if checklist else 0

        return EvaluationResult(
            score=score,
            checklist=checklist,
            narrative_feedback="",  # deterministic evaluator doesn't write prose
            evaluator_name=self.name,
        )

    # -- individual checks -------------------------------------------------

    def _check_not_empty(self, submission: DesignSubmission) -> ChecklistItem:
        has_content = bool(submission.classes) or bool(submission.code.strip())
        return ChecklistItem(
            label="Submission has content",
            passed=has_content,
            detail="No classes or code were submitted." if not has_content
                   else "Submission contains a design.",
        )

    def _check_expected_entities(self, problem: ProblemSpec, submission: DesignSubmission) -> ChecklistItem:
        declared_names = {c.name.lower() for c in submission.classes}
        code_lower = submission.code.lower()
        missing = []
        for entity in problem.expected_entities:
            entity_lower = entity.lower()
            if entity_lower not in declared_names and entity_lower not in code_lower:
                missing.append(entity)

        passed = len(missing) == 0
        if passed:
            detail = "All expected entities for this problem are represented."
        else:
            detail = f"Missing or unclear: {', '.join(missing)}."
        return ChecklistItem(label="Expected entities present", passed=passed, detail=detail)

    def _check_abstraction_for_variation(self, problem: ProblemSpec, submission: DesignSubmission) -> ChecklistItem:
        has_interface = any(c.kind == "interface" for c in submission.classes)
        # also accept a loose textual signal in free-text code (e.g. "abstract", "Strategy", "interface")
        code_signal = any(
            kw in submission.code.lower() for kw in ["interface", "abstract", "strategy", "protocol"]
        )
        passed = has_interface or code_signal
        detail = (
            "This problem has behavior that varies by type (" + "; ".join(problem.hints_for_variation) + "), "
            + ("and your design uses an interface/abstraction for it." if passed
               else "but no interface/abstraction was found — consider whether a fixed if/else "
                    "on type will get harder to extend.")
        )
        return ChecklistItem(label="Uses abstraction for varying behavior", passed=passed, detail=detail)

    def _check_no_god_class(self, submission: DesignSubmission) -> ChecklistItem:
        offenders = [
            c.name for c in submission.classes
            if (len(c.fields) + len(c.methods)) > GOD_CLASS_MEMBER_THRESHOLD
        ]
        passed = len(offenders) == 0
        detail = (
            "No single class is overloaded with responsibilities."
            if passed else
            f"{', '.join(offenders)} has a lot of fields/methods — consider splitting responsibilities."
        )
        return ChecklistItem(label="No god classes", passed=passed, detail=detail)

    def _check_relationships_declared(self, submission: DesignSubmission) -> ChecklistItem:
        if len(submission.classes) <= 1:
            return ChecklistItem(
                label="Relationships declared",
                passed=True,
                detail="Only one class defined, so relationships aren't expected yet.",
            )
        passed = len(submission.relationships) > 0
        detail = (
            "Relationships between classes are declared."
            if passed else
            "Multiple classes are defined but no relationships between them were declared — "
            "how do they collaborate?"
        )
        return ChecklistItem(label="Relationships declared", passed=passed, detail=detail)
