"""Bounded C05 multi-row B11 execution without changing per-case solver semantics."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Callable

from bilqis_mlx.learning.frame_embeddings import semantic_bank_views
from bilqis_mlx.learning.frame_encoder import CompiledEncoderInput
from bilqis_mlx.learning.source_atoms.backbone import (
    finalize_source_backbone_hidden,
    start_source_backbone_producer,
)
from bilqis_mlx.runtime.atlas_model_backend import model_backend
from bilqis_mlx.runtime.atlas_model_forward import _decode_bamf_producer_row
from bilqis_mlx.runtime.atlas_model_contracts import BamfCompiledBatch
from bilqis_mlx.runtime.factory_task_authority import FactoryTaskAuthority
from bilqis_mlx.runtime.model_topology_v2 import ModelTopologySpecV2
from bilqis_mlx.runtime.task_goal_readout import task_goal_route_decisions
from bilqis_mlx.semantics.frame_compiler import CompiledFrameRows
from bilqis_mlx.learning.atlas_readout import AnswerPlan, ModelOutput

from .capability_evaluation import _invalid


_LEGACY_BATCH_ROWS = 24
_LEGACY_POSITION_LIMIT = 96
_ACTIVATION_POSITION_BUDGET = _LEGACY_BATCH_ROWS * _LEGACY_POSITION_LIMIT
_ATTENTION_POSITION_BUDGET = _LEGACY_BATCH_ROWS * _LEGACY_POSITION_LIMIT ** 2


@dataclass(frozen=True)
class PreparedFactoryEvaluation:
    """One already validated C05 row, ready for scalar or shared B11 execution."""

    batch: BamfCompiledBatch
    plan: AnswerPlan
    authority: FactoryTaskAuthority

    def __post_init__(self):
        if (type(self.batch) is not BamfCompiledBatch
                or type(self.plan) is not AnswerPlan
                or type(self.authority) is not FactoryTaskAuthority
                or self.batch.task_authority != self.authority
                or self.plan.generation_binding != self.authority.generation_binding):
            _invalid("BAMF_C05_BATCH_PREPARATION_INVALID")
        self.batch.__post_init__()
        self.plan.__post_init__()
        self.authority.__post_init__()


def _positions(item: PreparedFactoryEvaluation) -> int:
    return len(item.batch.compiled.compiled.rows[0].positions)


def _capacity(items: tuple[PreparedFactoryEvaluation, ...]) -> int:
    if not items:
        return 1
    longest = max(_positions(item) for item in items)
    if longest < 1 or longest > _LEGACY_POSITION_LIMIT:
        return 1
    return max(1, min(
        len(items),
        _ACTIVATION_POSITION_BUDGET // longest,
        _ATTENTION_POSITION_BUDGET // (longest ** 2),
    ))


def _batchable(item: PreparedFactoryEvaluation) -> bool:
    return bool(task_goal_route_decisions(item.authority.goal)) and _positions(item) <= _LEGACY_POSITION_LIMIT


def _compatible(left: PreparedFactoryEvaluation, right: PreparedFactoryEvaluation) -> bool:
    a, b = left.batch, right.batch
    return (
        left.plan.generation_binding == right.plan.generation_binding
        and a.compiled.features == b.compiled.features
        and a.compiled.extents == b.compiled.extents
        and a.feature_schema == b.feature_schema
        and a.active_semantic_rows == b.active_semantic_rows
    )


def _combine(items: tuple[PreparedFactoryEvaluation, ...]) -> CompiledEncoderInput:
    batches = tuple(item.batch.compiled for item in items)
    rows = tuple(compiled.compiled.rows[0] for compiled in batches)
    width = max(len(row.positions) for row in rows)
    compiled_rows = CompiledFrameRows(
        rows,
        tuple(row.positions + (None,) * (width - len(row.positions)) for row in rows),
        tuple((True,) * len(row.positions) + (False,) * (width - len(row.positions))
              for row in rows),
    )
    first = batches[0]
    source_asts = tuple(compiled.source_asts[0] for compiled in batches)
    receipts = tuple(compiled.partial_forest_receipts[0] for compiled in batches)
    return CompiledEncoderInput(
        compiled_rows,
        tuple(compiled.compiler_configs[0] for compiled in batches),
        first.features,
        first.extents,
        source_asts=source_asts,
        partial_forest_receipts=receipts,
    )


def _execute_chunk(
    parameters,
    items: tuple[PreparedFactoryEvaluation, ...],
    on_launch: Callable[[int, int], None] | None,
) -> tuple[ModelOutput, ...]:
    if len(items) < 2 or any(not _batchable(item) for item in items):
        _invalid("BAMF_C05_BATCH_CHUNK_INVALID")
    if any(not _compatible(items[0], item) for item in items[1:]):
        _invalid("BAMF_C05_BATCH_CHUNK_INCOMPATIBLE")
    if _capacity(items) < len(items):
        _invalid("BAMF_C05_BATCH_CHUNK_OVER_BUDGET")

    combined = _combine(items)
    first = items[0].batch
    first.atlas_feature_artifact_owner.require(combined.features)
    banks = semantic_bank_views(
        parameters, combined.extents, combined.features.semantic_release,
        first.active_semantic_rows.active_indices)
    producer = start_source_backbone_producer(
        combined,
        parameters,
        tuple(item.batch.sources[0] for item in items),
        first.feature_schema,
        banks,
        first.atlas_feature_artifact_owner,
    )
    hidden = finalize_source_backbone_hidden(producer)
    backend = model_backend(ModelTopologySpecV2())
    if on_launch is not None:
        on_launch(len(items), max(_positions(item) for item in items))
    return tuple(
        _decode_bamf_producer_row(
            backend, parameters, item.batch, item.plan,
            producer, hidden, index)
        for index, item in enumerate(items)
    )


def batched_factory_outputs(
    parameters,
    prepared: tuple[PreparedFactoryEvaluation, ...],
    *,
    on_launch: Callable[[int, int], None] | None = None,
) -> tuple[ModelOutput | None, ...]:
    """Return issued outputs where sharing is lawful; None selects the scalar path."""
    if (not isinstance(prepared, tuple) or not prepared
            or any(type(item) is not PreparedFactoryEvaluation for item in prepared)
            or (on_launch is not None and not callable(on_launch))):
        _invalid("BAMF_C05_BATCH_INPUT_INVALID")
    outputs: list[ModelOutput | None] = [None] * len(prepared)
    cursor = 0
    while cursor < len(prepared):
        first = prepared[cursor]
        if not _batchable(first):
            cursor += 1
            continue
        chunk = [first]
        index = cursor + 1
        while index < len(prepared):
            candidate = prepared[index]
            proposed = tuple((*chunk, candidate))
            if (not _batchable(candidate)
                    or not _compatible(first, candidate)
                    or _capacity(proposed) < len(proposed)):
                break
            chunk.append(candidate)
            index += 1
        if len(chunk) > 1:
            issued = _execute_chunk(parameters, tuple(chunk), on_launch)
            outputs[cursor:cursor + len(chunk)] = issued
            cursor += len(chunk)
        else:
            cursor += 1
    return tuple(outputs)


__all__ = ("PreparedFactoryEvaluation", "batched_factory_outputs")
