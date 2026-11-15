"""Disposable trainer observations; accepted RunRef is context, never a result."""
from dataclasses import dataclass
import math

from .model import (
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
