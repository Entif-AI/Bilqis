"""Process-local hydration and execution-cache owner for accepted BAMF state."""
from __future__ import annotations

from dataclasses import dataclass
import json
from pathlib import Path
from threading import RLock

from bilqis_mlx.runtime.backbone_identity import execution_generation_digest

from .accepted_runtime import (
    _accepted_source_authority_registry, _published_in_memory_identity_locked,
    _read_accepted_locked,
)
from .codec import validate_bamf_bundle_custody
from .execution_cache import _new_execution_cache
from .publication import _pointer_lock, _read_pointer
from .records import CompleteStudent, canonical, invalid, sha


@dataclass(frozen=True)
class _AcceptedHydration:
    manifest_sha256: str
    pointer_sha256: str
    acceptance_sha256: str
    acceptance_file_sha256: str
    student: CompleteStudent
    correction_frontier_canonical: bytes


@dataclass(frozen=True)
class _AcceptedExecutionEntry:
    hydration: _AcceptedHydration
    cache: object
    registry: object | None
    registry_sha256: str | None
    generation_binding: str
    motif_manifest_sha256: str


def _acceptance_file_sha256(run_dir: Path, manifest_sha256: str) -> str:
    path = Path(run_dir) / "bamf-acceptance" / f"{manifest_sha256}.json"
    if path.is_symlink() or not path.is_file():
        invalid("BAMF_GENERATION_ACCEPTANCE_REQUIRED")
    return sha(path.read_bytes())


def _require_current_hydration(run_dir: Path, pointer: dict | None, hydration):
    if hydration is None:
        invalid("B13_EXECUTION_CACHE_REQUIRED")
    student = hydration.student
    if (pointer is None
            or sha(canonical(pointer)) != hydration.pointer_sha256
            or pointer.get("manifest_sha256") != hydration.manifest_sha256
            or pointer.get("run_id") != student.run_id
            or pointer.get("generation") != student.generation
            or pointer.get("acceptance_sha256") != hydration.acceptance_sha256
            or _acceptance_file_sha256(run_dir, hydration.manifest_sha256)
            != hydration.acceptance_file_sha256):
        invalid("B13_EXECUTION_CACHE_STALE")
    validate_bamf_bundle_custody(
        Path(run_dir) / "bamf-bundles" / hydration.manifest_sha256,
        expected_manifest_sha256=hydration.manifest_sha256)
    return hydration


def _current_registry(run_dir: Path, hydration):
    try:
        frontier = json.loads(hydration.correction_frontier_canonical)
    except (json.JSONDecodeError, UnicodeDecodeError):
        invalid("B13_EXECUTION_CACHE_REQUIRED")
    from .source_authority_custody import resolve_source_authority_registry
    return resolve_source_authority_registry(run_dir, frontier)


def _require_execution_entry(entry, registry) -> None:
    if entry is None:
        invalid("B13_EXECUTION_CACHE_REQUIRED")
    cache = entry.cache
    hydration = entry.hydration
    if (cache.accepted_manifest_sha256 != hydration.manifest_sha256
            or cache.run_id != hydration.student.run_id
            or cache.generation != hydration.student.generation
            or registry != entry.registry
            or cache._correction_registry is not entry.registry
            or cache.source_authority_registry_sha256 != entry.registry_sha256
            or cache.generation_binding != entry.generation_binding
            or cache.motif_manifest.digest != entry.motif_manifest_sha256):
        invalid("B13_EXECUTION_CACHE_REQUIRED")


def _new_hydration(run_dir: Path, pointer: dict, student: CompleteStudent):
    return _AcceptedHydration(
        pointer["manifest_sha256"], sha(canonical(pointer)),
        pointer["acceptance_sha256"],
        _acceptance_file_sha256(run_dir, pointer["manifest_sha256"]), student,
        canonical(dict(student.correction_frontier)))


def _new_execution_entry(run_dir: Path, hydration, registry):
    student = hydration.student
    binding = execution_generation_digest(
        student.retained_state.optimizer.parameters,
        spec=student.topology, extents=student.extents)
    cache = _new_execution_cache(
        run_id=student.run_id, generation=student.generation,
        accepted_manifest_sha256=hydration.manifest_sha256,
        generation_binding=binding,
        motif_manifest=student.retained_state.allocations.manifest,
        source_authority_registry_sha256=student.correction_frontier.get(
            "source_authority_registry_sha256"))
    object.__setattr__(cache, "_run_dir", run_dir)
    if registry is not None:
        object.__setattr__(cache, "_correction_registry", registry)
    return _AcceptedExecutionEntry(
        hydration, cache, registry,
        student.correction_frontier.get("source_authority_registry_sha256"),
        binding, student.retained_state.allocations.manifest.digest)


def _make_execution_cache_runtime():
    lock = RLock()
    hydrations, executions = {}, {}

    def current_hydration(run_dir: Path):
        run_dir = Path(run_dir).resolve()
        key = str(run_dir)
        with _pointer_lock(run_dir):
            pointer = _read_pointer(run_dir / "bamf-state.json")
            with lock:
                retained = hydrations.get(key)
            if (retained is not None and pointer is not None
                    and pointer.get("manifest_sha256") == retained.manifest_sha256):
                return _require_current_hydration(run_dir, pointer, retained)
            accepted_parent = (
                (retained.manifest_sha256, retained.student)
                if retained is not None else None)
            pointer, student = _read_accepted_locked(
                run_dir, accepted_parent=accepted_parent)
            _published_in_memory_identity_locked(
                run_dir, student, pointer, accepted_parent=accepted_parent,
                acceptance_verified=True)
            hydration = _new_hydration(run_dir, pointer, student)
            with lock:
                hydrations[key] = hydration
                executions.pop(key, None)
            return hydration

    def bind(run_dir: Path):
        run_dir = Path(run_dir).resolve()
        key = str(run_dir)
        hydration = current_hydration(run_dir)
        registry = _accepted_source_authority_registry(run_dir, hydration.student)
        with lock:
            retained = executions.get(key)
            if (retained is not None
                    and retained.hydration is hydration):
                _require_execution_entry(retained, registry)
                return retained.cache
            retained = _new_execution_entry(run_dir, hydration, registry)
            executions[key] = retained
            return retained.cache

    def require(cache):
        key = getattr(cache, "_run_dir", None)
        if key is None:
            invalid("B13_EXECUTION_CACHE_REQUIRED")
        run_dir = Path(key).resolve()
        hydration = current_hydration(run_dir)
        registry = _current_registry(run_dir, hydration)
        with lock:
            retained = executions.get(str(run_dir))
            if retained is None or retained.cache is not cache:
                invalid("B13_EXECUTION_CACHE_REQUIRED")
            _require_execution_entry(retained, registry)
        return cache

    def load(run_dir: Path):
        return current_hydration(run_dir).student

    def reset_for_tests():
        with lock:
            hydrations.clear()
            executions.clear()

    return bind, require, load, reset_for_tests


(
    bind_accepted_execution_cache,
    _require_owned_execution_cache,
    load_accepted_generation,
    _reset_execution_cache_owner_for_tests,
) = _make_execution_cache_runtime()


__all__ = ("bind_accepted_execution_cache", "load_accepted_generation")
