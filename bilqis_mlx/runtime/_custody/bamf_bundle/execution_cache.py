"""B13-issued retained cache authority consumed by the B11 forward owner."""
from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from threading import RLock
import weakref

from bilqis_mlx.data_plane import SHA256_HEX_LENGTH
from bilqis_mlx.errors import ErrorBus, SCHOOL
from bilqis_mlx.learning.atlas_engram import MotifManifest
from bilqis_mlx.runtime.backbone_identity import (
    execution_generation_object_key, issue_execution_generation_binding,
    require_execution_generation_binding,
)


_CANDIDATE_CACHE_ISSUER = object()


def _invalid(reason: str) -> None:
    ErrorBus.Raise(SCHOOL.STATE.HISTORICAL_ARTIFACT_INVALID, reason=reason)


def _digest(value: object) -> bool:
    return (
        isinstance(value, str)
        and len(value) == SHA256_HEX_LENGTH
        and all(char in "0123456789abcdef" for char in value)
    )


@dataclass(frozen=True, init=False)
class AcceptedExecutionCache:
    """A motif manifest authenticated against one accepted B13 generation."""

    run_id: str
    generation: int
    accepted_manifest_sha256: str
    generation_binding: str
    motif_manifest: MotifManifest
    source_authority_registry_sha256: str | None
    schema_version: str = "bilqis.mlx.b13-accepted-execution-cache/v1"
    _motif_artifact_owners: dict = field(init=False, repr=False, compare=False)
    _run_dir: Path | None = field(init=False, repr=False, compare=False)
    _correction_registry: object | None = field(init=False, repr=False, compare=False)
    _source_authority: object | None = field(init=False, repr=False, compare=False)
    _execution_bindings: dict = field(init=False, repr=False, compare=False)
    _execution_binding_lock: object = field(init=False, repr=False, compare=False)
    _candidate_identity_sha256: str | None = field(init=False, repr=False, compare=False)
    _currentness_transaction: object | None = field(init=False, repr=False, compare=False)
    _retention_protection_plan: object | None = field(
        init=False, repr=False, compare=False)

    def __init__(self, *args, **kwargs):
        _invalid("B13_EXECUTION_CACHE_CALLER_CONSTRUCTION_FORBIDDEN")

    def __post_init__(self) -> None:
        if (
            not isinstance(self.run_id, str) or not self.run_id
            or type(self.generation) is not int or self.generation < 0
            or not _digest(self.accepted_manifest_sha256)
            or not _digest(self.generation_binding)
            or type(self.motif_manifest) is not MotifManifest
            or (self.source_authority_registry_sha256 is not None
                and not _digest(self.source_authority_registry_sha256))
            or self.schema_version
            != "bilqis.mlx.b13-accepted-execution-cache/v1"
        ):
            _invalid("B13_EXECUTION_CACHE_INVALID")


@dataclass(frozen=True, init=False)
class CandidateExecutionCache:
    """B13-authenticated cache view for one unpublished candidate transaction."""

    run_id: str
    generation: int
    accepted_manifest_sha256: str
    generation_binding: str
    motif_manifest: MotifManifest
    _accepted_cache: AcceptedExecutionCache = field(repr=False, compare=False)
    _parent: object = field(repr=False, compare=False)
    _candidate: object = field(repr=False, compare=False)
    _spec: object = field(repr=False, compare=False)
    _extents: object = field(repr=False, compare=False)
    _execution_binding: object = field(repr=False, compare=False)
    _issuance: object = field(repr=False, compare=False)

    def __init__(self, *args, **kwargs):
        _invalid("B13_CANDIDATE_EXECUTION_CACHE_CALLER_CONSTRUCTION_FORBIDDEN")


