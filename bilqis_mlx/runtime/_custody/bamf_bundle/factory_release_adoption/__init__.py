"""B13-issued custody transition for neural-inert Factory-release adoption."""
from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass, field

from bilqis_mlx.data_plane import SHA256_HEX_LENGTH
from bilqis_mlx.errors import ErrorBus, SCHOOL


FACTORY_RELEASE_ADOPTION_TRANSITION_SCHEMA = (
    "bilqis.mlx.bamf-generation-transition/v3"
)
FACTORY_RELEASE_ADOPTION_KIND = "FACTORY_RELEASE_ADOPTION"
FACTORY_RELEASE_ADOPTION_EVENT = "BAMF_FACTORY_RELEASE_ADOPTION_COMMITTED"
FACTORY_RELEASE_ADOPTION_EVENT_SCHEMA = (
    "bilqis.mlx.bamf-factory-release-adoption-event/v1"
)
_DIGEST_FIELDS = (
    "predecessor_factory_release_sha256",
    "factory_release_sha256",
    "handoff_sha256",
    "proposal_sha256",
    "staged_candidate_sha256",
    "selection_receipt_sha256",
    "lease_sha256",
    "source_approval_sha256",
)
_FIELDS = ("schema", "kind", "invalidate_derived_caches") + _DIGEST_FIELDS
_ISSUER = object()


def _invalid() -> None:
    ErrorBus.Raise(
        SCHOOL.STATE.HISTORICAL_ARTIFACT_INVALID,
        reason="BAMF_GENERATION_TRANSITION_INVALID",
    )


def _hex(value) -> bool:
    return (
        type(value) is str
        and len(value) == SHA256_HEX_LENGTH
        and all(char in "0123456789abcdef" for char in value)
    )


@dataclass(frozen=True, init=False)
class FactoryReleaseAdoptionTransition(Mapping):
    """One B13-issued claim that only Factory authority advances."""

    predecessor_factory_release_sha256: str
    factory_release_sha256: str
    handoff_sha256: str
    proposal_sha256: str
    staged_candidate_sha256: str
    selection_receipt_sha256: str
    lease_sha256: str
    source_approval_sha256: str
    schema: str = FACTORY_RELEASE_ADOPTION_TRANSITION_SCHEMA
    kind: str = FACTORY_RELEASE_ADOPTION_KIND
    invalidate_derived_caches: bool = False
    _issuance: object = field(init=False, repr=False, compare=False)

    def __init__(self, *args, **kwargs):
        _invalid()

    def __post_init__(self) -> None:
        if getattr(self, "_issuance", None) is not _ISSUER:
            _invalid()
        validate_factory_release_adoption_transition(self)

    def __iter__(self):
        return iter(_FIELDS)

    def __len__(self):
        return len(_FIELDS)

    def __getitem__(self, key):
        if key not in _FIELDS:
            raise KeyError(key)
        return getattr(self, key)

    def to_record(self) -> dict:
        return {name: getattr(self, name) for name in _FIELDS}

    @property
    def digest(self) -> str:
        from ..records import canonical, sha
        return sha(canonical(self.to_record()))


def is_factory_release_adoption_transition(value) -> bool:
    return (
        isinstance(value, Mapping)
        and value.get("schema") == FACTORY_RELEASE_ADOPTION_TRANSITION_SCHEMA
        and value.get("kind") == FACTORY_RELEASE_ADOPTION_KIND
    )


def validate_factory_release_adoption_transition(value) -> None:
    if (
        not isinstance(value, Mapping)
        or set(value) != set(_FIELDS)
        or value.get("schema") != FACTORY_RELEASE_ADOPTION_TRANSITION_SCHEMA
        or value.get("kind") != FACTORY_RELEASE_ADOPTION_KIND
        or value.get("invalidate_derived_caches") is not False
        or any(not _hex(value.get(name)) for name in _DIGEST_FIELDS)
    ):
        _invalid()


def require_issued_factory_release_adoption_transition(
    value,
) -> FactoryReleaseAdoptionTransition:
    if (
        type(value) is not FactoryReleaseAdoptionTransition
        or getattr(value, "_issuance", None) is not _ISSUER
    ):
        _invalid()
    value.__post_init__()
    return value


def _issue_factory_release_adoption_transition(
    *,
    predecessor_factory_release_sha256,
    factory_release_sha256,
    handoff_sha256,
    proposal_sha256,
    staged_candidate_sha256,
    selection_receipt_sha256,
    lease_sha256,
    source_approval_sha256,
) -> FactoryReleaseAdoptionTransition:
    transition = object.__new__(FactoryReleaseAdoptionTransition)
    values = (
        ("predecessor_factory_release_sha256", predecessor_factory_release_sha256),
        ("factory_release_sha256", factory_release_sha256),
        ("handoff_sha256", handoff_sha256),
        ("proposal_sha256", proposal_sha256),
        ("staged_candidate_sha256", staged_candidate_sha256),
        ("selection_receipt_sha256", selection_receipt_sha256),
        ("lease_sha256", lease_sha256),
        ("source_approval_sha256", source_approval_sha256),
        ("schema", FACTORY_RELEASE_ADOPTION_TRANSITION_SCHEMA),
        ("kind", FACTORY_RELEASE_ADOPTION_KIND),
        ("invalidate_derived_caches", False),
        ("_issuance", _ISSUER),
    )
    for name, value in values:
        object.__setattr__(transition, name, value)
    transition.__post_init__()
    return transition


def derive_factory_release_adoption_candidate(
    parent,
    *,
    parent_manifest_sha256,
    transition,
):
    """Derive generation N+1 while preserving every neural/teacher state owner."""
    from ..records import BamfBundleCandidate, CompleteStudent

    if (
        type(parent) is not CompleteStudent
        or not _hex(parent_manifest_sha256)
    ):
        _invalid()
    transition = require_issued_factory_release_adoption_transition(transition)
    event = {
        "event": FACTORY_RELEASE_ADOPTION_EVENT,
        "schema": FACTORY_RELEASE_ADOPTION_EVENT_SCHEMA,
        "run_id": parent.run_id,
        "generation": parent.generation + 1,
        "optimizer_step": parent.retained_state.optimizer_step,
        "predecessor_factory_release_sha256":
            transition.predecessor_factory_release_sha256,
        "factory_release_sha256": transition.factory_release_sha256,
        "handoff_sha256": transition.handoff_sha256,
        "proposal_sha256": transition.proposal_sha256,
        "selection_receipt_sha256": transition.selection_receipt_sha256,
        "lease_sha256": transition.lease_sha256,
        "source_approval_sha256": transition.source_approval_sha256,
        "transition_sha256": transition.digest,
    }
    return BamfBundleCandidate(
        parent.run_id,
        parent.generation + 1,
        parent_manifest_sha256,
        parent.implementation_sha256,
        parent.topology,
        parent.extents,
        parent.retained_state,
        parent.optimizer_hyperparameters,
        parent.provenance,
        dict(parent.semantic_abi),
        dict(parent.compiler_features),
        dict(parent.correction_frontier),
        dict(parent.teacher_state),
        dict(parent.evaluation_contract),
        transition,
        (event,),
        parent.run_identity,
        parent.baseline_evidence,
    )
