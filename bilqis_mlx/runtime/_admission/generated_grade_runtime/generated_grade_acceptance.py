"""#1320 issued-proposal custody and accepted B13/C07 ancestry proof."""
from __future__ import annotations

import json
import os
from pathlib import Path
import tempfile

from bilqis_mlx.errors import ErrorBus, SCHOOL
from bilqis_mlx.factory.generated_grade import GeneratedGradeProposal
from bilqis_mlx.runtime.bamf_bundle.publication import _fsync_directory

from .atlas_admission import read_accepted_atlas_factory_release


def _proposal_path(run_dir: Path, proposal_sha256: str) -> Path:
    return Path(run_dir) / "generated-grade-proposals" / f"{proposal_sha256}.json"


def _persist_issued_proposal(
    run_dir: Path, proposal: GeneratedGradeProposal, *, sync_directory=_fsync_directory,
) -> None:
    """Persist the #1320-issued proposal as immutable content-addressed custody."""
    target = _proposal_path(run_dir, proposal.proposal_sha256)
    parent_existed = target.parent.exists()
    target.parent.mkdir(parents=True, exist_ok=True)
    if not parent_existed:
        sync_directory(target.parent)
        sync_directory(Path(run_dir))
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
        sync_directory(target.parent)


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


def _accepted_release_lineage(
    run_dir: Path, proposal: GeneratedGradeProposal, *,
    accepted_release_reader=read_accepted_atlas_factory_release,
) -> tuple:
    """Cold-read immutable release artifacts back to the proposal predecessor."""
    from .admission import _read_executable_factory_release_artifact
    accepted = accepted_release_reader(run_dir)
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


def _binding_accepts_proposal(binding, proposal: GeneratedGradeProposal) -> bool:
    from bilqis_mlx.runtime.bamf_bundle.atlas_admission import (
        ATLAS_ADMISSION_SCHEMA_V3, ParsedAtlasAdmissionBinding,
    )
    from bilqis_mlx.runtime.bamf_bundle.factory_release.admission import (
        FACTORY_RELEASE_ADMISSION_SCHEMA_V3, ParsedFactoryReleaseAdmissionBinding,
    )
    if isinstance(binding, ParsedFactoryReleaseAdmissionBinding):
        if binding.schema_version != FACTORY_RELEASE_ADMISSION_SCHEMA_V3:
            return False
    elif isinstance(binding, ParsedAtlasAdmissionBinding):
        if binding.schema_version != ATLAS_ADMISSION_SCHEMA_V3:
            return False
    else:
        return False
    return (
        binding.predecessor_factory_release_sha256 == proposal.current_release_sha256
        and binding.proposal_sha256 == proposal.a09_proposal_sha256
        and binding.generated_grade_proposal_sha256 == proposal.proposal_sha256
    )


def _proposal_bound_at_or_before_accepted_generation(
    run_dir: Path, proposal: GeneratedGradeProposal, *, run_id: str,
    generation: int, manifest_sha256: str, acceptance_sha256: str,
) -> bool:
    """Authenticate a proposal in accepted B13 ancestry no later than activation."""
    from bilqis_mlx.runtime.bamf_bundle.codec import load_bamf_bundle
    from bilqis_mlx.runtime.bamf_bundle.feature.acceptance import (
        accepted_binding_for_manifest, parent_acceptance_anchor_from_manifest,
    )
    root = Path(run_dir)
    student = load_bamf_bundle(
        root / "bamf-bundles" / manifest_sha256,
        expected_manifest_sha256=manifest_sha256,
    )
    if student.run_id != run_id or student.generation != generation:
        return False
    manifest, acceptance, visited = manifest_sha256, acceptance_sha256, set()
    while student.generation > 0:
        if manifest in visited:
            return False
        visited.add(manifest)
        binding = accepted_binding_for_manifest(
            root, manifest, student, expected_acceptance_sha256=acceptance)
        if _binding_accepts_proposal(binding, proposal):
            return True
        parent_manifest = student.parent_manifest_sha256
        parent_acceptance = parent_acceptance_anchor_from_manifest(root, manifest)
        if parent_manifest is None or parent_acceptance is None:
            return False
        student = load_bamf_bundle(
            root / "bamf-bundles" / parent_manifest,
            expected_manifest_sha256=parent_manifest)
        manifest, acceptance = parent_manifest, parent_acceptance
    return False


def _proposal_bound_in_accepted_ancestry(
    run_dir: Path, proposal: GeneratedGradeProposal,
) -> bool:
    """Authenticate a predecessor proposal through current accepted B13 ancestry."""
    from bilqis_mlx.runtime.bamf_bundle.feature.acceptance import accepted_generation
    pointer, student = accepted_generation(Path(run_dir) / "bamf-state.json")
    return _proposal_bound_at_or_before_accepted_generation(
        run_dir, proposal,
        run_id=student.run_id,
        generation=student.generation,
        manifest_sha256=pointer["manifest_sha256"],
        acceptance_sha256=pointer["acceptance_sha256"],
    )
