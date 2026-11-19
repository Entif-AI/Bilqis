#!/usr/bin/env python3
"""Disposable proof of the production coordinator -> MLX worker-cohort surface."""
from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys

import mlx.core as mx

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from bilqis_mlx.runtime.atlas_resources import DistributedRank
from bilqis_mlx.runtime.c08_distributed_executor import (
    configure_mlx_distributed_execution,
)


SCOPE = "SAME_HOST_DISPOSABLE_WORKER_COHORT_NOT_HETEROGENEOUS_ACCEPTANCE"


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--backend", default="ring")
    parser.add_argument("--world-size", type=int, default=2)
    args = parser.parse_args()
    device = str(mx.device_info()["device_name"])
    workers = tuple(
        DistributedRank(rank, f"probe-rank-{rank}", device)
        for rank in range(args.world_size))
    binding = configure_mlx_distributed_execution(
        workers, hosts=("127.0.0.1",), partition_seed=0,
        backend=args.backend, working_directory=ROOT)
    outcome = binding.probe()
    print(json.dumps({
        "schema": "bilqis.c08.worker-cohort-launcher-probe/v1",
        "scope": SCOPE,
        "backend": args.backend,
        "world_size": args.world_size,
        "worker_outcome": outcome,
    }, sort_keys=True))


if __name__ == "__main__":
    main()
