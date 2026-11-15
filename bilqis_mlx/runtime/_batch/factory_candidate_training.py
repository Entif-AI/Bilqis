"""Production C02 composition for one source-qualified BAMF candidate step."""
from __future__ import annotations

from pathlib import Path
import time

from bilqis_mlx.runtime.atlas_resources import MemoryBudget
from bilqis_mlx.runtime.bamf_bundle import (
    AuthenticatedGenerationFeatureContext, CompleteStudent,
)
from bilqis_mlx.runtime.bamf_bundle.admission import (
    admit_uninterrupted_candidate_step, bind_accepted_execution_cache,
)
from bilqis_mlx.runtime.bamf_bundle.execution_cache import (
    bind_candidate_execution_cache, bind_execution_generation,
)
from bilqis_mlx.learning._atlas_candidate.identity_binding import (
    candidate_identity_metrics_delta, candidate_identity_metrics_snapshot,
)

from .atlas_training_delivery import capture_realized_delivery
from .factory_candidate_microbatch import (
    execute_factory_logical_batch, execute_factory_training_row,
)
from .factory_training_bridge import (
    PreparedFactoryTrainingBatch, prepare_factory_training_batch,
)
from .atlas_visit_provenance import BamfVisitProvenance


from .factory_candidate_components import (
    FactoryCandidateDiagnostics, FactoryCandidateStep, FactoryDeliveryObservation,
    _frame_stats, _invalid, _reporting_diagnostics, _resource_plan,
    _stage_retained_motifs,
)


def _prepared_feature_context(prepared, semantic_context):
    feature_context = prepared.semantic_context if semantic_context is None else semantic_context
    if type(feature_context) is not AuthenticatedGenerationFeatureContext:
        _invalid("FACTORY_CANDIDATE_SEMANTIC_CONTEXT_INVALID")
    feature_context.__post_init__()
    return feature_context


def _realized_candidate_cost(
        start, candidate_step_started_at, loss_total, prepared,
        resource_plan, memory_budget, transaction,
        feature_context, semantic_context_materialized_in_step, c08_metrics,
        stage_metrics, gradient):
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
    elapsed = time.perf_counter() - start
    return {
        "wall_seconds": elapsed,
        "candidate_step_wall_seconds": (
            time.perf_counter() - candidate_step_started_at),
        "pre_neural_source_compile_wall_seconds": stage_metrics[
            "pre_neural_source_compile_wall_seconds"],
        "currentness_binding_wall_seconds": stage_metrics[
            "currentness_binding_wall_seconds"],
        "b11_preflight_wall_seconds": float(
            b11.get("b11_preflight_wall_seconds", 0.0)),
        "b11_autodiff_wall_seconds": float(
            b11.get("b11_autodiff_wall_seconds", 0.0)),
        "optimizer_admission_wall_seconds": stage_metrics[
            "optimizer_admission_wall_seconds"],
        "motif_staging_wall_seconds": stage_metrics[
            "motif_staging_wall_seconds"],
        "candidate_terminal_step": stage_metrics["candidate_terminal_step"],
        "b11_provider_draw_count": int(b11.get("b11_provider_draw_count", 0)),
        "b11_atlas_reload_count": int(b11.get("b11_atlas_reload_count", 0)),
        "logical_rows": len(prepared.compiled_rows),
        "compiled_positions": sum(
            len(item.compiled.compiled.rows[0].positions)
            for item in prepared.compiled_rows),
        "loss_total": float(loss_total.item()),
        "c08_estimated_peak_bytes": resource_plan.estimated_peak_bytes,
        "c08_memory_budget_bytes": memory_budget.allocation_bytes,
        "c08_gradient_launches": gradient_launches,
        "c08_vectorized_microbatches": vectorized_microbatches,
        "c08_materialization_barriers": materialization_barriers,
        "c08_scalar_fallback_rows": scalar_fallback_rows,
        "c08_logical_batch_wall_seconds": logical_batch_wall_seconds,
        "c08_rows_per_gradient_launch": (
            len(prepared.compiled_rows) / gradient_launches),
        "optimizer_steps": 1,
        "candidate_optimizer_steps": transaction.update_steps,
        "atlas_reload_count": step_atlas_reloads,
        "feature_manifest_rebuild_count": step_feature_rebuilds,
        "visit_atlas_reload_count": feature_context.atlas_reload_count,
        "visit_feature_manifest_rebuild_count": (
            feature_context.feature_manifest_rebuild_count),
    }


