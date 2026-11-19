"""Content-addressed B13.1 immutable bundle codec."""
from __future__ import annotations

import json
import os
from dataclasses import asdict, dataclass
from pathlib import Path

import bilqis_mlx.runtime.mlx_checkpoint as _mlx_checkpoint
from bilqis_mlx.data_plane import DataPlaneError, data_plane
from bilqis_mlx.runtime.disk import assert_headroom
from bilqis_mlx.learning._retention._atlas_candidate.identity import (
    IDENTITY_SCHEMES, LEGACY_IDENTITY_SCHEME,
)
from .records import (
    ACCEPTANCE_BOUND_BAMF_BUNDLE_SCHEMA, BAMF_BUNDLE_SCHEMA,
    OBJECTIVE_ACCEPTANCE_BOUND_BAMF_BUNDLE_SCHEMA,
    OBJECTIVE_BOUND_BAMF_BUNDLE_SCHEMA, SIDECARS,
    BamfBundleCandidate,
    BamfGenerationManifest, CompleteStudent,
    canonical, invalid, sha, sidecar_records, validate_sidecars,
)


@dataclass(frozen=True)
class _ValidatedBundleParts:
    """One custody-validated bundle read, before CandidateState rehydration."""

    manifest: dict
    spec: object
    extents: object
    provenance: object
    records: dict
    hp: object
    numerical: object
    motif: object
    policy: object
    optimizer_step: int
    run_identity: object | None


def _write_file(path: Path, raw: bytes) -> str:
    with path.open("xb") as stream:
        stream.write(raw)
        from .publication.instrumentation import note_write
        note_write(len(raw))
        stream.flush()
        os.fsync(stream.fileno())
        from .publication.instrumentation import note_fsync
        note_fsync(len(raw))
    return sha(raw)


_UNBOUND_PARENT_ACCEPTANCE = object()


def save_bamf_bundle(candidate: BamfBundleCandidate, destination: Path, *,
                     reserve_gib: float = 100.0,
                     parent_acceptance_sha256=_UNBOUND_PARENT_ACCEPTANCE) -> dict:
    """Write and read back one immutable generation without publishing it.

    Publication passes the exact accepted-parent digest explicitly. Standalone
    unbound custody writes remain v2 so they cannot masquerade as acceptance-bound
    publication evidence.
    """
    destination = Path(destination)
    if destination.exists() or destination.is_symlink():
        invalid(DataPlaneError.BUNDLE_IDENTITY_CONFLICT)
    records = sidecar_records(candidate)
    destination.mkdir(parents=True)
    retained = candidate.retained_state
    plane = data_plane()
    with plane.transaction():
        tensor = _mlx_checkpoint.save_bamf_state_payload(
            destination / "bamf-state.safetensors", candidate.topology, candidate.extents,
            retained.optimizer, optimizer_step=retained.optimizer_step,
            reserve_gib=reserve_gib)
        try:
            local_tensor = destination / tensor["filename"]
            object_path = plane.file_object_destination(tensor["sha256"])
            if not plane.owns_file_object(tensor["sha256"]):
                assert_headroom(
                    object_path, required_bytes=local_tensor.stat().st_size,
                    reserve_gib=reserve_gib)
            plane.adopt_file_object(local_tensor, tensor["sha256"])
            local_tensor.unlink()
            tensor = {**tensor, "object_sha256": tensor["sha256"]}
        except ValueError:
            invalid(DataPlaneError.BUNDLE_PAYLOAD_DRIFT)
    bindings = {}
    for name, record in records.items():
        raw = canonical(record)
        digest = sha(raw)
        plane.put_object(digest, raw)
        filename = SIDECARS[name]
        bindings[name] = {
            "filename": filename, "sha256": _write_file(destination / filename, raw),
            "object_sha256": digest,
        }
    hp = candidate.optimizer_hyperparameters
    from bilqis_mlx.runtime.training_objective import (
        current_training_objective,
    )
    objective = current_training_objective()
    custody = retained.custody
    if (custody is not None
            and custody.training_objective_digest is not None
            and (custody.training_objective_ref != objective.ref
                 or custody.training_objective_digest != objective.digest)):
        invalid("TRAINING_OBJECTIVE_CONTRACT_DRIFT")
    publication_bound = parent_acceptance_sha256 is not _UNBOUND_PARENT_ACCEPTANCE
    manifest = BamfGenerationManifest(
        candidate.run_id, candidate.generation, candidate.parent_manifest_sha256,
        candidate.implementation_sha256, candidate.topology.to_record(),
        candidate.extents.to_record(), candidate.provenance.to_record(), tensor,
        {"schema": retained.optimizer.schema_version, "step": retained.optimizer_step,
         "hyperparameters": asdict(hp),
         **({"identity_scheme": retained.identity_scheme}
            if retained.identity_scheme != LEGACY_IDENTITY_SCHEME else {})},
        candidate.transition, bindings,
        training_objective_ref=objective.ref,
        training_objective_digest=objective.digest,
        parent_acceptance_sha256=(
            parent_acceptance_sha256 if publication_bound else None),
        schema=(OBJECTIVE_ACCEPTANCE_BOUND_BAMF_BUNDLE_SCHEMA
                if publication_bound else OBJECTIVE_BOUND_BAMF_BUNDLE_SCHEMA)).to_record()
    raw = canonical(manifest)
    digest = _write_file(destination / "manifest.json", raw)
    plane.put_node(digest, raw, candidate.generation, candidate.parent_manifest_sha256)
    directory = os.open(destination, os.O_RDONLY)
    try:
        os.fsync(directory)
    finally:
        os.close(directory)
    validate_bamf_bundle_custody(destination, expected_manifest_sha256=digest)
    return {**manifest, "manifest_sha256": digest}


