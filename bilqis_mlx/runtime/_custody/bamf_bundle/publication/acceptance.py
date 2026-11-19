"""Persisted B13 acceptance parsing and lineage validation."""
from __future__ import annotations

import json
from pathlib import Path

from bilqis_mlx.data_plane import DataPlaneError
from bilqis_mlx.errors import BilqisError
from bilqis_mlx.learning.atlas_acceptance import (
    ACCEPTANCE_SCHEMA, MOTIF_ACCEPTANCE_SCHEMA, CLOSURE_ACCEPTANCE_SCHEMA,
    MOTIF_CLOSURE_ACCEPTANCE_SCHEMA, EXACT_ACCEPTANCE_SCHEMA,
    EXACT_CLOSURE_ACCEPTANCE_SCHEMA, EXACT_MOTIF_ACCEPTANCE_SCHEMA,
    EXACT_MOTIF_CLOSURE_ACCEPTANCE_SCHEMA, AcceptedCandidateBinding,
)
from bilqis_mlx.learning._atlas_candidate.identity_binding import (
    bind_candidate_identity_or_fallback,
)

from ..atlas_admission import (
    ATLAS_ADMISSION_SCHEMAS, AtlasAdmissionBinding, ParsedAtlasAdmissionBinding,
    validate_parsed_atlas_championship_state,
)
from ..factory_release.admission import (
    FACTORY_RELEASE_ADMISSION_SCHEMAS,
    FactoryReleaseAdmissionBinding,
    ParsedFactoryReleaseAdmissionBinding,
    validate_parsed_factory_release_admission_binding,
)
from ..motif.transition import is_motif_allocation_transition
from ..records import (
    ACCEPTANCE_BOUND_BAMF_BUNDLE_SCHEMA, BAMF_POINTER_SCHEMA,
    CompleteStudent, OBJECTIVE_ACCEPTANCE_BOUND_BAMF_BUNDLE_SCHEMA, invalid,
)
from .storage import ACCEPTANCE_DIR


def require_accepted_parent(
        run_dir: Path, candidate, acceptance, *, load_bundle,
        parent: CompleteStudent | None = None) -> None:
    """Verify the C05 parent identity against immutable B13 parent custody."""
    if candidate.generation == 0:
        return
    parent_sha = candidate.parent_manifest_sha256
    if parent_sha is None:
        invalid("BAMF_GENERATION_ACCEPTANCE_DRIFT")
    if parent is None:
        parent = load_bundle(
            run_dir / "bamf-bundles" / parent_sha,
            expected_manifest_sha256=parent_sha)
    elif type(parent) is not CompleteStudent:
        invalid("BAMF_GENERATION_ACCEPTANCE_DRIFT")
    parent_digest = bind_candidate_identity_or_fallback(
        parent.retained_state, parent.topology.digest, parent.extents.digest,
        expected_digest=acceptance.parent_candidate_identity_sha256)
    if (parent.run_id != candidate.run_id
            or parent.generation + 1 != candidate.generation
            or parent.run_identity != candidate.run_identity
            or acceptance.parent_candidate_identity_sha256 != parent_digest):
        invalid("BAMF_GENERATION_ACCEPTANCE_DRIFT")
    vocabulary_changed = (
        parent.extents.semantic_bank_count != candidate.extents.semantic_bank_count
        or parent.extents.active_semantic_digest
        != candidate.extents.active_semantic_digest)
    if vocabulary_changed and type(acceptance) is not AtlasAdmissionBinding:
        invalid("BAMF_ATLAS_ADMISSION_EXECUTOR_REQUIRED")


def load_generation_locked(
        pointer_path: Path, *, read_pointer, live_manifest,
        load_bundle) -> tuple[CompleteStudent, dict]:
    pointer = read_pointer(pointer_path)
    if pointer is None:
        invalid(DataPlaneError.BUNDLE_ROOT_UNSAFE)
    live_manifest(pointer_path.parent, pointer)
    student = load_bundle(
        pointer_path.parent / "bamf-bundles" / pointer["manifest_sha256"],
        expected_manifest_sha256=pointer["manifest_sha256"])
    if (student.run_id != pointer["run_id"] or student.generation != pointer["generation"]
            or student.parent_manifest_sha256 != pointer["parent_manifest_sha256"]):
        invalid(DataPlaneError.BUNDLE_PAYLOAD_DRIFT)
    return student, pointer


