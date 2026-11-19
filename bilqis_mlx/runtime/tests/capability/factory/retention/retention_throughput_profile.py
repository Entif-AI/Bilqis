"""Disposable native C05 throughput profile for issue #1389.

This witness creates a temporary generation, performs a genuine source-owned
GPU candidate horizon, then invokes the production Factory C05 owner without
publishing the candidate. It emits one machine-readable profile for comparable
before/after runs.
"""
from __future__ import annotations

from dataclasses import asdict
import json
import os
from pathlib import Path
import resource
import tempfile
import time
from unittest.mock import patch

import mlx.core as mx

from bilqis_mlx.learning.champions import Checkpoint
from bilqis_mlx.runtime.accepted_corrections import AcceptedRuntimeHost
from bilqis_mlx.runtime.admission import _executable_factory_admission
from bilqis_mlx.runtime.bamf_bundle import authenticate_bamf_execution_feature_context
from bilqis_mlx.runtime.bamf_bundle.admission import (
    bind_accepted_execution_cache, load_accepted_generation,
)
from bilqis_mlx.runtime.bamf_first_student import BamfFoundationConfig, preflight_bamf_foundation
from bilqis_mlx.runtime.factory_retention_owner import (
    bind_current_retention_protection_plan, bind_current_retention_source_rows,
    evaluate_factory_retention_candidate,
)
from bilqis_mlx.runtime.mlx_memory import training_memory_policy
from bilqis_mlx.runtime.state import _fingerprint
from bilqis_mlx.runtime.tests.capability.factory.retention.factory_retention_live_support import (
    C05_TRAINING_LEARNING_RATE, HP, live_factory_context,
)
from bilqis_mlx.runtime.tests.capability.factory.owner.bamf_c16_2c_witness_support import (
    real_candidate_training_horizon, real_candidate_training_step,
)
from bilqis_mlx.runtime.tests.custody.bamf_bundle.publication.publication_helpers import (
    host_source_authority_patch,
)
from bilqis_mlx.semantics.atlas.feature_io import persist_feature_manifest
from bilqis_mlx.semantics.atlas.snapshot import (
    AtlasArtifactIdentity,
)
from bilqis_mlx.state_dag import persist


def _memory() -> dict[str, int]:
    usage = resource.getrusage(resource.RUSAGE_SELF)
    return {
        "mlx_active_bytes": int(mx.get_active_memory()),
        "mlx_cache_bytes": int(mx.get_cache_memory()),
        "mlx_peak_bytes": int(mx.get_peak_memory()),
        "host_peak_rss_bytes": int(
            usage.ru_maxrss if os.uname().sysname == "Darwin" else usage.ru_maxrss * 1024),
    }


def _artifact() -> Path:
    artifact_raw = os.environ.get("BILQIS_A01_ATLAS_BUNDLE")
    if not artifact_raw:
        raise SystemExit("BILQIS_A01_ATLAS_BUNDLE is required")
    artifact = Path(artifact_raw).resolve()
    if not artifact.is_dir():
        raise SystemExit(f"BILQIS_A01_ATLAS_BUNDLE is not a directory: {artifact}")
    return artifact


def _prepare_run(stage_root: Path, root: Path, source: Path, artifact: Path):
    run_dir = stage_root / "target"
    source_run = stage_root / "source"
    source_context, _manifest = live_factory_context(root, source)
    atlas = json.loads((artifact / "atlas.json").read_text())
    identity = AtlasArtifactIdentity(
        artifact.name, atlas["release_sha256"], atlas["source_bundle_id"])
    origin = Checkpoint("7" * 64, "bundles/foundation-origin", 0, True)
    _, release_file, admission = _executable_factory_admission(
        source_run, source_context.release, origin,
        _fingerprint(source_context.graph), source_context.graph)
    persist(source_run, {
        "generation": 0,
        "factory_release_sha256": source_context.release.release_sha256,
        "factory_release_file": release_file,
        "factory_admission_v2": asdict(admission),
        "semantic_graph_sha256": _fingerprint(source_context.graph),
        "school": {"current_student": asdict(origin)},
        "result": "READY_FOR_HUMAN_START",
    })
    config = BamfFoundationConfig(
        source_run_dir=str(source_run), run_id="c05-throughput-profile",
        run_seed=993, semantic_graph=source_context.graph,
        atlas_artifact=identity, optimizer_hyperparameters=HP)
    preflight_bamf_foundation(config, source_context.release, run_dir)
    parent = load_accepted_generation(run_dir)
    accepted_context = AcceptedRuntimeHost(run_dir).source_context(
        graph=source_context.graph, source_root=source)
    return run_dir, parent, accepted_context


