"""True MLX microbatch execution while preserving row-scoped B11 evidence."""
from __future__ import annotations

from dataclasses import dataclass, field

import mlx.core as mx

from bilqis_mlx.learning.frame_encoder import CompiledEncoderInput
from bilqis_mlx.runtime.atlas_artifact_owner import AtlasFeatureArtifactOwner
from bilqis_mlx.semantics.frame_compiler import CompiledFrameRows

from .atlas_model_backend import Backend, model_backend
from .atlas_model_contracts import (
    BamfCompiledBatch, BamfMicrobatchGradientExecution,
    _MICROBATCH_EXECUTION_ISSUER, _invalid,
)
from .atlas_model_forward import (
    _decode_bamf_producer_row, _finalize_source_hidden, _source_producer,
)
from .atlas_model_training import loss_bearing_bamf
from bilqis_mlx.runtime.backbone_identity import issue_execution_generation_binding
from bilqis_mlx.runtime.bamf_bundle.execution_cache import bind_execution_generation
from bilqis_mlx.runtime.model_topology_v2 import (
    ModelTopologySpecV2, validate_bamf_parameters,
)


_MIN_ROWS = 2


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


def microbatch_compatible(row_batches) -> bool:
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
    return True


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
    if salience_supervision is not None:
        from .salience_training import SalienceSupervision
        if type(salience_supervision) is not SalienceSupervision:
            _invalid("BAMF_SALIENCE_SUPERVISION_REQUIRED")
        for row_batch in row_batches:
            salience_supervision.labels_for(row_batch)
    generation = answer_plans[0].generation_binding
    if any(plan.generation_binding != generation for plan in answer_plans):
        _invalid("B11_MICROBATCH_GENERATION_BINDING_MISMATCH")
    holder = {}

    def objective(current):
        execution_binding = (
            issue_execution_generation_binding(
                current, spec=backend.topology, extents=batch.compiled.extents,
                expected_generation=generation)
            if cache is None else bind_execution_generation(
                cache, current, spec=backend.topology, extents=batch.compiled.extents)
        )
        producer, accepted_cache, _capture_derived_cache = _source_producer(
            current, batch, generation, cache, execution_binding)
        hidden = _finalize_source_hidden(
            producer, accepted_cache, batch, capture_derived_cache=False)
        if hidden.shape[0] != len(row_batches):
            _invalid("B11_MICROBATCH_HIDDEN_BATCH_MISMATCH")
        executions = []
        total = mx.array(0.0, dtype=mx.float32)
        for index, (row_batch, plan, row_targets, mask) in enumerate(zip(
                row_batches, answer_plans, targets, masks)):
            output = _decode_bamf_producer_row(
                backend, current, row_batch, plan, producer, hidden, index,
                accepted_cache, execution_binding, refinement_training=True)
            execution = loss_bearing_bamf(
                output, row_targets, mask,
                salience_supervision=salience_supervision)
            executions.append(execution)
            total = total + execution.loss.total
        holder["executions"] = tuple(executions)
        return total / len(row_batches)

    mean_loss, gradients = mx.value_and_grad(objective)(params)
    mx.eval(mean_loss, gradients)
    executions = holder.get("executions")
    if (type(executions) is not tuple or len(executions) != len(row_batches)):
        _invalid("B11_MICROBATCH_EXECUTION_MISSING")
    validate_bamf_parameters(
        backend.topology, batch.compiled.extents, gradients)
    result = object.__new__(BamfMicrobatchGradientExecution)
    for name, value in (
        ("executions", executions), ("gradients", gradients),
        ("mean_loss", mean_loss),
        ("schema_version", "bilqis.mlx.b11-microbatch-gradient-execution/v1"),
        ("_issuance", _MICROBATCH_EXECUTION_ISSUER),
    ):
        object.__setattr__(result, name, value)
    result.__post_init__()
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
