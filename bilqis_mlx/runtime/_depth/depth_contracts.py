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

from bilqis_mlx.errors import ErrorBus, SCHOOL
from bilqis_mlx.learning.frame_embeddings import FeatureRequest, compose_factor_features
from bilqis_mlx.learning.atlas_plasticity import AdapterParameters, adapter_forward
from bilqis_mlx.semantics.atlas_features import AtlasFeatures
from bilqis_mlx.semantics.atlas.snapshot import AtlasArtifactSelection
from bilqis_mlx.runtime.backbone_identity import (
    bamf_parameter_tree_digest, execution_generation_digest,
    require_execution_generation_binding,
)
from .model_topology_v2 import (
    GenerationExtents, ModelTopologySpecV2, expected_bamf_shapes,
    validate_bamf_parameters,
)


WIDTH = ModelTopologySpecV2.width
INNER = 128
MIN_COMPLETED_GROUPS = 1
MAX_COMPLETED_GROUPS = ModelTopologySpecV2.depth_groups
FRAME_RANK = 3
BATCH_POSITION_AXES = 2
_SHA = re.compile(r"[0-9a-f]{64}\Z")
PARAMETER_SHAPES = MappingProxyType({
    "norm": (WIDTH,),
    "query": (INNER, WIDTH),
    "key": (INNER, WIDTH),
    "value": (INNER, WIDTH),
    "output": (WIDTH, INNER),
    "gate_vector": (WIDTH,),
    "gate_bias": (1,),
})
FEATURES_SCHEMA = "bilqis.mlx.depth-frame-features/v1"
RELEASED_FEATURES_SCHEMA = "bilqis.mlx.depth-frame-features/v2"
SUMMARY_SCHEMA = "bilqis.mlx.depth-summary/v1"
DIAGNOSTICS_SCHEMA = "bilqis.mlx.depth-diagnostics/v1"
PARAMETER_VIEW_SCHEMA = "bilqis.mlx.depth-parameter-view/v1"
_VIEW_SEAL = object()
SOURCE_ORDER = ("h0", "g1", "g2", "g3")
COMPLETED_LAYERS = (0, 4, 8, 12)


def _invalid() -> None:
    ErrorBus.Raise(SCHOOL.MODEL_TOPOLOGY.INVALID)


def _depth_names(boundary_group):
    return {"norm": "depth.norm", "query": "depth.query", "key": "depth.key",
            "value": "depth.value", "output": "depth.output",
            "gate_vector": f"depth.gate.{boundary_group - 1}.vector",
            "gate_bias": f"depth.gate.{boundary_group - 1}.bias"}


@dataclass(frozen=True)
class DepthParameterView(Mapping[str, mx.array]):
    """Sealed, immutable B01-validated references, not anonymous local weights."""

    _tensors: Mapping[str, mx.array]
    boundary_group: int
    _seal: object
    _full_parameters: Mapping[str, mx.array] | None = None
    _extents: GenerationExtents | None = None
    _execution_binding: object | None = field(default=None, repr=False, compare=False)
    _feature_parameters: Mapping[str, mx.array] = field(init=False, repr=False, compare=False)
    schema_version: str = PARAMETER_VIEW_SCHEMA

    def __post_init__(self) -> None:
        if (self._seal is not _VIEW_SEAL
                or self.schema_version != PARAMETER_VIEW_SCHEMA
                or type(self.boundary_group) is not int
                or not MIN_COMPLETED_GROUPS <= self.boundary_group <= MAX_COMPLETED_GROUPS
                or not isinstance(self._tensors, Mapping)
                or set(self._tensors) != set(PARAMETER_SHAPES)
                or not isinstance(self._full_parameters, Mapping)
                or type(self._extents) is not GenerationExtents):
            _invalid()
        validate_bamf_parameters(ModelTopologySpecV2(), self._extents, self._full_parameters)
        if self._execution_binding is not None:
            require_execution_generation_binding(
                self._execution_binding, self._full_parameters,
                spec=ModelTopologySpecV2(), extents=self._extents)
        if any(self._tensors[local] is not self._full_parameters[path]
               for local, path in _depth_names(self.boundary_group).items()):
            _invalid()
        object.__setattr__(self, "_tensors", MappingProxyType(dict(self._tensors)))
        object.__setattr__(self, "_full_parameters", MappingProxyType(dict(self._full_parameters)))
        object.__setattr__(self, "_feature_parameters", MappingProxyType({
            name: value for name, value in self._full_parameters.items() if name.startswith("features.")}))

    def __getitem__(self, name: str) -> mx.array:
        return self._tensors[name]

    def __iter__(self):
        return iter(self._tensors)

    def __len__(self) -> int:
        return len(self._tensors)

    @property
    def parameter_tree_digest(self) -> str:
        if self._execution_binding is not None:
            return require_execution_generation_binding(
                self._execution_binding, self._full_parameters,
                spec=ModelTopologySpecV2(), extents=self._extents,
            ).parameter_tree_digest
        return bamf_parameter_tree_digest(
            self._full_parameters, spec=ModelTopologySpecV2(), extents=self._extents)

    @property
    def generation_digest(self) -> str:
        if self._execution_binding is not None:
            return require_execution_generation_binding(
                self._execution_binding, self._full_parameters,
                spec=ModelTopologySpecV2(), extents=self._extents,
            ).generation_digest
        return execution_generation_digest(
            self._full_parameters, spec=ModelTopologySpecV2(), extents=self._extents)


