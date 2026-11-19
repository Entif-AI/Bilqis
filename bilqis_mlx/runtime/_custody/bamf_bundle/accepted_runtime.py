"""Accepted-generation runtime custody for B08/B14/C09 live execution."""
from __future__ import annotations

from dataclasses import asdict, dataclass
from pathlib import Path

from bilqis_mlx.data_plane import SHA256_HEX_LENGTH
from bilqis_mlx.learning.atlas_acceptance import candidate_identity_digest

from .codec import load_bamf_bundle
from .publication import (
    _live_bundle_manifest, _pointer_read_lock, _read_pointer,
    _require_published_acceptance,
)
from .records import (
    BAMF_POINTER_SCHEMA, CompleteStudent, canonical, invalid, sha, sidecar_records,
)


def _accepted_source_authority_registry(run_dir: Path, student: CompleteStudent):
    from .source_authority_custody import resolve_source_authority_registry
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

def _read_accepted_locked(
        run_dir: Path, *, accepted_parent: tuple[str, CompleteStudent] | None = None):
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
    _require_published_acceptance(
        run_dir, pointer, student, accepted_parent=accepted_parent)
    return pointer, student


def _read_accepted(run_dir: Path):
    run_dir = Path(run_dir)
    with _pointer_read_lock(run_dir):
        return _read_accepted_locked(run_dir)


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
        run_dir: Path, student: CompleteStudent, pointer: dict, *,
        accepted_parent: tuple[str, CompleteStudent] | None = None,
        acceptance_verified: bool = False,
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
    if not acceptance_verified:
        _require_published_acceptance(
            run_dir, pointer, student, accepted_parent=accepted_parent)
    return identity


def _published_in_memory_identity(
        run_dir: Path, student: CompleteStudent) -> AcceptedGenerationIdentity:
    run_dir = Path(run_dir)
    with _pointer_read_lock(run_dir):
        pointer = _read_pointer(run_dir / "bamf-state.json")
        if pointer is None:
            invalid("BAMF_GENERATION_POINTER_MISSING")
        return _published_in_memory_identity_locked(run_dir, student, pointer)


from .accepted_execution_cache import (
    _require_owned_execution_cache, _reset_execution_cache_owner_for_tests,
    bind_accepted_execution_cache, load_accepted_generation,
)


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
