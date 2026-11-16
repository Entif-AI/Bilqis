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


def _validate_compiled_batch_shape(batch):
    if (
        batch.schema_version != "bilqis.mlx.b11-compiled-batch/v1"
        or type(batch.compiled) is not CompiledEncoderInput
        or type(batch.sources) is not tuple
        or len(batch.sources) != len(batch.compiled.compiled.rows)
        or len(batch.sources) != 1
        or any(type(item) is not SourceAtomRow for item in batch.sources)
        or type(batch.feature_schema) is not FeatureSchema
        or type(batch.active_semantic_rows) is not BamfActiveSemanticRows
        or (batch.training_authority is not None
            and type(batch.training_authority) is not BamfTrainingAuthority)
        or (batch.visit_provenance is not None
            and type(batch.visit_provenance) is not BamfVisitProvenance)
        or ((batch.training_authority is None)
            != (batch.visit_provenance is None))
    ):
        _invalid("B11_COMPILED_BATCH_INVALID")
    batch.compiled.__post_init__()
    batch.active_semantic_rows.__post_init__()


def _validate_active_semantic_rows(batch):
    rows = batch.active_semantic_rows
    compiled = batch.compiled
    if (
        rows.extents_digest != compiled.extents.digest
        or rows.feature_digest != compiled.features.digest
        or rows.semantic_release != compiled.features.semantic_release
        or rows.active_semantic_digest != compiled.extents.active_semantic_digest
        or any(index >= compiled.extents.semantic_bank_count
               * ModelTopologySpecV2.semantic_bank_rows
               for index in rows.active_indices)
    ):
        _invalid("B11_ACTIVE_SEMANTIC_ROWS_GENERATION_MISMATCH")


def _validate_bound_source_authority(batch):
    if batch.source_execution_authority is None:
        return
    from bilqis_mlx.runtime.b11_source_execution_authority import (
        require_b11_source_execution_authority,
    )
    from bilqis_mlx.runtime.b11_source_execution_authority import (
        b11_source_authority_launch_trusted,
    )
    row = batch.compiled.compiled.rows[0]
    config = batch.compiled.compiler_configs[0]
    source = batch.sources[0]
    if not b11_source_authority_launch_trusted(
            batch.source_execution_authority, row, config, source):
        require_b11_source_execution_authority(
            batch.source_execution_authority, row, config, source)


def _validate_task_authority(batch):
    if batch.task_authority is None:
        return
    from bilqis_mlx.runtime.factory_task_authority import FactoryTaskAuthority
    if type(batch.task_authority) is not FactoryTaskAuthority:
        _invalid("B11_FACTORY_TASK_AUTHORITY_INVALID")
    batch.task_authority.__post_init__()
    training = batch.training_authority
    if (
        batch.task_authority.source_row_id
        != batch.sources[0].source_row.get("id")
        or batch.task_authority.capability_id
        != batch.sources[0].source_row.get("capability")
        or ((training is None)
            != (batch.task_authority.training_authority_sha256 is None))
        or (training is not None
            and training.digest
            != batch.task_authority.training_authority_sha256)
    ):
        _invalid("B11_FACTORY_TASK_AUTHORITY_MISMATCH")


def _validate_training_context(batch):
    if batch.training_authority is None:
        return
    batch.visit_provenance.__post_init__()
    if (batch.visit_provenance.capability_id
            != batch.training_authority.delivery_capability
            or batch.visit_provenance.visit_id
            != batch.training_authority.visit_id):
        _invalid("B11_VISIT_PROVENANCE_CAPABILITY_MISMATCH")
    row = batch.compiled.compiled.rows[0]
    frame_nodes = batch.compiled.packed_frame_artifact_owner.require_row(row)
    contextual_kinds = {
        DependencyKind.POLICY, DependencyKind.RIGHTS, DependencyKind.TIME,
    }
    current_context = {
        ref for node in frame_nodes for ref in node.immediate_dependencies
        if ref.kind in contextual_kinds
    }
    authority_context = {
        ref for ref in batch.training_authority.immediate_dependencies
        if ref.kind in contextual_kinds
    }
    if not current_context.issubset(authority_context):
        _invalid("B11_TRAINING_AUTHORITY_CONTEXT_DRIFT")


def _bind_atlas_feature_owner(batch):
    owner = getattr(batch, "atlas_feature_artifact_owner", None)
    if owner is None:
        object.__setattr__(
            batch,
            "atlas_feature_artifact_owner",
            AtlasFeatureArtifactOwner(
                batch.compiled.features, batch.feature_schema),
        )
        return
    owner.require(batch.compiled.features)


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
        _validate_compiled_batch_shape(self)
        _validate_active_semantic_rows(self)
        _validate_bound_source_authority(self)
        _validate_task_authority(self)
        _validate_training_context(self)
        _bind_atlas_feature_owner(self)


# Keep the pre-extraction public identity stable for introspection and pickle.
BamfCompiledBatch.__module__ = "bilqis_mlx.runtime.atlas_model_contracts"


__all__ = ("BamfCompiledBatch",)
