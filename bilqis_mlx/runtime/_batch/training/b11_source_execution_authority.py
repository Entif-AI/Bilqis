"""Process-local B11 source authority bound before neural execution."""
from __future__ import annotations

from contextlib import contextmanager
from contextvars import ContextVar
from dataclasses import asdict, dataclass, field, replace

from bilqis_mlx.errors import ErrorBus, SCHOOL
from bilqis_mlx.learning._engram.atlas_engram_source_context import (
    qualify_source_motif_context,
)
from bilqis_mlx.learning._engram.atlas_engram_identity import MotifFrameInput
from bilqis_mlx.learning.frame_embeddings.requests import FeatureRequest
from bilqis_mlx.learning.source_atoms.inputs import SourceAtomRow
from bilqis_mlx.semantics.atlas_projection import FrozenAtlasSnapshot
from bilqis_mlx.semantics.atlas_features import AtlasFeatures
from bilqis_mlx.semantics.atlas_features.formal import source_qualified_feature_row
from bilqis_mlx.semantics.atlas_features.records import FeatureRow
from bilqis_mlx.semantics.context_eligibility import (
    ApprovedContextProjection, ContextHold, SourceFrontier, TaskScope,
    project_context,
)
from bilqis_mlx.semantics.domains import contract_digest
from bilqis_mlx.semantics.frame_compiler import (
    CompiledFrameBatch, FrameCompilerConfig, PositionKind,
)
from bilqis_mlx.semantics.frame_schema import FrameInstance
from bilqis_mlx.learning.atlas_engram_reads.source import (
    _schema_grant_live, schema_source_handle,
)
from bilqis_mlx.semantics.source_atom_binding import SourceAtomHandoff
from bilqis_mlx.source_adapters.atom_binding import (
    _build_source_atom_handoff_from_snapshot,
)