def _read_published_acceptance_record(run_dir: Path, pointer: dict) -> dict:
    acceptance_path = (
        Path(run_dir) / ACCEPTANCE_DIR / f"{pointer['manifest_sha256']}.json")
    if acceptance_path.is_symlink() or not acceptance_path.is_file():
        invalid("BAMF_GENERATION_ACCEPTANCE_MISSING")
    try:
        return json.loads(acceptance_path.read_bytes())
    except (OSError, UnicodeDecodeError, json.JSONDecodeError):
        invalid("BAMF_GENERATION_ACCEPTANCE_INVALID")


def _parse_published_acceptance(student, pointer, record):
    if student.generation == 0:
        try:
            from ..genesis import (
                InitialGenerationBinding,
                validate_parsed_initial_generation_binding,
            )
            acceptance = InitialGenerationBinding.from_record(record)
            validate_parsed_initial_generation_binding(
                student, acceptance, pointer["acceptance_sha256"])
        except BilqisError:
            invalid("BAMF_GENERATION_ACCEPTANCE_INVALID")
        return acceptance
    if record.get("schema_version") in FACTORY_RELEASE_ADMISSION_SCHEMAS:
        acceptance = FactoryReleaseAdmissionBinding.from_record(record)
        validate_parsed_factory_release_admission_binding(
            student, acceptance, pointer["acceptance_sha256"])
        return acceptance
    try:
        return (
            AtlasAdmissionBinding.from_record(record)
            if record.get("schema_version") in ATLAS_ADMISSION_SCHEMAS
            else AcceptedCandidateBinding.from_record(record))
    except BilqisError:
        invalid("BAMF_GENERATION_ACCEPTANCE_INVALID")


def _require_non_genesis_acceptance_identity(acceptance, pointer, student) -> None:
    from bilqis_mlx.learning._atlas_candidate.identity_binding import bind_candidate_identity
    candidate_digest = bind_candidate_identity_or_fallback(
        student.retained_state, student.topology.digest, student.extents.digest,
        expected_digest=acceptance.candidate_identity_sha256)
    if (acceptance.digest != pointer["acceptance_sha256"]
            or acceptance.run_id != student.run_id
            or acceptance.generation != student.generation
            or acceptance.feature_sha256 != student.extents.factor_map_digest
            or acceptance.optimizer_step != student.retained_state.optimizer_step
            or acceptance.candidate_identity_sha256 != candidate_digest
            or (not isinstance(acceptance, (
                    ParsedAtlasAdmissionBinding,
                    ParsedFactoryReleaseAdmissionBinding))
                and (acceptance.schema_version not in {
                        ACCEPTANCE_SCHEMA, MOTIF_ACCEPTANCE_SCHEMA,
                        CLOSURE_ACCEPTANCE_SCHEMA, MOTIF_CLOSURE_ACCEPTANCE_SCHEMA,
                        EXACT_ACCEPTANCE_SCHEMA, EXACT_CLOSURE_ACCEPTANCE_SCHEMA,
                        EXACT_MOTIF_ACCEPTANCE_SCHEMA,
                        EXACT_MOTIF_CLOSURE_ACCEPTANCE_SCHEMA}
                     or acceptance.step_proof_sha256 != tuple(
                         proof.digest for proof in student.retained_state.step_proofs)
                     or acceptance.source_authority_registry_sha256
                     != student.correction_frontier.get(
                         "source_authority_registry_sha256")))):
        invalid("BAMF_GENERATION_ACCEPTANCE_DRIFT")
    if isinstance(acceptance, ParsedAtlasAdmissionBinding):
        validate_parsed_atlas_championship_state(student, acceptance)
    if is_motif_allocation_transition(student.transition):
        from ..genesis.records import successor_candidate_identity_digest
        if (acceptance.schema_version not in (
                MOTIF_ACCEPTANCE_SCHEMA, MOTIF_CLOSURE_ACCEPTANCE_SCHEMA,
                EXACT_MOTIF_ACCEPTANCE_SCHEMA, EXACT_MOTIF_CLOSURE_ACCEPTANCE_SCHEMA)
                or acceptance.generation_authority_sha256
                != successor_candidate_identity_digest(student)):
            invalid("BAMF_GENERATION_ACCEPTANCE_DRIFT")
    elif (not isinstance(acceptance, (
            ParsedAtlasAdmissionBinding, ParsedFactoryReleaseAdmissionBinding))
          and acceptance.schema_version not in (
              ACCEPTANCE_SCHEMA, CLOSURE_ACCEPTANCE_SCHEMA,
              EXACT_ACCEPTANCE_SCHEMA, EXACT_CLOSURE_ACCEPTANCE_SCHEMA)):
        invalid("BAMF_GENERATION_ACCEPTANCE_DRIFT")

    if (not isinstance(acceptance, (
            ParsedAtlasAdmissionBinding, ParsedFactoryReleaseAdmissionBinding))
            and acceptance.schema_version in (
                EXACT_ACCEPTANCE_SCHEMA, EXACT_CLOSURE_ACCEPTANCE_SCHEMA,
                EXACT_MOTIF_ACCEPTANCE_SCHEMA, EXACT_MOTIF_CLOSURE_ACCEPTANCE_SCHEMA)):
        from ..genesis.records import successor_candidate_identity_digest
        from ..records import canonical, sha
        if (acceptance.generation_authority_sha256
                != successor_candidate_identity_digest(student)
                or acceptance.teacher_state_sha256
                != sha(canonical(dict(student.teacher_state)))):
            invalid("BAMF_GENERATION_ACCEPTANCE_DRIFT")

    if not isinstance(acceptance, (
            ParsedAtlasAdmissionBinding, ParsedFactoryReleaseAdmissionBinding)):
        from bilqis_mlx.learning._retention._atlas_acceptance_records import require_closure_proofs
        require_closure_proofs(acceptance, student.retained_state.step_proofs)


