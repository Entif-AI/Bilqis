"""Exact generation-zero retry and interrupted-pointer recovery."""
from __future__ import annotations

import json
from pathlib import Path

from bilqis_mlx.data_plane import DataPlaneError, SHA256_HEX_LENGTH
from bilqis_mlx.learning.atlas_acceptance import (
    AcceptedCandidateBinding, ParsedAcceptedCandidateBinding,
)
from bilqis_mlx.learning._atlas_candidate.identity_binding import (
    candidate_identity_for_canonical_consumer,
)

from ..atlas_admission import AtlasAdmissionBinding, ParsedAtlasAdmissionBinding
from ..factory_release.admission import (
    FactoryReleaseAdmissionBinding,
    ParsedFactoryReleaseAdmissionBinding,
)
from ..codec import load_bamf_bundle
from ..records import (
    BAMF_POINTER_SCHEMA, BamfBundleCandidate, canonical, invalid, sha, sidecar_records,
)
from .authority import (
    authenticate_current_successor_retry,
    load_generation_locked as _load_generation_locked_impl,
    require_published_acceptance as _require_published_acceptance_impl,
)
from .events import reconcile_bamf_outbox
from .factory_release import (
    persist_prepared_initial_factory_release,
    require_initial_factory_release,
)
from .storage import (
    _atomic_pointer, _live_bundle_manifest, _pointer_lock, _read_pointer,
    _initial_generation_pointer_lock, _remove_stage, _write_acceptance,
    _write_parsed_initial_generation_acceptance,
)


def _same_initial_candidate(student, candidate: BamfBundleCandidate) -> bool:
    return (
        student.run_id == candidate.run_id
        and student.generation == candidate.generation == 0
        and student.parent_manifest_sha256 is candidate.parent_manifest_sha256 is None
        and student.implementation_sha256 == candidate.implementation_sha256
        and student.topology == candidate.topology
        and student.extents == candidate.extents
        and candidate_identity_for_canonical_consumer(student.retained_state)
        == candidate_identity_for_canonical_consumer(candidate.retained_state)
        and student.provenance == candidate.provenance
        and student.transition == candidate.transition
        and student.run_identity == candidate.run_identity
        and student.optimizer_hyperparameters == candidate.optimizer_hyperparameters
        and sidecar_records(student) == sidecar_records(candidate)
    )


def _recovery_pointer(run_dir: Path, manifest_sha256: str, prepared) -> dict:
    return {
        "schema": BAMF_POINTER_SCHEMA,
        "run_id": prepared.candidate.run_id,
        "generation": 0,
        "parent_manifest_sha256": None,
        "bundle": f"bamf-bundles/{manifest_sha256}",
        "manifest_sha256": manifest_sha256,
        "acceptance_sha256": prepared.binding.digest,
    }


def _prepared_unsealed_manifest(run_dir: Path, prepared, load_bundle) -> str | None:
    """Find the one exact unsealed generation-zero bundle under prepared authority."""
    root = run_dir / "bamf-bundles"
    if not root.exists() and not root.is_symlink():
        return None
    if root.is_symlink() or not root.is_dir():
        invalid(DataPlaneError.BUNDLE_ENTRY_UNSAFE)
    entries = tuple(root.iterdir())
    if len(entries) != 1:
        invalid(DataPlaneError.BUNDLE_IDENTITY_CONFLICT)
    target = entries[0]
    manifest_sha256 = target.name
    if (target.is_symlink() or not target.is_dir()
            or len(manifest_sha256) != SHA256_HEX_LENGTH
            or any(char not in "0123456789abcdef" for char in manifest_sha256)):
        invalid(DataPlaneError.BUNDLE_IDENTITY_CONFLICT)
    student = load_bundle(target, expected_manifest_sha256=manifest_sha256)
    if not _same_initial_candidate(student, prepared.candidate):
        invalid(DataPlaneError.BUNDLE_IDENTITY_CONFLICT)
    return manifest_sha256


