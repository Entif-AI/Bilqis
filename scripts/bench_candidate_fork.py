#!/usr/bin/env python3
"""Fresh-process benchmark for historical and MLX-native candidate cloning."""
from __future__ import annotations

import argparse
import gc
import json
import os
import resource
import statistics
import subprocess
import sys
import time

import mlx.core as mx
import mlx.optimizers as optim
import numpy as np


def _peak_rss_bytes() -> int:
    value = int(resource.getrusage(resource.RUSAGE_SELF).ru_maxrss)
    return value if sys.platform == "darwin" else value * 1024


def _tree_nbytes(value) -> int:
    if isinstance(value, mx.array):
        return int(value.nbytes)
    if isinstance(value, dict):
        return sum(_tree_nbytes(item) for item in value.values())
    return 0


def _clone_tree(value, *, host_round_trip: bool):
    if isinstance(value, mx.array):
        if host_round_trip:
            return mx.array(np.asarray(value).copy())
        return mx.array(value)
    if isinstance(value, dict):
        return {
            key: _clone_tree(item, host_round_trip=host_round_trip)
            for key, item in value.items()
        }
    raise TypeError(type(value))


def _child(variant: str, arrays: int, rows: int, cols: int,
           iterations: int) -> dict:
    mx.set_default_device(mx.cpu)
    parameters = {
        f"weight.{index}":
            mx.ones((rows, cols), dtype=mx.float32) * (index + 1)
        for index in range(arrays)
    }
    optimizer = optim.AdamW(learning_rate=1e-4, bias_correction=True)
    optimizer.update(
        parameters,
        {name: mx.zeros_like(value) for name, value in parameters.items()},
    )
    mx.eval(parameters, optimizer.state)

    logical_bytes = _tree_nbytes(parameters) + _tree_nbytes(optimizer.state)
    peak_before = _peak_rss_bytes()
    wall_samples = []
    peak_samples = []
    for _ in range(iterations):
        started = time.perf_counter()
        trial_parameters = _clone_tree(
            parameters, host_round_trip=variant == "historical")
        trial_optimizer = optim.AdamW(
            learning_rate=float(optimizer.learning_rate),
            betas=list(optimizer.betas),
            eps=optimizer.eps,
            weight_decay=optimizer.weight_decay,
            bias_correction=optimizer.bias_correction,
        )
        trial_optimizer.state = _clone_tree(
            optimizer.state, host_round_trip=variant == "historical")
        mx.eval(trial_parameters, trial_optimizer.state)
        wall_samples.append(time.perf_counter() - started)
        peak_samples.append(_peak_rss_bytes())
        del trial_parameters, trial_optimizer
        gc.collect()
    peak_after = peak_samples[-1]

    return {
        "variant": variant,
        "parameter_arrays": arrays,
        "array_shape": [rows, cols],
        "iterations": iterations,
        "logical_candidate_bytes": logical_bytes,
        "host_roundtrip_bytes": logical_bytes if variant == "historical" else 0,
        "wall_seconds_median": statistics.median(wall_samples),
        "wall_seconds_samples": wall_samples,
        "peak_rss_before_bytes": peak_before,
        "peak_rss_after_bytes": peak_after,
        "peak_rss_delta_bytes": peak_after - peak_before,
        "peak_rss_by_iteration_bytes": peak_samples,
    }


def _main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--variant", choices=("historical", "native"))
    parser.add_argument("--arrays", type=int, default=16)
    parser.add_argument("--rows", type=int, default=1024)
    parser.add_argument("--cols", type=int, default=1024)
    parser.add_argument("--iterations", type=int, default=1)
    args = parser.parse_args()

    if args.variant is not None:
        print(json.dumps(
            _child(args.variant, args.arrays, args.rows, args.cols,
                   args.iterations),
            sort_keys=True,
        ))
        return 0

    results = []
    for variant in ("historical", "native"):
        command = [
            sys.executable,
            os.path.abspath(__file__),
            "--variant", variant,
            "--arrays", str(args.arrays),
            "--rows", str(args.rows),
            "--cols", str(args.cols),
            "--iterations", str(args.iterations),
        ]
        completed = subprocess.run(
            command, check=True, capture_output=True, text=True)
        results.append(json.loads(completed.stdout))
    print(json.dumps({"results": results}, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(_main())
