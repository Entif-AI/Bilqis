"""B13-bound #1314 activation of frozen learner-generated grades."""
from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path

from bilqis_mlx.errors import ErrorBus, SCHOOL
from bilqis_mlx.factory.generated_grade import GeneratedGradeProposal

from .active_generated_grade_contracts import (
    ActiveGeneratedGrade,
    issue_active_generated_grade,
)
from . import active_generated_grade_custody as _custody
from .generated_grade import (
    seal_accepted_generated_grade,
)


def _fail(reason: str):
    ErrorBus.raise_(
        SCHOOL.BAMF_ATLAS_ADMISSION.INVALID,
        reason=reason,
    )


def _accepted_generation_identity(
    run_dir: Path,
) -> tuple[str, int, str, str]:
    return _custody._accepted_generation_identity(run_dir)


def _activation_is_accepted_ancestor(
    run_dir: Path,
    active: ActiveGeneratedGrade,
) -> bool:
    return _custody._activation_is_accepted_ancestor(run_dir, active)


def read_active_generated_grade(run_dir: Path) -> ActiveGeneratedGrade:
    active = _custody._read_stored_active(Path(run_dir))
    if active is None:
        _fail("BAMF_ACTIVE_GENERATED_GRADE_MISSING")
    if not _activation_is_accepted_ancestor(Path(run_dir), active):
        _fail("BAMF_ACTIVE_GENERATED_GRADE_ACCEPTED_ANCESTRY_DRIFT")
    return active


def _active_from_proposal(
    identity, proposal, definition, *,
    predecessor=None, transition_kind="INITIAL",
    transition_receipt_sha256=None, transition_reason=None,
) -> ActiveGeneratedGrade:
    run_id, generation, manifest, acceptance = identity
    return issue_active_generated_grade(
        run_id=run_id,
        activation_generation=generation,
        activation_manifest_sha256=manifest,
        activation_acceptance_sha256=acceptance,
        generated_grade_id=definition.definition_sha256,
        definition=definition,
        proposal_sha256=proposal.proposal_sha256,
        a09_snapshot_sha256=proposal.snapshot_sha256,
        a09_closure_sha256=proposal.closure_sha256,
        a09_proposal_sha256=proposal.a09_proposal_sha256,
        predecessor_activation_sha256=(
            None if predecessor is None else predecessor.activation_sha256),
        predecessor_definition_sha256=(
            None if predecessor is None
            else predecessor.definition.definition_sha256),
        transition_kind=transition_kind,
        transition_receipt_sha256=transition_receipt_sha256,
        transition_reason=transition_reason,
    )


def _publish_if_current(
    run_dir: Path,
    identity,
    active: ActiveGeneratedGrade,
    *,
    predecessor: ActiveGeneratedGrade | None,
) -> ActiveGeneratedGrade:
    from bilqis_mlx.runtime.bamf_bundle.publication import (
        _pointer_lock,
    )
    root = Path(run_dir)
    with _pointer_lock(root, create=True):
        _require_identity_still_current(root, identity)
        current = _custody._read_stored_active(root)
        if predecessor is None:
            if current is not None:
                if current.definition == active.definition:
                    return current
                _fail(
                    "BAMF_ACTIVE_GENERATED_GRADE_TRANSITION_AUTHORITY_REQUIRED")
        elif (
            current is None
            or current.activation_sha256 != predecessor.activation_sha256
        ):
            _fail("BAMF_ACTIVE_GENERATED_GRADE_PREDECESSOR_DRIFT")
        _custody._persist_activation(root, active)
    return read_active_generated_grade(root)


def _require_identity_still_current(run_dir: Path, identity) -> None:
    _custody._require_identity_still_current(run_dir, identity)


def activate_accepted_generated_grade(
    run_dir: Path,
    proposal: GeneratedGradeProposal,
) -> ActiveGeneratedGrade:
    root = Path(run_dir)
    definition = seal_accepted_generated_grade(root, proposal)
    identity = _accepted_generation_identity(root)
    active = _active_from_proposal(identity, proposal, definition)
    return _publish_if_current(
        root, identity, active, predecessor=None)