def _unpointed_initial_generation_retry(
        run_dir: Path, prepared, *, load_bundle, require_published_acceptance,
        atomic_pointer, reconcile, sealed_manifest, write_acceptance):
    """Recover an exact durable genesis whose pointer install was interrupted."""
    manifest_sha256 = sealed_manifest(prepared)
    if manifest_sha256 is None:
        manifest_sha256 = _prepared_unsealed_manifest(
            run_dir, prepared, load_bundle)
        if manifest_sha256 is None:
            return None
    target = run_dir / "bamf-bundles" / manifest_sha256
    if not target.exists() and not target.is_symlink():
        return None
    student = load_bundle(target, expected_manifest_sha256=manifest_sha256)
    pointer = _recovery_pointer(run_dir, manifest_sha256, prepared)
    if not _same_initial_candidate(student, prepared.candidate):
        invalid(DataPlaneError.BUNDLE_IDENTITY_CONFLICT)
    persist_prepared_initial_factory_release(run_dir, prepared)
    from .genesis_trust import publish_initial_generation_trust_root
    publish_initial_generation_trust_root(run_dir, prepared, manifest_sha256)
    write_acceptance(run_dir, manifest_sha256, prepared.binding)
    acceptance = require_published_acceptance(run_dir, pointer, student)
    if (acceptance.digest != prepared.binding.digest
            or not _same_initial_candidate(student, prepared.candidate)):
        invalid(DataPlaneError.BUNDLE_IDENTITY_CONFLICT)
    atomic_pointer(run_dir / "bamf-state.json", pointer)
    reconcile(run_dir, student)
    return pointer


def existing_initial_generation_retry(
        run_dir: Path, candidate: BamfBundleCandidate, prepared, *,
        pointer_lock, read_pointer, load_generation_locked,
        require_published_acceptance, load_bundle, atomic_pointer, reconcile,
        sealed_manifest, write_acceptance):
    """Converge only the exact live-capability genesis already sealed by B13."""
    run_dir = Path(run_dir)
    pointer_path = run_dir / "bamf-state.json"
    with pointer_lock(run_dir):
        current = read_pointer(pointer_path)
        if current is None:
            return _unpointed_initial_generation_retry(
                run_dir, prepared, load_bundle=load_bundle,
                require_published_acceptance=require_published_acceptance,
                atomic_pointer=atomic_pointer, reconcile=reconcile,
                sealed_manifest=sealed_manifest,
                write_acceptance=write_acceptance)
        if (current.get("schema") != BAMF_POINTER_SCHEMA
                or current.get("run_id") != candidate.run_id
                or current.get("generation") != 0
                or current.get("parent_manifest_sha256") is not None
                or current.get("acceptance_sha256") != prepared.binding.digest):
            invalid(DataPlaneError.BUNDLE_IDENTITY_CONFLICT)
        student, locked_pointer = load_generation_locked(pointer_path)
        if locked_pointer != current:
            invalid(DataPlaneError.BUNDLE_IDENTITY_CONFLICT)
        acceptance = require_published_acceptance(run_dir, current, student)
        if (acceptance.digest != prepared.binding.digest
                or not _same_initial_candidate(student, candidate)):
            invalid(DataPlaneError.BUNDLE_IDENTITY_CONFLICT)
        require_initial_factory_release(run_dir, student)
        reconcile(run_dir, student)
        return current


def _require_published_acceptance(run_dir: Path, pointer: dict, student):
    return _require_published_acceptance_impl(
        run_dir, pointer, student,
        load_bundle=load_bamf_bundle, live_manifest=_live_bundle_manifest)


def _load_generation_locked(pointer_path: Path):
    return _load_generation_locked_impl(
        pointer_path, read_pointer=_read_pointer,
        live_manifest=_live_bundle_manifest, load_bundle=load_bamf_bundle)


