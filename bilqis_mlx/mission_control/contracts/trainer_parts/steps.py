"""Completed-step trainer observation contracts."""
from dataclasses import dataclass
import math

from ..model import is_wire_integer, require


@dataclass(frozen=True)
class CandidateStepPerformance:
    candidate_step: int
    candidate_optimizer_step: int
    candidate_step_wall_seconds: float
    pre_neural_source_compile_wall_seconds: float | None
    currentness_binding_wall_seconds: float | None
    b11_preflight_wall_seconds: float | None
    b11_autodiff_wall_seconds: float | None
    optimizer_admission_wall_seconds: float | None
    motif_staging_wall_seconds: float | None
    evidence_capture_wall_seconds: float | None
    candidate_terminal_step: bool | None
    c08_gradient_launches: int | None
    c08_vectorized_microbatches: int | None
    c08_materialization_barriers: int | None
    c08_scalar_fallback_rows: int | None
    c08_logical_batch_wall_seconds: float | None
    c08_rows_per_gradient_launch: float | None
    b11_provider_draw_count: int | None
    b11_atlas_reload_count: int | None
    logical_rows: int | None
    compiled_positions: int | None

    def __post_init__(self):
        require(is_wire_integer(self.candidate_step) and self.candidate_step > 0,
                'OBSERVATION_STEP_COORDINATE')
        require(is_wire_integer(self.candidate_optimizer_step)
                and self.candidate_optimizer_step >= 0,
                'OBSERVATION_STEP_COORDINATE')
        seconds = (
            self.candidate_step_wall_seconds,
            self.pre_neural_source_compile_wall_seconds,
            self.currentness_binding_wall_seconds,
            self.b11_preflight_wall_seconds,
            self.b11_autodiff_wall_seconds,
            self.optimizer_admission_wall_seconds,
            self.motif_staging_wall_seconds,
            self.evidence_capture_wall_seconds,
            self.c08_logical_batch_wall_seconds,
        )
        require(all(value is None or (
            type(value) in (int, float) and math.isfinite(value) and value >= 0)
            for value in seconds), 'OBSERVATION_STEP_SECONDS')
        require(self.c08_rows_per_gradient_launch is None or (
            type(self.c08_rows_per_gradient_launch) in (int, float)
            and math.isfinite(self.c08_rows_per_gradient_launch)
            and self.c08_rows_per_gradient_launch >= 0),
            'OBSERVATION_STEP_ROWS_PER_LAUNCH')
        counts = (
            self.c08_gradient_launches,
            self.c08_vectorized_microbatches,
            self.c08_materialization_barriers,
            self.c08_scalar_fallback_rows,
            self.b11_provider_draw_count,
            self.b11_atlas_reload_count,
            self.logical_rows,
            self.compiled_positions,
        )
        require(all(value is None or (
            is_wire_integer(value) and value >= 0) for value in counts),
            'OBSERVATION_STEP_COUNT')
        require(self.candidate_terminal_step is None
                or type(self.candidate_terminal_step) is bool,
                'OBSERVATION_STEP_TERMINAL')

@dataclass(frozen=True)
class CandidateStepPerformanceV2(CandidateStepPerformance):
    """Raw-v6 completed-step diagnostics without changing historical wire shapes."""
    accepted_currentness_refresh_wall_seconds: float | None
    accepted_currentness_live_fence_wall_seconds: float | None
    accepted_parent_currentness_wall_seconds: float | None
    lawful_frontier_currentness_wall_seconds: float | None
    teacher_visit_currentness_wall_seconds: float | None
    source_currentness_wall_seconds: float | None
    candidate_binding_wall_seconds: float | None

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
        )
        require(all(value is None or (
            type(value) in (int, float) and math.isfinite(value) and value >= 0)
            for value in seconds), 'OBSERVATION_STEP_CURRENTNESS_SECONDS')
