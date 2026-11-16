"""CP06 disposable projection, revision, frontier, and rebuild behavior."""
from dataclasses import replace
import hashlib
from pathlib import Path
import sqlite3
from tempfile import TemporaryDirectory
import unittest

from bilqis_mlx.errors import BilqisError
from bilqis_mlx.control_plane.event_stream import EventFamily, EventStreamBroker
from bilqis_mlx.mission_control.envelopes import event_cursor_sha256
from bilqis_mlx.mission_control.observability import GenerationManifest
from bilqis_mlx.mission_control.projection import (
    MissionControlProjection, ProjectionFrontierState,
)
from bilqis_mlx.mission_control.query_catalog import MissionControlQueryCatalog
from bilqis_mlx.mission_control.query_contracts import (
    QueryFamily, QueryMode, QueryRequest,
)
from bilqis_mlx.mission_control.tests.samples import SAMPLES


class MissionControlProjectionTests(unittest.TestCase):
    def test_empty_build_queries_and_delete_rebuild_are_equivalent(self):
        with TemporaryDirectory() as temporary:
            path = Path(temporary) / "mission-control.sqlite3"
            records = SAMPLES[:16]
            frontier = ("mission-control", "epoch-a", 2, "a" * 64)
            expected = MissionControlQueryCatalog(records)
            projection = MissionControlProjection.rebuild(
                path, records, frontiers=(frontier,))
            requests = (
                QueryRequest(QueryFamily.RUN, run_id="run-7", limit=32),
                QueryRequest(QueryFamily.CAPABILITY, record_id="capability"),
                QueryRequest(QueryFamily.EPISODE, record_id="episode"),
                QueryRequest(QueryFamily.GENERATION, generation=7),
                QueryRequest(QueryFamily.REFERENCE, reference="evidence:a", limit=32),
            )
            first = tuple(
                expected.encode_page(projection.catalog().query(request))
                for request in requests
            )
            literal = tuple(
                expected.encode_page(expected.query(request))
                for request in requests
            )
            self.assertEqual(first, literal)
            self.assertEqual(
                projection.frontier_status(*frontier).state,
                ProjectionFrontierState.CURRENT,
            )

            path.unlink()
            rebuilt = MissionControlProjection.rebuild(
                path, records, frontiers=(frontier,))
            second = tuple(
                expected.encode_page(rebuilt.catalog().query(request))
                for request in requests
            )
            self.assertEqual(second, first)
            self.assertEqual(
                rebuilt.frontier_status(*frontier).state,
                ProjectionFrontierState.CURRENT,
            )

    def test_duplicate_event_and_receipt_ingestion_is_idempotent(self):
        with TemporaryDirectory() as temporary:
            path = Path(temporary) / "projection.sqlite3"
            projection = MissionControlProjection.create_empty(path)
            payload = SAMPLES[6]
            broker = EventStreamBroker(
                stream_id="mission-control", epoch_id="epoch-a")
            event = broker.publish_record(EventFamily.CANDIDATE_ASSESSED, payload)
            self.assertIsNotNone(event)
            receipt = SAMPLES[8]
            projection.ingest_records((event,))
            before_payload = projection.frontier_status(
                event.position.stream_id, event.position.epoch_id,
                event.position.ordinal + 1, event.position.cursor_sha256,
            )
            self.assertEqual(before_payload.state, ProjectionFrontierState.EMPTY)
            projection.ingest_event(event, payload)
            first = projection.ingest_records((receipt,))
            projection.ingest_event(event, payload)
            second = projection.ingest_records((receipt,))
            self.assertEqual(second, first)
            self.assertEqual(first.active_records, 3)
            self.assertEqual(first.revisions, 3)
            self.assertEqual(first.events, 1)
            status = projection.frontier_status(
                event.position.stream_id, event.position.epoch_id,
                event.position.ordinal + 1, event.position.cursor_sha256,
            )
            self.assertEqual(status.state, ProjectionFrontierState.CURRENT)
            conflicting = replace(
                event,
                meta=replace(
                    event.meta,
                    materialized_at=event.meta.materialized_at + 1,
                ),
            )
            with self.assertRaises(BilqisError) as collision:
                projection.ingest_records((conflicting,))
            self.assertEqual(
                collision.exception.context["reason"],
                "PROJECTION_EVENT_IDENTITY_CONFLICT",
            )
            alternate_id = "event-position-conflict"
            alternate_cursor = event_cursor_sha256(
                stream_id=event.position.stream_id,
                epoch_id=event.position.epoch_id,
                ordinal=event.position.ordinal,
                event_id=alternate_id,
                payload_schema_version=event.payload_schema_version,
                payload_record_id=event.payload_record_id,
                payload_sha256=event.payload_sha256,
                previous_cursor_sha256=event.position.previous_cursor_sha256,
            )
            alternate = replace(
                event,
                meta=replace(
                    event.meta, record_id=f"event-envelope:{alternate_id}"),
                event_id=alternate_id,
                position=replace(event.position, cursor_sha256=alternate_cursor),
            )
            with self.assertRaises(BilqisError) as position_collision:
                projection.ingest_event(alternate, payload)
            self.assertEqual(
                position_collision.exception.context["reason"],
                "PROJECTION_EVENT_POSITION_CONFLICT",
            )

    def test_event_frontier_lag_clears_only_after_verified_payload_ingestion(self):
        with TemporaryDirectory() as temporary:
            projection = MissionControlProjection.create_empty(
                Path(temporary) / "projection.sqlite3")
            broker = EventStreamBroker(
                stream_id="mission-control", epoch_id="epoch-a")
            first_payload, second_payload = SAMPLES[5], SAMPLES[6]
            first = broker.publish_record(
                EventFamily.LESSON_VISIT_COMPLETED, first_payload)
            second = broker.publish_record(
                EventFamily.CANDIDATE_ASSESSED, second_payload)
            self.assertIsNotNone(first)
            self.assertIsNotNone(second)
            frontier = broker.frontier()
            with self.assertRaises(BilqisError) as skipped:
                projection.ingest_event(second, second_payload)
            self.assertEqual(
                skipped.exception.context["reason"],
                "PROJECTION_FRONTIER_GAP_REBUILD_REQUIRED",
            )
            self.assertEqual(
                projection.frontier_status(
                    frontier.stream_id, frontier.epoch_id,
                    frontier.next_ordinal, frontier.latest_cursor_sha256,
                ).state,
                ProjectionFrontierState.EMPTY,
            )
            projection.ingest_event(first, first_payload)
            lagging = projection.frontier_status(
                frontier.stream_id, frontier.epoch_id,
                frontier.next_ordinal, frontier.latest_cursor_sha256,
            )
            self.assertEqual(lagging.state, ProjectionFrontierState.STALE)
            projection.ingest_event(second, second_payload)
            caught_up = projection.frontier_status(
                frontier.stream_id, frontier.epoch_id,
                frontier.next_ordinal, frontier.latest_cursor_sha256,
            )
            self.assertEqual(caught_up.state, ProjectionFrontierState.CURRENT)

    def test_large_event_payload_stays_external_by_ref_and_digest(self):
        with TemporaryDirectory() as temporary:
            root = Path(temporary)
            projection = MissionControlProjection.create_empty(
                root / "projection.sqlite3")
            blob = (b"CP06-EXTERNAL-PAYLOAD-" * 65536)
            digest = hashlib.sha256(blob).hexdigest()
            broker = EventStreamBroker(
                stream_id="mission-control", epoch_id="epoch-a")
            event = broker.publish_reference(
                EventFamily.WARNING_FAILURE,
                meta=SAMPLES[5].meta,
                payload_schema_version=SAMPLES[5].schema_version,
                payload_record_id="external-large-payload",
                payload_sha256=digest,
                payload_ref="artifact:external-large-payload",
            )
            self.assertIsNotNone(event)
            projection.ingest_records((event,))
            stored = projection.revisions(event.meta.record_id)[0]
            self.assertEqual(stored.payload_sha256, digest)
            self.assertEqual(
                stored.payload_ref, "artifact:external-large-payload")
            self.assertNotIn(blob[:4096], projection.path.read_bytes())
            status = projection.frontier_status(
                event.position.stream_id, event.position.epoch_id,
                event.position.ordinal + 1, event.position.cursor_sha256,
            )
            self.assertEqual(status.state, ProjectionFrontierState.EMPTY)



if __name__ == "__main__":
    unittest.main()
