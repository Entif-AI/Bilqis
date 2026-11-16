"""Typed, non-authoritative learning health evidence."""
from __future__ import annotations
from dataclasses import dataclass
from .model import is_name, is_wire_integer, require


@dataclass(frozen=True)
class LearningHealthScore:
    correct: int
    total: int

    def __post_init__(self):
        require(is_wire_integer(self.correct) and is_wire_integer(self.total)
                and self.total > 0 and 0 <= self.correct <= self.total,
                'LEARNING_HEALTH_SCORE')


@dataclass(frozen=True)
class LearningHealthWarning:
    signal: str
    status: str
    note: str
    evidence_count: int

    def __post_init__(self):
        from bilqis_mlx.diagnostics.signals import DiagnosticStatus, LearningSignal
        require(self.signal in {item.value for item in LearningSignal},
                'LEARNING_HEALTH_SIGNAL')
        require(self.status in {item.value for item in DiagnosticStatus},
                'LEARNING_HEALTH_STATUS')
        require(isinstance(self.note, str) and len(self.note) <= 256,
                'LEARNING_HEALTH_NOTE')
        require(is_wire_integer(self.evidence_count) and self.evidence_count >= 0,
                'LEARNING_HEALTH_EVIDENCE_COUNT')


@dataclass(frozen=True)
class LearningHealthCheckpoint:
    checkpoint_sha256: str
    optimizer_step: int
    correct: int
    total: int

    def __post_init__(self):
        from .model import is_sha256
        require(is_sha256(self.checkpoint_sha256),
                'LEARNING_HEALTH_CHECKPOINT_ID')
        require(is_wire_integer(self.optimizer_step) and self.optimizer_step >= 0,
                'LEARNING_HEALTH_CHECKPOINT_STEP')
        require(is_wire_integer(self.correct) and is_wire_integer(self.total)
                and self.total > 0 and 0 <= self.correct <= self.total,
                'LEARNING_HEALTH_CHECKPOINT_SCORE')


@dataclass(frozen=True)
class LearningHealthEvidence:
    capability_id: str
    grade_id: str
    grade_definition_id: str | None
    grade_definition_version: str | None
    epoch_sha256: str
    state: str
    history_state: str
    history_error: str | None
    first: LearningHealthScore | None
    latest: LearningHealthScore | None
    best: LearningHealthScore | None
    comparable_points: int
    recent_checkpoints: tuple[LearningHealthCheckpoint, ...]
    gain_from_first: int | None
    regressed_from_first: bool
    distance_to_mastery_state: str
    distance_to_mastery: int | None
    fixed_screen_errors: int | None
    qualification_state: str
    protected_regression_state: str
    regressed_protected_capabilities: tuple[str, ...]
    prior_certified_surface_ids: tuple[str, ...]
    certified_surface_regression_state: str
    warnings: tuple[LearningHealthWarning, ...]

    def __post_init__(self):
        from .model import is_names, is_sha256
        require(is_name(self.capability_id) and is_name(self.grade_id),
                'LEARNING_HEALTH_ID')
        require(all(item is None or is_name(item) for item in (
            self.grade_definition_id, self.grade_definition_version)),
            'LEARNING_HEALTH_GRADE_ID')
        require(is_sha256(self.epoch_sha256),
                'LEARNING_HEALTH_EPOCH')
        require(self.state in {'MEASURED', 'NOT_MEASURED'},
                'LEARNING_HEALTH_STATE')
        require(self.history_state in
                {'VALID', 'PARTIAL', 'INVALID', 'NOT_MEASURED'},
                'LEARNING_HEALTH_HISTORY_STATE')
        require(self.history_error is None or is_name(self.history_error),
                'LEARNING_HEALTH_HISTORY_ERROR')
        require((self.history_state == 'INVALID') == (self.history_error is not None),
                'LEARNING_HEALTH_HISTORY_ERROR_STATE')
        require(all(item is None or type(item) is LearningHealthScore
                    for item in (self.first, self.latest, self.best)),
                'LEARNING_HEALTH_SCORES')
        require(is_wire_integer(self.comparable_points)
                and 0 <= self.comparable_points <= 64, 'LEARNING_HEALTH_POINTS')
        require(len(self.recent_checkpoints) <= 3
                and all(type(item) is LearningHealthCheckpoint
                        for item in self.recent_checkpoints)
                and len({item.checkpoint_sha256 for item in self.recent_checkpoints})
                == len(self.recent_checkpoints), 'LEARNING_HEALTH_HISTORY')
        require(tuple(item.optimizer_step for item in self.recent_checkpoints)
                == tuple(sorted({item.optimizer_step for item in self.recent_checkpoints})),
                'LEARNING_HEALTH_HISTORY_STEP')
        require(self.gain_from_first is None or
                (is_wire_integer(self.gain_from_first) and self.gain_from_first >= 0),
                'LEARNING_HEALTH_GAIN')
        require(type(self.regressed_from_first) is bool,
                'LEARNING_HEALTH_REGRESSED_FROM_FIRST')
        require(self.distance_to_mastery_state in {'MEASURED', 'NOT_MEASURED'},
                'LEARNING_HEALTH_DISTANCE_STATE')
        require((self.distance_to_mastery_state == 'NOT_MEASURED'
                 and self.distance_to_mastery is None)
                or (self.distance_to_mastery_state == 'MEASURED'
                    and is_wire_integer(self.distance_to_mastery)
                    and self.distance_to_mastery >= 0),
                'LEARNING_HEALTH_DISTANCE')
        require(self.fixed_screen_errors is None or
                (is_wire_integer(self.fixed_screen_errors) and
                 self.fixed_screen_errors >= 0), 'LEARNING_HEALTH_FIXED_ERRORS')
        require(self.qualification_state == 'NOT_MEASURED',
                'LEARNING_HEALTH_QUALIFICATION')
        require(self.protected_regression_state in
                {'NOT_MEASURED', 'NOT_OBSERVED', 'OBSERVED_REGRESSION'},
                'LEARNING_HEALTH_PROTECTED_STATE')
        require(is_names(self.regressed_protected_capabilities) and
                is_names(self.prior_certified_surface_ids),
                'LEARNING_HEALTH_PROTECTED')
        require(self.certified_surface_regression_state in
                {'NOT_MEASURED', 'NOT_OBSERVED', 'OBSERVED_REGRESSION'},
                'LEARNING_HEALTH_REGRESSION')
        require(len(self.warnings) == 5 and
                all(type(item) is LearningHealthWarning for item in self.warnings),
                'LEARNING_HEALTH_WARNINGS')
