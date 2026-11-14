"""Source-owned rows prepared before a C03 priority policy is selected."""
from __future__ import annotations

from dataclasses import dataclass, field, replace
import hashlib
import json
import math
from pathlib import Path

from bilqis_mlx.runtime.source_execution import SourceBatchAuthority, SourceExecutionContext, _invalid_source_batch
from bilqis_mlx.semantics.domains import contract_digest

_ISSUER = object()
_PLANNING_ISSUER = object()


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


def _current_cache(source_context, parent):
    if type(source_context) is not SourceExecutionContext:
        _invalid_source_batch('BAMF_PRIORITY_SOURCE_CONTEXT_INVALID')
    from bilqis_mlx.runtime.bamf_bundle import CompleteStudent
    from bilqis_mlx.runtime.bamf_bundle.accepted_runtime import _published_in_memory_identity
    from bilqis_mlx.runtime.accepted_corrections import AcceptedRuntimeHost
    from bilqis_mlx.runtime.backbone_identity import execution_generation_digest
    if type(parent) is not CompleteStudent:
        _invalid_source_batch('BAMF_PRIORITY_SOURCE_CONTEXT_INVALID')
    host = source_context._accepted_runtime_host
    if (type(host) is not AcceptedRuntimeHost
            or host.run_dir.resolve() != Path(source_context.run_dir).resolve()
            or host._accepted_cache is None):
        _invalid_source_batch('BAMF_PRIORITY_SOURCE_CONTEXT_INVALID')
    cache = host._accepted_cache
    _published_in_memory_identity(source_context.run_dir, parent)
    generation = execution_generation_digest(
        parent.retained_state.optimizer.parameters, spec=parent.topology, extents=parent.extents)
    if (cache.run_id != parent.run_id or cache.generation != parent.generation
            or cache.generation_binding != generation):
        _invalid_source_batch('BAMF_PRIORITY_SOURCE_ACCEPTED_GENERATION_DRIFT')
    return cache


def _retained_object_guard(parent):
    """Detect in-process accepted-state replacement without rehashing tensor bytes."""
    state = parent.retained_state
    optimizer = state.optimizer
    groups = []
    for group in ('parameters', 'm', 'v', 'update_counts'):
        values = getattr(optimizer, group)
        groups.append((
            group, id(values),
            tuple((name, id(value)) for name, value in sorted(values.items())),
        ))
    return (id(state), id(optimizer), state.optimizer_step, tuple(groups))


def _planning_pointer_snapshot(run_dir: Path):
    from bilqis_mlx.runtime.bamf_bundle.publication import _pointer_lock, _read_pointer

    run_dir = Path(run_dir).resolve()
    with _pointer_lock(run_dir):
        pointer = _read_pointer(run_dir / 'bamf-state.json')
        if not isinstance(pointer, dict):
            _invalid_source_batch('BAMF_PRIORITY_PLANNING_GENERATION_INVALID')
        manifest = pointer.get('manifest_sha256')
        if not isinstance(manifest, str):
            _invalid_source_batch('BAMF_PRIORITY_PLANNING_GENERATION_INVALID')
        acceptance_path = run_dir / 'bamf-acceptance' / f'{manifest}.json'
        if acceptance_path.is_symlink() or not acceptance_path.is_file():
            _invalid_source_batch('BAMF_PRIORITY_PLANNING_GENERATION_INVALID')
        acceptance_file_sha256 = hashlib.sha256(acceptance_path.read_bytes()).hexdigest()
    return pointer, acceptance_file_sha256


@dataclass(frozen=True, init=False, eq=False)
class PriorityPlanningGeneration:
    """Process-live proof for one immutable accepted-generation planning transaction."""

    accepted_manifest_sha256: str
    generation_binding: str
    acceptance_sha256: str
    acceptance_file_sha256: str
    run_identity_sha256: str
    _run_dir: Path = field(repr=False)
    _source_context: object = field(repr=False, compare=False)
    _parent: object = field(repr=False, compare=False)
    _cache: object = field(repr=False, compare=False)
    _authenticated_features: object = field(repr=False, compare=False)
    _retained_guard: object = field(repr=False, compare=False)
    _issuance: object = field(repr=False, compare=False)

    def __init__(self, *args, **kwargs):
        _invalid_source_batch('BAMF_PRIORITY_PLANNING_CALLER_CONSTRUCTION_FORBIDDEN')


