"""CP04 live event replay, gap recovery, backpressure, and coalescing."""
from dataclasses import replace
from pathlib import Path
from tempfile import TemporaryDirectory
from threading import Thread
import unittest

from bilqis_mlx.control_plane import (
    EVENT_GAP_SCHEMA, ControlPlaneClient, ControlPlaneService, EventFamily,
    EventIdentityDeduplicator, EventStreamBroker,
)
from bilqis_mlx.errors import BilqisError
from bilqis_mlx.mission_control.codec import (
    canonical_json, decode_json, decode_record, encode_record,
)
from bilqis_mlx.mission_control.events import LearningEpisode
from bilqis_mlx.mission_control.observability import (
    GenerationManifest, ResourceSample,
)
from bilqis_mlx.mission_control.tests.samples import SAMPLES

from .support import start_service


def _sample(record_type):
    return next(record for record in SAMPLES if type(record) is record_type)


def _at(record, name: str, materialized_at: int):
    return replace(
        record,
        meta=replace(
            record.meta,
            record_id=name,
            materialized_at=materialized_at,
        ),
    )


class ControlPlaneEventStreamTests(unittest.TestCase):
    def test_required_cp04_event_families_are_explicit(self):
        self.assertEqual(
            [family.value for family in EventFamily],
            [
                "run.state.changed",
                "run.trainer.observed",
                "lesson.visit.started",
                "lesson.visit.completed",
                "candidate.started",
                "candidate.assessed",
                "candidate.retained",
                "candidate.rejected",
                "capability.changed",
                "checkpoint.committed",
                "checkpoint.recovered",
                "semantic.coverage.changed",
                "memory.changed",
                "teacher.strategy.outcome",
                "salience.observed",
                "correction.requalification.changed",
                "resource.health.sample",
                "warning.failure",
                "operator.action.state",
            ],
        )

    def test_live_client_receives_event_without_snapshot_polling(self):
        with TemporaryDirectory() as temporary:
            root = Path(temporary)
            service = ControlPlaneService(
                root / "missing-run",
                root / "cp.sock",
                event_heartbeat_seconds=0.02,
            )
            thread = start_service(service)
            try:
                with ControlPlaneClient(root / "cp.sock") as client:
                    frontier = client.request("event-frontier")
                    self.assertTrue(frontier["accepted"])
                    self.assertEqual(frontier["next_ordinal"], 0)
                    subscription = client.subscribe_events()
                    self.assertTrue(subscription.acknowledgement["accepted"])
                    self.assertEqual(
                        subscription.acknowledgement["replay_count"], 0)

                    episode = _sample(LearningEpisode)
                    emitted = service.publish_event(
                        EventFamily.LESSON_VISIT_COMPLETED, episode)
                    observed = next(subscription)
                    self.assertEqual(observed.event_id, emitted.event_id)
                    self.assertEqual(
                        observed.event_family,
                        EventFamily.LESSON_VISIT_COMPLETED.value,
                    )
                    self.assertEqual(
                        observed.payload_record_id, episode.meta.record_id)
            finally:
                service.shutdown()
                thread.join(2)

    def test_disconnect_reconnect_replays_missing_events_and_projection_deduplicates(self):
        with TemporaryDirectory() as temporary:
            root = Path(temporary)
            service = ControlPlaneService(root / "missing-run", root / "cp.sock")
            thread = start_service(service)
            try:
                first_client = ControlPlaneClient(root / "cp.sock")
                first_client.connect()
                first_subscription = first_client.subscribe_events()
                first = service.publish_event(
                    EventFamily.LESSON_VISIT_STARTED,
                    _at(_sample(LearningEpisode), "episode:first", 121),
                )
                observed_first = next(first_subscription)
                first_client.close()

                second = service.publish_event(
                    EventFamily.LESSON_VISIT_COMPLETED,
                    _at(_sample(LearningEpisode), "episode:second", 122),
                )
                with ControlPlaneClient(root / "cp.sock") as replay_client:
                    replay = replay_client.subscribe_events(
                        after_cursor=observed_first.position.cursor_sha256)
                    self.assertEqual(replay.acknowledgement["replay_count"], 1)
                    observed_second = next(replay)

                self.assertEqual(observed_second.event_id, second.event_id)
                projection = EventIdentityDeduplicator()
                projected = []
                for delivered in (
                    observed_first, observed_second, observed_second,
                ):
                    if projection.accept(delivered):
                        projected.append(delivered.payload_record_id)
                self.assertEqual(
                    projected, ["episode:first", "episode:second"])
                self.assertEqual(first.position.ordinal, 0)
                self.assertEqual(second.position.ordinal, 1)
            finally:
                service.shutdown()
                thread.join(2)

    def test_expired_cursor_requires_fresh_snapshot(self):
        broker = EventStreamBroker(retention_limit=2)
        episode = _sample(LearningEpisode)
        first = broker.publish_record(
            EventFamily.LESSON_VISIT_STARTED, _at(episode, "episode:1", 121))
        broker.publish_record(
            EventFamily.LESSON_VISIT_COMPLETED, _at(episode, "episode:2", 122))
        broker.publish_record(
            EventFamily.LESSON_VISIT_COMPLETED, _at(episode, "episode:3", 123))

        opened = broker.open_subscription(first.position.cursor_sha256)
        self.assertIsNone(opened.subscription)
        self.assertEqual(opened.acknowledgement["schema"], EVENT_GAP_SCHEMA)
        self.assertFalse(opened.acknowledgement["accepted"])
        self.assertEqual(
            opened.acknowledgement["state"], "fresh-snapshot-required")
        self.assertEqual(
            opened.acknowledgement["reason"], "cursor-unavailable")

    def test_malformed_cursor_is_rejected_not_misreported_as_replay_gap(self):
        with TemporaryDirectory() as temporary:
            root = Path(temporary)
            service = ControlPlaneService(root / "missing-run", root / "cp.sock")
            thread = start_service(service)
            try:
                with ControlPlaneClient(root / "cp.sock") as client:
                    with self.assertRaises(BilqisError) as caught:
                        client.subscribe_events(after_cursor="not-a-cursor")
                    self.assertEqual(
                        caught.exception.code,
                        "SCHOOL.BAMF_CONTROL_PLANE.INVALID",
                    )
                    self.assertEqual(
                        caught.exception.context["reason"],
                        "CONTROL_PLANE_EVENT_CURSOR_INVALID",
                    )
            finally:
                service.shutdown()
                thread.join(2)

    def test_invalid_stream_config_fails_before_socket_ownership(self):
        with TemporaryDirectory() as temporary:
            root = Path(temporary)
            socket_path = root / "cp.sock"
            with self.assertRaises(BilqisError) as caught:
                ControlPlaneService(
                    root / "missing-run",
                    socket_path,
                    event_queue_limit=0,
                )
            self.assertEqual(
                caught.exception.context["reason"],
                "CONTROL_PLANE_EVENT_CONFIG_INVALID",
            )
            service = ControlPlaneService(root / "missing-run", socket_path)
            service.server_close()

    def test_reference_path_emits_families_without_inventing_payload_schema(self):
        broker = EventStreamBroker()
        episode = _sample(LearningEpisode)
        emitted = []
        for index, family in enumerate((
            EventFamily.CANDIDATE_STARTED,
            EventFamily.WARNING_FAILURE,
        )):
            emitted.append(broker.publish_reference(
                family,
                meta=_at(episode, f"reference:{index}", 121 + index).meta,
                payload_schema_version=episode.schema_version,
                payload_record_id=f"authoritative:{index}",
                payload_sha256=str(index + 5) * 64,
                payload_ref=f"evidence:authoritative:{index}",
                event_id=f"event-reference-{index}",
            ))
        self.assertEqual(
            [event.event_family for event in emitted],
            [
                EventFamily.CANDIDATE_STARTED.value,
                EventFamily.WARNING_FAILURE.value,
            ],
        )
        self.assertEqual(
            [event.payload_record_id for event in emitted],
            ["authoritative:0", "authoritative:1"],
        )

    def test_slow_consumer_overflow_marks_gap_without_blocking_publisher(self):
        broker = EventStreamBroker(
            retention_limit=32, subscriber_queue_limit=1)
        opened = broker.open_subscription(None)
        subscription = opened.subscription
        episode = _sample(LearningEpisode)

        def publish_many():
            for index in range(12):
                broker.publish_record(
                    EventFamily.LESSON_VISIT_COMPLETED,
                    _at(episode, f"episode:{index}", 121 + index),
                )

        publisher = Thread(target=publish_many)
        publisher.start()
        publisher.join(1)
        self.assertFalse(publisher.is_alive())
        gap = subscription.next_record(0.1)
        self.assertEqual(gap["schema"], EVENT_GAP_SCHEMA)
        self.assertEqual(gap["reason"], "slow-consumer")
        self.assertEqual(gap["state"], "fresh-snapshot-required")
        subscription.close()

    def test_resource_samples_coalesce_before_cursor_assignment(self):
        broker = EventStreamBroker(resource_bucket_span=10)
        resource = _sample(ResourceSample)
        for materialized_at in (120, 121, 122):
            broker.publish_record(
                EventFamily.RESOURCE_HEALTH_SAMPLE,
                _at(
                    resource,
                    f"resources:{materialized_at}",
                    materialized_at,
                ),
            )
        self.assertEqual(broker.frontier().next_ordinal, 0)
        emitted = broker.flush_resource_samples()
        self.assertEqual(broker.frontier().next_ordinal, 1)
        self.assertEqual(broker.coalesced_resource_samples, 2)
        self.assertEqual(emitted.payload_record_id, "resources:122")

    def test_ordering_is_ingress_order_and_times_roundtrip_literally(self):
        broker = EventStreamBroker()
        episode = _sample(LearningEpisode)
        later_time = broker.publish_record(
            EventFamily.LESSON_VISIT_STARTED,
            _at(episode, "episode:later-time", 130),
        )
        earlier_time = broker.publish_record(
            EventFamily.LESSON_VISIT_COMPLETED,
            _at(episode, "episode:earlier-time", 125),
        )
        decoded_later = decode_record(encode_record(later_time))
        decoded_earlier = decode_record(encode_record(earlier_time))

        self.assertEqual(
            (decoded_later.position.ordinal, decoded_earlier.position.ordinal),
            (0, 1),
        )
        self.assertEqual(
            (
                decoded_later.meta.materialized_at,
                decoded_earlier.meta.materialized_at,
            ),
            (130, 125),
        )
        self.assertEqual(
            decoded_earlier.position.previous_cursor_sha256,
            decoded_later.position.cursor_sha256,
        )

    def test_stream_loss_never_owns_checkpoint_recovery(self):
        manifest = _sample(GenerationManifest)
        with TemporaryDirectory() as temporary:
            checkpoint = Path(temporary) / "generation.json"
            checkpoint.write_bytes(canonical_json(manifest))
            broker = EventStreamBroker(epoch_id="epoch-before-loss")
            event = broker.publish_record(
                EventFamily.CHECKPOINT_COMMITTED, manifest)
            old_cursor = event.position.cursor_sha256

            recovered_broker = EventStreamBroker(epoch_id="epoch-after-loss")
            opened = recovered_broker.open_subscription(old_cursor)
            self.assertFalse(opened.acknowledgement["accepted"])
            self.assertEqual(
                opened.acknowledgement["state"], "fresh-snapshot-required")
            self.assertEqual(decode_json(checkpoint.read_bytes()), manifest)


if __name__ == "__main__":
    unittest.main()
