"""Portable B13 witness and process-local cache for C08 rank execution."""
from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
import weakref

from bilqis_mlx.data_plane import SHA256_HEX_LENGTH
from bilqis_mlx.errors import ErrorBus, SCHOOL
from bilqis_mlx.learning.atlas_engram import MotifManifest
from bilqis_mlx.runtime.backbone_identity import (
    issue_execution_generation_binding, require_execution_generation_binding,
)


_ISSUER = object()


def _invalid(reason: str) -> None:
    ErrorBus.Raise(SCHOOL.STATE.HISTORICAL_ARTIFACT_INVALID, reason=reason)


def _digest(value: object) -> bool:
    return (
        isinstance(value, str)
        and len(value) == SHA256_HEX_LENGTH
        and all(char in "0123456789abcdef" for char in value)
    )


@dataclass(frozen=True)
class DistributedExecutionCacheWitness:
    """Portable B13-derived facts; never optimizer or publication authority."""

    run_id: str
    generation: int
    accepted_manifest_sha256: str
    generation_binding: str
    motif_manifest: MotifManifest
    schema_version: str = "bilqis.mlx.b13-distributed-execution-cache-witness/v1"

    def __post_init__(self) -> None:
        if (not isinstance(self.run_id, str) or not self.run_id
                or type(self.generation) is not int or self.generation < 0
                or not _digest(self.accepted_manifest_sha256)
                or not _digest(self.generation_binding)
                or type(self.motif_manifest) is not MotifManifest
                or self.schema_version
                != "bilqis.mlx.b13-distributed-execution-cache-witness/v1"):
            _invalid("B13_DISTRIBUTED_EXECUTION_CACHE_WITNESS_INVALID")


@dataclass(frozen=True, init=False)
class DistributedExecutionCache:
    """Rank-local read authority reconstructed from a coordinator witness."""

    run_id: str
    generation: int
    accepted_manifest_sha256: str
    generation_binding: str
    motif_manifest: MotifManifest
    _execution_binding: object = field(repr=False, compare=False)
    _motif_artifact_owners: dict = field(repr=False, compare=False)
    _run_dir: Path | None = field(repr=False, compare=False)
    _issuance: object = field(repr=False, compare=False)

    def __init__(self, *args, **kwargs):
        _invalid("B13_DISTRIBUTED_EXECUTION_CACHE_CALLER_CONSTRUCTION_FORBIDDEN")

    def __post_init__(self) -> None:
        if (self._issuance is not _ISSUER
                or not isinstance(self.run_id, str) or not self.run_id
                or type(self.generation) is not int or self.generation < 0
                or not _digest(self.accepted_manifest_sha256)
                or not _digest(self.generation_binding)
                or type(self.motif_manifest) is not MotifManifest
                or self._run_dir is not None):
            _invalid("B13_DISTRIBUTED_EXECUTION_CACHE_INVALID")


def issue_distributed_execution_cache_witness(cache, parameters, *, spec, extents):
    """Project immutable B13 execution facts from a live coordinator cache."""
    from bilqis_mlx.runtime.bamf_bundle.execution_cache import (
        CandidateExecutionCache, bind_execution_generation,
        require_accepted_execution_cache, require_candidate_execution_cache,
    )
    if type(cache) is CandidateExecutionCache:
        execution = require_candidate_execution_cache(cache)
        accepted = require_accepted_execution_cache(execution._accepted_cache)
    else:
        accepted = require_accepted_execution_cache(cache)
        execution = accepted
    binding = bind_execution_generation(execution, parameters, spec=spec, extents=extents)
    return DistributedExecutionCacheWitness(
        accepted.run_id, accepted.generation, accepted.accepted_manifest_sha256,
        binding.generation_digest, accepted.motif_manifest)


def bind_distributed_execution_cache(
        witness: DistributedExecutionCacheWitness, parameters, *, spec, extents
) -> DistributedExecutionCache:
    """Mint rank-local read authority after revalidating exact parameter identity."""
    if type(witness) is not DistributedExecutionCacheWitness:
        _invalid("B13_DISTRIBUTED_EXECUTION_CACHE_WITNESS_INVALID")
    witness.__post_init__()
    if witness.motif_manifest.digest != extents.motif_key_map_digest:
        _invalid("B13_DISTRIBUTED_EXECUTION_CACHE_DRIFT")
    try:
        binding = issue_execution_generation_binding(
            parameters, spec=spec, extents=extents,
            expected_generation=witness.generation_binding)
    except Exception:
        _invalid("B13_DISTRIBUTED_EXECUTION_CACHE_DRIFT")
    result = object.__new__(DistributedExecutionCache)
    for name, value in (
            ("run_id", witness.run_id), ("generation", witness.generation),
            ("accepted_manifest_sha256", witness.accepted_manifest_sha256),
            ("generation_binding", witness.generation_binding),
            ("motif_manifest", witness.motif_manifest),
            ("_execution_binding", binding),
            ("_motif_artifact_owners", weakref.WeakValueDictionary()),
            ("_run_dir", None), ("_issuance", _ISSUER)):
        object.__setattr__(result, name, value)
    result.__post_init__()
    return result


def require_distributed_execution_cache(cache) -> DistributedExecutionCache:
    if type(cache) is not DistributedExecutionCache:
        _invalid("B13_DISTRIBUTED_EXECUTION_CACHE_REQUIRED")
    cache.__post_init__()
    return cache


def require_distributed_execution_binding(cache, parameters, *, spec, extents):
    cache = require_distributed_execution_cache(cache)
    try:
        return require_execution_generation_binding(
            cache._execution_binding, parameters, spec=spec, extents=extents)
    except Exception:
        _invalid("B13_DISTRIBUTED_EXECUTION_CACHE_DRIFT")


__all__ = (
    "DistributedExecutionCache", "DistributedExecutionCacheWitness",
    "bind_distributed_execution_cache", "issue_distributed_execution_cache_witness",
    "require_distributed_execution_binding", "require_distributed_execution_cache",
)
