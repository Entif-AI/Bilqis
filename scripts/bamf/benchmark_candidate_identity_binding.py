"""Disposable full-B01 #1238 first-bind versus repeated-require benchmark.

This constructs the same full B01 optimizer geometry used by the #1169 identity
benchmark, performs zero optimizer updates, binds identity once, then requires
that exact immutable binding repeatedly. Run from the repository root.
"""
from __future__ import annotations

import argparse
import json
import time


def measure(requires: int) -> dict:
    import mlx.core as mx

    from bilqis_mlx.learning.atlas_candidate import CandidateState
    from bilqis_mlx.learning.atlas_engram import MotifManifest
    from bilqis_mlx.learning.atlas_engram_transaction import MotifAllocationSnapshot
    from bilqis_mlx.learning.atlas_plasticity import PlasticityPolicy
    from bilqis_mlx.learning._atlas_candidate.identity_binding import (
        _reset_candidate_identity_metrics_for_tests,
        bind_candidate_identity,
        candidate_identity_metrics_snapshot,
        require_candidate_identity_binding,
    )
    from bilqis_mlx.runtime.atlas_optimizer import _create_unbound_bamf_optimizer
    from bilqis_mlx.runtime.model_topology_v2 import (
        GenerationExtents, ModelTopologySpecV2,
    )

    mx.set_cache_limit(0)
    mx.set_memory_limit(6 * 1024**3)
    topology = ModelTopologySpecV2()
    extents = GenerationExtents(1, 1, "a" * 64, "b" * 64, "c" * 64)
    optimizer, _, _ = _create_unbound_bamf_optimizer(
        topology, extents, run_seed=1238)
    mx.eval(optimizer.parameters, optimizer.m, optimizer.v, optimizer.update_counts)
    state = CandidateState(
        optimizer,
        PlasticityPolicy("FOUNDATION", 0, ()),
        MotifAllocationSnapshot(MotifManifest("d" * 64)),
        0,
    )

    _reset_candidate_identity_metrics_for_tests()
    started = time.perf_counter()
    binding = bind_candidate_identity(state, topology.digest, extents.digest)
    first_wall = time.perf_counter() - started
    first_metrics = candidate_identity_metrics_snapshot()

    started = time.perf_counter()
    for _ in range(requires):
        require_candidate_identity_binding(
            state, topology.digest, extents.digest, binding)
    require_wall = time.perf_counter() - started
    final_metrics = candidate_identity_metrics_snapshot()
    tensor_bytes = sum(
        int(value.nbytes)
        for group in (optimizer.parameters, optimizer.m, optimizer.v,
                      optimizer.update_counts)
        for value in group.values())
    average_require = require_wall / requires
    return {
        "scope": "DISPOSABLE_FULL_B01_IDENTITY_BINDING_ZERO_OPTIMIZER_UPDATES",
        "digest": binding.digest,
        "tensor_bytes": tensor_bytes,
        "first_bind_wall_seconds": first_wall,
        "average_require_wall_seconds": average_require,
        "require_count": requires,
        "wall_speedup_first_bind_over_require": first_wall / average_require,
        "first_bind_metrics": first_metrics,
        "final_metrics": final_metrics,
        "topology_sha256": topology.digest,
        "extents_sha256": extents.digest,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--requires", type=int, default=25)
    args = parser.parse_args()
    if args.requires < 1:
        parser.error("--requires must be >= 1")
    result = measure(args.requires)
    if result["first_bind_metrics"]["candidate_identity_full_computations"] != 1:
        raise AssertionError(json.dumps(result))
    if result["final_metrics"]["candidate_identity_full_computations"] != 1:
        raise AssertionError(json.dumps(result))
    print(json.dumps(result, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
