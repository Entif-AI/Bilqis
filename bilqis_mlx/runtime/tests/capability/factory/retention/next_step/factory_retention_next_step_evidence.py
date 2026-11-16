"""Numeric, structural, and custody evidence for the B13.2 continuation witness."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path
import sys

import mlx.core as mx
import numpy as np

from bilqis_mlx.data_plane import data_plane
from bilqis_mlx.learning.atlas_acceptance import candidate_identity_digest
from bilqis_mlx.runtime.atlas_attention import MLX_VERSION, ROPE_VARIANT
from bilqis_mlx.runtime.atlas_model import model_backend
from bilqis_mlx.runtime.bamf_bundle.admission import load_accepted_generation
from bilqis_mlx.semantics.foundation.domains import contract_digest


FP32_ATOL = 2e-3
REFERENCE_SCHEMA = "bilqis.mlx.b13.2-backend-reference/v1"


def _sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with Path(path).open("rb") as stream:
        while chunk := stream.read(1024 * 1024):
            digest.update(chunk)
    return digest.hexdigest()


def _json_digest(value) -> str:
    raw = json.dumps(
        value, sort_keys=True, separators=(",", ":"), ensure_ascii=False,
        allow_nan=False).encode("utf-8")
    return hashlib.sha256(raw).hexdigest()


def _mapping_digest(mapping) -> str:
    digest = hashlib.sha256()
    for name, value in sorted(mapping.items()):
        array = np.asarray(value)
        digest.update(name.encode("utf-8"))
        digest.update(str(array.dtype).encode("ascii"))
        digest.update(json.dumps(array.shape).encode("ascii"))
        digest.update(array.tobytes())
    return digest.hexdigest()


def _tensor_census_digest(optimizer):
    records = []
    for group in ("parameters", "m", "v", "update_counts"):
        records.extend(
            (group, name, list(value.shape), str(value.dtype))
            for name, value in sorted(getattr(optimizer, group).items()))
    return _json_digest(records)


def _device_provenance(parent):
    backend = model_backend(parent.topology)
    device = backend.device.lower()
    family = "CPU" if "cpu" in device else (
        "APPLE_METAL" if sys.platform == "darwin" and mx.metal.is_available()
        else "MLX_GPU")
    return {
        "device": backend.device, "device_family": family,
        "precision": backend.precision, "backend_schema": backend.schema_version,
        "mlx_version": MLX_VERSION,
        "attention_kernel": "mlx.core.fast.scaled_dot_product_attention",
        "rope_variant": list(ROPE_VARIANT),
    }


def _parent_identity(parent):
    retained = parent.retained_state
    return {
        "run_id": parent.run_id, "generation": parent.generation,
        "parent_manifest_sha256": parent.parent_manifest_sha256,
        "candidate_identity_sha256": candidate_identity_digest(retained),
        "optimizer_step": retained.optimizer_step,
        "tensor_census_sha256": _tensor_census_digest(retained.optimizer),
        "implementation_sha256": parent.implementation_sha256,
        "policy_sha256": _json_digest(retained.policy.to_record()),
        "motif_sha256": retained.allocations.manifest.digest,
        "teacher_state_sha256": _json_digest(dict(parent.teacher_state)),
        "semantic_abi_sha256": _json_digest(dict(parent.semantic_abi)),
        "correction_frontier_sha256": _json_digest(dict(parent.correction_frontier)),
    }


def _forward_structure(gradient):
    output = gradient.execution.output
    decisions = [{
        "decision_id": record.decision_id, "kind": record.kind.value,
        "candidates_sha256": contract_digest(record.candidates),
        "logit_shape": list(record.logits.shape),
    } for record in output.decisions]
    return {
        "generation_binding": output.generation_binding,
        "status": output.status.value, "execution_mode": output.execution_mode.value,
        "fallback_requested": output.fallback_requested,
        "decisions": decisions, "committed_sha256": contract_digest(output.committed),
    }


def _numeric_arrays(parent, gradient, transaction):
    arrays = {}
    for index, record in enumerate(gradient.execution.output.decisions):
        arrays[f"forward/{index}:{record.decision_id}"] = record.logits
    loss = gradient.execution.loss
    for name in ("primary", "role", "epistemic", "total"):
        arrays[f"loss/{name}"] = getattr(loss, name)
    arrays.update({f"gradient/{name}": value
                   for name, value in gradient.gradients.items()})
    for group in ("parameters", "m", "v"):
        before = getattr(parent.retained_state.optimizer, group)
        after = getattr(transaction.optimizer, group)
        arrays.update({f"delta/{group}/{name}": after[name] - before[name]
                       for name in before})
    return arrays


def _require_finite(logical: str, value, role: str) -> None:
    finite = mx.all(mx.isfinite(value))
    mx.eval(finite)
    if not bool(finite):
        raise AssertionError(f"B13.2 numeric {role} non-finite: {logical}")


def _write_numeric_reference(path: Path, arrays) -> dict:
    path = Path(path)
    if path.exists() or path.with_suffix(".json").exists():
        raise AssertionError("B13.2 numeric reference already exists")
    records, stored = {}, {}
    for index, (logical, value) in enumerate(sorted(arrays.items())):
        _require_finite(logical, value, "source")
        key = f"t{index:05d}"
        records[logical] = {"key": key, "shape": list(value.shape), "dtype": str(value.dtype)}
        stored[key] = value
    mx.eval(*stored.values())
    mx.save_safetensors(str(path), stored)
    metadata = {"schema": REFERENCE_SCHEMA, "arrays": records}
    path.with_suffix(".json").write_text(
        json.dumps(metadata, sort_keys=True, separators=(",", ":")) + "\n")
    return {
        "array_count": len(records), "tensor_sha256": _sha256_file(path),
        "metadata_sha256": _sha256_file(path.with_suffix(".json")),
    }


def _comparison_group(logical: str) -> str:
    return logical.split("/", 1)[0]


def _compare_numeric_reference(path: Path, arrays) -> dict:
    metadata = json.loads(Path(path).with_suffix(".json").read_text())
    if metadata.get("schema") != REFERENCE_SCHEMA:
        raise AssertionError("B13.2 numeric reference schema drift")
    loaded = mx.load(str(path))
    if set(metadata["arrays"]) != set(arrays):
        raise AssertionError("B13.2 numeric reference census drift")
    maxima = {"forward": 0.0, "loss": 0.0, "gradient": 0.0, "delta": 0.0}
    for logical, current in arrays.items():
        record = metadata["arrays"][logical]
        expected = loaded[record["key"]]
        if list(current.shape) != record["shape"] or str(current.dtype) != record["dtype"]:
            raise AssertionError("B13.2 numeric tensor contract drift")
        _require_finite(logical, expected, "reference")
        _require_finite(logical, current, "current")
        delta = mx.max(mx.abs(current - expected))
        _require_finite(logical, delta, "delta")
        group = _comparison_group(logical)
        maxima[group] = max(maxima[group], float(delta))
    maxima["overall"] = max(maxima.values())
    return maxima


def _structural_evidence(
        parent, cache, visit, training, compiled_batch,
        plan, targets, mask, gradient, transaction):
    _context, receipt, capability, seed, row, key, policy, metadata = visit
    proof = transaction.step_proofs[-1]
    proof_record = proof.to_record()
    proof_record["parameter_names"] = list(proof_record["parameter_names"])
    return {
        "backend": _device_provenance(parent), "parent": _parent_identity(parent),
        "cache": {
            "generation": cache.generation,
            "accepted_manifest_sha256": cache.accepted_manifest_sha256,
            "generation_binding": cache.generation_binding,
            "motif_sha256": cache.motif_manifest.digest,
        },
        "visit": {
            "factory_release_sha256": receipt["factory_release_sha256"],
            "capability": capability, "seed": seed, "row_id": row["id"],
            "row_sha256": _json_digest(row), "teacher_policy_key": key,
            "teacher_policy_sha256": _json_digest(policy),
            "teacher_learning_rate": float(policy["lr"]),
            "selection_reason": metadata["selection_reason"],
            "scheduler_selected": receipt["continuation_fixture"]["scheduler_selected"],
            "controlled_optimizer_fixture": True,
        },
        "plan_sha256": contract_digest((
            plan.modality_id, plan.input_prefix_end, plan.decisions,
            plan.generation_binding, plan.maximum_decisions)),
        "targets_sha256": contract_digest(targets), "mask_sha256": contract_digest(mask),
        "forward": _forward_structure(gradient),
        "training_batch_authority_sha256": training.authority_digest,
        "training_authority_sha256": compiled_batch.training_authority.digest,
        "step_proof": proof_record,
        "candidate_update_counts_sha256": _mapping_digest(transaction.optimizer.update_counts),
    }


def _custody_hashes(run_dir: Path, published) -> dict:
    root = Path(run_dir) / published["bundle"]
    result = {
        str(path.relative_to(root)): _sha256_file(path)
        for path in sorted(root.rglob("*")) if path.is_file()
    }
    manifest = json.loads((root / "manifest.json").read_text())
    object_sha = manifest["tensors"].get("object_sha256")
    if object_sha is not None:
        result[f"cas:{object_sha}"] = _sha256_file(
            data_plane().require_file_object(object_sha))
    return result


def _assert_structural_parity(source, destination):
    for field in (
            "parent", "cache", "visit", "plan_sha256", "targets_sha256",
            "mask_sha256", "training_batch_authority_sha256",
            "training_authority_sha256",
            "candidate_update_counts_sha256"):
        if source[field] != destination[field]:
            raise AssertionError(f"B13.2 structural parity drift: {field}")
    if source["step_proof"] != destination["step_proof"]:
        differing = tuple(
            key for key in source["step_proof"]
            if source["step_proof"].get(key) != destination["step_proof"].get(key)
        )
        raise AssertionError(
            "B13.2 structural parity drift: step_proof fields="
            + ",".join(differing))
    source_forward = {
        key: value for key, value in source["forward"].items()
        if key != "committed_sha256"
    }
    destination_forward = {
        key: value for key, value in destination["forward"].items()
        if key != "committed_sha256"
    }
    if source_forward != destination_forward:
        raise AssertionError("B13.2 structural parity drift: forward")
    if source["backend"]["device_family"] != "APPLE_METAL":
        raise AssertionError("B13.2 source arm is not Apple Metal")
    if destination["backend"]["device_family"] != "CPU":
        raise AssertionError("B13.2 destination arm is not CPU")
    for field in (
            "precision", "backend_schema", "mlx_version",
            "attention_kernel", "rope_variant"):
        if source["backend"][field] != destination["backend"][field]:
            raise AssertionError(f"B13.2 execution provenance drift: {field}")
    return (
        source["forward"]["committed_sha256"]
        == destination["forward"]["committed_sha256"])


def _assert_parent_unchanged(run_dir, published, held, snapshot):
    pointer_before, bundles_before, hashes_before, identity_before = snapshot
    if (Path(run_dir) / "bamf-state.json").read_bytes() != pointer_before:
        raise AssertionError("B13.2 accepted pointer mutated")
    bundles = tuple(sorted(path.name for path in (Path(run_dir) / "bamf-bundles").iterdir()))
    if bundles != bundles_before or _custody_hashes(run_dir, published) != hashes_before:
        raise AssertionError("B13.2 accepted bundle/CAS mutated")
    if _parent_identity(held) != identity_before:
        raise AssertionError("B13.2 in-memory accepted parent mutated")
    cold = load_accepted_generation(run_dir)
    if cold.generation != 1 or _parent_identity(cold) != identity_before:
        raise AssertionError("B13.2 cold accepted parent drift or generation-2 publication")


__all__ = (
    "FP32_ATOL", "_assert_parent_unchanged", "_assert_structural_parity",
    "_compare_numeric_reference", "_custody_hashes", "_json_digest",
    "_numeric_arrays", "_parent_identity", "_structural_evidence",
    "_write_numeric_reference",
)
