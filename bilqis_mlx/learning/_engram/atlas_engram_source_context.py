"""Source-context qualification mechanics for B07 motif preparation."""
from __future__ import annotations

from pathlib import Path

from bilqis_mlx.factory.adapters import RegisteredSourceAdapter
from bilqis_mlx.semantics.atlas.snapshot import (
    AtlasArtifactSelection, load_pinned_atlas_snapshot,
)
from bilqis_mlx.semantics.atlas_projection import FrozenAtlasSnapshot
from bilqis_mlx.semantics.context_eligibility import (
    ApprovedContextProjection, ContextHold, ContextPolicy, SourceFrontier,
    TaskScope, project_context,
)
from bilqis_mlx.semantics.frame_adapters.registry import source_frame_strategy
from bilqis_mlx.semantics.frame_adapters.public_formal import public_formal_context
from bilqis_mlx.semantics.frame_adapters.public_formal_grants import (
    _issue_source_schema_grants_from_snapshot, issue_source_schema_grants,
)
from bilqis_mlx.semantics.frame_adapters.public_formal_schema_rights import (
    issue_source_schema_rights_authority, source_schema_rights_frontier,
)
from bilqis_mlx.semantics.frame_adapters.public_formal_sources import canonical_graph
from bilqis_mlx.semantics.frame_adapters.public_formal_sources import (
    _require_public_formal_projection_authority,
)
from bilqis_mlx.semantics.frame_schema import FrameInstance, validate_frame_bindings
from bilqis_mlx.semantics.released_frame_schemas import (
    _load_pinned_released_frame_schemas_from_snapshot,
)

from .atlas_engram_identity import MotifFrameInput, _invalid
from .atlas_engram_keys import build_motif_input


def _source_family(adapter_id: str) -> str | None:
    return source_frame_strategy(adapter_id).source_family


def _qualify_frame(envelope, snapshot, pinned_schemas,
                   source_root, graph, adapter_id):
    frame = envelope.frame
    witness = pinned_schemas.lookup(
        frame.frame_schema_id, frame.frame_schema_revision)
    body = next((
        item for item in pinned_schemas.manifest.bodies
        if (item.schema_id, item.revision)
        == (frame.frame_schema_id, frame.frame_schema_revision)
    ), None)
    if body is None:
        _invalid("BAMF_MOTIF_SOURCE_SCHEMA_UNRELEASED")
    schema = pinned_schemas.require_schema(body.parse(), witness)
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
    if source_family is None:
        if any(isinstance(envelope.frame, FrameInstance)
               for envelope in projection.envelopes):
            _invalid("BAMF_MOTIF_SOURCE_SCHEMA_UNRELEASED")
        return ()
    pinned_schemas = _load_pinned_released_frame_schemas_from_snapshot(
        source_family, atlas_selection, snapshot)
    qualified = {}
    for envelope in projection.envelopes:
        if not isinstance(envelope.frame, FrameInstance):
            continue
        frame, schema = _qualify_frame(
            envelope, snapshot, pinned_schemas,
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
    snapshot: FrozenAtlasSnapshot | None = None,
) -> tuple[
    ApprovedContextProjection, tuple[MotifFrameInput, ...], SourceFrontier,
] | ContextHold:
    """Replay A03/A13 owners and expose derived motif context, never authority."""
    if (type(atlas_selection) is not AtlasArtifactSelection
            or type(task_scope) is not TaskScope
            or type(source_frontier) is not SourceFrontier
            or type(policy) is not ContextPolicy):
        _invalid("BAMF_MOTIF_SOURCE_AUTHORITY_INVALID")
    if snapshot is None:
        snapshot = load_pinned_atlas_snapshot(atlas_selection)
    elif (
        type(snapshot) is not FrozenAtlasSnapshot
        or (
            snapshot.release_sha256,
            snapshot.bundle_id,
            snapshot.source_bundle_id,
        ) != (
            atlas_selection.release_sha256,
            atlas_selection.bundle_id,
            atlas_selection.source_bundle_id,
        )
    ):
        _invalid("BAMF_MOTIF_SOURCE_AUTHORITY_INVALID")
    if snapshot.release_sha256 != task_scope.semantic_release:
        _invalid("BAMF_MOTIF_SOURCE_AUTHORITY_INVALID")
    source_family = _source_family(source_adapter.descriptor.adapter_id)
    if source_family is None:
        if policy.rights_epoch != source_frontier.rights_epoch:
            _invalid("BAMF_MOTIF_SOURCE_POLICY_STALE")
    else:
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
    if source_family is not None:
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


