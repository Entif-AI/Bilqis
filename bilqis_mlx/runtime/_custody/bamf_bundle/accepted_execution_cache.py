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
from .bundle_currentness import (
    bind_bamf_bundle_currentness, require_bamf_bundle_currentness,
)
from .execution_cache import _new_execution_cache
from .publication import _pointer_read_lock, _read_pointer
from .records import CompleteStudent, canonical, invalid, sha


def _require_initial_foundation_authority(
        run_dir: Path, student: CompleteStudent) -> None:
    """Cold-bind a current BAMF lineage to its signed generation-zero release."""
    if student.run_identity is None:
        return
    from .publication.factory_release import require_initial_factory_release
    require_initial_factory_release(run_dir, student)


@dataclass(frozen=True)
class _AcceptedHydration:
    manifest_sha256: str
    pointer_sha256: str
    acceptance_sha256: str
    acceptance_file_sha256: str
    student: CompleteStudent
    correction_frontier_canonical: bytes
    candidate_identity_sha256: str


@dataclass(frozen=True)
class _AcceptedExecutionEntry:
    hydration: _AcceptedHydration
    cache: object
    registry: object | None
    registry_sha256: str | None
    generation_binding: str
    motif_manifest_sha256: str


_PUBLICATION_PARENT_ISSUER = object()


@dataclass(frozen=True, init=False, eq=False)
class AcceptedPublicationParent:
    """Non-serializable proof that one hydrated parent is current B13 custody."""

    manifest_sha256: str
    acceptance_sha256: str
    student: CompleteStudent
    _pointer_sha256: str
    _acceptance_file_sha256: str
    _hydration: _AcceptedHydration
    _currentness: object
    _issuance: object

    def __init__(self, *args, **kwargs):
        invalid("B13_PUBLICATION_PARENT_REQUIRED")


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
    _require_initial_foundation_authority(run_dir, student)
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
            or cache._candidate_identity_sha256
            != hydration.candidate_identity_sha256
            or registry != entry.registry
            or cache._correction_registry is not entry.registry
            or cache.source_authority_registry_sha256 != entry.registry_sha256
            or cache.generation_binding != entry.generation_binding
            or cache.motif_manifest.digest != entry.motif_manifest_sha256):
        invalid("B13_EXECUTION_CACHE_REQUIRED")


def _new_hydration(
        run_dir: Path, pointer: dict, student: CompleteStudent,
        candidate_identity_sha256: str):
    return _AcceptedHydration(
        pointer["manifest_sha256"], sha(canonical(pointer)),
        pointer["acceptance_sha256"],
        _acceptance_file_sha256(run_dir, pointer["manifest_sha256"]), student,
        canonical(dict(student.correction_frontier)), candidate_identity_sha256)


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
    object.__setattr__(
        cache, "_candidate_identity_sha256", hydration.candidate_identity_sha256)
    if registry is not None:
        object.__setattr__(cache, "_correction_registry", registry)
    return _AcceptedExecutionEntry(
        hydration, cache, registry,
        student.correction_frontier.get("source_authority_registry_sha256"),
        binding, student.retained_state.allocations.manifest.digest)


def _new_publication_parent(run_dir: Path, hydration) -> AcceptedPublicationParent:
    result = object.__new__(AcceptedPublicationParent)
    currentness = bind_bamf_bundle_currentness(
        Path(run_dir) / "bamf-bundles" / hydration.manifest_sha256,
        expected_manifest_sha256=hydration.manifest_sha256)
    for name, value in (
        ("manifest_sha256", hydration.manifest_sha256),
        ("acceptance_sha256", hydration.acceptance_sha256),
        ("student", hydration.student),
        ("_pointer_sha256", hydration.pointer_sha256),
        ("_acceptance_file_sha256", hydration.acceptance_file_sha256),
        ("_hydration", hydration),
        ("_currentness", currentness),
        ("_issuance", _PUBLICATION_PARENT_ISSUER),
    ):
        object.__setattr__(result, name, value)
    return result


