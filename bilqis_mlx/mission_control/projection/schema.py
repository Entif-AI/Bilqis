"""SQLite schema for the disposable CP06 Model Forensics projection."""
from .contracts import PROJECTION_SCHEMA, PROJECTION_SCHEMA_VERSION


SCHEMA_SQL = f"""
CREATE TABLE projection_meta (
    key TEXT PRIMARY KEY,
    value TEXT NOT NULL
) WITHOUT ROWID;
INSERT INTO projection_meta(key, value)
VALUES ('schema_version', '{PROJECTION_SCHEMA_VERSION}');
INSERT INTO projection_meta(key, value)
VALUES ('schema_id', '{PROJECTION_SCHEMA}');

CREATE TABLE record_revisions (
    revision_id INTEGER PRIMARY KEY AUTOINCREMENT,
    record_id TEXT NOT NULL,
    schema_version TEXT NOT NULL,
    payload_sha256 TEXT NOT NULL,
    run_id TEXT,
    generation INTEGER,
    materialized_at INTEGER NOT NULL,
    observed_at INTEGER,
    as_of INTEGER,
    event_id TEXT,
    event_stream_id TEXT,
    event_epoch_id TEXT,
    event_ordinal INTEGER,
    event_cursor_sha256 TEXT,
    payload_json TEXT NOT NULL,
    active INTEGER NOT NULL CHECK(active IN (0, 1)),
    UNIQUE(record_id, payload_sha256)
);
CREATE UNIQUE INDEX active_record_by_id
ON record_revisions(record_id) WHERE active = 1;
CREATE INDEX records_by_schema
ON record_revisions(schema_version, active);
CREATE INDEX records_by_run_generation
ON record_revisions(run_id, generation, active);
CREATE UNIQUE INDEX event_identity_unique
ON record_revisions(event_id) WHERE event_id IS NOT NULL;
CREATE UNIQUE INDEX event_position_unique
ON record_revisions(event_stream_id, event_epoch_id, event_ordinal)
WHERE event_stream_id IS NOT NULL;

CREATE TABLE record_refs (
    revision_id INTEGER NOT NULL REFERENCES record_revisions(revision_id)
        ON DELETE CASCADE,
    relation TEXT NOT NULL,
    ref TEXT NOT NULL,
    PRIMARY KEY(revision_id, relation, ref)
) WITHOUT ROWID;
CREATE INDEX refs_by_target ON record_refs(ref, relation);

CREATE TABLE event_frontiers (
    stream_id TEXT PRIMARY KEY,
    epoch_id TEXT NOT NULL,
    next_ordinal INTEGER NOT NULL,
    latest_cursor_sha256 TEXT
) WITHOUT ROWID;
"""
