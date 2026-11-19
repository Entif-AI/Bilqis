"""Execution half of one accepted C03 priority visit."""
from dataclasses import replace
import math
from pathlib import Path
import time

from bilqis_mlx.errors import ErrorBus, SCHOOL
from bilqis_mlx.factory.teaching import describe_delivered_teaching
from bilqis_mlx.runtime.atlas_optimizer import AdamWHyperparameters
from bilqis_mlx.runtime.atlas_training_contracts import BamfVisitProvenance
from bilqis_mlx.runtime.factory_candidate_training import execute_factory_candidate_step

from .accepted_priority_visit_contracts import _require_issued
from .accepted_teacher_custody import _require_current_visit


def _invalid(reason):
    ErrorBus.Raise(SCHOOL.BAMF_CURRICULUM.INVALID, reason=reason)


def _rehearsal_inputs(rows, bindings, authorities):
    rehearsal = tuple(rows)
    by_id = {} if bindings is None else dict(bindings)
    source_bindings = {} if authorities is None else dict(authorities)
    roles = {row.get("id") for row in rehearsal}
    if set(by_id) != roles:
        _invalid('BAMF_PRIORITY_REHEARSAL_BINDING_DRIFT')
    return rehearsal, by_id, source_bindings


def _candidate_delivery_inputs(
        selection, source_context, prepared_source_rows, prepared_enrichment_rows,
        prepared_rehearsal_rows, rehearsal_by_id, rehearsal_bindings,
        rehearsal_authorities, observation):
    offer = selection.offer
    rows = offer.rows() if prepared_source_rows is None else tuple(prepared_source_rows)
    enrichment = tuple(prepared_enrichment_rows)
    rehearsal, role_bindings, source_authorities = _rehearsal_inputs(
        prepared_rehearsal_rows, rehearsal_by_id, rehearsal_authorities)
    binding_records = {} if rehearsal_bindings is None else dict(rehearsal_bindings)
    if set(binding_records) != set(role_bindings) or set(source_authorities) != set(role_bindings):
        _invalid('BAMF_PRIORITY_REHEARSAL_AUTHORITY_DRIFT')
    capability = offer.capability_id
    execution = source_context.release.execution_plan.capability_map[capability]
    delivery = describe_delivered_teaching(
        source_context.release, capability, execution.teaching_option_ids[0], rows)
    observation = replace(
        observation, option_rows=rows, seed=offer.source_seed,
        **({"enrichment": enrichment} if enrichment else {}))
    return (offer, rows, enrichment, rehearsal, role_bindings, binding_records,
            source_authorities, capability, delivery, observation)


def _candidate_currentness(selection, source_context, prepared_source_rows):
    planning_generation = selection.offer._planning_generation
    from bilqis_mlx.runtime.bamf_bundle.currentness_transaction import (
        refresh_accepted_currentness,
    )
    stage_started = time.perf_counter()
    currentness_step = refresh_accepted_currentness(
        planning_generation._accepted_currentness, planning_generation._parent)
    timings = {
        "accepted_currentness_refresh_wall_seconds": (
            time.perf_counter() - stage_started),
    }
    stage_started = time.perf_counter()
    parent, cache = selection.offer.require_current_parent(source_context)
    timings["accepted_parent_currentness_wall_seconds"] = (
        time.perf_counter() - stage_started)
    lawful_frontier = selection._lawful_frontier
    if (lawful_frontier is None
            or getattr(lawful_frontier, '_planning_generation', None)
               is not planning_generation):
        _invalid('BAMF_PRIORITY_LAWFUL_FRONTIER_BINDING_DRIFT')
    from bilqis_mlx.runtime.lawful_teaching_frontier import (
        require_bound_lawful_teaching_frontier,
    )
    stage_started = time.perf_counter()
    require_bound_lawful_teaching_frontier(
        lawful_frontier, source_context, parent, currentness_step=currentness_step)
    timings["lawful_frontier_currentness_wall_seconds"] = (
        time.perf_counter() - stage_started)
    if selection.offer.capability_id not in set(lawful_frontier.ready_capability_ids):
        _invalid('BAMF_PRIORITY_SELECTION_OUTSIDE_LAWFUL_FRONTIER')
    stage_started = time.perf_counter()
    _require_current_visit(
        parent, cache, selection.visit,
        candidate_identity_sha256=planning_generation.parent_candidate_identity_sha256,
        currentness_step=currentness_step,
        currentness_transaction=planning_generation._accepted_currentness)
    timings["teacher_visit_currentness_wall_seconds"] = (
        time.perf_counter() - stage_started)
    stage_started = time.perf_counter()
    prepared_source = (
        selection.offer.require_current(source_context, parent)
        if prepared_source_rows is None else
        selection.offer.require_current(
            source_context, parent, prepared_rows=prepared_source_rows))
    timings["source_currentness_wall_seconds"] = (
        time.perf_counter() - stage_started)
    return (
        planning_generation, parent, currentness_step,
        planning_generation._authenticated_features, prepared_source, timings,
    )


