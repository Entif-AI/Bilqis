"""Accepted-generation custody for one process-live priority planning transaction."""
from __future__ import annotations

from dataclasses import dataclass, field
import hashlib
from pathlib import Path

from bilqis_mlx.runtime.source_execution import SourceExecutionContext, _invalid_source_batch
from bilqis_mlx.semantics.domains import contract_digest


_PLANNING_ISSUER = object()


def _current_cache(source_context, parent):
    if type(source_context) is not SourceExecutionContext:
        _invalid_source_batch('BAMF_PRIORITY_SOURCE_CONTEXT_INVALID')
    from bilqis_mlx.runtime.bamf_bundle import CompleteStudent
    from bilqis_mlx.runtime.bamf_bundle.accepted_runtime import _published_in_memory_identity
    from bilqis_mlx.runtime.accepted_corrections import AcceptedRuntimeHost
    from bilqis_mlx.runtime.bamf_bundle.execution_cache import bind_execution_generation
    if type(parent) is not CompleteStudent:
        _invalid_source_batch('BAMF_PRIORITY_SOURCE_CONTEXT_INVALID')
    host = source_context._accepted_runtime_host
    if (type(host) is not AcceptedRuntimeHost
            or host.run_dir.resolve() != Path(source_context.run_dir).resolve()
            or host._accepted_cache is None):
        _invalid_source_batch('BAMF_PRIORITY_SOURCE_CONTEXT_INVALID')
    cache = host._accepted_cache
    _published_in_memory_identity(source_context.run_dir, parent)
    generation = bind_execution_generation(
        cache, parent.retained_state.optimizer.parameters,
        spec=parent.topology, extents=parent.extents).generation_digest
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
            group,
            id(values),
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
    release_sha256: str
    correction_frontier_sha256: str
    feature_receipt_sha256: str
    _run_dir: Path = field(repr=False)
    _source_context: object = field(repr=False, compare=False)
    _parent: object = field(repr=False, compare=False)
    _cache: object = field(repr=False, compare=False)
    _authenticated_features: object = field(repr=False, compare=False)
    _bundle_currentness: object = field(repr=False, compare=False)
    _source_authority_currentness: object = field(repr=False, compare=False)
    _target_registrar: object = field(repr=False, compare=False)
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
    run_dir = binding._run_dir
    pointer, acceptance_file_sha256 = _planning_pointer_snapshot(run_dir)
    if (pointer.get('run_id') != cache.run_id
            or pointer.get('generation') != cache.generation
            or pointer.get('manifest_sha256') != binding.accepted_manifest_sha256
            or pointer.get('acceptance_sha256') != binding.acceptance_sha256
            or acceptance_file_sha256 != binding.acceptance_file_sha256):
        _invalid_source_batch('BAMF_PRIORITY_PLANNING_GENERATION_DRIFT')
    if (source_context.release.release_sha256 != binding.release_sha256
            or contract_digest(parent.correction_frontier)
            != binding.correction_frontier_sha256
            or binding._authenticated_features.receipt.digest
            != binding.feature_receipt_sha256
            or binding._authenticated_features.receipt.generation_manifest_sha256
            != binding.accepted_manifest_sha256):
        _invalid_source_batch('BAMF_PRIORITY_PLANNING_GENERATION_DRIFT')
    from bilqis_mlx.runtime.bamf_bundle.bundle_currentness import (
        require_bamf_bundle_currentness,
    )
    require_bamf_bundle_currentness(binding._bundle_currentness)
    from bilqis_mlx.runtime.bamf_bundle.source_authority_custody import (
        require_source_authority_currentness,
    )
    require_source_authority_currentness(
        binding._source_authority_currentness, run_dir,
        parent.correction_frontier, cache._correction_registry)
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
    from bilqis_mlx.runtime.bamf_bundle.bundle_currentness import (
        bind_bamf_bundle_currentness,
    )
    bundle_currentness = bind_bamf_bundle_currentness(
        run_dir / 'bamf-bundles' / cache.accepted_manifest_sha256,
        expected_manifest_sha256=cache.accepted_manifest_sha256)
    from bilqis_mlx.runtime.bamf_bundle.source_authority_custody import (
        bind_source_authority_currentness,
    )
    source_authority_currentness = bind_source_authority_currentness(
        run_dir, parent.correction_frontier, cache._correction_registry)
    from bilqis_mlx.runtime.accepted_correction_runtime import (
        _bind_accepted_target_registrar,
    )
    target_registrar = _bind_accepted_target_registrar(
        source_context._accepted_runtime_host, cache)
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
        ('release_sha256', source_context.release.release_sha256),
        ('correction_frontier_sha256', contract_digest(parent.correction_frontier)),
        ('feature_receipt_sha256', authenticated.receipt.digest),
        ('_run_dir', run_dir),
        ('_source_context', source_context),
        ('_parent', parent),
        ('_cache', cache),
        ('_authenticated_features', authenticated),
        ('_bundle_currentness', bundle_currentness),
        ('_source_authority_currentness', source_authority_currentness),
        ('_target_registrar', target_registrar),
        ('_retained_guard', _retained_object_guard(parent)),
        ('_issuance', _PLANNING_ISSUER),
    ):
        object.__setattr__(result, name, value)
    _require_planning_generation(result, source_context, parent)
    return result


__all__ = (
    'PriorityPlanningGeneration',
    'bind_priority_planning_generation',
)
