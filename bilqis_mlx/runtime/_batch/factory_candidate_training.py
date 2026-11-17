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
from .factory_candidate_cost import realized_candidate_cost


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
        salience_supervision, mentor_supervision):
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
        gradient, authorities, target_rows = execute_factory_logical_batch(
            parameters, prepared, source_context, feature_context.snapshot,
            generation, cache, resource_plan,
            salience_supervision=salience_supervision,
            mentor_supervision=mentor_supervision)
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
            gradient.wall_seconds)
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
        stage_metrics=None,
        finalize_candidate=True) -> FactoryCandidateStep:
    stage_metrics = dict(stage_metrics or {})
    if mentor_supervision is not None:
        try:
            mentor_supervision.require_evidence(
                observation.mentors, observation.guidance)
        except ValueError:
            _invalid("FACTORY_MENTOR_EVIDENCE_DRIFT")
    identity_before = candidate_identity_metrics_snapshot()
    resource_plan, memory_budget = _resource_plan(prepared, parent, memory_budget)
    feature_context = _prepared_feature_context(prepared, semantic_context)
    (
        gradient, authorities, target_rows, transaction, loss_total, c08_metrics,
        optimizer_wall_seconds,
    ) = _execute_training_and_admission(
        run_dir, source_context, parent, prepared, feature_context, generation, cache,
        resource_plan, teacher_hparams, max_norm, candidate,
        currentness_transaction, salience_supervision, mentor_supervision)
    stage_metrics["optimizer_admission_wall_seconds"] = optimizer_wall_seconds
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


def _prepare_candidate_step_inputs(
        run_dir, source_context, parent, atlas_artifact_path, feature_artifact_path,
        delivered_rows, capability, delivery, requested_count, source_seed,
        source_each, optimizer_step_seed, visit_provenance, teacher_strategy,
        rehearsal_by_id, salience_provider, candidate, currentness_transaction,
        candidate_step_started_at, currentness_binding_wall_seconds,
        upstream_pre_neural_source_compile_wall_seconds, semantic_context,
        prepared_source):
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
        visit_provenance=visit_provenance, teacher_strategy=teacher_strategy,
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
    return (
        start, cache, generation, stage_metrics, prepared, supervision,
        semantic_context_materialized_in_step,
    )


def _require_mentor_supervision_current(
        mentor_supervision, observation, parent, cache, teacher_strategy,
        source_seed):
    if mentor_supervision is None:
        if (observation.mentors is not None
                or (isinstance(observation.guidance, dict)
                    and observation.guidance.get("schema")
                    == "bilqis.mlx.championship-guidance/v1")):
            _invalid("FACTORY_MENTOR_EVIDENCE_WITHOUT_SUPERVISION")
        return
    from bilqis_mlx.learning._championship.adviser_supervision import (
        MentorSupervision, mentor_policy_binding,
    )
    from bilqis_mlx.learning._championship.cohort_soup import POLICY_ID
    from bilqis_mlx.semantics.domains import contract_digest
    if type(mentor_supervision) is not MentorSupervision:
        _invalid("FACTORY_MENTOR_SUPERVISION_INVALID")
    championship_state = getattr(parent, "championship_state", None)
    if not isinstance(championship_state, dict):
        _invalid("FACTORY_MENTOR_CHAMPIONSHIP_STATE_REQUIRED")
    try:
        mentor_supervision.require_current(
            cache.accepted_manifest_sha256,
            contract_digest(championship_state["identity"]),
            POLICY_ID,
            mentor_policy_binding(POLICY_ID, teacher_strategy),
            source_seed,
        )
        mentor_supervision.require_evidence(
            observation.mentors, observation.guidance)
    except ValueError:
        _invalid("FACTORY_MENTOR_SUPERVISION_CURRENTNESS_DRIFT")


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
    mentor_supervision=None,
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
    (
        start, cache, generation, stage_metrics, prepared, supervision,
        semantic_context_materialized_in_step,
    ) = _prepare_candidate_step_inputs(
        run_dir, source_context, parent, atlas_artifact_path, feature_artifact_path,
        delivered_rows, capability, delivery, requested_count, source_seed,
        source_each, optimizer_step_seed, visit_provenance, teacher_strategy,
        rehearsal_by_id, salience_provider, candidate, currentness_transaction,
        candidate_step_started_at, currentness_binding_wall_seconds,
        upstream_pre_neural_source_compile_wall_seconds, semantic_context,
        prepared_source)
    _require_mentor_supervision_current(
        mentor_supervision, observation, parent, cache, teacher_strategy,
        source_seed)
    return _execute_prepared_candidate(
        run_dir, source_context, parent, atlas_artifact_path, delivered_rows,
        capability=capability, teacher_hparams=teacher_hparams,
        max_norm=max_norm, observation=observation, memory_budget=memory_budget,
        cache=cache, generation=generation, prepared=prepared, start=start,
        capture_diagnostics=capture_diagnostics,
        salience_supervision=supervision, mentor_supervision=mentor_supervision,
        candidate=candidate,
        currentness_transaction=currentness_transaction,
        finalize_candidate=finalize_candidate, semantic_context=semantic_context,
        semantic_context_materialized_in_step=semantic_context_materialized_in_step,
        stage_metrics=stage_metrics)


__all__ = (
    "FactoryCandidateDiagnostics", "FactoryCandidateStep",
    "FactoryDeliveryObservation",
    "execute_factory_candidate_step",
)
