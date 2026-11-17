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


def execute_accepted_priority_candidate(selection, source_context,
        atlas_artifact_path, feature_artifact_path, *, teacher_hparams, observation,
        optimizer_step_seed, max_norm, memory_budget=None, salience_provider=None,
        capture_diagnostics=False, candidate=None, finalize_candidate=True,
        prepared_source_rows=None, prepared_enrichment_rows=(),
        candidate_step_started_at=None,
        source_prepare_wall_seconds=0.0):
    _require_issued(selection)
    if selection.status != 'TEACHER_SELECTED':
        return selection
    planning_generation = selection.offer._planning_generation
    from bilqis_mlx.runtime.bamf_bundle.currentness_transaction import (
        refresh_accepted_currentness,
    )
    if candidate_step_started_at is None:
        candidate_step_started_at = time.perf_counter()
    currentness_started = time.perf_counter()
    refresh_accepted_currentness(
        planning_generation._accepted_currentness, planning_generation._parent)
    parent, cache = selection.offer.require_current_parent(source_context)
    lawful_frontier = selection._lawful_frontier
    if (lawful_frontier is None
            or getattr(lawful_frontier, '_planning_generation', None)
               is not planning_generation):
        _invalid('BAMF_PRIORITY_LAWFUL_FRONTIER_BINDING_DRIFT')
    from bilqis_mlx.runtime.lawful_teaching_frontier import (
        require_bound_lawful_teaching_frontier,
    )
    require_bound_lawful_teaching_frontier(lawful_frontier, source_context, parent)
    if selection.offer.capability_id not in set(lawful_frontier.ready_capability_ids):
        _invalid('BAMF_PRIORITY_SELECTION_OUTSIDE_LAWFUL_FRONTIER')
    semantic_context = planning_generation._authenticated_features
    _require_current_visit(
        parent, cache, selection.visit,
        candidate_identity_sha256=planning_generation.parent_candidate_identity_sha256)
    prepared_source = (
        selection.offer.require_current(source_context, parent)
        if prepared_source_rows is None else
        selection.offer.require_current(
            source_context, parent, prepared_rows=prepared_source_rows))
    currentness_wall_seconds = time.perf_counter() - currentness_started
    caller_pre_neural_started = time.perf_counter()
    policy = selection.policy
    lr = policy.get('lr') if isinstance(policy, dict) else None
    if (type(teacher_hparams) is not AdamWHyperparameters
            or type(lr) not in (int, float) or not math.isfinite(lr) or lr <= 0):
        _invalid('BAMF_PRIORITY_TEACHER_RATE_INVALID')
    hparams = replace(teacher_hparams, learning_rate=float(lr))
    offer = selection.offer
    rows = offer.rows() if prepared_source_rows is None else tuple(prepared_source_rows)
    enrichment = tuple(prepared_enrichment_rows)
    delivered_rows = (*rows, *enrichment)
    capability = offer.capability_id
    execution = source_context.release.execution_plan.capability_map[capability]
    delivery = describe_delivered_teaching(
        source_context.release, capability, execution.teaching_option_ids[0], rows)
    provenance = BamfVisitProvenance.from_c03_record(selection.visit.identity.to_record())
    observation = replace(
        observation, option_rows=rows, seed=offer.source_seed,
        **({"enrichment": enrichment} if enrichment else {}))
    caller_pre_neural_wall_seconds = (
        float(source_prepare_wall_seconds)
        + time.perf_counter() - caller_pre_neural_started)
    return execute_factory_candidate_step(
        Path(selection._run_dir), source_context, parent,
        atlas_artifact_path, feature_artifact_path, delivered_rows,
        capability=capability, delivery=delivery, requested_count=len(delivered_rows),
        source_seed=offer.source_seed, source_each=len(delivered_rows),
        optimizer_step_seed=optimizer_step_seed, visit_provenance=provenance,
        teacher_strategy=policy, teacher_hparams=hparams, max_norm=max_norm,
        observation=observation, memory_budget=memory_budget,
        salience_provider=salience_provider, capture_diagnostics=capture_diagnostics,
        candidate=candidate, finalize_candidate=finalize_candidate,
        currentness_transaction=planning_generation._accepted_currentness,
        candidate_step_started_at=candidate_step_started_at,
        currentness_binding_wall_seconds=currentness_wall_seconds,
        upstream_pre_neural_source_compile_wall_seconds=caller_pre_neural_wall_seconds,
        semantic_context=semantic_context,
        prepared_source=(prepared_source if not enrichment else None))


__all__ = ("execute_accepted_priority_candidate",)
