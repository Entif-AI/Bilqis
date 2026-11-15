"""Versioned MLX FP32 + AdamW snapshot codec, initially qualified on fixtures.

The external native checkpoint remains immutable. Tensor identifiers in the
safetensors file are opaque ordinal keys so historic dot-delimited parameter
names cannot be confused with MLX's tree paths. The manifest preserves exact
name/order and optimizer hyperparameters not stored inside MLX AdamW.state.

A directory is created exclusively; no checkpoint overwrite or auto-pruning.
This does not itself authorize neural updates to any real Bilqis student.
"""
from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path
from typing import Mapping

from bilqis_mlx.errors import ErrorBus, SCHOOL
from bilqis_mlx.backup import digest_file
from bilqis_mlx.data_plane import verify_file_digest
from bilqis_mlx.runtime.disk import assert_headroom

SCHEMA = "bilqis.mlx.fp32-adamw-bundle/v1"
BAMF_TENSOR_SCHEMA = "bilqis.mlx.bamf-named-state/v2"


def _json_hash(value: object) -> str:
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(",", ":"),
                                     allow_nan=False).encode("utf-8")).hexdigest()


def _validate_name_list(names: list[str]) -> None:
    if (not names or any(not isinstance(name, str) or not name or
                         name.startswith(".") or "\x00" in name for name in names)
            or len(names) != len(set(names))):
        raise ValueError("MLX_BUNDLE_INVALID_PARAMETER_IDENTITY")


def _fp32_array(mx, item, *, what: str):
    if not isinstance(item, mx.array) or item.dtype != mx.float32:
        raise ValueError("MLX_BUNDLE_NOT_FP32_" + what)
    return item


def _bundle_arrays(mx, parameters, state):
    names = list(parameters)
    arrays = {}
    expected_bytes = 0
    for i, name in enumerate(names):
        param = _fp32_array(mx, parameters[name], what="PARAMETER")
        cell = state[name]
        if set(cell) != {"m", "v"}:
            raise ValueError("MLX_BUNDLE_MISSING_ADAMW_MOMENTS")
        for field, arr in (("weight", param), ("m", cell["m"]), ("v", cell["v"])):
            arr = _fp32_array(mx, arr, what="MOMENT")
            if arr.shape != param.shape:
                raise ValueError("MLX_BUNDLE_PARAM_MOMENT_SHAPE_DRIFT")
            key = f"p{i:04d}_{field}"
            arrays[key] = arr
            expected_bytes += arr.size * arr.itemsize
    arrays["adamw_global_step"] = state["step"]
    arrays["adamw_learning_rate"] = state["learning_rate"]
    return arrays, expected_bytes


