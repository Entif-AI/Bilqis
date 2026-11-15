"""External B13 trust root for accepted generation-zero custody."""
from __future__ import annotations

import json
from pathlib import Path
import sqlite3

from bilqis_mlx.data_plane import SHA256_HEX_LENGTH, data_plane
from bilqis_mlx.learning._atlas_candidate.identity_binding import (
    candidate_identity_for_canonical_consumer,
)

from ..codec import load_bamf_bundle
from ..records import CompleteStudent, canonical, invalid, sha
from .retry import _same_initial_candidate


GENESIS_TRUST_SCHEMA = "bilqis.mlx.bamf-genesis-trust/v1"


def _hex(value: object) -> bool:
    return (isinstance(value, str) and len(value) == SHA256_HEX_LENGTH
            and all(char in "0123456789abcdef" for char in value))


def _identity(run_id: str, manifest_sha256: str) -> tuple[str, str]:
    if not isinstance(run_id, str) or not run_id or not _hex(manifest_sha256):
        invalid("BAMF_INITIAL_GENERATION_TRUST_ROOT_INVALID")
    return run_id, manifest_sha256


def _trust_record(prepared, manifest_sha256: str) -> dict:
    """Project one accepted-custody receipt from the live prepared capability."""
    from ..genesis import PreparedInitialGeneration, validate_initial_generation_binding

    if type(prepared) is not PreparedInitialGeneration:
        invalid("BAMF_INITIAL_GENERATION_PREPARATION_REQUIRED")
    prepared.__post_init__()
    candidate = prepared.candidate
    validate_initial_generation_binding(candidate, prepared.binding)
    identity = candidate.run_identity
    factory = prepared.factory_authority
    return {
        "schema": GENESIS_TRUST_SCHEMA,
        "run_id": candidate.run_id,
        "generation": 0,
        "manifest_sha256": manifest_sha256,
        "acceptance_sha256": prepared.binding.digest,
        "run_identity_sha256": identity.digest,
        "candidate_identity_sha256": candidate_identity_for_canonical_consumer(
            candidate.retained_state),
        "topology_digest": candidate.topology.digest,
        "extents_digest": candidate.extents.digest,
        "implementation_sha256": candidate.implementation_sha256,
        "factory_state_sha256": factory.current_state_sha256,
        "factory_release_sha256": identity.factory_release_sha256,
        "semantic_graph_sha256": identity.semantic_graph_sha256,
        "source_identity": identity.initial_source_identity,
        "release_digest": identity.initial_release_digest,
        "teacher_identity": identity.initial_teacher_identity,
        "teacher_epoch": identity.initial_teacher_epoch,
    }


def _stored_trust(run_id: str):
    plane = data_plane()
    with plane._lock:
        return plane._db.execute(
            "SELECT generation,manifest_sha256,payload_sha256,payload "
            "FROM bamf_genesis_trust WHERE run_id=?", (run_id,)
        ).fetchone()


def _require_exact_stored_trust(run_id: str, manifest_sha256: str, raw: bytes) -> bool:
    stored = _stored_trust(run_id)
    if stored is None:
        return False
    generation, stored_manifest, payload_sha256, payload = stored
    if (generation != 0 or stored_manifest != manifest_sha256
            or payload_sha256 != sha(payload) or payload != raw):
        invalid("BAMF_INITIAL_GENERATION_TRUST_ROOT_DRIFT")
    return True


def sealed_initial_generation_manifest(prepared) -> str | None:
    """Return an already sealed exact genesis without replaying mutable upstream."""
    prepared.__post_init__()
    stored = _stored_trust(prepared.candidate.run_id)
    if stored is None:
        return None
    manifest_sha256 = stored[1]
    raw = canonical(_trust_record(prepared, manifest_sha256))
    _require_exact_stored_trust(
        prepared.candidate.run_id, manifest_sha256, raw)
    return manifest_sha256


