"""Loss and gradient ownership layered on the exact live B11 forward."""
from __future__ import annotations

from dataclasses import replace
import time

import mlx.core as mx

from bilqis_mlx.learning.atlas_readout import (
    AnswerPlan, DecisionKind, DecisionOutput, ExecutionMode, answer_loss,
)
from bilqis_mlx.learning.atlas_readout.decoder.prediction import attest_issued_output
from bilqis_mlx.semantics.frame_schema import ConceptRef
from bilqis_mlx.runtime.backbone_identity import (
    _execution_generation_autodiff_rebinder,
    issue_execution_generation_binding,
)
from bilqis_mlx.runtime.bamf_bundle.execution_cache import bind_execution_generation
from bilqis_mlx.runtime.model_topology_v2 import (
    ModelTopologySpecV2, validate_bamf_parameters,
)
from bilqis_mlx.runtime.atlas_refinement import masked_routing_loss

from .atlas_model_backend import Backend, model_backend
from bilqis_mlx.runtime.training_objective import REFINEMENT_ROUTING_WEIGHT
from .atlas_model_contracts import (
    BamfCompiledBatch, BamfGradientExecution, BamfLossExecution,
    _FORWARD_ISSUANCE, _LOSS_EXECUTION_ISSUER, _invalid,
    _issue_loss_execution,
)
from .atlas_model_forward import _forward_bamf_impl
from bilqis_mlx.runtime.autodiff_trace import defer_host_tensor_validation
from bilqis_mlx.b11_observation import (
    attach_performance_observation, source_replay_observation,
)


def _require_finite_tensor_tree(values, code):
    """Attest a flat BAMF tensor tree at an explicit host boundary.

    Per-module guards stay off the differentiated tape.  One aggregated
    scalar witness here preserves fail-closed finite-value semantics without
    hundreds of Python-visible device synchronizations inside ``value_and_grad``.
    """
    checks = tuple(mx.all(mx.isfinite(value)) for value in values.values())
    if not checks:
        _invalid(code)
    finite = mx.all(mx.stack(checks))
    mx.eval(finite)
    if not bool(finite):
        _invalid(code)


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
    *, salience_supervision=None, source_loss_multiplier: float = 1.0,
    validate_finite=True,
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
    labelled = {target.decision_id for target in targets}
    required = {decision_id for decision_id, enabled in mask.items()
                if enabled and decision_id in labelled}
    executed = {item.decision_id for item in output.decisions}
    if not required or not required.issubset(executed):
        _invalid("B11_LOSS_TARGET_NOT_EXECUTED")
    from bilqis_mlx.learning._championship.champion_confidence import MAX_INFLUENCE
    if (type(source_loss_multiplier) not in (int, float)
            or not 1.0 <= float(source_loss_multiplier) <= 1.0 + MAX_INFLUENCE):
        _invalid("BAMF_MENTOR_SOURCE_LOSS_MULTIPLIER_INVALID")
    loss = answer_loss(output, targets, mask)
    heads, dependencies, artifact_nodes = (), (), ()
    if salience_supervision is not None:
        from .salience_training import PortableSalienceSupervision, SalienceSupervision
        from .salience_loss import salience_loss_components
        if type(salience_supervision) not in (
                SalienceSupervision, PortableSalienceSupervision):
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
    route_supervision = record.refinement_route_supervision
    if route_supervision:
        routing = mx.mean(mx.stack(tuple(
            masked_routing_loss(logits, label)
            for logits, label in route_supervision))) * REFINEMENT_ROUTING_WEIGHT
        loss = replace(loss, total=loss.total + routing, routing=routing)
    if float(source_loss_multiplier) != 1.0:
        loss = replace(loss, total=loss.total * float(source_loss_multiplier))
    if validate_finite and not bool(mx.all(mx.isfinite(loss.total))):
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


def _gradient_preflight(
        backend, params, compiled_batch, answer_plan, targets, mask, cache,
        salience_supervision, source_loss_multiplier):
    started = time.perf_counter()
    _require_finite_tensor_tree(params, "B11_PARAMETER_NONFINITE")
    rebind_execution = _gradient_execution_rebinder(
        params, cache, spec=backend.topology, extents=compiled_batch.compiled.extents,
        generation=answer_plan.generation_binding)
    preflight_binding = rebind_execution(params)
    from bilqis_mlx.runtime.b11_source_execution_authority import (
        b11_source_authority_launch_epoch,
    )
    with b11_source_authority_launch_epoch((compiled_batch,)):
        preflight_output = _forward_bamf_impl(
            backend, params, compiled_batch, answer_plan, ExecutionMode.INFERENCE, cache,
            refinement_training=True, execution_binding=preflight_binding,
            decoder_trace=False)
    preflight_execution = loss_bearing_bamf(
        preflight_output, targets, mask, salience_supervision=salience_supervision,
        source_loss_multiplier=source_loss_multiplier)
    return (
        rebind_execution, preflight_output, preflight_execution,
        time.perf_counter() - started,
    )


