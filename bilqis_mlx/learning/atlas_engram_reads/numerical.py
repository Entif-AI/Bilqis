"""Experimental gated motif arithmetic; no source-admission authority."""
from __future__ import annotations

from dataclasses import asdict
import math

import mlx.core as mx

from bilqis_mlx.semantics.context_eligibility import ApprovedContextProjection, ContextHold, ContextPolicy, SourceFrontier, TaskScope, project_context
from bilqis_mlx.semantics.frame_schema import AtomicFrame
from bilqis_mlx.runtime.model_topology_v2 import ModelTopologySpecV2
from ..atlas_engram import (
    INITIAL_MOTIF_CAPACITY, MotifManifest, build_motif_input, motif_keys,
)
from ..atlas_engram_parameters import MotifParameterView, SITE_COUNT


from .records import _invalid, WIDTH, MOTIF_WIDTH, READ_TENSOR_RANK, FEATURE_AXIS, BATCH_PREFIX_AXES, MotifReadPosition, MotifReadResult
from .source import _schema_grant_live, schema_source_handle


def _schema_rights_dependency(row, frontier):
    grants = {item.source_handle: item for item in frontier.grants}
    dependencies = {}
    for item in row:
        if item is None or item.schema is None:
            continue
        handle = schema_source_handle(item.schema)
        grant = grants.get(handle)
        dependencies[handle] = None if grant is None else asdict(grant)
    return tuple((handle, dependencies[handle]) for handle in sorted(dependencies))

def _validate_candidate_inputs(
    site_index, hidden, features, positions, tasks, frontiers, policies,
    manifest, parameters,
):
    if (type(site_index) is not int or not 0 <= site_index < SITE_COUNT
            or type(manifest) is not MotifManifest
            or type(parameters) is not MotifParameterView
            or parameters.site_index != site_index
            or manifest.capacity > parameters.page_count * INITIAL_MOTIF_CAPACITY
            or not isinstance(hidden, mx.array) or hidden.ndim != READ_TENSOR_RANK
            or hidden.shape[FEATURE_AXIS] != WIDTH or hidden.dtype != mx.float32
            or not isinstance(features, mx.array)
            or features.shape != (*hidden.shape[:BATCH_PREFIX_AXES], MOTIF_WIDTH)
            or features.dtype != mx.float32
            or not isinstance(positions, tuple)
            or not isinstance(tasks, tuple)
            or not isinstance(frontiers, tuple)
            or not isinstance(policies, tuple)
            or not (len(positions) == len(tasks) == len(frontiers)
                    == len(policies) == hidden.shape[0])
            or any(not isinstance(row, tuple) or len(row) != hidden.shape[1]
                   or any(item is not None and type(item) is not MotifReadPosition
                          for item in row) for row in positions)
            or any(type(item) is not TaskScope for item in tasks)
            or any(type(item) is not SourceFrontier for item in frontiers)
            or any(type(item) is not ContextPolicy for item in policies)
            or not bool(mx.all(mx.isfinite(hidden)))
            or not bool(mx.all(mx.isfinite(features)))):
        _invalid()
    parameters.__post_init__()


def _lookup_slot(item, manifest, row):
    qualified = {
        position.envelope.frame.occurrence_id:
            (position.envelope.frame, position.schema)
        for position in row
        if position is not None and type(position.envelope.frame) is not AtomicFrame
    }
    atomic = {
        position.envelope.frame.occurrence_id: position.envelope.frame
        for position in row
        if position is not None and type(position.envelope.frame) is AtomicFrame
    }
    source = build_motif_input(
        item.envelope.frame.occurrence_id, qualified, atomic)
    exact, structural = motif_keys(source, manifest.semantic_release)
    slot_id = manifest.lookup(exact)
    disposition = "EXACT"
    if slot_id is None:
        slot_id = manifest.lookup(structural)
        disposition = "STRUCTURAL"
    return slot_id, disposition


def _gated_residual(state, feature, slot_id, parameters, projections):
    page_index, local_index = divmod(slot_id, INITIAL_MOTIF_CAPACITY)
    slot_vector = parameters[f"page.{page_index}"][local_index]
    normalized = mx.fast.rms_norm(
        state, projections["norm"], ModelTopologySpecV2.rms_norm_epsilon)
    gate_logit = (
        mx.sum(projections["gate_hidden"] * normalized) / math.sqrt(WIDTH)
        + mx.sum(projections["gate_feature"] * feature)
        / math.sqrt(MOTIF_WIDTH)
        + projections["bias"][0]
    )
    gate = mx.sigmoid(gate_logit)
    return state + gate * (projections["projection"] @ slot_vector)


