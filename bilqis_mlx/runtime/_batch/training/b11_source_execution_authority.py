"""Process-local B11 source authority bound before neural execution."""
from __future__ import annotations

from dataclasses import dataclass, field, replace

from bilqis_mlx.errors import ErrorBus, SCHOOL
from bilqis_mlx.learning._engram.atlas_engram_identity import MotifFrameInput
from bilqis_mlx.learning.source_atoms.inputs import SourceAtomRow
from bilqis_mlx.semantics.atlas_projection import FrozenAtlasSnapshot
from bilqis_mlx.semantics.atlas_features import AtlasFeatures
from bilqis_mlx.semantics.atlas_features.records import FeatureRow
from bilqis_mlx.semantics.context_eligibility import (
    ApprovedContextProjection, SourceFrontier, TaskScope,
)
from bilqis_mlx.semantics.domains import contract_digest
from bilqis_mlx.semantics.frame_compiler import CompiledFrameBatch, FrameCompilerConfig
from bilqis_mlx.semantics.source_atom_binding import SourceAtomHandoff, SourceRowWitness
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
from .b11_source_launch_trust import (
    _LAUNCH_TRUST,
    compiled_input_launch_trusted as b11_compiled_input_launch_trusted,
    source_authority_launch_epoch as b11_source_authority_launch_epoch,
    source_authority_launch_trusted as b11_source_authority_launch_trusted,
)


_ISSUER = object()
_PREPARED_PROOF_ISSUER = object()
_MOTIF_FEATURE_ROW_WIDTH = 3
_MOTIF_FEATURE_VALUE_INDEX = 2
_MOTIF_SCHEMA_LIVENESS_ROW_WIDTH = 2


def _invalid(reason: str) -> None:
    ErrorBus.Raise(SCHOOL.BAMF_B11.SOURCE_EXECUTION_AUTHORITY_INVALID, reason=reason)


def _source_digest(source: SourceAtomRow) -> str:
    """Cheap row-content drift guard; graph authority was frozen at issuance."""
    return contract_digest(source.source_row)


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


@dataclass(frozen=True, init=False)
class B11SourceExecutionAuthority:
    """One owner-issued source proof reusable within an immutable compiled row."""

    snapshot: FrozenAtlasSnapshot
    source_adapter: object
    source_handoff: SourceAtomHandoff
    motif_projection: ApprovedContextProjection
    motif_execution_projection: ApprovedContextProjection
    motif_inputs: tuple[MotifFrameInput, ...]
    motif_feature_rows: tuple[tuple[str, str, FeatureRow], ...]
    motif_frontier: SourceFrontier
    task_scope: TaskScope
    motif_context_digest: str
    motif_schema_liveness: tuple[tuple[str, bool], ...]
    source_digest: str
    _compiled_row: CompiledFrameBatch = field(repr=False, compare=False)
    _config: FrameCompilerConfig = field(repr=False, compare=False)
    _source: SourceAtomRow = field(repr=False, compare=False)
    _issuance: object = field(repr=False, compare=False)

    def __init__(self, *args, **kwargs):
        _invalid("B11_SOURCE_EXECUTION_AUTHORITY_CALLER_CONSTRUCTION_FORBIDDEN")

    def __post_init__(self) -> None:
        descriptor = getattr(self.source_adapter, "descriptor", None)
        adapter_id = getattr(descriptor, "adapter_id", None)
        selection = self._source.selection
        if (
            self._issuance is not _ISSUER
            or type(self.snapshot) is not FrozenAtlasSnapshot
            or type(self.source_handoff) is not SourceAtomHandoff
            or type(self.motif_projection) is not ApprovedContextProjection
            or type(self.motif_execution_projection) is not ApprovedContextProjection
            or self.motif_execution_projection.digest != self._compiled_row.context_digest
            or type(self.motif_inputs) is not tuple
            or any(type(item) is not MotifFrameInput for item in self.motif_inputs)
            or type(self.motif_feature_rows) is not tuple
            or any(type(item) is not tuple
                   or len(item) != _MOTIF_FEATURE_ROW_WIDTH
                   or not isinstance(item[0], str) or not item[0]
                   or not isinstance(item[1], str) or not item[1]
                   or type(item[_MOTIF_FEATURE_VALUE_INDEX]) is not FeatureRow
                   for item in self.motif_feature_rows)
            or len({(item[0], item[1]) for item in self.motif_feature_rows})
            != len(self.motif_feature_rows)
            or type(self.motif_frontier) is not SourceFrontier
            or type(self.task_scope) is not TaskScope
            or not isinstance(self.motif_context_digest, str)
            or not self.motif_context_digest
            or type(self.motif_schema_liveness) is not tuple
            or any(type(item) is not tuple
                   or len(item) != _MOTIF_SCHEMA_LIVENESS_ROW_WIDTH
                   or not isinstance(item[0], str) or not item[0]
                   or type(item[1]) is not bool
                   for item in self.motif_schema_liveness)
            or type(self._compiled_row) is not CompiledFrameBatch
            or type(self._config) is not FrameCompilerConfig
            or type(self._source) is not SourceAtomRow
            or not isinstance(adapter_id, str) or not adapter_id
            or not isinstance(self.source_digest, str) or not self.source_digest
            or self.source_digest != _source_digest(self._source)
            or self.source_handoff.source_adapter_id != adapter_id
            or self.source_handoff.visible_end != self._compiled_row.visible_end
            or not self.source_handoff.embedding_ready
            or (
                self.snapshot.release_sha256,
                self.snapshot.bundle_id,
                self.snapshot.source_bundle_id,
            ) != (
                selection.release_sha256,
                selection.bundle_id,
                selection.source_bundle_id,
            )
            or (
                self.source_handoff.semantic_release,
                self.source_handoff.a01_bundle_id,
                self.source_handoff.a01_source_bundle_id,
            ) != (
                selection.release_sha256,
                selection.bundle_id,
                selection.source_bundle_id,
            )
            or self.task_scope
            != replace(
                self._config.task,
                causal_prefix_end=self._compiled_row.visible_end,
            )
        ):
            _invalid("B11_SOURCE_EXECUTION_AUTHORITY_INVALID")
        self.source_handoff.__post_init__()


def _issue_b11_source_execution_authority(
    compiled_row, config, source, source_adapter, snapshot, handoff,
    task_scope, projection, execution_projection, motifs, feature_rows, frontier,
    context_digest, schema_liveness,
):
    authority = object.__new__(B11SourceExecutionAuthority)
    for name, value in (
        ("snapshot", snapshot),
        ("source_adapter", source_adapter),
        ("source_handoff", handoff),
        ("motif_projection", projection),
        ("motif_execution_projection", execution_projection),
        ("motif_inputs", motifs),
        ("motif_feature_rows", feature_rows),
        ("motif_frontier", frontier),
        ("task_scope", task_scope),
        ("motif_context_digest", context_digest),
        ("motif_schema_liveness", schema_liveness),
        ("source_digest", _source_digest(source)),
        ("_compiled_row", compiled_row),
        ("_config", config),
        ("_source", source),
        ("_issuance", _ISSUER),
    ):
        object.__setattr__(authority, name, value)
    authority.__post_init__()
    return authority


def bind_b11_source_execution_authority(
    compiled_row: CompiledFrameBatch,
    config: FrameCompilerConfig,
    source: SourceAtomRow,
    source_adapter,
    snapshot: FrozenAtlasSnapshot,
    features: AtlasFeatures,
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
    "require_b11_source_execution_authority",
    "require_b11_source_execution_authority_current",
    "require_b11_source_feature_row",
)
