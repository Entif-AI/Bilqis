"""B13-bound #1314 activation of frozen learner-generated grades."""
from __future__ import annotations

from pathlib import Path

from bilqis_mlx.errors import ErrorBus, SCHOOL
from bilqis_mlx.factory.generated_grade import GeneratedGradeProposal

from .active_generated_grade_contracts import (
    ActiveGeneratedGrade,
    issue_active_generated_grade,
)
from . import active_generated_grade_custody as _custody
from .generated_grade import (
    _read_issued_proposal,
    seal_accepted_generated_grade,
)
from .active_generated_grade_acceptance import (
    _persist_proposal_acceptance,
    _reconcile_accepted_generated_grade,
)
from .active_generated_grade_correction import (
    _issue_correction_transition_authority,
    require_correction_transition_authority,
)
from .active_generated_grade_certification import (
    _issue_certification_transition_authority,
    require_certification_transition_authority,
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


def _require_active_transition_current(
        root: Path, active: ActiveGeneratedGrade) -> None:
    if active.transition_kind == "BOOTSTRAP":
        from .initial_grade_bootstrap import require_initial_grade_bootstrap
        require_initial_grade_bootstrap(root, active)
    else:
        proposal = _read_issued_proposal(root, active.proposal_sha256)
        _reconcile_accepted_generated_grade(root, active, proposal)
    if active.transition_kind == "CORRECTION":
        require_correction_transition_authority(root, active)
    if active.transition_kind == "CERTIFICATION":
        require_certification_transition_authority(root, active)


def read_active_generated_grade(run_dir: Path, *, repair: bool = True) -> ActiveGeneratedGrade:
    root = Path(run_dir)
    active = _custody._read_stored_active(root)
    if active is None:
        _fail("BAMF_ACTIVE_GENERATED_GRADE_MISSING")
    if not _activation_is_accepted_ancestor(root, active):
        _fail("BAMF_ACTIVE_GENERATED_GRADE_ACCEPTED_ANCESTRY_DRIFT")
    _require_active_transition_current(root, active)
    # Heal only after every accepted-ancestry and transition check succeeds.
    if repair:
        _custody._persist_commit(root, active)
    return active


def _read_bound_active_generated_grade(
        run_dir: Path, *, expected_activation_sha256: str,
        expected_definition_sha256: str, currentness_step,
        currentness_transaction, parent,
        active_currentness=None) -> ActiveGeneratedGrade:
    """Revalidate the exact frozen grade after B13 currentness was paid this step.

    The cold reader proves accepted ancestry.  A hot caller may reuse that proof
    only while the accepted parent is covered by the latest revocable B13 step
    witness and the content-addressed active-grade custody still names the exact
    activation/definition that was fully validated when the frontier was issued.
    """
    from bilqis_mlx.runtime.bamf_bundle.currentness_transaction import (
        require_accepted_currentness_step,
    )
    require_accepted_currentness_step(
        currentness_step, currentness_transaction, parent)
    if active_currentness is not None:
        from .active_generated_grade_currentness import (
            require_active_generated_grade_currentness,
        )
        return require_active_generated_grade_currentness(
            active_currentness, run_dir,
            expected_activation_sha256=expected_activation_sha256,
            expected_definition_sha256=expected_definition_sha256,
        )
    root = Path(run_dir)
    active = _custody._read_stored_active(root)
    if (active is None
            or active.activation_sha256 != expected_activation_sha256
            or active.definition.definition_sha256 != expected_definition_sha256):
        _fail("BAMF_ACTIVE_GENERATED_GRADE_CURRENTNESS_DRIFT")
    _require_active_transition_current(root, active)
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
    proposal: GeneratedGradeProposal | None,
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
                    return read_active_generated_grade(root)
                _fail(
                    "BAMF_ACTIVE_GENERATED_GRADE_TRANSITION_AUTHORITY_REQUIRED")
            if _custody._activation_history_exists(root):
                if not _custody._recoverable_initial_orphan(root, active):
                    _fail("BAMF_ACTIVE_GENERATED_GRADE_POINTER_MISSING")
        elif (
            current is None
            or current.activation_sha256 != predecessor.activation_sha256
        ):
            _fail("BAMF_ACTIVE_GENERATED_GRADE_PREDECESSOR_DRIFT")
        if proposal is None:
            if active.transition_kind != "BOOTSTRAP":
                _fail("BAMF_ACTIVE_GENERATED_GRADE_PROPOSAL_REQUIRED")
        else:
            _persist_proposal_acceptance(root, active, proposal)
        _custody._persist_activation(root, active)
    return read_active_generated_grade(root)


def _require_identity_still_current(run_dir: Path, identity) -> None:
    _custody._require_identity_still_current(run_dir, identity)


def activate_accepted_generated_grade(
    run_dir: Path,
    proposal: GeneratedGradeProposal,
) -> ActiveGeneratedGrade:
    root = Path(run_dir)
    identity = _accepted_generation_identity(root)
    definition = seal_accepted_generated_grade(root, proposal)
    active = _active_from_proposal(identity, proposal, definition)
    return _publish_if_current(
        root, identity, active, proposal, predecessor=None)


def ensure_active_generated_grade(run_dir: Path) -> ActiveGeneratedGrade:
    """Return the frozen active grade, activating only accepted C07/B13 custody."""
    root = Path(run_dir)
    pointer = _custody._pointer_path(root)
    if pointer.exists() or pointer.is_symlink():
        return read_active_generated_grade(root)
    proposal = _custody._accepted_bound_generated_grade_proposal(root)
    return activate_accepted_generated_grade(root, proposal)


from .active_generated_grade_currentness import (  # noqa: E402
    _bind_active_generated_grade_currentness,
    _require_active_generated_grade_currentness,
)
from .active_generated_grade_transitions import (  # noqa: E402
    activate_certified_generated_grade,
    activate_corrected_generated_grade,
)

__all__ = (
    "ActiveGeneratedGrade",
    "activate_accepted_generated_grade",
    "activate_certified_generated_grade",
    "activate_corrected_generated_grade",
    "ensure_active_generated_grade",
    "read_active_generated_grade",
)