def execute_accepted_priority_candidate(selection, source_context,
        atlas_artifact_path, feature_artifact_path, *, teacher_hparams, observation,
        optimizer_step_seed, max_norm, memory_budget=None, salience_provider=None,
        capture_diagnostics=False, candidate=None, finalize_candidate=True,
        prepared_source_rows=None, prepared_enrichment_rows=(),
        prepared_rehearsal_rows=(), rehearsal_by_id=None,
        rehearsal_bindings=None, rehearsal_authorities=None,
        candidate_step_started_at=None,
        source_prepare_wall_seconds=0.0,
        distributed_profile=None, distributed_executor=None):
    _require_issued(selection)
    if selection.status != 'TEACHER_SELECTED':
        return selection
    if candidate_step_started_at is None:
        candidate_step_started_at = time.perf_counter()
    (planning_generation, parent, currentness_step, semantic_context,
     prepared_source, currentness_timings) = _candidate_currentness(
        selection, source_context, prepared_source_rows)
    caller_pre_neural_started = time.perf_counter()
    policy = selection.policy
    lr = policy.get('lr') if isinstance(policy, dict) else None
    if (type(teacher_hparams) is not AdamWHyperparameters
            or type(lr) not in (int, float) or not math.isfinite(lr) or lr <= 0):
        _invalid('BAMF_PRIORITY_TEACHER_RATE_INVALID')
    hparams = replace(teacher_hparams, learning_rate=float(lr))
    (offer, rows, enrichment, rehearsal, rehearsal_by_id, rehearsal_bindings,
     rehearsal_authorities, capability, delivery, observation) = _candidate_delivery_inputs(
        selection, source_context, prepared_source_rows, prepared_enrichment_rows,
        prepared_rehearsal_rows, rehearsal_by_id, rehearsal_bindings,
        rehearsal_authorities, observation)
    delivered_rows = (*rows, *rehearsal, *enrichment)
    provenance = BamfVisitProvenance.from_c03_record(selection.visit.identity.to_record())
    caller_pre_neural_wall_seconds = (
        float(source_prepare_wall_seconds)
        + time.perf_counter() - caller_pre_neural_started)
    from bilqis_mlx.runtime.bamf_bundle.currentness_transaction import (
        require_live_accepted_currentness_step,
    )
    stage_started = time.perf_counter()
    require_live_accepted_currentness_step(
        currentness_step, planning_generation._accepted_currentness, parent)
    currentness_timings["accepted_currentness_live_fence_wall_seconds"] = (
        time.perf_counter() - stage_started)
    currentness_wall_seconds = sum(currentness_timings.values())
    result = execute_factory_candidate_step(
        Path(selection._run_dir), source_context, parent,
        atlas_artifact_path, feature_artifact_path, delivered_rows,
        capability=capability, delivery=delivery, requested_count=len(delivered_rows),
        source_seed=offer.source_seed, source_each=len(rows) + len(enrichment),
        optimizer_step_seed=optimizer_step_seed, visit_provenance=provenance,
        teacher_strategy=policy, teacher_hparams=hparams, max_norm=max_norm,
        observation=observation, memory_budget=memory_budget,
        rehearsal_by_id=rehearsal_by_id,
        rehearsal_bindings=rehearsal_bindings,
        rehearsal_authorities=rehearsal_authorities,
        salience_provider=salience_provider, capture_diagnostics=capture_diagnostics,
        candidate=candidate, finalize_candidate=finalize_candidate,
        currentness_transaction=planning_generation._accepted_currentness,
        candidate_step_started_at=candidate_step_started_at,
        currentness_binding_wall_seconds=currentness_wall_seconds,
        upstream_pre_neural_source_compile_wall_seconds=caller_pre_neural_wall_seconds,
        semantic_context=semantic_context,
        prepared_source=(prepared_source if not enrichment and not rehearsal else None),
        distributed_profile=distributed_profile,
        distributed_executor=distributed_executor)
    if not hasattr(result, "realized_cost"):
        return result
    cost = dict(result.realized_cost)
    cost.update(currentness_timings)
    cost["candidate_binding_wall_seconds"] = max(
        0.0, float(cost.get("currentness_binding_wall_seconds", 0.0))
        - currentness_wall_seconds)
    return replace(result, realized_cost=cost)


__all__ = ("execute_accepted_priority_candidate",)
