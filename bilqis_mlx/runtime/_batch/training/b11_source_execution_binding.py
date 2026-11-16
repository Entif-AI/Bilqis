"""Bind source/motif facts once before B11 neural execution."""
from dataclasses import asdict, replace

from bilqis_mlx.errors import ErrorBus, SCHOOL
from bilqis_mlx.learning._engram.atlas_engram_source_context import (
    qualify_source_motif_context,
)
from bilqis_mlx.learning.atlas_engram_reads.source import (
    _schema_grant_live, schema_source_handle,
)
from bilqis_mlx.semantics.atlas_features.formal import source_qualified_feature_row
from bilqis_mlx.semantics.context_eligibility import (
    ApprovedContextProjection, ContextHold, project_context,
)
from bilqis_mlx.semantics.frame_compiler import PositionKind
from bilqis_mlx.semantics.frame_schema import FrameInstance
from bilqis_mlx.source_adapters.atom_binding import (
    _build_source_atom_handoff_from_snapshot,
)


def _invalid(reason):
    ErrorBus.Raise(SCHOOL.MODEL_TOPOLOGY.INVALID, reason=reason)


def bind_source_handoff(compiled_row, config, source, snapshot):
    handoff = _build_source_atom_handoff_from_snapshot(
        compiled_row, config, source.selection, snapshot, source.source_row,
        source.graph, **source.replay_arguments())
    if not handoff.embedding_ready:
        _invalid("B11_SOURCE_EXECUTION_HANDOFF_HELD")
    return handoff


def bind_motif_context(compiled_row, config, source, source_adapter, snapshot):
    task_scope = replace(config.task, causal_prefix_end=compiled_row.visible_end)
    replayed = qualify_source_motif_context(
        source_adapter, source.source_row, source.selection,
        source_root=source.source_root, graph=source.graph, task_scope=task_scope,
        source_frontier=config.frontier, policy=config.policy,
        source_seed=source.source_seed, source_each=source.source_each,
        source_profile_parameters=source.source_profile_parameters,
        course=source.course, snapshot=snapshot)
    if isinstance(replayed, ContextHold):
        _invalid("B11_SOURCE_EXECUTION_MOTIF_CONTEXT_HELD")
    projection, motifs, frontier = replayed
    return task_scope, projection, motifs, frontier


def motif_schema_map(motifs):
    schemas = {}

    def collect(item):
        previous = schemas.get(item.frame.occurrence_id)
        if previous is not None and previous != item.schema:
            _invalid("B11_SOURCE_EXECUTION_MOTIF_SCHEMA_DRIFT")
        schemas[item.frame.occurrence_id] = item.schema
        for child in item.children:
            collect(child)

    for motif in motifs:
        collect(motif)
    return schemas


def bind_motif_feature_rows(projection, motifs, features, source):
    schemas = motif_schema_map(motifs)
    rows = []
    for envelope in projection.envelopes:
        if type(envelope.frame) is not FrameInstance:
            continue
        if schemas.get(envelope.frame.occurrence_id) is None:
            _invalid("B11_SOURCE_EXECUTION_MOTIF_SCHEMA_MISSING")
        for binding in envelope.frame.bindings:
            if binding.concept is None:
                continue
            member = next((item for item in envelope.members
                           if item.key == binding.key), None)
            if member is None:
                _invalid("B11_SOURCE_EXECUTION_MOTIF_MEMBER_MISSING")
            row = source_qualified_feature_row(
                features, binding.concept, binding.role_id, envelope.frame,
                envelope.scope, source.selection,
                invalid=lambda: _invalid(
                    "B11_SOURCE_EXECUTION_FEATURE_AUTHORITY_INVALID"))
            rows.append((envelope.frame_handle, member.source_handle, row))
    return tuple(rows)


def bind_motif_execution_projection(
        compiled_row, config, motif_projection, frontier, task_scope):
    handles = tuple(position.frame_handle for position in compiled_row.positions
                    if position.kind is PositionKind.CLOSURE)
    if not handles or len(set(handles)) != len(handles):
        _invalid("B11_SOURCE_EXECUTION_MOTIF_PROJECTION_INVALID")
    handle_set = set(handles)
    envelopes = tuple(envelope for envelope in motif_projection.envelopes
                      if envelope.frame_handle in handle_set)
    if len(envelopes) != len(handles):
        _invalid("B11_SOURCE_EXECUTION_MOTIF_PROJECTION_INVALID")
    projection = project_context(envelopes, task_scope, frontier, config.policy)
    if (type(projection) is not ApprovedContextProjection
            or projection.digest != compiled_row.context_digest):
        _invalid("B11_SOURCE_EXECUTION_MOTIF_PROJECTION_INVALID")
    return projection


def bind_motif_read_context(projection, motifs, frontier, task_scope):
    schemas = motif_schema_map(motifs)
    grants = {item.source_handle: item for item in frontier.grants}
    dependencies, liveness = {}, {}
    for envelope in projection.envelopes:
        if type(envelope.frame) is not FrameInstance:
            continue
        schema = schemas.get(envelope.frame.occurrence_id)
        if schema is None:
            _invalid("B11_SOURCE_EXECUTION_MOTIF_SCHEMA_MISSING")
        handle = schema_source_handle(schema)
        grant = grants.get(handle)
        dependencies[handle] = None if grant is None else asdict(grant)
        liveness[handle] = _schema_grant_live(schema, envelope, task_scope, frontier)
    schema_rights = tuple(
        (handle, dependencies[handle]) for handle in sorted(dependencies))
    digest = (projection.cache_key("B08_SCHEMA_RIGHTS_V1", schema_rights)
              if schema_rights else projection.digest)
    return digest, tuple(sorted(liveness.items()))