def _require_publication_parent_locked(lock, hydrations, run_dir, pointer, witness):
    run_dir = Path(run_dir).resolve()
    key = str(run_dir)
    if (type(witness) is not AcceptedPublicationParent
            or getattr(witness, "_issuance", None) is not _PUBLICATION_PARENT_ISSUER):
        invalid("B13_PUBLICATION_PARENT_REQUIRED")
    with lock:
        retained = hydrations.get(key)
    if retained is not witness._hydration:
        invalid("B13_PUBLICATION_PARENT_STALE")
    if (pointer is None
            or sha(canonical(pointer)) != witness._pointer_sha256
            or pointer.get("manifest_sha256") != witness.manifest_sha256
            or pointer.get("acceptance_sha256") != witness.acceptance_sha256
            or _acceptance_file_sha256(run_dir, witness.manifest_sha256)
            != witness._acceptance_file_sha256):
        invalid("B13_PUBLICATION_PARENT_STALE")
    require_bamf_bundle_currentness(witness._currentness)
    return witness


def _current_hydration_locked(
        lock, hydrations, executions, run_dir, key, pointer, *, metrics=None):
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
    _require_initial_foundation_authority(run_dir, student)
    identity = _published_in_memory_identity_locked(
        run_dir, student, pointer, accepted_parent=accepted_parent,
        acceptance_verified=True)
    if metrics is not None:
        metrics.increment("full_candidate_identity_hashes")
    hydration = _new_hydration(
        run_dir, pointer, student, identity.candidate_identity_sha256)
    with lock:
        hydrations[key] = hydration
        executions.pop(key, None)
    return hydration


def _make_execution_cache_runtime():
    lock = RLock()
    hydrations, executions = {}, {}

    def current_hydration(run_dir: Path, *, metrics=None):
        run_dir = Path(run_dir).resolve()
        key = str(run_dir)
        with _pointer_read_lock(run_dir):
            pointer = _read_pointer(run_dir / "bamf-state.json")
            return _current_hydration_locked(
                lock, hydrations, executions, run_dir, key, pointer,
                metrics=metrics)

    def bind(run_dir: Path, *, metrics=None):
        run_dir = Path(run_dir).resolve()
        key = str(run_dir)
        with _pointer_read_lock(run_dir):
            pointer = _read_pointer(run_dir / "bamf-state.json")
            hydration = _current_hydration_locked(
                lock, hydrations, executions, run_dir, key, pointer,
                metrics=metrics)
            registry = _accepted_source_authority_registry(
                run_dir, hydration.student)
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
        if (getattr(cache, "accepted_manifest_sha256", None)
                != hydration.manifest_sha256
                or getattr(cache, "run_id", None) != hydration.student.run_id
                or getattr(cache, "generation", None) != hydration.student.generation):
            invalid("B13_EXECUTION_CACHE_STALE")
        registry = _current_registry(run_dir, hydration)
        with lock:
            retained = executions.get(str(run_dir))
            if retained is None or retained.cache is not cache:
                invalid("B13_EXECUTION_CACHE_REQUIRED")
            _require_execution_entry(retained, registry)
        return cache

    def load(run_dir: Path):
        return current_hydration(run_dir).student

    def bind_publication_parent_locked(run_dir: Path, pointer):
        run_dir = Path(run_dir).resolve()
        key = str(run_dir)
        from .publication.instrumentation import publication_bundle_load
        with publication_bundle_load("parent"):
            hydration = _current_hydration_locked(
                lock, hydrations, executions, run_dir, key, pointer)
        return _new_publication_parent(run_dir, hydration)

    def bind_publication_parent(run_dir: Path):
        run_dir = Path(run_dir).resolve()
        with _pointer_read_lock(run_dir):
            pointer = _read_pointer(run_dir / "bamf-state.json")
            return bind_publication_parent_locked(run_dir, pointer)

    def require_publication_parent_locked(run_dir: Path, pointer, witness):
        return _require_publication_parent_locked(
            lock, hydrations, run_dir, pointer, witness)

    def reset_for_tests():
        with lock:
            hydrations.clear()
            executions.clear()

    return (
        bind, require, load, reset_for_tests,
        bind_publication_parent, bind_publication_parent_locked,
        require_publication_parent_locked,
    )


(
    bind_accepted_execution_cache,
    _require_owned_execution_cache,
    load_accepted_generation,
    _reset_execution_cache_owner_for_tests,
    bind_accepted_publication_parent,
    _bind_accepted_publication_parent_locked,
    _require_accepted_publication_parent_locked,
) = _make_execution_cache_runtime()


__all__ = (
    "AcceptedPublicationParent", "bind_accepted_execution_cache",
    "bind_accepted_publication_parent", "load_accepted_generation",
)
