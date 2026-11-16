"""Accepted-run #1320 proposal and definition authority."""
from __future__ import annotations

from pathlib import Path

from bilqis_mlx.errors import ErrorBus, SCHOOL
from bilqis_mlx.factory.generated_grade import GeneratedGradeProposal, synthesize_generated_grade
from bilqis_mlx.factory.generated_grade.definition import _seal_generated_grade
from bilqis_mlx.factory.generated_grade.inputs import _compile_generated_grade_inputs

from .atlas_admission import read_accepted_atlas_factory_release


def propose_accepted_generated_grade(supervisor) -> GeneratedGradeProposal:
    """Recompute one proposal from a custody-reloaded A09/C07 flywheel state."""
    from .atlas_flywheel_runtime import AcceptedAtlasFlywheelSupervisor
    if type(supervisor) is not AcceptedAtlasFlywheelSupervisor:
        ErrorBus.raise_(
            SCHOOL.BAMF_ATLAS_ADMISSION.INVALID,
            reason="BAMF_GENERATED_GRADE_ACCEPTED_SUPERVISOR_REQUIRED",
        )
    state = supervisor.load_state()
    inputs = _compile_generated_grade_inputs(
        state.epoch, state.learner_evidence, state.plan)
    return synthesize_generated_grade(
        state.epoch.snapshot, state.epoch.closure,
        state.epoch.current_release, inputs)


def _accepted_release_lineage(
    run_dir: Path, proposal: GeneratedGradeProposal,
) -> tuple:
    """Cold-read immutable release artifacts back to the proposal predecessor."""
    from .admission import _read_executable_factory_release_artifact
    accepted = read_accepted_atlas_factory_release(run_dir)
    reverse = [accepted]
    seen = {accepted.release_sha256}
    while reverse[-1].release_sha256 != proposal.current_release_sha256:
        predecessor = reverse[-1].predecessor_release_sha256
        if predecessor is None or predecessor in seen:
            ErrorBus.raise_(
                SCHOOL.BAMF_ATLAS_ADMISSION.INVALID,
                reason="BAMF_GENERATED_GRADE_ACCEPTED_LINEAGE_MISSING",
            )
        seen.add(predecessor)
        reverse.append(_read_executable_factory_release_artifact(Path(run_dir), {
            "factory_release_sha256": predecessor,
            "factory_release_file": "factory-releases/" + predecessor + ".json",
        }))
    lineage = tuple(reversed(reverse))
    for parent, child in zip(lineage, lineage[1:]):
        child.verify_successor_of(parent)
    return lineage


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
    from .atlas_flywheel_runtime import AcceptedAtlasFlywheelSupervisor
    accepted_proposal = propose_accepted_generated_grade(
        AcceptedAtlasFlywheelSupervisor(Path(run_dir)))
    if accepted_proposal.proposal_sha256 != proposal.proposal_sha256:
        ErrorBus.raise_(
            SCHOOL.BAMF_ATLAS_ADMISSION.INVALID,
            reason="BAMF_GENERATED_GRADE_ACCEPTED_PROPOSAL_MISMATCH",
        )
    lineage = _accepted_release_lineage(run_dir, proposal)
    return _seal_generated_grade(
        proposal, lineage[-1], release_lineage=lineage)


__all__ = ("propose_accepted_generated_grade", "seal_accepted_generated_grade")
