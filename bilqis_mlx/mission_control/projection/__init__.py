"""Disposable CP06 projection over accepted Model Forensics records."""
from __future__ import annotations

import hashlib
import os
from pathlib import Path
import sqlite3
import tempfile
from typing import Iterable

from ..contracts.codec import canonical_json
from ..contracts.envelopes import EventEnvelope
from ..contracts.model import WireRecord, is_name, is_sha256, is_wire_integer
from .contracts import (
    PROJECTION_SCHEMA, PROJECTION_SCHEMA_VERSION, ProjectionFrontierState,
    ProjectionFrontierStatus, ProjectionStats, projection_invalid,
)
from ..query_catalog import MissionControlQueryCatalog
from . import store


def _valid_frontier(
    stream_id: str, epoch_id: str, next_ordinal: int,
    latest_cursor_sha256: str | None,
) -> bool:
    return (
        is_name(stream_id)
        and is_name(epoch_id)
        and is_wire_integer(next_ordinal)
        and next_ordinal >= 0
        and (latest_cursor_sha256 is None or is_sha256(latest_cursor_sha256))
        and ((next_ordinal == 0) == (latest_cursor_sha256 is None))
    )


class MissionControlProjection:
    """Rebuildable local index; CP02 records and durable artifacts remain truth."""

    def __init__(self, path: Path, *, _create: bool = False):
        self.path = Path(path)
        if self.path.is_symlink():
            projection_invalid("PROJECTION_PATH_UNSAFE")
        if not self.path.exists():
            if not _create:
                projection_invalid("PROJECTION_MISSING_REBUILD_REQUIRED")
            self.path.parent.mkdir(parents=True, exist_ok=True)
            store.create(self.path)
        elif not self.path.is_file():
            projection_invalid("PROJECTION_PATH_UNSAFE")
        store.validate(self.path)

    @classmethod
    def create_empty(cls, path: Path) -> "MissionControlProjection":
        target = Path(path)
        if target.exists() or target.is_symlink():
            projection_invalid("PROJECTION_ALREADY_EXISTS")
        return cls(target, _create=True)

    @classmethod
    def rebuild(
        cls, path: Path, records: Iterable[WireRecord], *,
        frontiers: Iterable[tuple[str, str, int, str | None]] = (),
    ) -> "MissionControlProjection":
        target = Path(path)
        target.parent.mkdir(parents=True, exist_ok=True)
        if target.is_symlink() or (target.exists() and not target.is_file()):
            projection_invalid("PROJECTION_PATH_UNSAFE")
        handle, temp_name = tempfile.mkstemp(
            prefix=target.name + ".rebuild-", dir=target.parent)
        os.close(handle)
        temp = Path(temp_name)
        try:
            temp.unlink()
            candidate = cls(temp, _create=True)
            candidate.ingest_records(records)
            for frontier in frontiers:
                candidate.record_frontier(*frontier)
            os.replace(temp, target)
            return cls(target)
        finally:
            if temp.exists():
                temp.unlink()

    @classmethod
    def rebuild_from_bamf(
        cls, path: Path, run_dir: Path,
    ) -> "MissionControlProjection":
        """Rebuild solely from authenticated immutable BAMF run artifacts.

        The adapter is imported lazily so ordinary CP02/CP06 consumers retain
        their existing lightweight dependency boundary.  No model tensors are
        hydrated and no learner artifact is mutated by reconstruction.
        """
        from bilqis_mlx.control_plane.native_source import materialize_native_projection

        material = materialize_native_projection(Path(run_dir))
        return cls.rebuild(path, material.records)

    def ingest_records(self, records: Iterable[WireRecord]) -> ProjectionStats:
        material = tuple(records)
        if not all(isinstance(record, WireRecord) for record in material):
            projection_invalid("PROJECTION_RECORD_REQUIRED")
        try:
            with store.connect(self.path) as db:
                for record in material:
                    store.ingest_record(db, record)
                db.commit()
                return store.stats(db)
        except sqlite3.Error:
            projection_invalid("PROJECTION_WRITE_FAILED_REBUILD_REQUIRED")

    def ingest_event(
        self, event: EventEnvelope, payload: WireRecord,
    ) -> ProjectionStats:
        if type(event) is not EventEnvelope or not isinstance(payload, WireRecord):
            projection_invalid("PROJECTION_EVENT_PAYLOAD_REQUIRED")
        digest = hashlib.sha256(canonical_json(payload)).hexdigest()
        if (event.payload_schema_version != payload.schema_version
                or event.payload_record_id != payload.meta.record_id
                or event.payload_sha256 != digest):
            projection_invalid("PROJECTION_EVENT_PAYLOAD_MISMATCH")
        try:
            with store.connect(self.path) as db:
                store.ingest_record(db, payload)
                store.ingest_record(db, event)
                store.advance_frontier(db, event.position)
                db.commit()
                return store.stats(db)
        except sqlite3.Error:
            projection_invalid("PROJECTION_WRITE_FAILED_REBUILD_REQUIRED")

    def record_frontier(
        self, stream_id: str, epoch_id: str, next_ordinal: int,
        latest_cursor_sha256: str | None,
    ) -> None:
        if not _valid_frontier(
                stream_id, epoch_id, next_ordinal, latest_cursor_sha256):
            projection_invalid("PROJECTION_FRONTIER_INVALID")
        try:
            with store.connect(self.path) as db:
                store.initialize_frontier(
                    db, stream_id, epoch_id, next_ordinal, latest_cursor_sha256)
                db.commit()
        except sqlite3.Error:
            projection_invalid("PROJECTION_WRITE_FAILED_REBUILD_REQUIRED")

    def frontier_status(
        self, stream_id: str, epoch_id: str, next_ordinal: int,
        latest_cursor_sha256: str | None,
    ) -> ProjectionFrontierStatus:
        if not _valid_frontier(
                stream_id, epoch_id, next_ordinal, latest_cursor_sha256):
            projection_invalid("PROJECTION_FRONTIER_INVALID")
        with store.connect(self.path) as db:
            row = db.execute(
                "SELECT * FROM event_frontiers WHERE stream_id = ?", (stream_id,),
            ).fetchone()
        if row is None:
            state = ProjectionFrontierState.EMPTY
            projected_epoch = projected_next = None
        else:
            projected_epoch = row["epoch_id"]
            projected_next = row["next_ordinal"]
            if projected_epoch != epoch_id or projected_next < next_ordinal:
                state = ProjectionFrontierState.STALE
            elif (projected_next > next_ordinal
                  or row["latest_cursor_sha256"] != latest_cursor_sha256):
                state = ProjectionFrontierState.DIVERGED
            else:
                state = ProjectionFrontierState.CURRENT
        return ProjectionFrontierStatus(
            state, stream_id, projected_epoch, projected_next,
            epoch_id, next_ordinal,
        )

    def catalog(self) -> MissionControlQueryCatalog:
        try:
            with store.connect(self.path) as db:
                rows = tuple(db.execute(
                    """SELECT payload_json, payload_sha256 FROM record_revisions
                    WHERE active = 1 ORDER BY record_id"""))
            return MissionControlQueryCatalog(store.decode_rows(rows))
        except sqlite3.Error:
            projection_invalid("PROJECTION_READ_FAILED_REBUILD_REQUIRED")

    def revisions(self, record_id: str) -> tuple[WireRecord, ...]:
        try:
            with store.connect(self.path) as db:
                rows = tuple(db.execute(
                    """SELECT payload_json, payload_sha256 FROM record_revisions
                    WHERE record_id = ? ORDER BY revision_id""", (record_id,)))
            return store.decode_rows(rows)
        except sqlite3.Error:
            projection_invalid("PROJECTION_READ_FAILED_REBUILD_REQUIRED")

    def stats(self) -> ProjectionStats:
        try:
            with store.connect(self.path) as db:
                return store.stats(db)
        except sqlite3.Error:
            projection_invalid("PROJECTION_READ_FAILED_REBUILD_REQUIRED")


__all__ = (
    "MissionControlProjection", "PROJECTION_SCHEMA", "PROJECTION_SCHEMA_VERSION",
    "ProjectionFrontierState", "ProjectionFrontierStatus", "ProjectionStats",
)
