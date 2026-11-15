"""BAMF embedding composition owner."""
from __future__ import annotations
from dataclasses import dataclass, replace
from typing import Mapping
import mlx.core as mx
import numpy as np
from bilqis_mlx.runtime.model_topology_v2 import FEATURE_NONE_ROW, GenerationExtents, ModelTopologySpecV2, expected_bamf_shapes
from bilqis_mlx.semantics.atlas_features import AtlasFeatures
from bilqis_mlx.semantics.atlas_features.formal import source_qualified_feature_row
from .common import COMPOSITION_SCHEMA, FactorGate, POSITION_BASE, WIDTH, _SINUSOID_PAIR_WIDTH, _invalid
from .requests import FeatureRequest


@dataclass(frozen=True)
class FactorComposition:
    """Differentiable values with recomputable release and request provenance."""

    type_role: mx.array
    all_factors: mx.array
    feature_digest: str
    semantic_release: str
    requests: tuple[tuple[FeatureRequest, ...], ...]
    schema_version: str = COMPOSITION_SCHEMA

def _factor_vector(table, row, overflow):
    value = table[row]
    return value if overflow is None else value + mx.array(overflow, dtype=mx.float32)

def _local_position(table, slot):
    if slot < table.shape[0]:
        return table[slot]
    frequencies = np.power(POSITION_BASE, -np.arange(0, WIDTH, _SINUSOID_PAIR_WIDTH) / WIDTH)
    angles = float(slot) * frequencies
    values = np.empty((WIDTH,), dtype=np.float32)
    values[0::_SINUSOID_PAIR_WIDTH] = np.sin(angles)
    values[1::_SINUSOID_PAIR_WIDTH] = np.cos(angles)
    return mx.array(values)

def _validate_feature_parameters(parameters, features, extents):
    if (not isinstance(parameters, Mapping) or type(features) is not AtlasFeatures or
            type(extents) is not GenerationExtents or extents.factor_map_digest != features.digest):
        _invalid()
    for item in expected_bamf_shapes(ModelTopologySpecV2(), extents):
        if item.name.startswith("features."):
            value = parameters.get(item.name)
            if not isinstance(value, mx.array) or value.shape != item.shape or value.dtype != mx.float32:
                _invalid()

def _validate_composer(parameters, requests, features, extents):
    _validate_feature_parameters(parameters, features, extents)
    if (type(requests) is not tuple or not requests or type(requests[0]) is not tuple or
            not requests[0] or any(type(row) is not tuple or len(row) != len(requests[0]) or
                                  any(type(item) is not FeatureRequest for item in row) for row in requests)):
        _invalid()

def _released_categorical_factors(parameters, row):
    overflow_types = dict(row.type_overflow)
    types = [_factor_vector(parameters["features.type"], index, overflow_types.get(type_id))
             for type_id, index in zip(row.type_ids, row.type_rows)]
    type_mean = mx.mean(mx.stack(types), axis=0) if types else parameters["features.type"][FEATURE_NONE_ROW]
    role = _factor_vector(parameters["features.role"], row.role_row, row.role_overflow)
    schema = _factor_vector(parameters["features.schema"], row.schema_row, row.schema_overflow)
    return type_mean, role, schema


def _source_qualified_feature_row(
        features, request, atlas_selection=None, qualified_feature_rows=None):
    if type(request) is not FeatureRequest:
        _invalid()
    request.__post_init__()
    if qualified_feature_rows is not None:
        if not isinstance(qualified_feature_rows, Mapping):
            _invalid()
        row = qualified_feature_rows.get(
            (request.frame_handle, request.member_handle))
        if (row is None
                or row.semantic_id != request.concept.semantic_id
                or row.abi_index != request.concept.abi_index
                or row.role_id != request.role_id
                or row.schema_id != request.schema_id
                or row.scope != request.scope):
            _invalid()
        return row
    frame = request.projection.frame(request.frame_handle)
    return source_qualified_feature_row(
        features, request.concept, request.role_id, frame, request.scope,
        atlas_selection, invalid=_invalid)


def _released_factor_terms(parameters, row):
    type_mean, role, schema = _released_categorical_factors(parameters, row)
    gates = mx.sigmoid(parameters["features.gates"])
    return (gates[FactorGate.TYPE] * (type_mean @ parameters["features.project_type"].T),
            gates[FactorGate.ROLE] * (role @ parameters["features.project_role"].T),
            gates[FactorGate.SCHEMA] * (schema @ parameters["features.project_schema"].T),
            gates[FactorGate.GRAPH] * (mx.array(row.graph64, dtype=mx.float32) @
                                      parameters["features.project_graph"].T))

def _compose_one(
        parameters, request, features, atlas_selection=None,
        qualified_feature_rows=None):
    row = _source_qualified_feature_row(
        features, request, atlas_selection, qualified_feature_rows)
    terms = _released_factor_terms(parameters, row)
    type_role = terms[FactorGate.TYPE] + terms[FactorGate.ROLE]
    factors = (type_role + terms[FactorGate.SCHEMA] + terms[FactorGate.GRAPH] +
               _local_position(parameters["features.local_slot"], request.local_slot))
    return type_role, factors

def compose_factor_features(
        parameters: Mapping[str, mx.array],
        requests: tuple[tuple[FeatureRequest, ...], ...],
        features: AtlasFeatures, *, extents: GenerationExtents,
        atlas_selection: AtlasArtifactSelection | None = None,
        qualified_feature_rows=None) -> FactorComposition:
    """Use actual A06 rows and shared B01 tables; never accept anonymous feature tensors.

    Each projected type/role/schema/graph term has its learned sigmoid gate.
    Categorical overflow is UNKNOWN plus the released exact-ID vector. Multiple
    types use their arithmetic mean. Extended local slots use a fixed base-10000
    alternating sine/cosine encoding, retaining role and occurrence separately.
    Identity-bank activation and model-generation admission remain upstream.
    """
    _validate_composer(parameters, requests, features, extents)
    composed = [[_compose_one(
        parameters, request, features, atlas_selection, qualified_feature_rows)
        for request in batch] for batch in requests]
    type_role = mx.stack([mx.stack([item[0] for item in batch]) for batch in composed])
    all_factors = mx.stack([mx.stack([item[1] for item in batch]) for batch in composed])
    return FactorComposition(type_role, all_factors, features.digest, features.semantic_release,
                             requests)