def _new_execution_cache(
    *,
    run_id: str,
    generation: int,
    accepted_manifest_sha256: str,
    generation_binding: str,
    motif_manifest: MotifManifest,
    source_authority_registry_sha256: str | None = None,
) -> AcceptedExecutionCache:
    cache = object.__new__(AcceptedExecutionCache)
    for name, value in (
        ("run_id", run_id),
        ("generation", generation),
        ("accepted_manifest_sha256", accepted_manifest_sha256),
        ("generation_binding", generation_binding),
        ("motif_manifest", motif_manifest),
        ("source_authority_registry_sha256", source_authority_registry_sha256),
        ("schema_version", "bilqis.mlx.b13-accepted-execution-cache/v1"),
        ("_motif_artifact_owners", weakref.WeakValueDictionary()),
        ("_run_dir", None),
        ("_correction_registry", None),
        ("_source_authority", None),
        ("_execution_bindings", {}),
        ("_execution_binding_lock", RLock()),
        ("_candidate_identity_sha256", None),
        ("_currentness_transaction", None),
        ("_retention_protection_plan", None),
        ("_retention_source_rows", {}),
    ):
        object.__setattr__(cache, name, value)
    cache.__post_init__()
    return cache


def bind_candidate_execution_cache(cache, parent, candidate, *, spec, extents):
    """Bind speculative neural weights to the current accepted cache authority."""
    accepted = require_accepted_execution_cache(cache)
    from bilqis_mlx.learning.atlas_candidate import CandidateTransaction
    from bilqis_mlx.runtime.bamf_bundle.records import CompleteStudent
    if (type(parent) is not CompleteStudent
            or type(candidate) is not CandidateTransaction
            or candidate.parent is not parent.retained_state):
        _invalid("B13_CANDIDATE_EXECUTION_CACHE_REQUIRED")
    candidate.__post_init__()
    custody = candidate.parent.custody
    if (custody is None
            or custody.run_id != accepted.run_id
            or custody.generation != accepted.generation
            or custody.manifest_sha256 != accepted.accepted_manifest_sha256
            or candidate.allocations.manifest.digest != accepted.motif_manifest.digest
            or custody.topology_digest != spec.digest
            or custody.extents_digest != extents.digest):
        _invalid("B13_CANDIDATE_EXECUTION_CACHE_DRIFT")
    binding = issue_execution_generation_binding(
        candidate.optimizer.parameters, spec=spec, extents=extents)
    result = object.__new__(CandidateExecutionCache)
    for name, value in (
            ("run_id", accepted.run_id), ("generation", accepted.generation),
            ("accepted_manifest_sha256", accepted.accepted_manifest_sha256),
            ("generation_binding", binding.generation_digest),
            ("motif_manifest", accepted.motif_manifest),
            ("_accepted_cache", accepted), ("_parent", parent),
            ("_candidate", candidate),
            ("_spec", spec), ("_extents", extents),
            ("_execution_binding", binding),
            ("_issuance", _CANDIDATE_CACHE_ISSUER)):
        object.__setattr__(result, name, value)
    return result


def require_candidate_execution_cache(cache) -> CandidateExecutionCache:
    if type(cache) is not CandidateExecutionCache:
        _invalid("B13_CANDIDATE_EXECUTION_CACHE_REQUIRED")
    accepted = require_accepted_execution_cache(cache._accepted_cache)
    candidate = cache._candidate
    candidate.__post_init__()
    custody = candidate.parent.custody
    if (cache._issuance is not _CANDIDATE_CACHE_ISSUER
            or accepted is not cache._accepted_cache
            or candidate.parent is not cache._parent.retained_state
            or custody is None
            or cache.run_id != accepted.run_id
            or cache.generation != accepted.generation
            or cache.accepted_manifest_sha256 != accepted.accepted_manifest_sha256
            or cache.motif_manifest.digest != accepted.motif_manifest.digest
            or candidate.allocations.manifest.digest != accepted.motif_manifest.digest
            or custody.topology_digest != cache._spec.digest
            or custody.extents_digest != cache._extents.digest
            or cache.generation_binding != cache._execution_binding.generation_digest):
        _invalid("B13_CANDIDATE_EXECUTION_CACHE_DRIFT")
    try:
        require_execution_generation_binding(
            cache._execution_binding, candidate.optimizer.parameters,
            spec=cache._spec, extents=cache._extents)
    except Exception:
        _invalid("B13_CANDIDATE_EXECUTION_CACHE_DRIFT")
    return cache