def _train_candidate(run_dir, parent, source_context, feature_path, artifact,
                     capability: str, source_each: int):
    candidate_horizon = int(os.environ.get(
        "BILQIS_C05_PROFILE_CANDIDATE_HORIZON", "1"))
    if candidate_horizon == 1:
        bound, rows, step = real_candidate_training_step(
            run_dir, parent, source_context, feature_path, artifact,
            learning_rate=C05_TRAINING_LEARNING_RATE, capability=capability,
            source_each=source_each)
    else:
        bound, rows, steps = real_candidate_training_horizon(
            run_dir, parent, source_context, feature_path, artifact,
            learning_rate=C05_TRAINING_LEARNING_RATE,
            horizon=candidate_horizon, capability=capability,
            source_each=source_each)
        step = steps[-1]
    mx.synchronize()
    return bound, rows, step


def _print_preflight(capability, source_each, retention_setup_wall, protection,
                     cached_rows, step, source_context, training_wall) -> None:
    from bilqis_mlx.runtime.factory_retention_owner import (
        _fresh_rows, _training_exclusions,
    )
    training = _training_exclusions(step.transaction)
    fresh = _fresh_rows(
        source_context, (capability,), seed=17, training=training,
        require_independent=False)
    print("C05_RETENTION_THROUGHPUT_PREFLIGHT " + json.dumps({
        "schema": "bilqis.mlx.c05-retention-throughput-preflight/v1",
        "target_capability": capability,
        "training_source_each": source_each,
        "retention_setup_wall_seconds": retention_setup_wall,
        "retention_protection_plan_sha256": protection.digest,
        "retention_cached_capability_ids": [item[0] for item in cached_rows],
        "training_source_families": list(training[0]),
        "training_episode_ids": list(training[1]),
        "fresh_seed": fresh.seed,
        "fresh_row_ids": [row["id"] for row in fresh.rows],
        "training_wall_seconds": training_wall,
    }, sort_keys=True), flush=True)


def _profile_receipt(capability, bound, rows, step, cached_rows, evaluation,
                     issued, observed, training_wall, retention_setup_wall,
                     retention_wall, attempt_wall):
    profile = {}
    for event in observed:
        profile.update(event)
    decision = evaluation.decision
    accepted = bool(issued.accepted)
    steps_per_hour = (
        3600.0 * step.transaction.update_steps / attempt_wall
        if attempt_wall > 0 else None)
    return {
        "schema": "bilqis.mlx.c05-retention-throughput-profile/v1",
        "authorizing": False,
        "published": False,
        "target_capability": capability,
        "candidate_update_steps": step.transaction.update_steps,
        "selected_visit": bound.identity.to_record(),
        "training_row_ids": [row["id"] for row in rows],
        "training_wall_seconds": training_wall,
        "retention_setup_wall_seconds": retention_setup_wall,
        "retention_cached_capability_ids": [item[0] for item in cached_rows],
        "retention_wall_seconds": retention_wall,
        "attempt_wall_seconds": attempt_wall,
        "attempted_steps_per_hour": steps_per_hour,
        "retained_steps_per_hour": steps_per_hour if accepted else 0.0,
        "accepted": accepted,
        "decision_status": decision.status.value,
        "decision_reason": decision.reason,
        "outcome_scores": [list(item) for item in decision.outcome_scores],
        "evaluated_capability_ids": list(decision.evaluated_capability_ids),
        "evidence_sha256": decision.evidence_sha256,
        "policy_sha256": decision.policy_sha256,
        "retention_protection_plan_sha256": decision.retention_protection_plan_sha256,
        "parent_generation": decision.parent_generation,
        "candidate_generation": decision.candidate_generation,
        "parent_candidate_sha256": evaluation.parent_candidate_sha256,
        "candidate_candidate_sha256": evaluation.candidate_candidate_sha256,
        "parent_cache_receipt_reused": (
            evaluation.parent_assessment_cache.reused
            if evaluation.parent_assessment_cache is not None else None),
        "profile": profile,
        "memory": _memory(),
        "mlx_default_device": str(mx.default_device()),
    }


