"""Compiled for the existing frame encoder contract."""
from __future__ import annotations

from bilqis_mlx.learning.frame_embeddings import ChildFrameRequest
from bilqis_mlx.learning.frame_embeddings import FeatureRequest
from bilqis_mlx.learning.frame_embeddings import FrameConstituentRequest
from bilqis_mlx.learning.frame_embeddings import validate_frame_members
from bilqis_mlx.runtime.model_topology_v2 import GenerationExtents
from bilqis_mlx.semantics.atlas_features import AtlasFeatures
from bilqis_mlx.semantics.context_eligibility import ApprovedContextProjection
from bilqis_mlx.semantics.context_eligibility import project_context
from bilqis_mlx.semantics.frame_compiler import CompiledFrameRows
from bilqis_mlx.semantics.frame_compiler import FrameCompilerConfig
from bilqis_mlx.semantics.frame_compiler import PositionKind
from bilqis_mlx.semantics.frame_compiler import StreamingAST
from bilqis_mlx.semantics.frame_compiler import compile_prefix
from bilqis_mlx.semantics.frame_compiler import reconstruct
from bilqis_mlx.semantics.frame_schema import AtomicFrame
from bilqis_mlx.semantics.frame_schema import FrameInstance
from bilqis_mlx.semantics.partial_visible_forest import PartialVisibleForestReceipt
from bilqis_mlx.semantics.partial_visible_forest import validate_partial_visible_forest
from dataclasses import dataclass
from dataclasses import field
from bilqis_mlx.runtime.atlas_artifact_owner import PackedFrameArtifactOwner
from dataclasses import replace
from .contracts import (
    AtomicSourceHandle, _invalid,
)


def _compiled_groups(row, config, source_ast=None, receipt=None):
    if source_ast is None:
        if receipt is not None:
            _invalid()
        visible = reconstruct(row)
        def has_child_edge(tree):
            return (
                (type(tree.root) is FrameInstance
                 and any(binding.child_frame is not None
                         for binding in tree.root.bindings))
                or any(has_child_edge(child) for child in tree.children))
        if any(has_child_edge(tree) for tree in visible.frames):
            _invalid()
        rebuilt = compile_prefix(
            StreamingAST(
                visible.source_instance_id, visible.atoms, visible.frames),
            row.visible_end, row.semantic_release, config)
        if rebuilt != row:
            _invalid()
    else:
        if type(source_ast) is not StreamingAST or type(
                receipt) is not PartialVisibleForestReceipt:
            _invalid()
        validate_partial_visible_forest(
            row, source_ast, config, expected_receipt=receipt)
    closures = tuple(position for position in row.positions if position.kind is PositionKind.CLOSURE)
    projection = None
    if closures:
        if config.approved is None:
            _invalid()
        handles = {position.frame_handle for position in closures}
        projection = project_context(tuple(item for item in config.approved.envelopes if item.frame_handle in handles),
                                     replace(config.task, causal_prefix_end=row.visible_end), config.frontier, config.policy)
        if type(projection) is not ApprovedContextProjection or projection.digest != row.context_digest:
            _invalid()
    groups = []
    for position in row.positions:
        if position.kind is PositionKind.ATOM:
            groups.append(())
            continue
        frame = projection.frame(position.frame_handle)
        if type(frame) is AtomicFrame:
            groups.append(())
            continue
        if type(frame) is not FrameInstance:
            _invalid()
        envelope = next(item for item in projection.envelopes if item.frame_handle == position.frame_handle)
        group = []
        for member in envelope.members:
            binding = next((
                item for item in frame.bindings
                if item.key == member.key), None)
            if binding is None:
                _invalid()
            constructor = (
                FeatureRequest if binding.concept is not None
                else ChildFrameRequest if binding.child_frame is not None
                else None)
            if constructor is None:
                _invalid()
            group.append(constructor.from_context(
                projection, position.frame_handle, member.source_handle))
        group = tuple(group)
        if group:
            validate_frame_members(group)
        groups.append(group)
    return tuple(groups), projection