def _read_row(
    row_index, row, hidden, features, task, frontier, policy,
    manifest, parameters, projections,
):
    unchanged = tuple(
        hidden[row_index, index] for index in range(hidden.shape[1]))
    envelopes = tuple(item.envelope for item in row if item is not None)
    if not envelopes:
        return unchanged, ("MISS",) * hidden.shape[1], None, ()
    projection = project_context(envelopes, task, frontier, policy)
    if isinstance(projection, ContextHold):
        status = tuple("HELD" if item is not None else "MISS" for item in row)
        return unchanged, status, None, ()
    if type(projection) is not ApprovedContextProjection:
        _invalid()
    schema_rights = _schema_rights_dependency(row, frontier)
    context_digest = (
        projection.cache_key("B08_SCHEMA_RIGHTS_V1", schema_rights)
        if schema_rights else projection.digest)
    live_schema_handles = {}
    for item in row:
        if item is None or type(item.envelope.frame) is AtomicFrame:
            continue
        handle = schema_source_handle(item.schema)
        live_schema_handles[handle] = _schema_grant_live(
            item.schema, item.envelope, task, frontier)
    row_schema_live = all(live_schema_handles.values())
    output, status, participating = [], [], set()
    for index, item in enumerate(row):
        state = hidden[row_index, index]
        if item is None or type(item.envelope.frame) is AtomicFrame:
            output.append(state)
            status.append("MISS")
            continue
        if task.semantic_release != manifest.semantic_release:
            output.append(state)
            status.append("FOREIGN_RELEASE")
            continue
        if projection.frame(item.envelope.frame_handle) != item.envelope.frame:
            _invalid()
        if (not row_schema_live
                or not live_schema_handles[schema_source_handle(item.schema)]):
            output.append(state)
            status.append("HELD")
            continue
        slot_id, disposition = _lookup_slot(item, manifest, row)
        if slot_id is None:
            output.append(state)
            status.append("MISS")
            continue
        output.append(_gated_residual(
            state, features[row_index, index], slot_id, parameters, projections))
        status.append(disposition)
        participating.add(slot_id)
    return tuple(output), tuple(status), context_digest, tuple(participating)


def _read_motif_unqualified_candidate(
    *,
    site_index: int,
    hidden: mx.array,
    features: mx.array,
    positions: tuple[tuple[MotifReadPosition | None, ...], ...],
    tasks: tuple[TaskScope, ...],
    frontiers: tuple[SourceFrontier, ...],
    policies: tuple[ContextPolicy, ...],
    manifest: MotifManifest,
    parameters: MotifParameterView,
) -> MotifReadResult:
    """Experimental helper; set eligibility precedes every row's slot gather.

    B11 must bind feature128 to B02 source features. Caller vectors confer
    no source authority; individually eligible frames cannot bypass join checks.
    """
    _validate_candidate_inputs(
        site_index, hidden, features, positions, tasks, frontiers, policies,
        manifest, parameters)
    projections = {name: parameters[name] for name in (
        "projection", "norm", "gate_hidden", "gate_feature", "bias")}
    output_rows = []
    dispositions = []
    context_digests = []
    participating = set()
    row_participating = []
    for row_index, row in enumerate(positions):
        task, frontier, policy = tasks[row_index], frontiers[row_index], policies[row_index]
        output, status, digest, row_slots = _read_row(
            row_index, row, hidden, features, task, frontier, policy,
            manifest, parameters, projections)
        output_rows.append(output)
        dispositions.append(status)
        context_digests.append(digest)
        row_participating.append(tuple(sorted(row_slots)))
        participating.update(row_slots)
    if not participating:
        return MotifReadResult(
            hidden, tuple(dispositions), (), tuple(context_digests),
            tuple(row_participating))
    return MotifReadResult(
        mx.stack(tuple(mx.stack(row) for row in output_rows)),
        tuple(dispositions), tuple(sorted(participating)),
        tuple(context_digests), tuple(row_participating),
    )