def _accepted_correction_by_id(
    run_dir: Path,
    manifest_sha256: str,
    correction_event_id: str,
):
    return _custody._accepted_correction_by_id(
        run_dir, manifest_sha256, correction_event_id)


def activate_corrected_generated_grade(
    run_dir: Path,
    proposal: GeneratedGradeProposal,
    *,
    correction_event_id: str,
) -> ActiveGeneratedGrade:
    root = Path(run_dir)
    predecessor = read_active_generated_grade(root)
    identity = _accepted_generation_identity(root)
    correction = _accepted_correction_by_id(
        root, identity[2], correction_event_id)
    definition = seal_accepted_generated_grade(root, proposal)
    if definition.learner_foot_sha256 != (
            predecessor.definition.learner_foot_sha256):
        _fail("BAMF_ACTIVE_GENERATED_GRADE_CORRECTION_LEARNER_DRIFT")
    active = _active_from_proposal(
        identity, proposal, definition,
        predecessor=predecessor,
        transition_kind="CORRECTION",
        transition_receipt_sha256=correction_event_id,
        transition_reason=correction.reason_code,
    )
    return _publish_if_current(
        root, identity, active, predecessor=predecessor)


_CERTIFIED_TRANSITION_ISSUER = object()


@dataclass(frozen=True, init=False)
class _CertifiedGradeTransitionAuthority:
    predecessor_activation_sha256: str
    successor_proposal_sha256: str
    certification_receipt_sha256: str
    _issuance: object = field(init=False, repr=False, compare=False)


def _issue_certified_grade_transition_authority(
    predecessor_activation_sha256: str,
    successor_proposal_sha256: str,
    certification_receipt_sha256: str,
) -> _CertifiedGradeTransitionAuthority:
    """Internal handoff minted by #1334 only after successful certification."""
    authority = object.__new__(_CertifiedGradeTransitionAuthority)
    object.__setattr__(
        authority, "predecessor_activation_sha256",
        predecessor_activation_sha256)
    object.__setattr__(authority, "successor_proposal_sha256", successor_proposal_sha256)
    object.__setattr__(
        authority, "certification_receipt_sha256", certification_receipt_sha256)
    object.__setattr__(authority, "_issuance", _CERTIFIED_TRANSITION_ISSUER)
    return authority


def activate_certified_generated_grade(
    run_dir: Path,
    proposal: GeneratedGradeProposal,
    *,
    transition_authority: _CertifiedGradeTransitionAuthority,
) -> ActiveGeneratedGrade:
    """Activate #1320's sealed successor only with #1334-issued authority."""
    root = Path(run_dir)
    predecessor = read_active_generated_grade(root)
    if (type(transition_authority) is not _CertifiedGradeTransitionAuthority
            or getattr(transition_authority, "_issuance", None)
               is not _CERTIFIED_TRANSITION_ISSUER
            or transition_authority.predecessor_activation_sha256
               != predecessor.activation_sha256
            or transition_authority.successor_proposal_sha256
               != proposal.proposal_sha256):
        _fail("BAMF_ACTIVE_GENERATED_GRADE_CERTIFICATION_AUTHORITY_REQUIRED")
    identity = _accepted_generation_identity(root)
    definition = seal_accepted_generated_grade(root, proposal)
    active = _active_from_proposal(
        identity, proposal, definition, predecessor=predecessor,
        transition_kind="CERTIFICATION",
        transition_receipt_sha256=(
            transition_authority.certification_receipt_sha256),
        transition_reason="GRADE_CERTIFIED",
    )
    return _publish_if_current(root, identity, active, predecessor=predecessor)


def ensure_active_generated_grade(run_dir: Path) -> ActiveGeneratedGrade:
    """Return the frozen active grade, activating only accepted C07/B13 custody."""
    root = Path(run_dir)
    pointer = _custody._pointer_path(root)
    if pointer.exists() or pointer.is_symlink():
        return read_active_generated_grade(root)
    proposal = _custody._accepted_bound_generated_grade_proposal(root)
    return activate_accepted_generated_grade(root, proposal)


__all__ = (
    "ActiveGeneratedGrade",
    "activate_accepted_generated_grade",
    "activate_certified_generated_grade",
    "activate_corrected_generated_grade",
    "ensure_active_generated_grade",
    "read_active_generated_grade",
)
