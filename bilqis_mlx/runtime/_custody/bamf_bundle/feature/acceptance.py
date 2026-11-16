"""Historical acceptance verification for B13 feature-lineage replay."""
from __future__ import annotations

import json
from pathlib import Path

from bilqis_mlx.errors import BilqisError
from bilqis_mlx.learning.atlas_acceptance import (
    ACCEPTANCE_SCHEMA, CLOSURE_ACCEPTANCE_SCHEMA, MOTIF_CLOSURE_ACCEPTANCE_SCHEMA,
    EXACT_ACCEPTANCE_SCHEMA, EXACT_CLOSURE_ACCEPTANCE_SCHEMA,
    EXACT_MOTIF_ACCEPTANCE_SCHEMA, EXACT_MOTIF_CLOSURE_ACCEPTANCE_SCHEMA,
    AcceptedCandidateBinding, candidate_identity_digest,
)

from ..atlas_admission import (
    ATLAS_ADMISSION_SCHEMAS, AtlasAdmissionBinding, ParsedAtlasAdmissionBinding,
)
from ..factory_release.admission import (
    FACTORY_RELEASE_ADMISSION_SCHEMAS,
    FactoryReleaseAdmissionBinding,
    ParsedFactoryReleaseAdmissionBinding,
    validate_parsed_factory_release_admission_binding,
)
from ..codec import load_bamf_bundle
from ..publication import ACCEPTANCE_DIR, _pointer_lock, _read_pointer
from ..records import (
    ACCEPTANCE_BOUND_BAMF_BUNDLE_SCHEMA, BAMF_BUNDLE_SCHEMA,
    BamfGenerationManifest, invalid, sha,
)
from .receipt import is_digest


def accepted_generation(pointer_path: Path):
    """Read the published accepted generation under the custody pointer lock."""
    pointer_path = Path(pointer_path)
    with _pointer_lock(pointer_path.parent):
        pointer = _read_pointer(pointer_path)
        if pointer is None:
            invalid("BAMF_FEATURE_POINTER_MISSING")
        student = load_bamf_bundle(
            pointer_path.parent / "bamf-bundles" / pointer["manifest_sha256"],
            expected_manifest_sha256=pointer["manifest_sha256"])
        if (student.run_id != pointer["run_id"]
                or student.generation != pointer["generation"]
                or student.parent_manifest_sha256 != pointer["parent_manifest_sha256"]):
            invalid("BAMF_FEATURE_POINTER_DRIFT")
    return pointer, student


def _require_retention_binding(student, binding) -> None:
    if isinstance(binding, (ParsedAtlasAdmissionBinding, ParsedFactoryReleaseAdmissionBinding)):
        return
    if (binding.schema_version not in (
            ACCEPTANCE_SCHEMA, CLOSURE_ACCEPTANCE_SCHEMA,
            MOTIF_CLOSURE_ACCEPTANCE_SCHEMA, EXACT_ACCEPTANCE_SCHEMA,
            EXACT_CLOSURE_ACCEPTANCE_SCHEMA, EXACT_MOTIF_ACCEPTANCE_SCHEMA,
            EXACT_MOTIF_CLOSURE_ACCEPTANCE_SCHEMA)
            or binding.step_proof_sha256 != tuple(
                proof.digest for proof in student.retained_state.step_proofs)):
        invalid("BAMF_GENERATION_ACCEPTANCE_DRIFT")
    from bilqis_mlx.learning._retention._atlas_acceptance_records import require_closure_proofs
    from ..motif.transition import is_motif_allocation_transition
    if ((binding.schema_version in (
            MOTIF_CLOSURE_ACCEPTANCE_SCHEMA, EXACT_MOTIF_ACCEPTANCE_SCHEMA,
            EXACT_MOTIF_CLOSURE_ACCEPTANCE_SCHEMA))
            != is_motif_allocation_transition(student.transition)):
        invalid("BAMF_GENERATION_ACCEPTANCE_DRIFT")
    if binding.schema_version in (
            CLOSURE_ACCEPTANCE_SCHEMA, MOTIF_CLOSURE_ACCEPTANCE_SCHEMA,
            EXACT_CLOSURE_ACCEPTANCE_SCHEMA, EXACT_MOTIF_CLOSURE_ACCEPTANCE_SCHEMA):
        if binding.source_authority_registry_sha256 != student.correction_frontier.get(
                "source_authority_registry_sha256"):
            invalid("BAMF_GENERATION_ACCEPTANCE_DRIFT")
    if binding.schema_version in (
            MOTIF_CLOSURE_ACCEPTANCE_SCHEMA, EXACT_ACCEPTANCE_SCHEMA,
            EXACT_CLOSURE_ACCEPTANCE_SCHEMA, EXACT_MOTIF_ACCEPTANCE_SCHEMA,
            EXACT_MOTIF_CLOSURE_ACCEPTANCE_SCHEMA):
        from ..genesis.records import successor_candidate_identity_digest
        if binding.generation_authority_sha256 != successor_candidate_identity_digest(student):
            invalid("BAMF_GENERATION_ACCEPTANCE_DRIFT")
    if binding.schema_version in (
            EXACT_ACCEPTANCE_SCHEMA, EXACT_CLOSURE_ACCEPTANCE_SCHEMA,
            EXACT_MOTIF_ACCEPTANCE_SCHEMA, EXACT_MOTIF_CLOSURE_ACCEPTANCE_SCHEMA):
        from ..records import canonical
        if binding.teacher_state_sha256 != sha(canonical(dict(student.teacher_state))):
            invalid("BAMF_GENERATION_ACCEPTANCE_DRIFT")
    require_closure_proofs(binding, student.retained_state.step_proofs)


