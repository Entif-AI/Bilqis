"""Versioned trainer observation contract extensions."""
from dataclasses import dataclass
import math

from ..model import is_name, is_wire_integer, require
from .base import TrainerObservationV2
from .steps import CandidateStepPerformance, CandidateStepPerformanceV2
from ..trainer_evidence import (
    GeneratedGradeEvidence, LearningHealthEvidence, RetentionStageTiming, VisitEvidence,
)


@dataclass(frozen=True)
class TrainerObservationV3(TrainerObservationV2):
    SCHEMA = 'bilqis.bamf.mission-control.trainer-observation/v3'
    candidate_steps: tuple[CandidateStepPerformance, ...]

    def __post_init__(self):
        super().__post_init__()
        require(len(self.candidate_steps) <= 64, 'OBSERVATION_STEP_HISTORY_LIMIT')
        ordinals = tuple(item.candidate_step for item in self.candidate_steps)
        require(ordinals == tuple(sorted(set(ordinals))),
                'OBSERVATION_STEP_HISTORY_ORDER')

@dataclass(frozen=True)
class TrainerObservationV4(TrainerObservationV3):
    SCHEMA = 'bilqis.bamf.mission-control.trainer-observation/v4'
    planning_wall_seconds: float | None
    source_materialization_wall_seconds: float | None
    target_evaluation_wall_seconds: float | None
    protected_retention_wall_seconds: float | None
    broad_certification_wall_seconds: float | None
    visit_evidence: VisitEvidence | None
    generated_grade_evidence: GeneratedGradeEvidence | None
    retention_stage_timings: tuple[RetentionStageTiming, ...]

    def __post_init__(self):
        super().__post_init__()
        for value in (self.planning_wall_seconds, self.source_materialization_wall_seconds,
                      self.target_evaluation_wall_seconds,
                      self.protected_retention_wall_seconds,
                      self.broad_certification_wall_seconds):
            require(value is None or (type(value) in (int, float)
                    and math.isfinite(value) and value >= 0),
                    'OBSERVATION_VISIT_SECONDS')
        require(self.visit_evidence is None or type(self.visit_evidence) is VisitEvidence,
                'OBSERVATION_VISIT_EVIDENCE')
        require(self.generated_grade_evidence is None
                or type(self.generated_grade_evidence) is GeneratedGradeEvidence,
                'OBSERVATION_GRADE_EVIDENCE')
        require(all(type(item) is RetentionStageTiming
                    for item in self.retention_stage_timings),
                'OBSERVATION_RETENTION_TIMINGS')
        require(len(self.retention_stage_timings) <= 256,
                'OBSERVATION_RETENTION_TIMINGS_LIMIT')


@dataclass(frozen=True)
class TrainerObservationV5(TrainerObservationV4):
    SCHEMA = 'bilqis.bamf.mission-control.trainer-observation/v5'
    learning_health: LearningHealthEvidence | None

    def __post_init__(self):
        super().__post_init__()
        require(self.learning_health is None
                or type(self.learning_health) is LearningHealthEvidence,
                'OBSERVATION_LEARNING_HEALTH')

