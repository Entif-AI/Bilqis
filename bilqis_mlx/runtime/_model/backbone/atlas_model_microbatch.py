"""True MLX microbatch execution while preserving row-scoped B11 evidence."""
from __future__ import annotations

from dataclasses import dataclass, field
import time

import mlx.core as mx

from bilqis_mlx.learning.frame_encoder import CompiledEncoderInput
from bilqis_mlx.runtime.atlas_artifact_owner import AtlasFeatureArtifactOwner
from bilqis_mlx.semantics.frame_compiler import CompiledFrameRows

from .atlas_model_backend import Backend, model_backend
from .atlas_model_contracts import (
    BamfCompiledBatch, BamfMicrobatchGradientExecution,
    _invalid,
)
from .atlas_model_forward import (
    _decode_bamf_producer_row, _finalize_source_hidden, _source_producer,
)
from .atlas_model_forward_validation import (
    finalize_microbatch_gradient, microbatch_trace_from_hidden,
    microbatch_trace_from_route, microbatch_trace_preflight,
)
from .atlas_model_training import (
    _gradient_execution_rebinder, _require_finite_tensor_tree, loss_bearing_bamf,
)
from .microbatch.refinement_kernel import (
    batched_refine_hidden, prepare_refinement_selections,
)
from .microbatch.route_kernel import (
    prepare_route_microbatch_kernel, route_microbatch_compatible,
    route_microbatch_loss_and_trajectory,
)
from bilqis_mlx.runtime.autodiff_trace import defer_host_tensor_validation
from bilqis_mlx.runtime.model_topology_v2 import ModelTopologySpecV2
from bilqis_mlx.b11_observation import (
    attach_performance_observation, source_replay_observation,
)


_MIN_ROWS = 2
_ROUTE_CONTEXT_FIELDS = 3


@dataclass(frozen=True)
class _CompiledMicrobatch:
    compiled: CompiledEncoderInput
    sources: tuple
    feature_schema: object
    active_semantic_rows: object
    row_batches: tuple[BamfCompiledBatch, ...]
    atlas_feature_artifact_owner: AtlasFeatureArtifactOwner = field(
        init=False, compare=False)

    def __post_init__(self):
        if (type(self.compiled) is not CompiledEncoderInput
                or type(self.sources) is not tuple
                or len(self.sources) != len(self.compiled.compiled.rows)
                or type(self.row_batches) is not tuple
                or len(self.row_batches) != len(self.sources)
                or len(self.row_batches) < _MIN_ROWS
                or any(type(item) is not BamfCompiledBatch
                       for item in self.row_batches)):
            _invalid("B11_MICROBATCH_COMPILED_INPUT_INVALID")
        object.__setattr__(
            self, "atlas_feature_artifact_owner",
            AtlasFeatureArtifactOwner(self.compiled.features, self.feature_schema))


def _merge_compiled_rows(row_batches):
    rows = tuple(item.compiled.compiled.rows[0] for item in row_batches)
    width = max(len(row.positions) for row in rows)
    compiled_rows = CompiledFrameRows(
        rows,
        tuple(row.positions + (None,) * (width - len(row.positions))
              for row in rows),
        tuple((True,) * len(row.positions) + (False,) * (width - len(row.positions))
              for row in rows))
    first = row_batches[0].compiled
    source_asts = tuple(
        None if item.compiled.source_asts is None else item.compiled.source_asts[0]
        for item in row_batches)
    receipts = tuple(
        None if item.compiled.partial_forest_receipts is None
        else item.compiled.partial_forest_receipts[0]
        for item in row_batches)
    if not any(item is not None for item in source_asts):
        source_asts = receipts = None
    return CompiledEncoderInput(
        compiled_rows,
        tuple(item.compiled.compiler_configs[0] for item in row_batches),
        first.features, first.extents,
        source_asts=source_asts, partial_forest_receipts=receipts)


def microbatch_compatible(
        row_batches, answer_plans=None, targets=None, masks=None) -> bool:
    """Return whether rows can share one B11 source-backbone dispatch safely."""
    if (type(row_batches) is not tuple or len(row_batches) < _MIN_ROWS
            or any(type(item) is not BamfCompiledBatch for item in row_batches)):
        return False
    first = row_batches[0]
    for item in row_batches:
        item.__post_init__()
        row = item.compiled.compiled.rows[0]
        item.compiled.packed_frame_artifact_owner.require_row(row)
        item.atlas_feature_artifact_owner.require(item.compiled.features)
        if (item.compiled.features != first.compiled.features
                or item.compiled.extents != first.compiled.extents
                or item.feature_schema != first.feature_schema
                or item.active_semantic_rows != first.active_semantic_rows
                or item.sources[0].selection != first.sources[0].selection):
            return False
    source_authorities = tuple(
        item.source_execution_authority for item in row_batches)
    bound_source_authorities = tuple(
        authority is not None for authority in source_authorities)
    if any(bound_source_authorities):
        if not all(bound_source_authorities):
            return False
        first_owner = source_authorities[0].source_owner_contract
        if any(authority.source_owner_contract != first_owner
               for authority in source_authorities[1:]):
            return False
    if answer_plans is None and targets is None and masks is None:
        return True
    if answer_plans is None or targets is None or masks is None:
        return False
    if any(plan.snapshot != answer_plans[0].snapshot for plan in answer_plans):
        return False
    return route_microbatch_compatible(
        row_batches, answer_plans, targets, masks)


