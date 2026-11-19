"""Observed cost accounting for one native Factory candidate step."""
from __future__ import annotations

import time

from bilqis_mlx.runtime.atlas_resources import DistributedStepTelemetry


def _distributed_cost(prepared, gradient, logical_batch_wall_seconds) -> dict:
    metadata = getattr(gradient, "distributed_metadata", None)
    if metadata is None:
        return {}
    manifest = metadata.manifest
    communication = metadata.communication_seconds
    compute = metadata.compute_seconds_per_worker
    peaks = metadata.peak_memory_per_worker
    step_seconds = max(float(logical_batch_wall_seconds or 0.0), 1e-12)
    logical_positions = sum(
        len(item.compiled.compiled.rows[0].positions)
        for item in prepared.compiled_rows)
    telemetry = DistributedStepTelemetry(
        manifest.digest, len(prepared.compiled_rows), logical_positions,
        compute, communication, step_seconds, 1, peaks, manifest.world_size)
    return {
        "c08_distributed_manifest_digest": manifest.digest,
        "c08_distributed_retained_generation": manifest.retained_generation,
        "c08_distributed_retained_manifest_sha256":
            manifest.retained_manifest_sha256,
        "c08_distributed_logical_batch_digest": manifest.logical_batch_digest,
        "c08_distributed_source_release": manifest.source_release,
        "c08_distributed_curriculum_release": manifest.curriculum_release,
        "c08_distributed_world_size": manifest.world_size,
        "c08_distributed_backend": manifest.backend,
        "c08_distributed_device_families": tuple(
            worker.device_family for worker in manifest.workers),
        "c08_distributed_mlx_version": manifest.mlx_version,
        "c08_distributed_numeric_precision": manifest.numeric_precision,
        "c08_distributed_reduction_policy": manifest.reduction_policy,
        "c08_distributed_compute_seconds_per_worker": compute,
        "c08_distributed_communication_seconds": communication,
        "c08_distributed_peak_memory_bytes_per_worker": peaks,
        "c08_distributed_examples_per_second": telemetry.examples_per_second,
        "c08_distributed_positions_per_second": telemetry.positions_per_second,
        "c08_distributed_attempted_steps_per_hour":
            telemetry.attempted_steps_per_hour,
    }


def realized_candidate_cost(
        start, candidate_step_started_at, loss_total, prepared,
        resource_plan, memory_budget, transaction,
        feature_context, semantic_context_materialized_in_step, c08_metrics,
        stage_metrics, gradient, *, invalid):
    gradient_launches, vectorized_microbatches, materialization_barriers, \
        scalar_fallback_rows, logical_batch_wall_seconds = c08_metrics
    b11 = getattr(gradient, "_performance_observation", {})
    if not isinstance(b11, dict):
        b11 = {}
    step_atlas_reloads = (
        feature_context.atlas_reload_count
        if semantic_context_materialized_in_step else 0)
    step_feature_rebuilds = (
        feature_context.feature_manifest_rebuild_count
        if semantic_context_materialized_in_step else 0)
    bound_source_authorities = sum(
        compiled.source_execution_authority is not None
        for compiled in prepared.compiled_rows)
    cold_requalification_rows = len(prepared.compiled_rows) - bound_source_authorities
    if cold_requalification_rows:
        invalid("FACTORY_CANDIDATE_SOURCE_EXECUTION_AUTHORITY_MISSING")
    elapsed = time.perf_counter() - start
    cost = {
        "wall_seconds": elapsed,
        "candidate_step_wall_seconds": time.perf_counter() - candidate_step_started_at,
        "pre_neural_source_compile_wall_seconds": stage_metrics[
            "pre_neural_source_compile_wall_seconds"],
        "currentness_binding_wall_seconds": stage_metrics[
            "currentness_binding_wall_seconds"],
        "b11_preflight_wall_seconds": float(b11.get("b11_preflight_wall_seconds", 0.0)),
        "b11_autodiff_wall_seconds": float(b11.get("b11_autodiff_wall_seconds", 0.0)),
        "optimizer_admission_wall_seconds": stage_metrics[
            "optimizer_admission_wall_seconds"],
        "motif_staging_wall_seconds": stage_metrics["motif_staging_wall_seconds"],
        "candidate_terminal_step": stage_metrics["candidate_terminal_step"],
        "b11_provider_draw_count": int(b11.get("b11_provider_draw_count", 0)),
        "b11_atlas_reload_count": int(b11.get("b11_atlas_reload_count", 0)),
        "logical_rows": len(prepared.compiled_rows),
        "compiled_positions": sum(
            len(item.compiled.compiled.rows[0].positions) for item in prepared.compiled_rows),
        "loss_total": float(loss_total.item()),
        "c08_estimated_peak_bytes": resource_plan.estimated_peak_bytes,
        "c08_memory_budget_bytes": memory_budget.allocation_bytes,
        "c08_gradient_launches": gradient_launches,
        "c08_vectorized_microbatches": vectorized_microbatches,
        "c08_materialization_barriers": materialization_barriers,
        "c08_scalar_fallback_rows": scalar_fallback_rows,
        "c08_logical_batch_wall_seconds": logical_batch_wall_seconds,
        "c08_rows_per_gradient_launch": len(prepared.compiled_rows) / gradient_launches,
        "optimizer_steps": 1,
        "candidate_optimizer_steps": transaction.update_steps,
        "atlas_reload_count": step_atlas_reloads,
        "feature_manifest_rebuild_count": step_feature_rebuilds,
        "visit_atlas_reload_count": feature_context.atlas_reload_count,
        "visit_feature_manifest_rebuild_count": feature_context.feature_manifest_rebuild_count,
        "b11_source_authority_bound_rows": bound_source_authorities,
        "b11_source_cold_requalification_rows": cold_requalification_rows,
    }
    cost.update(_distributed_cost(
        prepared, gradient, logical_batch_wall_seconds))
    return cost


__all__ = ("realized_candidate_cost",)
