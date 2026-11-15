"""B11 compiled-batch execution contract."""
from __future__ import annotations

from dataclasses import dataclass, field

from bilqis_mlx.errors import ErrorBus, SCHOOL
from bilqis_mlx.learning.frame_encoder import CompiledEncoderInput
from bilqis_mlx.learning.source_atoms.inputs import SourceAtomRow
from bilqis_mlx.runtime.atlas_artifact_owner import AtlasFeatureArtifactOwner
from bilqis_mlx.runtime.atlas_training_authority import BamfTrainingAuthority
from bilqis_mlx.runtime.atlas_visit_provenance import BamfVisitProvenance
from bilqis_mlx.runtime.model_topology_v2 import ModelTopologySpecV2
from bilqis_mlx.semantics.atlas_features import FeatureSchema
from bilqis_mlx.semantics.cognitive_dependencies import DependencyKind

from .active_semantic_rows import BamfActiveSemanticRows


def _invalid(reason: str) -> None:
    ErrorBus.Raise(SCHOOL.MODEL_TOPOLOGY.INVALID, reason=reason)


@dataclass(frozen=True)
class BamfCompiledBatch:
    """One source-qualified compiled row and the source inputs that created it."""

    compiled: CompiledEncoderInput
    sources: tuple[SourceAtomRow, ...]
    feature_schema: FeatureSchema
    active_semantic_rows: BamfActiveSemanticRows
    training_authority: BamfTrainingAuthority | None = None
    visit_provenance: BamfVisitProvenance | None = None
    task_authority: object | None = None
    schema_version: str = "bilqis.mlx.b11-compiled-batch/v1"
    source_execution_authority: object | None = field(
        default=None, repr=False, compare=False)
    atlas_feature_artifact_owner: AtlasFeatureArtifactOwner = field(init=False, compare=False)

    def __post_init__(self) -> None:
        if (
            self.schema_version != "bilqis.mlx.b11-compiled-batch/v1"
            or type(self.compiled) is not CompiledEncoderInput
            or type(self.sources) is not tuple
            or len(self.sources) != len(self.compiled.compiled.rows)
            or len(self.sources) != 1
            or any(type(item) is not SourceAtomRow for item in self.sources)
            or type(self.feature_schema) is not FeatureSchema
            or type(self.active_semantic_rows) is not BamfActiveSemanticRows
            or (self.training_authority is not None
                and type(self.training_authority) is not BamfTrainingAuthority)
            or (self.visit_provenance is not None
                and type(self.visit_provenance) is not BamfVisitProvenance)
            or ((self.training_authority is None) != (self.visit_provenance is None))
        ):
            _invalid("B11_COMPILED_BATCH_INVALID")
        self.compiled.__post_init__()
        self.active_semantic_rows.__post_init__()
        if (
            self.active_semantic_rows.extents_digest != self.compiled.extents.digest
            or self.active_semantic_rows.feature_digest != self.compiled.features.digest
            or self.active_semantic_rows.semantic_release
            != self.compiled.features.semantic_release
            or self.active_semantic_rows.active_semantic_digest
            != self.compiled.extents.active_semantic_digest
            or any(index >= self.compiled.extents.semantic_bank_count
                   * ModelTopologySpecV2.semantic_bank_rows
                   for index in self.active_semantic_rows.active_indices)
        ):
            _invalid("B11_ACTIVE_SEMANTIC_ROWS_GENERATION_MISMATCH")
        if self.source_execution_authority is not None:
            from bilqis_mlx.runtime.b11_source_execution_authority import (
                require_b11_source_execution_authority,
            )
            require_b11_source_execution_authority(
                self.source_execution_authority,
                self.compiled.compiled.rows[0],
                self.compiled.compiler_configs[0],
                self.sources[0],
            )
        if self.task_authority is not None:
            from bilqis_mlx.runtime.factory_task_authority import FactoryTaskAuthority
            if type(self.task_authority) is not FactoryTaskAuthority:
                _invalid("B11_FACTORY_TASK_AUTHORITY_INVALID")
            self.task_authority.__post_init__()
            training = self.training_authority
            if (
                self.task_authority.source_row_id != self.sources[0].source_row.get("id")
                or self.task_authority.capability_id
                != self.sources[0].source_row.get("capability")
                or ((training is None)
                    != (self.task_authority.training_authority_sha256 is None))
                or (training is not None
                    and training.digest
                    != self.task_authority.training_authority_sha256)
            ):
                _invalid("B11_FACTORY_TASK_AUTHORITY_MISMATCH")
        if self.training_authority is not None:
            self.visit_provenance.__post_init__()
            if (self.visit_provenance.capability_id
                    != self.training_authority.delivery_capability
                    or self.visit_provenance.visit_id
                    != self.training_authority.visit_id):
                _invalid("B11_VISIT_PROVENANCE_CAPABILITY_MISMATCH")
            row = self.compiled.compiled.rows[0]
            frame_nodes = self.compiled.packed_frame_artifact_owner.require_row(row)
            contextual_kinds = {
                DependencyKind.POLICY, DependencyKind.RIGHTS, DependencyKind.TIME,
            }
            current_context = {
                ref
                for node in frame_nodes
                for ref in node.immediate_dependencies
                if ref.kind in contextual_kinds
            }
            authority_context = {
                ref for ref in self.training_authority.immediate_dependencies
                if ref.kind in contextual_kinds
            }
            if not current_context.issubset(authority_context):
                _invalid("B11_TRAINING_AUTHORITY_CONTEXT_DRIFT")
        owner = getattr(self, "atlas_feature_artifact_owner", None)
        if owner is None:
            object.__setattr__(
                self,
                "atlas_feature_artifact_owner",
                AtlasFeatureArtifactOwner(self.compiled.features, self.feature_schema),
            )
        else:
            owner.require(self.compiled.features)


# Keep the pre-extraction public identity stable for introspection and pickle.
BamfCompiledBatch.__module__ = "bilqis_mlx.runtime.atlas_model_contracts"


__all__ = ("BamfCompiledBatch",)
