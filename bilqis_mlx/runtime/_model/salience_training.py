"""Revalidate signed C06 supervision at the C02/B11 execution boundary."""
from __future__ import annotations

from dataclasses import dataclass, replace

from bilqis_mlx.learning.atlas_salience import SalienceEvidence
from bilqis_mlx.learning.salience_contracts import AuthoritySnapshot, _invalid
from bilqis_mlx.runtime.salience_auxiliaries import RowSalienceBinding, attach_salience_labels
from bilqis_mlx.runtime.salience_evidence_owner import SalienceEvidenceArtifactOwner
from bilqis_mlx.runtime.source_execution import SourceExecutionContext, source_content_digest
from bilqis_mlx.runtime.atlas_training_contracts import _canonical_digest

SALIENCE_REQUEST_RECORD_WIDTH = 2
PORTABLE_SALIENCE_ROW_WIDTH = 3


@dataclass(frozen=True)
class SalienceLabelRequest:
    records: tuple
    snapshot: AuthoritySnapshot
    verify_existing: object

    def __post_init__(self):
        if (type(self.records) is not tuple or not self.records
                or any(type(item) is not tuple
                       or len(item) != SALIENCE_REQUEST_RECORD_WIDTH
                       or not isinstance(item[0], RowSalienceBinding)
                       or not isinstance(item[1], SalienceEvidence) for item in self.records)
                or len({item[0].row_id for item in self.records}) != len(self.records)
                or not isinstance(self.snapshot, AuthoritySnapshot)
                or not callable(self.verify_existing)):
            _invalid('BAMF_SALIENCE_REQUEST_INVALID')


def _current(source_context, request, batch):
    if type(source_context) is not SourceExecutionContext or type(request) is not SalienceLabelRequest:
        _invalid('BAMF_SALIENCE_REQUEST_INVALID')
    request.__post_init__()
    source_context.require_accepted_runtime(source_context.run_dir)
    from bilqis_mlx.runtime.bamf_bundle.accepted_runtime import _accepted_correction_registry
    cache, registry = _accepted_correction_registry(source_context.run_dir)
    _require_current_identity(cache, registry, request, batch)
    return cache


def _require_current_identity(cache, registry, request, batch):
    if (request.snapshot.registry.digest != registry.digest
            or batch.generation_binding != cache.generation_binding
            or any(context.generation_digest != cache.generation_binding
                   for context in request.snapshot.contexts)):
        _invalid('BAMF_SALIENCE_CURRENT_AUTHORITY_MISMATCH')


def _attach(batch, source_context, request):
    return attach_salience_labels(batch, source_context, request.records, request.snapshot,
                                  verify_existing=request.verify_existing)


@dataclass(frozen=True, init=False)
class SalienceSupervision:
    _batch: object
    _request: SalienceLabelRequest
    _source_context: SourceExecutionContext
    _owner: SalienceEvidenceArtifactOwner
    _compiled_rows: tuple

    def __init__(self, *args, **kwargs):
        _invalid('BAMF_SALIENCE_SUPERVISION_CALLER_CONSTRUCTION_FORBIDDEN')

    @property
    def artifact_nodes(self):
        self._owner.require()
        return self._owner.index.nodes

    @property
    def dependencies(self):
        node = self._owner.require()
        return tuple(sorted(set((node.reference, *node.immediate_dependencies))))

    def labels_for(self, compiled):
        cache = _current(self._source_context, self._request, self._batch)
        index = next((i for i, row in enumerate(self._compiled_rows)
                      if row.compiled is compiled.compiled
                      and row.training_authority is compiled.training_authority
                      and row.sources == compiled.sources), None)
        if index is None:
            _invalid('BAMF_SALIENCE_COMPILED_ROW_MISMATCH')
        labelled = _attach(self._batch, self._source_context, self._request)
        row = labelled.rows[index]
        provenance = row.provenance
        authority = compiled.training_authority
        source = compiled.sources[0].source_row
        expected_aux = _canonical_digest(row.auxiliaries) if row.auxiliaries else None
        if (authority is None or authority.training_batch_sha256 != labelled.authority_digest
                or authority.auxiliary_labels_sha256 != expected_aux
                or authority.release_sha256 != labelled.release_sha256
                or authority.generation_binding != cache.generation_binding
                or authority.delivery_capability != provenance.capability_id
                or authority.source_row_id != provenance.row_id
                or authority.source_row_sha256 != provenance.source_row_content_sha256
                or authority.source_family_id != provenance.source_family_id
                or source.get('id') != provenance.row_id
                or source.get('capability') != provenance.capability_id
                or source_content_digest((source,)) != provenance.source_row_content_sha256
                or compiled.compiled.compiled.rows != (row.model_input.prefix,)):
            _invalid('BAMF_SALIENCE_COMPILED_ROW_MISMATCH')
        self._source_context.register_compiled_batch(compiled)
        from bilqis_mlx.runtime.accepted_corrections import register_accepted_target
        register_accepted_target(self._source_context.run_dir, cache.accepted_manifest_sha256,
                                 'SALIENCE_EVIDENCE', self._owner)
        compiled.atlas_feature_artifact_owner.require(compiled.compiled.features)
        compiled.compiled.packed_frame_artifact_owner.require_row(row.model_input.prefix)
        self._owner.require()
        return {name: value for name, value, _, _ in row.auxiliaries
                if name in ('impact', 'exigency', 'novelty')}


