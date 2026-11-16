"""CP07 composed CP03/CP04/CP06 recovery with bounded client delivery."""
from dataclasses import replace
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest

from bilqis_mlx.control_plane import (
    ControlPlaneClient, ControlPlaneService, EventFamily,
)
from bilqis_mlx.mission_control.projection import (
    MissionControlProjection, ProjectionFrontierState,
)
from bilqis_mlx.mission_control.query_contracts import QueryFamily, QueryRequest
from bilqis_mlx.mission_control.tests.samples import SAMPLES

from ..support import start_service


class CP07StreamRecoveryTests(unittest.TestCase):
    def _assert_snapshot_replay_and_projection(self, service, socket, projection, marker):
        with ControlPlaneClient(socket) as stream:
            snapshot = stream.query(QueryRequest(QueryFamily.CAPABILITY))
            self.assertEqual(snapshot["state"], "PRESENT")
            subscription = stream.subscribe_events()
            payloads = (SAMPLES[5], SAMPLES[6], SAMPLES[3], SAMPLES[15])
            families = (
                EventFamily.LESSON_VISIT_COMPLETED,
                EventFamily.CANDIDATE_ASSESSED,
                EventFamily.CAPABILITY_CHANGED,
                EventFamily.RESOURCE_HEALTH_SAMPLE,
            )
            first = service.publish_event(families[0], payloads[0])
            received_first = next(subscription)
            self.assertEqual(received_first.event_id, first.event_id)
            self.assertEqual(received_first.payload_record_id, "episode")

        emitted = [first]
        for family, payload in zip(families[1:3], payloads[1:3]):
            emitted.append(service.publish_event(family, payload))
        self.assertIsNone(service.publish_event(families[3], payloads[3]))
        emitted.append(service.flush_event_telemetry())
        with ControlPlaneClient(socket) as replay_client:
            replay = replay_client.subscribe_events(
                after_cursor=received_first.position.cursor_sha256)
            self.assertEqual(replay.acknowledgement["replay_count"], 3)
            recovered = tuple(next(replay) for _ in range(3))
        self.assertEqual(
            tuple(item.event_id for item in recovered),
            tuple(item.event_id for item in emitted[1:]))
        self.assertEqual([item.event_family for item in recovered],
                         [family.value for family in families[1:]])

        frontier = service.events.frontier()
        self.assertEqual(projection.frontier_status(
            frontier.stream_id, frontier.epoch_id,
            frontier.next_ordinal, frontier.latest_cursor_sha256,
        ).state, ProjectionFrontierState.EMPTY)
        for envelope, payload in zip(emitted, payloads):
            projection.ingest_event(envelope, payload)
            projection.ingest_event(envelope, payload)
        self.assertEqual(projection.frontier_status(
            frontier.stream_id, frontier.epoch_id,
            frontier.next_ordinal, frontier.latest_cursor_sha256,
        ).state, ProjectionFrontierState.CURRENT)
        self.assertEqual(projection.stats().events, 4)
        self.assertEqual(marker.read_bytes(),
                         b"fixture:checkpoint-never-writable-by-cp")
        return snapshot, emitted, received_first

    def _assert_expired_replay_requires_snapshot(
        self, service, socket, projection, received_first,
    ):
        for index_id in range(5):
            payload = replace(SAMPLES[5], meta=replace(
                SAMPLES[5].meta,
                record_id=f"fixture:episode:new:{index_id}",
                materialized_at=123 + index_id))
            service.publish_event(EventFamily.LESSON_VISIT_COMPLETED, payload)
        after = service.events.frontier()
        self.assertEqual(projection.frontier_status(
            after.stream_id, after.epoch_id,
            after.next_ordinal, after.latest_cursor_sha256,
        ).state, ProjectionFrontierState.STALE)
        with ControlPlaneClient(socket) as expired_client:
            gap = expired_client.subscribe_events(
                after_cursor=received_first.position.cursor_sha256)
            self.assertEqual(gap.gap["state"], "fresh-snapshot-required")
            self.assertEqual(gap.gap["reason"], "cursor-unavailable")

    def test_snapshot_delta_replay_gap_and_projection_frontier(self):
        with TemporaryDirectory() as temporary:
            root = Path(temporary)
            run = root / "fixture-run"
            run.mkdir()
            marker = run / "accepted-checkpoint"
            marker.write_bytes(b"fixture:checkpoint-never-writable-by-cp")
            index = root / "projection.sqlite3"
            projection = MissionControlProjection.rebuild(index, SAMPLES[:16])
            socket = root / "cp.sock"
            service = ControlPlaneService(
                run, socket, query_source=projection.catalog,
                event_retention_limit=4, event_queue_limit=4,
                event_heartbeat_seconds=0.02,
            )
            thread = start_service(service)
            try:
                snapshot, emitted, received_first = self._assert_snapshot_replay_and_projection(
                    service, socket, projection, marker)
                self._assert_expired_replay_requires_snapshot(
                    service, socket, projection, received_first)
            finally:
                service.shutdown()
                thread.join(2)

            # A service restart changes its stream epoch but neither pointer
            # custody nor the CP06 query records it derived from source inputs.
            restarted = ControlPlaneService(
                run, socket, query_source=projection.catalog)
            restart_thread = start_service(restarted)
            try:
                with ControlPlaneClient(socket) as client:
                    self.assertEqual(client.query(
                        QueryRequest(QueryFamily.CAPABILITY))["records"],
                        snapshot["records"])
                    gap = client.subscribe_events(
                        after_cursor=emitted[-1].position.cursor_sha256)
                    self.assertEqual(gap.gap["state"], "fresh-snapshot-required")
            finally:
                restarted.shutdown()
                restart_thread.join(2)
            self.assertEqual(marker.read_bytes(),
                             b"fixture:checkpoint-never-writable-by-cp")


if __name__ == "__main__":
    unittest.main()
