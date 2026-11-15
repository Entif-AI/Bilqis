"""Source-context qualification mechanics for B07 motif preparation."""
from __future__ import annotations

from pathlib import Path

from bilqis_mlx.factory.adapters import RegisteredSourceAdapter
from bilqis_mlx.semantics.atlas.snapshot import (
    AtlasArtifactSelection, load_pinned_atlas_snapshot,
)
from bilqis_mlx.semantics.context_eligibility import (
    ApprovedContextProjection, ContextHold, ContextPolicy, SourceFrontier,
    TaskScope,
)
from bilqis_mlx.semantics.frame_adapters.common import (
    BOOLEAN_COMPOSITE_ADAPTER, BOOLEAN_CONNECTIVE_ADAPTER,
    BOOLEAN_IDENTIFICATION_ADAPTER, FINITE_NUMERIC_ADAPTER,
    MICRO_PREDICATE_ADAPTER,
)
from bilqis_mlx.semantics.frame_adapters.public_formal import public_formal_context
from bilqis_mlx.semantics.frame_adapters.public_formal_grants import (
    issue_source_schema_grants,
)
from bilqis_mlx.semantics.frame_adapters.public_formal_schema_rights import (
    issue_source_schema_rights_authority, source_schema_rights_frontier,
)
from bilqis_mlx.semantics.frame_adapters.public_formal_sources import canonical_graph
from bilqis_mlx.semantics.frame_schema import FrameInstance, validate_frame_bindings
from bilqis_mlx.semantics.released_frame_schemas import (
    lookup_source_pinned_frame_schema,
)

from .atlas_engram import MotifFrameInput, build_motif_input
from .atlas_engram_identity import _invalid


_BOOLEAN_SOURCE_ADAPTERS = (
    BOOLEAN_CONNECTIVE_ADAPTER,
    BOOLEAN_COMPOSITE_ADAPTER,
    BOOLEAN_IDENTIFICATION_ADAPTER,
)


def _source_family(adapter_id: str) -> str:
    if adapter_id == MICRO_PREDICATE_ADAPTER:
        return "micro"
    if adapter_id in _BOOLEAN_SOURCE_ADAPTERS:
        return "boolean"
    if adapter_id == FINITE_NUMERIC_ADAPTER:
        return "numeric"
    _invalid("BAMF_MOTIF_SOURCE_FAMILY_UNRELEASED")


def _qualify_frame(envelope, snapshot, source_family, atlas_selection,
                   source_root, graph, adapter_id):
    frame = envelope.frame
    schema, _witness = lookup_source_pinned_frame_schema(
        frame.frame_schema_id, frame.frame_schema_revision,
        source_family=source_family, atlas_selection=atlas_selection,
    )
    _, authoritative_graph = canonical_graph(
        source_root, graph, adapter_id, frame.source_span)
    validated = validate_frame_bindings(
        schema, snapshot, bindings=frame.bindings,
        source_span=frame.source_span,
        causal_prefix_end=frame.causal_prefix_end,
        declared_scope=schema.scope,
        source_graph=authoritative_graph, source_adapter_id=adapter_id,
    )
    if validated != frame.bindings:
        _invalid("BAMF_MOTIF_SOURCE_BINDING_DRIFT")
    for binding in validated:
        concepts = ((binding.concept,) if binding.concept is not None
                    else binding.alternatives)
        if any(not snapshot.abi_for_semantic(concept.semantic_id).active
               for concept in concepts):
            _invalid("BAMF_MOTIF_SEMANTIC_NOT_ADMITTED")
    return frame, schema


def _qualified_motif_inputs(projection, snapshot, source_adapter,
                            atlas_selection, source_root, graph):
    adapter_id = source_adapter.descriptor.adapter_id
    source_family = _source_family(adapter_id)
    atomic = {
        envelope.frame.occurrence_id: envelope.frame
        for envelope in projection.envelopes
        if not isinstance(envelope.frame, FrameInstance)
    }
    qualified = {}
    for envelope in projection.envelopes:
        if not isinstance(envelope.frame, FrameInstance):
            continue
        frame, schema = _qualify_frame(
            envelope, snapshot, source_family, atlas_selection,
            source_root, graph, adapter_id)
        if frame.occurrence_id in qualified:
            _invalid("BAMF_MOTIF_CHILD_STRUCTURE_INVALID")
        qualified[frame.occurrence_id] = (frame, schema)
    return tuple(
        build_motif_input(envelope.frame.occurrence_id, qualified, atomic)
        for envelope in projection.envelopes
        if isinstance(envelope.frame, FrameInstance)
    )


def qualify_source_motif_context(
    source_adapter: RegisteredSourceAdapter,
    row: dict,
    atlas_selection: AtlasArtifactSelection,
    *,
    source_root: str | Path,
    graph: dict,
    task_scope: TaskScope,
    source_frontier: SourceFrontier,
    policy: ContextPolicy,
    source_seed: int,
    source_each: int,
    source_profile_parameters: dict | None = None,
    course=None,
) -> tuple[
    ApprovedContextProjection, tuple[MotifFrameInput, ...], SourceFrontier,
] | ContextHold:
    """Replay A03/A13 owners and expose derived motif context, never authority."""
    if (type(atlas_selection) is not AtlasArtifactSelection
            or type(task_scope) is not TaskScope
            or type(source_frontier) is not SourceFrontier
            or type(policy) is not ContextPolicy):
        _invalid("BAMF_MOTIF_SOURCE_AUTHORITY_INVALID")
    snapshot = load_pinned_atlas_snapshot(atlas_selection)
    if snapshot.release_sha256 != task_scope.semantic_release:
        _invalid("BAMF_MOTIF_SOURCE_AUTHORITY_INVALID")
    rights_authority = issue_source_schema_rights_authority(atlas_selection)
    owner_frontier = source_schema_rights_frontier(rights_authority)
    if not source_frontier.grants:
        source_frontier = owner_frontier
    elif (
        source_frontier.rights_epoch != owner_frontier.rights_epoch
        or source_frontier.correction_generation
        != owner_frontier.correction_generation
    ):
        _invalid("BAMF_MOTIF_SOURCE_AUTHORITY_STALE")
    if policy.rights_epoch != owner_frontier.rights_epoch:
        _invalid("BAMF_MOTIF_SOURCE_POLICY_STALE")
    admitted = public_formal_context(
        source_adapter, row, snapshot, source_root=source_root, graph=graph,
        task_scope=task_scope, source_frontier=source_frontier, policy=policy,
        source_seed=source_seed, source_each=source_each,
        source_profile_parameters=source_profile_parameters, course=course)
    if isinstance(admitted, ContextHold):
        return admitted
    projection, issued_frontier = admitted
    issued_frontier = issue_source_schema_grants(
        projection,
        source_adapter_id=source_adapter.descriptor.adapter_id,
        atlas_selection=atlas_selection,
        task_scope=task_scope,
        source_frontier=issued_frontier,
        policy=policy,
    )
    qualified = _qualified_motif_inputs(
        projection, snapshot, source_adapter, atlas_selection, source_root, graph)
    return projection, qualified, issued_frontier