def main() -> int:
    if not mx.metal.is_available():
        raise SystemExit("Apple Metal is required")
    previous_device = mx.default_device()
    mx.set_default_device(mx.gpu)
    artifact = _artifact()
    capability = os.environ.get("BILQIS_C05_PROFILE_CAPABILITY", "B.AND")
    source_each = 4 if capability == "B.AND" else 1
    root = Path.cwd()
    source = (root / "vendor/legacy-v16").resolve()
    if not source.is_dir():
        raise SystemExit("pinned vendor/legacy-v16 source fixture is required")
    memory_policy = training_memory_policy(mx)
    with memory_policy:
        with tempfile.TemporaryDirectory() as directory, host_source_authority_patch():
            stage_root = Path(directory)
            with patch.dict(os.environ, {
                    "BILQIS_DATA_PLANE": str(stage_root / "plane.sqlite3")
            }):
                run_dir, parent, source_context = _prepare_run(
                    stage_root, root, source, artifact)
                retention_setup_started = time.perf_counter()
                accepted_cache = bind_accepted_execution_cache(run_dir)
                protection = bind_current_retention_protection_plan(
                    source_context, parent, accepted_cache)
                cached_rows = bind_current_retention_source_rows(
                    source_context, accepted_cache, capability)
                retention_setup_wall = max(
                    0.0, time.perf_counter() - retention_setup_started)
                feature = authenticate_bamf_execution_feature_context(
                    parent, str(artifact), run_dir)
                feature_path = persist_feature_manifest(
                    feature.features, stage_root / "features").path

                mx.clear_cache()
                mx.reset_peak_memory()
                attempt_started = time.perf_counter()
                training_started = time.perf_counter()
                bound, rows, step = _train_candidate(
                    run_dir, parent, source_context, feature_path, artifact,
                    capability, source_each)
                training_wall = max(0.0, time.perf_counter() - training_started)

                if os.environ.get("BILQIS_C05_PROFILE_PREFLIGHT_ONLY") == "1":
                    _print_preflight(
                        capability, source_each, retention_setup_wall, protection,
                        cached_rows, step, source_context, training_wall)
                    mx.set_default_device(previous_device)
                    return 0

                observed: list[dict] = []
                retention_started = time.perf_counter()
                evaluation = evaluate_factory_retention_candidate(
                    source_context, step.transaction, str(artifact), capability,
                    run_dir=run_dir, observer=observed.append)
                mx.synchronize()
                retention_wall = max(0.0, time.perf_counter() - retention_started)
                from bilqis_mlx.learning.atlas_retention_decision import (
                    issue_factory_retention_decision,
                )
                issued = issue_factory_retention_decision(evaluation)
                attempt_wall = max(0.0, time.perf_counter() - attempt_started)
                receipt = _profile_receipt(
                    capability, bound, rows, step, cached_rows, evaluation, issued,
                    observed, training_wall, retention_setup_wall, retention_wall,
                    attempt_wall)
                print("C05_RETENTION_THROUGHPUT_PROFILE " + json.dumps(
                    receipt, sort_keys=True), flush=True)
    mx.set_default_device(previous_device)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