@dataclass(frozen=True)
class PortableSalienceSupervision:
    """Coordinator-validated salience evidence safe for C08 rank transport."""

    rows: tuple
    dependencies: tuple
    artifact_nodes: tuple

    def __post_init__(self) -> None:
        if (type(self.rows) is not tuple
                or any(
                    type(item) is not tuple
                    or len(item) != PORTABLE_SALIENCE_ROW_WIDTH
                    for item in self.rows)
                or type(self.dependencies) is not tuple
                or type(self.artifact_nodes) is not tuple):
            _invalid('BAMF_SALIENCE_PORTABLE_SUPERVISION_INVALID')

    def labels_for(self, compiled):
        sources = getattr(compiled, "sources", ())
        if type(sources) is not tuple or len(sources) != 1:
            _invalid('BAMF_SALIENCE_COMPILED_ROW_MISMATCH')
        row = sources[0].source_row
        identity = row.get("id") if isinstance(row, dict) else None
        digest = source_content_digest((row,)) if isinstance(row, dict) else None
        labels = next((
            labels for row_id, row_sha256, labels in self.rows
            if row_id == identity and row_sha256 == digest), None)
        if labels is None:
            _invalid('BAMF_SALIENCE_COMPILED_ROW_MISMATCH')
        return dict(labels)


def portable_salience_supervision(supervision, compiled_rows):
    """Freeze owner-validated labels and evidence before entering rank workers."""
    if supervision is None:
        return None
    if type(supervision) is not SalienceSupervision or type(compiled_rows) is not tuple:
        _invalid('BAMF_SALIENCE_PORTABLE_SUPERVISION_INVALID')
    rows = []
    for compiled in compiled_rows:
        source = compiled.sources[0].source_row
        rows.append((
            source["id"], source_content_digest((source,)),
            tuple(sorted(supervision.labels_for(compiled).items())),
        ))
    result = PortableSalienceSupervision(
        tuple(rows), tuple(supervision.dependencies), tuple(supervision.artifact_nodes))
    result.__post_init__()
    return result


def prepare_salience_training(prepared, source_context, request):
    """Bind verified row labels to actual C02/B11 inputs under accepted custody."""
    cache = _current(source_context, request, prepared.training_batch)
    from bilqis_mlx.runtime.factory_training_bridge import PreparedFactoryTrainingBatch
    from bilqis_mlx.runtime.atlas_training_authority import bind_compiled_training_batch
    from bilqis_mlx.runtime.accepted_corrections import register_accepted_target
    if type(prepared) is not PreparedFactoryTrainingBatch:
        _invalid('BAMF_SALIENCE_PREPARED_INPUT_INVALID')
    prepared.__post_init__()
    labelled = _attach(prepared.training_batch, source_context, request)
    row_deps = tuple((row.provenance.row_id, row.provenance.immediate_dependencies)
                     for row in labelled.rows if row.provenance.row_id in
                     {binding.row_id for binding, _ in request.records})
    owner = SalienceEvidenceArtifactOwner(request.records, row_deps)
    register_accepted_target(source_context.run_dir, cache.accepted_manifest_sha256,
                             'SALIENCE_EVIDENCE', owner)
    owner.require()
    rebound = tuple(bind_compiled_training_batch(
        labelled, original.compiled, original.sources, original.feature_schema,
        active_semantic_rows=original.active_semantic_rows, row_index=index,
        source_execution_authority=original.source_execution_authority)
        for index, original in enumerate(prepared.compiled_rows))
    for compiled in rebound:
        source_context.register_compiled_batch(compiled)
    result = replace(prepared, training_batch=labelled, compiled_rows=rebound)
    supervision = object.__new__(SalienceSupervision)
    for name, value in (('_batch', prepared.training_batch), ('_request', request),
                        ('_source_context', source_context), ('_owner', owner),
                        ('_compiled_rows', rebound)):
        object.__setattr__(supervision, name, value)
    return result, supervision