def _compiled_microbatch(row_batches):
    if not microbatch_compatible(row_batches):
        _invalid("B11_MICROBATCH_ROWS_INCOMPATIBLE")
    merged = _merge_compiled_rows(row_batches)
    first = row_batches[0]
    result = _CompiledMicrobatch(
        merged, tuple(item.sources[0] for item in row_batches),
        first.feature_schema, first.active_semantic_rows, row_batches)
    result.__post_init__()
    return result


def _microbatch_salience_labels(row_batches, salience_supervision):
    if salience_supervision is None:
        return ()
    from .salience_training import SalienceSupervision
    if type(salience_supervision) is not SalienceSupervision:
        _invalid("BAMF_SALIENCE_SUPERVISION_REQUIRED")
    return tuple(
        salience_supervision.labels_for(row_batch) for row_batch in row_batches)


def _gradient_path(
        backend, params, batch, row_batches, answer_plans, targets, masks,
        generation, cache, rebind_execution, salience_supervision, snapshot,
        salience_labels):
    route_vectorized = route_microbatch_compatible(
        row_batches, answer_plans, targets, masks)
    if not route_vectorized:
        from bilqis_mlx.runtime.b11_source_execution_authority import (
            b11_source_authority_launch_epoch,
        )
        with b11_source_authority_launch_epoch(row_batches):
            preflight = microbatch_trace_preflight(
                backend, params, batch, row_batches, answer_plans, targets, masks,
                generation, cache, rebind_execution, salience_supervision, snapshot)
        return False, preflight, None, None
    refinement = prepare_refinement_selections(
        row_batches, answer_plans, generation)
    kernel = prepare_route_microbatch_kernel(
        row_batches, answer_plans, targets, masks, None, salience_labels)
    return True, None, refinement, kernel


def _materialize_gradient(
        objective, params, route_vectorized, holder, backend, row_batches,
        answer_plans, targets, masks, salience_supervision, rebind_execution,
        refinement_selections):
    if not route_vectorized:
        mean_loss, gradients = mx.value_and_grad(objective)(params)
        mx.eval(mean_loss, gradients)
        return mean_loss, gradients, holder.get("executions"), None
    (mean_loss, route_hidden, route_trajectory, route_logits), gradients = mx.value_and_grad(
        objective)(params)
    mx.eval(mean_loss, gradients, route_hidden, route_trajectory, route_logits)
    route_context = holder.get("route_context")
    if (type(route_context) is not tuple
            or len(route_context) != _ROUTE_CONTEXT_FIELDS):
        _invalid("B11_MICROBATCH_EXECUTION_MISSING")
    producer, accepted_cache, _trace_binding = route_context
    execution_binding = rebind_execution(params)
    executions = microbatch_trace_from_route(
        backend, params, row_batches, answer_plans, targets, masks,
        producer, route_hidden, accepted_cache, execution_binding,
        salience_supervision, refinement_selections, route_trajectory, route_logits)
    return mean_loss, gradients, executions, route_trajectory


def _microbatch_objective(
        backend, batch, row_batches, answer_plans, targets, masks, cache,
        generation, snapshot, rebind_execution, route_vectorized,
        preflight_executions, refinement_selections, route_kernel,
        salience_supervision, holder):
    def objective(current):
        with defer_host_tensor_validation():
            execution_binding = rebind_execution(current)
            producer, accepted_cache, _capture_derived_cache = _source_producer(
                current, batch, generation, cache, execution_binding,
                trace=True, snapshot=snapshot)
            hidden = _finalize_source_hidden(
                producer, accepted_cache, batch, capture_derived_cache=False)
            if hidden.shape[0] != len(row_batches):
                _invalid("B11_MICROBATCH_HIDDEN_BATCH_MISMATCH")
            if not route_vectorized:
                executions = []
                total = mx.array(0.0, dtype=mx.float32)
                for index, (row_batch, plan, row_targets, mask) in enumerate(zip(
                        row_batches, answer_plans, targets, masks)):
                    output = _decode_bamf_producer_row(
                        backend, current, row_batch, plan, producer, hidden, index,
                        accepted_cache, execution_binding, refinement_training=True,
                        trace=True, replay_output=preflight_executions[index].output)
                    execution = loss_bearing_bamf(
                        output, row_targets, mask,
                        salience_supervision=salience_supervision,
                        validate_finite=False)
                    executions.append(execution)
                    total = total + execution.loss.total
                holder["executions"] = tuple(executions)
                return total / len(row_batches)
            holder["route_context"] = (producer, accepted_cache, execution_binding)
            salience_hidden = hidden
            refined = batched_refine_hidden(
                current, row_batches, producer, hidden, refinement_selections)
            mean_loss, trajectory, route_logits = route_microbatch_loss_and_trajectory(
                current, refined, route_kernel, salience_hidden=salience_hidden,
                return_logits=True)
            return mean_loss, hidden, trajectory, route_logits

    return objective