def save_new_bundle(destination: Path, parameters: Mapping[str, object], optimizer,
                    *, source_digest: str, reserve_gib: float = 100.0,
                    semantic_catalog: dict | None = None, model_topology=None) -> dict:
    """Store an optimizer-bearing snapshot in an exclusive new directory.

    For now used by disposable fixtures only. The caller may not substitute
    this for full-history AdamW equivalence without independent comparison.
    """
    from .model_topology import validate_parameter_shapes
    if model_topology is not None:
        validate_parameter_shapes(parameters, model_topology, len(semantic_catalog["tokens"]))
    import mlx.core as mx
    names = list(parameters)
    _validate_name_list(names)
    if (len(source_digest) != 64 or
            any(x not in "0123456789abcdef" for x in source_digest)):
        raise ValueError("MLX_BUNDLE_SOURCE_DIGEST_MISSING")
    if not optimizer.bias_correction:
        raise ValueError("MLX_BUNDLE_REQUIRES_BIAS_CORRECTED_ADAMW")
    state = optimizer.state
    if set(state) != {"step", "learning_rate", *names}:
        raise ValueError("MLX_BUNDLE_OPTIMIZER_STATE_NOT_COMPLETE")
    if not (0 < len(names) <= 4096):
        raise ValueError("MLX_BUNDLE_TOO_MANY_PARAMETERS")
    arrays, expected_bytes = _bundle_arrays(mx, parameters, state)
    if semantic_catalog is not None:
        from bilqis_mlx.vocabulary_growth import _check_catalog, digest
        _check_catalog(semantic_catalog)
        if ("embedding.weight" not in parameters or
                len(semantic_catalog["tokens"]) != int(parameters["embedding.weight"].shape[0])):
            raise ValueError("MLX_BUNDLE_CATALOG_EMBEDDING_ROW_COUNT_MISMATCH")
    if arrays["adamw_global_step"].dtype != mx.uint64:
        raise ValueError("MLX_BUNDLE_OPTIMIZER_STEP_DTYPE_DRIFT")
    if arrays["adamw_learning_rate"].dtype != mx.float32:
        raise ValueError("MLX_BUNDLE_LEARNING_RATE_DTYPE_DRIFT")
    mx.eval(arrays)
    manifest = {
        "schema": SCHEMA,
        "source_digest": source_digest,
        "parameter_names": names,
        "name_order_sha256": _json_hash(names),
        "optimizer": {"algorithm": "AdamW", "betas": list(optimizer.betas),
                      "eps": optimizer.eps, "weight_decay": optimizer.weight_decay,
                      "bias_correction": optimizer.bias_correction},
        "optimizer_step": int(state["step"].item()),
        "tensor_count": len(arrays),
        "uncompressed_parameter_and_moment_bytes": expected_bytes,
    }
    if model_topology is not None:
        manifest["model_topology"] = model_topology.to_record()
        from .topology_lifecycle import model_implementation
        manifest["model_implementation"] = model_implementation()
    if semantic_catalog is not None:
        manifest["semantic_catalog"] = {
            "filename": "semantic-catalog.json",
            "digest": digest(semantic_catalog),
            "token_count": len(semantic_catalog["tokens"]),
        }
    destination = Path(destination)
    assert_headroom(destination, required_bytes=expected_bytes*2+65536, reserve_gib=reserve_gib)
    destination.mkdir(parents=True, exist_ok=False)
    if semantic_catalog is not None:
        semantic_file = destination / "semantic-catalog.json"
        semantic_file.write_text(json.dumps(semantic_catalog,sort_keys=True,indent=2,
                                            ensure_ascii=False)+"\n",encoding="utf-8")
        manifest["semantic_catalog"]["file_sha256"] = digest_file(semantic_file)
    data_path = destination / "model-and-own-adamw.safetensors"
    mx.save_safetensors(str(data_path), arrays)
    manifest["safetensors_sha256"] = digest_file(data_path)
    (destination / "manifest.json").write_text(json.dumps(manifest,sort_keys=True,indent=2)+"\n")
    # Verify bytes and every restored identity in the same call.
    restored_parameters, restored_optimizer, restored_manifest = load_bundle(destination)
    if list(restored_parameters) != names or restored_manifest != manifest:
        raise ValueError("MLX_BUNDLE_POSTWRITE_READBACK_DRIFT")
    mx.eval(restored_parameters, restored_optimizer.state)
    return manifest


