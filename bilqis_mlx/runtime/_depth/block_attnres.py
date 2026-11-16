"""Shared depth selection with recomputed source-member factor features.

The public feature interface reads approved A13 coordinates and actual A06/B01
factors. Trusted backbone-summary capture remains an assembly qualification gate.
"""
from __future__ import annotations

from dataclasses import dataclass, field
import re
from types import MappingProxyType
from typing import Callable, Mapping

import mlx.core as mx
from bilqis_mlx.runtime.autodiff_trace import host_tensor_validation_enabled

from bilqis_mlx.errors import ErrorBus, SCHOOL
from bilqis_mlx.learning.frame_embeddings import FeatureRequest, compose_factor_features
from bilqis_mlx.learning.atlas_plasticity import AdapterParameters, adapter_forward
from bilqis_mlx.semantics.atlas_features import AtlasFeatures
from bilqis_mlx.runtime.backbone_identity import tensor_content_digest
from .model_topology_v2 import (
    GenerationExtents, ModelTopologySpecV2, expected_bamf_shapes,
    validate_bamf_parameters,
)


from .depth_contracts import (
    WIDTH, INNER, MIN_COMPLETED_GROUPS, MAX_COMPLETED_GROUPS, FRAME_RANK,
    BATCH_POSITION_AXES, PARAMETER_SHAPES, FEATURES_SCHEMA, RELEASED_FEATURES_SCHEMA,
    SUMMARY_SCHEMA, DIAGNOSTICS_SCHEMA, PARAMETER_VIEW_SCHEMA, _SHA, _VIEW_SEAL,
    SOURCE_ORDER, COMPLETED_LAYERS, _invalid, _depth_names, DepthParameterView,
    depth_parameter_view, _DepthFeatureValues, DepthFrameFeatures, DepthSummary,
)


from .depth_selection import (
    DepthSelectionDiagnostics, _depth_components, _numerical_depth_select,
    _numerical_depth_select_with_diagnostics, _rms_norm, depth_select,
    depth_select_with_diagnostics, source_depth_select,
    source_depth_select_with_diagnostics,
)


@dataclass(frozen=True)
class _NumericalGroupBoundary:
    """Private assembly proof; not a B08 source-authorized motif read."""

    captured: DepthSummary
    selected: mx.array
    adapted: mx.array
    alpha: mx.array
    gate: mx.array


def _group_boundary_numerical(
    current: mx.array, previous: tuple[DepthSummary, ...],
    features: _DepthFeatureValues, depth_params: Mapping[str, mx.array],
    adapter: AdapterParameters,
    *, second_motif_read: Callable[[mx.array], mx.array] | None = None,
) -> _NumericalGroupBoundary:
    """Prove B05 boundary ordering without granting a production motif reader.

    At group one, the caller-supplied private numerical motif read runs after
    layer four but before g1 is captured. At every group, the selector sees
    only h0 and already completed groups; the matching rank-eight adapter
    runs *after* selection. B08/B11 must later qualify the actual source
    read and backbone summary origin before this sequence is published.
    """
    if (type(features) is not _DepthFeatureValues
            or type(adapter) is not AdapterParameters
            or type(previous) is not tuple
            or len(previous) != features.boundary_group
            or adapter.group_index != features.boundary_group - 1
            or (features.boundary_group == 1) != (second_motif_read is not None)
            or (second_motif_read is not None and not callable(second_motif_read))
            or not isinstance(current, mx.array)
            or current.ndim != FRAME_RANK
            or current.shape[-1] != WIDTH
            or current.dtype != mx.float32
            or not isinstance(depth_params, Mapping)
            or "norm" not in depth_params
            or not isinstance(depth_params["norm"], mx.array)
            or depth_params["norm"].shape != (WIDTH,)
            or depth_params["norm"].dtype != mx.float32
            or (host_tensor_validation_enabled()
                and not bool(mx.all(mx.isfinite(current))))):
        _invalid()
    post_motif = (second_motif_read(current)
                  if second_motif_read is not None else current)
    if (not isinstance(post_motif, mx.array)
            or post_motif.shape != current.shape
            or post_motif.dtype != mx.float32):
        _invalid()
    group = features.boundary_group
    captured = DepthSummary(
        SOURCE_ORDER[group], COMPLETED_LAYERS[group],
        _rms_norm(post_motif, depth_params["norm"]))
    selected, alpha, gate = _depth_components(
        post_motif, (*previous, captured), features, depth_params)
    adapted = adapter_forward(selected, adapter)
    return _NumericalGroupBoundary(captured, selected, adapted, alpha, gate)
