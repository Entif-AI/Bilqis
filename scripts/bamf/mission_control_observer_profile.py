#!/usr/bin/env python3
"""Profile native Mission Control observation without mutating an accepted run."""
from __future__ import annotations

import argparse
from contextlib import redirect_stdout
import io
import json
from pathlib import Path
from statistics import mean
import sys
from time import perf_counter, process_time
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from bilqis_mlx.control_plane.native_source import (
    native_query_catalog, native_query_source, refresh_native_events,
)
from bilqis_mlx.control_plane.native_contracts import run_ref
from bilqis_mlx.control_plane.native_custody import authenticated_history
from bilqis_mlx.control_plane.native_mapping import accepted_records
from bilqis_mlx.control_plane.native_rejections import rejection_material
from bilqis_mlx.control_plane.observed import observed_records
from bilqis_mlx.control_plane.tests.cp07.native_source_support import NativeSourceFixture
from bilqis_mlx.control_plane.tests.observed import test_source as observed_support
from bilqis_mlx.mission_control import MissionControlQueryCatalog
from bilqis_mlx.mission_control.query_contracts import QueryFamily, QueryRequest


SCHEMA = "bilqis.bamf.mission-control.observer-profile/v1"
FAMILIES = tuple(
    family for family in QueryFamily if family.value not in {"reference", "links"})
IDLE_CORE_FRACTION_BUDGET = 0.01
LIVE_CORE_FRACTION_BUDGET = 0.02
WORST_CHANGE_CORE_FRACTION_BUDGET = 0.05


def _measure(fn, count: int):
    samples = []
    for _ in range(count):
        wall, cpu = perf_counter(), process_time()
        fn()
        samples.append((perf_counter() - wall, process_time() - cpu))
    return samples


def _mean_ms(samples, index):
    return mean(item[index] for item in samples) * 1000.0


def _query_round(catalog, run_id):
    pages = []
    for family in FAMILIES:
        pages.append(catalog.query(QueryRequest(family, run_id=run_id)))
    return pages


def _cold_attribution(run_dir: Path):
    def timed(fn):
        wall, cpu = perf_counter(), process_time()
        value = fn()
        return value, (perf_counter() - wall) * 1000.0, (process_time() - cpu) * 1000.0

    history, history_wall, history_cpu = timed(lambda: authenticated_history(run_dir))

    def accepted_projection():
        records, events, parent = [], [], None
        for generation in history:
            generated, emitted = accepted_records(generation, parent)
            records.extend(generated)
            events.extend(emitted)
            parent = generation
        return records, events

    accepted, accepted_wall, accepted_cpu = timed(accepted_projection)
    rejected, rejection_wall, rejection_cpu = timed(
        lambda: rejection_material(run_dir, history))
    health = {}
    for generation in history:
        health_state = generation.learning_health_state
        by_capability = (
            health_state.get("by_capability", {})
            if isinstance(health_state, dict) else {})
        if isinstance(by_capability, dict):
            health[generation.manifest_sha256] = by_capability
    observed, observed_wall, observed_cpu = timed(lambda: observed_records(
        run_dir, tuple(run_ref(item) for item in history),
        accepted_health_by_manifest=health))
    all_records = (*accepted[0], *observed, *rejected[0])
    _catalog, catalog_wall, catalog_cpu = timed(lambda: MissionControlQueryCatalog(all_records))
    return {
        "authenticated_history_wall_ms": history_wall,
        "authenticated_history_cpu_ms": history_cpu,
        "accepted_record_projection_wall_ms": accepted_wall,
        "accepted_record_projection_cpu_ms": accepted_cpu,
        "rejection_ledger_sqlite_wall_ms": rejection_wall,
        "rejection_ledger_sqlite_cpu_ms": rejection_cpu,
        "observation_overlay_wall_ms": observed_wall,
        "observation_overlay_cpu_ms": observed_cpu,
        "catalog_construction_wall_ms": catalog_wall,
        "catalog_construction_cpu_ms": catalog_cpu,
    }


def _real_profile(run_dir: Path):
    pointer = json.loads((run_dir / "bamf-state.json").read_text())
    run_id = pointer["run_id"]
    attribution = _cold_attribution(run_dir)
    uncached = _measure(lambda: _query_round(native_query_catalog(run_dir), run_id), 3)
    source = native_query_source(run_dir)
    prime = _measure(lambda: _query_round(source(), run_id), 1)
    warm = _measure(lambda: _query_round(source(), run_id), 20)
    run_only = _measure(
        lambda: source().query(QueryRequest(QueryFamily.RUN, run_id=run_id)), 50)
    catalog = source()
    pages = _query_round(catalog, run_id)

    def serialize():
        for page in pages:
            json.dumps(catalog.encode_page(page), separators=(",", ":"), sort_keys=True)

    serialization = _measure(serialize, 20)
    return {
        "run_id": run_id,
        "families_per_full_round": len(FAMILIES),
        "uncached_full_round_wall_ms": _mean_ms(uncached, 0),
        "uncached_full_round_cpu_ms": _mean_ms(uncached, 1),
        "cached_prime_full_round_wall_ms": _mean_ms(prime, 0),
        "cached_prime_full_round_cpu_ms": _mean_ms(prime, 1),
        "warm_full_round_wall_ms": _mean_ms(warm, 0),
        "warm_full_round_cpu_ms": _mean_ms(warm, 1),
        "warm_run_query_wall_ms": _mean_ms(run_only, 0),
        "warm_run_query_cpu_ms": _mean_ms(run_only, 1),
        "serialization_full_round_wall_ms": _mean_ms(serialization, 0),
        "serialization_full_round_cpu_ms": _mean_ms(serialization, 1),
        "cold_attribution": attribution,
        "sqlite_role": "cold rejection-ledger authentication only; warm cached query path avoids it",
    }


