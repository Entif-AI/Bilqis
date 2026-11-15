"""Production C02 composition for one source-qualified BAMF candidate step."""
from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
import time

from bilqis_mlx.errors import ErrorBus, SCHOOL
from bilqis_mlx.learning.atlas_engram import MOTIF_PAGE_STATE_BYTES, MotifBudget
from bilqis_mlx.learning.atlas_engram_source import SourceQualifiedMotifRequest
from bilqis_mlx.runtime.atlas_model import (
    BamfGradientExecution,
    bamf_value_and_grad,
)
from bilqis_mlx.runtime.atlas_resources import (
    FrameStats, MemoryBudget, ResourceRow, plan_microbatches,
)
from bilqis_mlx.runtime.backbone_identity import execution_generation_digest
from bilqis_mlx.runtime.bamf_bundle import (
    CompleteStudent, authenticate_bamf_execution_feature_context,
    seal_source_qualified_motif_batch_from_bundle,
    seal_source_qualified_motifs_from_bundle,
    stage_source_qualified_motif_allocation,
)
from bilqis_mlx.runtime.bamf_bundle.admission import (
    admit_uninterrupted_candidate_step, bind_accepted_execution_cache,
)
from bilqis_mlx.runtime.bamf_bundle.execution_cache import (
    bind_candidate_execution_cache,
)
from bilqis_mlx.runtime.factory_task_authority import (
    bind_factory_task_compiled_batch, factory_task_authority,
    factory_task_training_goal,
)
from bilqis_mlx.runtime.model_topology_v2 import bamf_parameter_census
from bilqis_mlx.runtime.task_goal_readout import (
    task_goal_route_plan, task_goal_training_targets,
)
from bilqis_mlx.semantics.frame_compiler import PositionKind

from .atlas_training_delivery import capture_realized_delivery
from .c08_gradient_accumulation import (
    LogicalBatchGradientExecution,
    accumulate_logical_batch_gradients,
)
from .factory_training_bridge import (
    PreparedFactoryTrainingBatch, prepare_factory_training_batch,
)
from .atlas_visit_provenance import BamfVisitProvenance


from .factory_candidate_components import (
    FactoryCandidateDiagnostics, FactoryCandidateStep, FactoryDeliveryObservation,
    _frame_stats, _reporting_diagnostics, _resource_plan, _stage_retained_motifs,
)


