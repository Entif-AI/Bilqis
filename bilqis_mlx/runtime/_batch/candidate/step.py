"""Run and observe one prepared Factory candidate step before publication."""
from __future__ import annotations

from pathlib import Path
import time

from bilqis_mlx.errors import BilqisError
from bilqis_mlx.learning._atlas_candidate.identity_binding import (
    candidate_identity_metrics_delta, candidate_identity_metrics_snapshot,
)
from bilqis_mlx.runtime.bamf_bundle import AuthenticatedGenerationFeatureContext
from bilqis_mlx.runtime.bamf_bundle.admission import (
    admit_uninterrupted_candidate_step, bind_accepted_execution_cache,
)
from bilqis_mlx.runtime.bamf_bundle.execution_cache import (
    bind_candidate_execution_cache, bind_execution_generation,
)
from bilqis_mlx.runtime.atlas_resources import (
    DistributedExecutionProfile, persist_distributed_manifest,
)

from ..atlas_training_delivery import capture_realized_delivery
from ..factory_candidate_components import (
    FactoryCandidateStep, _invalid, _reporting_diagnostics, _resource_plan,
    _stage_retained_motifs,
)
from bilqis_mlx.runtime.factory_candidate_cost import realized_candidate_cost
from bilqis_mlx.runtime.factory_candidate_microbatch import (
    bind_factory_distributed_outcome, execute_factory_logical_batch,
    execute_factory_training_row,
)
from bilqis_mlx.runtime.c08_distributed_manifest import issue_distributed_step_manifest
from bilqis_mlx.runtime.c08_distributed_outcome import DistributedStepOutcome
from bilqis_mlx.runtime.c08_distributed_executor import DistributedExecutorBinding
from .retry import execute_with_oom_retry


def _realized_candidate_cost(*args, **kwargs):
    """Compatibility seam for the reporting contract after structural extraction."""
    return realized_candidate_cost(*args, **kwargs, invalid=_invalid)


def _prepared_feature_context(prepared, semantic_context):
    feature_context = prepared.semantic_context if semantic_context is None else semantic_context
    if type(feature_context) is not AuthenticatedGenerationFeatureContext:
        _invalid("FACTORY_CANDIDATE_SEMANTIC_CONTEXT_INVALID")
    feature_context.__post_init__()
    return feature_context


def _execute_training_and_admission(
        run_dir, source_context, parent, prepared, feature_context, generation, cache,
        resource_plan, teacher_hparams, max_norm, candidate, currentness_transaction,
        salience_supervision, mentor_supervision, distributed_profile,
        distributed_executor):
    parameters = dict((parent.retained_state.optimizer if candidate is None
                       else candidate.optimizer).parameters)
    if len(prepared.compiled_rows) == 1:
        gradient, authority, targets = execute_factory_training_row(
            parameters, prepared.compiled_rows[0], source_context,
            feature_context.snapshot, generation, cache,
            salience_supervision=salience_supervision,
            mentor_supervision=mentor_supervision)
        authorities, target_rows = (authority,), (targets,)
        optimizer_started = time.perf_counter()
        transaction = admit_uninterrupted_candidate_step(
            Path(run_dir), parent, loss_bearing_target=True,
            gradient_execution=gradient, teacher_hparams=teacher_hparams,
            max_norm=max_norm, candidate=candidate, execution_cache=cache,
            currentness_transaction=currentness_transaction)
        loss_total = gradient.loss_total
        c08_metrics = (1, 0, 1, 0, None)
    else:
        if (distributed_profile is None) != (distributed_executor is None):
            _invalid("FACTORY_DISTRIBUTED_CONFIGURATION_INCOMPLETE")
        if distributed_profile is None:
            gradient, authorities, target_rows = execute_factory_logical_batch(
                parameters, prepared, source_context, feature_context.snapshot,
                generation, cache, resource_plan,
                salience_supervision=salience_supervision,
                mentor_supervision=mentor_supervision)
            logical_batch_wall_seconds = gradient.wall_seconds
        else:
            if (type(distributed_profile) is not DistributedExecutionProfile
                    or type(distributed_executor) is not DistributedExecutorBinding
                    or distributed_executor.profile != distributed_profile):
                _invalid("FACTORY_DISTRIBUTED_CONFIGURATION_INVALID")
            distributed_started = time.perf_counter()
            manifest = issue_distributed_step_manifest(
                parent, prepared.training_batch, resource_plan,
                distributed_profile)
            persist_distributed_manifest(Path(run_dir), manifest)
            outcome = distributed_executor.execute(
                parameters=parameters, prepared=prepared,
                source_context=source_context,
                feature_snapshot=feature_context.snapshot,
                generation=generation, cache=cache, resource_plan=resource_plan,
                manifest=manifest, salience_supervision=salience_supervision,
                mentor_supervision=mentor_supervision)
            if type(outcome) is not DistributedStepOutcome:
                _invalid("FACTORY_DISTRIBUTED_OUTCOME_REQUIRED")
            gradient, authorities, target_rows = bind_factory_distributed_outcome(
                prepared, source_context, feature_context.snapshot, generation,
                resource_plan, manifest, outcome)
            logical_batch_wall_seconds = time.perf_counter() - distributed_started
        optimizer_started = time.perf_counter()
        transaction = admit_uninterrupted_candidate_step(
            Path(run_dir), parent, loss_bearing_target=True,
            logical_batch_execution=gradient,
            training_batch=prepared.training_batch,
            logical_batch_plan=resource_plan,
            teacher_hparams=teacher_hparams, max_norm=max_norm, candidate=candidate,
            execution_cache=cache,
            currentness_transaction=currentness_transaction)
        loss_total = gradient.weighted_mean_loss
        c08_metrics = (
            gradient.gradient_launches, gradient.vectorized_microbatches,
            gradient.materialization_barriers, gradient.scalar_fallback_rows,
            logical_batch_wall_seconds)
    return (
        gradient, authorities, target_rows, transaction, loss_total, c08_metrics,
        time.perf_counter() - optimizer_started,
    )