def _execute_prepared_candidate(
        run_dir, source_context, parent, atlas_artifact_path, delivered_rows, *,
        capability, teacher_hparams, max_norm, observation, memory_budget,
        cache, generation, prepared, start, capture_diagnostics,
        salience_supervision=None, candidate=None, currentness_transaction=None,
        semantic_context=None,
        semantic_context_materialized_in_step=False,
        stage_metrics=None,
        finalize_candidate=True) -> FactoryCandidateStep:
    stage_metrics = dict(stage_metrics or {})
    identity_before = candidate_identity_metrics_snapshot()
    resource_plan, memory_budget = _resource_plan(prepared, parent, memory_budget)
    feature_context = _prepared_feature_context(prepared, semantic_context)
    parameters = dict((parent.retained_state.optimizer if candidate is None
                       else candidate.optimizer).parameters)

    if len(prepared.compiled_rows) == 1:
        gradient, authority, targets = execute_factory_training_row(
            parameters, prepared.compiled_rows[0], source_context,
            feature_context.snapshot, generation, cache,
            salience_supervision=salience_supervision)
        authorities, target_rows = (authority,), (targets,)
        optimizer_started = time.perf_counter()
        transaction = admit_uninterrupted_candidate_step(
            Path(run_dir), parent, loss_bearing_target=True,
            gradient_execution=gradient, teacher_hparams=teacher_hparams,
            max_norm=max_norm, candidate=candidate, execution_cache=cache,
            currentness_transaction=currentness_transaction)
        stage_metrics["optimizer_admission_wall_seconds"] = (
            time.perf_counter() - optimizer_started)
        loss_total = gradient.loss_total
        c08_metrics = (1, 0, 1, 0, None)
    else:
        gradient, authorities, target_rows = execute_factory_logical_batch(
            parameters, prepared, source_context, feature_context.snapshot,
            generation, cache, resource_plan,
            salience_supervision=salience_supervision)
        optimizer_started = time.perf_counter()
        transaction = admit_uninterrupted_candidate_step(
            Path(run_dir), parent, loss_bearing_target=True,
            logical_batch_execution=gradient,
            training_batch=prepared.training_batch,
            logical_batch_plan=resource_plan,
            teacher_hparams=teacher_hparams, max_norm=max_norm, candidate=candidate,
            execution_cache=cache,
            currentness_transaction=currentness_transaction)
        stage_metrics["optimizer_admission_wall_seconds"] = (
            time.perf_counter() - optimizer_started)
        loss_total = gradient.weighted_mean_loss
        c08_metrics = (
            gradient.gradient_launches, gradient.vectorized_microbatches,
            gradient.materialization_barriers, gradient.scalar_fallback_rows,
            gradient.wall_seconds)
    motif_started = time.perf_counter()
    if finalize_candidate:
        transaction = _stage_retained_motifs(
            run_dir, parent, cache, transaction, prepared, resource_plan, memory_budget)
    stage_metrics["motif_staging_wall_seconds"] = (
        time.perf_counter() - motif_started if finalize_candidate else 0.0)
    stage_metrics["candidate_terminal_step"] = finalize_candidate
    cost = _realized_candidate_cost(
        start, stage_metrics["candidate_step_started_at"], loss_total,
        prepared, resource_plan, memory_budget, transaction,
        feature_context, semantic_context_materialized_in_step, c08_metrics,
        stage_metrics, gradient)
    cost.update(candidate_identity_metrics_delta(identity_before))
    evidence_started = time.perf_counter()
    capture_realized_delivery(
        prepared.training_batch, source_context, observation.capture,
        capability, observation.step, tuple(delivered_rows),
        generation_binding=generation, option_rows=observation.option_rows,
        priority=observation.priority, preservation=observation.preservation,
        support=observation.support, enrichment=observation.enrichment,
        guidance=observation.guidance, controls=observation.controls,
        seed=observation.seed, cost=cost, prior=observation.prior,
        mentors=observation.mentors)
    cost["evidence_capture_wall_seconds"] = time.perf_counter() - evidence_started
    elapsed = time.perf_counter() - start
    cost["wall_seconds"] = elapsed
    cost["candidate_step_wall_seconds"] = (
        time.perf_counter() - stage_metrics["candidate_step_started_at"])
    diagnostics = _reporting_diagnostics(gradient, capture_diagnostics)
    return FactoryCandidateStep(
        prepared, resource_plan,
        authorities[0] if len(authorities) == 1 else authorities,
        target_rows[0] if len(target_rows) == 1 else target_rows,
        diagnostics, transaction, cost)


