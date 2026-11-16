"""Assessment, learning-evidence, and admission contracts for Factory releases."""
from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

from .model_contracts import AssessmentClass, _sha256

if TYPE_CHECKING:
    from .model_release import FactoryRelease


@dataclass(frozen=True)
class AssessmentPlan:
    grade_id: str
    assessment_class: AssessmentClass
    lifecycle: str
    fresh_on_decision: bool
    reusable_after_failure: bool
    burn_after_failure: bool


def assessment_plans(grade_ids) -> tuple[AssessmentPlan, ...]:
    from ..generated_assessment import (
        GENERALIZATION_LIFECYCLE, PROMOTION_ATTEMPT_LIFECYCLE,
        ROUTINE_EVAL_LIFECYCLE,
    )
    return tuple(
        AssessmentPlan(grade, kind, lifecycle, fresh, reusable, burn)
        for grade in grade_ids
        for kind, lifecycle, fresh, reusable, burn in (
            (AssessmentClass.ROUTINE, ROUTINE_EVAL_LIFECYCLE, True, False, False),
            (AssessmentClass.PROMOTION, PROMOTION_ATTEMPT_LIFECYCLE, False, True, False),
            (AssessmentClass.GENERALIZATION, GENERALIZATION_LIFECYCLE, True, False, True)))


@dataclass(frozen=True)
class LearningEvidence:
    assessment_class: AssessmentClass
    cohort_sha256: str
    checkpoint_sha256: str
    optimizer_step: int
    passed: bool
    contaminated_for_qualification: bool = False

    def __post_init__(self):
        if not isinstance(self.assessment_class, AssessmentClass):
            raise ValueError("FACTORY_LEARNING_EVIDENCE_CLASS_INVALID")
        _sha256(self.cohort_sha256, "FACTORY_LEARNING_EVIDENCE_COHORT_INVALID")
        _sha256(self.checkpoint_sha256, "FACTORY_LEARNING_EVIDENCE_STUDENT_INVALID")
        if (type(self.optimizer_step) is not int or self.optimizer_step < 0 or
                type(self.passed) is not bool or
                type(self.contaminated_for_qualification) is not bool):
            raise ValueError("FACTORY_LEARNING_EVIDENCE_VALUE_INVALID")


@dataclass(frozen=True)
class AdmissionReceipt:
    factory_release_sha256: str
    course_sha256: str
    student_sha256: str
    optimizer_step: int
    semantic_graph_sha256: str

    def verify(self, release: FactoryRelease) -> None:
        release.verify()
        if (self.factory_release_sha256 != release.release_sha256 or
                self.course_sha256 != release.course.digest()):
            raise ValueError("FACTORY_ADMISSION_RELEASE_MISMATCH")
        _sha256(self.student_sha256, "FACTORY_ADMISSION_STUDENT_DIGEST_INVALID")
        _sha256(self.semantic_graph_sha256, "FACTORY_ADMISSION_GRAPH_DIGEST_INVALID")
        if type(self.optimizer_step) is not int or self.optimizer_step < 0:
            raise ValueError("FACTORY_ADMISSION_OPTIMIZER_STEP_INVALID")


__all__ = (
    "AdmissionReceipt",
    "AssessmentPlan",
    "LearningEvidence",
    "assessment_plans",
)
