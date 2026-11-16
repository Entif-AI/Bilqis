"""Source-context helpers for the C02 Factory training composition seam."""
from __future__ import annotations

from bilqis_mlx.semantics.context_eligibility import (
    PUBLIC_FORMAL, ContextPolicy, SourceFrontier, TaskScope,
)
from bilqis_mlx.semantics.frame_schema import FrameInstance, FrameTree


def _source_frame_inventory_materialized(
        source_context, row, atlas_selection, snapshot, manifest):
    """Derive source inventory from already-authenticated semantic material."""
    from bilqis_mlx.semantics.frame_adapters import bind_registered_source_row
    from bilqis_mlx.semantics.frame_schema import SourceSpan
    from bilqis_mlx.source_adapters.atoms.authority import canonical_graph_for

    adapter = source_context.source_registry.resolve_owner(
        row.get("generator"))
    graph = canonical_graph_for(row.get('generator'), source_context.source_root)
    end = len(row['tokens'])
    if ((snapshot.release_sha256, snapshot.bundle_id, snapshot.source_bundle_id)
          != (atlas_selection.release_sha256, atlas_selection.bundle_id,
              atlas_selection.source_bundle_id)):
        from .atlas_training_contracts import _invalid
        _invalid("CONTEXT_SOURCE_LINEAGE_MISMATCH")
    tree = bind_registered_source_row(
        adapter, row, snapshot,
        source_root=source_context.source_root, graph=graph,
        source_span=SourceSpan(0, end), causal_prefix_end=end,
        course=source_context.release.curriculum)
    if ((manifest.semantic_release, manifest.atlas_bundle_id, manifest.source_bundle_id)
          != (snapshot.release_sha256, snapshot.bundle_id, snapshot.source_bundle_id)):
        from .atlas_training_contracts import _invalid
        _invalid("CONTEXT_SOURCE_LINEAGE_MISMATCH")
    schemas = frozenset(body.schema_id for body in manifest.bodies)
    return tree.root.source_instance_id, ((tree,) if schemas_cover_tree(tree, schemas) else ())


def _source_frame_inventory_verified(
        source_context, row, atlas_selection, snapshot, manifest):
    """Derive inventory after SourceBatchAuthority already proved provider check."""
    from bilqis_mlx.semantics.frame_adapters.registry import _bind_verified_source_row
    from bilqis_mlx.semantics.frame_schema import SourceSpan
    from bilqis_mlx.source_adapters.atoms.authority import canonical_graph_for

    adapter = source_context.source_registry.resolve_owner(
        row.get("generator"))
    graph = canonical_graph_for(row.get('generator'), source_context.source_root)
    end = len(row['tokens'])
    if ((snapshot.release_sha256, snapshot.bundle_id, snapshot.source_bundle_id)
          != (atlas_selection.release_sha256, atlas_selection.bundle_id,
              atlas_selection.source_bundle_id)):
        from .atlas_training_contracts import _invalid
        _invalid("CONTEXT_SOURCE_LINEAGE_MISMATCH")
    tree = _bind_verified_source_row(
        adapter, row, snapshot, graph=graph, source_span=SourceSpan(0, end),
        causal_prefix_end=end)
    if ((manifest.semantic_release, manifest.atlas_bundle_id, manifest.source_bundle_id)
          != (snapshot.release_sha256, snapshot.bundle_id, snapshot.source_bundle_id)):
        from .atlas_training_contracts import _invalid
        _invalid("CONTEXT_SOURCE_LINEAGE_MISMATCH")
    schemas = frozenset(body.schema_id for body in manifest.bodies)
    return tree.root.source_instance_id, ((tree,) if schemas_cover_tree(tree, schemas) else ())


