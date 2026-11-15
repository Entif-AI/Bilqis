"""Row-scoped validation for B11 source-backed forward decoding."""
from __future__ import annotations

import mlx.core as mx

from bilqis_mlx.learning.atlas_readout import AnswerPlan

from .atlas_model_backend import Backend
from .atlas_model_contracts import (
    BamfCompiledBatch, BamfMicrobatchGradientExecution,
    _MICROBATCH_EXECUTION_ISSUER, _invalid,
)
from bilqis_mlx.runtime.model_topology_v2 import validate_bamf_parameters


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


def microbatch_trace_preflight(
    backend, params, batch, row_batches, answer_plans, targets, masks,
    generation, cache, rebind_execution, salience_supervision,
):
    """Capture model-derived row trajectories outside the autodiff tape."""
    from .atlas_model_forward import (
        _decode_bamf_producer_row, _finalize_source_hidden, _source_producer,
    )
    from .atlas_model_training import loss_bearing_bamf

    binding = rebind_execution(params)
    producer, accepted_cache, _ = _source_producer(
        params, batch, generation, cache, binding, trace=True)
    hidden = _finalize_source_hidden(
        producer, accepted_cache, batch, capture_derived_cache=False)
    if hidden.shape[0] != len(row_batches):
        _invalid("B11_MICROBATCH_HIDDEN_BATCH_MISMATCH")
    executions = []
    for index, (row_batch, plan, row_targets, mask) in enumerate(zip(
            row_batches, answer_plans, targets, masks)):
        output = _decode_bamf_producer_row(
            backend, params, row_batch, plan, producer, hidden, index,
            accepted_cache, binding, refinement_training=True,
            trace=False)
        executions.append(loss_bearing_bamf(
            output, row_targets, mask,
            salience_supervision=salience_supervision))
    return tuple(executions)


def finalize_microbatch_gradient(
    backend, batch, row_batches, preflight_executions,
    executions, mean_loss, gradients,
):
    """Verify replay parity and issue one post-autodiff microbatch result."""
    from bilqis_mlx.learning.atlas_readout.decoder.prediction import (
        attest_issued_output,
    )

    if (type(executions) is not tuple or len(executions) != len(row_batches)):
        _invalid("B11_MICROBATCH_EXECUTION_MISSING")
    if any(not attest_issued_output(execution.output) for execution in executions):
        _invalid("B11_MICROBATCH_OUTPUT_ATTESTATION_FAILED")
    if any(
            execution.output.committed != preflight.output.committed
            or execution.output.status is not preflight.output.status
            for execution, preflight in zip(executions, preflight_executions)):
        _invalid("B11_MICROBATCH_TRAJECTORY_DRIFT")
    preflight_mean = sum(
        (execution.loss.total for execution in preflight_executions),
        mx.array(0.0, dtype=mx.float32)) / len(preflight_executions)
    mx.eval(preflight_mean)
    if not bool(mx.allclose(mean_loss, preflight_mean, rtol=1e-5, atol=1e-6)):
        _invalid("B11_MICROBATCH_LOSS_DRIFT")
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


__all__ = (
    "finalize_microbatch_gradient",
    "microbatch_trace_preflight",
    "validate_decode_row_custody",
    "validate_decode_row_input",
    "validate_task_plan_custody",
)