def _read_sidecar(root: Path, binding: dict):
    if (not isinstance(binding, dict)
            or set(binding) != {"filename", "sha256", "object_sha256"}
            or not isinstance(binding.get("filename"), str)
            or Path(binding["filename"]).name != binding["filename"]):
        invalid()
    path = root / binding["filename"]
    if path.is_symlink() or not path.is_file():
        invalid(DataPlaneError.BUNDLE_ENTRY_UNSAFE)
    raw = path.read_bytes()
    if sha(raw) != binding["sha256"] or binding["sha256"] != binding["object_sha256"]:
        invalid(DataPlaneError.BUNDLE_PAYLOAD_DRIFT)
    try:
        if data_plane().get_object(binding["object_sha256"]) != raw:
            invalid(DataPlaneError.BUNDLE_PAYLOAD_DRIFT)
    except ValueError:
        invalid(DataPlaneError.BUNDLE_PAYLOAD_DRIFT)
    return json.loads(raw)


def validate_bamf_bundle_custody(
        root: Path, *, expected_manifest_sha256: str | None = None) -> dict:
    """Verify local immutable bundle bytes without constructing MLX tensor state."""
    root = Path(root)
    manifest_path = root / "manifest.json"
    if root.is_symlink() or not root.is_dir() or manifest_path.is_symlink() or not manifest_path.is_file():
        invalid(DataPlaneError.BUNDLE_ROOT_UNSAFE)
    raw = manifest_path.read_bytes()
    digest = sha(raw)
    if expected_manifest_sha256 is not None and digest != expected_manifest_sha256:
        invalid(DataPlaneError.BUNDLE_PAYLOAD_DRIFT)
    try:
        if data_plane().get_node(digest) != raw:
            invalid(DataPlaneError.BUNDLE_PAYLOAD_DRIFT)
        manifest = BamfGenerationManifest.from_record(json.loads(raw)).to_record()
    except (ValueError, json.JSONDecodeError, KeyError, TypeError):
        invalid(DataPlaneError.BUNDLE_PAYLOAD_DRIFT)
    recorded = set(manifest.get("sidecars", {}))
    optional = {
        "run_identity", "baseline_evidence", "learning_health_state",
        "championship_state",
    }
    if manifest["schema"] in {
            BAMF_BUNDLE_SCHEMA, OBJECTIVE_BOUND_BAMF_BUNDLE_SCHEMA}:
        optional.add("step_proofs")
    required = set(SIDECARS) - optional
    if (not required <= recorded <= set(SIDECARS)
            or set(manifest["optimizer"]) not in (
                {"schema", "step", "hyperparameters"},
                {"schema", "step", "hyperparameters", "identity_scheme"})
            or manifest["optimizer"].get(
                "identity_scheme", LEGACY_IDENTITY_SCHEME) not in IDENTITY_SCHEMES
            or manifest["optimizer"]["step"] != manifest.get("tensors", {}).get("optimizer_step")):
        invalid()
    for name in recorded:
        _read_sidecar(root, manifest["sidecars"][name])
    tensor = manifest.get("tensors", {})
    legacy_keys = {"schema", "filename", "sha256", "optimizer_step",
                   "tensor_count", "uncompressed_bytes"}
    current_keys = legacy_keys | {"object_sha256"}
    if (not isinstance(tensor, dict) or set(tensor) not in (legacy_keys, current_keys)
            or Path(tensor.get("filename", "")).name != tensor.get("filename")):
        invalid(DataPlaneError.BUNDLE_PAYLOAD_DRIFT)
    if "object_sha256" in tensor:
        if tensor["object_sha256"] != tensor.get("sha256"):
            invalid(DataPlaneError.BUNDLE_PAYLOAD_DRIFT)
        try:
            data_plane().require_file_object(tensor["object_sha256"])
        except ValueError:
            invalid(DataPlaneError.BUNDLE_PAYLOAD_DRIFT)
    else:
        tensor_path = root / tensor["filename"]
        if (tensor_path.is_symlink() or not tensor_path.is_file()
                or not _mlx_checkpoint.verify_file_digest(tensor_path, tensor.get("sha256"))):
            invalid(DataPlaneError.BUNDLE_PAYLOAD_DRIFT)
    return manifest