def require_published_acceptance(
        run_dir: Path, pointer: dict, student: CompleteStudent, *,
        load_bundle, live_manifest,
        accepted_parent: tuple[str, CompleteStudent] | None = None):
    """Authenticate the generation-specific acceptance bound by one live pointer."""
    if pointer.get("schema") != BAMF_POINTER_SCHEMA:
        invalid("BAMF_GENERATION_ACCEPTANCE_MISSING")
    record = _read_published_acceptance_record(run_dir, pointer)
    acceptance = _parse_published_acceptance(student, pointer, record)
    if student.generation == 0:
        from .genesis_trust import require_initial_generation_trust_root
        require_initial_generation_trust_root(pointer, student, acceptance)
        return acceptance
    _require_non_genesis_acceptance_identity(acceptance, pointer, student)
    manifest = live_manifest(run_dir, pointer)
    legacy_student = manifest.get("schema") not in {
        ACCEPTANCE_BOUND_BAMF_BUNDLE_SCHEMA,
        OBJECTIVE_ACCEPTANCE_BOUND_BAMF_BUNDLE_SCHEMA,
    }
    parent_sha = student.parent_manifest_sha256
    if parent_sha is None:
        invalid("BAMF_RUN_IDENTITY_DRIFT")
    if accepted_parent is not None and accepted_parent[0] == parent_sha:
        parent = accepted_parent[1]
        if type(parent) is not CompleteStudent:
            invalid("BAMF_RUN_IDENTITY_DRIFT")
    else:
        parent = load_bundle(
            Path(run_dir) / "bamf-bundles" / parent_sha,
            expected_manifest_sha256=parent_sha)
    from bilqis_mlx.learning._atlas_candidate.identity_binding import bind_candidate_identity
    parent_digest = bind_candidate_identity_or_fallback(
        parent.retained_state, parent.topology.digest, parent.extents.digest,
        expected_digest=acceptance.parent_candidate_identity_sha256)
    if (parent.run_id != student.run_id
            or parent.generation + 1 != student.generation
            or (not legacy_student
                and parent.run_identity != student.run_identity)
            or (not is_motif_allocation_transition(student.transition)
                and parent.retained_state.allocations.digest
                != student.retained_state.allocations.digest)
            or acceptance.parent_candidate_identity_sha256 != parent_digest):
        invalid("BAMF_RUN_IDENTITY_DRIFT")
    return acceptance
