"""Row-scoped validation for B11 source-backed forward decoding."""
from __future__ import annotations

import mlx.core as mx

from bilqis_mlx.learning.atlas_readout import AnswerPlan

from .atlas_model_backend import Backend
from .atlas_model_contracts import BamfCompiledBatch, _invalid


_FORWARD_HIDDEN_RANK = 3


def validate_decode_row_input(
    backend: Backend,
    compiled_batch: BamfCompiledBatch,
    answer_plan: AnswerPlan,
    final_hidden,
    row_index: int,
) -> None:
    if (
        type(compiled_batch) is not BamfCompiledBatch
        or type(answer_plan) is not AnswerPlan
        or type(backend) is not Backend
        or type(row_index) is not int
        or row_index < 0
        or not isinstance(final_hidden, mx.array)
        or final_hidden.ndim != _FORWARD_HIDDEN_RANK
        or row_index >= final_hidden.shape[0]
    ):
        _invalid("B11_FORWARD_ROW_INPUT_INVALID")
    compiled_batch.__post_init__()
    answer_plan.__post_init__()
    backend.__post_init__()


def validate_decode_row_custody(
    compiled_batch: BamfCompiledBatch,
    answer_plan: AnswerPlan,
    producer,
    row_index: int,
    generation: str,
) -> None:
    extents = compiled_batch.compiled.extents
    if (
        answer_plan.generation_binding != generation
        or getattr(producer, "_generation", None) != generation
        or getattr(producer, "_compiled", None) is None
        or producer._compiled.features != compiled_batch.compiled.features
        or producer._compiled.extents != extents
        or row_index >= len(producer._compiled.compiled.rows)
        or producer._compiled.compiled.rows[row_index]
        != compiled_batch.compiled.compiled.rows[0]
        or getattr(producer, "_sources", None) is None
        or row_index >= len(producer._sources)
        or producer._sources[row_index] != compiled_batch.sources[0]
        or getattr(producer, "_feature_schema", None) != compiled_batch.feature_schema
        or producer._compiled.compiler_configs[row_index]
        != compiled_batch.compiled.compiler_configs[0]
        or producer._compiled._projections[row_index]
        != compiled_batch.compiled._projections[0]
    ):
        _invalid("B11_FORWARD_ROW_CUSTODY_MISMATCH")


def validate_task_plan_custody(
    compiled_batch: BamfCompiledBatch,
    answer_plan: AnswerPlan,
) -> None:
    authority = compiled_batch.task_authority
    if authority is None:
        return
    from bilqis_mlx.runtime.refinement_request import refinement_request_disposition
    from bilqis_mlx.runtime.task_goal_readout import task_goal_route_decisions

    authority.__post_init__()
    route = task_goal_route_decisions(authority.goal)
    expected_refinement = refinement_request_disposition(authority.goal)
    if (answer_plan.refinement_request != expected_refinement
            or (answer_plan.route_only and answer_plan.decisions != route)
            or (not answer_plan.route_only
                and answer_plan.decisions[:len(route)] != route)):
        _invalid("B11_FORWARD_TASK_PLAN_CUSTODY_MISMATCH")


__all__ = (
    "validate_decode_row_custody",
    "validate_decode_row_input",
    "validate_task_plan_custody",
)
