"""Source and semantic authority checks for C02 training inputs."""
from __future__ import annotations

from bilqis_mlx.semantics.atlas_features import AtlasFeatures
from bilqis_mlx.semantics.atlas_features.formal import source_qualified_feature_row
from bilqis_mlx.semantics.context_eligibility import (
    ApprovedContextProjection, ContextPolicy, SourceFrontier, TaskScope,
)
from bilqis_mlx.semantics.frame_compiler import FrameCompilerConfig, StreamingAST
from bilqis_mlx.semantics.frame_schema import FrameInstance

from .atlas_training_contracts import _invalid
from .factory_training_context import source_frame_inventory


SOURCE_INVENTORY_PARTS = 2
SOURCE_INVENTORY_ID_INDEX = 0
SOURCE_INVENTORY_FRAMES_INDEX = 1


def require_source_inventory(
        ast, source_context, row, atlas_selection, semantic_context=None,
        released_manifest=None, *, prepared_inventory=None) -> None:
    if prepared_inventory is not None:
        if (type(prepared_inventory) is not tuple
                or len(prepared_inventory) != SOURCE_INVENTORY_PARTS
                or not isinstance(prepared_inventory[SOURCE_INVENTORY_ID_INDEX], str)
                or not prepared_inventory[SOURCE_INVENTORY_ID_INDEX]
                or type(prepared_inventory[SOURCE_INVENTORY_FRAMES_INDEX]) is not tuple):
            _invalid("CONTEXT_SOURCE_LINEAGE_MISMATCH")
        source_id, frames = prepared_inventory
    elif semantic_context is None:
        source_id, frames = source_frame_inventory(source_context, row, atlas_selection)
    else:
        from .factory_training_context import _source_frame_inventory_from_context
        source_id, frames = _source_frame_inventory_from_context(
            source_context, row, semantic_context, released_manifest)
    if (type(ast) is not StreamingAST or ast.source_instance_id != source_id
            or ast.frames != frames):
        _invalid("CONTEXT_SOURCE_LINEAGE_MISMATCH")


def source_frame_roots(ast: StreamingAST) -> tuple:
    roots = []

    def walk(tree) -> None:
        for child in tree.children:
            walk(child)
        roots.append(tree.root)

    for tree in ast.frames:
        walk(tree)
    return tuple(sorted(roots, key=lambda frame: frame.occurrence_id))


def require_source_lineage(ast, frames, visible, graph) -> None:
    source_instance_id = getattr(ast, "source_instance_id", None)
    try:
        expected_tokens = tuple(graph["tokens"][token_id] for token_id in visible)
    except (KeyError, IndexError, TypeError):
        _invalid("CONTEXT_SOURCE_LINEAGE_MISMATCH")
    admitted_frames = tuple(sorted(
        (envelope.frame for envelope in frames),
        key=lambda frame: frame.occurrence_id))
    if (type(ast) is not StreamingAST
            or not isinstance(source_instance_id, str) or not source_instance_id
            or len(ast.atoms) != len(visible)
            or tuple(atom.token for atom in ast.atoms) != expected_tokens
            or tuple(atom.index for atom in ast.atoms) != tuple(range(len(visible)))
            or any(frame.source_instance_id != source_instance_id
                   for frame in admitted_frames)
            or source_frame_roots(ast) != admitted_frames):
        _invalid("CONTEXT_SOURCE_LINEAGE_MISMATCH")


def require_semantic_authority(
        compiler_config: FrameCompilerConfig, task_scope: TaskScope,
        source_frontier: SourceFrontier,
        eligibility_policy: ContextPolicy, atlas_selection,
        feature_artifact_path, rederive_training_authority,
        semantic_context=None, released_manifest=None) -> AtlasFeatures:
    if (type(compiler_config) is not FrameCompilerConfig
            or compiler_config.approved is not None
            or compiler_config.task != task_scope
            or compiler_config.frontier != source_frontier
            or compiler_config.policy != eligibility_policy):
        _invalid("UPSTREAM_SEMANTIC_AUTHORITY_MISMATCH")
    if semantic_context is None:
        atlas_features = rederive_training_authority(
            compiler_config, atlas_selection, feature_artifact_path)
    else:
        from .factory_training_context import _require_materialized_manifest
        manifest = _require_materialized_manifest(
            semantic_context, released_manifest)
        if semantic_context.selection != atlas_selection:
            _invalid("UPSTREAM_SEMANTIC_AUTHORITY_MISMATCH")
        atlas_features = semantic_context.features
        schemas, roles = dict(atlas_features.schema_map), dict(atlas_features.role_map)
        canonical = tuple(body.parse() for body in manifest.bodies)
        if (compiler_config.schema_map != manifest.schema_map
                or compiler_config.schemas != canonical
                or any(schema.schema_id not in schemas
                       for schema in compiler_config.schemas)
                or any(role.role_id not in roles
                       for schema in compiler_config.schemas for role in schema.roles)):
            _invalid("UPSTREAM_SEMANTIC_AUTHORITY_MISMATCH")
    if (type(atlas_features) is not AtlasFeatures
            or atlas_features.semantic_release != task_scope.semantic_release):
        _invalid("UPSTREAM_SEMANTIC_AUTHORITY_MISMATCH")
    return atlas_features


def row_contexts(value, expected_type, count: int, reason: str):
    """Broadcast one authority context or require one exact context per row."""
    if type(value) is expected_type:
        return (value,) * count
    if (type(value) is tuple and len(value) == count
            and all(type(item) is expected_type for item in value)):
        return value
    _invalid(reason)


def source_features(
        projection: ApprovedContextProjection,
        atlas_features: AtlasFeatures, atlas_selection) -> tuple:
    result = []
    for envelope in projection.envelopes:
        frame = envelope.frame
        if type(frame) is not FrameInstance:
            continue
        for binding in frame.bindings:
            concepts = ((binding.concept,) if binding.concept is not None
                        else binding.alternatives)
            for concept in concepts:
                result.append(source_qualified_feature_row(
                    atlas_features, concept, binding.role_id, frame,
                    envelope.scope, atlas_selection,
                    invalid=lambda: _invalid(
                        "UPSTREAM_SEMANTIC_AUTHORITY_MISMATCH")))
    return tuple(result)


__all__ = (
    "require_semantic_authority", "require_source_lineage", "row_contexts",
    "source_features", "require_source_inventory",
)
