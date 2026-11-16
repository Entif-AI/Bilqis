"""Append-only provenance anchor for builder-produced candidate-frontier releases."""
from __future__ import annotations

from dataclasses import dataclass
import hashlib
import json
import sqlite3

from bilqis_mlx.data_plane import data_plane
from bilqis_mlx.errors import ErrorBus, SCHOOL
from bilqis_mlx.factory.candidate_frontier import CandidateFrontierRelease


SCHEMA = "bilqis.mlx.planner-frontier-trust/v1"
KEY_SCHEMA = "bilqis.mlx.planner-frontier-trust-key/v1"


def _invalid(reason: str):
    ErrorBus.Raise(SCHOOL.MODEL_TOPOLOGY.INVALID, reason=reason)


def _sha(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()


def _wire(value: dict) -> bytes:
    return json.dumps(
        value, sort_keys=True, ensure_ascii=False,
        separators=(",", ":"), allow_nan=False).encode("utf-8")


def _is_digest(value) -> bool:
    return (isinstance(value, str) and len(value) == 64
            and all(char in "0123456789abcdef" for char in value))


def planner_frontier_trust_key(
        builder_sha256: str, input_digest: str, factory_release_sha256: str) -> str:
    if not all(_is_digest(value) for value in (
            builder_sha256, input_digest, factory_release_sha256)):
        _invalid("BAMF_PLANNER_FRONTIER_TRUST_INVALID")
    return _sha(_wire({
        "schema": KEY_SCHEMA,
        "builder_sha256": builder_sha256,
        "input_digest": input_digest,
        "factory_release_sha256": factory_release_sha256,
    }))


@dataclass(frozen=True)
class PlannerFrontierTrust:
    trust_key_sha256: str
    builder_sha256: str
    input_digest: str
    factory_release_sha256: str
    output_digest: str
    frontier_release_sha256: str
    receipt_sha256: str
    receipt_raw: bytes


def _row(trust_key_sha256: str):
    plane = data_plane()
    with plane._lock:
        return plane._db.execute(
            "SELECT builder_sha256,input_digest,factory_release_sha256,output_digest,"
            "frontier_release_sha256,receipt_sha256,receipt_payload "
            "FROM bamf_planner_frontier_trust WHERE trust_key_sha256=?",
            (trust_key_sha256,),
        ).fetchone()


def _validate_row(trust_key_sha256: str, row):
    if row is None:
        return None
    (builder, input_digest, factory_release, output_digest,
     frontier_release, receipt_sha256, receipt_raw) = row
    digests = (
        trust_key_sha256, builder, input_digest, factory_release,
        output_digest, frontier_release, receipt_sha256,
    )
    if (not all(_is_digest(value) for value in digests)
            or not isinstance(receipt_raw, bytes)
            or _sha(receipt_raw) != receipt_sha256):
        _invalid("BAMF_PLANNER_FRONTIER_TRUST_DRIFT")
    try:
        receipt = json.loads(receipt_raw)
    except (UnicodeDecodeError, json.JSONDecodeError, TypeError):
        _invalid("BAMF_PLANNER_FRONTIER_TRUST_DRIFT")
        raise AssertionError
    expected = {
        "schema": SCHEMA,
        "trust_key_sha256": trust_key_sha256,
        "builder_sha256": builder,
        "input_digest": input_digest,
        "factory_release_sha256": factory_release,
        "output_digest": output_digest,
        "frontier_release_sha256": frontier_release,
    }
    if receipt != expected:
        _invalid("BAMF_PLANNER_FRONTIER_TRUST_DRIFT")
    return PlannerFrontierTrust(
        trust_key_sha256, builder, input_digest, factory_release,
        output_digest, frontier_release, receipt_sha256, receipt_raw)


def load_planner_frontier_trust(
        builder_sha256: str, input_digest: str, factory_release_sha256: str):
    """Return the immutable builder-produced release anchor for the exact inputs."""
    key = planner_frontier_trust_key(
        builder_sha256, input_digest, factory_release_sha256)
    return _validate_row(key, _row(key))


def planner_frontier_trust_matches(
        trust: PlannerFrontierTrust, release: CandidateFrontierRelease) -> bool:
    if type(trust) is not PlannerFrontierTrust or type(release) is not CandidateFrontierRelease:
        _invalid("BAMF_PLANNER_FRONTIER_TRUST_INVALID")
    release.verify()
    return (
        trust.builder_sha256 == release.builder_sha256
        and trust.input_digest == release.input_digest
        and trust.output_digest == release.output_digest
        and trust.frontier_release_sha256 == release.release_sha256
    )


def publish_planner_frontier_trust(
        release: CandidateFrontierRelease, factory_release_sha256: str):
    """Seal one deterministic builder/input/Factory-release result exactly once."""
    if type(release) is not CandidateFrontierRelease or not _is_digest(factory_release_sha256):
        _invalid("BAMF_PLANNER_FRONTIER_TRUST_INVALID")
    release.verify()
    key = planner_frontier_trust_key(
        release.builder_sha256, release.input_digest, factory_release_sha256)
    receipt = {
        "schema": SCHEMA,
        "trust_key_sha256": key,
        "builder_sha256": release.builder_sha256,
        "input_digest": release.input_digest,
        "factory_release_sha256": factory_release_sha256,
        "output_digest": release.output_digest,
        "frontier_release_sha256": release.release_sha256,
    }
    raw = _wire(receipt)
    receipt_sha = _sha(raw)
    existing = _validate_row(key, _row(key))
    if existing is not None:
        if existing.receipt_raw != raw:
            _invalid("BAMF_PLANNER_FRONTIER_TRUST_CONFLICT")
        return existing
    plane = data_plane()
    values = (
        key, release.builder_sha256, release.input_digest, factory_release_sha256,
        release.output_digest, release.release_sha256, receipt_sha, raw,
    )
    try:
        with plane.transaction():
            row = plane._db.execute(
                "SELECT builder_sha256,input_digest,factory_release_sha256,output_digest,"
                "frontier_release_sha256,receipt_sha256,receipt_payload "
                "FROM bamf_planner_frontier_trust WHERE trust_key_sha256=?",
                (key,),
            ).fetchone()
            if row is None:
                plane._db.execute(
                    "INSERT INTO bamf_planner_frontier_trust("
                    "trust_key_sha256,builder_sha256,input_digest,factory_release_sha256,"
                    "output_digest,frontier_release_sha256,receipt_sha256,receipt_payload) "
                    "VALUES(?,?,?,?,?,?,?,?)",
                    values,
                )
            elif _validate_row(key, row).receipt_raw != raw:
                _invalid("BAMF_PLANNER_FRONTIER_TRUST_CONFLICT")
    except sqlite3.IntegrityError:
        _invalid("BAMF_PLANNER_FRONTIER_TRUST_CONFLICT")
    stored = load_planner_frontier_trust(
        release.builder_sha256, release.input_digest, factory_release_sha256)
    if stored is None or stored.receipt_raw != raw:
        _invalid("BAMF_PLANNER_FRONTIER_TRUST_DRIFT")
    return stored


__all__ = (
    "PlannerFrontierTrust",
    "load_planner_frontier_trust",
    "planner_frontier_trust_key",
    "planner_frontier_trust_matches",
    "publish_planner_frontier_trust",
)