def _bamf_microbatch_value_and_grad_impl(
    backend: Backend,
    params,
    row_batches: tuple[BamfCompiledBatch, ...],
    answer_plans: tuple,
    targets: tuple,
    masks: tuple,
    cache=None,
    *, salience_supervision=None,
) -> BamfMicrobatchGradientExecution:
    """Run one differentiable source-backbone graph for one compatible C08 group."""
    if (type(answer_plans) is not tuple or type(targets) is not tuple
            or type(masks) is not tuple or len(row_batches) < _MIN_ROWS
            or not (len(row_batches) == len(answer_plans) == len(targets) == len(masks))):
        _invalid("B11_MICROBATCH_ARGUMENT_INVALID")
    batch = _compiled_microbatch(row_batches)
    backend.__post_init__()
    salience_labels = _microbatch_salience_labels(
        row_batches, salience_supervision)
    generation = answer_plans[0].generation_binding
    if any(plan.generation_binding != generation for plan in answer_plans):
        _invalid("B11_MICROBATCH_GENERATION_BINDING_MISMATCH")
    snapshot = answer_plans[0].snapshot
    if any(plan.snapshot != snapshot for plan in answer_plans):
        _invalid("B11_MICROBATCH_SEMANTIC_SNAPSHOT_MISMATCH")
    with source_replay_observation() as replay:
        preflight_started = time.perf_counter()
        _require_finite_tensor_tree(params, "B11_PARAMETER_NONFINITE")
        rebind_execution = _gradient_execution_rebinder(
            params, cache, spec=backend.topology, extents=batch.compiled.extents,
            generation=generation)
        route_vectorized, preflight_executions, refinement_selections, route_kernel = (
            _gradient_path(
                backend, params, batch, row_batches, answer_plans, targets, masks,
                generation, cache, rebind_execution, salience_supervision, snapshot,
                salience_labels))
        preflight_wall_seconds = time.perf_counter() - preflight_started
        holder = {}
        objective = _microbatch_objective(
            backend, batch, row_batches, answer_plans, targets, masks, cache,
            generation, snapshot, rebind_execution, route_vectorized,
            preflight_executions, refinement_selections, route_kernel,
            salience_supervision, holder)
        autodiff_started = time.perf_counter()
        from bilqis_mlx.runtime.b11_source_execution_authority import (
            b11_source_authority_launch_epoch,
        )
        with b11_source_authority_launch_epoch(row_batches):
            mean_loss, gradients, executions, route_trajectory = _materialize_gradient(
                objective, params, route_vectorized, holder, backend, row_batches,
                answer_plans, targets, masks, salience_supervision, rebind_execution,
                refinement_selections)
        autodiff_wall_seconds = time.perf_counter() - autodiff_started
    _require_finite_tensor_tree(gradients, "B11_GRADIENT_NONFINITE")
    result = finalize_microbatch_gradient(
        backend, batch, row_batches, preflight_executions,
        executions, mean_loss, gradients, answer_plans=answer_plans,
        route_trajectory=route_trajectory)
    attach_performance_observation(result, {
        "b11_preflight_wall_seconds": float(preflight_wall_seconds),
        "b11_autodiff_wall_seconds": float(autodiff_wall_seconds),
        "b11_provider_draw_count": replay["provider_draws"],
        "b11_atlas_reload_count": replay["atlas_reloads"],
    })
    return result


def bamf_microbatch_value_and_grad(
    params,
    row_batches: tuple[BamfCompiledBatch, ...],
    answer_plans: tuple,
    targets: tuple,
    masks: tuple,
    cache=None,
    *, salience_supervision=None,
) -> BamfMicrobatchGradientExecution:
    return model_backend(ModelTopologySpecV2()).microbatch_value_and_grad(
        params, row_batches, answer_plans, targets, masks, cache,
        salience_supervision=salience_supervision)


__all__ = ("bamf_microbatch_value_and_grad", "microbatch_compatible")
