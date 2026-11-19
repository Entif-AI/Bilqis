#!/usr/bin/env python3
"""Disposable same-host C08.4 MLX collective proof.

This proves only local two-rank collective mechanics. It is explicitly not
heterogeneous Apple-Silicon acceptance.
"""
from __future__ import annotations

import argparse
from importlib.metadata import version
import json
import os
from pathlib import Path
import platform
import sys
import time

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

import mlx.core as mx

from bilqis_mlx.runtime.c08_distributed_collective import (
    all_reduce_fp32_rank_mean,
)
from bilqis_mlx.runtime.c08_distributed_evidence import (
    DistributedB11Evidence, all_gather_b11_evidence,
)
from bilqis_mlx.runtime.c08_distributed_outcome import (
    DistributedRuntimeAttestation, all_gather_runtime_attestation,
)
from bilqis_mlx.runtime.atlas_resources import (
    DistributedPartition, DistributedRank, DistributedStepManifest,
    validate_runtime_rank,
)


SCOPE = "SAME_HOST_DISPOSABLE_NOT_HETEROGENEOUS_ACCEPTANCE"


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser()
    parser.add_argument("--backend", default="ring")
    parser.add_argument("--expected-world-size", type=int, default=2)
    return parser


def main() -> None:
    args = _parser().parse_args()
    started = time.perf_counter()
    group = mx.distributed.init(strict=True, backend=args.backend)
    rank = group.rank()
    world_size = group.size()
    if world_size != args.expected_world_size:
        raise RuntimeError(
            f"world size {world_size} != {args.expected_world_size}")
    mlx_version = version("mlx")
    device_family = str(mx.device_info()["device_name"])
    workers = tuple(
        DistributedRank(index, f"probe-rank-{index}", device_family)
        for index in range(world_size))
    manifest = DistributedStepManifest(
        retained_generation=0, retained_manifest_sha256="c" * 64,
        curriculum_release="probe-curriculum",
        source_release="d" * 64, logical_batch_digest="e" * 64,
        partition_seed=0, world_size=world_size, workers=workers,
        mlx_version=mlx_version, backend=args.backend, numeric_precision="fp32")
    partition = DistributedPartition(
        manifest.digest, rank, (rank,), (f"probe-row:{rank}",))
    validate_runtime_rank(
        manifest, partition, group, backend=args.backend,
        device_family=device_family, mlx_version=mlx_version)
    local = mx.array([float(rank + 1)], dtype=mx.float32)
    summed = mx.distributed.all_sum(local, stream=mx.cpu)
    gathered = mx.distributed.all_gather(
        mx.array([rank], dtype=mx.int32), stream=mx.cpu)
    mx.eval(summed, gathered)
    expected_sum = world_size * (world_size + 1) / 2
    if float(summed.item()) != expected_sum:
        raise RuntimeError("all_sum mismatch")
    observed_ranks = tuple(int(value) for value in gathered.tolist())
    if observed_ranks != tuple(range(world_size)):
        raise RuntimeError(f"all_gather rank mismatch: {observed_ranks!r}")
    reduced_gradient, reduced_loss, collective_seconds = (
        all_reduce_fp32_rank_mean(
            {"probe": local}, local,
            local_rows=1, total_rows=world_size, group=group))
    expected_mean = expected_sum / world_size
    if float(reduced_gradient["probe"].item()) != expected_mean:
        raise RuntimeError("C08 collective gradient mismatch")
    if float(reduced_loss.item()) != expected_mean:
        raise RuntimeError("C08 collective loss mismatch")
    local_evidence = DistributedB11Evidence(
        "a" * 64, rank, rank, f"probe-row:{rank}", "b" * 64,
        "probe-run", 0, "c" * 64, ((0, rank),), (), (), (), (), (), (),
        ("probe",), (), "d" * 64,
        (("SOURCE", f"probe-source:{rank}"),), "[]")
    gathered_evidence = all_gather_b11_evidence((local_evidence,), group)
    if tuple(item.rank for item in gathered_evidence) != tuple(range(world_size)):
        raise RuntimeError("C08 portable evidence gather mismatch")
    gathered_runtime = all_gather_runtime_attestation(
        DistributedRuntimeAttestation(
            manifest.digest, rank, manifest.workers[rank].worker_id,
            device_family, mlx_version, manifest.backend,
            manifest.numeric_precision),
        group)
    if tuple(item.rank for item in gathered_runtime) != tuple(range(world_size)):
        raise RuntimeError("C08 runtime attestation gather mismatch")
    receipt = {
        "schema": "bilqis.c08.same-host-mlx-collective-probe/v1",
        "scope": SCOPE,
        "backend": args.backend,
        "mlx_version": mlx_version,
        "device_family": device_family,
        "runtime_rank_attested": True,
        "runtime_attestation_ranks": tuple(item.rank for item in gathered_runtime),
        "rank": rank,
        "world_size": world_size,
        "host": platform.node(),
        "machine": platform.machine(),
        "mlx_rank_env": os.environ.get("MLX_RANK"),
        "all_sum": float(summed.item()),
        "expected_sum": expected_sum,
        "gathered_ranks": observed_ranks,
        "wall_seconds": time.perf_counter() - started,
        "peak_memory_bytes": int(mx.get_peak_memory()),
        "c08_collective_mean": float(reduced_gradient["probe"].item()),
        "c08_collective_seconds": collective_seconds,
        "portable_evidence_rows": tuple(item.row_id for item in gathered_evidence),
    }
    print(json.dumps(receipt, sort_keys=True), flush=True)


if __name__ == "__main__":
    main()
