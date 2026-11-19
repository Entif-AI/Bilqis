"""Reusable records and preparation helpers for BAMF Factory candidate execution."""
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
    FrameStats, MemoryBudget, MICROBATCH_SIZES, ResourceRow, plan_microbatches,
)
from bilqis_mlx.runtime.backbone_identity import execution_generation_digest
from bilqis_mlx.runtime.bamf_bundle import (
    CompleteStudent,
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


def _invalid(reason: str):
    ErrorBus.raise_(SCHOOL.BAMF_TRAINING_ADAPTER.INVALID, reason=reason)


@dataclass(frozen=True)
class FactoryDeliveryObservation:
    """Existing #333 capture coordinates for one realized C02 delivery."""

    capture: object
    step: int
    option_rows: tuple
    seed: int
    priority: tuple = ()
    preservation: tuple = ()
    support: tuple = ()
    enrichment: tuple = ()
    guidance: object = None
    controls: dict = field(default_factory=dict)
    prior: tuple = ()
    mentors: object = None
    _mentor_supervision: object = field(
        default=None, repr=False, compare=False)

    def __post_init__(self):
        capture = self.capture
        if (type(self.step) is not int or self.step < 1
                or type(self.seed) is not int or self.seed < 0
                or type(self.option_rows) is not tuple or not self.option_rows
                or not isinstance(self.controls, dict)
                or not callable(getattr(capture, "delivery", None))
                or any(not isinstance(getattr(capture, name, None), str)
                       or not getattr(capture, name)
                       for name in ("attempt_id", "proposal_id", "selected_option"))):
            _invalid("FACTORY_TRAINING_OBSERVATION_INVALID")


@dataclass(frozen=True)
class FactoryCandidateStep:
    """One non-published BAMF candidate step plus its C02/C08 evidence."""

    prepared: PreparedFactoryTrainingBatch
    resource_plan: object
    task_authority: object
    route_targets: tuple
    diagnostics: object
    transaction: object
    realized_cost: dict


@dataclass(frozen=True)
class FactoryCandidateDiagnostics:
    """Opt-in heavy B11/C08 execution evidence for operator diagnostics only."""

    gradient_execution: object
    schema_version: str = "bilqis.mlx.b11-factory-diagnostics/v1"

    def __post_init__(self):
        if (type(self.gradient_execution)
                not in (BamfGradientExecution, LogicalBatchGradientExecution)
                or self.schema_version != "bilqis.mlx.b11-factory-diagnostics/v1"):
            _invalid("FACTORY_CANDIDATE_DIAGNOSTICS_INVALID")


def _reporting_diagnostics(gradient, capture_diagnostics: bool):
    """Retain activation-heavy execution evidence only for explicit diagnostics."""
    if type(capture_diagnostics) is not bool:
        _invalid("FACTORY_CANDIDATE_DIAGNOSTICS_FLAG_INVALID")
    return (
        FactoryCandidateDiagnostics(gradient)
        if capture_diagnostics else None
    )


def _frame_stats(compiled_batch) -> FrameStats:
    row = compiled_batch.compiled.compiled.rows[0]
    compiled_batch.compiled.packed_frame_artifact_owner.require_row(row)
    closures = tuple(
        position for position in row.positions
        if position.kind is PositionKind.CLOSURE)
    frame_lengths = tuple(
        max(1, position.packed.sidecar.source_span.end
            - position.packed.sidecar.source_span.start)
        for position in closures)
    if not frame_lengths:
        frame_lengths = (1,) * len(row.positions)
    return FrameStats(
        compiled_positions=len(row.positions),
        frame_lengths=frame_lengths,
        constituent_expansions=sum(
            len(position.packed.sidecar.constituents) for position in closures),
        # Every visible neural position retains one summary per configured depth
        # group; C08 multiplies this position count by topology.depth_groups.
        depth_summaries=len(row.positions),
    )


def _resource_rows(prepared):
    return tuple(
        ResourceRow.from_training_row(
            training_row, _frame_stats(compiled),
            generation_binding=prepared.training_batch.generation_binding,
            delivered_content_sha256=prepared.training_batch.delivered_content_sha256,
        )
        for training_row, compiled in zip(
            prepared.training_batch.rows, prepared.compiled_rows))


def _resource_plan(prepared, parent, memory_budget):
    if memory_budget is None:
        memory_budget = MemoryBudget(
            bamf_parameter_census(parent.topology, parent.extents))
    elif not isinstance(memory_budget, MemoryBudget):
        _invalid("FACTORY_TRAINING_MEMORY_BUDGET_INVALID")
    rows = _resource_rows(prepared)
    # Choose the smallest supported cap that covers the full delivery so a
    # retry at the next smaller cap always reduces the actual group size.
    size_cap = next(
        (size for size in reversed(MICROBATCH_SIZES) if size >= len(rows)),
        MICROBATCH_SIZES[0],
    )
    return plan_microbatches(
        rows, parent.topology, memory_budget, max_microbatch_size=size_cap,
    ), memory_budget


def _stage_retained_motifs(run_dir, parent, cache, transaction, prepared,
                           resource_plan, memory_budget):
    spare = max(0, memory_budget.allocation_bytes - resource_plan.estimated_peak_bytes)
    budget = MotifBudget(
        64,
        page_growth_bytes=(MOTIF_PAGE_STATE_BYTES
                           if spare >= MOTIF_PAGE_STATE_BYTES else 0))
    bundle_root = Path(run_dir) / "bamf-bundles" / cache.accepted_manifest_sha256
    from bilqis_mlx.semantics.context_eligibility import ContextHold
    if len(prepared.motif_inputs) > 1:
        requests = tuple(
            SourceQualifiedMotifRequest(
                motif.source_adapter, motif.row, motif.atlas_selection,
                motif.source_root, motif.source_graph, motif.task, motif.frontier,
                motif.policy, motif.source_seed, motif.source_each,
                motif.source_profile_parameters, motif.course,
            )
            for motif in prepared.motif_inputs
        )
        result = seal_source_qualified_motif_batch_from_bundle(
            requests,
            retained_bundle_root=bundle_root,
            expected_manifest_sha256=cache.accepted_manifest_sha256,
            budget=budget,
        )
        if isinstance(result, ContextHold):
            _invalid("FACTORY_CANDIDATE_STEP_MOTIF_CONTEXT_HELD")
        continuation, _ = result
        if (continuation.approved.candidate.proposed.digest
                == parent.retained_state.allocations.digest):
            return transaction
        return stage_source_qualified_motif_allocation(
            Path(run_dir), transaction, continuation)
    motif = prepared.motif_inputs[0]
    result = seal_source_qualified_motifs_from_bundle(
        motif.source_adapter, motif.row, motif.atlas_selection,
        retained_bundle_root=bundle_root,
        expected_manifest_sha256=cache.accepted_manifest_sha256,
        source_root=motif.source_root, graph=motif.source_graph,
        task_scope=motif.task, source_frontier=motif.frontier,
        policy=motif.policy, source_seed=motif.source_seed,
        source_each=motif.source_each, budget=budget,
        source_profile_parameters=motif.source_profile_parameters,
        course=motif.course)
    if isinstance(result, ContextHold):
        _invalid("FACTORY_CANDIDATE_STEP_MOTIF_CONTEXT_HELD")
    continuation, _ = result
    if (continuation.approved.candidate.proposed.digest
            == parent.retained_state.allocations.digest):
        return transaction
    return stage_source_qualified_motif_allocation(
        Path(run_dir), transaction, continuation)
