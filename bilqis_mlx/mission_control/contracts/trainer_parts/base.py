"""Base disposable trainer observation contracts."""
from dataclasses import dataclass
import math

from ..model import (
    AuthorityClass, CoverageState, RecordMeta, WireRecord, is_name,
    is_wire_integer, require,
)


PHASES = frozenset({'PREPARING', 'SELECTING', 'TRAINING', 'RETENTION',
                    'PUBLISHING', 'COMPLETED'})
OUTCOMES = frozenset({'RUNNING', 'ACCEPTED', 'REJECTED', 'HELD',
                      'ACTION_REQUIRED', 'INTERRUPTED'})


@dataclass(frozen=True)
class TrainerObservation(WireRecord):
    SCHEMA = 'bilqis.bamf.mission-control.trainer-observation/v1'
    meta: RecordMeta
    observation_id: str
    revision: int
    process_id: int
    visit_index: int
    posture: str
    phase: str
    outcome: str
    connection_state: str
    capability_id: str | None
    elapsed_ms: int
    candidate_optimizer_step: int | None
    candidate_step: int | None
    candidate_horizon: int | None
    retention_completed: int | None
    retention_total: int | None
    retention_subject: str | None
    retention_role: str | None
    cpu_seconds: float | None
    peak_rss_bytes: int | None
    disk_free_bytes: int | None
    error_code: str | None
    error_detail: str | None

    def __post_init__(self):
        super().__post_init__()
        require(self.meta.run is not None and self.meta.as_of is None,
                'OBSERVATION_PARENT_CONTEXT')
        require(self.meta.authority is AuthorityClass.MEASURED
                and self.meta.coverage is CoverageState.PARTIAL
                and not self.meta.receipt_refs and not self.meta.evidence_refs,
                'OBSERVATION_AUTHORITY')
        require(is_name(self.observation_id), 'OBSERVATION_ID')
        require(all(is_wire_integer(n) and n > 0 for n in (
            self.revision, self.process_id, self.visit_index)), 'OBSERVATION_COORDINATE')
        require(self.posture == 'OBSERVED' and self.phase in PHASES
                and self.outcome in OUTCOMES, 'OBSERVATION_POSTURE')
        terminal = self.phase == 'COMPLETED'
        require(terminal == (self.outcome != 'RUNNING'), 'OBSERVATION_TERMINAL')
        require(self.connection_state in ({'FINISHED'} if terminal else
                {'LIVE', 'DISCONNECTED'}), 'OBSERVATION_CONNECTION')
        require(self.retention_role in {None, 'parent', 'candidate'}, 'OBSERVATION_ROLE')
        for value in (self.capability_id, self.retention_subject):
            require(value is None or is_name(value), 'OBSERVATION_SUBJECT')
        for value in (self.error_code, self.error_detail):
            require(value is None or is_name(value), 'OBSERVATION_ERROR')
        require(self.error_detail is None or self.error_code is not None,
                'OBSERVATION_ERROR_PAIR')
        require(self.outcome == 'INTERRUPTED' or self.error_code is None,
                'OBSERVATION_ERROR_OUTCOME')
        require(is_wire_integer(self.elapsed_ms) and self.elapsed_ms >= 0,
                'OBSERVATION_ELAPSED')
        for value in (self.candidate_optimizer_step, self.candidate_step,
                      self.candidate_horizon, self.retention_completed,
                      self.retention_total, self.peak_rss_bytes, self.disk_free_bytes):
            require(value is None or (is_wire_integer(value) and value >= 0),
                    'OBSERVATION_NONNEGATIVE')
        for completed, total in ((self.candidate_step, self.candidate_horizon),
                                 (self.retention_completed, self.retention_total)):
            require((completed is None) == (total is None), 'OBSERVATION_PROGRESS_PAIR')
            require(total is None or completed <= total, 'OBSERVATION_PROGRESS_RANGE')
        require(self.cpu_seconds is None or (
            type(self.cpu_seconds) in (int, float) and math.isfinite(self.cpu_seconds)
            and self.cpu_seconds >= 0), 'OBSERVATION_CPU')


@dataclass(frozen=True)
class TrainerObservationV2(TrainerObservation):
    SCHEMA = 'bilqis.bamf.mission-control.trainer-observation/v2'
    candidate_step_wall_seconds: float | None
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
    retention_wall_seconds: float | None
    evidence_finalization_wall_seconds: float | None
    publishing_wall_seconds: float | None

    def __post_init__(self):
        super().__post_init__()
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
            self.retention_wall_seconds,
            self.evidence_finalization_wall_seconds,
            self.publishing_wall_seconds,
        )
        require(all(value is None or (
            type(value) in (int, float) and math.isfinite(value) and value >= 0)
            for value in seconds), 'OBSERVATION_STAGE_SECONDS')
        require(self.c08_rows_per_gradient_launch is None or (
            type(self.c08_rows_per_gradient_launch) in (int, float)
            and math.isfinite(self.c08_rows_per_gradient_launch)
            and self.c08_rows_per_gradient_launch >= 0),
            'OBSERVATION_ROWS_PER_LAUNCH')
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
            'OBSERVATION_STAGE_COUNT')
        require(self.candidate_terminal_step is None
                or type(self.candidate_terminal_step) is bool,
                'OBSERVATION_TERMINAL_STEP')
