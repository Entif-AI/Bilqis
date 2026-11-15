"""Process-local B11 source authority bound before neural execution."""
from __future__ import annotations

from dataclasses import dataclass, field, replace

from bilqis_mlx.errors import ErrorBus, SCHOOL
from bilqis_mlx.learning._engram.atlas_engram_source_context import (
    qualify_source_motif_context,
)
from bilqis_mlx.learning._engram.atlas_engram_identity import MotifFrameInput
from bilqis_mlx.learning.source_atoms.inputs import SourceAtomRow
from bilqis_mlx.semantics.atlas_projection import FrozenAtlasSnapshot
from bilqis_mlx.semantics.context_eligibility import (
    ApprovedContextProjection, ContextHold, SourceFrontier, TaskScope,
)
from bilqis_mlx.semantics.domains import contract_digest
from bilqis_mlx.semantics.frame_compiler import CompiledFrameBatch, FrameCompilerConfig
from bilqis_mlx.semantics.source_atom_binding import SourceAtomHandoff
from bilqis_mlx.source_adapters.atom_binding import (
    _build_source_atom_handoff_from_snapshot,
)


_ISSUER = object()


def _invalid(reason: str) -> None:
    ErrorBus.Raise(SCHOOL.MODEL_TOPOLOGY.INVALID, reason=reason)


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
    motif_inputs: tuple[MotifFrameInput, ...]
    motif_frontier: SourceFrontier
    task_scope: TaskScope
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
            or type(self.motif_inputs) is not tuple
            or any(type(item) is not MotifFrameInput for item in self.motif_inputs)
            or type(self.motif_frontier) is not SourceFrontier
            or type(self.task_scope) is not TaskScope
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


def bind_b11_source_execution_authority(
    compiled_row: CompiledFrameBatch,
    config: FrameCompilerConfig,
    source: SourceAtomRow,
    source_adapter,
    snapshot: FrozenAtlasSnapshot,
) -> B11SourceExecutionAuthority:
    """Qualify one source row once before B11 enters the neural hot path."""
    if (
        type(compiled_row) is not CompiledFrameBatch
        or type(config) is not FrameCompilerConfig
        or type(source) is not SourceAtomRow
        or type(snapshot) is not FrozenAtlasSnapshot
    ):
        _invalid("B11_SOURCE_EXECUTION_AUTHORITY_INPUT_INVALID")
    task_scope = replace(config.task, causal_prefix_end=compiled_row.visible_end)
    handoff = _build_source_atom_handoff_from_snapshot(
        compiled_row,
        config,
        source.selection,
        snapshot,
        source.source_row,
        source.graph,
        **source.replay_arguments(),
    )
    if not handoff.embedding_ready:
        _invalid("B11_SOURCE_EXECUTION_HANDOFF_HELD")
    replayed = qualify_source_motif_context(
        source_adapter,
        source.source_row,
        source.selection,
        source_root=source.source_root,
        graph=source.graph,
        task_scope=task_scope,
        source_frontier=config.frontier,
        policy=config.policy,
        source_seed=source.source_seed,
        source_each=source.source_each,
        source_profile_parameters=source.source_profile_parameters,
        course=source.course,
        snapshot=snapshot,
    )
    if isinstance(replayed, ContextHold):
        _invalid("B11_SOURCE_EXECUTION_MOTIF_CONTEXT_HELD")
    projection, motifs, frontier = replayed
    authority = object.__new__(B11SourceExecutionAuthority)
    for name, value in (
        ("snapshot", snapshot),
        ("source_adapter", source_adapter),
        ("source_handoff", handoff),
        ("motif_projection", projection),
        ("motif_inputs", motifs),
        ("motif_frontier", frontier),
        ("task_scope", task_scope),
        ("source_digest", _source_digest(source)),
        ("_compiled_row", compiled_row),
        ("_config", config),
        ("_source", source),
        ("_issuance", _ISSUER),
    ):
        object.__setattr__(authority, name, value)
    authority.__post_init__()
    return authority


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


__all__ = (
    "B11SourceExecutionAuthority",
    "bind_b11_source_execution_authority",
    "require_b11_source_execution_authority",
)
