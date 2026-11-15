"""B05 depth selection math and execution-owned producer qualification."""
from dataclasses import dataclass
from typing import Mapping

import mlx.core as mx

from bilqis_mlx.learning.frame_embeddings import (
    EmptyFrameFactorTerms, FrameFactorTerms, compose_factor_features,
)
from bilqis_mlx.learning.frame_encoder import FrameEncoding
from .depth_contracts import (
    WIDTH, INNER, MIN_COMPLETED_GROUPS, MAX_COMPLETED_GROUPS, FRAME_RANK,
    BATCH_POSITION_AXES, PARAMETER_SHAPES, DIAGNOSTICS_SCHEMA, SOURCE_ORDER,
    DepthParameterView, _DepthFeatureValues, DepthFrameFeatures, DepthSummary,
    _invalid,
)
from .model_topology_v2 import ModelTopologySpecV2


def _validate(current, summaries, features, params) -> None:
    if (not isinstance(current, mx.array) or current.ndim != FRAME_RANK
            or current.shape[-1] != WIDTH or current.dtype != mx.float32
            or min(current.shape[:BATCH_POSITION_AXES]) < 1
            or not isinstance(summaries, tuple)
            or not MIN_COMPLETED_GROUPS + 1 <= len(summaries) <= MAX_COMPLETED_GROUPS + 1
            or any(type(value) is not DepthSummary
                   or not isinstance(value.hidden, mx.array)
                   or value.hidden.shape != current.shape
                   or value.hidden.dtype != mx.float32 for value in summaries)
            or type(features) is not _DepthFeatureValues
            or len(summaries) != features.boundary_group + 1
            or tuple(value.source_id for value in summaries) != SOURCE_ORDER[:len(summaries)]
            or not isinstance(features.frame_seed, mx.array)
            or features.frame_seed.shape != current.shape
            or features.frame_seed.dtype != mx.float32
            or not isinstance(features.type_role, mx.array)
            or features.type_role.shape != current.shape
            or features.type_role.dtype != mx.float32
            or not isinstance(params, Mapping) or set(params) != set(PARAMETER_SHAPES)):
        _invalid()
    for name, shape in PARAMETER_SHAPES.items():
        value = params[name]
        if (not isinstance(value, mx.array) or value.shape != shape
                or value.dtype != mx.float32):
            _invalid()
    finite = tuple(mx.all(mx.isfinite(value)) for value in (
        current, features.frame_seed, features.type_role,
        *(item.hidden for item in summaries), *params.values(),
    ))
    mx.eval(*finite)
    if not all(bool(flag) for flag in finite):
        _invalid()


def _rms_norm(values: mx.array, gamma: mx.array) -> mx.array:
    epsilon = ModelTopologySpecV2.rms_norm_epsilon
    return values * mx.rsqrt(
        mx.mean(values * values, axis=-1, keepdims=True) + epsilon) * gamma


def _depth_components(current, summaries, features, params):
    _validate(current, summaries, features, params)
    q = _rms_norm(current + features.frame_seed, params["norm"]) @ params["query"].T
    keys = mx.stack([
        _rms_norm(summary.hidden + features.type_role, params["norm"]) @ params["key"].T
        for summary in summaries
    ], axis=-2)
    values = mx.stack([summary.hidden @ params["value"].T for summary in summaries], axis=-2)
    scores = mx.sum(q[:, :, None, :] * keys, axis=-1) * (INNER ** -0.5)
    alpha = mx.softmax(scores, axis=-1)
    mix = mx.sum(alpha[:, :, :, None] * values, axis=-2)
    gate_logits = (
        mx.sum(params["gate_vector"] * _rms_norm(current, params["norm"]),
               axis=-1, keepdims=True) + params["gate_bias"])
    gate = 0.1 * mx.sigmoid(gate_logits)
    return current + gate * (mix @ params["output"].T), alpha, gate


@dataclass(frozen=True)
class DepthSelectionDiagnostics:
    output: mx.array
    alpha: mx.array
    gate: mx.array
    schema_version: str = DIAGNOSTICS_SCHEMA


def _numerical_depth_select(current, summaries, frame_features, params):
    return _numerical_depth_select_with_diagnostics(
        current, summaries, frame_features, params).output


def _numerical_depth_select_with_diagnostics(
    current, summaries, frame_features, params,
) -> DepthSelectionDiagnostics:
    if (type(params) is not DepthParameterView
            or type(frame_features) is not DepthFrameFeatures
            or params.boundary_group != frame_features.boundary_group
            or not isinstance(current, mx.array)
            or current.ndim != FRAME_RANK
            or current.shape[:BATCH_POSITION_AXES]
            != (len(frame_features.requests), len(frame_features.requests[0]))
            or type(summaries) is not tuple or not summaries
            or type(summaries[0]) is not DepthSummary):
        _invalid()
    type_role = mx.stack([mx.stack([
        mx.mean(compose_factor_features(
            params._feature_parameters, (members,), frame_features.features,
            extents=params._extents, atlas_selection=frame_features.atlas_selection).type_role[0], axis=0)
        for members in row]) for row in frame_features.requests])
    numerical = _DepthFeatureValues(
        summaries[0].hidden, type_role, frame_features.features.semantic_release,
        frame_features.features.digest, frame_features.boundary_group)
    output, alpha, gate = _depth_components(current, summaries, numerical, params)
    return DepthSelectionDiagnostics(output, alpha, gate)


