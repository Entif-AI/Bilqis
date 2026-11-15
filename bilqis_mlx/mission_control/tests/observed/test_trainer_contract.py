"""Observed progress stays outside accepted and historical authority."""
from dataclasses import replace
import unittest

from bilqis_mlx.mission_control import (
    AuthorityClass, CoverageState, MissionControlQueryCatalog, QueryFamily,
    QueryMode, QueryRequest, decode_record, encode_record,
)
from bilqis_mlx.mission_control.contracts.trainer import TrainerObservation
from bilqis_mlx.mission_control.tests.samples import meta


def observation():
    return TrainerObservation(
        meta=replace(meta('observed:1'), authority=AuthorityClass.MEASURED,
                     coverage=CoverageState.PARTIAL, as_of=None,
                     evidence_refs=(), receipt_refs=()),
        observation_id='visit-1', revision=1, process_id=42, visit_index=1,
        posture='OBSERVED', phase='RETENTION', outcome='RUNNING',
        connection_state='LIVE', capability_id='A.IDENTITY', elapsed_ms=1200,
        candidate_optimizer_step=8, candidate_step=1, candidate_horizon=1,
        retention_completed=1, retention_total=4,
        retention_subject='A.IDENTITY', retention_role='parent',
        cpu_seconds=0.4, peak_rss_bytes=4096, disk_free_bytes=100000,
    )


class TrainerContractTests(unittest.TestCase):
    def test_wire_roundtrip_preserves_observed_posture(self):
        record = observation()
        self.assertEqual(decode_record(encode_record(record)), record)
        self.assertEqual(record.meta.receipt_refs, ())
        self.assertNotIn('retained_optimizer_step', encode_record(record))

    def test_invalid_progress_and_authority_are_rejected(self):
        for change in ({'retention_completed': 5}, {'candidate_step': 2},
                       {'posture': 'ACCEPTED'}, {'phase': 'UNKNOWN'},
                       {'elapsed_ms': -1}, {'cpu_seconds': float('nan')},
                       {'outcome': 'ACCEPTED'},
                       {'meta': replace(observation().meta, receipt_refs=('accepted:fake',))}):
            with self.subTest(change=change), self.assertRaises(ValueError):
                replace(observation(), **change)

    def test_current_run_contains_progress_but_historical_never_does(self):
        record = observation()
        catalog = MissionControlQueryCatalog((record,))
        self.assertEqual(catalog.query(QueryRequest(QueryFamily.RUN)).records, (record,))
        for family in (QueryFamily.RUN, QueryFamily.RECORD, QueryFamily.LINKS,
                       QueryFamily.REFERENCE):
            extras = {'record_id': record.meta.record_id} if family is QueryFamily.LINKS else {}
            if family is QueryFamily.REFERENCE:
                extras['reference'] = record.meta.source_refs[0]
            for bound in ({'mode': QueryMode.HISTORICAL, 'generation': 7}, {'generation': 7}, {'as_of': 118}):
                with self.subTest(family=family, bound=bound):
                    page = catalog.query(QueryRequest(family, **extras, **bound))
                    self.assertEqual(page.records, ())
                    self.assertEqual(page.links, ())

    def test_published_successor_keeps_parent_observation_in_current_history(self):
        from bilqis_mlx.mission_control.snapshots import RunContext
        record = replace(observation(), phase='COMPLETED', outcome='ACCEPTED',
                         connection_state='FINISHED')
        successor_run = replace(record.meta.run, generation=8,
                                generation_manifest_sha256='f' * 64)
        run = RunContext(replace(record.meta, record_id='run:8', run=successor_run),
                         'ACCEPTED', 9, 'FOUNDATION')
        page = MissionControlQueryCatalog((record, run)).query(QueryRequest(QueryFamily.RUN))
        self.assertIn(record, page.records)
        self.assertIn(run, page.records)
