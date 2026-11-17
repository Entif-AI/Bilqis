"""Immutable #1333 cadence contracts for one active generated grade."""
from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
import hashlib
import json

from bilqis_mlx.errors import ErrorBus, SCHOOL


CADENCE_SCHEMA = "bilqis.bamf.active-grade-cadence/v1"
CADENCE_POINTER_SCHEMA = "bilqis.bamf.active-grade-cadence-pointer/v1"
CADENCE_AUTHORIZATION_SCHEMA = "bilqis.bamf.active-grade-cadence-authorization/v1"
RECOVERY_WIDTH = 3
MAX_RECOVERY_ROUNDS = 2
_ISSUER = object()


def _invalid(reason: str):
    ErrorBus.Raise(SCHOOL.BAMF_CURRICULUM.INVALID, reason=reason)


def _sha(value) -> bool:
    return (isinstance(value, str) and len(value) == 64
            and all(char in "0123456789abcdef" for char in value))


def _digest(value) -> str:
    raw = json.dumps(
        value, sort_keys=True, separators=(",", ":"),
        ensure_ascii=False, allow_nan=False).encode()
    return hashlib.sha256(raw).hexdigest()


class ActiveGradeCadencePhase(str, Enum):
    MAIN = "MAIN"
    RECOVERY_1 = "RECOVERY_1"
    RECOVERY_2 = "RECOVERY_2"
    BOUNDARY = "BOUNDARY"


class ActiveGradeCadenceDisposition(str, Enum):
    TEACHING = "TEACHING"
    HELD = "HELD"
    GRADE_COMPLETE = "GRADE_COMPLETE"
    RECOVERY_EXHAUSTED = "RECOVERY_EXHAUSTED"


@dataclass(frozen=True, init=False)
class ActiveGradeCadenceState:
    run_id: str
    revision: int
    predecessor_sha256: str | None
    active_grade_activation_sha256: str
    active_grade_definition_sha256: str
    policy_epoch: int
    member_census_sha256: str
    phase: ActiveGradeCadencePhase
    phase_round: int
    phase_sha256: str
    phase_capability_ids: tuple[str, ...]
    attempted_capability_ids: tuple[str, ...]
    deficit_evidence_sha256: str
    recovery_attempt_counts: tuple[tuple[str, int], ...]
    cadence_sha256: str
    schema: str = CADENCE_SCHEMA
    _issuance: object = field(repr=False, compare=False)

    def __init__(self, *args, **kwargs):
        _invalid("BAMF_ACTIVE_GRADE_CADENCE_CALLER_CONSTRUCTION_FORBIDDEN")

    def to_record(self) -> dict:
        return {
            "schema": self.schema,
            "run_id": self.run_id,
            "revision": self.revision,
            "predecessor_sha256": self.predecessor_sha256,
            "active_grade_activation_sha256": self.active_grade_activation_sha256,
            "active_grade_definition_sha256": self.active_grade_definition_sha256,
            "policy_epoch": self.policy_epoch,
            "member_census_sha256": self.member_census_sha256,
            "phase": self.phase.value,
            "phase_round": self.phase_round,
            "phase_sha256": self.phase_sha256,
            "phase_capability_ids": list(self.phase_capability_ids),
            "attempted_capability_ids": list(self.attempted_capability_ids),
            "deficit_evidence_sha256": self.deficit_evidence_sha256,
            "recovery_attempt_counts": [list(item) for item in self.recovery_attempt_counts],
            "cadence_sha256": self.cadence_sha256,
        }

    def expected_digest(self) -> str:
        record = self.to_record()
        record["cadence_sha256"] = "0" * 64
        return _digest(record)

    def verify(self) -> None:
        counts = dict(self.recovery_attempt_counts)
        if (self.schema != CADENCE_SCHEMA or not self.run_id
                or type(self.revision) is not int or self.revision < 0
                or (self.predecessor_sha256 is not None
                    and not _sha(self.predecessor_sha256))
                or not all(_sha(value) for value in (
                    self.active_grade_activation_sha256,
                    self.active_grade_definition_sha256,
                    self.member_census_sha256,
                    self.phase_sha256,
                    self.deficit_evidence_sha256,
                    self.cadence_sha256))
                or type(self.policy_epoch) is not int or self.policy_epoch < 0
                or not isinstance(self.phase, ActiveGradeCadencePhase)
                or self.phase_round not in set(range(MAX_RECOVERY_ROUNDS + 2))
                or (self.phase is ActiveGradeCadencePhase.MAIN and self.phase_round != 0)
                or (self.phase is ActiveGradeCadencePhase.RECOVERY_1 and self.phase_round != 1)
                or (self.phase is ActiveGradeCadencePhase.RECOVERY_2 and self.phase_round != 2)
                or (self.phase is ActiveGradeCadencePhase.BOUNDARY
                    and self.phase_round != MAX_RECOVERY_ROUNDS + 1)
                or any(not isinstance(item, str) or not item
                       for item in self.phase_capability_ids + self.attempted_capability_ids)
                or len(set(self.phase_capability_ids)) != len(self.phase_capability_ids)
                or len(set(self.attempted_capability_ids)) != len(self.attempted_capability_ids)
                or not set(self.attempted_capability_ids) <= set(self.phase_capability_ids)
                or len(counts) != len(self.recovery_attempt_counts)
                or any(not isinstance(capability, str) or not capability
                       or type(count) is not int or count < 0
                       for capability, count in self.recovery_attempt_counts)
                or self.cadence_sha256 != self.expected_digest()):
            _invalid("BAMF_ACTIVE_GRADE_CADENCE_INVALID")


