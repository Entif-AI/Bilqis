"""Accepted-generation custody for one process-live priority planning transaction."""
from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path

from bilqis_mlx.runtime.source_execution import SourceExecutionContext, _invalid_source_batch
from bilqis_mlx.semantics.domains import contract_digest


_PLANNING_ISSUER = object()


def _current_cache(source_context, parent):
    if type(source_context) is not SourceExecutionContext:
        _invalid_source_batch('BAMF_PRIORITY_SOURCE_CONTEXT_INVALID')
    from bilqis_mlx.runtime.bamf_bundle import CompleteStudent
    from bilqis_mlx.runtime.accepted_corrections import AcceptedRuntimeHost
    if type(parent) is not CompleteStudent:
        _invalid_source_batch('BAMF_PRIORITY_SOURCE_CONTEXT_INVALID')
    host = source_context._accepted_runtime_host
    if (type(host) is not AcceptedRuntimeHost
            or host.run_dir.resolve() != Path(source_context.run_dir).resolve()
            or host._accepted_cache is None):
        _invalid_source_batch('BAMF_PRIORITY_SOURCE_CONTEXT_INVALID')
    cache = host._accepted_cache
    if (cache.run_id != parent.run_id or cache.generation != parent.generation
            or not isinstance(getattr(cache, "_candidate_identity_sha256", None), str)):
        _invalid_source_batch('BAMF_PRIORITY_SOURCE_ACCEPTED_GENERATION_DRIFT')
    return cache


@dataclass(frozen=True, init=False, eq=False)
class PriorityPlanningGeneration:
    """Process-live proof for one immutable accepted-generation planning transaction."""

    accepted_manifest_sha256: str
    generation_binding: str
    acceptance_sha256: str
    acceptance_file_identity_sha256: str
    run_identity_sha256: str
    release_sha256: str
    correction_frontier_sha256: str
    feature_receipt_sha256: str
    parent_candidate_identity_sha256: str
    _run_dir: Path = field(repr=False)
    _source_context: object = field(repr=False, compare=False)
    _parent: object = field(repr=False, compare=False)
    _cache: object = field(repr=False, compare=False)
    _authenticated_features: object = field(repr=False, compare=False)
    _accepted_currentness: object = field(repr=False, compare=False)
    _target_registrar: object = field(repr=False, compare=False)
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
            or Path(source_context.run_dir).resolve() != binding._run_dir):
        _invalid_source_batch('BAMF_PRIORITY_PLANNING_GENERATION_INVALID')
    cache = binding._cache
    if (cache.accepted_manifest_sha256 != binding.accepted_manifest_sha256
            or cache.generation_binding != binding.generation_binding):
        _invalid_source_batch('BAMF_PRIORITY_PLANNING_GENERATION_DRIFT')
    if (source_context.release.release_sha256 != binding.release_sha256
            or contract_digest(parent.correction_frontier)
            != binding.correction_frontier_sha256
            or binding._authenticated_features.receipt.digest
            != binding.feature_receipt_sha256
            or binding._authenticated_features.receipt.generation_manifest_sha256
            != binding.accepted_manifest_sha256):
        _invalid_source_batch('BAMF_PRIORITY_PLANNING_GENERATION_DRIFT')
    from bilqis_mlx.runtime.bamf_bundle.currentness_transaction import (
        require_accepted_currentness,
    )
    require_accepted_currentness(binding._accepted_currentness, cache, parent)
    return cache, binding._authenticated_features


def bind_priority_planning_generation(source_context, parent, atlas_artifact_path):
    """Authenticate the accepted generation once before capability fan-out."""
    if type(source_context) is not SourceExecutionContext:
        _invalid_source_batch('BAMF_PRIORITY_SOURCE_CONTEXT_INVALID')
    source_context.require_accepted_runtime(source_context.run_dir)
    if getattr(parent, 'run_identity', None) is None:
        _invalid_source_batch('BAMF_PRIORITY_PLANNING_GENERATION_INVALID')
    run_dir = Path(source_context.run_dir).resolve()
    cache = _current_cache(source_context, parent)
    from bilqis_mlx.runtime.bamf_bundle.currentness_transaction import (
        bind_accepted_currentness_transaction,
    )
    metrics = getattr(source_context._accepted_runtime_host, "currentness_metrics", None)
    currentness = bind_accepted_currentness_transaction(
        run_dir, parent, cache, metrics=metrics)
    from bilqis_mlx.runtime.bamf_bundle import (
        AuthenticatedGenerationFeatureContext,
        authenticate_bamf_execution_feature_context,
    )
    authenticated = source_context._accepted_feature_context
    if authenticated is None:
        authenticated = authenticate_bamf_execution_feature_context(
            parent, atlas_artifact_path, source_context.run_dir)
    elif (type(authenticated) is not AuthenticatedGenerationFeatureContext
            or authenticated.selection.path != str(atlas_artifact_path)):
        _invalid_source_batch('BAMF_PRIORITY_PLANNING_GENERATION_INVALID')
    authenticated.__post_init__()
    if parent.run_identity is None:
        _invalid_source_batch('BAMF_PRIORITY_PLANNING_GENERATION_INVALID')
    from bilqis_mlx.runtime.accepted_correction_runtime import (
        _bind_accepted_target_registrar,
    )
    target_registrar = _bind_accepted_target_registrar(
        source_context._accepted_runtime_host, cache)
    result = object.__new__(PriorityPlanningGeneration)
    for name, value in (
        ('accepted_manifest_sha256', cache.accepted_manifest_sha256),
        ('generation_binding', cache.generation_binding),
        ('acceptance_sha256', currentness._acceptance_sha256),
        ('acceptance_file_identity_sha256',
         contract_digest(currentness._acceptance_identity)),
        ('run_identity_sha256', parent.run_identity.digest),
        ('release_sha256', source_context.release.release_sha256),
        ('correction_frontier_sha256', contract_digest(parent.correction_frontier)),
        ('feature_receipt_sha256', authenticated.receipt.digest),
        ('parent_candidate_identity_sha256', currentness.candidate_identity_sha256),
        ('_run_dir', run_dir),
        ('_source_context', source_context),
        ('_parent', parent),
        ('_cache', cache),
        ('_authenticated_features', authenticated),
        ('_accepted_currentness', currentness),
        ('_target_registrar', target_registrar),
        ('_issuance', _PLANNING_ISSUER),
    ):
        object.__setattr__(result, name, value)
    _require_planning_generation(result, source_context, parent)
    return result


__all__ = (
    'PriorityPlanningGeneration',
    'bind_priority_planning_generation',
)
