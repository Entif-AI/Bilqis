"""Accepted-run #1320 proposal and definition authority."""
from __future__ import annotations

import json
import os
from pathlib import Path
import tempfile
from dataclasses import dataclass

from bilqis_mlx.errors import ErrorBus, SCHOOL
from bilqis_mlx.factory.generated_grade import GeneratedGradeProposal, synthesize_generated_grade
from bilqis_mlx.factory.generated_grade.definition import _seal_generated_grade
from bilqis_mlx.factory.generated_grade.inputs import _compile_generated_grade_inputs
from bilqis_mlx.runtime.bamf_bundle.publication import _fsync_directory

from .atlas_admission import read_accepted_atlas_factory_release

_GENERATED_GRADE_AUTHORITY_ISSUER = object()


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


def _proposal_path(run_dir: Path, proposal_sha256: str) -> Path:
    return Path(run_dir) / "generated-grade-proposals" / f"{proposal_sha256}.json"


def _persist_issued_proposal(run_dir: Path, proposal: GeneratedGradeProposal) -> None:
    """Persist the #1320-issued proposal as immutable content-addressed custody."""
    target = _proposal_path(run_dir, proposal.proposal_sha256)
    parent_existed = target.parent.exists()
    target.parent.mkdir(parents=True, exist_ok=True)
    if not parent_existed:
        _fsync_directory(target.parent)
        _fsync_directory(Path(run_dir))
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
        _fsync_directory(target.parent)


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


def _recompute_current_accepted_proposal(run_dir: Path) -> GeneratedGradeProposal:
    from .atlas_flywheel_runtime import AcceptedAtlasFlywheelSupervisor
    return _recompute_accepted_generated_grade(
        AcceptedAtlasFlywheelSupervisor(Path(run_dir), None))


def _proposal_bound_in_accepted_ancestry(
    run_dir: Path, proposal: GeneratedGradeProposal,
) -> bool:
    """Authenticate a predecessor proposal through accepted B13/C07 ancestry."""
    from bilqis_mlx.runtime.bamf_bundle.atlas_admission import (
        ATLAS_ADMISSION_SCHEMA_V3,
        ParsedAtlasAdmissionBinding,
    )
    from bilqis_mlx.runtime.bamf_bundle.codec import load_bamf_bundle
    from bilqis_mlx.runtime.bamf_bundle.factory_release.admission import (
        FACTORY_RELEASE_ADMISSION_SCHEMA_V3,
        ParsedFactoryReleaseAdmissionBinding,
    )
    from bilqis_mlx.runtime.bamf_bundle.feature.acceptance import (
        accepted_binding_for_manifest,
        accepted_generation,
        parent_acceptance_anchor_from_manifest,
    )

    root = Path(run_dir)
    pointer, student = accepted_generation(root / "bamf-state.json")
    manifest_sha256 = pointer["manifest_sha256"]
    acceptance_sha256 = pointer["acceptance_sha256"]
    visited = set()
    while student.generation > 0:
        if manifest_sha256 in visited:
            return False
        visited.add(manifest_sha256)
        binding = accepted_binding_for_manifest(
            root, manifest_sha256, student,
            expected_acceptance_sha256=acceptance_sha256)
        if (
            isinstance(binding, ParsedFactoryReleaseAdmissionBinding)
            and binding.schema_version == FACTORY_RELEASE_ADMISSION_SCHEMA_V3
            and binding.predecessor_factory_release_sha256
                == proposal.current_release_sha256
            and binding.proposal_sha256 == proposal.a09_proposal_sha256
            and binding.generated_grade_proposal_sha256
                == proposal.proposal_sha256
        ):
            return True
        if (
            isinstance(binding, ParsedAtlasAdmissionBinding)
            and binding.schema_version == ATLAS_ADMISSION_SCHEMA_V3
            and binding.predecessor_factory_release_sha256
                == proposal.current_release_sha256
            and binding.proposal_sha256 == proposal.a09_proposal_sha256
            and binding.generated_grade_proposal_sha256
                == proposal.proposal_sha256
        ):
            return True
        parent_manifest = student.parent_manifest_sha256
        parent_acceptance = parent_acceptance_anchor_from_manifest(
            root, manifest_sha256)
        if parent_manifest is None or parent_acceptance is None:
            return False
        student = load_bamf_bundle(
            root / "bamf-bundles" / parent_manifest,
            expected_manifest_sha256=parent_manifest)
        manifest_sha256 = parent_manifest
        acceptance_sha256 = parent_acceptance
    return False


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