def bind_execution_generation(cache, parameters, *, spec, extents):
    """Return the one process-local generation proof for this immutable state."""
    from .distributed_execution_cache import (
        DistributedExecutionCache, require_distributed_execution_binding,
    )
    if type(cache) is DistributedExecutionCache:
        return require_distributed_execution_binding(
            cache, parameters, spec=spec, extents=extents)
    if type(cache) is CandidateExecutionCache:
        candidate = require_candidate_execution_cache(cache)
        try:
            return require_execution_generation_binding(
                candidate._execution_binding, parameters, spec=spec, extents=extents)
        except Exception:
            _invalid("B13_CANDIDATE_EXECUTION_CACHE_DRIFT")
    accepted = require_accepted_execution_cache(cache)
    key = execution_generation_object_key(parameters, spec=spec, extents=extents)
    with accepted._execution_binding_lock:
        binding = accepted._execution_bindings.get(key)
        if binding is None:
            try:
                binding = issue_execution_generation_binding(
                    parameters, spec=spec, extents=extents,
                    expected_generation=accepted.generation_binding)
            except Exception:
                _invalid("B13_EXECUTION_CACHE_GENERATION_MISMATCH")
            accepted._execution_bindings[key] = binding
        try:
            return require_execution_generation_binding(
                binding, parameters, spec=spec, extents=extents)
        except Exception:
            _invalid("B13_EXECUTION_CACHE_GENERATION_MISMATCH")


def require_accepted_execution_cache(cache) -> AcceptedExecutionCache:
    if type(cache) is not AcceptedExecutionCache:
        _invalid("B13_EXECUTION_CACHE_REQUIRED")
    cache.__post_init__()
    currentness = getattr(cache, "_currentness_transaction", None)
    if currentness is not None:
        from .currentness_transaction import require_accepted_currentness
        require_accepted_currentness(currentness, cache)
        return cache
    from bilqis_mlx.runtime.bamf_bundle.accepted_runtime import (
        _require_owned_execution_cache,
    )
    return _require_owned_execution_cache(cache)


def bind_motif_artifact_owner(cache, compiled):
    """Bind mutable C09 hold state to one immutable compiled-frame identity."""
    from .distributed_execution_cache import (
        DistributedExecutionCache, require_distributed_execution_cache,
    )
    distributed = type(cache) is DistributedExecutionCache
    cache = (require_distributed_execution_cache(cache) if distributed
             else require_accepted_execution_cache(cache))
    from bilqis_mlx.runtime.atlas_motif_owner import MotifArtifactOwner
    packed_owner = compiled.packed_frame_artifact_owner
    key = packed_owner.cache_identity
    owner = cache._motif_artifact_owners.get(key)
    if owner is not None and not owner.accepts_packed_owner(packed_owner):
        owner = None
    if owner is None:
        owner = MotifArtifactOwner(cache, compiled)
        cache._motif_artifact_owners[key] = owner
    if not distributed and cache._run_dir is not None:
        from bilqis_mlx.runtime.accepted_corrections import (
            register_accepted_target,
        )
        register_accepted_target(
            cache._run_dir, cache.accepted_manifest_sha256,
            "MOTIF", owner,
        )
    owner.require(cache, compiled)
    return owner


from .distributed_execution_cache import (
    DistributedExecutionCache, DistributedExecutionCacheWitness,
    bind_distributed_execution_cache, issue_distributed_execution_cache_witness,
    require_distributed_execution_cache,
)


__all__ = (
    "AcceptedExecutionCache", "CandidateExecutionCache",
    "DistributedExecutionCache", "DistributedExecutionCacheWitness",
    "bind_distributed_execution_cache",
    "bind_candidate_execution_cache", "bind_execution_generation",
    "bind_motif_artifact_owner", "issue_distributed_execution_cache_witness",
    "require_accepted_execution_cache", "require_candidate_execution_cache",
    "require_distributed_execution_cache",
)
