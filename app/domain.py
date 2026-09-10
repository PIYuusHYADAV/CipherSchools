
from dataclasses import dataclass, field
from typing import Optional
from abc import ABC, abstractmethod


@dataclass
class ClassSpec:
    """One class/interface the learner defined in their design."""
    name: str
    kind: str = "class"       
    fields: list[str] = field(default_factory=list)
    methods: list[str] = field(default_factory=list)


@dataclass
class RelationshipSpec:
    """A relationship the learner declared between two classes."""
    source: str
    target: str
    kind: str = "association"  # association | inheritance | composition | implements


@dataclass
class ProblemSpec:
    """The evaluation-relevant parts of a Problem (mirrors the ORM row)."""
    slug: str
    title: str
    requirements: list[str]
    expected_entities: list[str]
    hints_for_variation: list[str] = field(default_factory=list)


@dataclass
class DesignSubmission:
    """What a learner hands in for one submission."""
    classes: list[ClassSpec]
    relationships: list[RelationshipSpec]
    code: str = ""


@dataclass
class ChecklistItem:
    label: str
    passed: bool
    detail: str


@dataclass
class EvaluationResult:
    score: int                       # 0-100, simple and explainable
    checklist: list[ChecklistItem]
    narrative_feedback: str
    evaluator_name: str


class Evaluator(ABC):
    """
    The one interface every evaluation approach must implement.
    New evaluation strategies (a static-analysis tool, a different LLM
    provider, a rubric-based grader) just implement this and get wired
    into CompositeEvaluator — nothing else in the app needs to change.
    """

    @abstractmethod
    def evaluate(self, problem: ProblemSpec, submission: DesignSubmission) -> EvaluationResult:
        raise NotImplementedError