def _finalize_gradient_execution(
        backend, compiled_batch, execution, preflight_output, preflight_execution,
        loss_total, gradients, observation):
    _require_finite_tensor_tree(gradients, "B11_GRADIENT_NONFINITE")
    if type(execution) is not BamfLossExecution:
        _invalid("B11_GRADIENT_EXECUTION_MISSING")
    if not attest_issued_output(execution.output):
        _invalid("B11_TRAINING_OUTPUT_ATTESTATION_FAILED")
    if (execution.output.committed != preflight_output.committed
            or execution.output.status is not preflight_output.status):
        _invalid("B11_TRAINING_TRAJECTORY_DRIFT")
    if not bool(mx.allclose(
            execution.loss.total, preflight_execution.loss.total,
            rtol=1e-5, atol=1e-6)):
        _invalid("B11_TRAINING_LOSS_DRIFT")
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
    attach_performance_observation(result, observation)
    result.__post_init__()
    return result


def _bamf_value_and_grad_impl(
    backend: Backend,
    params,
    compiled_batch: BamfCompiledBatch,
    answer_plan: AnswerPlan,
    targets: tuple[DecisionOutput, ...],
    mask,
    cache=None,
    *, salience_supervision=None, source_loss_multiplier: float = 1.0,
) -> BamfGradientExecution:
    """Run one exact forward/loss/gradient dispatch with one execution identity."""
    if salience_supervision is not None:
        from .salience_training import PortableSalienceSupervision, SalienceSupervision
        if type(salience_supervision) not in (
                SalienceSupervision, PortableSalienceSupervision):
            _invalid("BAMF_SALIENCE_SUPERVISION_REQUIRED")
        salience_supervision.labels_for(compiled_batch)
    with source_replay_observation() as replay:
        (
            rebind_execution, preflight_output, preflight_execution,
            preflight_wall_seconds,
        ) = _gradient_preflight(
            backend, params, compiled_batch, answer_plan, targets, mask, cache,
            salience_supervision, source_loss_multiplier)
        holder = {}

        def objective(current):
            with defer_host_tensor_validation():
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
                    replay_output=preflight_output,
                )
                execution = loss_bearing_bamf(
                    output, targets, mask,
                    salience_supervision=salience_supervision,
                    source_loss_multiplier=source_loss_multiplier,
                    validate_finite=False)
                holder["execution"] = execution
                return execution.loss.total

        from bilqis_mlx.runtime.b11_source_execution_authority import (
            b11_source_authority_launch_epoch,
        )
        autodiff_started = time.perf_counter()
        with b11_source_authority_launch_epoch((compiled_batch,)):
            loss_total, gradients = mx.value_and_grad(objective)(params)
        mx.eval(loss_total, gradients)
        autodiff_wall_seconds = time.perf_counter() - autodiff_started
    return _finalize_gradient_execution(
        backend, compiled_batch, holder.get("execution"), preflight_output,
        preflight_execution, loss_total, gradients, {
        "b11_preflight_wall_seconds": float(preflight_wall_seconds),
        "b11_autodiff_wall_seconds": float(autodiff_wall_seconds),
        "b11_provider_draw_count": replay["provider_draws"],
        "b11_atlas_reload_count": replay["atlas_reloads"],
    })


def bamf_value_and_grad(
    params,
    compiled_batch: BamfCompiledBatch,
    answer_plan: AnswerPlan,
    targets: tuple[DecisionOutput, ...],
    mask,
    cache=None,
    *, salience_supervision=None, source_loss_multiplier: float = 1.0,
) -> BamfGradientExecution:
    """Public gradient entrypoint through the same backend as direct inference."""
    return model_backend(ModelTopologySpecV2()).value_and_grad(
        params, compiled_batch, answer_plan, targets, mask, cache,
        salience_supervision=salience_supervision,
        source_loss_multiplier=source_loss_multiplier)


__all__ = ("loss_bearing_bamf", "bamf_value_and_grad")
