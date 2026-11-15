"""Source-bound raw categorical means for the B08 motif gate."""
from dataclasses import dataclass
from typing import Mapping

import mlx.core as mx
from bilqis_mlx.runtime.autodiff_trace import host_tensor_validation_enabled

from bilqis_mlx.runtime.model_topology_v2 import FEATURE_NONE_ROW, GenerationExtents
from bilqis_mlx.semantics.atlas_features import AtlasFeatures
from bilqis_mlx.semantics.atlas.snapshot import AtlasArtifactSelection
from bilqis_mlx.semantics.context_eligibility import ApprovedContextProjection
from bilqis_mlx.semantics.frame_schema import FrameInstance
from .common import _invalid
from .composition import (
    _released_categorical_factors, _source_qualified_feature_row,
    _validate_feature_parameters,
)
from .frame_factors import (
    _child_categorical_factors, empty_frame_factor_terms, validate_frame_members,
)
from .requests import ChildFrameRequest, FeatureRequest


@dataclass(frozen=True)
class MotifGateFeatures:
    """Computed data with source coordinates; not an admission credential."""

    vector128: mx.array
    frame_handle: str
    context_digest: str
    feature_digest: str
    semantic_release: str
    requests: tuple[FeatureRequest | ChildFrameRequest, ...]
    schema_version: str = "bilqis.mlx.motif-gate-features/v1"


def _categorical_factors(
        parameters, features, request, atlas_selection=None,
        source_execution_authority=None):
    if type(request) is ChildFrameRequest:
        schema, role, types = _child_categorical_factors(parameters, request, features)
        return types, role, schema
    row = _source_qualified_feature_row(
        features, request, atlas_selection, source_execution_authority)
    return _released_categorical_factors(parameters, row)


def _requests(projection, frame_handle, envelope):
    requests = []
    for binding in envelope.frame.bindings:
        member = next((item for item in envelope.members if item.key == binding.key), None)
        constructor = (FeatureRequest if binding.concept is not None
                       else ChildFrameRequest if binding.child_frame is not None else None)
        if member is None or constructor is None:
            _invalid()
        requests.append(constructor.from_context(
            projection, frame_handle, member.source_handle))
    result = tuple(requests)
    validate_frame_members(result)
    return result


def motif_gate_features(
    parameters: Mapping[str, mx.array], projection: ApprovedContextProjection,
    frame_handle: str, features: AtlasFeatures, *, extents: GenerationExtents,
    atlas_selection: AtlasArtifactSelection | None = None,
    source_execution_authority=None,
) -> MotifGateFeatures:
    """Mean member types, mean member roles and schema, before 768 projections.

    Consume the same validated B02 coordinates and categorical overflow rules.
    Empty legal frames use explicit NONE type/role rows. Atomic fallback has
    no frame gate. A13 eligibility and A03 schema authority remain upstream.
    """
    _validate_feature_parameters(parameters, features, extents)
    if type(projection) is not ApprovedContextProjection:
        _invalid()
    envelope = next((item for item in projection.envelopes
                     if item.frame_handle == frame_handle), None)
    if (envelope is None or type(envelope.frame) is not FrameInstance
            or envelope.semantic_release != features.semantic_release):
        _invalid()
    if envelope.frame.bindings:
        requests = _requests(projection, frame_handle, envelope)
        values = tuple(_categorical_factors(
                       parameters, features, request, atlas_selection,
                       source_execution_authority)
                       for request in requests)
        types, roles, schema = (
            mx.mean(mx.stack(tuple(value[index] for value in values)), axis=0)
            for index in range(3))
    else:
        terms = empty_frame_factor_terms(
            parameters, projection, frame_handle, features, extents=extents)
        requests = ()
        types = parameters["features.type"][FEATURE_NONE_ROW]
        roles, schema = terms.mean_role128, terms.schema128
    vector = (types + roles + schema) / 3
    if host_tensor_validation_enabled() and not bool(mx.all(mx.isfinite(vector))):
        _invalid()
    return MotifGateFeatures(vector, frame_handle, projection.digest,
                             features.digest, features.semantic_release, requests)
