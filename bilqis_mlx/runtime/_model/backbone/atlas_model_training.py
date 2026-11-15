"""Loss and gradient ownership layered on the exact live B11 forward."""
from __future__ import annotations

from dataclasses import replace

import mlx.core as mx

from bilqis_mlx.learning.atlas_readout import (
    AnswerPlan, DecisionKind, DecisionOutput, ExecutionMode, answer_loss,
)
from bilqis_mlx.semantics.frame_schema import ConceptRef
from bilqis_mlx.runtime.backbone_identity import (
    _execution_generation_autodiff_rebinder,
    issue_execution_generation_binding,
)
from bilqis_mlx.runtime.bamf_bundle.execution_cache import bind_execution_generation
from bilqis_mlx.runtime.model_topology_v2 import (
    ModelTopologySpecV2, validate_bamf_parameters,
)

from .atlas_model_backend import Backend, model_backend
from .atlas_model_contracts import (
    BamfCompiledBatch, BamfGradientExecution, BamfLossExecution,
    _FORWARD_ISSUANCE, _LOSS_EXECUTION_ISSUER, _invalid,
    _issue_loss_execution,
)
from .atlas_model_forward import _forward_bamf_impl


def _loss_participation(output, targets, mask, record):
    """Return exact semantic/role rows read by the supervised loss ancestry."""
    labelled = {target.decision_id for target in targets}
    specs = {item.decision_id: item for item in output.plan.decisions}
    supervised = {
        item.decision_id for item in output.decisions
        if mask.get(item.decision_id, False) and item.decision_id in labelled
    }
    relevant = set(supervised)
    pending = list(supervised)
    while pending:
        current = pending.pop()
        for parent in specs[current].depends_on:
            if parent not in relevant:
                relevant.add(parent)
                pending.append(parent)

    semantic = set()
    role_denominator = set()
    for item in output.decisions:
        if item.decision_id not in supervised:
            continue
        if item.kind is DecisionKind.VALUE and type(item.candidates[0]) is ConceptRef:
            semantic.update(
                divmod(value.abi_index, ModelTopologySpecV2.semantic_bank_rows)
                for value in item.candidates
            )
        elif item.kind is DecisionKind.ROLE:
            role_denominator.update(value.role_id for value in item.candidates)

    feedback = {
        divmod(item.value.abi_index, ModelTopologySpecV2.semantic_bank_rows)
        for item in output.committed
        if item.decision_id in relevant - supervised and type(item.value) is ConceptRef
    }
    roles = dict(record.role_map)
    role_reads = {
        ("role", roles[specs[key].role_id or "NONE"])
        for key in relevant
    }
    semantic_features = {("role", roles[role]) for role in role_denominator}
    return (
        tuple(sorted(feedback)),
        tuple(sorted(semantic)),
        tuple(sorted(semantic_features)),
        tuple(sorted(role_reads)),
    )


def loss_bearing_bamf(
    output,
    targets: tuple[DecisionOutput, ...],
    mask,
    *, salience_supervision=None,
) -> BamfLossExecution:
    """Bind a nonempty B10 supervised loss to the exact live B11 forward."""
    record = _FORWARD_ISSUANCE.require(output)
    if (
        type(targets) is not tuple
        or not targets
        or not isinstance(mask, dict)
        or not any(mask.values())
    ):
        _invalid("B11_LOSS_TARGET_REQUIRED")
    loss = answer_loss(output, targets, mask)
    heads, dependencies, artifact_nodes = (), (), ()
    if salience_supervision is not None:
        from .salience_training import SalienceSupervision
        from .salience_loss import salience_loss_components
        if type(salience_supervision) is not SalienceSupervision:
            _invalid("BAMF_SALIENCE_SUPERVISION_REQUIRED")
        primary = {DecisionKind.VALUE, DecisionKind.CONTROL,
                   DecisionKind.OPERATOR, DecisionKind.OPERAND}
        labelled = {target.decision_id for target in targets}
        if not any(item.kind in primary and item.decision_id in labelled
                   and mask.get(item.decision_id, False) for item in output.decisions):
            _invalid("BAMF_SALIENCE_PRIMARY_TARGET_REQUIRED")
        labels = salience_supervision.labels_for(record.compiled_batch)
        components = salience_loss_components(
            record.salience_parameters, record.salience_hidden, ModelTopologySpecV2(),
            record.compiled_batch.compiled.extents, labels)
        loss = replace(loss, total=loss.total + components.total,
                       impact=components.impact, exigency=components.exigency,
                       novelty=components.novelty)
        heads, dependencies = components.heads, salience_supervision.dependencies
        artifact_nodes = salience_supervision.artifact_nodes
    if not bool(mx.all(mx.isfinite(loss.total))):
        _invalid("B11_LOSS_NONFINITE")
    return _issue_loss_execution(
        output, loss, record, _loss_participation(output, targets, mask, record),
        salience_heads=heads, salience_dependencies=dependencies,
        salience_artifact_nodes=artifact_nodes)