def _execute_prepared_candidate(
        run_dir, source_context, parent, atlas_artifact_path, delivered_rows, *,
        capability, teacher_hparams, max_norm, observation, memory_budget,
        cache, generation, prepared, start, capture_diagnostics,
        salience_supervision=None, candidate=None, currentness_transaction=None,
        mentor_supervision=None,
        semantic_context=None,
        semantic_context_materialized_in_step=False,
        stage_metrics=None, distributed_profile=None, distributed_executor=None,
        finalize_candidate=True) -> FactoryCandidateStep:
    stage_metrics = dict(stage_metrics or {})
    if mentor_supervision is not None:
        try:
            mentor_supervision.require_evidence(
                observation.mentors, observation.guidance)
        except BilqisError:
            _invalid("FACTORY_MENTOR_EVIDENCE_DRIFT")
    identity_before = candidate_identity_metrics_snapshot()
    resource_plan, memory_budget = _resource_plan(prepared, parent, memory_budget)
    feature_context = _prepared_feature_context(prepared, semantic_context)
    def execute(plan):
        (gradient, authorities, target_rows, transaction, loss_total, c08_metrics,
         optimizer_seconds) = _execute_training_and_admission(
            run_dir, source_context, parent, prepared, feature_context, generation,
            cache, plan, teacher_hparams, max_norm, candidate, currentness_transaction,
            salience_supervision, mentor_supervision, distributed_profile,
            distributed_executor)
        motif_started = time.perf_counter()
        if finalize_candidate:
            transaction = _stage_retained_motifs(
                run_dir, parent, cache, transaction, prepared, plan, memory_budget)
        motif_seconds = time.perf_counter() - motif_started if finalize_candidate else 0.0
        return (gradient, authorities, target_rows, transaction, loss_total,
                c08_metrics, optimizer_seconds, motif_seconds)

    def require_current():
        if currentness_transaction is not None:
            from bilqis_mlx.runtime.bamf_bundle.currentness_transaction import (
                refresh_accepted_currentness,
            )
            refresh_accepted_currentness(currentness_transaction, parent)
        return _candidate_cache_and_generation(
            run_dir, source_context, parent, candidate, currentness_transaction)

    result, resource_plan, retry = execute_with_oom_retry(
        execute, resource_plan, parent=parent, candidate=candidate, prepared=prepared,
        budget=memory_budget, cache=cache, require_current=require_current)
    (gradient, authorities, target_rows, transaction, loss_total, c08_metrics,
     optimizer_wall_seconds, motif_seconds) = result
    stage_metrics["optimizer_admission_wall_seconds"] = optimizer_wall_seconds
    stage_metrics["motif_staging_wall_seconds"] = motif_seconds
    stage_metrics["candidate_terminal_step"] = finalize_candidate
    cost = _realized_candidate_cost(
        start, stage_metrics["candidate_step_started_at"], loss_total,
        prepared, resource_plan, memory_budget, transaction,
        feature_context, semantic_context_materialized_in_step, c08_metrics,
        stage_metrics, gradient)
    if retry is not None:
        cost["c08_oom_retries"] = retry.retries_used
        cost["c08_original_microbatch_size"] = retry.original_plan.microbatch_size
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