def _execute_prepared_candidate(
        run_dir, source_context, parent, atlas_artifact_path, delivered_rows, *,
        capability, teacher_hparams, max_norm, observation, memory_budget,
        cache, generation, prepared, start, capture_diagnostics,
        salience_supervision=None, candidate=None,
        finalize_candidate=True) -> FactoryCandidateStep:
    resource_plan, memory_budget = _resource_plan(prepared, parent, memory_budget)
    feature_context = authenticate_bamf_execution_feature_context(
        parent, atlas_artifact_path, source_context.run_dir)
    parameters = dict((parent.retained_state.optimizer if candidate is None
                       else candidate.optimizer).parameters)
    authorities = [None] * len(prepared.compiled_rows)
    target_rows = [None] * len(prepared.compiled_rows)

    def execute_row(index):
        compiled = prepared.compiled_rows[index]
        authority = factory_task_authority(source_context, compiled)
        compiled = bind_factory_task_compiled_batch(compiled, authority)
        resolved = factory_task_training_goal(source_context, compiled, authority)
        targets, mask = task_goal_training_targets(authority.goal, resolved)
        plan = task_goal_route_plan(
            authority.goal, compiled, feature_context.snapshot, generation)
        gradient = bamf_value_and_grad(
            parameters, compiled, plan, targets, mask, cache,
            salience_supervision=salience_supervision)
        authorities[index] = authority
        target_rows[index] = targets
        return gradient

    if len(prepared.compiled_rows) == 1:
        gradient = execute_row(0)
        transaction = admit_uninterrupted_candidate_step(
            Path(run_dir), parent, loss_bearing_target=True,
            gradient_execution=gradient, teacher_hparams=teacher_hparams,
            max_norm=max_norm, candidate=candidate)
        loss_total = gradient.loss_total
    else:
        gradient = accumulate_logical_batch_gradients(resource_plan, execute_row)
        transaction = admit_uninterrupted_candidate_step(
            Path(run_dir), parent, loss_bearing_target=True,
            logical_batch_execution=gradient,
            training_batch=prepared.training_batch,
            logical_batch_plan=resource_plan,
            teacher_hparams=teacher_hparams, max_norm=max_norm, candidate=candidate)
        loss_total = gradient.weighted_mean_loss
    if finalize_candidate:
        transaction = _stage_retained_motifs(
            run_dir, parent, cache, transaction, prepared, resource_plan, memory_budget)
    cost = {
        "wall_seconds": time.perf_counter() - start,
        "loss_total": float(loss_total.item()),
        "c08_estimated_peak_bytes": resource_plan.estimated_peak_bytes,
        "c08_memory_budget_bytes": memory_budget.allocation_bytes,
        "optimizer_steps": 1,
        "candidate_optimizer_steps": transaction.update_steps,
    }
    capture_realized_delivery(
        prepared.training_batch, source_context, observation.capture,
        capability, observation.step, tuple(delivered_rows),
        generation_binding=generation, option_rows=observation.option_rows,
        priority=observation.priority, preservation=observation.preservation,
        support=observation.support, enrichment=observation.enrichment,
        guidance=observation.guidance, controls=observation.controls,
        seed=observation.seed, cost=cost, prior=observation.prior,
        mentors=observation.mentors)
    diagnostics = _reporting_diagnostics(gradient, capture_diagnostics)
    return FactoryCandidateStep(
        prepared, resource_plan,
        authorities[0] if len(authorities) == 1 else tuple(authorities),
        target_rows[0] if len(target_rows) == 1 else tuple(target_rows),
        diagnostics, transaction, cost)


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
) -> FactoryCandidateStep:
    """Compose C02→C08→B10/B11→candidate custody without publishing state.

    B11 remains row-scoped. C08 plans the complete delivered batch, accumulates
    row-scoped raw MLX gradient trees using plan group weights, unions execution
    participation, and enters B12 exactly once for one logical teacher batch.
    """
    if (not isinstance(parent, CompleteStudent)
            or not isinstance(observation, FactoryDeliveryObservation)
            or type(capture_diagnostics) is not bool
            or type(finalize_candidate) is not bool):
        _invalid("FACTORY_CANDIDATE_STEP_INPUT_INVALID")
    source_context.require_accepted_runtime(Path(run_dir))
    start = time.perf_counter()
    cache = bind_accepted_execution_cache(Path(run_dir))
    generation = execution_generation_digest(
        (parent.retained_state.optimizer if candidate is None else candidate.optimizer).parameters,
        spec=parent.topology, extents=parent.extents)
    if candidate is not None:
        cache = bind_candidate_execution_cache(
            cache, parent, candidate, spec=parent.topology, extents=parent.extents)
    if cache.generation_binding != generation:
        _invalid("FACTORY_CANDIDATE_STEP_GENERATION_DRIFT")
    prepared = prepare_factory_training_batch(
        source_context, parent, atlas_artifact_path, feature_artifact_path,
        delivered_rows, generation, capability=capability, delivery=delivery,
        requested_count=requested_count, source_seed=source_seed,
        source_each=source_each, optimizer_step_seed=optimizer_step_seed,
        visit_provenance=visit_provenance,
        teacher_strategy=teacher_strategy,
        rehearsal_by_id=rehearsal_by_id)
    supervision = None
    if salience_provider is not None:
        from bilqis_mlx.runtime.salience_training import prepare_salience_training
        if not callable(salience_provider):
            _invalid("BAMF_SALIENCE_PROVIDER_REQUIRED")
        prepared, supervision = prepare_salience_training(
            prepared, source_context, salience_provider(prepared))
    return _execute_prepared_candidate(
        run_dir, source_context, parent, atlas_artifact_path, delivered_rows,
        capability=capability, teacher_hparams=teacher_hparams,
        max_norm=max_norm, observation=observation, memory_budget=memory_budget,
        cache=cache, generation=generation, prepared=prepared, start=start,
        capture_diagnostics=capture_diagnostics,
        salience_supervision=supervision, candidate=candidate,
        finalize_candidate=finalize_candidate)


__all__ = (
    "FactoryCandidateDiagnostics", "FactoryCandidateStep",
    "FactoryDeliveryObservation",
    "execute_factory_candidate_step",
)