def _tensor_read_path(root: Path, binding: dict) -> tuple[Path, dict]:
    if "object_sha256" not in binding:
        return root / binding["filename"], binding
    try:
        plane = data_plane()
        with plane.transaction():
            digest = binding["object_sha256"]
            path = plane.require_file_object(digest)
            if not plane.owns_file_object(digest):
                assert_headroom(path, required_bytes=path.stat().st_size)
                path = plane.adopt_file_object(path, digest)
    except ValueError:
        invalid(DataPlaneError.BUNDLE_PAYLOAD_DRIFT)
    return path, {key: value for key, value in binding.items()
                  if key != "object_sha256"} | {"filename": path.name}


def _load_validated_bundle_parts(
        root: Path, *, expected_manifest_sha256: str | None = None) -> _ValidatedBundleParts:
    """Read one complete immutable bundle without issuing learning authority."""
    from bilqis_mlx.runtime.atlas_optimizer import AdamWHyperparameters, STATE_SCHEMA
    from bilqis_mlx.runtime.checkpoint_outbox import ordinary_outbox_lineage
    from bilqis_mlx.runtime.model_topology_v2 import GenerationExtents, GenerationProvenance, ModelTopologySpecV2
    root = Path(root)
    manifest = validate_bamf_bundle_custody(
        root, expected_manifest_sha256=expected_manifest_sha256)
    if manifest["optimizer"]["schema"] != STATE_SCHEMA:
        invalid()
    spec = ModelTopologySpecV2.from_record(manifest["topology"])
    extents = GenerationExtents.from_record(manifest["extents"])
    provenance = GenerationProvenance.from_record(manifest["provenance"])
    recorded = set(manifest["sidecars"])
    records = {name: _read_sidecar(root, manifest["sidecars"][name])
               for name in recorded}
    records.setdefault("step_proofs", {
        "schema": "bilqis.mlx.bamf-step-proofs/v1", "proofs": []})
    motif, policy = validate_sidecars(extents, provenance, records)
    lineage = {"run_id": manifest["run_id"], "generation": manifest["generation"]}
    if not records["outbox"] or not ordinary_outbox_lineage(lineage, list(records["outbox"])):
        invalid("BAMF_OUTBOX_LINEAGE_INVALID")
    hp_record = dict(manifest["optimizer"]["hyperparameters"])
    hp_record["betas"] = tuple(hp_record.get("betas", ()))
    hp = AdamWHyperparameters(**hp_record)
    tensor_path, tensor_binding = _tensor_read_path(root, manifest["tensors"])
    numerical = _mlx_checkpoint.load_bamf_state_payload(
        tensor_path, tensor_binding, spec, extents)
    run_identity = None
    if "run_identity" in records:
        from .genesis import BamfRunIdentity
        run_identity = BamfRunIdentity.from_record(records["run_identity"])
        if run_identity.run_id != manifest["run_id"]:
            invalid("BAMF_RUN_IDENTITY_DRIFT")
    return _ValidatedBundleParts(
        manifest, spec, extents, provenance, records, hp, numerical, motif, policy,
        manifest["optimizer"]["step"], run_identity)