def _existing_initial_generation_retry(
        run_dir: Path, candidate: BamfBundleCandidate, prepared):
    """Converge an exact sealed genesis retry without depending on mutable upstream."""
    from .genesis_trust import sealed_initial_generation_manifest

    return existing_initial_generation_retry(
        run_dir, candidate, prepared,
        pointer_lock=_initial_generation_pointer_lock, read_pointer=_read_pointer,
        load_generation_locked=_load_generation_locked,
        require_published_acceptance=_require_published_acceptance,
        load_bundle=load_bamf_bundle, atomic_pointer=_atomic_pointer,
        reconcile=reconcile_bamf_outbox,
        sealed_manifest=sealed_initial_generation_manifest,
        write_acceptance=_write_acceptance)


def recover_prepared_initial_generation(run_dir: Path, prepared):
    """Converge exact prepared generation zero before or after trust sealing."""
    return _existing_initial_generation_retry(
        Path(run_dir), prepared.candidate, prepared)


def _sealed_genesis_student(
        run_dir: Path, manifest_sha256: str, *, expected_run_id: str,
        expected_run_seed: int, expected_topology_digest: str,
        expected_atlas_artifact, expected_optimizer_hyperparameters_sha256: str):
    from ..genesis import validate_initial_generation_source_authority
    from ..genesis.records import optimizer_hyperparameters_digest

    target = run_dir / "bamf-bundles" / manifest_sha256
    if target.is_symlink() or not target.is_dir():
        invalid(DataPlaneError.BUNDLE_IDENTITY_CONFLICT)
    student = load_bamf_bundle(
        target, expected_manifest_sha256=manifest_sha256)
    identity = student.run_identity
    feature_source = student.compiler_features.get("feature_source")
    if (identity is None or student.generation != 0
            or student.run_id != expected_run_id
            or identity.run_seed != expected_run_seed
            or student.topology.digest != expected_topology_digest
            or optimizer_hyperparameters_digest(student.optimizer_hyperparameters)
            != expected_optimizer_hyperparameters_sha256
            or not isinstance(feature_source, dict)
            or feature_source.get("atlas_bundle_id") != expected_atlas_artifact.bundle_id
            or feature_source.get("release_sha256") != expected_atlas_artifact.release_sha256
            or feature_source.get("source_bundle_id") != expected_atlas_artifact.source_bundle_id):
        invalid(DataPlaneError.BUNDLE_IDENTITY_CONFLICT)
    validate_initial_generation_source_authority(student)
    return student


def _sealed_genesis_binding(student, expected_acceptance: str):
    from ..genesis.records import (
        INITIAL_BINDING_SCHEMA, InitialGenerationBinding,
        initial_generation_candidate_identity_digest,
        optimizer_hyperparameters_digest,
    )

    fields = {
        "run_id": student.run_id,
        "generation": 0,
        "run_identity_sha256": student.run_identity.digest,
        "candidate_identity_sha256": initial_generation_candidate_identity_digest(student),
        "optimizer_hyperparameters_sha256":
            optimizer_hyperparameters_digest(student.optimizer_hyperparameters),
        "feature_sha256": student.extents.factor_map_digest,
        "optimizer_step": student.retained_state.optimizer_step,
        "schema_version": INITIAL_BINDING_SCHEMA,
    }
    binding = InitialGenerationBinding.from_record(
        {**fields, "binding_sha256": sha(canonical(fields))})
    if binding.digest != expected_acceptance or binding.optimizer_step != 0:
        invalid("BAMF_INITIAL_GENERATION_TRUST_ROOT_INVALID")
    return binding


