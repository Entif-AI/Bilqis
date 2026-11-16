"""Accepted-run #1320 proposal and definition authority."""
from __future__ import annotations

import json
import os
from pathlib import Path
import tempfile

from bilqis_mlx.errors import ErrorBus, SCHOOL
from bilqis_mlx.factory.generated_grade import GeneratedGradeProposal, synthesize_generated_grade
from bilqis_mlx.factory.generated_grade.definition import _seal_generated_grade
from bilqis_mlx.factory.generated_grade.inputs import _compile_generated_grade_inputs

from .atlas_admission import read_accepted_atlas_factory_release


def _proposal_path(run_dir: Path, proposal_sha256: str) -> Path:
    return Path(run_dir) / "generated-grade-proposals" / f"{proposal_sha256}.json"


def _persist_issued_proposal(run_dir: Path, proposal: GeneratedGradeProposal) -> None:
    """Persist the #1320-issued proposal as immutable content-addressed custody."""
    target = _proposal_path(run_dir, proposal.proposal_sha256)
    target.parent.mkdir(parents=True, exist_ok=True)
    payload = json.dumps(
        proposal.manifest(), sort_keys=True, separators=(",", ":"),
    ).encode("utf-8")
    if target.exists():
        existing = GeneratedGradeProposal.from_manifest(
            json.loads(target.read_text(encoding="utf-8")))
        if existing != proposal:
            ErrorBus.raise_(
                SCHOOL.BAMF_ATLAS_ADMISSION.INVALID,
                reason="BAMF_GENERATED_GRADE_ISSUANCE_COLLISION",
            )
        return
    with tempfile.NamedTemporaryFile(
        dir=target.parent, prefix=".generated-grade-", delete=False,
    ) as handle:
        temporary = Path(handle.name)
        handle.write(payload)
        handle.flush()
        os.fsync(handle.fileno())
    try:
        try:
            os.link(temporary, target)
        except FileExistsError:
            existing = GeneratedGradeProposal.from_manifest(
                json.loads(target.read_text(encoding="utf-8")))
            if existing != proposal:
                ErrorBus.raise_(
                    SCHOOL.BAMF_ATLAS_ADMISSION.INVALID,
                    reason="BAMF_GENERATED_GRADE_ISSUANCE_COLLISION",
                )
    finally:
        temporary.unlink(missing_ok=True)


def _read_issued_proposal(
    run_dir: Path, proposal_sha256: str,
) -> GeneratedGradeProposal:
    path = _proposal_path(run_dir, proposal_sha256)
    if not path.is_file() or path.is_symlink():
        ErrorBus.raise_(
            SCHOOL.BAMF_ATLAS_ADMISSION.INVALID,
            reason="BAMF_GENERATED_GRADE_ISSUANCE_MISSING",
        )
    try:
        result = GeneratedGradeProposal.from_manifest(
            json.loads(path.read_text(encoding="utf-8")))
    except (OSError, json.JSONDecodeError):
        ErrorBus.raise_(
            SCHOOL.BAMF_ATLAS_ADMISSION.INVALID,
            reason="BAMF_GENERATED_GRADE_ISSUANCE_INVALID",
        )
    if result.proposal_sha256 != proposal_sha256:
        ErrorBus.raise_(
            SCHOOL.BAMF_ATLAS_ADMISSION.INVALID,
            reason="BAMF_GENERATED_GRADE_ISSUANCE_INVALID",
        )
    return result


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
    proposal = synthesize_generated_grade(
        state.epoch.snapshot, state.epoch.closure,
        state.epoch.current_release, inputs)
    _persist_issued_proposal(supervisor.run_dir, proposal)
    return proposal


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
    issued_proposal = _read_issued_proposal(run_dir, proposal.proposal_sha256)
    if issued_proposal != proposal:
        ErrorBus.raise_(
            SCHOOL.BAMF_ATLAS_ADMISSION.INVALID,
            reason="BAMF_GENERATED_GRADE_ACCEPTED_PROPOSAL_MISMATCH",
        )
    lineage = _accepted_release_lineage(run_dir, proposal)
    return _seal_generated_grade(
        proposal, lineage[-1], release_lineage=lineage)


__all__ = ("propose_accepted_generated_grade", "seal_accepted_generated_grade")
