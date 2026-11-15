"""BAMF embedding frame factors owner."""
from __future__ import annotations
from dataclasses import dataclass
from typing import Mapping
import mlx.core as mx
from bilqis_mlx.runtime.model_topology_v2 import FEATURE_NONE_ROW, GenerationExtents
from bilqis_mlx.semantics.atlas_features import AtlasFeatures, _factor_overflow
from bilqis_mlx.semantics.atlas.snapshot import AtlasArtifactSelection
from bilqis_mlx.semantics.context_eligibility import ApprovedContextProjection
from bilqis_mlx.semantics.frame_schema import FrameInstance
from .common import FactorGate, _invalid
from .requests import ChildFrameRequest, FeatureRequest, FrameConstituentRequest
from .composition import (
    _factor_vector, _released_factor_terms, _source_qualified_feature_row,
    _validate_feature_parameters,
)


def validate_frame_members(
    requests: tuple[FrameConstituentRequest, ...],
) -> FrameInstance:
    """Require every source binding once, without casting child frames to concepts."""
    if (type(requests) is not tuple or not requests or
            any(type(item) not in (FeatureRequest, ChildFrameRequest)
                for item in requests)):
        _invalid()
    first = requests[0]
    frame = first.projection.frame(first.frame_handle)
    if (type(frame) is not FrameInstance or
            tuple(item.local_slot for item in requests) != tuple(range(len(frame.bindings))) or
            any((item.projection.digest, item.frame_handle) !=
                (first.projection.digest, first.frame_handle) for item in requests)):
        _invalid()
    for item, binding in zip(requests, frame.bindings):
        if (item.role_id != binding.role_id
                or (type(item) is FeatureRequest)
                != (binding.concept is not None)):
            _invalid()
        constructor = (
            FeatureRequest if type(item) is FeatureRequest
            else ChildFrameRequest)
        if item != constructor.from_context(
                item.projection, item.frame_handle, item.member_handle):
            _invalid()
    return frame

@dataclass(frozen=True)
class FrameFactorTerms:
    """Raw frame-summary factors and shared depth features with source provenance."""

    schema128: mx.array
    mean_role128: mx.array
    type_role768: mx.array
    requests: tuple[FrameConstituentRequest, ...]
    feature_digest: str
    semantic_release: str
    schema_version: str = "bilqis.mlx.frame-factor-terms/v1"

def _child_categorical_factors(parameters, request, features):
    """Typed child-frame factors; there is no invented semantic or graph row."""
    types = dict(features.type_map)
    roles = dict(features.role_map)
    schemas = dict(features.schema_map)
    source = next((
        envelope for envelope in request.projection.envelopes
        if envelope.frame_handle == request.frame_handle), None)
    if (request.role_id not in roles or request.schema_id not in schemas
            or source is None
            or features.semantic_release != source.semantic_release):
        _invalid()
    type_vectors = tuple(_factor_vector(
        parameters["features.type"], types.get(type_id, 0),
        _factor_overflow("type", type_id)
        if types.get(type_id, 0) == 0 else None)
        for type_id in request.child.type_ids)
    type_mean = mx.mean(mx.stack(type_vectors), axis=0)
    role_row = roles[request.role_id]
    role = _factor_vector(
        parameters["features.role"], role_row,
        _factor_overflow("role", request.role_id)
        if role_row == 0 and request.role_id != "UNKNOWN" else None)
    schema_row = schemas[request.schema_id]
    schema = _factor_vector(
        parameters["features.schema"], schema_row,
        _factor_overflow("schema", request.schema_id)
        if schema_row == 0 and request.schema_id != "UNKNOWN" else None)
    return schema, role, type_mean

def _child_factor_terms(parameters, request, features):
    schema, role, type_mean = _child_categorical_factors(parameters, request, features)
    gates = mx.sigmoid(parameters["features.gates"])
    type_role = (
        gates[FactorGate.TYPE]
        * (type_mean @ parameters["features.project_type"].T)
        + gates[FactorGate.ROLE]
        * (role @ parameters["features.project_role"].T))
    return schema, role, type_role

