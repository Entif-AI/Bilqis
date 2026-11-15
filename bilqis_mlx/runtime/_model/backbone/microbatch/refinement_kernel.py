"""Batched B06 refinement over statically selected microbatch frames."""
from __future__ import annotations

from types import SimpleNamespace

import mlx.core as mx

from bilqis_mlx.runtime.atlas_refinement import (
    INNER, MAX_LOCAL_PASSES, RESIDUAL_GATE_SCALE, _norm,
)

from ..atlas_model_contracts import _invalid
from ..atlas_model_refinement import (
    _prediction_refinement_selection, _refinement_role_vector,
    _selected_frame_index,
)


def prepare_refinement_selections(
        row_batches, answer_plans, generation):
    """Resolve every policy-only refinement choice before autodiff begins."""
    return tuple(
        _prediction_refinement_selection(
            row_batch, plan, generation, training=True)
        for row_batch, plan in zip(row_batches, answer_plans)
    )


def _role_batch(params, row_batches, selections):
    features = row_batches[0].compiled.features
    semantics = SimpleNamespace(features=features)
    values = []
    for selection in selections:
        if selection is None:
            request = SimpleNamespace(requested_roles=())
        else:
            request = selection[0]
        role, _roles = _refinement_role_vector(request, semantics, params)
        values.append(role)
    return mx.stack(tuple(values))


def _slot_inputs(producer, row_batches, selections, slot, width):
    positions, passes, members, seeds = [], [], [], []
    max_members = 1
    raw = []
    for row_index, (row_batch, selection) in enumerate(zip(row_batches, selections)):
        choices = () if selection is None else selection[1]
        if slot >= len(choices):
            raw.append((0, 0, None, None))
            continue
        choice = choices[slot]
        row = row_batch.compiled.compiled.rows[0]
        config = row_batch.compiled.compiler_configs[0]
        position = _selected_frame_index(
            row, producer._encoded, config, choice, row_index=row_index)
        member_values = producer._encoded.members[row_index][position]
        if choice.passes > 0 and member_values.shape[0] == 0:
            _invalid("B11_REFINEMENT_MEMBER_INPUT_REQUIRED")
        max_members = max(max_members, member_values.shape[0])
        raw.append((
            position, choice.passes, member_values,
            producer._encoded.global_seeds[row_index, position],
        ))
    zero_member = mx.zeros((max_members, width), dtype=mx.float32)
    zero_seed = mx.zeros((width,), dtype=mx.float32)
    for position, count, member_values, seed in raw:
        positions.append(position)
        passes.append(count)
        if member_values is None:
            members.append(zero_member)
            seeds.append(zero_seed)
            continue
        padding = max_members - member_values.shape[0]
        members.append(
            member_values if padding == 0 else
            mx.pad(member_values, ((0, padding), (0, 0))))
        seeds.append(seed)
    counts = tuple(
        1 if item[2] is None else max(1, item[2].shape[0]) for item in raw)
    return (
        mx.array(positions, dtype=mx.int32),
        mx.array(passes, dtype=mx.int32),
        mx.array(counts, dtype=mx.int32),
        mx.stack(tuple(members)),
        mx.stack(tuple(seeds)),
    )


def _batched_refine_slot(
        params, state, seeds, role, members, member_counts, passes):
    """Run one selected-frame slot for every row without rowwise kernels."""
    keys = members @ params["refine.key"].T
    values = members @ params["refine.value"].T
    member_mask = mx.arange(members.shape[1])[None, :] < member_counts[:, None]
    for pass_index in range(MAX_LOCAL_PASSES):
        query = _norm(
            state + seeds + role, params["refine.norm"]) @ params["refine.query"].T
        scores = mx.sum(query[:, None, :] * keys, axis=-1) / (INNER ** .5)
        attention = mx.softmax(mx.where(member_mask, scores, -mx.inf), axis=-1)
        residual = (mx.sum(attention[..., None] * values, axis=1)
                    @ params["refine.output"].T)
        gate = RESIDUAL_GATE_SCALE * mx.sigmoid(
            mx.sum(_norm(state, params["refine.norm"])
                   * params["refine.gate_vector"], axis=-1)
            + params["refine.bias"])
        candidate = state + gate[:, None] * residual
        active = passes > pass_index
        state = mx.where(active[:, None], candidate, state)
    return state


def batched_refine_hidden(params, row_batches, producer, hidden, selections):
    """Apply selected local refinement with one batched kernel per selection slot."""
    slots = max((0 if item is None else len(item[1]) for item in selections), default=0)
    if slots == 0:
        return hidden
    width = hidden.shape[-1]
    batch_size = hidden.shape[0]
    rows = mx.arange(batch_size)
    role = _role_batch(params, row_batches, selections)
    refined = hidden
    for slot in range(slots):
        positions, passes, member_counts, members, seeds = _slot_inputs(
            producer, row_batches, selections, slot, width)
        state = refined[rows, positions]
        state = _batched_refine_slot(
            params, state, seeds, role, members, member_counts, passes)
        position_mask = (
            mx.arange(refined.shape[1])[None, :] == positions[:, None])
        position_mask = position_mask & (passes[:, None] > 0)
        refined = mx.where(position_mask[..., None], state[:, None, :], refined)
    return refined


__all__ = ("batched_refine_hidden", "prepare_refinement_selections")
