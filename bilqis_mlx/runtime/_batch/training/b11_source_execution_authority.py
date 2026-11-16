"""Process-local B11 source authority bound before neural execution."""
from __future__ import annotations

from dataclasses import dataclass, field

from bilqis_mlx.errors import ErrorBus, SCHOOL
from bilqis_mlx.factory.adapters import SourceAdapterRegistry
from bilqis_mlx.learning.source_atoms.inputs import SourceAtomRow
from bilqis_mlx.semantics.atlas_projection import FrozenAtlasSnapshot
from bilqis_mlx.semantics.atlas_features import AtlasFeatures
from bilqis_mlx.semantics.context_eligibility import (
    ApprovedContextProjection, SourceFrontier,
)
from bilqis_mlx.semantics.frame_compiler import CompiledFrameBatch, FrameCompilerConfig
from bilqis_mlx.semantics.source_atom_binding import SourceRowWitness
from bilqis_mlx.runtime.source_execution import (
    SourceBatchAuthority, SourceExecutionContext, source_content_digest,
)

from .b11_source_execution_binding import (
    bind_motif_context as _bind_motif_context,
    bind_prepared_motif_context as _bind_prepared_motif_context,
    bind_prepared_source_handoff as _bind_prepared_source_handoff,
    bind_motif_execution_projection as _bind_motif_execution_projection,
    bind_motif_feature_rows as _bind_motif_feature_rows,
    bind_motif_read_context as _bind_motif_read_context,
    bind_source_handoff as _bind_source_handoff,
)
from .b11_source_feature_authority import (
    require_source_feature_row as require_b11_source_feature_row,
)
from .b11_source_execution_contracts import (
    B11SourceExecutionAuthority, _ISSUER, _source_digest,
    issue_b11_source_execution_authority as _issue_b11_source_execution_authority,
)
from .b11_source_launch_trust import (
    _LAUNCH_TRUST,
    compiled_input_launch_trusted as b11_compiled_input_launch_trusted,
    source_authority_launch_epoch as b11_source_authority_launch_epoch,
    source_authority_launch_trusted as b11_source_authority_launch_trusted,
)
from .b11_source_owner_authority import (
    require_bound_row_owner_current as require_b11_source_owner_current,
    require_row_owner as _require_row_owner,
)


_PREPARED_PROOF_ISSUER = object()


def _invalid(reason: str) -> None:
    ErrorBus.Raise(SCHOOL.BAMF_B11.SOURCE_EXECUTION_AUTHORITY_INVALID, reason=reason)


@dataclass(frozen=True)
class _PreparedB11SourceProof:
    """Sealed proof that one exact row passed its SourceBatchAuthority boundary."""

    source_authority: SourceBatchAuthority
    row_sha256: str
    source_witness: SourceRowWitness
    motif_projection: ApprovedContextProjection
    motif_frontier: SourceFrontier
    _issuance: object = field(repr=False, compare=False)

    def __post_init__(self):
        if (type(self.source_authority) is not SourceBatchAuthority
                or not isinstance(self.row_sha256, str) or not self.row_sha256
                or type(self.source_witness) is not SourceRowWitness
                or type(self.motif_projection) is not ApprovedContextProjection
                or type(self.motif_frontier) is not SourceFrontier
                or self._issuance is not _PREPARED_PROOF_ISSUER):
            _invalid("B11_SOURCE_EXECUTION_PREPARED_PROOF_INVALID")


def _issue_prepared_b11_source_proof(
        source_context, rows, source_authority, row, source_witness,
        motif_projection, motif_frontier):
    """Mint only after the exact batch has passed its owner-issued proof boundary."""
    if type(source_context) is not SourceExecutionContext:
        _invalid("B11_SOURCE_EXECUTION_PREPARED_PROOF_INVALID")
    source_context.require_bound_rows(rows, source_authority)
    if not any(candidate is row for candidate in rows):
        _invalid("B11_SOURCE_EXECUTION_PREPARED_PROOF_INVALID")
    proof = _PreparedB11SourceProof(
        source_authority, source_content_digest((row,)), source_witness,
        motif_projection, motif_frontier, _PREPARED_PROOF_ISSUER)
    proof.__post_init__()
    return proof


def _require_prepared_b11_source_proof(proof, source, source_adapter):
    if type(proof) is not _PreparedB11SourceProof:
        _invalid("B11_SOURCE_EXECUTION_PREPARED_PROOF_INVALID")
    proof.__post_init__()
    if (proof.row_sha256 != source_content_digest((source.source_row,))
            or proof.source_authority.capability_id
            != source.source_row.get("capability")
            or proof.source_witness.source_adapter_id
            != source_adapter.descriptor.adapter_id):
        _invalid("B11_SOURCE_EXECUTION_PREPARED_PROOF_DRIFT")
    return proof