def child_frame_source_context(
    parameters: Mapping[str, mx.array],
    request: ChildFrameRequest,
    features: AtlasFeatures,
    *,
    extents: GenerationExtents,
) -> mx.array:
    """Typed child factors plus the exact parent occurrence slot; no ABI lookup."""
    if type(request) is not ChildFrameRequest:
        _invalid()
    request.__post_init__()
    _validate_feature_parameters(parameters, features, extents)
    type_role = _child_factor_terms(parameters, request, features)[2]
    slot = (parameters["features.local_slot"][request.local_slot]
            if request.local_slot < parameters["features.local_slot"].shape[0]
            else _sinusoid_768(request.local_slot))
    return type_role + slot

def frame_factor_terms(
    parameters: Mapping[str, mx.array],
    requests: tuple[FrameConstituentRequest, ...],
    features: AtlasFeatures, *, extents: GenerationExtents,
    atlas_selection: AtlasArtifactSelection | None = None,
    source_execution_authority=None,
) -> FrameFactorTerms:
    """Gather actual A06 factors for concepts and typed child closures."""
    validate_frame_members(requests)
    _validate_feature_parameters(parameters, features, extents)
    values = []
    for request in requests:
        if type(request) is ChildFrameRequest:
            values.append(_child_factor_terms(parameters, request, features))
            continue
        row = _source_qualified_feature_row(
            features, request, atlas_selection, source_execution_authority)
        terms = _released_factor_terms(parameters, row)
        values.append((
            _factor_vector(
                parameters["features.schema"], row.schema_row,
                row.schema_overflow),
            _factor_vector(
                parameters["features.role"], row.role_row,
                row.role_overflow),
            terms[FactorGate.TYPE] + terms[FactorGate.ROLE]))
    return FrameFactorTerms(
        values[0][0],
        mx.mean(mx.stack([item[1] for item in values]), axis=0),
        mx.mean(mx.stack([item[2] for item in values]), axis=0),
        requests, features.digest, features.semantic_release)

@dataclass(frozen=True)
class EmptyFrameFactorTerms:
    """Source-bound empty factors; legal cardinality is the compiler's proof."""

    schema128: mx.array
    mean_role128: mx.array
    type_role768: mx.array
    projection: ApprovedContextProjection
    frame_handle: str
    feature_digest: str
    semantic_release: str
    requests: tuple[FeatureRequest, ...] = ()
    schema_version: str = "bilqis.mlx.empty-frame-factor-terms/v1"

def empty_frame_factor_terms(parameters: Mapping[str, mx.array], projection: ApprovedContextProjection,
                             frame_handle: str, features: AtlasFeatures, *,
                             extents: GenerationExtents) -> EmptyFrameFactorTerms:
    """Read raw schema and explicit NONE factors from one approved empty frame."""
    _validate_feature_parameters(parameters, features, extents)
    if type(projection) is not ApprovedContextProjection:
        _invalid()
    frame = projection.frame(frame_handle)
    envelope = next(item for item in projection.envelopes if item.frame_handle == frame_handle)
    if (type(frame) is not FrameInstance or frame.bindings or envelope.members or
            envelope.semantic_release != features.semantic_release or
            frame.frame_schema_id not in dict(features.schema_map)):
        _invalid()
    schema_row = dict(features.schema_map)[frame.frame_schema_id]
    overflow = (_factor_overflow("schema", frame.frame_schema_id)
                if schema_row == 0 and frame.frame_schema_id != "UNKNOWN" else None)
    schema = _factor_vector(parameters["features.schema"], schema_row, overflow)
    role = parameters["features.role"][FEATURE_NONE_ROW]
    gates = mx.sigmoid(parameters["features.gates"])
    type_role = (gates[FactorGate.TYPE] * (parameters["features.type"][FEATURE_NONE_ROW] @
                                         parameters["features.project_type"].T) +
                 gates[FactorGate.ROLE] * (role @ parameters["features.project_role"].T))
    return EmptyFrameFactorTerms(schema, role, type_role, projection, frame_handle,
                                 features.digest, features.semantic_release)
