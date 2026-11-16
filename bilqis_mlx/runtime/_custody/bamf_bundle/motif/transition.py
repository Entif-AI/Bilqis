"""B13-issued generation transition for one accepted B07 allocation change."""
from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass, field

from bilqis_mlx.data_plane import SHA256_HEX_LENGTH
from bilqis_mlx.errors import ErrorBus, SCHOOL
from bilqis_mlx.learning._atlas_candidate.motif_transition import (
    CandidateMotifAllocationTransition,
    _require_candidate_motif_allocation_transition,
)


MOTIF_ALLOCATION_TRANSITION_SCHEMA = "bilqis.mlx.bamf-generation-transition/v3"
MOTIF_ALLOCATION_KIND = "MOTIF_ALLOCATION"
_DIGEST_FIELDS = (
    "b12_transition_sha256", "parent_extents_sha256", "candidate_extents_sha256",
    "parent_allocation_sha256", "candidate_allocation_sha256",
    "motif_candidate_sha256", "approved_context_sha256",
    "candidate_identity_sha256",
)
_FIELDS = ("schema", "kind", "invalidate_derived_caches", "added_pages") + _DIGEST_FIELDS


def _new_transition_owner():
    issued = {}

    def require(value):
        expected = issued.get(id(value))
        if expected is None or expected[0] is not value or dict(value) != expected[1]:
            _invalid()
        return value

    def issue(values):
        transition = object.__new__(MotifAllocationTransition)
        for name, value in values.items():
            object.__setattr__(transition, name, value)
        issued[id(transition)] = (
            transition, {name: getattr(transition, name) for name in _FIELDS})
        transition.__post_init__()
        return transition

    return require, issue


def _invalid():
    ErrorBus.Raise(
        SCHOOL.STATE.HISTORICAL_ARTIFACT_INVALID,
        reason="BAMF_GENERATION_TRANSITION_INVALID")


def _hex(value):
    return (type(value) is str and len(value) == SHA256_HEX_LENGTH
            and all(char in "0123456789abcdef" for char in value))


@dataclass(frozen=True, init=False)
class MotifAllocationTransition(Mapping):
    b12_transition_sha256: str
    parent_extents_sha256: str
    candidate_extents_sha256: str
    parent_allocation_sha256: str
    candidate_allocation_sha256: str
    motif_candidate_sha256: str
    approved_context_sha256: str
    candidate_identity_sha256: str
    added_pages: int
    schema: str = MOTIF_ALLOCATION_TRANSITION_SCHEMA
    kind: str = MOTIF_ALLOCATION_KIND
    invalidate_derived_caches: bool = True

    def __init__(self, *args, **kwargs):
        _invalid()

    def __post_init__(self):
        _require_transition_issued(self)
        validate_motif_allocation_transition(self)

    def __iter__(self):
        return iter(_FIELDS)

    def __len__(self):
        return len(_FIELDS)

    def __getitem__(self, key):
        if key not in _FIELDS:
            raise KeyError(key)
        return getattr(self, key)


def is_motif_allocation_transition(value) -> bool:
    return (isinstance(value, Mapping)
            and value.get("schema") == MOTIF_ALLOCATION_TRANSITION_SCHEMA
            and value.get("kind") == MOTIF_ALLOCATION_KIND)


def validate_motif_allocation_transition(value) -> None:
    if (not isinstance(value, Mapping) or set(value) != set(_FIELDS)
            or value.get("schema") != MOTIF_ALLOCATION_TRANSITION_SCHEMA
            or value.get("kind") != MOTIF_ALLOCATION_KIND
            or value.get("invalidate_derived_caches") is not True
            or type(value.get("added_pages")) is not int
            or value.get("added_pages") not in (0, 1)
            or any(not _hex(value.get(name)) for name in _DIGEST_FIELDS)):
        _invalid()


def require_issued_motif_allocation_transition(value) -> None:
    if type(value) is not MotifAllocationTransition:
        _invalid()
    _require_transition_issued(value)
    value.__post_init__()


_require_transition_issued, _raw_issue_transition = _new_transition_owner()


def _make_transition_deriver(issue_transition):
    def derive(b12: CandidateMotifAllocationTransition, retained_state):
        from bilqis_mlx.learning._atlas_candidate.identity_binding import (
            candidate_identity_for_canonical_consumer,
        )

        _require_candidate_motif_allocation_transition(b12)
        candidate_identity_sha256 = candidate_identity_for_canonical_consumer(
            retained_state)
        values = {
        "b12_transition_sha256": b12.digest,
        "parent_extents_sha256": b12.parent_extents_sha256,
        "candidate_extents_sha256": b12.candidate_extents.digest,
        "parent_allocation_sha256": b12.parent_allocation_sha256,
        "candidate_allocation_sha256": b12.candidate_allocation_sha256,
        "motif_candidate_sha256": b12.motif_candidate_sha256,
        "approved_context_sha256": b12.approved_context_sha256,
        "candidate_identity_sha256": candidate_identity_sha256,
        "added_pages": b12.added_pages,
        "schema": MOTIF_ALLOCATION_TRANSITION_SCHEMA,
        "kind": MOTIF_ALLOCATION_KIND,
        "invalidate_derived_caches": True,
        }
        return issue_transition(values)
    return derive


derive_motif_allocation_transition = _make_transition_deriver(_raw_issue_transition)
del _raw_issue_transition