def depth_parameter_view(
    parameters: Mapping[str, mx.array], *, spec: ModelTopologySpecV2,
    extents: GenerationExtents, boundary_group: int, execution_binding=None,
) -> DepthParameterView:
    """Borrow only shared depth tensors and the selected B01 boundary gate."""
    if (type(spec) is not ModelTopologySpecV2
            or type(extents) is not GenerationExtents
            or type(boundary_group) is not int
            or not MIN_COMPLETED_GROUPS <= boundary_group <= MAX_COMPLETED_GROUPS):
        _invalid()
    validate_bamf_parameters(spec, extents, parameters)
    declared = {item.name: item for item in expected_bamf_shapes(spec, extents)}
    names = _depth_names(boundary_group)
    if (set(names) != set(PARAMETER_SHAPES)
            or any(name not in declared
                   or declared[name].shape != PARAMETER_SHAPES[local]
                   for local, name in names.items())):
        _invalid()
    return DepthParameterView(
        {local: parameters[name] for local, name in names.items()},
        boundary_group, _VIEW_SEAL, parameters, extents, execution_binding)


@dataclass(frozen=True)
class _DepthFeatureValues:
    """Private numerical test seam; these arrays are not source authority."""

    frame_seed: mx.array
    type_role: mx.array
    semantic_release: str
    source_evidence_digest: str
    boundary_group: int
    schema_version: str = FEATURES_SCHEMA

    def __post_init__(self) -> None:
        if (not isinstance(self.semantic_release, str)
                or not _SHA.fullmatch(self.semantic_release)
                or not isinstance(self.source_evidence_digest, str)
                or not _SHA.fullmatch(self.source_evidence_digest)
                or type(self.boundary_group) is not int
                or not MIN_COMPLETED_GROUPS <= self.boundary_group <= MAX_COMPLETED_GROUPS
                or self.schema_version != FEATURES_SCHEMA):
            _invalid()


@dataclass(frozen=True)
class DepthFrameFeatures:
    """Complete source-member groups, never caller-supplied feature vectors."""

    requests: tuple[tuple[tuple[FeatureRequest, ...], ...], ...]
    features: AtlasFeatures
    boundary_group: int
    schema_version: str = RELEASED_FEATURES_SCHEMA
    atlas_selection: AtlasArtifactSelection | None = None

    def __post_init__(self):
        if (self.schema_version != RELEASED_FEATURES_SCHEMA or type(self.features) is not AtlasFeatures
                or (self.atlas_selection is not None and type(self.atlas_selection) is not AtlasArtifactSelection)
                or type(self.boundary_group) is not int
                or not MIN_COMPLETED_GROUPS <= self.boundary_group <= MAX_COMPLETED_GROUPS
                or type(self.requests) is not tuple or not self.requests
                or type(self.requests[0]) is not tuple or not self.requests[0]):
            _invalid()
        for row in self.requests:
            if type(row) is not tuple or len(row) != len(self.requests[0]):
                _invalid()
            for members in row:
                if type(members) is not tuple or not members or any(type(item) is not FeatureRequest for item in members):
                    _invalid()
                first = members[0]
                frame = first.projection.frame(first.frame_handle)
                if (tuple(item.local_slot for item in members) != tuple(range(len(frame.bindings)))
                        or any((item.projection.digest, item.frame_handle) !=
                               (first.projection.digest, first.frame_handle) for item in members)):
                    _invalid()


@dataclass(frozen=True)
class DepthSummary:
    source_id: str
    completed_layer: int
    hidden: mx.array
    schema_version: str = SUMMARY_SCHEMA

    def __post_init__(self) -> None:
        if (self.source_id not in SOURCE_ORDER
                or type(self.completed_layer) is not int
                or self.completed_layer != COMPLETED_LAYERS[
                    SOURCE_ORDER.index(self.source_id)]
                or self.schema_version != SUMMARY_SCHEMA):
            _invalid()

DepthParameterView.__module__ = "bilqis_mlx.runtime.block_attnres"
depth_parameter_view.__module__ = "bilqis_mlx.runtime.block_attnres"
_DepthFeatureValues.__module__ = "bilqis_mlx.runtime.block_attnres"
DepthFrameFeatures.__module__ = "bilqis_mlx.runtime.block_attnres"
DepthSummary.__module__ = "bilqis_mlx.runtime.block_attnres"
