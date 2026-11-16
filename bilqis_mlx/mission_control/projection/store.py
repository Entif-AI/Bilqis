"""Low-level storage mechanics for the disposable CP06 projection."""
from __future__ import annotations

import hashlib
import os
from pathlib import Path
import sqlite3

from ..contracts.codec import canonical_json, decode_json
from ..contracts.envelopes import EventEnvelope, StreamPosition
from ..contracts.model import MissionControlContractError, WireRecord
from .contracts import (
    PROJECTION_SCHEMA, PROJECTION_SCHEMA_VERSION, ProjectionStats,
    projection_invalid,
)
from .schema import SCHEMA_SQL


def connect(path: Path) -> sqlite3.Connection:
    if path.is_symlink():
        projection_invalid("PROJECTION_PATH_UNSAFE")
    if not path.exists():
        projection_invalid("PROJECTION_MISSING_REBUILD_REQUIRED")
    if not path.is_file():
        projection_invalid("PROJECTION_PATH_UNSAFE")
    try:
        db = sqlite3.connect(path)
        db.row_factory = sqlite3.Row
        db.execute("PRAGMA foreign_keys = ON")
        return db
    except sqlite3.Error:
        projection_invalid("PROJECTION_CORRUPT_REBUILD_REQUIRED")


def create(path: Path) -> None:
    try:
        db = sqlite3.connect(path)
        try:
            db.executescript(SCHEMA_SQL)
            db.commit()
        finally:
            db.close()
        os.chmod(path, 0o600)
    except (OSError, sqlite3.Error):
        projection_invalid("PROJECTION_CREATE_FAILED")


def validate(path: Path) -> None:
    try:
        with connect(path) as db:
            if db.execute("PRAGMA integrity_check").fetchone()[0] != "ok":
                projection_invalid("PROJECTION_CORRUPT_REBUILD_REQUIRED")
            rows = dict(db.execute(
                "SELECT key, value FROM projection_meta").fetchall())
    except sqlite3.Error:
        projection_invalid("PROJECTION_CORRUPT_REBUILD_REQUIRED")
    if rows.get("schema_id") != PROJECTION_SCHEMA:
        projection_invalid("PROJECTION_SCHEMA_INCOMPATIBLE_REBUILD_REQUIRED")
    if rows.get("schema_version") != str(PROJECTION_SCHEMA_VERSION):
        projection_invalid("PROJECTION_SCHEMA_INCOMPATIBLE_REBUILD_REQUIRED")


def _rank(record: WireRecord, digest: str) -> tuple:
    run = record.meta.run
    return (
        -1 if run is None else run.generation,
        -1 if record.meta.as_of is None else record.meta.as_of,
        -1 if record.meta.observed_at is None else record.meta.observed_at,
        record.meta.materialized_at,
        digest,
    )


def _row_rank(row: sqlite3.Row) -> tuple:
    return (
        -1 if row["generation"] is None else row["generation"],
        -1 if row["as_of"] is None else row["as_of"],
        -1 if row["observed_at"] is None else row["observed_at"],
        row["materialized_at"],
        row["payload_sha256"],
    )


def _assert_revision_identity(
    db: sqlite3.Connection, record: WireRecord, digest: str,
) -> None:
    run = record.meta.run
    generation = None if run is None else run.generation
    existing = db.execute(
        """SELECT payload_sha256 FROM record_revisions
        WHERE record_id = ?
          AND generation IS ?
          AND materialized_at = ?
          AND observed_at IS ?
          AND as_of IS ?""",
        (
            record.meta.record_id, generation, record.meta.materialized_at,
            record.meta.observed_at, record.meta.as_of,
        ),
    ).fetchall()
    if any(row["payload_sha256"] != digest for row in existing):
        projection_invalid("PROJECTION_RECORD_IDENTITY_CONFLICT")


def ingest_record(db: sqlite3.Connection, record: WireRecord) -> None:
    payload = canonical_json(record)
    digest = hashlib.sha256(payload).hexdigest()
    run = record.meta.run
    _assert_revision_identity(db, record, digest)
    if type(record) is EventEnvelope:
        existing = db.execute(
            "SELECT payload_sha256 FROM record_revisions WHERE event_id = ?",
            (record.event_id,),
        ).fetchone()
        if existing is not None and existing["payload_sha256"] != digest:
            projection_invalid("PROJECTION_EVENT_IDENTITY_CONFLICT")
        existing_position = db.execute(
            """SELECT event_id, payload_sha256 FROM record_revisions
            WHERE event_stream_id = ? AND event_epoch_id = ? AND event_ordinal = ?""",
            (
                record.position.stream_id, record.position.epoch_id,
                record.position.ordinal,
            ),
        ).fetchone()
        if (existing_position is not None
                and (existing_position["event_id"] != record.event_id
                     or existing_position["payload_sha256"] != digest)):
            projection_invalid("PROJECTION_EVENT_POSITION_CONFLICT")
    current = db.execute(
        "SELECT * FROM record_revisions WHERE record_id = ? AND active = 1",
        (record.meta.record_id,),
    ).fetchone()
    db.execute(
        """INSERT OR IGNORE INTO record_revisions(
            record_id, schema_version, payload_sha256, run_id, generation,
            materialized_at, observed_at, as_of, event_id,
            event_stream_id, event_epoch_id, event_ordinal, event_cursor_sha256,
            payload_json, active
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 0)""",
        (
            record.meta.record_id, record.schema_version, digest,
            None if run is None else run.run_id,
            None if run is None else run.generation,
            record.meta.materialized_at, record.meta.observed_at, record.meta.as_of,
            record.event_id if type(record) is EventEnvelope else None,
            record.position.stream_id if type(record) is EventEnvelope else None,
            record.position.epoch_id if type(record) is EventEnvelope else None,
            record.position.ordinal if type(record) is EventEnvelope else None,
            record.position.cursor_sha256 if type(record) is EventEnvelope else None,
            payload.decode("utf-8"),
        ),
    )
    revision = db.execute(
        "SELECT revision_id FROM record_revisions WHERE record_id = ? AND payload_sha256 = ?",
        (record.meta.record_id, digest),
    ).fetchone()[0]
    for relation, refs in (
        ("SOURCE", record.meta.source_refs),
        ("EVIDENCE", record.meta.evidence_refs),
        ("RECEIPT", record.meta.receipt_refs),
    ):
        db.executemany(
            "INSERT OR IGNORE INTO record_refs(revision_id, relation, ref) VALUES (?, ?, ?)",
            ((revision, relation, ref) for ref in refs),
        )
    if current is None or _rank(record, digest) > _row_rank(current):
        db.execute(
            "UPDATE record_revisions SET active = 0 WHERE record_id = ?",
            (record.meta.record_id,),
        )
        db.execute(
            "UPDATE record_revisions SET active = 1 WHERE revision_id = ?",
            (revision,),
        )


