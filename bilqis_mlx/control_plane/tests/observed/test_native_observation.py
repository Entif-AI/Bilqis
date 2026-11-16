"""Production snapshot/query/subscription integration on disposable custody."""
import unittest

from bilqis_mlx.control_plane import EventStreamBroker
from bilqis_mlx.control_plane.native_source import native_query_catalog, refresh_native_events
from bilqis_mlx.mission_control import QueryFamily, QueryMode, QueryRequest
from bilqis_mlx.mission_control.contracts.trainer import TrainerObservation as ProgressRecord
from bilqis_mlx.runtime.bamf_operator.telemetry import TrainerObservation
from bilqis_mlx.control_plane.tests.cp07.native_source_support import NativeSourceFixture


class ObservedService:
    def __init__(self, run_dir):
        self.run_dir = run_dir
        self.events = EventStreamBroker(retention_limit=2)

    def publish_event(self, family, record, **kwargs):
        return self.events.publish_record(family, record, **kwargs)

    def flush_event_telemetry(self):
        return self.events.flush_resource_samples()


class NativeObservationTests(NativeSourceFixture, unittest.TestCase):
    def test_generation_zero_progress_streams_and_rejection_never_advances_custody(self):
        self.parent()
        before = (self.run / 'bamf-state.json').read_bytes()
        service = ObservedService(self.run)
        with TrainerObservation(self.run, 1) as producer:
            producer.update(phase='RETENTION', capability_id='A.IDENTITY',
                            candidate_step=1, candidate_horizon=1,
                            retention_completed=1, retention_total=4,
                            retention_subject='A.IDENTITY', retention_role='parent')
            page = native_query_catalog(self.run).query(QueryRequest(QueryFamily.RUN))
            observed = next(row for row in page.records if isinstance(row, ProgressRecord))
            self.assertEqual(observed.meta.run.generation, 0)
            self.assertEqual(observed.retention_completed, 1)
            initial = refresh_native_events(service)
            self.assertEqual([row.event_family for row in initial], ['run.trainer.observed'])
            opened = service.events.open_subscription(initial[0].position.cursor_sha256)
            producer.update(retention_completed=2, retention_role='candidate')
            refresh_native_events(service)
            event = opened.subscription.next_record(0.1)
            self.assertEqual(event['event_family'], 'run.trainer.observed')
            producer.finish('REJECTED')
            refresh_native_events(service)
            opened.subscription.close()
        self.assertFalse(service.events.open_subscription(initial[0].position.cursor_sha256).acknowledgement['accepted'])
        current = native_query_catalog(self.run).query(QueryRequest(QueryFamily.RUN))
        rejected = next(row for row in current.records if isinstance(row, ProgressRecord))
        self.assertEqual(rejected.outcome, 'REJECTED')
        self.assertEqual(rejected.connection_state, 'FINISHED')
        historical = native_query_catalog(self.run).query(QueryRequest(
            QueryFamily.RUN, mode=QueryMode.HISTORICAL, generation=0))
        self.assertFalse(any(isinstance(row, ProgressRecord) for row in historical.records))
        self.assertEqual((self.run / 'bamf-state.json').read_bytes(), before)

    def test_actual_successor_publication_preserves_observed_parent_history(self):
        self.parent()
        with TrainerObservation(self.run, 1) as producer:
            producer.update(phase='PUBLISHING', capability_id='A.NATIVE',
                            candidate_step=1, candidate_horizon=1)
            self.publish_successor()
            producer.finish('ACCEPTED')
        page = native_query_catalog(self.run).query(QueryRequest(QueryFamily.RUN))
        observed = next(row for row in page.records if isinstance(row, ProgressRecord))
        self.assertEqual(observed.outcome, 'ACCEPTED')
        self.assertEqual(observed.meta.run.generation, 0)
        self.assertEqual(max(row.meta.run.generation for row in page.records), 1)
        episode = native_query_catalog(self.run).query(QueryRequest(QueryFamily.EPISODE))
        self.assertEqual(sum(getattr(row, 'outcome', None) == 'ACCEPTED'
                             for row in episode.records), 1)
