"""Process-local accepted execution-cache ownership and currentness."""
from __future__ import annotations

from dataclasses import dataclass
import json
from pathlib import Path
from threading import RLock

from bilqis_mlx.runtime.backbone_identity import execution_generation_digest

from .codec import validate_bamf_bundle_custody
from .execution_cache import _new_execution_cache
from .publication import _pointer_lock, _read_pointer
from .records import canonical, invalid, sha


def _accepted_source_authority_registry(run_dir: Path, student):
    from .source_authority_custody import resolve_source_authority_registry
    return resolve_source_authority_registry(
        run_dir, student.correction_frontier)


@dataclass(frozen=True)
class _AcceptedExecutionCacheEntry:
    manifest_sha256: str
    pointer_sha256: str
    acceptance_sha256: str
    acceptance_file_sha256: str
    cache: object
    registry: object | None
    registry_sha256: str | None
    generation_binding: str
    motif_manifest_sha256: str
    correction_frontier_canonical: bytes


def _require_retained_entry(entry, cache, current_registry) -> None:
    if (entry is None
            or entry.manifest_sha256 != cache.accepted_manifest_sha256
            or entry.cache is not cache
            or current_registry != entry.registry
            or cache._correction_registry is not entry.registry
            or cache.source_authority_registry_sha256 != entry.registry_sha256
            or cache.generation_binding != entry.generation_binding
            or cache.motif_manifest.digest != entry.motif_manifest_sha256):
        invalid("B13_EXECUTION_CACHE_REQUIRED")


def _acceptance_file_sha256(run_dir: Path, manifest_sha256: str) -> str:
    path = Path(run_dir) / "bamf-acceptance" / f"{manifest_sha256}.json"
    if path.is_symlink() or not path.is_file():
        invalid("BAMF_GENERATION_ACCEPTANCE_REQUIRED")
    return sha(path.read_bytes())


def _fast_retained_registry(run_dir: Path, pointer: dict, entry):
    """Revalidate immutable accepted custody without rebuilding numerical state."""
    if entry is None:
        invalid("B13_EXECUTION_CACHE_REQUIRED")
    cache = entry.cache
    if (pointer is None
            or sha(canonical(pointer)) != entry.pointer_sha256
            or pointer.get("manifest_sha256") != entry.manifest_sha256
            or pointer.get("run_id") != cache.run_id
            or pointer.get("generation") != cache.generation
            or pointer.get("acceptance_sha256") != entry.acceptance_sha256
            or _acceptance_file_sha256(run_dir, entry.manifest_sha256)
            != entry.acceptance_file_sha256):
        invalid("B13_EXECUTION_CACHE_STALE")
    validate_bamf_bundle_custody(
        Path(run_dir) / "bamf-bundles" / entry.manifest_sha256,
        expected_manifest_sha256=entry.manifest_sha256)
    from .source_authority_custody import resolve_source_authority_registry
    try:
        frontier = json.loads(entry.correction_frontier_canonical)
    except (json.JSONDecodeError, UnicodeDecodeError):
        invalid("B13_EXECUTION_CACHE_REQUIRED")
    return resolve_source_authority_registry(run_dir, frontier)


def _reuse_retained_cache(retained, identity, generation_binding, student, registry):
    cache = retained.cache
    if (cache.run_id != identity.run_id
            or cache.generation != identity.generation
            or cache.generation_binding != generation_binding
            or cache.source_authority_registry_sha256
            != student.correction_frontier.get("source_authority_registry_sha256")
            or cache.motif_manifest.digest
            != student.retained_state.allocations.manifest.digest):
        invalid("BAMF_EXECUTION_CACHE_CUSTODY_DRIFT")
    cached_identity = getattr(cache, "_candidate_identity_sha256", None)
    if cached_identity is None:
        object.__setattr__(cache, "_candidate_identity_sha256",
                           identity.candidate_identity_sha256)
    elif cached_identity != identity.candidate_identity_sha256:
        invalid("BAMF_EXECUTION_CACHE_CUSTODY_DRIFT")
    if registry is not None:
        if cache._correction_registry is None:
            object.__setattr__(cache, "_correction_registry", registry)
        elif cache._correction_registry != registry:
            invalid("BAMF_C09_CORRECTION_AUTHORITY_DRIFT")
    if (cache._correction_registry is not retained.registry
            or cache.source_authority_registry_sha256 != retained.registry_sha256
            or cache.generation_binding != retained.generation_binding
            or cache.motif_manifest.digest != retained.motif_manifest_sha256):
        invalid("BAMF_EXECUTION_CACHE_CUSTODY_DRIFT")
    return cache


def _require_current_execution_cache(run_dir: Path, cache, entries, lock):
    key = str(run_dir)
    with _pointer_lock(run_dir):
        pointer = _read_pointer(run_dir / "bamf-state.json")
        if (pointer is None
                or pointer.get("manifest_sha256") != cache.accepted_manifest_sha256
                or pointer.get("run_id") != cache.run_id
                or pointer.get("generation") != cache.generation):
            invalid("B13_EXECUTION_CACHE_STALE")
        with lock:
            retained = entries.get(key)
        current_registry = _fast_retained_registry(
            run_dir, pointer, retained)
        with lock:
            _require_retained_entry(entries.get(key), cache, current_registry)
    return cache