def accepted_binding_for_manifest(
        run_dir: Path, manifest_sha256: str, student, *,
        expected_acceptance_sha256: str):
    """Authenticate one immutable generation's generation-specific acceptance."""
    path = run_dir / ACCEPTANCE_DIR / f"{manifest_sha256}.json"
    if path.is_symlink() or not path.is_file():
        invalid("BAMF_GENERATION_ACCEPTANCE_MISSING")
    try:
        record = json.loads(path.read_bytes())
    except (UnicodeDecodeError, json.JSONDecodeError):
        invalid("BAMF_GENERATION_ACCEPTANCE_INVALID")
    if student.generation == 0:
        try:
            from ..genesis import (
                InitialGenerationBinding,
                validate_parsed_initial_generation_binding,
            )
            binding = InitialGenerationBinding.from_record(record)
            validate_parsed_initial_generation_binding(
                student, binding, expected_acceptance_sha256)
        except BilqisError:
            invalid("BAMF_GENERATION_ACCEPTANCE_INVALID")
        return binding
    schema = record.get("schema_version")
    if schema in FACTORY_RELEASE_ADMISSION_SCHEMAS:
        binding = FactoryReleaseAdmissionBinding.from_record(record)
    else:
        try:
            binding = (
                AtlasAdmissionBinding.from_record(record)
                if schema in ATLAS_ADMISSION_SCHEMAS
                else AcceptedCandidateBinding.from_record(record))
        except BilqisError:
            invalid("BAMF_GENERATION_ACCEPTANCE_INVALID")
    if schema in FACTORY_RELEASE_ADMISSION_SCHEMAS:
        validate_parsed_factory_release_admission_binding(
            student, binding, expected_acceptance_sha256)
    if (binding.digest != expected_acceptance_sha256
            or binding.run_id != student.run_id
            or binding.generation != student.generation
            or binding.feature_sha256 != student.extents.factor_map_digest
            or binding.optimizer_step != student.retained_state.optimizer_step
            or binding.candidate_identity_sha256
            != candidate_identity_digest(student.retained_state)):
        invalid("BAMF_GENERATION_ACCEPTANCE_DRIFT")
    _require_retention_binding(student, binding)
    parent_anchor = parent_acceptance_anchor_from_manifest(
        run_dir, manifest_sha256)
    parent_sha = student.parent_manifest_sha256
    if parent_sha is None:
        invalid("BAMF_GENERATION_ACCEPTANCE_DRIFT")
    parent = load_bamf_bundle(
        run_dir / "bamf-bundles" / parent_sha,
        expected_manifest_sha256=parent_sha)
    if (parent.generation + 1 != student.generation
            or parent.run_id != student.run_id
            or (parent_anchor is not None
                and parent.run_identity != student.run_identity)
            or binding.parent_candidate_identity_sha256
            != candidate_identity_digest(parent.retained_state)):
        invalid("BAMF_GENERATION_ACCEPTANCE_DRIFT")
    return binding

def parent_acceptance_anchor_from_manifest(
        run_dir: Path, manifest_sha256: str) -> str | None:
    """Read a v3 parent-acceptance anchor; v2 marks the legacy cutover boundary."""
    path = run_dir / "bamf-bundles" / manifest_sha256 / "manifest.json"
    if path.is_symlink() or not path.is_file():
        invalid("BAMF_GENERATION_ACCEPTANCE_MISSING")
    raw = path.read_bytes()
    if sha(raw) != manifest_sha256:
        invalid("BAMF_GENERATION_ACCEPTANCE_DRIFT")
    try:
        manifest = BamfGenerationManifest.from_record(json.loads(raw)).to_record()
    except (UnicodeDecodeError, json.JSONDecodeError, BilqisError):
        invalid("BAMF_GENERATION_ACCEPTANCE_INVALID")
    if manifest.get("schema") == BAMF_BUNDLE_SCHEMA:
        return None
    parent_acceptance = manifest.get("parent_acceptance_sha256")
    if (manifest.get("schema") != ACCEPTANCE_BOUND_BAMF_BUNDLE_SCHEMA
            or not is_digest(parent_acceptance)):
        invalid("BAMF_GENERATION_ACCEPTANCE_MISSING")
    return parent_acceptance
