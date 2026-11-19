#!/usr/bin/env python3
"""Compare loader-backed planning with authenticated Atlas snapshot reuse."""
from __future__ import annotations

import argparse
import json
from pathlib import Path
from statistics import mean
import sys
from time import perf_counter

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from bilqis_mlx.factory.skos_curriculum import (
    SOURCE_FAMILY_ADAPTERS, LearnedFrontier,
    _compile_semantic_curriculum_snapshot, compile_semantic_curriculum,
)
from bilqis_mlx.semantics.atlas.snapshot import (
    AtlasArtifactSelection, load_pinned_atlas_snapshot,
)


SCHEMA = "bilqis.bamf.priority-planning-atlas-profile/v1"


def _selection(path: Path) -> AtlasArtifactSelection:
    payload = json.loads((path / "atlas.json").read_text())
    return AtlasArtifactSelection(
        str(path), path.name, payload["release_sha256"], payload["source_bundle_id"])


def profile(path: Path, repeats: int):
    selection = _selection(path)
    frontier = LearnedFrontier(selection.release_sha256)
    started = perf_counter()
    snapshot = load_pinned_atlas_snapshot(selection)
    load_seconds = perf_counter() - started
    legacy_times, snapshot_times = [], []
    baseline = None
    for _ in range(repeats):
        started = perf_counter()
        legacy = compile_semantic_curriculum(
            selection, SOURCE_FAMILY_ADAPTERS, frontier)
        legacy_times.append(perf_counter() - started)
        started = perf_counter()
        direct = _compile_semantic_curriculum_snapshot(
            snapshot, SOURCE_FAMILY_ADAPTERS, frontier)
        snapshot_times.append(perf_counter() - started)
        if baseline is None:
            baseline = legacy
        if legacy != direct or direct != baseline:
            raise AssertionError("authenticated snapshot changed planning output")
    legacy_mean = mean(legacy_times)
    snapshot_mean = mean(snapshot_times)
    return {
        "schema": SCHEMA,
        "status": "PASS",
        "atlas_bundle_id": selection.bundle_id,
        "release_sha256": selection.release_sha256,
        "source_bundle_id": selection.source_bundle_id,
        "abi_entries": len(snapshot.abi_entries),
        "source_lessons": len(baseline.source_lessons),
        "repeats": repeats,
        "snapshot_load_seconds": load_seconds,
        "legacy_reload_compile_seconds": legacy_times,
        "authenticated_snapshot_compile_seconds": snapshot_times,
        "legacy_mean_seconds": legacy_mean,
        "authenticated_snapshot_mean_seconds": snapshot_mean,
        "mean_saved_seconds": legacy_mean - snapshot_mean,
        "speedup": legacy_mean / snapshot_mean,
        "structurally_identical": True,
    }


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--atlas-bundle", type=Path, required=True)
    parser.add_argument("--repeats", type=int, default=1)
    args = parser.parse_args()
    if args.repeats < 1:
        raise SystemExit("--repeats must be positive")
    result = profile(args.atlas_bundle.expanduser().resolve(), args.repeats)
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
