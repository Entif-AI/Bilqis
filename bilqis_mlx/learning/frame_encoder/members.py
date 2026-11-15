"""Source-bound member gathering for compiled frame closures."""
import mlx.core as mx
from bilqis_mlx.learning.frame_embeddings import (
    ChildFrameRequest, FeatureRequest, child_frame_source_context,
    frame_factor_terms,
)
from .contracts import _invalid
from .kernel import _encode_one


def encode_group(
    group, supplied, cursor, closure_outputs, compiled, parameters, *,
    atlas_selection=None, qualified_feature_rows=None,
):
    selected = []
    for request in group:
        if type(request) is FeatureRequest:
            if (cursor >= len(supplied)
                    or supplied[cursor].request != request):
                _invalid()
            selected.append(supplied[cursor].vector)
            cursor += 1
        elif type(request) is ChildFrameRequest:
            child_vector = closure_outputs.get(
                request.child_frame_handle)
            if child_vector is None:
                _invalid()
            selected.append(
                child_vector + child_frame_source_context(
                    parameters, request, compiled.features,
                    extents=compiled.extents))
        else:
            _invalid()
    matrix = mx.stack(selected)
    factor = frame_factor_terms(
        parameters, group, compiled.features,
        extents=compiled.extents, atlas_selection=atlas_selection,
        qualified_feature_rows=qualified_feature_rows)
    seed = _encode_one(matrix, factor, parameters)
    return seed, matrix, factor, cursor
