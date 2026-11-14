"""Accepted-generation runtime custody for B08/B14/C09 live execution."""
from __future__ import annotations

from dataclasses import asdict, dataclass
import json
from pathlib import Path
from threading import RLock

from bilqis_mlx.data_plane import SHA256_HEX_LENGTH
from bilqis_mlx.learning.atlas_acceptance import candidate_identity_digest
from bilqis_mlx.runtime.backbone_identity import execution_generation_digest

from .codec import load_bamf_bundle, validate_bamf_bundle_custody
from .execution_cache import _new_execution_cache
from .publication import (
    _live_bundle_manifest, _pointer_lock, _read_pointer,
    _require_published_acceptance,
)
from .records import (
    BAMF_POINTER_SCHEMA, CompleteStudent, canonical, invalid, sha, sidecar_records,
)


def _accepted_source_authority_registry(run_dir: Path, student: CompleteStudent):
    from .source_authority_custody import (
        resolve_source_authority_registry,
    )
    return resolve_source_authority_registry(
        run_dir, student.correction_frontier)


@dataclass(frozen=True)
class AcceptedGenerationIdentity:
    """The published identity of the accepted generation in custody."""

    run_id: str
    generation: int
    manifest_sha256: str
    topology_digest: str
    extents_digest: str
    optimizer_step: int
    candidate_identity_sha256: str


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


def _read_accepted_locked(run_dir: Path):
    run_dir = Path(run_dir)
    pointer_path = run_dir / "bamf-state.json"
    pointer = _read_pointer(pointer_path)
    if pointer is None:
        invalid("BAMF_GENERATION_POINTER_MISSING")
    student = load_bamf_bundle(
        run_dir / "bamf-bundles" / pointer["manifest_sha256"],
        expected_manifest_sha256=pointer["manifest_sha256"])
    if (student.run_id != pointer["run_id"]
            or student.generation != pointer["generation"]
            or student.parent_manifest_sha256 != pointer["parent_manifest_sha256"]):
        invalid("BAMF_GENERATION_POINTER_DRIFT")
    _require_published_acceptance(run_dir, pointer, student)
    return pointer, student


def _read_accepted(run_dir: Path):
    run_dir = Path(run_dir)
    with _pointer_lock(run_dir):
        return _read_accepted_locked(run_dir)


def load_accepted_generation(run_dir: Path) -> CompleteStudent:
    """Load the currently published accepted generation under the pointer lock."""
    return _read_accepted(run_dir)[1]


def _identity_from_pointer(
        student: CompleteStudent, pointer: dict) -> AcceptedGenerationIdentity:
    manifest = pointer.get("manifest_sha256") if isinstance(pointer, dict) else None
    if (type(student) is not CompleteStudent
            or not isinstance(pointer, dict)
            or pointer.get("schema") != BAMF_POINTER_SCHEMA
            or pointer.get("run_id") != student.run_id
            or pointer.get("generation") != student.generation
            or pointer.get("parent_manifest_sha256") != student.parent_manifest_sha256
            or not isinstance(manifest, str) or len(manifest) != SHA256_HEX_LENGTH
            or any(char not in "0123456789abcdef" for char in manifest)):
        invalid("BAMF_GENERATION_POINTER_DRIFT")
    return AcceptedGenerationIdentity(
        run_id=student.run_id,
        generation=student.generation,
        manifest_sha256=manifest,
        topology_digest=student.topology.digest,
        extents_digest=student.extents.digest,
        optimizer_step=student.retained_state.optimizer_step,
        candidate_identity_sha256=candidate_identity_digest(student.retained_state))


def _published_in_memory_identity_locked(
        run_dir: Path, student: CompleteStudent, pointer: dict,
) -> AcceptedGenerationIdentity:
    run_dir = Path(run_dir)
    if type(student) is not CompleteStudent:
        invalid("BAMF_GENERATION_POINTER_DRIFT")
    identity = _identity_from_pointer(student, pointer)
    manifest = _live_bundle_manifest(run_dir, pointer)
    if (manifest["implementation_sha256"] != student.implementation_sha256
            or canonical(manifest["topology"])
            != canonical(student.topology.to_record())
            or canonical(manifest["extents"])
            != canonical(student.extents.to_record())
            or canonical(manifest["provenance"])
            != canonical(student.provenance.to_record())
            or canonical(manifest["transition"])
            != canonical(dict(student.transition))
            or manifest["optimizer"]["step"] != student.retained_state.optimizer_step
            or canonical(manifest["optimizer"]["hyperparameters"])
            != canonical(asdict(student.optimizer_hyperparameters))):
        invalid("BAMF_GENERATION_POINTER_DRIFT")
    for name, record in sidecar_records(student).items():
        stored = manifest["sidecars"].get(name)
        if (not isinstance(stored, dict)
                or stored.get("sha256") != sha(canonical(record))):
            invalid("BAMF_GENERATION_POINTER_DRIFT")
    _require_published_acceptance(run_dir, pointer, student)
    return identity


def _published_in_memory_identity(
        run_dir: Path, student: CompleteStudent) -> AcceptedGenerationIdentity:
    run_dir = Path(run_dir)
    with _pointer_lock(run_dir):
        pointer = _read_pointer(run_dir / "bamf-state.json")
        if pointer is None:
            invalid("BAMF_GENERATION_POINTER_MISSING")
        return _published_in_memory_identity_locked(run_dir, student, pointer)


def _require_current_execution_cache(run_dir: Path, cache, entries, lock):
    key = str(run_dir)
    with _pointer_lock(run_dir):
        with lock:
            retained = entries.get(key)
        current_registry = _fast_retained_registry(
            run_dir, _read_pointer(run_dir / "bamf-state.json"), retained)
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
        run_dir: Path, pointer: dict, student: CompleteStudent,
        identity: AcceptedGenerationIdentity, generation_binding: str,
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
        run_dir = Path(key).resolve()
        return _require_current_execution_cache(run_dir, cache, entries, lock)

    def bind(run_dir: Path):
        """Authenticate and bind exactly the live accepted generation cache."""
        run_dir = Path(run_dir).resolve()
        with _pointer_lock(run_dir):
            pointer = _read_pointer(run_dir / "bamf-state.json")
            retained = _reuse_current_execution_cache(run_dir, pointer, entries, lock)
            if retained is not None:
                return retained
            pointer, student = _read_accepted_locked(run_dir)
            identity = _published_in_memory_identity_locked(
                run_dir, student, pointer)
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
    "AcceptedGenerationIdentity",
    "_identity_from_pointer", "_published_in_memory_identity", "_read_accepted",
    "bind_accepted_execution_cache",
    "load_accepted_generation",
)
