"""Row-scoped validation for B11 source-backed forward decoding."""
from __future__ import annotations

import mlx.core as mx
import numpy as np

from bilqis_mlx.learning.atlas_readout import AnswerPlan

from .atlas_model_backend import Backend
from .atlas_model_contracts import (
    BamfCompiledBatch, BamfMicrobatchGradientExecution,
    _FORWARD_ISSUANCE, _MICROBATCH_EXECUTION_ISSUER, _invalid,
)
from bilqis_mlx.runtime.model_topology_v2 import validate_bamf_parameters


_ROUTE_TRAJECTORY_NDIM = 2


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
    generation, cache, rebind_execution, salience_supervision, snapshot,
):
    """Capture model-derived row trajectories outside the autodiff tape."""
    from .atlas_model_forward import (
        _decode_bamf_producer_row, _finalize_source_hidden, _source_producer,
    )
    from .atlas_model_training import loss_bearing_bamf

    binding = rebind_execution(params)
    producer, accepted_cache, _ = _source_producer(
        params, batch, generation, cache, binding, trace=True, snapshot=snapshot)
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


def microbatch_trace_from_hidden(
    backend, params, row_batches, answer_plans, targets, masks,
    producer, hidden, accepted_cache, execution_binding, salience_supervision,
):
    """Issue row evidence from one already-executed source backbone."""
    from .atlas_model_forward import _decode_bamf_producer_row
    from .atlas_model_training import loss_bearing_bamf

    if hidden.shape[0] != len(row_batches):
        _invalid("B11_MICROBATCH_HIDDEN_BATCH_MISMATCH")
    executions = []
    for index, (row_batch, plan, row_targets, mask) in enumerate(zip(
            row_batches, answer_plans, targets, masks)):
        output = _decode_bamf_producer_row(
            backend, params, row_batch, plan, producer, hidden, index,
            accepted_cache, execution_binding, refinement_training=True,
            trace=False)
        executions.append(loss_bearing_bamf(
            output, row_targets, mask,
            salience_supervision=salience_supervision))
    return tuple(executions)


def _route_output_from_materialized_logits(plan, row_index, trajectory_indices, route_logits):
    """Rebuild one route-only output from logits already computed by autodiff."""
    from bilqis_mlx.learning.atlas_readout.decisions import (
        DecodeStatus, DecisionOutput, commit_decisions, ready_decisions, start_decoding,
    )
    from bilqis_mlx.learning.atlas_readout.decoder.prediction import (
        DecisionLogits, ExecutionMode, ModelOutput, _issue_output,
    )

    ordered = tuple(
        {item.decision_id: item for item in plan.decisions}[key]
        for key in plan.execution_order)
    if (trajectory_indices.ndim != _ROUTE_TRAJECTORY_NDIM
            or trajectory_indices.shape[0] != len(route_logits)
            or trajectory_indices.shape[0] < len(ordered)
            or row_index >= trajectory_indices.shape[1]):
        _invalid("B11_MICROBATCH_ROUTE_EVIDENCE_MISSING")
    evidence = {}
    for step, decision in enumerate(ordered):
        selected = int(trajectory_indices[step, row_index])
        if not 0 <= selected < len(decision.legal_values):
            _invalid("B11_MICROBATCH_TRAJECTORY_DRIFT")
        logits = route_logits[step][row_index, :len(decision.legal_values)]
        evidence[decision.decision_id] = (
            DecisionLogits(
                decision.decision_id, decision.kind, decision.legal_values, logits),
            DecisionOutput(decision.decision_id, decision.legal_values[selected]),
        )

    state = start_decoding(plan)
    records = []
    while state.status is DecodeStatus.ACTIVE:
        ready = ready_decisions(state)
        if not ready or any(item.decision_id not in evidence for item in ready):
            _invalid("B11_MICROBATCH_TRAJECTORY_DRIFT")
        outputs = tuple(evidence[item.decision_id][1] for item in ready)
        records.extend(evidence[item.decision_id][0] for item in ready)
        state = commit_decisions(state, outputs)
    if state.status is not DecodeStatus.COMPLETE:
        _invalid("B11_MICROBATCH_TRAJECTORY_DRIFT")
    return _issue_output(ModelOutput(
        plan, tuple(records), state.committed, state.status,
        ExecutionMode.INFERENCE, None, False),
        fingerprint=False, freeze_meaning=False)


def _refinement_participation(selection):
    if selection is None or not selection[1]:
        return (), False
    request, choices = selection
    roles = request.requested_roles
    if len(roles) > 1:
        _invalid("B11_REFINEMENT_MULTI_ROLE_UNRESOLVED")
    return ((roles[0] if roles else "NONE",),
            any(choice.passes > 0 for choice in choices))


