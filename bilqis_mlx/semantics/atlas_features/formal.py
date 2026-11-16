"""Re-derive admitted formal types from independent A01 and A03 source pins."""
from dataclasses import replace

from bilqis_mlx.errors import BilqisError, ErrorBus, SCHOOL

from ..atlas.snapshot import AtlasArtifactSelection, load_pinned_atlas_snapshot
from ..frame_adapters.registry import source_frame_strategy
from ..frame_adapters.public_formal_sources import source_graph_for_adapter
from ..frame_schema import FrameInstance, _formal_source_types
from ..released_frame_schemas import lookup_source_pinned_frame_schema
from .common import _factor_overflow

def source_family_for_adapter(adapter_id: str) -> str:
    """Return the A06-owned released-schema family for one source adapter."""
    try:
        family = source_frame_strategy(adapter_id).source_family
    except BilqisError:
        family = None
    if family is None:
        ErrorBus.Raise(SCHOOL.MODEL_TOPOLOGY.INVALID)
    return family


def _reject(invalid):
    invalid()
    ErrorBus.Raise(SCHOOL.MODEL_TOPOLOGY.INVALID)


def source_qualified_feature_row(features, concept, role_id, frame, scope, selection, *, invalid):
    """Preserve A06 factors while deriving formal types from the pinned source."""
    admitted = next((item for item in features.concepts if item.semantic_id == concept.semantic_id), None)
    if admitted is None or admitted.source_status != 'ADMITTED_FORMAL_ABI_UNTYPED':
        return features.features_for(concept, role_id, frame.frame_schema_id, scope)
    row = features.features_for(concept.semantic_id, role_id, frame.frame_schema_id, scope)
    if (type(selection) is not AtlasArtifactSelection or type(frame) is not FrameInstance
            or concept.semantic_release != features.semantic_release or concept.abi_index != row.abi_index):
        _reject(invalid)
    selection.__post_init__()
    if (selection.bundle_id != features.atlas_bundle_id or selection.release_sha256 != features.semantic_release
            or selection.source_bundle_id != features.source_bundle_id):
        _reject(invalid)
    reference = concept.source_reference
    if not isinstance(reference, str) or ':' not in reference:
        _reject(invalid)
    adapter_id, _ = reference.split(':', 1)
    family = source_family_for_adapter(adapter_id)
    snapshot = load_pinned_atlas_snapshot(selection)
    _, graph = source_graph_for_adapter(adapter_id)
    types = _formal_source_types(snapshot, concept, graph, adapter_id, frame.source_span, role_id)
    schema, _ = lookup_source_pinned_frame_schema(frame.frame_schema_id, frame.frame_schema_revision,
                                                    source_family=family, atlas_selection=selection)
    role = next((item for item in schema.roles if item.role_id == role_id), None)
    if role is None or concept.type_ids != types or not set(types).issubset(set(role.allowed_type_ids)):
        _reject(invalid)
    type_map = dict(features.type_map)
    type_rows = tuple(type_map.get(identifier, 0) for identifier in types)
    return replace(row, type_ids=types, type_rows=type_rows,
                   type_overflow=tuple((identifier, _factor_overflow('type', identifier))
                                       for identifier, index in zip(types, type_rows) if index == 0))
