"""Batched numerical B10 route replay and loss for compatible C08 rows."""
from __future__ import annotations

from dataclasses import dataclass
from types import SimpleNamespace

import mlx.core as mx

from bilqis_mlx.learning.atlas_readout import DecisionKind
from bilqis_mlx.learning.atlas_readout.causal_training import encode_feedback_value
from bilqis_mlx.learning.atlas_readout.decoder.feedback import (
    occurrence_vector, role_id_vector,
)
from bilqis_mlx.learning.atlas_salience import project_salience_heads
from bilqis_mlx.runtime.model_topology_v2 import ModelTopologySpecV2

from ..atlas_model_contracts import _invalid


_INNER = 192
_WIDTH = ModelTopologySpecV2.width
_SALIENCE_HEADS = ("impact", "exigency", "novelty")


@dataclass(frozen=True)
class RouteMicrobatchKernel:
    lengths: mx.array
    operator_masks: tuple[mx.array, ...]
    operand_masks: tuple[mx.array, ...]
    occurrences: tuple[mx.array, ...]
    feedback: tuple[mx.array, ...]
    candidate_vectors: tuple[mx.array, ...]
    candidate_masks: tuple[mx.array, ...]
    target_indices: tuple[mx.array, ...]
    operator_counts: mx.array
    operand_counts: mx.array
    salience_targets: tuple[tuple[mx.array, mx.array], ...]
    has_salience: bool
    features: object
    extents: object


def _ordered(plan):
    lookup = {item.decision_id: item for item in plan.decisions}
    return tuple(lookup[key] for key in plan.execution_order)


def route_microbatch_compatible(row_batches, answer_plans, targets, masks) -> bool:
    """Require one static route geometry before entering the vector kernel."""
    count = len(row_batches)
    if not (count > 1 and len(answer_plans) == len(targets) == len(masks) == count):
        return False
    if any(
            not hasattr(plan, "route_only")
            or not hasattr(plan, "decisions")
            or not hasattr(plan, "execution_order")
            for plan in answer_plans):
        return False
    ordered = tuple(_ordered(plan) for plan in answer_plans)
    if not ordered or any(not plan.route_only or not items
                          for plan, items in zip(answer_plans, ordered)):
        return False
    for items, row_targets, row_mask in zip(ordered, targets, masks):
        if (not isinstance(row_mask, dict)
                or any(item.kind not in (DecisionKind.OPERATOR, DecisionKind.OPERAND)
                       for item in items)
                or any(type(value) is not str for item in items
                       for value in item.legal_values)):
            return False
        target_map = {item.decision_id: item.value for item in row_targets}
        if (set(target_map) != {item.decision_id for item in items}
                or any(not row_mask.get(item.decision_id, False) for item in items)
                or any(type(target_map[item.decision_id]) is not str
                       or target_map[item.decision_id] not in item.legal_values
                       for item in items)):
            return False
    return True


def _padded_candidates(items):
    vectors = tuple(
        mx.zeros((1, _WIDTH), dtype=mx.float32) if item is None else
        mx.stack(tuple(encode_feedback_value(value) for value in item.legal_values))
        for item in items)
    width = max(value.shape[0] for value in vectors)
    padded = tuple(
        value if value.shape[0] == width else
        mx.pad(value, ((0, width - value.shape[0]), (0, 0)))
        for value in vectors)
    mask = mx.array(tuple(
        (True,) * value.shape[0] + (False,) * (width - value.shape[0])
        for value in vectors), dtype=mx.bool_)
    return mx.stack(padded), mask


def _feedback_vector(decision, committed):
    if decision is None:
        return mx.zeros((_WIDTH,), dtype=mx.float32)
    values = tuple(committed[key] for key in decision.depends_on)
    if any(type(value) is not str for value in values):
        _invalid("B11_MICROBATCH_ROUTE_FEEDBACK_UNSUPPORTED")
    if not values:
        return mx.zeros((_WIDTH,), dtype=mx.float32)
    return mx.mean(mx.stack(tuple(encode_feedback_value(value) for value in values)), axis=0)