def record_frontier(
    db: sqlite3.Connection, stream_id: str, epoch_id: str,
    next_ordinal: int, latest_cursor_sha256: str | None,
) -> None:
    current = db.execute(
        "SELECT * FROM event_frontiers WHERE stream_id = ?", (stream_id,),
    ).fetchone()
    if current is not None and current["epoch_id"] != epoch_id:
        projection_invalid("PROJECTION_FRONTIER_EPOCH_MISMATCH_REBUILD_REQUIRED")
    if current is not None:
        if next_ordinal < current["next_ordinal"]:
            return
        if (next_ordinal == current["next_ordinal"]
                and latest_cursor_sha256 != current["latest_cursor_sha256"]):
            projection_invalid("PROJECTION_FRONTIER_CONFLICT")
    db.execute(
        """INSERT INTO event_frontiers(
            stream_id, epoch_id, next_ordinal, latest_cursor_sha256
        ) VALUES (?, ?, ?, ?)
        ON CONFLICT(stream_id) DO UPDATE SET
            epoch_id = excluded.epoch_id,
            next_ordinal = excluded.next_ordinal,
            latest_cursor_sha256 = excluded.latest_cursor_sha256""",
        (stream_id, epoch_id, next_ordinal, latest_cursor_sha256),
    )


def initialize_frontier(
    db: sqlite3.Connection, stream_id: str, epoch_id: str,
    next_ordinal: int, latest_cursor_sha256: str | None,
) -> None:
    """Set a rebuild/snapshot baseline once; event ingestion owns advancement."""
    current = db.execute(
        "SELECT * FROM event_frontiers WHERE stream_id = ?", (stream_id,),
    ).fetchone()
    if current is not None:
        if (
            current["epoch_id"] == epoch_id
            and current["next_ordinal"] == next_ordinal
            and current["latest_cursor_sha256"] == latest_cursor_sha256
        ):
            return
        projection_invalid("PROJECTION_FRONTIER_BASELINE_CONFLICT")
    record_frontier(
        db, stream_id, epoch_id, next_ordinal, latest_cursor_sha256)


def advance_frontier(db: sqlite3.Connection, position: StreamPosition) -> None:
    """Advance only across one contiguous verified CP04 event position."""
    current = db.execute(
        "SELECT * FROM event_frontiers WHERE stream_id = ?",
        (position.stream_id,),
    ).fetchone()
    if current is None:
        if position.ordinal != 0 or position.previous_cursor_sha256 is not None:
            projection_invalid("PROJECTION_FRONTIER_GAP_REBUILD_REQUIRED")
    else:
        if current["epoch_id"] != position.epoch_id:
            projection_invalid("PROJECTION_FRONTIER_EPOCH_MISMATCH_REBUILD_REQUIRED")
        if position.ordinal < current["next_ordinal"]:
            return
        if (position.ordinal != current["next_ordinal"]
                or position.previous_cursor_sha256
                != current["latest_cursor_sha256"]):
            projection_invalid("PROJECTION_FRONTIER_GAP_REBUILD_REQUIRED")
    record_frontier(
        db, position.stream_id, position.epoch_id,
        position.ordinal + 1, position.cursor_sha256,
    )


def decode_rows(rows) -> tuple[WireRecord, ...]:
    decoded = []
    for row in rows:
        payload_json = row["payload_json"]
        if type(payload_json) is not str:
            projection_invalid("PROJECTION_ROW_CORRUPT_REBUILD_REQUIRED")
        payload = payload_json.encode("utf-8")
        if hashlib.sha256(payload).hexdigest() != row["payload_sha256"]:
            projection_invalid("PROJECTION_ROW_DIGEST_MISMATCH_REBUILD_REQUIRED")
        try:
            decoded.append(decode_json(payload))
        except MissionControlContractError:
            projection_invalid("PROJECTION_ROW_CORRUPT_REBUILD_REQUIRED")
    return tuple(decoded)


def stats(db: sqlite3.Connection) -> ProjectionStats:
    active = db.execute(
        "SELECT COUNT(*) FROM record_revisions WHERE active = 1").fetchone()[0]
    revisions = db.execute("SELECT COUNT(*) FROM record_revisions").fetchone()[0]
    references = db.execute("SELECT COUNT(*) FROM record_refs").fetchone()[0]
    events = db.execute(
        "SELECT COUNT(*) FROM record_revisions WHERE schema_version = ?",
        (EventEnvelope.SCHEMA,),
    ).fetchone()[0]
    return ProjectionStats(active, revisions, references, events)
