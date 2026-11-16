"""Source-owned rows prepared before a C03 priority policy is selected."""
from __future__ import annotations

from dataclasses import dataclass, field
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
    _materialized: dict = field(repr=False, compare=False)
    _qualification_owner: object = field(repr=False, compare=False)
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
                or type(self._materialized) is not dict
                or any(key != 'value' for key in self._materialized)
                or self._qualification_owner is None
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

    def require_qualified_current(self, source_context, parent, *, prepared_rows=None):
        """Verify source qualification/currentness without rebuilding source content."""
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
        source_context.require_bound_rows(rows, self.source_authority)
        if _canonical_rows(rows) != self._rows_json:
            _invalid_source_batch('BAMF_PRIORITY_SOURCE_OFFER_ROWS_DRIFT')
        self._qualification_owner.require()
        return rows

    def require_current(self, source_context, parent, *, prepared_rows=None):
        """Materialize the selected source once, then revalidate its cached owners."""
        from .priority_source_materialization import (
            prepare_priority_source_materialization,
        )
        return prepare_priority_source_materialization(
            self, source_context, parent, prepared_rows=prepared_rows)


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
    rows, authority = source_context.draw_bound_rows(
        seed=source_seed, capability=capability, each=source_each)
    wire = _canonical_rows(rows)
    if len(rows) != source_each:
        _invalid_source_batch('BAMF_PRIORITY_SOURCE_ROWS_INVALID')
    if authenticated.receipt.generation_manifest_sha256 != cache.accepted_manifest_sha256:
        _invalid_source_batch('BAMF_PRIORITY_SOURCE_ACCEPTED_GENERATION_DRIFT')
    from bilqis_mlx.runtime.salience_evidence_owner import SalienceEvidenceArtifactOwner
    qualification_owner = SalienceEvidenceArtifactOwner.for_source_qualification(
        authority, rows, authenticated.features.semantic_release)
    offer = object.__new__(PreparedPrioritySourceOffer)
    for name, value in (
        ('source_authority', authority), ('accepted_manifest_sha256', cache.accepted_manifest_sha256),
        ('generation_binding', cache.generation_binding), ('release_sha256', source_context.release.release_sha256),
        ('capability_id', capability), ('source_seed', source_seed), ('source_each', source_each),
        ('source_family_id', authority.source_family_id),
        ('source_binding_digest', contract_digest(source_context.release.source_bindings.by_capability[capability])),
        ('_rows_json', wire), ('_rows_sha256', hashlib.sha256(wire.encode('utf-8')).hexdigest()),
        ('_run_dir', Path(source_context.run_dir).resolve()), ('_materialized', {}),
        ('_qualification_owner', qualification_owner),
        ('_planning_generation', planning_generation),
        ('_issuance', _ISSUER)):
        object.__setattr__(offer, name, value)
    planning_generation._target_registrar.register(
        'SALIENCE_EVIDENCE', qualification_owner)
    offer.require_qualified_current(source_context, parent)
    return offer