def qualify_prepared_source_motif_context(
    source_adapter: RegisteredSourceAdapter,
    projection: ApprovedContextProjection,
    prepared_frontier: SourceFrontier,
    atlas_selection: AtlasArtifactSelection,
    *,
    source_root: str | Path,
    graph: dict,
    task_scope: TaskScope,
    source_frontier: SourceFrontier,
    policy: ContextPolicy,
    snapshot: FrozenAtlasSnapshot,
) -> tuple[ApprovedContextProjection, tuple[MotifFrameInput, ...], SourceFrontier]:
    """Rebind a source-owner projection without replaying its provider proof."""
    if (not isinstance(source_adapter, RegisteredSourceAdapter)
            or type(projection) is not ApprovedContextProjection
            or type(atlas_selection) is not AtlasArtifactSelection
            or type(snapshot) is not FrozenAtlasSnapshot
            or type(task_scope) is not TaskScope
            or type(prepared_frontier) is not SourceFrontier
            or type(source_frontier) is not SourceFrontier
            or type(policy) is not ContextPolicy
            or (snapshot.release_sha256, snapshot.bundle_id,
                snapshot.source_bundle_id) != (
                    atlas_selection.release_sha256, atlas_selection.bundle_id,
                    atlas_selection.source_bundle_id)
            or snapshot.release_sha256 != task_scope.semantic_release):
        _invalid("BAMF_MOTIF_SOURCE_AUTHORITY_INVALID")
    adapter_id = source_adapter.descriptor.adapter_id
    _require_public_formal_projection_authority(projection, adapter_id)
    source_family = _source_family(adapter_id)
    if source_family is None:
        if (prepared_frontier.rights_epoch != source_frontier.rights_epoch
                or prepared_frontier.correction_generation
                != source_frontier.correction_generation):
            _invalid("BAMF_MOTIF_SOURCE_AUTHORITY_STALE")
        if policy.rights_epoch != source_frontier.rights_epoch:
            _invalid("BAMF_MOTIF_SOURCE_POLICY_STALE")
    else:
        rights_authority = issue_source_schema_rights_authority(atlas_selection)
        owner_frontier = source_schema_rights_frontier(rights_authority)
        if (prepared_frontier.rights_epoch != owner_frontier.rights_epoch
                or prepared_frontier.correction_generation
                != owner_frontier.correction_generation
                or source_frontier.rights_epoch != owner_frontier.rights_epoch
                or source_frontier.correction_generation
                != owner_frontier.correction_generation):
            _invalid("BAMF_MOTIF_SOURCE_AUTHORITY_STALE")
        if policy.rights_epoch != owner_frontier.rights_epoch:
            _invalid("BAMF_MOTIF_SOURCE_POLICY_STALE")
    replayed = project_context(
        projection.envelopes, task_scope, prepared_frontier, policy)
    if type(replayed) is not ApprovedContextProjection or replayed != projection:
        _invalid("BAMF_MOTIF_SOURCE_PREPARED_CONTEXT_DRIFT")
    grants = {item.source_handle: item for item in source_frontier.grants}
    for grant in prepared_frontier.grants:
        prior = grants.get(grant.source_handle)
        if prior is not None and prior != grant:
            _invalid("BAMF_MOTIF_SOURCE_PREPARED_FRONTIER_DRIFT")
        grants[grant.source_handle] = grant
    source_frontier = SourceFrontier(
        source_frontier.rights_epoch, source_frontier.correction_generation,
        tuple(sorted(grants.values(), key=lambda item: item.source_handle)))
    issued_frontier = source_frontier
    if source_family is not None:
        issued_frontier = _issue_source_schema_grants_from_snapshot(
            projection,
            source_adapter_id=adapter_id,
            atlas_selection=atlas_selection,
            task_scope=task_scope,
            source_frontier=source_frontier,
            policy=policy,
            snapshot=snapshot,
        )
    qualified = _qualified_motif_inputs(
        projection, snapshot, source_adapter, atlas_selection, source_root, graph)
    return projection, qualified, issued_frontier