def publish_initial_generation_trust_root(
        run_dir: Path, prepared, manifest_sha256: str) -> None:
    """Seal one B13-owned append-only acceptance witness outside the BAMF package."""
    from ..genesis import validate_initial_generation_preparation

    run_id, manifest_sha256 = _identity(prepared.candidate.run_id, manifest_sha256)
    record = _trust_record(prepared, manifest_sha256)
    raw = canonical(record)
    target = Path(run_dir) / "bamf-bundles" / manifest_sha256
    student = load_bamf_bundle(target, expected_manifest_sha256=manifest_sha256)
    if not _same_initial_candidate(student, prepared.candidate):
        invalid("BAMF_INITIAL_GENERATION_TRUST_ROOT_DRIFT")
    if _require_exact_stored_trust(run_id, manifest_sha256, raw):
        return

    plane = data_plane()
    payload_sha256 = sha(raw)
    validate_initial_generation_preparation(prepared)
    with plane.transaction():
        existing = plane._db.execute(
            "SELECT generation,manifest_sha256,payload_sha256,payload "
            "FROM bamf_genesis_trust WHERE run_id=?", (run_id,)
        ).fetchone()
        if existing is not None:
            generation, stored_manifest, stored_sha256, stored_raw = existing
            if (generation != 0 or stored_manifest != manifest_sha256
                    or stored_sha256 != payload_sha256 or stored_raw != raw):
                invalid("BAMF_INITIAL_GENERATION_TRUST_ROOT_DRIFT")
            return
        try:
            plane._db.execute(
                "INSERT INTO bamf_genesis_trust("
                "run_id,generation,manifest_sha256,payload_sha256,payload) "
                "VALUES(?,?,?,?,?)",
                (run_id, 0, manifest_sha256, payload_sha256, raw),
            )
        except sqlite3.IntegrityError:
            invalid("BAMF_INITIAL_GENERATION_TRUST_ROOT_DRIFT")
    if not _require_exact_stored_trust(run_id, manifest_sha256, raw):
        invalid("BAMF_INITIAL_GENERATION_TRUST_ROOT_DRIFT")


def require_initial_generation_trust_root(
        pointer: dict, student: CompleteStudent, binding) -> None:
    """Require the external owner-issued witness before granting cold authority."""
    identity = student.run_identity
    run_id, manifest_sha256 = _identity(
        student.run_id, pointer.get("manifest_sha256"))
    stored = _stored_trust(run_id)
    if stored is None:
        invalid("BAMF_INITIAL_GENERATION_TRUST_ROOT_REQUIRED")
    generation, stored_manifest, payload_sha256, raw = stored
    if (generation != 0 or stored_manifest != manifest_sha256
            or payload_sha256 != sha(raw)):
        invalid("BAMF_INITIAL_GENERATION_TRUST_ROOT_INVALID")
    try:
        record = json.loads(raw)
    except (UnicodeDecodeError, json.JSONDecodeError):
        invalid("BAMF_INITIAL_GENERATION_TRUST_ROOT_INVALID")
    expected = {
        "schema": GENESIS_TRUST_SCHEMA,
        "run_id": student.run_id,
        "generation": 0,
        "manifest_sha256": manifest_sha256,
        "acceptance_sha256": binding.digest,
        "run_identity_sha256": identity.digest,
        "candidate_identity_sha256": candidate_identity_for_canonical_consumer(
            student.retained_state),
        "topology_digest": student.topology.digest,
        "extents_digest": student.extents.digest,
        "implementation_sha256": student.implementation_sha256,
        "factory_release_sha256": identity.factory_release_sha256,
        "semantic_graph_sha256": identity.semantic_graph_sha256,
        "source_identity": identity.initial_source_identity,
        "release_digest": identity.initial_release_digest,
        "teacher_identity": identity.initial_teacher_identity,
        "teacher_epoch": identity.initial_teacher_epoch,
    }
    if (not isinstance(record, dict)
            or set(record) != set(expected) | {"factory_state_sha256"}
            or any(record.get(name) != value for name, value in expected.items())
            or not _hex(record.get("factory_state_sha256"))):
        invalid("BAMF_INITIAL_GENERATION_TRUST_ROOT_INVALID")


__all__ = (
    "publish_initial_generation_trust_root", "require_initial_generation_trust_root",
)