def _owned_compiled_groups(row, config, artifact_owner, source_ast=None, receipt=None):
    artifact_owner.require_row(row)
    return _compiled_groups(row, config, source_ast, receipt)


@dataclass(frozen=True)
class CompiledEncoderInput:
    """Actual A05 rows, current compiler authority and released B02 features."""

    compiled: CompiledFrameRows
    compiler_configs: tuple[FrameCompilerConfig, ...]
    features: AtlasFeatures
    extents: GenerationExtents
    source_asts: tuple[StreamingAST, ...] | None = None
    partial_forest_receipts: tuple[PartialVisibleForestReceipt, ...] | None = None
    member_requests: tuple[tuple[FeatureRequest, ...], ...] = field(init=False)
    atomic_handles: tuple[tuple[AtomicSourceHandle, ...], ...] = field(init=False)
    _groups: tuple[tuple[tuple[FrameConstituentRequest, ...], ...], ...] = field(init=False, repr=False)
    _projections: tuple[ApprovedContextProjection | None, ...] = field(init=False, repr=False)
    packed_frame_artifact_owner: PackedFrameArtifactOwner = field(
        init=False, repr=False, compare=False)
    schema_version: str = "bilqis.mlx.compiled-encoder-input/v1"

    def __post_init__(self):
        if (self.schema_version != "bilqis.mlx.compiled-encoder-input/v1" or
                type(self.compiled) is not CompiledFrameRows or not self.compiled.rows or
                type(self.compiler_configs) is not tuple or len(self.compiler_configs) != len(self.compiled.rows) or
                any(type(config) is not FrameCompilerConfig for config in self.compiler_configs) or
                type(self.features) is not AtlasFeatures or type(self.extents) is not GenerationExtents or
                self.extents.factor_map_digest != self.features.digest or
                any(row.semantic_release != self.features.semantic_release for row in self.compiled.rows)
                or ((self.source_asts is None)
                    != (self.partial_forest_receipts is None))
                or (self.source_asts is not None
                    and (type(self.source_asts) is not tuple
                         or type(self.partial_forest_receipts) is not tuple
                         or len(self.source_asts) != len(self.compiled.rows)
                         or len(self.partial_forest_receipts) != len(self.compiled.rows)))):
            _invalid()
        self.compiled.__post_init__()
        if not hasattr(self, "packed_frame_artifact_owner"):
            object.__setattr__(
                self, "packed_frame_artifact_owner",
                PackedFrameArtifactOwner(self.compiled))
        from bilqis_mlx.runtime.b11_source_execution_authority import (
            b11_compiled_input_launch_trusted,
        )
        if (b11_compiled_input_launch_trusted(self)
                and hasattr(self, "_groups") and hasattr(self, "_projections")
                and hasattr(self, "member_requests") and hasattr(self, "atomic_handles")):
            return
        source_asts = self.source_asts or (None,) * len(self.compiled.rows)
        receipts = self.partial_forest_receipts or (None,) * len(self.compiled.rows)
        checked = tuple(
            _owned_compiled_groups(
                row, config, self.packed_frame_artifact_owner, source_ast, receipt)
            for row, config, source_ast, receipt in zip(
                self.compiled.rows, self.compiler_configs,
                source_asts, receipts))
        groups = tuple(item[0] for item in checked)
        object.__setattr__(self, "_groups", groups)
        object.__setattr__(self, "_projections", tuple(item[1] for item in checked))
        object.__setattr__(self, "member_requests", tuple(tuple(item for group in row for item in group
                                                                if type(item) is FeatureRequest)
                                                         for row in groups))
        atomic_handles = []
        for row, (_, projection) in zip(self.compiled.rows, checked):
            handles = []
            for position in row.positions:
                if (position.kind is PositionKind.CLOSURE and
                        type(projection.frame(position.frame_handle)) is AtomicFrame):
                    source = next(item for item in projection.envelopes if item.frame_handle == position.frame_handle)
                    handles.append(AtomicSourceHandle(projection, position.frame_handle, source.members[0].source_handle))
            atomic_handles.append(tuple(handles))
        object.__setattr__(self, "atomic_handles", tuple(atomic_handles))
