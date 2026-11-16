"""Read-only, advisory displacement from an epoch origin and a holistic peak."""
from __future__ import annotations

from functools import lru_cache
import json
from pathlib import Path

from bilqis_mlx.backup import digest_file
from bilqis_mlx.runtime.mlx_checkpoint import SCHEMA as BUNDLE_SCHEMA, _json_hash


@lru_cache(maxsize=4)
def _weights(path: str, sha: str, graph_sha: str):
    """Verify an immutable existing bundle, then cache weights only."""
    import mlx.core as mx
    from safetensors import safe_open

    folder = Path(path)
    manifest = json.loads((folder / "manifest.json").read_text())
    names = manifest.get("parameter_names")
    if (manifest.get("schema") != BUNDLE_SCHEMA or
            not isinstance(names, list) or not names or len(set(names)) != len(names) or
            manifest.get("name_order_sha256") != _json_hash(names)):
        raise ValueError("MATRIX_STRAIN_REFERENCE_PARAMETER_IDENTITY_DRIFT")
    if manifest.get("semantic_catalog", {}).get("digest") != graph_sha:
        raise ValueError("MATRIX_STRAIN_REFERENCE_SEMANTIC_GRAPH_DRIFT")
    blob = folder / "model-and-own-adamw.safetensors"
    if sha != manifest.get("safetensors_sha256") or digest_file(blob) != sha:
        raise ValueError("MATRIX_STRAIN_REFERENCE_BLOB_CHANGED")
    with safe_open(str(blob), framework="np", device="cpu") as tensors:
        result = {name: mx.array(tensors.get_tensor(f"p{index:04d}_weight"), dtype=mx.float32)
                  for index, name in enumerate(names)}
    mx.eval(result)
    return result


def references(run_dir: Path, receipt: dict):
    """Freeze compatible source pointers for the duration of a visit."""
    origin = receipt.get("curriculum_parent")
    exam = receipt.get("last_exam") or {}
    status = exam.get("whole_student_retention") or {}
    identity = status.get("scope_sha256")
    peak = next((item for item in receipt.get("whole_student_peaks", ())
                 if item.get("scope_sha256") == identity), None)
    if not origin or peak is None:
        return None, "MISSING_COMPARABLE_REFERENCE"
    return ((origin, peak["checkpoint"]), None)


def score(mx, parent: dict, candidate: dict, start: dict, best: dict) -> dict:
    """Per-tensor normalized squared-distance changes, no parameter writes."""
    if not parent or set(parent) != set(candidate) or set(parent) != set(start) or set(parent) != set(best):
        raise ValueError("MATRIX_STRAIN_PARAMETER_SET_MISMATCH")
    matrix = {}
    for name in parent:
        p, c, s, b = parent[name], candidate[name], start[name], best[name]
        if any(x.shape != p.shape or x.dtype != p.dtype for x in (c, s, b)):
            raise ValueError("MATRIX_STRAIN_TENSOR_SHAPE_OR_DTYPE_MISMATCH")
        shift = c - p
        distance_start = mx.sum((c - s) ** 2 - (p - s) ** 2) / p.size
        distance_best = mx.sum((c - b) ** 2 - (p - b) ** 2) / p.size
        displacement = mx.sum(shift ** 2) / p.size
        mx.eval(distance_start, distance_best, displacement)
        matrix[name] = {
            "delta_start_mean_sq": float(distance_start.item()),
            "delta_best_mean_sq": float(distance_best.item()),
            "candidate_shift_mean_sq": float(displacement.item()),
        }
    return {"schema": "bilqis.mlx.matrix-strain/v1", "tensor_count": len(matrix),
            "matrices": matrix, "advisory_only": True}


def observe(mx, run_dir: Path, receipt: dict, parent: dict, candidate: dict) -> dict:
    pointers, reason = references(run_dir, receipt)
    if reason:
        return {"status": "NOT_MEASURED", "reason": reason}
    origin, peak = pointers
    graph_sha = receipt.get("semantic_graph_sha256")
    if not isinstance(graph_sha, str) or len(graph_sha) != 64:
        return {"status": "NOT_MEASURED", "reason": "MISSING_SEMANTIC_GRAPH_IDENTITY"}
    root = Path(run_dir).resolve()
    arrays = []
    try:
        for pointer in (origin, peak):
            filename = pointer.get("filename")
            if not isinstance(filename, str):
                return {"status": "NOT_MEASURED", "reason": "MISSING_CHECKPOINT_PATH"}
            path = root / filename
            if (root not in path.resolve().parents or path.is_symlink()
                    or not path.is_dir()):
                return {"status": "NOT_MEASURED", "reason": "UNSAFE_CHECKPOINT_PATH"}
            arrays.append(_weights(str(path.resolve()), pointer["sha256"], graph_sha))
    except (OSError, KeyError, ValueError):
        return {"status": "NOT_MEASURED", "reason": "REFERENCE_UNAVAILABLE_OR_INVALID"}
    try:
        result = score(mx, parent, candidate, *arrays)
    except ValueError as exc:
        return {"status": "NOT_MEASURED", "reason": str(exc)}
    return {**result, "status": "MEASURED",
            "start_checkpoint_sha256": origin["sha256"],
            "best_checkpoint_sha256": peak["sha256"],
            "best_optimizer_step": peak["optimizer_step"]}