def _require_materialized_manifest(semantic_context, manifest):
    from bilqis_mlx.runtime.bamf_bundle import (
        AuthenticatedCandidateFeatureContext, AuthenticatedGenerationFeatureContext,
    )
    from bilqis_mlx.semantics.released_frame_schemas import _source_pins
    if type(semantic_context) not in (
            AuthenticatedCandidateFeatureContext,
            AuthenticatedGenerationFeatureContext):
        from .atlas_training_contracts import _invalid
        _invalid("UPSTREAM_SEMANTIC_AUTHORITY_MISMATCH")
    semantic_context.__post_init__()
    manifest.__post_init__()
    snapshot = semantic_context.snapshot
    matches = tuple(entry for entry in _source_pins()
                    if entry["semantic_release"] == manifest.semantic_release
                    and entry["atlas_bundle_id"] == manifest.atlas_bundle_id
                    and entry["source_bundle_id"] == manifest.source_bundle_id
                    and entry["schema_manifest_sha256"] == manifest.digest
                    and entry["schema_map_sha256"] == manifest.schema_map.digest)
    if (len(matches) != 1
            or (manifest.semantic_release, manifest.atlas_bundle_id,
                manifest.source_bundle_id)
            != (snapshot.release_sha256, snapshot.bundle_id,
                snapshot.source_bundle_id)):
        from .atlas_training_contracts import _invalid
        _invalid("UPSTREAM_SEMANTIC_AUTHORITY_MISMATCH")
    return manifest


def _source_frame_inventory_from_context(
        source_context, row, semantic_context, manifest):
    manifest = _require_materialized_manifest(semantic_context, manifest)
    return _source_frame_inventory_materialized(
        source_context, row, semantic_context.selection,
        semantic_context.snapshot, manifest)


def _source_frame_inventory_from_verified_context(
        source_context, row, semantic_context, manifest):
    manifest = _require_materialized_manifest(semantic_context, manifest)
    return _source_frame_inventory_verified(
        source_context, row, semantic_context.selection,
        semantic_context.snapshot, manifest)


def source_frame_inventory(source_context, row, atlas_selection):
    """Cold source-owner replay when no authenticated semantic context is bound."""
    from bilqis_mlx.semantics.atlas.snapshot import load_pinned_atlas_snapshot
    from bilqis_mlx.semantics.atlas_features.formal import source_family_for_adapter
    from bilqis_mlx.semantics.released_frame_schemas import _load_pinned_released_frame_schemas

    adapter = source_context.source_registry.resolve_owner(
        row.get("generator"))
    manifest = _load_pinned_released_frame_schemas(
        source_family_for_adapter(adapter.descriptor.adapter_id), atlas_selection).manifest
    snapshot = load_pinned_atlas_snapshot(atlas_selection)
    return _source_frame_inventory_materialized(
        source_context, row, atlas_selection, snapshot, manifest)


def training_answer_plan(prefix, release, kind, generation_binding):
    head = next(item for item in release.answer_heads if item.kind == kind)
    return {
        "modalityID": head.modality_id,
        "input_prefix_end": prefix.visible_end,
        "decisions": [
            {"id": "value", "roleID": "answer", "occurrence": 0,
             "kind": "VALUE", "legalValues": list(head.values),
             "depends_on": []},
            {"id": "end", "roleID": "end", "occurrence": 0,
             "kind": "CONTROL", "legalValues": ["END_FRAME"],
             "depends_on": ["value"]},
        ],
        "allowedOutputSchema": "factory-training/v1",
        "maximum_decisions": 2,
        "generation_binding": generation_binding,
    }


def public_training_context(release: str, capability: str, prefix_end: int):
    task = TaskScope(
        "bamf-factory-trainer", "bamf-factory", "TRAINING", release,
        "LOCAL", capability, 0, 0, prefix_end)
    policy = ContextPolicy(
        "bamf-factory-public-formal/v1", 1, 1,
        ("TRAINING",), (PUBLIC_FORMAL,), ("LOCAL",), (capability,),
        (PUBLIC_FORMAL,), ((PUBLIC_FORMAL, PUBLIC_FORMAL),),
        tuple((PUBLIC_FORMAL,) * count for count in range(3, 25)))
    return task, SourceFrontier(1, 1, ()), policy


def schemas_cover_tree(tree: FrameTree, schema_ids: frozenset[str]) -> bool:
    root = tree.root
    return ((isinstance(root, FrameInstance)
             and root.frame_schema_id in schema_ids)
            and all(schemas_cover_tree(child, schema_ids) for child in tree.children))


__all__ = (
    "public_training_context", "schemas_cover_tree", "training_answer_plan",
    "source_frame_inventory",
)