def _producer_summaries(producer, boundary_group, params):
    from bilqis_mlx.learning.source_atoms.backbone import _SourceBackboneProducerSession
    if (type(producer) is not _SourceBackboneProducerSession
            or type(params) is not DepthParameterView):
        _invalid()
    receipts = _SourceBackboneProducerSession._validated_receipts(
        producer, boundary_group)
    # One source selection has one sealed parameter view. Rehashing the entire
    # model for each receipt adds no verification strength within this call.
    parameter_tree_digest = params.parameter_tree_digest
    generation_digest = params.generation_digest
    for index, item in enumerate(receipts):
        if (item.source_id != SOURCE_ORDER[index]
                or (index and item.predecessor_receipt_digest != receipts[index - 1].receipt_digest)
                or item.source_handoff_digest != receipts[0].source_handoff_digest
                or item.topology_digest != receipts[0].topology_digest
                or item.generation_digest != receipts[0].generation_digest
                or item.parameter_tree_digest != receipts[0].parameter_tree_digest
                or item.prefix_digest != receipts[0].prefix_digest
                or item.parameter_tree_digest != parameter_tree_digest
                or item.generation_digest != generation_digest):
            _invalid()
    summaries = tuple(DepthSummary(
        item.source_id, item.completed_layer,
        item.hidden if index == 0 else _rms_norm(item.hidden, params["norm"]),
    ) for index, item in enumerate(receipts))
    return summaries, receipts


def depth_select(producer, frame_features, params):
    return depth_select_with_diagnostics(
        producer, frame_features, params).output


def depth_select_with_diagnostics(producer, frame_features, params):
    if (type(frame_features) is not DepthFrameFeatures
            or type(params) is not DepthParameterView):
        _invalid()
    summaries, receipts = _producer_summaries(
        producer, frame_features.boundary_group, params)
    current = receipts[frame_features.boundary_group].hidden
    return _numerical_depth_select_with_diagnostics(
        current, summaries, frame_features, params)


def source_depth_select_with_diagnostics(producer, params):
    """Select depth only from the B11 producer's executed source factors."""
    from bilqis_mlx.learning.source_atoms.backbone import _SourceBackboneProducerSession
    if (type(producer) is not _SourceBackboneProducerSession
            or type(params) is not DepthParameterView
            or type(producer._encoded) is not FrameEncoding):
        _invalid()
    summaries, receipts = _producer_summaries(
        producer, params.boundary_group, params)
    encoded = producer._encoded
    if (encoded.global_seeds.shape != receipts[0].hidden.shape
            or len(encoded.features) != encoded.global_seeds.shape[0]
            or any(not 0 < len(row) <= encoded.global_seeds.shape[1]
                   for row in encoded.features)):
        _invalid()
    rows = []
    for row in encoded.features:
        values = []
        padded = row + (None,) * (encoded.global_seeds.shape[1] - len(row))
        for factor in padded:
            if factor is None:
                values.append(mx.zeros((WIDTH,), dtype=mx.float32))
            elif type(factor) in (FrameFactorTerms, EmptyFrameFactorTerms):
                if (factor.feature_digest != producer._compiled.features.digest
                        or factor.semantic_release
                        != producer._compiled.features.semantic_release
                        or factor.type_role768.shape != (WIDTH,)
                        or factor.type_role768.dtype != mx.float32):
                    _invalid()
                values.append(factor.type_role768)
            else:
                _invalid()
        rows.append(mx.stack(tuple(values)))
    numerical = _DepthFeatureValues(
        encoded.global_seeds, mx.stack(tuple(rows)),
        producer._compiled.features.semantic_release,
        producer._compiled.features.digest, params.boundary_group)
    output, alpha, gate = _depth_components(
        receipts[params.boundary_group].hidden, summaries, numerical, params)
    return DepthSelectionDiagnostics(output, alpha, gate)


def source_depth_select(producer, params):
    return source_depth_select_with_diagnostics(producer, params).output


DepthSelectionDiagnostics.__module__ = "bilqis_mlx.runtime.block_attnres"
depth_select.__module__ = "bilqis_mlx.runtime.block_attnres"
depth_select_with_diagnostics.__module__ = "bilqis_mlx.runtime.block_attnres"
source_depth_select.__module__ = "bilqis_mlx.runtime.block_attnres"
source_depth_select_with_diagnostics.__module__ = "bilqis_mlx.runtime.block_attnres"
