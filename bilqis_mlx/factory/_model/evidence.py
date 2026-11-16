"""Learner evidence and admission receipts associated with FactoryRelease v1."""
from __future__ import annotations

from dataclasses import dataclass

from .contracts import AssessmentClass, _sha256
from .release import FactoryRelease

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