def _reuse_current_execution_cache(run_dir: Path, pointer: dict | None, entries, lock):
    key = str(run_dir)
    with lock:
        retained = entries.get(key)
    if (retained is None or pointer is None
            or pointer.get("manifest_sha256") != retained.manifest_sha256):
        return None
    current_registry = _fast_retained_registry(run_dir, pointer, retained)
    with lock:
        _require_retained_entry(entries.get(key), retained.cache, current_registry)
    return retained.cache


def _install_execution_cache(
        run_dir: Path, pointer: dict, student, identity, generation_binding: str,
        registry, entries, lock):
    key = str(run_dir)
    acceptance_file_sha256 = _acceptance_file_sha256(
        run_dir, identity.manifest_sha256)
    correction_frontier_canonical = canonical(dict(student.correction_frontier))
    with lock:
        retained = entries.get(key)
        if (retained is not None
                and retained.manifest_sha256 == identity.manifest_sha256):
            return _reuse_retained_cache(
                retained, identity, generation_binding, student, registry)
        cache = _new_execution_cache(
            run_id=identity.run_id,
            generation=identity.generation,
            accepted_manifest_sha256=identity.manifest_sha256,
            generation_binding=generation_binding,
            motif_manifest=student.retained_state.allocations.manifest,
            source_authority_registry_sha256=student.correction_frontier.get(
                "source_authority_registry_sha256"),
        )
        object.__setattr__(cache, "_run_dir", run_dir)
        object.__setattr__(
            cache, "_candidate_identity_sha256", identity.candidate_identity_sha256)
        if registry is not None:
            object.__setattr__(cache, "_correction_registry", registry)
        entries[key] = _AcceptedExecutionCacheEntry(
            manifest_sha256=identity.manifest_sha256,
            pointer_sha256=sha(canonical(pointer)),
            acceptance_sha256=pointer["acceptance_sha256"],
            acceptance_file_sha256=acceptance_file_sha256,
            cache=cache,
            registry=registry,
            registry_sha256=student.correction_frontier.get(
                "source_authority_registry_sha256"),
            generation_binding=generation_binding,
            motif_manifest_sha256=student.retained_state.allocations.manifest.digest,
            correction_frontier_canonical=correction_frontier_canonical,
        )
        return cache


def _make_execution_cache_runtime():
    """Close cache installation over the one canonical live-pointer verifier."""
    lock = RLock()
    entries = {}

    def require(cache):
        key = getattr(cache, "_run_dir", None)
        if key is None:
            invalid("B13_EXECUTION_CACHE_REQUIRED")
        return _require_current_execution_cache(
            Path(key).resolve(), cache, entries, lock)

    def bind(run_dir: Path, *, metrics=None):
        run_dir = Path(run_dir).resolve()
        with _pointer_lock(run_dir):
            pointer = _read_pointer(run_dir / "bamf-state.json")
            retained = _reuse_current_execution_cache(run_dir, pointer, entries, lock)
            if retained is not None:
                return retained
            from .accepted_runtime import (
                _published_in_memory_identity_locked, _read_accepted_locked,
            )
            pointer, student = _read_accepted_locked(run_dir)
            identity = _published_in_memory_identity_locked(
                run_dir, student, pointer)
            if metrics is not None:
                metrics.increment("full_candidate_identity_hashes")
            generation_binding = execution_generation_digest(
                student.retained_state.optimizer.parameters,
                spec=student.topology,
                extents=student.extents,
            )
            registry = _accepted_source_authority_registry(run_dir, student)
            return _install_execution_cache(
                run_dir, pointer, student, identity, generation_binding,
                registry, entries, lock)

    def reset_for_tests():
        with lock:
            entries.clear()

    return bind, require, reset_for_tests


(
    bind_accepted_execution_cache,
    _require_owned_execution_cache,
    _reset_execution_cache_owner_for_tests,
) = _make_execution_cache_runtime()


def _accepted_correction_registry(run_dir: Path):
    """Resolve C09 verifier material only from current accepted B13 custody."""
    from bilqis_mlx.runtime.atlas_revalidation import SourceAuthorityRegistry
    from bilqis_mlx.runtime.atlas_source_authority import (
        _provision_source_authority_runtime,
    )
    cache = bind_accepted_execution_cache(run_dir)
    bound = cache._correction_registry
    if (not isinstance(bound, SourceAuthorityRegistry)
            or cache.source_authority_registry_sha256 is None
            or bound.digest != cache.source_authority_registry_sha256):
        invalid("BAMF_C09_CORRECTION_AUTHORITY_REQUIRED")
    _provision_source_authority_runtime(cache)
    return cache, bound


__all__ = (
    "_accepted_correction_registry",
    "_require_owned_execution_cache",
    "_reset_execution_cache_owner_for_tests",
    "bind_accepted_execution_cache",
)