def recover_sealed_initial_generation(
        run_dir: Path, *, expected_run_id: str, expected_run_seed: int,
        expected_topology_digest: str, expected_atlas_artifact,
        expected_optimizer_hyperparameters_sha256: str):
    """Recover sealed generation zero without replaying mutable Factory authority."""
    from .genesis_trust import require_initial_generation_trust_root, _stored_trust

    run_dir = Path(run_dir)
    pointer_path = run_dir / "bamf-state.json"
    with _pointer_lock(run_dir):
        if _read_pointer(pointer_path) is not None:
            return None
        stored = _stored_trust(expected_run_id)
        if stored is None:
            return None
        generation, manifest_sha256, payload_sha256, raw = stored
        if generation != 0 or payload_sha256 != sha(raw):
            invalid("BAMF_INITIAL_GENERATION_TRUST_ROOT_INVALID")
        try:
            trust = json.loads(raw)
        except (UnicodeDecodeError, json.JSONDecodeError):
            invalid("BAMF_INITIAL_GENERATION_TRUST_ROOT_INVALID")
        student = _sealed_genesis_student(
            run_dir, manifest_sha256, expected_run_id=expected_run_id,
            expected_run_seed=expected_run_seed,
            expected_topology_digest=expected_topology_digest,
            expected_atlas_artifact=expected_atlas_artifact,
            expected_optimizer_hyperparameters_sha256=
                expected_optimizer_hyperparameters_sha256)
        require_initial_factory_release(run_dir, student)
        expected_acceptance = trust.get("acceptance_sha256")
        binding = _sealed_genesis_binding(student, expected_acceptance)
        pointer = {
            "schema": BAMF_POINTER_SCHEMA,
            "run_id": student.run_id,
            "generation": 0,
            "parent_manifest_sha256": None,
            "bundle": f"bamf-bundles/{manifest_sha256}",
            "manifest_sha256": manifest_sha256,
            "acceptance_sha256": binding.digest,
        }
        require_initial_generation_trust_root(pointer, student, binding)
        _write_parsed_initial_generation_acceptance(
            run_dir, manifest_sha256, binding,
            expected_acceptance_sha256=expected_acceptance)
        persisted = _require_published_acceptance(run_dir, pointer, student)
        if persisted.digest != binding.digest:
            invalid("BAMF_GENERATION_ACCEPTANCE_DRIFT")
        _atomic_pointer(pointer_path, pointer)
        reconcile_bamf_outbox(run_dir, student)
        return pointer


def _require_retry_acceptance_family(authority, persisted) -> None:
    if type(authority) is AcceptedCandidateBinding:
        valid = isinstance(persisted, ParsedAcceptedCandidateBinding)
    elif type(authority) is AtlasAdmissionBinding:
        valid = isinstance(persisted, ParsedAtlasAdmissionBinding)
    elif type(authority) is FactoryReleaseAdmissionBinding:
        valid = isinstance(persisted, ParsedFactoryReleaseAdmissionBinding)
    else:
        valid = False
    if (not valid or persisted.digest != authority.digest
            or persisted.schema_version != authority.schema_version):
        invalid("BAMF_GENERATION_ACCEPTANCE_DRIFT")


def reconcile_already_pointed_retry(
        run_dir, current, candidate, authority, prepared, digest, stage, *,
        require_successor_source_authority):
    if (current["run_id"] != candidate.run_id
            or current["manifest_sha256"] != digest
            or current["parent_manifest_sha256"] != candidate.parent_manifest_sha256
            or current["schema"] != BAMF_POINTER_SCHEMA
            or current["acceptance_sha256"] != authority.digest):
        invalid(DataPlaneError.BUNDLE_IDENTITY_CONFLICT)
    student = load_bamf_bundle(
        run_dir / current["bundle"], expected_manifest_sha256=digest)
    if prepared is not None:
        from .genesis_trust import require_initial_generation_trust_root
        require_initial_factory_release(run_dir, student)
        require_initial_generation_trust_root(current, student, authority)
    else:
        parent, persisted = authenticate_current_successor_retry(
            run_dir, current, candidate, student,
            load_bundle=load_bamf_bundle,
            require_published_acceptance=_require_published_acceptance,
        )
        _require_retry_acceptance_family(authority, persisted)
        require_successor_source_authority(run_dir, parent, student, authority)
    _remove_stage(stage)
    _write_acceptance(run_dir, digest, authority)
    reconcile_bamf_outbox(run_dir, student)
    return current