def bind_b11_source_execution_authority(
    compiled_row: CompiledFrameBatch,
    config: FrameCompilerConfig,
    source: SourceAtomRow,
    source_adapter,
    snapshot: FrozenAtlasSnapshot,
    features: AtlasFeatures,
    *,
    source_registry: SourceAdapterRegistry | None = None,
) -> B11SourceExecutionAuthority:
    """Qualify one source row once before B11 enters the neural hot path."""
    if (
        type(compiled_row) is not CompiledFrameBatch
        or type(config) is not FrameCompilerConfig
        or type(source) is not SourceAtomRow
        or type(snapshot) is not FrozenAtlasSnapshot
        or type(features) is not AtlasFeatures
    ):
        _invalid("B11_SOURCE_EXECUTION_AUTHORITY_INPUT_INVALID")
    if source_registry is None:
        from bilqis_mlx.source_adapters.school import live_source_registry
        source_registry = live_source_registry()
    _require_row_owner(source_adapter, source_registry, source, drift=False)
    handoff = _bind_source_handoff(
        compiled_row, config, source, snapshot)
    task_scope, projection, motifs, frontier = _bind_motif_context(
        compiled_row, config, source, source_adapter, snapshot)
    feature_rows = _bind_motif_feature_rows(
        projection, motifs, features, source)
    execution_projection = _bind_motif_execution_projection(
        compiled_row, config, projection, frontier, task_scope)
    context_digest, schema_liveness = _bind_motif_read_context(
        execution_projection, motifs, frontier, task_scope)
    return _issue_b11_source_execution_authority(
        compiled_row, config, source, source_adapter, snapshot, handoff,
        task_scope, projection, execution_projection, motifs, feature_rows, frontier,
        context_digest, schema_liveness)


def _bind_prepared_b11_source_execution_authority(
    compiled_row: CompiledFrameBatch,
    config: FrameCompilerConfig,
    source: SourceAtomRow,
    source_adapter,
    snapshot: FrozenAtlasSnapshot,
    features: AtlasFeatures,
    proof,
) -> B11SourceExecutionAuthority:
    """Consume only a sealed SourceBatchAuthority-backed preparation proof."""
    if (type(compiled_row) is not CompiledFrameBatch
            or type(config) is not FrameCompilerConfig
            or type(source) is not SourceAtomRow
            or type(snapshot) is not FrozenAtlasSnapshot
            or type(features) is not AtlasFeatures):
        _invalid("B11_SOURCE_EXECUTION_AUTHORITY_INPUT_INVALID")
    proof = _require_prepared_b11_source_proof(proof, source, source_adapter)
    handoff = _bind_prepared_source_handoff(
        compiled_row, config, source, snapshot, proof.source_witness)
    task_scope, projection, motifs, frontier = _bind_prepared_motif_context(
        compiled_row, config, source, source_adapter, snapshot,
        proof.motif_projection, proof.motif_frontier)
    feature_rows = _bind_motif_feature_rows(
        projection, motifs, features, source)
    execution_projection = _bind_motif_execution_projection(
        compiled_row, config, projection, frontier, task_scope)
    context_digest, schema_liveness = _bind_motif_read_context(
        execution_projection, motifs, frontier, task_scope)
    return _issue_b11_source_execution_authority(
        compiled_row, config, source, source_adapter, snapshot, handoff,
        task_scope, projection, execution_projection, motifs, feature_rows, frontier,
        context_digest, schema_liveness)


def require_b11_source_execution_authority(
    authority,
    compiled_row: CompiledFrameBatch,
    config: FrameCompilerConfig,
    source: SourceAtomRow,
) -> B11SourceExecutionAuthority:
    """Require cheap exact-object currentness after the bind-time content proof."""
    if (
        type(authority) is not B11SourceExecutionAuthority
        or authority._issuance is not _ISSUER
        or authority._compiled_row is not compiled_row
        or authority._config is not config
        or authority._source is not source
        or authority.source_digest != _source_digest(source)
    ):
        _invalid("B11_SOURCE_EXECUTION_AUTHORITY_DRIFT")
    return authority


def require_b11_source_execution_authority_current(
    authority,
    compiled_row: CompiledFrameBatch,
    config: FrameCompilerConfig,
    source: SourceAtomRow,
) -> B11SourceExecutionAuthority:
    """Require exact objects plus the current A13 rights/correction epoch."""
    authority = require_b11_source_execution_authority(
        authority, compiled_row, config, source)
    from bilqis_mlx.semantics.frame_adapters.registry import source_frame_strategy
    adapter_id = authority.source_adapter.descriptor.adapter_id
    if source_frame_strategy(adapter_id).source_family is None:
        if (authority.motif_frontier.rights_epoch != config.frontier.rights_epoch
                or authority.motif_frontier.correction_generation
                != config.frontier.correction_generation):
            _invalid("B11_SOURCE_EXECUTION_SCHEMA_RIGHTS_STALE")
        return authority
    from bilqis_mlx.semantics.frame_adapters.public_formal_schema_rights import (
        issue_source_schema_rights_authority,
    )
    current = issue_source_schema_rights_authority(source.selection)
    if (authority.motif_frontier.rights_epoch != current.rights_epoch
            or authority.motif_frontier.correction_generation
            != current.correction_generation):
        _invalid("B11_SOURCE_EXECUTION_SCHEMA_RIGHTS_STALE")
    return authority


__all__ = (
    "B11SourceExecutionAuthority",
    "bind_b11_source_execution_authority",
    "b11_compiled_input_launch_trusted",
    "b11_source_authority_launch_epoch",
    "b11_source_authority_launch_trusted",
    "require_b11_source_owner_current",
    "require_b11_source_execution_authority",
    "require_b11_source_execution_authority_current",
    "require_b11_source_feature_row",
)
