"""Sealed B11 source-execution record and issuance contract."""
from __future__ import annotations

from dataclasses import dataclass, field, replace

from bilqis_mlx.errors import ErrorBus, SCHOOL
from bilqis_mlx.learning._engram.atlas_engram_identity import MotifFrameInput
from bilqis_mlx.learning.source_atoms.inputs import SourceAtomRow
from bilqis_mlx.semantics.atlas_projection import FrozenAtlasSnapshot
from bilqis_mlx.semantics.atlas_features.records import FeatureRow
from bilqis_mlx.semantics.context_eligibility import (
    ApprovedContextProjection, SourceFrontier, TaskScope,
)
from bilqis_mlx.semantics.domains import contract_digest
from bilqis_mlx.semantics.frame_compiler import CompiledFrameBatch, FrameCompilerConfig
from bilqis_mlx.semantics.source_atom_binding import SourceAtomHandoff

from .b11_source_owner_authority import row_owner_contract as _row_owner_contract


_ISSUER = object()
_MOTIF_FEATURE_ROW_WIDTH = 3
_MOTIF_FEATURE_VALUE_INDEX = 2
_MOTIF_SCHEMA_LIVENESS_ROW_WIDTH = 2


def _invalid(reason: str) -> None:
    ErrorBus.Raise(SCHOOL.BAMF_B11.SOURCE_EXECUTION_AUTHORITY_INVALID, reason=reason)


def _source_digest(source: SourceAtomRow) -> str:
    """Cheap row-content drift guard; graph authority was frozen at issuance."""
    return contract_digest(source.source_row)


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
    source_owner_contract: tuple
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
            or self.source_owner_contract
            != _row_owner_contract(self.source_adapter, self._source)
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
            or self.task_scope != replace(
                self._config.task, causal_prefix_end=self._compiled_row.visible_end)
        ):
            _invalid("B11_SOURCE_EXECUTION_AUTHORITY_INVALID")
        self.source_handoff.__post_init__()


def issue_b11_source_execution_authority(
    compiled_row, config, source, source_adapter, snapshot, handoff,
    task_scope, projection, execution_projection, motifs, feature_rows, frontier,
    context_digest, schema_liveness,
):
    authority = object.__new__(B11SourceExecutionAuthority)
    for name, value in (
        ("snapshot", snapshot), ("source_adapter", source_adapter),
        ("source_handoff", handoff), ("motif_projection", projection),
        ("motif_execution_projection", execution_projection),
        ("motif_inputs", motifs), ("motif_feature_rows", feature_rows),
        ("motif_frontier", frontier), ("task_scope", task_scope),
        ("motif_context_digest", context_digest),
        ("motif_schema_liveness", schema_liveness),
        ("source_digest", _source_digest(source)),
        ("source_owner_contract", _row_owner_contract(source_adapter, source)),
        ("_compiled_row", compiled_row), ("_config", config),
        ("_source", source), ("_issuance", _ISSUER),
    ):
        object.__setattr__(authority, name, value)
    authority.__post_init__()
    return authority


__all__ = (
    "B11SourceExecutionAuthority", "_ISSUER", "_source_digest",
    "issue_b11_source_execution_authority",
)