def _gradient_execution_rebinder(params, cache, *, spec, extents, generation):
    binding = (
        issue_execution_generation_binding(
            params, spec=spec, extents=extents, expected_generation=generation)
        if cache is None else bind_execution_generation(
            cache, params, spec=spec, extents=extents)
    )
    if binding.generation_digest != generation:
        _invalid("B11_GRADIENT_GENERATION_BINDING_MISMATCH")
    return _execution_generation_autodiff_rebinder(
        binding, params, spec=spec, extents=extents)


def _bamf_value_and_grad_impl(
    backend: Backend,
    params,
    compiled_batch: BamfCompiledBatch,
    answer_plan: AnswerPlan,
    targets: tuple[DecisionOutput, ...],
    mask,
    cache=None,
    *, salience_supervision=None,
) -> BamfGradientExecution:
    """Run one exact forward/loss/gradient dispatch with one execution identity."""
    if salience_supervision is not None:
        from .salience_training import SalienceSupervision
        if type(salience_supervision) is not SalienceSupervision:
            _invalid("BAMF_SALIENCE_SUPERVISION_REQUIRED")
        salience_supervision.labels_for(compiled_batch)
    rebind_execution = _gradient_execution_rebinder(
        params, cache, spec=backend.topology, extents=compiled_batch.compiled.extents,
        generation=answer_plan.generation_binding)
    holder = {}

    def objective(current):
        execution_binding = rebind_execution(current)
        output = _forward_bamf_impl(
            backend,
            current,
            compiled_batch,
            answer_plan,
            ExecutionMode.INFERENCE,
            cache,
            refinement_training=True,
            execution_binding=execution_binding,
        )
        execution = loss_bearing_bamf(output, targets, mask,
                                      salience_supervision=salience_supervision)
        holder["execution"] = execution
        return execution.loss.total

    loss_total, gradients = mx.value_and_grad(objective)(params)
    mx.eval(loss_total, gradients)
    execution = holder.get("execution")
    if type(execution) is not BamfLossExecution:
        _invalid("B11_GRADIENT_EXECUTION_MISSING")
    validate_bamf_parameters(
        backend.topology, compiled_batch.compiled.extents, gradients)
    result = object.__new__(BamfGradientExecution)
    for name, value in (
        ("execution", execution),
        ("gradients", gradients),
        ("loss_total", loss_total),
        ("schema_version", "bilqis.mlx.b11-gradient-execution/v1"),
        ("_issuance", _LOSS_EXECUTION_ISSUER),
    ):
        object.__setattr__(result, name, value)
    result.__post_init__()
    return result


def bamf_value_and_grad(
    params,
    compiled_batch: BamfCompiledBatch,
    answer_plan: AnswerPlan,
    targets: tuple[DecisionOutput, ...],
    mask,
    cache=None,
    *, salience_supervision=None,
) -> BamfGradientExecution:
    """Public gradient entrypoint through the same backend as direct inference."""
    return model_backend(ModelTopologySpecV2()).value_and_grad(
        params, compiled_batch, answer_plan, targets, mask, cache,
        salience_supervision=salience_supervision)


__all__ = ("loss_bearing_bamf", "bamf_value_and_grad")
