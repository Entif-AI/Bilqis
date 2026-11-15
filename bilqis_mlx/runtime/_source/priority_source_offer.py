"""Source-owned rows prepared before a C03 priority policy is selected."""
from __future__ import annotations

from dataclasses import dataclass, field, replace
import hashlib
import json
import math
from pathlib import Path

from bilqis_mlx.runtime.source_execution import SourceBatchAuthority, SourceExecutionContext, _invalid_source_batch
from bilqis_mlx.semantics.domains import contract_digest
from .priority_planning_generation import (
    PriorityPlanningGeneration,
    _PLANNING_ISSUER,
    _current_cache,
    _require_planning_generation,
    bind_priority_planning_generation,
)

_ISSUER = object()


def _json_value(value):
    if value is None or type(value) in (str, bool, int):
        return True
    if type(value) is float:
        return math.isfinite(value)
    if type(value) is list:
        return all(_json_value(item) for item in value)
    if type(value) is dict:
        return all(type(key) is str and _json_value(item) for key, item in value.items())
    return False


def _canonical_rows(rows):
    if (type(rows) is not tuple or not rows
            or any(type(row) is not dict or not _json_value(row) for row in rows)):
        _invalid_source_batch('BAMF_PRIORITY_SOURCE_ROWS_INVALID')
    try:
        wire = json.dumps(rows, sort_keys=True, separators=(',', ':'), ensure_ascii=False, allow_nan=False)
        wire.encode('utf-8')
    except (TypeError, ValueError, UnicodeError):
        _invalid_source_batch('BAMF_PRIORITY_SOURCE_ROWS_INVALID')
    return wire


def _decode_rows(wire):
    try:
        rows = tuple(json.loads(wire))
        if _canonical_rows(rows) != wire:
            _invalid_source_batch('BAMF_PRIORITY_SOURCE_ROWS_INVALID')
        return rows
    except (ValueError, TypeError):
        _invalid_source_batch('BAMF_PRIORITY_SOURCE_ROWS_INVALID')


@dataclass(frozen=True, init=False, eq=False)
class PreparedPrioritySourceOffer:
    source_authority: SourceBatchAuthority
    accepted_manifest_sha256: str
    generation_binding: str
    release_sha256: str
    capability_id: str
    source_seed: int
    source_each: int
    source_family_id: str
    source_binding_digest: str
    _rows_json: str = field(repr=False)
    _rows_sha256: str = field(repr=False)
    _run_dir: Path = field(repr=False)
    _features: object = field(repr=False)
    _prefixes: tuple = field(repr=False)
    _feature_owner: object = field(repr=False)
    _packed_owner: object = field(repr=False)
    _source_owner: object = field(repr=False)
    _planning_generation: PriorityPlanningGeneration = field(repr=False, compare=False)
    _issuance: object = field(repr=False)

    def __init__(self, *args, **kwargs):
        _invalid_source_batch('BAMF_PRIORITY_SOURCE_OFFER_CALLER_CONSTRUCTION_FORBIDDEN')

    def _validate(self):
        if (getattr(self, '_issuance', None) is not _ISSUER
                or type(self.source_authority) is not SourceBatchAuthority
                or hashlib.sha256(self._rows_json.encode('utf-8')).hexdigest() != self._rows_sha256
                or self.source_authority.release_sha256 != self.release_sha256
                or self.source_authority.capability_id != self.capability_id
                or self.source_authority.seed != self.source_seed
                or self.source_authority.each != self.source_each
                or self.source_authority.source_family_id != self.source_family_id
                or type(self._planning_generation) is not PriorityPlanningGeneration
                or getattr(self._planning_generation, '_issuance', None) is not _PLANNING_ISSUER):
            _invalid_source_batch('BAMF_PRIORITY_SOURCE_OFFER_INVALID')
        self.source_authority.__post_init__()

    def rows(self):
        self._validate()
        return _decode_rows(self._rows_json)

    def require_current_parent(self, source_context):
        self._validate()
        parent = self._planning_generation._parent
        cache, _authenticated = _require_planning_generation(
            self._planning_generation, source_context, parent)
        return parent, cache

    def require_current(self, source_context, parent, *, prepared_rows=None):
        self._validate()
        cache, _authenticated = _require_planning_generation(
            self._planning_generation, source_context, parent)
        if (Path(source_context.run_dir).resolve() != self._run_dir
                or cache.accepted_manifest_sha256 != self.accepted_manifest_sha256
                or cache.generation_binding != self.generation_binding
                or source_context.release.release_sha256 != self.release_sha256
                or self.capability_id not in source_context.release.execution_plan.capability_map
                or contract_digest(source_context.release.source_bindings.by_capability[self.capability_id])
                != self.source_binding_digest):
            _invalid_source_batch('BAMF_PRIORITY_SOURCE_OFFER_STALE')
        rows = self.rows() if prepared_rows is None else tuple(prepared_rows)
        current = source_context.bind_rows(rows, seed=self.source_seed,
            capability=self.capability_id, each=self.source_each)
        # bind_rows() already performs the authoritative owner redraw and rejects
        # source-content drift. The second identical draw that used to live here
        # repeated that source work at every offer boundary; the exact supplied or
        # retained row representation is still checked against the sealed offer.
        if (current != self.source_authority
                or _canonical_rows(rows) != self._rows_json):
            _invalid_source_batch('BAMF_PRIORITY_SOURCE_OFFER_ROWS_DRIFT')
        for kind, owner in (('ATLAS_FEATURE', self._feature_owner), ('PACKED_FRAME', self._packed_owner),
                            ('SALIENCE_EVIDENCE', self._source_owner)):
            self._planning_generation._target_registrar.register(kind, owner)
        self._feature_owner.require(self._features)
        self._source_owner.require()
        for prefix in self._prefixes:
            self._packed_owner.require_row(prefix)