def prepare_route_microbatch_kernel(
        row_batches, answer_plans, targets, masks, preflight_executions,
        salience_labels=()):
    """Freeze route metadata into tensors; no model parameter is captured here."""
    if not route_microbatch_compatible(row_batches, answer_plans, targets, masks):
        _invalid("B11_MICROBATCH_ROUTE_KERNEL_INCOMPATIBLE")
    if len(preflight_executions) != len(row_batches):
        _invalid("B11_MICROBATCH_ROUTE_PREFLIGHT_REQUIRED")
    ordered = tuple(_ordered(plan) for plan in answer_plans)
    target_maps = tuple(
        {item.decision_id: item.value for item in row_targets}
        for row_targets in targets)
    committed = tuple(
        {item.decision_id: item.value for item in execution.output.committed}
        for execution in preflight_executions)
    steps = max(len(items) for items in ordered)
    operator_masks, operand_masks = [], []
    occurrences, feedback, candidates, candidate_masks, target_indices = [], [], [], [], []
    for index in range(steps):
        decisions = tuple(
            items[index] if index < len(items) else None for items in ordered)
        operator_masks.append(mx.array(tuple(
            item is not None and item.kind is DecisionKind.OPERATOR
            for item in decisions), dtype=mx.bool_))
        operand_masks.append(mx.array(tuple(
            item is not None and item.kind is DecisionKind.OPERAND
            for item in decisions), dtype=mx.bool_))
        occurrences.append(mx.stack(tuple(
            (mx.zeros((_WIDTH,), dtype=mx.float32) if item is None
             else occurrence_vector(item.occurrence)) for item in decisions)))
        feedback.append(mx.stack(tuple(
            _feedback_vector(item, values)
            for item, values in zip(decisions, committed))))
        vectors, candidate_mask = _padded_candidates(decisions)
        candidates.append(vectors)
        candidate_masks.append(candidate_mask)
        target_indices.append(mx.array(tuple(
            0 if item is None else item.legal_values.index(target_map[item.decision_id])
            for item, target_map in zip(decisions, target_maps)), dtype=mx.int32))
    labels = salience_labels or tuple({} for _ in row_batches)
    if len(labels) != len(row_batches):
        _invalid("B11_MICROBATCH_SALIENCE_LABEL_COUNT_MISMATCH")
    salience_targets = []
    has_salience = any(labels)
    for name in _SALIENCE_HEADS:
        active = tuple(name in row for row in labels)
        values = tuple(row.get(name, 0) for row in labels)
        salience_targets.append((
            mx.array(values, dtype=mx.int32), mx.array(active, dtype=mx.bool_)))
    return RouteMicrobatchKernel(
        mx.array(tuple(len(item.compiled.compiled.rows[0].positions)
                       for item in row_batches), dtype=mx.int32),
        tuple(operator_masks), tuple(operand_masks), tuple(occurrences),
        tuple(feedback), tuple(candidates),
        tuple(candidate_masks), tuple(target_indices),
        mx.array(tuple(sum(item.kind is DecisionKind.OPERATOR for item in items)
                       for items in ordered), dtype=mx.int32),
        mx.array(tuple(sum(item.kind is DecisionKind.OPERAND for item in items)
                       for items in ordered), dtype=mx.int32),
        tuple(salience_targets), has_salience, row_batches[0].compiled.features,
        row_batches[0].compiled.extents)


def _norm(value, gamma):
    return value * mx.rsqrt(
        mx.mean(value * value, axis=-1, keepdims=True)
        + ModelTopologySpecV2.rms_norm_epsilon) * gamma