def _require_planning_generation(binding, source_context, parent):
    from bilqis_mlx.runtime.bamf_bundle import CompleteStudent
    if (type(binding) is not PriorityPlanningGeneration
            or getattr(binding, '_issuance', None) is not _PLANNING_ISSUER
            or binding._source_context is not source_context
            or binding._parent is not parent
            or type(parent) is not CompleteStudent
            or parent.run_identity is None
            or parent.run_identity.digest != binding.run_identity_sha256
            or _retained_object_guard(parent) != binding._retained_guard
            or Path(source_context.run_dir).resolve() != binding._run_dir):
        _invalid_source_batch('BAMF_PRIORITY_PLANNING_GENERATION_INVALID')
    cache = binding._cache
    if (cache.accepted_manifest_sha256 != binding.accepted_manifest_sha256
            or cache.generation_binding != binding.generation_binding):
        _invalid_source_batch('BAMF_PRIORITY_PLANNING_GENERATION_DRIFT')
    from bilqis_mlx.runtime.bamf_bundle.codec import validate_bamf_bundle_custody
    run_dir = binding._run_dir
    pointer, acceptance_file_sha256 = _planning_pointer_snapshot(run_dir)
    if (pointer.get('run_id') != cache.run_id
            or pointer.get('generation') != cache.generation
            or pointer.get('manifest_sha256') != binding.accepted_manifest_sha256
            or pointer.get('acceptance_sha256') != binding.acceptance_sha256
            or acceptance_file_sha256 != binding.acceptance_file_sha256):
        _invalid_source_batch('BAMF_PRIORITY_PLANNING_GENERATION_DRIFT')
    validate_bamf_bundle_custody(
        run_dir / 'bamf-bundles' / binding.accepted_manifest_sha256,
        expected_manifest_sha256=binding.accepted_manifest_sha256)
    from bilqis_mlx.runtime.bamf_bundle.source_authority_custody import (
        resolve_source_authority_registry,
    )
    if resolve_source_authority_registry(run_dir, parent.correction_frontier) != cache._correction_registry:
        _invalid_source_batch('BAMF_PRIORITY_PLANNING_GENERATION_DRIFT')
    return cache, binding._authenticated_features


def bind_priority_planning_generation(source_context, parent, atlas_artifact_path):
    """Authenticate the accepted generation once before capability fan-out."""
    if type(source_context) is not SourceExecutionContext:
        _invalid_source_batch('BAMF_PRIORITY_SOURCE_CONTEXT_INVALID')
    source_context.require_accepted_runtime(source_context.run_dir)
    if getattr(parent, 'run_identity', None) is None:
        _invalid_source_batch('BAMF_PRIORITY_PLANNING_GENERATION_INVALID')
    run_dir = Path(source_context.run_dir).resolve()
    before_pointer, before_acceptance_file = _planning_pointer_snapshot(run_dir)
    cache = _current_cache(source_context, parent)
    from bilqis_mlx.runtime.bamf_bundle import authenticate_bamf_execution_feature_context
    authenticated = authenticate_bamf_execution_feature_context(
        parent, atlas_artifact_path, source_context.run_dir)
    after_pointer, after_acceptance_file = _planning_pointer_snapshot(run_dir)
    if (before_pointer != after_pointer
            or before_acceptance_file != after_acceptance_file
            or after_pointer.get('run_id') != cache.run_id
            or after_pointer.get('generation') != cache.generation
            or after_pointer.get('manifest_sha256') != cache.accepted_manifest_sha256
            or not isinstance(after_pointer.get('acceptance_sha256'), str)
            or parent.run_identity is None):
        _invalid_source_batch('BAMF_PRIORITY_PLANNING_GENERATION_INVALID')
    result = object.__new__(PriorityPlanningGeneration)
    for name, value in (
        ('accepted_manifest_sha256', cache.accepted_manifest_sha256),
        ('generation_binding', cache.generation_binding),
        ('acceptance_sha256', after_pointer['acceptance_sha256']),
        ('acceptance_file_sha256', after_acceptance_file),
        ('run_identity_sha256', parent.run_identity.digest),
        ('_run_dir', run_dir), ('_source_context', source_context), ('_parent', parent),
        ('_cache', cache), ('_authenticated_features', authenticated),
        ('_retained_guard', _retained_object_guard(parent)),
        ('_issuance', _PLANNING_ISSUER),
    ):
        object.__setattr__(result, name, value)
    _require_planning_generation(result, source_context, parent)
    return result


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

    def require_current(self, source_context, parent):
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
        rows = self.rows()
        current = source_context.bind_rows(rows, seed=self.source_seed,
            capability=self.capability_id, each=self.source_each)
        if (current != self.source_authority or _canonical_rows(tuple(source_context.draw_rows(
                seed=self.source_seed, capability=self.capability_id, each=self.source_each)))
                != self._rows_json):
            _invalid_source_batch('BAMF_PRIORITY_SOURCE_OFFER_ROWS_DRIFT')
        from bilqis_mlx.runtime.accepted_corrections import register_accepted_target
        for kind, owner in (('ATLAS_FEATURE', self._feature_owner), ('PACKED_FRAME', self._packed_owner),
                            ('SALIENCE_EVIDENCE', self._source_owner)):
            register_accepted_target(source_context.run_dir, cache.accepted_manifest_sha256, kind, owner)
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
    from bilqis_mlx.runtime.accepted_corrections import register_accepted_target
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
        register_accepted_target(source_context.run_dir, cache.accepted_manifest_sha256, kind, owner)
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