def load_bundle(destination: Path):
    """Read and verify complete optimizer + weights; never implicitly train."""
    import mlx.core as mx
    import mlx.optimizers as optim
    destination = Path(destination)
    manifest = json.loads((destination/"manifest.json").read_text())
    if manifest.get("schema") != SCHEMA:
        raise ValueError("MLX_BUNDLE_SCHEMA_DRIFT")
    topology = None
    if manifest.get("model_topology") is not None:
        from .model_topology import ModelTopologySpec
        topology = ModelTopologySpec.from_record(manifest["model_topology"])
    vocabulary_record = manifest.get("semantic_catalog")
    if vocabulary_record is not None:
        _read_catalog(destination,vocabulary_record)
    names = manifest.get("parameter_names")
    if not isinstance(names,list):
        raise ValueError("MLX_BUNDLE_NAMES_MISSING")
    _validate_name_list(names)
    if _json_hash(names) != manifest["name_order_sha256"]:
        raise ValueError("MLX_BUNDLE_PARAMETER_ORDER_DRIFT")
    blob = destination / "model-and-own-adamw.safetensors"
    if not verify_file_digest(blob, manifest["safetensors_sha256"]):
        raise ValueError("MLX_BUNDLE_TENSOR_FILE_CORRUPTED")
    arrays = mx.load(str(blob))
    expected = {f"p{i:04d}_{part}" for i in range(len(names))
                for part in ("weight","m","v")}
    expected.update(("adamw_global_step","adamw_learning_rate"))
    if set(arrays) != expected or manifest["tensor_count"] != len(arrays):
        raise ValueError("MLX_BUNDLE_MISSING_OR_EXTRA_TENSORS")
    params = {}
    state = {"step":arrays["adamw_global_step"],
             "learning_rate":arrays["adamw_learning_rate"]}
    for i,name in enumerate(names):
        key=f"p{i:04d}"
        weight=_fp32_array(mx,arrays[key+"_weight"],what="WEIGHT")
        m=_fp32_array(mx,arrays[key+"_m"],what="MOMENT")
        v=_fp32_array(mx,arrays[key+"_v"],what="MOMENT")
        if weight.shape != m.shape or weight.shape != v.shape:
            raise ValueError("MLX_BUNDLE_RESTORED_MOMENT_SHAPE_DRIFT")
        params[name]=weight
        state[name]={"m":m,"v":v}
    if (state["step"].dtype != mx.uint64 or
            int(state["step"].item()) != manifest["optimizer_step"]):
        raise ValueError("MLX_BUNDLE_RESTORED_OPTIMIZER_STEP_DRIFT")
    hp=manifest["optimizer"]
    if hp.get("algorithm") != "AdamW" or hp.get("bias_correction") is not True:
        raise ValueError("MLX_BUNDLE_UNSUPPORTED_OPTIMIZER_CONFIG")
    restored=optim.AdamW(learning_rate=float(state["learning_rate"].item()),
                         betas=hp["betas"], eps=hp["eps"],
                         weight_decay=hp["weight_decay"],bias_correction=True)
    restored.state=state
    if topology is not None:
        from .model_topology import validate_parameter_shapes
        validate_parameter_shapes(params, topology, int(params["embedding.weight"].shape[0]))
    mx.eval(params, restored.state)
    return params,restored,manifest


def _read_catalog(destination: Path, binding: dict) -> dict:
    from bilqis_mlx.vocabulary_growth import _check_catalog, digest
    from bilqis_mlx.token_atlas import validate_one_to_one
    if (not isinstance(binding,dict) or
            binding.get("filename") != "semantic-catalog.json"):
        raise ValueError("MLX_BUNDLE_UNRECOGNIZED_CATALOG_BINDING")
    catalog_file = destination / binding["filename"]
    if not verify_file_digest(catalog_file, binding.get("file_sha256")):
        raise ValueError("MLX_BUNDLE_SEMANTIC_CATALOG_FILE_CHANGED")
    catalog = json.loads(catalog_file.read_text(encoding="utf-8"))
    _check_catalog(catalog)
    validate_one_to_one(catalog)
    if (digest(catalog) != binding.get("digest") or
            len(catalog["tokens"]) != binding.get("token_count")):
        raise ValueError("MLX_BUNDLE_SEMANTIC_CATALOG_DIGEST_DRIFT")
    return catalog


def load_semantically_bound_bundle(destination: Path):
    """Return model, own AdamW, immutable semantic manifest and exact token graph."""
    params,optimizer,manifest = load_bundle(destination)
    binding = manifest.get("semantic_catalog")
    if binding is None:
        raise ValueError("MLX_BUNDLE_HAS_NO_SEMANTIC_CATALOG")
    catalog = _read_catalog(Path(destination),binding)
    if int(params["embedding.weight"].shape[0]) != len(catalog["tokens"]):
        raise ValueError("MLX_BUNDLE_RELOADED_MODEL_VOCAB_DRIFT")
    return params,optimizer,manifest,catalog


def _bamf_count_key(parameter_name: str) -> str:
    from bilqis_mlx.runtime.model_topology_v2 import bamf_storage_key
    return bamf_storage_key(parameter_name, "weight")[:-len("weight")] + "count"