def microbatch_trace_from_route(
    backend, params, row_batches, answer_plans, targets, masks, producer, hidden,
    accepted_cache, execution_binding, salience_supervision, refinement_selections,
    trajectory, route_logits,
):
    """Issue row evidence from the exact materialized vector route execution."""
    from dataclasses import replace
    from bilqis_mlx.runtime.autodiff_trace import defer_host_tensor_validation
    from bilqis_mlx.runtime.backbone_identity import require_execution_generation_binding
    from .atlas_model_participation import _forward_participation
    from .atlas_model_training import loss_bearing_bamf

    if (hidden.shape[0] != len(row_batches)
            or len(refinement_selections) != len(row_batches)):
        _invalid("B11_MICROBATCH_HIDDEN_BATCH_MISMATCH")
    generation = require_execution_generation_binding(
        execution_binding, params, spec=backend.topology,
        extents=row_batches[0].compiled.extents).generation_digest
    validate_bamf_parameters(
        backend.topology, row_batches[0].compiled.extents, params)
    if not trajectory:
        _invalid("B11_MICROBATCH_ROUTE_EVIDENCE_MISSING")
    trajectory_indices = np.asarray(mx.stack(trajectory), dtype=np.int64)
    executions = []
    for index, (row_batch, plan, row_targets, mask, refinement) in enumerate(zip(
            row_batches, answer_plans, targets, masks, refinement_selections)):
        validate_decode_row_input(backend, row_batch, plan, hidden, index)
        validate_decode_row_custody(row_batch, plan, producer, index, generation)
        validate_task_plan_custody(row_batch, plan)
        if (row_batch.training_authority is not None
                and row_batch.training_authority.generation_binding != generation):
            _invalid("B11_TRAINING_AUTHORITY_GENERATION_MISMATCH")
        with defer_host_tensor_validation():
            output = _route_output_from_materialized_logits(
                plan, index, trajectory_indices, route_logits)
            roles, refined = _refinement_participation(refinement)
            row = row_batch.compiled.compiled.rows[0]
            record = replace(
                _forward_participation(
                    params, row_batch, plan, output, producer, accepted_cache,
                    roles, refined, producer_row_index=index),
                salience_hidden=hidden[index, len(row.positions) - 1],
                salience_parameters=params, compiled_batch=row_batch)
            _FORWARD_ISSUANCE.issue(output, record)
            executions.append(loss_bearing_bamf(
                output, row_targets, mask, salience_supervision=salience_supervision,
                validate_finite=False))
    return tuple(executions)


def _validate_route_trajectory(answer_plans, executions, trajectory):
    if (type(answer_plans) is not tuple or type(executions) is not tuple
            or type(trajectory) is not tuple
            or len(answer_plans) != len(executions)):
        _invalid("B11_MICROBATCH_TRAJECTORY_DRIFT")
    ordered = tuple(
        tuple({item.decision_id: item for item in plan.decisions}[key]
              for key in plan.execution_order)
        for plan in answer_plans)
    if len(trajectory) != max(len(items) for items in ordered):
        _invalid("B11_MICROBATCH_TRAJECTORY_DRIFT")
    committed = tuple(
        {item.decision_id: item.value for item in execution.output.committed}
        for execution in executions)
    for index, observed in enumerate(trajectory):
        expected = []
        for items, values in zip(ordered, committed):
            if index >= len(items):
                expected.append(0)
                continue
            decision = items[index]
            if decision.decision_id not in values:
                _invalid("B11_MICROBATCH_TRAJECTORY_DRIFT")
            value = values[decision.decision_id]
            try:
                expected.append(decision.legal_values.index(value))
            except ValueError:
                _invalid("B11_MICROBATCH_TRAJECTORY_DRIFT")
        expected_array = mx.array(tuple(expected), dtype=observed.dtype)
        if not bool(mx.all(observed == expected_array)):
            _invalid("B11_MICROBATCH_TRAJECTORY_DRIFT")


def finalize_microbatch_gradient(
    backend, batch, row_batches, preflight_executions,
    executions, mean_loss, gradients, *, answer_plans=None, route_trajectory=None,
):
    """Verify row evidence, numerical parity and issue one microbatch result."""
    from bilqis_mlx.learning.atlas_readout.decoder.prediction import (
        attest_issued_outputs,
    )

    if preflight_executions is None:
        if (type(executions) is not tuple or len(executions) != len(row_batches)
                or route_trajectory is None):
            _invalid("B11_MICROBATCH_EXECUTION_MISSING")
        _validate_route_trajectory(answer_plans, executions, route_trajectory)
        reference_executions = executions
    else:
        reused_preflight_evidence = executions is None
        if reused_preflight_evidence:
            executions = preflight_executions
        elif type(executions) is not tuple or len(executions) != len(row_batches):
            _invalid("B11_MICROBATCH_EXECUTION_MISSING")
        if not reused_preflight_evidence and any(
                execution.output.committed != preflight.output.committed
                or execution.output.status is not preflight.output.status
                for execution, preflight in zip(executions, preflight_executions)):
            _invalid("B11_MICROBATCH_TRAJECTORY_DRIFT")
        reference_executions = preflight_executions
    if type(executions) is not tuple or len(executions) != len(row_batches):
        _invalid("B11_MICROBATCH_EXECUTION_MISSING")
    if not attest_issued_outputs(tuple(execution.output for execution in executions)):
        _invalid("B11_MICROBATCH_OUTPUT_ATTESTATION_FAILED")
    reference_mean = sum(
        (execution.loss.total for execution in reference_executions),
        mx.array(0.0, dtype=mx.float32)) / len(reference_executions)
    if not bool(mx.allclose(mean_loss, reference_mean, rtol=1e-5, atol=1e-6)):
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
    "microbatch_trace_from_hidden",
    "microbatch_trace_from_route",
    "microbatch_trace_preflight",
    "validate_decode_row_custody",
    "validate_decode_row_input",
    "validate_task_plan_custody",
)