def _candidate_cache_and_generation(run_dir, source_context, parent, candidate,
                                    currentness_transaction):
    source_context.require_accepted_runtime(Path(run_dir))
    if currentness_transaction is None:
        cache = bind_accepted_execution_cache(Path(run_dir))
    else:
        from bilqis_mlx.runtime.bamf_bundle.currentness_transaction import (
            require_accepted_currentness,
        )
        cache = require_accepted_currentness(
            currentness_transaction, parent=parent)._cache
    if candidate is not None:
        cache = bind_candidate_execution_cache(
            cache, parent, candidate, spec=parent.topology, extents=parent.extents)
    parameters = (
        parent.retained_state.optimizer if candidate is None else candidate.optimizer
    ).parameters
    generation = bind_execution_generation(
        cache, parameters, spec=parent.topology,
        extents=parent.extents).generation_digest
    if cache.generation_binding != generation:
        _invalid("FACTORY_CANDIDATE_STEP_GENERATION_DRIFT")
    return cache, generation


def execute_factory_candidate_step(
    run_dir: Path,
    source_context,
    parent: CompleteStudent,
    atlas_artifact_path: str,
    feature_artifact_path: str,
    delivered_rows,
    *,
    capability: str,
    delivery,
    requested_count: int,
    source_seed: int,
    source_each: int,
    optimizer_step_seed: int,
    visit_provenance: BamfVisitProvenance,
    teacher_strategy: dict,
    teacher_hparams,
    max_norm: float,
    observation: FactoryDeliveryObservation,
    rehearsal_by_id: dict | None = None,
    memory_budget: MemoryBudget | None = None,
    capture_diagnostics: bool = False,
    salience_provider=None,
    candidate=None,
    finalize_candidate: bool = True,
    currentness_transaction=None,
    candidate_step_started_at: float | None = None,
    currentness_binding_wall_seconds: float = 0.0,
    upstream_pre_neural_source_compile_wall_seconds: float = 0.0,
    semantic_context=None,
    prepared_source=None,
) -> FactoryCandidateStep:
    """Compose C02→C08→B10/B11→candidate custody without publishing state.

    C08 plans the complete delivered batch, vectorizes compatible planned groups,
    preserves row-scoped B11 loss/authority evidence, accumulates group gradients
    with plan weights, and enters B12 exactly once per logical teacher step.
    """
    if (not isinstance(parent, CompleteStudent)
            or not isinstance(observation, FactoryDeliveryObservation)
            or type(capture_diagnostics) is not bool
            or type(finalize_candidate) is not bool):
        _invalid("FACTORY_CANDIDATE_STEP_INPUT_INVALID")
    start = time.perf_counter()
    if candidate_step_started_at is None:
        candidate_step_started_at = start
    binding_started = time.perf_counter()
    cache, generation = _candidate_cache_and_generation(
        run_dir, source_context, parent, candidate, currentness_transaction)
    stage_metrics = {
        "candidate_step_started_at": candidate_step_started_at,
        "currentness_binding_wall_seconds": (
            float(currentness_binding_wall_seconds)
            + time.perf_counter() - binding_started),
    }
    semantic_context_materialized_in_step = semantic_context is None
    pre_neural_started = time.perf_counter()
    prepared = prepare_factory_training_batch(
        source_context, parent, atlas_artifact_path, feature_artifact_path,
        delivered_rows, generation, capability=capability, delivery=delivery,
        requested_count=requested_count, source_seed=source_seed,
        source_each=source_each, optimizer_step_seed=optimizer_step_seed,
        visit_provenance=visit_provenance,
        teacher_strategy=teacher_strategy,
        rehearsal_by_id=rehearsal_by_id, semantic_context=semantic_context,
        prepared_source=prepared_source)
    supervision = None
    if salience_provider is not None:
        from bilqis_mlx.runtime.salience_training import prepare_salience_training
        if not callable(salience_provider):
            _invalid("BAMF_SALIENCE_PROVIDER_REQUIRED")
        prepared, supervision = prepare_salience_training(
            prepared, source_context, salience_provider(prepared))
    stage_metrics["pre_neural_source_compile_wall_seconds"] = (
        float(upstream_pre_neural_source_compile_wall_seconds)
        + time.perf_counter() - pre_neural_started)
    return _execute_prepared_candidate(
        run_dir, source_context, parent, atlas_artifact_path, delivered_rows,
        capability=capability, teacher_hparams=teacher_hparams,
        max_norm=max_norm, observation=observation, memory_budget=memory_budget,
        cache=cache, generation=generation, prepared=prepared, start=start,
        capture_diagnostics=capture_diagnostics,
        salience_supervision=supervision, candidate=candidate,
        currentness_transaction=currentness_transaction,
        finalize_candidate=finalize_candidate, semantic_context=semantic_context,
        semantic_context_materialized_in_step=semantic_context_materialized_in_step,
        stage_metrics=stage_metrics)


__all__ = (
    "FactoryCandidateDiagnostics", "FactoryCandidateStep",
    "FactoryDeliveryObservation",
    "execute_factory_candidate_step",
)