def save_bamf_state_payload(destination: Path, spec, extents, state, *,
                            optimizer_step: int, reserve_gib: float = 100.0) -> dict:
    """Persist one complete B12 numerical tree without granting publication."""
    import mlx.core as mx
    from bilqis_mlx.runtime.atlas_optimizer import AdamWStateTree
    from bilqis_mlx.runtime.model_topology_v2 import (
        ModelTopologySpecV2, GenerationExtents, bamf_storage_key,
        expected_bamf_shapes,
    )
    if (type(spec) is not ModelTopologySpecV2 or type(extents) is not GenerationExtents
            or type(state) is not AdamWStateTree or type(optimizer_step) is not int
            or optimizer_step < 0):
        ErrorBus.raise_legacy(SCHOOL.CHECKPOINT_CUSTODY.NUMERICAL_STATE_INVALID)
    state.validate()
    declared = expected_bamf_shapes(spec, extents)
    if (set(state.parameters) != {item.name for item in declared}
            or any(tuple(state.parameters[item.name].shape) != item.shape for item in declared)):
        ErrorBus.raise_legacy(SCHOOL.CHECKPOINT_CUSTODY.PARAMETER_IDENTITY_DRIFT)
    arrays = {}
    expected_bytes = 0
    for item in declared:
        for part, value in (("weight", state.parameters[item.name]),
                            ("m", state.m[item.name]), ("v", state.v[item.name])):
            arrays[bamf_storage_key(item.name, part)] = value
            expected_bytes += value.size * value.itemsize
        count = state.update_counts[item.name]
        arrays[_bamf_count_key(item.name)] = count
        expected_bytes += count.size * count.itemsize
    mx.eval(arrays)
    destination = Path(destination)
    assert_headroom(destination, required_bytes=expected_bytes + 65536,
                    reserve_gib=reserve_gib)
    mx.save_safetensors(str(destination), arrays)
    stored_bytes = destination.stat().st_size
    from bilqis_mlx.runtime.bamf_bundle.publication.instrumentation import note_write
    note_write(stored_bytes)
    with destination.open("rb") as stream:
        os.fsync(stream.fileno())
    from bilqis_mlx.runtime.bamf_bundle.publication.instrumentation import note_fsync
    note_fsync(stored_bytes)
    return {
        "schema": BAMF_TENSOR_SCHEMA,
        "filename": destination.name,
        "sha256": digest_file(destination),
        "optimizer_step": optimizer_step,
        "tensor_count": len(arrays),
        "uncompressed_bytes": expected_bytes,
    }


def load_bamf_state_payload(destination: Path, binding: dict, spec, extents):
    """Verify complete v2 bytes before constructing a detached optimizer tree."""
    import mlx.core as mx
    from bilqis_mlx.runtime.atlas_optimizer import AdamWStateTree
    from bilqis_mlx.runtime.model_topology_v2 import (
        ModelTopologySpecV2, GenerationExtents, bamf_storage_key,
        expected_bamf_shapes,
    )
    if (not isinstance(binding, dict) or binding.get("schema") != BAMF_TENSOR_SCHEMA
            or type(spec) is not ModelTopologySpecV2 or type(extents) is not GenerationExtents
            or binding.get("filename") != Path(destination).name):
        ErrorBus.raise_legacy(SCHOOL.CHECKPOINT_CUSTODY.TENSOR_BINDING_INVALID)
    if Path(destination).is_symlink() or not Path(destination).is_file():
        ErrorBus.raise_legacy(SCHOOL.CHECKPOINT_CUSTODY.TENSOR_BINDING_INVALID)
    if not verify_file_digest(destination, binding.get("sha256")):
        ErrorBus.raise_legacy(SCHOOL.CHECKPOINT_CUSTODY.TENSOR_FILE_CORRUPTED)
    arrays = mx.load(str(destination))
    declared = expected_bamf_shapes(spec, extents)
    expected = {bamf_storage_key(item.name, part)
                for item in declared for part in ("weight", "m", "v")}
    expected |= {_bamf_count_key(item.name) for item in declared}
    if set(arrays) != expected or binding.get("tensor_count") != len(arrays):
        ErrorBus.raise_legacy(SCHOOL.CHECKPOINT_CUSTODY.MISSING_OR_EXTRA_TENSORS)
    if any(tuple(arrays[bamf_storage_key(item.name, "weight")].shape) != item.shape
           for item in declared):
        ErrorBus.raise_legacy(SCHOOL.CHECKPOINT_CUSTODY.PARAMETER_IDENTITY_DRIFT)
    parameters = {item.name: arrays[bamf_storage_key(item.name, "weight")]
                  for item in declared}
    first = {item.name: arrays[bamf_storage_key(item.name, "m")] for item in declared}
    second = {item.name: arrays[bamf_storage_key(item.name, "v")] for item in declared}
    counts = {item.name: arrays[_bamf_count_key(item.name)] for item in declared}
    restored = AdamWStateTree(parameters, first, second, counts)
    mx.eval(restored.parameters, restored.m, restored.v, restored.update_counts)
    return restored
