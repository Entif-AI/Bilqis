"""Portable execution receipts for C08.4 cold-resume validation."""
from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Mapping

from .contracts import _invalid
from .distributed_contracts import DistributedRank, DistributedStepManifest, _sha


def _fsync_directory(path: Path) -> None:
    descriptor = os.open(path, os.O_RDONLY)
    try:
        os.fsync(descriptor)
    finally:
        os.close(descriptor)


def _prepare_receipt_root(run_dir: Path) -> Path:
    if run_dir.is_symlink() or not run_dir.is_dir():
        _invalid("BAMF_C08_DISTRIBUTED_RECEIPT_ROOT_INVALID")
    current = run_dir
    for part in ("receipts", "c08-distributed"):
        child = current / part
        if child.is_symlink() or (child.exists() and not child.is_dir()):
            _invalid("BAMF_C08_DISTRIBUTED_RECEIPT_ROOT_INVALID")
        created = not child.exists()
        child.mkdir(exist_ok=True)
        if created:
            _fsync_directory(child)
            _fsync_directory(current)
        current = child
    return current


def distributed_manifest_record(manifest: DistributedStepManifest) -> dict:
    if type(manifest) is not DistributedStepManifest:
        _invalid("BAMF_C08_DISTRIBUTED_MANIFEST_REQUIRED")
    manifest.__post_init__()
    record = {
        "schema_version": manifest.schema_version,
        "retained_generation": manifest.retained_generation,
        "retained_manifest_sha256": manifest.retained_manifest_sha256,
        "curriculum_release": manifest.curriculum_release,
        "source_release": manifest.source_release,
        "logical_batch_digest": manifest.logical_batch_digest,
        "partition_seed": manifest.partition_seed,
        "world_size": manifest.world_size,
        "workers": [
            {"rank": worker.rank, "worker_id": worker.worker_id,
             "device_family": worker.device_family}
            for worker in manifest.workers
        ],
        "mlx_version": manifest.mlx_version,
        "backend": manifest.backend,
        "numeric_precision": manifest.numeric_precision,
        "reduction_policy": manifest.reduction_policy,
        "manifest_digest": manifest.digest,
    }
    if manifest.training_objective_digest is not None:
        record["training_objective_digest"] = manifest.training_objective_digest
    return record


def load_distributed_manifest(record: Mapping) -> DistributedStepManifest:
    if not isinstance(record, Mapping):
        _invalid("BAMF_C08_DISTRIBUTED_RECEIPT_INVALID")
    try:
        workers = tuple(DistributedRank(
            worker["rank"], worker["worker_id"], worker["device_family"])
            for worker in record["workers"])
        manifest = DistributedStepManifest(
            retained_generation=record["retained_generation"],
            retained_manifest_sha256=record["retained_manifest_sha256"],
            curriculum_release=record["curriculum_release"],
            source_release=record["source_release"],
            logical_batch_digest=record["logical_batch_digest"],
            partition_seed=record["partition_seed"],
            world_size=record["world_size"], workers=workers,
            mlx_version=record["mlx_version"], backend=record["backend"],
            numeric_precision=record["numeric_precision"],
            reduction_policy=record["reduction_policy"],
            training_objective_digest=record.get("training_objective_digest"),
            schema_version=record["schema_version"])
    except (KeyError, TypeError, ValueError):
        _invalid("BAMF_C08_DISTRIBUTED_RECEIPT_INVALID")
    if record.get("manifest_digest") != manifest.digest:
        _invalid("BAMF_C08_DISTRIBUTED_RECEIPT_DIGEST_DRIFT")
    return manifest


def distributed_manifest_path(run_dir: Path, logical_batch_digest: str) -> Path:
    if not isinstance(run_dir, Path) or not _sha(logical_batch_digest):
        _invalid("BAMF_C08_DISTRIBUTED_RECEIPT_PATH_INVALID")
    return run_dir / "receipts" / "c08-distributed" / (
        logical_batch_digest + ".json")


def persist_distributed_manifest(
        run_dir: Path, manifest: DistributedStepManifest) -> Path:
    """Durably bind a logical batch to one non-semantic execution topology."""
    path = distributed_manifest_path(run_dir, manifest.logical_batch_digest)
    if _prepare_receipt_root(run_dir) != path.parent:
        _invalid("BAMF_C08_DISTRIBUTED_RECEIPT_ROOT_INVALID")
    if path.exists():
        existing = load_distributed_manifest(json.loads(path.read_text()))
        if existing.digest != manifest.digest:
            _invalid("BAMF_C08_DISTRIBUTED_RECEIPT_REPLAY_DRIFT")
        return path
    temporary = path.with_name(path.name + ".tmp")
    payload = json.dumps(
        distributed_manifest_record(manifest), sort_keys=True,
        separators=(",", ":")) + "\n"
    with temporary.open("w") as stream:
        stream.write(payload)
        stream.flush()
        os.fsync(stream.fileno())
    os.replace(temporary, path)
    _fsync_directory(path.parent)
    return path


def load_persisted_distributed_manifest(
        run_dir: Path, logical_batch_digest: str) -> DistributedStepManifest:
    path = distributed_manifest_path(run_dir, logical_batch_digest)
    if not path.is_file():
        _invalid("BAMF_C08_DISTRIBUTED_RECEIPT_MISSING")
    return load_distributed_manifest(json.loads(path.read_text()))


__all__ = (
    "distributed_manifest_path", "distributed_manifest_record",
    "load_distributed_manifest", "load_persisted_distributed_manifest",
    "persist_distributed_manifest",
)
