"""Accepted-run #1320 proposal and definition authority."""
from __future__ import annotations

from pathlib import Path
from dataclasses import dataclass

from bilqis_mlx.errors import ErrorBus, SCHOOL
from bilqis_mlx.factory.generated_grade import GeneratedGradeProposal, synthesize_generated_grade
from bilqis_mlx.factory.generated_grade.definition import _seal_generated_grade
from bilqis_mlx.factory.generated_grade.inputs import _compile_generated_grade_inputs
from bilqis_mlx.runtime.bamf_bundle.publication import _fsync_directory
from .atlas_admission import read_accepted_atlas_factory_release
from .generated_grade_acceptance import (
    _accepted_release_lineage as _accepted_release_lineage_impl,
    _persist_issued_proposal as _persist_issued_proposal_impl,
    _proposal_bound_in_accepted_ancestry,
    _read_issued_proposal,
)

_GENERATED_GRADE_AUTHORITY_ISSUER = object()


def _persist_issued_proposal(run_dir: Path, proposal: GeneratedGradeProposal) -> None:
    _persist_issued_proposal_impl(
        run_dir, proposal, sync_directory=_fsync_directory)


def _accepted_release_lineage(
    run_dir: Path, proposal: GeneratedGradeProposal,
) -> tuple:
    return _accepted_release_lineage_impl(
        run_dir, proposal,
        accepted_release_reader=read_accepted_atlas_factory_release,
    )


@dataclass(frozen=True, init=False)
class _AcceptedGeneratedGradeAuthority:
    """Unforgeable-by-contract capability issued from accepted #1320 state."""

    proposal_sha256: str
    predecessor_factory_release_sha256: str
    a09_proposal_sha256: str
    _issuance: object


def _mint_generated_grade_authority(
    proposal: GeneratedGradeProposal,
) -> _AcceptedGeneratedGradeAuthority:
    authority = object.__new__(_AcceptedGeneratedGradeAuthority)
    object.__setattr__(authority, "proposal_sha256", proposal.proposal_sha256)
    object.__setattr__(
        authority, "predecessor_factory_release_sha256",
        proposal.current_release_sha256)
    object.__setattr__(
        authority, "a09_proposal_sha256", proposal.a09_proposal_sha256)
    object.__setattr__(
        authority, "_issuance", _GENERATED_GRADE_AUTHORITY_ISSUER)
    return authority


def _require_generated_grade_authority(
    value,
) -> _AcceptedGeneratedGradeAuthority:
    if (
        type(value) is not _AcceptedGeneratedGradeAuthority
        or getattr(value, "_issuance", None) is not _GENERATED_GRADE_AUTHORITY_ISSUER
    ):
        ErrorBus.raise_(
            SCHOOL.BAMF_ATLAS_ADMISSION.INVALID,
            reason="BAMF_GENERATED_GRADE_ACCEPTED_AUTHORITY_REQUIRED",
        )
    return value


def _recompute_accepted_generated_grade(supervisor) -> GeneratedGradeProposal:
    """Derive one proposal from custody-reloaded A09/C07 state without persisting."""
    from .atlas_flywheel_runtime import AcceptedAtlasFlywheelSupervisor
    if type(supervisor) is not AcceptedAtlasFlywheelSupervisor:
        ErrorBus.raise_(
            SCHOOL.BAMF_ATLAS_ADMISSION.INVALID,
            reason="BAMF_GENERATED_GRADE_ACCEPTED_SUPERVISOR_REQUIRED",
        )
    state = supervisor.load_state()
    inputs = _compile_generated_grade_inputs(
        state.epoch, state.learner_evidence, state.plan)
    proposal = synthesize_generated_grade(
        state.epoch.snapshot, state.epoch.closure,
        state.epoch.current_release, inputs)
    return proposal


def _issue_generated_grade_admission_authority(
    supervisor, handoff,
) -> _AcceptedGeneratedGradeAuthority:
    """Issue the exact accepted-state #1320 capability consumed by C07/B13."""
    proposal = _recompute_accepted_generated_grade(supervisor)
    if (
        proposal.current_release_sha256
        != handoff.receipt.predecessor_release.release_sha256
        or proposal.a09_proposal_sha256 != handoff.proposal.proposal_sha256
    ):
        ErrorBus.raise_(
            SCHOOL.BAMF_ATLAS_ADMISSION.INVALID,
            reason="BAMF_GENERATED_GRADE_A09_PROPOSAL_MISMATCH",
        )
    _persist_issued_proposal(supervisor.run_dir, proposal)
    if _read_issued_proposal(
            supervisor.run_dir, proposal.proposal_sha256) != proposal:
        ErrorBus.raise_(
            SCHOOL.BAMF_ATLAS_ADMISSION.INVALID,
            reason="BAMF_GENERATED_GRADE_ACCEPTED_PROPOSAL_MISMATCH",
        )
    return _mint_generated_grade_authority(proposal)


def propose_accepted_generated_grade(supervisor) -> GeneratedGradeProposal:
    """Issue one proposal derived from custody-reloaded A09/C07 flywheel state."""
    proposal = _recompute_accepted_generated_grade(supervisor)
    _persist_issued_proposal(supervisor.run_dir, proposal)
    return proposal


def _recompute_current_accepted_proposal(run_dir: Path) -> GeneratedGradeProposal:
    from .atlas_flywheel_runtime import AcceptedAtlasFlywheelSupervisor
    return _recompute_accepted_generated_grade(
        AcceptedAtlasFlywheelSupervisor(Path(run_dir), None))


def _require_accepted_proposal_authority(
    run_dir: Path,
    proposal: GeneratedGradeProposal,
    lineage: tuple,
) -> None:
    if len(lineage) == 1:
        accepted = _recompute_current_accepted_proposal(run_dir)
        authorized = accepted == proposal
    else:
        authorized = _proposal_bound_in_accepted_ancestry(run_dir, proposal)
    if not authorized:
        ErrorBus.raise_(
            SCHOOL.BAMF_ATLAS_ADMISSION.INVALID,
            reason="BAMF_GENERATED_GRADE_ACCEPTED_PROPOSAL_MISMATCH",
        )


def seal_accepted_generated_grade(
    run_dir: Path, proposal: GeneratedGradeProposal,
):
    """Seal only an accepted-state proposal against accepted B13 Factory custody."""
    if not isinstance(run_dir, Path) or type(proposal) is not GeneratedGradeProposal:
        ErrorBus.raise_(
            SCHOOL.BAMF_ATLAS_ADMISSION.INVALID,
            reason="BAMF_GENERATED_GRADE_ACCEPTED_SEAL_INPUT_INVALID",
        )
    proposal.verify()
    issued_proposal = _read_issued_proposal(run_dir, proposal.proposal_sha256)
    if issued_proposal != proposal:
        ErrorBus.raise_(
            SCHOOL.BAMF_ATLAS_ADMISSION.INVALID,
            reason="BAMF_GENERATED_GRADE_ACCEPTED_PROPOSAL_MISMATCH",
        )
    lineage = _accepted_release_lineage(run_dir, proposal)
    _require_accepted_proposal_authority(run_dir, proposal, lineage)
    return _seal_generated_grade(
        proposal, lineage[-1], release_lineage=lineage)


__all__ = ("propose_accepted_generated_grade", "seal_accepted_generated_grade")