_ISSUER = object()
_MOTIF_FEATURE_ROW_WIDTH = 3
_MOTIF_FEATURE_VALUE_INDEX = 2
_LAUNCH_TRUST = ContextVar("b11_source_authority_launch_trust", default=())


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
            or any(type(item) is not tuple or len(item) != 2
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


def _bind_source_handoff(compiled_row, config, source, snapshot):
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
    return handoff


def _bind_motif_context(
    compiled_row, config, source, source_adapter, snapshot,
):
    task_scope = replace(config.task, causal_prefix_end=compiled_row.visible_end)
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
    return task_scope, projection, motifs, frontier


def _motif_schema_map(motifs):
    schemas = {}

    def collect(item):
        previous = schemas.get(item.frame.occurrence_id)
        if previous is not None and previous != item.schema:
            _invalid("B11_SOURCE_EXECUTION_MOTIF_SCHEMA_DRIFT")
        schemas[item.frame.occurrence_id] = item.schema
        for child in item.children:
            collect(child)

    for motif in motifs:
        collect(motif)
    return schemas


def _bind_motif_feature_rows(projection, motifs, features, source):
    schemas = _motif_schema_map(motifs)
    rows = []
    for envelope in projection.envelopes:
        if type(envelope.frame) is not FrameInstance:
            continue
        if schemas.get(envelope.frame.occurrence_id) is None:
            _invalid("B11_SOURCE_EXECUTION_MOTIF_SCHEMA_MISSING")
        for binding in envelope.frame.bindings:
            if binding.concept is None:
                continue
            member = next((
                item for item in envelope.members if item.key == binding.key
            ), None)
            if member is None:
                _invalid("B11_SOURCE_EXECUTION_MOTIF_MEMBER_MISSING")
            feature_row = source_qualified_feature_row(
                features, binding.concept, binding.role_id, envelope.frame,
                envelope.scope, source.selection,
                invalid=lambda: _invalid(
                    "B11_SOURCE_EXECUTION_FEATURE_AUTHORITY_INVALID"))
            rows.append(
                (envelope.frame_handle, member.source_handle, feature_row))
    return tuple(rows)


def _bind_motif_read_context(projection, motifs, frontier, task_scope):
    schemas = _motif_schema_map(motifs)
    grants = {item.source_handle: item for item in frontier.grants}
    dependencies = {}
    liveness = {}
    for envelope in projection.envelopes:
        if type(envelope.frame) is not FrameInstance:
            continue
        schema = schemas.get(envelope.frame.occurrence_id)
        if schema is None:
            _invalid("B11_SOURCE_EXECUTION_MOTIF_SCHEMA_MISSING")
        handle = schema_source_handle(schema)
        grant = grants.get(handle)
        dependencies[handle] = None if grant is None else asdict(grant)
        liveness[handle] = _schema_grant_live(
            schema, envelope, task_scope, frontier)
    schema_rights = tuple(
        (handle, dependencies[handle]) for handle in sorted(dependencies))
    context_digest = (
        projection.cache_key("B08_SCHEMA_RIGHTS_V1", schema_rights)
        if schema_rights else projection.digest)
    return context_digest, tuple(sorted(liveness.items()))


def _bind_motif_execution_projection(
    compiled_row, config, motif_projection, frontier, task_scope,
):
    handles = tuple(
        position.frame_handle for position in compiled_row.positions
        if position.kind is PositionKind.CLOSURE)
    if not handles or len(set(handles)) != len(handles):
        _invalid("B11_SOURCE_EXECUTION_MOTIF_PROJECTION_INVALID")
    handle_set = set(handles)
    envelopes = tuple(
        envelope for envelope in motif_projection.envelopes
        if envelope.frame_handle in handle_set)
    if len(envelopes) != len(handles):
        _invalid("B11_SOURCE_EXECUTION_MOTIF_PROJECTION_INVALID")
    projection = project_context(
        envelopes, task_scope, frontier, config.policy)
    if (type(projection) is not ApprovedContextProjection
            or projection.digest != compiled_row.context_digest):
        _invalid("B11_SOURCE_EXECUTION_MOTIF_PROJECTION_INVALID")
    return projection


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

def require_b11_source_feature_row(
    authority,
    request: FeatureRequest,
) -> FeatureRow:
    """Return one bind-time qualified A06 row only from an issued authority."""
    if (
        type(authority) is not B11SourceExecutionAuthority
        or authority._issuance is not _ISSUER
        or type(request) is not FeatureRequest
    ):
        _invalid("B11_SOURCE_EXECUTION_FEATURE_AUTHORITY_INVALID")
    request.__post_init__()
    if request.projection.digest != authority.motif_projection.digest:
        _invalid("B11_SOURCE_EXECUTION_FEATURE_AUTHORITY_INVALID")
    matches = tuple(
        row for frame_handle, member_handle, row in authority.motif_feature_rows
        if (frame_handle, member_handle)
        == (request.frame_handle, request.member_handle)
    )
    if len(matches) != 1:
        _invalid("B11_SOURCE_EXECUTION_FEATURE_AUTHORITY_INVALID")
    row = matches[0]
    if (
        row.semantic_id != request.concept.semantic_id
        or row.abi_index != request.concept.abi_index
        or row.role_id != request.role_id
        or row.schema_id != request.schema_id
        or row.scope != request.scope
    ):
        _invalid("B11_SOURCE_EXECUTION_FEATURE_AUTHORITY_INVALID")
    return row


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


def b11_source_authority_launch_trusted(
    authority, compiled_row, config, source,
) -> bool:
    return any(
        item[0] is authority and item[1] is compiled_row
        and item[2] is config and item[3] is source
        for item in _LAUNCH_TRUST.get())


def b11_compiled_input_launch_trusted(compiled) -> bool:
    records = _LAUNCH_TRUST.get()
    if not records:
        return False
    rows = getattr(getattr(compiled, "compiled", None), "rows", ())
    configs = getattr(compiled, "compiler_configs", ())
    return bool(rows) and len(rows) == len(configs) and all(
        any(record[1] is row and record[2] is config for record in records)
        for row, config in zip(rows, configs))


@contextmanager
def b11_source_authority_launch_epoch(batches):
    """Validate exact bound source rows once, then trust them for one launch."""
    records = []
    for batch in batches:
        authority = getattr(batch, "source_execution_authority", None)
        if authority is None:
            continue
        row = batch.compiled.compiled.rows[0]
        config = batch.compiled.compiler_configs[0]
        source = batch.sources[0]
        require_b11_source_execution_authority(
            authority, row, config, source)
        records.append((authority, row, config, source))
    token = _LAUNCH_TRUST.set(tuple(records))
    try:
        yield
    finally:
        _LAUNCH_TRUST.reset(token)


__all__ = (
    "B11SourceExecutionAuthority",
    "bind_b11_source_execution_authority",
    "b11_compiled_input_launch_trusted",
    "b11_source_authority_launch_epoch",
    "b11_source_authority_launch_trusted",
    "require_b11_source_execution_authority",
    "require_b11_source_feature_row",
)
