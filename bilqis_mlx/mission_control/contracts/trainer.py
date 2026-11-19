"""Disposable trainer observations; accepted RunRef is context, never a result.

The public import surface stays stable while version families live in focused modules.
"""
from .trainer_parts.base import OUTCOMES, PHASES, TrainerObservation, TrainerObservationV2
from .trainer_parts.steps import CandidateStepPerformance, CandidateStepPerformanceV2
from .trainer_parts.versions import (
    TrainerObservationV3, TrainerObservationV4, TrainerObservationV5,
    TrainerObservationV6, TrainerObservationV7,
)
from .trainer_evidence import (
    DeferredGradeCandidate, GeneratedGradeEvidence, GeneratedGradeHold,
    GeneratedGradeMemberEvidence, GradeSynthesisDimension, LearningHealthEvidence,
    RetentionStageTiming, VisitCapabilityScore, VisitEvidence, VisitRankingEvidence,
    VisitRoleCount,
)

__all__ = (
    "PHASES", "OUTCOMES", "TrainerObservation", "TrainerObservationV2",
    "TrainerObservationV3", "TrainerObservationV4", "TrainerObservationV5",
    "TrainerObservationV6", "TrainerObservationV7", "CandidateStepPerformance",
    "CandidateStepPerformanceV2", "DeferredGradeCandidate", "GeneratedGradeEvidence",
    "GeneratedGradeHold", "GeneratedGradeMemberEvidence", "GradeSynthesisDimension",
    "LearningHealthEvidence", "RetentionStageTiming", "VisitCapabilityScore",
    "VisitEvidence", "VisitRankingEvidence", "VisitRoleCount",
)