class _EventSink:
    def __init__(self, run_dir):
        self.run_dir = run_dir

    def publish_event(self, *_args, **_kwargs):
        return None

    def flush_event_telemetry(self):
        return None


def _observation_payload(source, pointer, revision):
    row = observed_support.visit(
        run_id=source.run_id,
        parent_manifest_sha256=pointer["manifest_sha256"],
        revision=revision,
        observed_at=1_800_000_000_000 + revision,
        outcome="COMPLETED",
    )
    return {"schema": "bilqis.bamf.trainer-observed/v1", "visits": [row]}


def _live_profile():
    fixture = NativeSourceFixture()
    fixture.setUp()
    try:
        with redirect_stdout(io.StringIO()):
            source_generation, pointer = fixture.publish_successor()
        query_source = native_query_source(fixture.run)
        query_source()
        sink = _EventSink(fixture.run)
        refresh_native_events(sink)

        def write_observation(revision):
            (fixture.run / "trainer-observed.json").write_text(json.dumps(
                _observation_payload(source_generation, pointer, revision)))

        import bilqis_mlx.control_plane.native_source as native_source_module
        with patch.object(
                native_source_module, "authenticated_history",
                wraps=native_source_module.authenticated_history) as authenticate, patch(
                    "bilqis_mlx.runtime.bamf_bundle.admission.load_accepted_generation",
                    side_effect=AssertionError("live observer cold-loaded accepted student")):
            query_samples, event_samples = [], []
            for revision in range(1, 21):
                write_observation(revision)
                query_samples.extend(_measure(lambda: query_source().query(QueryRequest(
                    QueryFamily.RUN, run_id=source_generation.run_id)), 1))
                write_observation(1000 + revision)
                event_samples.extend(_measure(lambda: refresh_native_events(sink), 1))
            reauths = authenticate.call_count
        unchanged = _measure(lambda: refresh_native_events(sink), 100)
        return {
            "observation_updates": 20,
            "accepted_history_reauthentications": reauths,
            "cold_student_loads": 0,
            "live_run_query_wall_ms": _mean_ms(query_samples, 0),
            "live_run_query_cpu_ms": _mean_ms(query_samples, 1),
            "live_cp04_refresh_wall_ms": _mean_ms(event_samples, 0),
            "live_cp04_refresh_cpu_ms": _mean_ms(event_samples, 1),
            "unchanged_cp04_check_wall_ms": _mean_ms(unchanged, 0),
            "unchanged_cp04_check_cpu_ms": _mean_ms(unchanged, 1),
        }
    finally:
        fixture.tearDown()


def profile(run_dir: Path):
    real = _real_profile(run_dir)
    live = _live_profile()
    idle_fraction = (real["warm_run_query_cpu_ms"] / 1000.0) / 2.0
    nominal_live_fraction = (
        4.0 * live["unchanged_cp04_check_cpu_ms"]
        + live["live_cp04_refresh_cpu_ms"]
        + live["live_run_query_cpu_ms"]
    ) / 1000.0
    worst_change_fraction = 4.0 * (
        live["live_cp04_refresh_cpu_ms"] + live["live_run_query_cpu_ms"]
    ) / 1000.0
    budgets = {
        "idle_core_fraction": IDLE_CORE_FRACTION_BUDGET,
        "nominal_live_core_fraction": LIVE_CORE_FRACTION_BUDGET,
        "worst_change_core_fraction": WORST_CHANGE_CORE_FRACTION_BUDGET,
    }
    measured = {
        "idle_core_fraction": idle_fraction,
        "nominal_live_core_fraction": nominal_live_fraction,
        "worst_change_core_fraction": worst_change_fraction,
    }
    passed = (
        live["accepted_history_reauthentications"] == 0
        and all(measured[key] <= value for key, value in budgets.items()))
    return {
        "schema": SCHEMA,
        "status": "PASS" if passed else "FAIL",
        "budgets": budgets,
        "measured": measured,
        "real_accepted_run": real,
        "disposable_live_observation": live,
        "cadence": {
            "home_recovery_seconds": 2.0,
            "control_plane_subscription_seconds": 0.25,
            "trainer_heartbeat_seconds": 1.0,
        },
        "attribution": {
            "accepted_record_reconstruction": "timed separately in cold_attribution",
            "query_fanout": "measured across 14 native query families",
            "serialization": "measured separately from catalog query execution",
            "sqlite": "timed with rejection-ledger authentication in cold_attribution",
            "event_subscription": "blocking wait; refresh cost measured separately",
        },
    }


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--run-dir", type=Path, required=True)
    args = parser.parse_args()
    result = profile(args.run_dir.expanduser().resolve())
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0 if result["status"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
