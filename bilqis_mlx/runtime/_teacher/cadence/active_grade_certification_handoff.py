"""Unforgeable #1333 boundary handoff consumed by #1334 certification."""
from __future__ import annotations

from dataclasses import dataclass, field
import hashlib
import json
from pathlib import Path

from bilqis_mlx.errors import ErrorBus, SCHOOL

from .active_grade_cadence_contracts import (
    ActiveGradeCadenceDisposition,
    ActiveGradeCadencePhase,
)
from .active_grade_cadence_custody import read_current_cadence


SCHEMA = "bilqis.bamf.active-grade-certification-boundary/v1"
SHA256_HEX_LENGTH = hashlib.sha256().digest_size * 2
_ISSUER = object()
_BOUNDARY_DISPOSITIONS = frozenset({
    ActiveGradeCadenceDisposition.GRADE_COMPLETE,
})


def _invalid(reason: str):
    ErrorBus.Raise(SCHOOL.BAMF_CURRICULUM.INVALID, reason=reason)


def _digest(value) -> str:
    raw = json.dumps(
        value, sort_keys=True, separators=(",", ":"),
        ensure_ascii=False, allow_nan=False).encode()
    return hashlib.sha256(raw).hexdigest()


@dataclass(frozen=True, init=False)
class ActiveGradeCertificationBoundary:
    run_id: str
    disposition: ActiveGradeCadenceDisposition
    cadence_sha256: str
    phase_sha256: str
    active_grade_activation_sha256: str
    active_grade_definition_sha256: str
    cadence_policy_epoch: int
    cadence_epoch: int
    member_census_sha256: str
    deficit_evidence_sha256: str
    boundary_sha256: str
    schema: str = SCHEMA
    _issuance: object = field(repr=False, compare=False)

    def __init__(self, *args, **kwargs):
        _invalid("BAMF_GRADE_CERTIFICATION_BOUNDARY_CALLER_CONSTRUCTION_FORBIDDEN")

    def to_record(self) -> dict:
        return {
            "schema": self.schema,
            "run_id": self.run_id,
            "disposition": self.disposition.value,
            "cadence_sha256": self.cadence_sha256,
            "phase_sha256": self.phase_sha256,
            "active_grade_activation_sha256": self.active_grade_activation_sha256,
            "active_grade_definition_sha256": self.active_grade_definition_sha256,
            "cadence_policy_epoch": self.cadence_policy_epoch,
            "cadence_epoch": self.cadence_epoch,
            "member_census_sha256": self.member_census_sha256,
            "deficit_evidence_sha256": self.deficit_evidence_sha256,
            "boundary_sha256": self.boundary_sha256,
        }

    def verify(self) -> None:
        record = self.to_record()
        claimed = record.pop("boundary_sha256")
        digests = (
            self.cadence_sha256, self.phase_sha256,
            self.active_grade_activation_sha256,
            self.active_grade_definition_sha256,
            self.member_census_sha256, self.deficit_evidence_sha256,
            self.boundary_sha256,
        )
        if (
            getattr(self, "_issuance", None) is not _ISSUER
            or self.schema != SCHEMA
            or not self.run_id
            or self.disposition not in _BOUNDARY_DISPOSITIONS
            or any(
                type(value) is not str or len(value) != SHA256_HEX_LENGTH
                or any(char not in "0123456789abcdef" for char in value)
                for value in digests
            )
            or type(self.cadence_policy_epoch) is not int
            or self.cadence_policy_epoch < 0
            or type(self.cadence_epoch) is not int
            or self.cadence_epoch < 0
            or claimed != _digest(record)
        ):
            _invalid("BAMF_GRADE_CERTIFICATION_BOUNDARY_INVALID")


def _issue_boundary(authorization) -> ActiveGradeCertificationBoundary:
    authorization.verify()
    state = authorization.state
    if (
        state.phase is not ActiveGradeCadencePhase.BOUNDARY
        or authorization.disposition not in _BOUNDARY_DISPOSITIONS
        or authorization.authorized_capability_ids
    ):
        _invalid("BAMF_GRADE_CERTIFICATION_BOUNDARY_AUTHORITY_REQUIRED")
    result = object.__new__(ActiveGradeCertificationBoundary)
    values = {
        "run_id": state.run_id,
        "disposition": authorization.disposition,
        "cadence_sha256": state.cadence_sha256,
        "phase_sha256": state.phase_sha256,
        "active_grade_activation_sha256": state.active_grade_activation_sha256,
        "active_grade_definition_sha256": state.active_grade_definition_sha256,
        "cadence_policy_epoch": state.policy_epoch,
        "cadence_epoch": state.cadence_epoch,
        "member_census_sha256": state.member_census_sha256,
        "deficit_evidence_sha256": state.deficit_evidence_sha256,
        "boundary_sha256": "0" * SHA256_HEX_LENGTH,
        "schema": SCHEMA,
        "_issuance": _ISSUER,
    }
    for name, value in values.items():
        object.__setattr__(result, name, value)
    record = result.to_record()
    record.pop("boundary_sha256")
    object.__setattr__(result, "boundary_sha256", _digest(record))
    result.verify()
    return result


def certification_boundary_from_priority_result(result):
    from bilqis_mlx.runtime.accepted_priority_visit_contracts import (
        require_priority_cadence_authorization,
    )
    authorization = require_priority_cadence_authorization(result)
    if authorization is None:
        return None
    if authorization.disposition not in _BOUNDARY_DISPOSITIONS:
        return None
    return _issue_boundary(authorization)


def require_current_certification_boundary(
    run_dir: Path,
    boundary: ActiveGradeCertificationBoundary,
) -> ActiveGradeCertificationBoundary:
    if type(boundary) is not ActiveGradeCertificationBoundary:
        _invalid("BAMF_GRADE_CERTIFICATION_BOUNDARY_AUTHORITY_REQUIRED")
    boundary.verify()
    current = read_current_cadence(Path(run_dir))
    if (
        current is None
        or current.phase is not ActiveGradeCadencePhase.BOUNDARY
        or current.run_id != boundary.run_id
        or current.cadence_sha256 != boundary.cadence_sha256
        or current.phase_sha256 != boundary.phase_sha256
        or current.active_grade_activation_sha256
           != boundary.active_grade_activation_sha256
        or current.active_grade_definition_sha256
           != boundary.active_grade_definition_sha256
        or current.policy_epoch != boundary.cadence_policy_epoch
        or current.cadence_epoch != boundary.cadence_epoch
        or current.member_census_sha256 != boundary.member_census_sha256
        or current.deficit_evidence_sha256 != boundary.deficit_evidence_sha256
    ):
        _invalid("BAMF_GRADE_CERTIFICATION_BOUNDARY_STALE")
    return boundary


__all__ = (
    "ActiveGradeCertificationBoundary",
    "certification_boundary_from_priority_result",
    "require_current_certification_boundary",
)