@dataclass(frozen=True)
class TrainerObservationV6(TrainerObservationV5):
    """Lossless public projection of trainer-observed/v6 diagnostics."""
    SCHEMA = 'bilqis.bamf.mission-control.trainer-observation/v6'
    accepted_currentness_refresh_wall_seconds: float | None
    accepted_currentness_live_fence_wall_seconds: float | None
    accepted_parent_currentness_wall_seconds: float | None
    lawful_frontier_currentness_wall_seconds: float | None
    teacher_visit_currentness_wall_seconds: float | None
    source_currentness_wall_seconds: float | None
    candidate_binding_wall_seconds: float | None
    retention_target_prepare_wall_seconds: float | None
    retention_target_solver_wall_seconds: float | None
    retention_target_parent_wall_seconds: float | None
    retention_target_candidate_wall_seconds: float | None
    retention_protected_prepare_wall_seconds: float | None
    retention_protected_parent_solver_wall_seconds: float | None
    retention_protected_parent_wall_seconds: float | None
    retention_protected_candidate_solver_wall_seconds: float | None
    retention_protected_candidate_wall_seconds: float | None
    retention_decision_finalize_wall_seconds: float | None
    championship_wall_seconds: float | None
    championship_prepare_wall_seconds: float | None
    championship_solver_wall_seconds: float | None
    championship_candidate_wall_seconds: float | None
    adviser_wall_seconds: float | None
    retention_target_case_count: int | None
    retention_protected_case_count: int | None
    retention_parent_cache_reused: bool | None
    retention_target_shared_backbone_launches: int | None
    retention_target_scalar_neural_launches: int | None
    retention_protected_shared_backbone_launches: int | None
    retention_protected_scalar_neural_launches: int | None
    championship_case_count: int | None
    championship_shared_backbone_launches: int | None
    championship_scalar_neural_launches: int | None
    candidate_steps: tuple[CandidateStepPerformanceV2, ...]

    def __post_init__(self):
        super().__post_init__()
        seconds = (
            self.accepted_currentness_refresh_wall_seconds,
            self.accepted_currentness_live_fence_wall_seconds,
            self.accepted_parent_currentness_wall_seconds,
            self.lawful_frontier_currentness_wall_seconds,
            self.teacher_visit_currentness_wall_seconds,
            self.source_currentness_wall_seconds,
            self.candidate_binding_wall_seconds,
            self.retention_target_prepare_wall_seconds,
            self.retention_target_solver_wall_seconds,
            self.retention_target_parent_wall_seconds,
            self.retention_target_candidate_wall_seconds,
            self.retention_protected_prepare_wall_seconds,
            self.retention_protected_parent_solver_wall_seconds,
            self.retention_protected_parent_wall_seconds,
            self.retention_protected_candidate_solver_wall_seconds,
            self.retention_protected_candidate_wall_seconds,
            self.retention_decision_finalize_wall_seconds,
            self.championship_wall_seconds,
            self.championship_prepare_wall_seconds,
            self.championship_solver_wall_seconds,
            self.championship_candidate_wall_seconds,
            self.adviser_wall_seconds,
        )
        require(all(value is None or (
            type(value) in (int, float) and math.isfinite(value) and value >= 0)
            for value in seconds), 'OBSERVATION_V6_SECONDS')
        counts = (
            self.retention_target_case_count,
            self.retention_protected_case_count,
            self.retention_target_shared_backbone_launches,
            self.retention_target_scalar_neural_launches,
            self.retention_protected_shared_backbone_launches,
            self.retention_protected_scalar_neural_launches,
            self.championship_case_count,
            self.championship_shared_backbone_launches,
            self.championship_scalar_neural_launches,
        )
        require(all(value is None or (
            is_wire_integer(value) and value >= 0) for value in counts),
            'OBSERVATION_V6_COUNT')
        require(self.retention_parent_cache_reused is None
                or type(self.retention_parent_cache_reused) is bool,
                'OBSERVATION_V6_CACHE_REUSE')
        require(all(type(item) is CandidateStepPerformanceV2
                    for item in self.candidate_steps),
                'OBSERVATION_V6_STEP_TYPE')


@dataclass(frozen=True)
class TrainerObservationV7(TrainerObservationV6):
    """Current operator activity projected from bounded trainer progress."""
    SCHEMA = 'bilqis.bamf.mission-control.trainer-observation/v7'
    activity: str | None
    activity_elapsed_ms: int | None

    def __post_init__(self):
        super().__post_init__()
        require(self.activity is None or is_name(self.activity),
                'OBSERVATION_ACTIVITY')
        require(self.activity_elapsed_ms is None or (
            is_wire_integer(self.activity_elapsed_ms)
            and self.activity_elapsed_ms >= 0),
            'OBSERVATION_ACTIVITY_ELAPSED')