def load_bamf_bundle(root: Path, *, expected_manifest_sha256: str | None = None) -> CompleteStudent:
    """Validate manifest and all sidecars before constructing B12 optimizer state."""
    from bilqis_mlx.learning.atlas_candidate import _load_retained_candidate_state_with_parts

    root = Path(root)
    if expected_manifest_sha256 is None:
        manifest_path = root / "manifest.json"
        if manifest_path.is_symlink() or not manifest_path.is_file():
            invalid(DataPlaneError.BUNDLE_ROOT_UNSAFE)
        expected_manifest_sha256 = sha(manifest_path.read_bytes())
    retained, parts = _load_retained_candidate_state_with_parts(
        root, expected_manifest_sha256=expected_manifest_sha256)
    from .publication.instrumentation import note_bundle_load
    note_bundle_load(parts.manifest)
    manifest = parts.manifest
    student = CompleteStudent(
        manifest["run_id"], manifest["generation"], manifest["parent_manifest_sha256"],
        manifest["implementation_sha256"], parts.spec, parts.extents, retained, parts.hp,
        parts.provenance, parts.records["semantic_abi"], parts.records["compiler_features"],
        parts.records["correction_frontier"], parts.records["teacher_state"],
        parts.records["evaluation_contract"], manifest["transition"],
        tuple(parts.records["outbox"]), parts.run_identity,
        parts.records.get("baseline_evidence"),
        parts.records.get("learning_health_state"),
        parts.records.get("championship_state"))
    if student.run_identity is not None and student.generation == 0:
        from bilqis_mlx.learning._atlas_candidate.identity_binding import (
            bind_candidate_identity_or_fallback,
        )
        identity = student.run_identity
        candidate_digest = bind_candidate_identity_or_fallback(
            student.retained_state, student.topology.digest, student.extents.digest,
            expected_digest=identity.initial_candidate_identity_sha256)
        if (candidate_digest != identity.initial_candidate_identity_sha256
                or identity.initial_topology_digest != student.topology.digest
                or identity.initial_extents_digest != student.extents.digest
                or identity.initial_implementation_sha256 != student.implementation_sha256
                or identity.initial_source_identity != student.provenance.source_identity
                or identity.initial_release_digest != student.provenance.release_digest
                or identity.initial_teacher_identity != student.provenance.teacher_identity
                or identity.initial_teacher_epoch != student.provenance.teacher_epoch):
            invalid("BAMF_RUN_IDENTITY_DRIFT")
    return student