def prepare_priority_source_offer(source_context, parent, atlas_artifact_path, *,
                                  capability, source_seed, source_each,
                                  planning_generation=None):
    """Issue a current, source-qualified offer without constructing a teacher visit."""
    if planning_generation is None:
        planning_generation = bind_priority_planning_generation(
            source_context, parent, atlas_artifact_path)
    cache, authenticated = _require_planning_generation(
        planning_generation, source_context, parent)
    if (not isinstance(capability, str) or not capability
            or type(source_seed) is not int or source_seed < 0
            or type(source_each) is not int or source_each < 1
            or capability not in source_context.release.execution_plan.capability_map
            or source_context.source_root is None):
        _invalid_source_batch('BAMF_PRIORITY_SOURCE_OFFER_INPUT_INVALID')
    rows = tuple(source_context.draw_rows(seed=source_seed, capability=capability, each=source_each))
    wire = _canonical_rows(rows)
    if len(rows) != source_each:
        _invalid_source_batch('BAMF_PRIORITY_SOURCE_ROWS_INVALID')
    authority = source_context.bind_rows(rows, seed=source_seed, capability=capability, each=source_each)
    from bilqis_mlx.runtime.factory_training_bridge import _prepare_factory_source_rows
    from bilqis_mlx.runtime.atlas_artifact_owner import AtlasFeatureArtifactOwner
    from bilqis_mlx.runtime.atlas_packed_frame_owner import PackedFrameArtifactOwner
    from bilqis_mlx.runtime.salience_evidence_owner import SalienceEvidenceArtifactOwner
    from bilqis_mlx.runtime.training_input_authority import require_source_lineage
    from bilqis_mlx.semantics.frame_compiler import CompiledFrameRows, compile_prefix, validate_partial_visible_forest
    from bilqis_mlx.source_adapters.atoms.admission import authorize_public_formal_prefix
    if authenticated.receipt.generation_manifest_sha256 != cache.accepted_manifest_sha256:
        _invalid_source_batch('BAMF_PRIORITY_SOURCE_ACCEPTED_GENERATION_DRIFT')
    _, _, source_rows = _prepare_factory_source_rows(
        source_context, authenticated, rows, capability=capability,
        source_seed=source_seed, source_each=source_each)
    if len({tuple(item.row['tokens']) for item in source_rows}) != len(rows):
        _invalid_source_batch('FACTORY_TRAINING_AMBIGUOUS_SOURCE_PREFIX')
    prefixes = []
    for item in source_rows:
        visible = tuple(item.row['tokens'])
        if item.projection is not None:
            require_source_lineage(item.ast, item.projection.envelopes, visible, source_context.graph)
        elif item.ast.frames:
            _invalid_source_batch('CONTEXT_SOURCE_FRAMES_REQUIRED')
        config = item.config if item.projection is None else replace(item.config, approved=item.projection)
        prefix = compile_prefix(item.ast, len(visible), item.task.semantic_release, config)
        config = authorize_public_formal_prefix(item.ast, prefix, config)
        if item.projection is not None:
            validate_partial_visible_forest(prefix, item.ast, config)
        prefixes.append(prefix)
    prefixes = tuple(prefixes)
    width = max(len(prefix.positions) for prefix in prefixes)
    compiled = CompiledFrameRows(prefixes,
        tuple(prefix.positions + (None,) * (width - len(prefix.positions)) for prefix in prefixes),
        tuple((True,) * len(prefix.positions) + (False,) * (width - len(prefix.positions)) for prefix in prefixes))
    feature_owner = AtlasFeatureArtifactOwner(authenticated.features, authenticated.schema)
    packed_owner = PackedFrameArtifactOwner(compiled)
    source_owner = SalienceEvidenceArtifactOwner.for_source_offer(authority, rows, prefixes)
    for kind, owner in (('ATLAS_FEATURE', feature_owner), ('PACKED_FRAME', packed_owner),
                        ('SALIENCE_EVIDENCE', source_owner)):
        planning_generation._target_registrar.register(kind, owner)
    offer = object.__new__(PreparedPrioritySourceOffer)
    for name, value in (
        ('source_authority', authority), ('accepted_manifest_sha256', cache.accepted_manifest_sha256),
        ('generation_binding', cache.generation_binding), ('release_sha256', source_context.release.release_sha256),
        ('capability_id', capability), ('source_seed', source_seed), ('source_each', source_each),
        ('source_family_id', authority.source_family_id),
        ('source_binding_digest', contract_digest(source_context.release.source_bindings.by_capability[capability])),
        ('_rows_json', wire), ('_rows_sha256', hashlib.sha256(wire.encode('utf-8')).hexdigest()),
        ('_run_dir', Path(source_context.run_dir).resolve()), ('_features', authenticated.features),
        ('_prefixes', prefixes), ('_feature_owner', feature_owner), ('_packed_owner', packed_owner),
        ('_source_owner', source_owner),
        ('_planning_generation', planning_generation),
        ('_issuance', _ISSUER)):
        object.__setattr__(offer, name, value)
    offer.require_current(source_context, parent)
    return offer
