"""Bounded full-B01 identity benchmark; disposable initialization, zero updates.

Run from the repository root with python3 -B -m scripts.bamf.benchmark_candidate_identity.
Each measurement uses a cold process with the same full topology and run seed.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import resource
import subprocess
import sys
import time
from types import SimpleNamespace


MODES = ('original', 'legacy-stream', 'raw-v2', 'raw-v2')


def _original(state):
    import numpy as np
    from bilqis_mlx.learning._retention._atlas_acceptance_records import canonical

    parts = {group: {name: np.asarray(value).tobytes().hex()
                     for name, value in sorted(getattr(state.optimizer, group).items())}
             for group in ('parameters', 'm', 'v', 'update_counts')}
    return hashlib.sha256(canonical({
        'state': parts, 'optimizer_step': state.optimizer_step})).hexdigest()


def measure(mode):
    import mlx.core as mx
    from bilqis_mlx.learning._retention.candidate_identity import (
        LEGACY_IDENTITY_SCHEME, RAW_IDENTITY_SCHEME, candidate_identity_digest,
    )
    from bilqis_mlx.runtime.atlas_optimizer import _create_unbound_bamf_optimizer
    from bilqis_mlx.runtime.model_topology_v2 import (
        GenerationExtents, ModelTopologySpecV2,
    )

    mx.set_cache_limit(0)
    mx.set_memory_limit(6 * 1024**3)
    topology = ModelTopologySpecV2()
    extents = GenerationExtents(1, 1, 'a' * 64, 'b' * 64, 'c' * 64)
    optimizer, _, _ = _create_unbound_bamf_optimizer(topology, extents, run_seed=1169)
    groups = [getattr(optimizer, name) for name in ('parameters', 'm', 'v', 'update_counts')]
    mx.eval(*groups)
    state = SimpleNamespace(optimizer=optimizer, optimizer_step=7,
                            identity_scheme=(RAW_IDENTITY_SCHEME if mode == 'raw-v2'
                                             else LEGACY_IDENTITY_SCHEME))
    before = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
    wall, cpu = time.perf_counter(), time.process_time()
    digest = _original(state) if mode == 'original' else candidate_identity_digest(state)
    cpu, wall = time.process_time() - cpu, time.perf_counter() - wall
    # Darwin reports bytes; Linux reports KiB.
    scale = 1 if sys.platform == 'darwin' else 1024
    return {
        'mode': mode, 'digest': digest, 'wall_seconds': wall, 'cpu_seconds': cpu,
        'peak_rss_bytes': resource.getrusage(resource.RUSAGE_SELF).ru_maxrss * scale,
        'setup_peak_rss_bytes': before * scale,
        'tensor_count': sum(len(group) for group in groups),
        'tensor_bytes': sum(value.nbytes for group in groups for value in group.values()),
        'parameter_count': sum(value.size for value in optimizer.parameters.values()),
        'topology_sha256': topology.digest, 'extents_sha256': extents.digest,
        'mlx_memory_limit_bytes': 6 * 1024**3, 'mlx_cache_limit_bytes': 0,
        'scope': 'DISPOSABLE_FULL_B01_IDENTITY_ONLY_ZERO_OPTIMIZER_UPDATES',
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--worker', choices=set(MODES))
    args = parser.parse_args()
    if args.worker:
        print(json.dumps(measure(args.worker), sort_keys=True))
        return
    from bilqis_mlx.runtime.disk import assert_headroom
    assert_headroom(Path.cwd(), required_bytes=0)
    rows = []
    for mode in MODES:
        result = subprocess.run(
            [sys.executable, '-B', '-m', 'scripts.bamf.benchmark_candidate_identity',
             '--worker', mode], capture_output=True, text=True, check=True, timeout=120)
        rows.append(json.loads(result.stdout))
    if rows[0]['digest'] != rows[1]['digest'] or rows[2]['digest'] != rows[3]['digest']:
        raise AssertionError('Historical identity or cold-process determinism differs')
    if any(row['tensor_bytes'] != rows[0]['tensor_bytes'] for row in rows):
        raise AssertionError('Benchmark state sizes differ')
    original, raw = rows[0], rows[2]
    result = {
        'measurements': rows,
        'raw_cpu_speedup': original['cpu_seconds'] / raw['cpu_seconds'],
        'raw_peak_rss_reduction_fraction': 1 - raw['peak_rss_bytes'] / original['peak_rss_bytes'],
    }
    if result['raw_cpu_speedup'] <= 1 or result['raw_peak_rss_reduction_fraction'] <= 0:
        raise AssertionError(json.dumps(result))
    print(json.dumps(result, indent=2, sort_keys=True))


if __name__ == '__main__':
    main()