def _decision_loss(params, anchors, keys, values, position_mask, role,
                   occurrence, feedback, candidates, candidate_mask, target_indices):
    combined = anchors + role[None, :] + occurrence + feedback @ params["readout.feedback"].T
    normalized = combined * mx.rsqrt(
        mx.mean(combined * combined, axis=-1, keepdims=True)
        + ModelTopologySpecV2.rms_norm_epsilon)
    normalized = normalized * params["readout.state_norm"]
    query = normalized @ params["readout.query"].T
    scores = mx.sum(query[:, None, :] * keys, axis=-1) / (_INNER ** .5)
    weights = mx.softmax(mx.where(position_mask, scores, -mx.inf), axis=-1)
    attended = (mx.sum(weights[..., None] * values, axis=1)
                @ params["readout.output"].T)
    state = _norm(normalized + attended, params["readout.output_norm"])
    logits = mx.sum(state[:, None, :] * candidates, axis=-1) / (_WIDTH ** .5)
    logits = mx.where(candidate_mask, logits, -mx.inf)
    target = mx.take_along_axis(logits, target_indices[:, None], axis=-1)[:, 0]
    return mx.logsumexp(logits, axis=-1) - target


def _salience_loss(params, hidden, kernel):
    rows = mx.arange(hidden.shape[0])
    query = hidden[rows, kernel.lengths - 1]
    logits = project_salience_heads(
        params, query, ModelTopologySpecV2(), kernel.extents, array_api=mx)
    total = mx.zeros((hidden.shape[0],), dtype=mx.float32)
    for name, (targets, active) in zip(_SALIENCE_HEADS, kernel.salience_targets):
        values = getattr(logits, name)
        selected = mx.take_along_axis(values, targets[:, None], axis=-1)[:, 0]
        loss = .05 * (mx.logsumexp(values, axis=-1) - selected)
        total = total + mx.where(active, loss, mx.zeros_like(loss))
    return total


def route_microbatch_mean_loss(
        params, hidden, kernel: RouteMicrobatchKernel, *, salience_hidden=None):
    """Return the exact row-mean route loss with row math batched on device."""
    position_mask = mx.arange(hidden.shape[1])[None, :] < kernel.lengths[:, None]
    rows = mx.arange(hidden.shape[0])
    anchors = hidden[rows, kernel.lengths - 1]
    keys = hidden @ params["readout.key"].T
    values = hidden @ params["readout.value"].T
    role = role_id_vector("NONE", SimpleNamespace(features=kernel.features), params)
    operator = mx.zeros((hidden.shape[0],), dtype=mx.float32)
    operand = mx.zeros((hidden.shape[0],), dtype=mx.float32)
    for operator_mask, operand_mask, occurrence, feedback, candidates, \
            candidate_mask, targets in zip(
                kernel.operator_masks, kernel.operand_masks,
                kernel.occurrences, kernel.feedback, kernel.candidate_vectors,
                kernel.candidate_masks, kernel.target_indices):
        loss = _decision_loss(
            params, anchors, keys, values, position_mask, role, occurrence, feedback,
            candidates, candidate_mask, targets)
        operator = operator + mx.where(
            operator_mask, loss, mx.zeros_like(loss))
        operand = operand + mx.where(
            operand_mask, loss, mx.zeros_like(loss))
    operator_denominator = mx.maximum(kernel.operator_counts, 1)
    operand_denominator = mx.maximum(kernel.operand_counts, 1)
    row_loss = mx.where(
        kernel.operator_counts > 0, operator / operator_denominator,
        mx.zeros_like(operator))
    row_loss = row_loss + mx.where(
        kernel.operand_counts > 0, operand / operand_denominator,
        mx.zeros_like(operand))
    if kernel.has_salience:
        if salience_hidden is None:
            _invalid("B11_MICROBATCH_SALIENCE_HIDDEN_REQUIRED")
        row_loss = row_loss + _salience_loss(params, salience_hidden, kernel)
    return mx.mean(row_loss)


__all__ = (
    "RouteMicrobatchKernel", "prepare_route_microbatch_kernel",
    "route_microbatch_compatible", "route_microbatch_mean_loss",
)