def issue_cadence_state(**values) -> ActiveGradeCadenceState:
    state = object.__new__(ActiveGradeCadenceState)
    for name, value in values.items():
        object.__setattr__(state, name, value)
    object.__setattr__(state, "schema", CADENCE_SCHEMA)
    object.__setattr__(state, "_issuance", _ISSUER)
    object.__setattr__(state, "cadence_sha256", "0" * 64)
    object.__setattr__(state, "cadence_sha256", state.expected_digest())
    state.verify()
    return state


def cadence_state_from_record(record: dict) -> ActiveGradeCadenceState:
    expected = {
        "schema", "run_id", "revision", "predecessor_sha256",
        "active_grade_activation_sha256", "active_grade_definition_sha256",
        "policy_epoch", "member_census_sha256", "phase", "phase_round",
        "phase_sha256", "phase_capability_ids", "attempted_capability_ids",
        "deficit_evidence_sha256", "recovery_attempt_counts", "cadence_sha256",
    }
    if not isinstance(record, dict) or set(record) != expected or record.get("schema") != CADENCE_SCHEMA:
        _invalid("BAMF_ACTIVE_GRADE_CADENCE_RECORD_INVALID")
    try:
        values = {key: record[key] for key in expected - {"schema", "cadence_sha256", "phase",
                                                           "phase_capability_ids",
                                                           "attempted_capability_ids",
                                                           "recovery_attempt_counts"}}
        state = issue_cadence_state(
            **values,
            phase=ActiveGradeCadencePhase(record["phase"]),
            phase_capability_ids=tuple(record["phase_capability_ids"]),
            attempted_capability_ids=tuple(record["attempted_capability_ids"]),
            recovery_attempt_counts=tuple(
                (item[0], item[1]) for item in record["recovery_attempt_counts"]),
        )
    except (KeyError, TypeError, ValueError, IndexError):
        _invalid("BAMF_ACTIVE_GRADE_CADENCE_RECORD_INVALID")
    if state.cadence_sha256 != record["cadence_sha256"]:
        _invalid("BAMF_ACTIVE_GRADE_CADENCE_RECORD_INVALID")
    return state


@dataclass(frozen=True, init=False)
class ActiveGradeCadenceAuthorization:
    state: ActiveGradeCadenceState
    authorized_capability_ids: tuple[str, ...]
    disposition: ActiveGradeCadenceDisposition
    _issuance: object = field(repr=False, compare=False)

    def __init__(self, *args, **kwargs):
        _invalid("BAMF_ACTIVE_GRADE_CADENCE_AUTHORIZATION_CALLER_CONSTRUCTION_FORBIDDEN")

    def verify(self) -> None:
        if (getattr(self.state, "_issuance", None) is not _ISSUER
                or not isinstance(self.disposition, ActiveGradeCadenceDisposition)
                or not isinstance(self.authorized_capability_ids, tuple)
                or any(not isinstance(item, str) or not item
                       for item in self.authorized_capability_ids)
                or len(set(self.authorized_capability_ids)) != len(
                    self.authorized_capability_ids)
                or not set(self.authorized_capability_ids) <= set(
                    self.state.phase_capability_ids)
                or ((self.disposition is ActiveGradeCadenceDisposition.TEACHING)
                    != bool(self.authorized_capability_ids))):
            _invalid("BAMF_ACTIVE_GRADE_CADENCE_AUTHORIZATION_INVALID")
        self.state.verify()

    @property
    def phase(self) -> ActiveGradeCadencePhase:
        return self.state.phase

    def to_record(self) -> dict:
        self.verify()
        return {
            "schema": CADENCE_AUTHORIZATION_SCHEMA,
            "phase": self.state.phase.value,
            "phase_round": self.state.phase_round,
            "phase_sha256": self.state.phase_sha256,
            "cadence_sha256": self.state.cadence_sha256,
            "active_grade_activation_sha256": self.state.active_grade_activation_sha256,
            "active_grade_definition_sha256": self.state.active_grade_definition_sha256,
            "member_census_sha256": self.state.member_census_sha256,
            "deficit_evidence_sha256": self.state.deficit_evidence_sha256,
            "policy_epoch": self.state.policy_epoch,
            "authorized_capability_ids": list(self.authorized_capability_ids),
            "disposition": self.disposition.value,
        }


def issue_cadence_authorization(
        state: ActiveGradeCadenceState,
        authorized_capability_ids: tuple[str, ...],
        disposition: ActiveGradeCadenceDisposition) -> ActiveGradeCadenceAuthorization:
    result = object.__new__(ActiveGradeCadenceAuthorization)
    object.__setattr__(result, "state", state)
    object.__setattr__(result, "authorized_capability_ids", tuple(authorized_capability_ids))
    object.__setattr__(result, "disposition", disposition)
    object.__setattr__(result, "_issuance", _ISSUER)
    result.verify()
    return result


__all__ = (
    "ActiveGradeCadenceAuthorization", "ActiveGradeCadenceDisposition",
    "ActiveGradeCadencePhase",
    "ActiveGradeCadenceState", "CADENCE_AUTHORIZATION_SCHEMA",
    "CADENCE_POINTER_SCHEMA", "CADENCE_SCHEMA", "MAX_RECOVERY_ROUNDS",
    "RECOVERY_WIDTH", "cadence_state_from_record", "issue_cadence_authorization",
    "issue_cadence_state",
)
