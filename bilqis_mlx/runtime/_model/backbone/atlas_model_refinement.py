"""Prediction-local B06 refinement assembly for the B11 forward."""
from __future__ import annotations

from dataclasses import replace

import mlx.core as mx

from bilqis_mlx.learning.atlas_readout.decoder.feedback import role_id_vector
from bilqis_mlx.runtime.atlas_refinement import (
    _refine_frame, refinement_parameter_view, routing_logits_from_state,
)
from bilqis_mlx.runtime.model_topology_v2 import ModelTopologySpecV2
from bilqis_mlx.runtime.refinement_policy import select_prediction_refinements
from bilqis_mlx.runtime.refinement_request import refinement_request_disposition
from bilqis_mlx.semantics.context_eligibility import ContextHold
from bilqis_mlx.semantics.frame_compiler import PositionKind

from .atlas_model_contracts import _invalid


REFINEMENT_MEMBER_RANK = 2


def _refinement_role_vector(request, semantics, params):
    """Reuse canonical NONE/single-role projection; undefined pooling fails closed."""
    roles = request.requested_roles
    if len(roles) > 1:
        _invalid("B11_REFINEMENT_MULTI_ROLE_UNRESOLVED")
    identifier = roles[0] if roles else "NONE"
    return role_id_vector(identifier, semantics, params), (identifier,)


def _selected_frame_index(row, encoded, config, choice, *, row_index=0):
    matches = tuple(
        (index, position) for index, position in enumerate(row.positions)
        if position.kind is PositionKind.CLOSURE
        and position.frame_handle == choice.frame_handle
    )
    if len(matches) != 1:
        _invalid("B11_REFINEMENT_FRAME_BINDING_INVALID")
    index, position = matches[0]
    position.__post_init__()
    if (
        type(row_index) is not int
        or not 0 <= row_index < len(encoded.handles)
        or position.packed is None
        or position.packed.sidecar.occurrence_id != choice.occurrence_id
        or encoded.handles[row_index][index] != position
        or config.approved is None
    ):
        _invalid("B11_REFINEMENT_FRAME_BINDING_INVALID")
    envelope = next(
        (item for item in config.approved.envelopes
         if item.frame_handle == choice.frame_handle),
        None,
    )
    if (
        envelope is None
        or envelope.frame.occurrence_id != choice.occurrence_id
        or encoded.global_seeds[row_index, index].shape != (ModelTopologySpecV2.width,)
        or encoded.members[row_index][index].ndim != REFINEMENT_MEMBER_RANK
        or encoded.members[row_index][index].shape[1] != ModelTopologySpecV2.width
        or encoded.members[row_index][index].shape[0] != len(envelope.members)
    ):
        _invalid("B11_REFINEMENT_FRAME_BINDING_INVALID")
    return index


def _prediction_local_refinement_with_routing(
    params, compiled_batch, answer_plan, generation, producer, row_hidden, semantics,
    *, training, producer_row_index=0,
):
    selection = _prediction_refinement_selection(
        compiled_batch, answer_plan, generation, training=training)
    if selection is None:
        return row_hidden, (), False, ()
    request, choices = selection
    compiled = compiled_batch.compiled
    config = compiled.compiler_configs[0]
    if (
        type(producer_row_index) is not int
        or not 0 <= producer_row_index < len(producer._encoded.compiled.rows)
        or producer._encoded.compiled.rows[producer_row_index]
        != compiled.compiled.rows[0]
    ):
        _invalid("B11_REFINEMENT_SOURCE_CUSTODY_REQUIRED")
    if not choices:
        return row_hidden, (), False, ()
    role, roles = _refinement_role_vector(request, semantics, params)
    parameters = refinement_parameter_view(
        params, spec=ModelTopologySpecV2(), extents=compiled.extents)
    row = compiled.compiled.rows[0]
    values = [row_hidden[index] for index in range(row_hidden.shape[0])]
    executed = False
    routing = []
    for choice in choices:
        index = _selected_frame_index(
            row, producer._encoded, config, choice,
            row_index=producer_row_index)
        if training:
            routing.append((
                routing_logits_from_state(values[index], parameters),
                choice.passes,
            ))
        if choice.passes == 0:
            continue
        members = producer._encoded.members[producer_row_index][index]
        if members.shape[0] == 0:
            _invalid("B11_REFINEMENT_MEMBER_INPUT_REQUIRED")
        result = _refine_frame(
            values[index], producer._encoded.global_seeds[producer_row_index, index],
            members, role, choice.passes, parameters)
        values[index] = result.hidden
        executed = True
    return (
        (mx.stack(tuple(values)) if executed else row_hidden),
        roles, executed, tuple(routing))


def _prediction_local_refinement(
    params, compiled_batch, answer_plan, generation, producer, row_hidden, semantics,
    *, training, producer_row_index=0,
):
    hidden, roles, executed, _routing = _prediction_local_refinement_with_routing(
        params, compiled_batch, answer_plan, generation, producer, row_hidden, semantics,
        training=training, producer_row_index=producer_row_index)
    return hidden, roles, executed

def _prediction_refinement_selection(
    compiled_batch, answer_plan, generation, *, training,
):
    """Resolve the static B06 selection before numerical refinement executes."""
    authority = compiled_batch.task_authority
    if authority is None:
        return None
    request = refinement_request_disposition(authority.goal)
    if answer_plan.refinement_request != request:
        _invalid("B11_REFINEMENT_REQUEST_AUTHORITY_MISMATCH")
    row = compiled_batch.compiled.compiled.rows[0]
    if not any(position.kind is PositionKind.CLOSURE for position in row.positions):
        return None
    compiled = compiled_batch.compiled
    config = compiled.compiler_configs[0]
    source_asts = compiled.source_asts
    if (
        source_asts is None
        or len(source_asts) != 1
        or config.approved is None
    ):
        _invalid("B11_REFINEMENT_SOURCE_CUSTODY_REQUIRED")
    task = replace(config.task, causal_prefix_end=row.visible_end)
    visit = compiled_batch.visit_provenance
    if training and visit is None:
        _invalid("B11_REFINEMENT_TRAINING_VISIT_REQUIRED")
    selection = select_prediction_refinements(
        frames=config.approved.envelopes,
        source_ast=source_asts[0],
        compiler_config=config,
        task_scope=task,
        source_frontier=config.frontier,
        policy=config.policy,
        input_generation=generation,
        query_id=compiled_batch.sources[0].source_row["id"],
        requested_roles=request.requested_roles,
        run_seed=visit.run_seed if training else None,
        visit_id=visit.visit_id if training else None,
        training=training,
        explicit_member_question=request.explicit_member_question,
        unresolved_nested_query=request.unresolved_nested_query,
    )
    if isinstance(selection, ContextHold):
        _invalid("B11_REFINEMENT_CONTEXT_HELD")
    return request, selection.selected


__all__ = (
    "_prediction_local_refinement", "_prediction_local_refinement_with_routing",
    "_refinement_role_vector",
    "_prediction_refinement_selection",
    "_selected_frame_index",
)
