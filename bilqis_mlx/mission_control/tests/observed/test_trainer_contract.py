"""Observed progress stays outside accepted and historical authority."""
from dataclasses import fields, replace
import unittest

from bilqis_mlx.mission_control import (
    AuthorityClass, CoverageState, MissionControlQueryCatalog, QueryFamily,
    QueryMode, QueryRequest, decode_record, encode_record,
)
from bilqis_mlx.mission_control.contracts.trainer import (
    CandidateStepPerformance, TrainerObservation, TrainerObservationV2,
    TrainerObservationV3,
)
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
        error_code=None, error_detail=None,
    )


def observation_v2():
    base = observation()
    return TrainerObservationV2(
        **{field.name: getattr(base, field.name) for field in fields(TrainerObservation)},
        candidate_step_wall_seconds=1.0,
        pre_neural_source_compile_wall_seconds=0.1,
        currentness_binding_wall_seconds=0.1,
        b11_preflight_wall_seconds=0.2,
        b11_autodiff_wall_seconds=0.4,
        optimizer_admission_wall_seconds=0.1,
        motif_staging_wall_seconds=0.0,
        evidence_capture_wall_seconds=0.01,
        candidate_terminal_step=False,
        c08_gradient_launches=1,
        c08_vectorized_microbatches=1,
        c08_materialization_barriers=1,
        c08_scalar_fallback_rows=0,
        c08_logical_batch_wall_seconds=0.7,
        c08_rows_per_gradient_launch=4.0,
        b11_provider_draw_count=16,
        b11_atlas_reload_count=4,
        logical_rows=4,
        compiled_positions=32,
        retention_wall_seconds=None,
        evidence_finalization_wall_seconds=None,
        publishing_wall_seconds=None,
    )


class TrainerContractTests(unittest.TestCase):
    def test_wire_roundtrip_preserves_observed_posture(self):
        record = observation()
        self.assertEqual(decode_record(encode_record(record)), record)
        self.assertEqual(record.meta.receipt_refs, ())
        self.assertNotIn('retained_optimizer_step', encode_record(record))

    def test_v2_roundtrip_adds_only_observational_performance(self):
        record = observation_v2()
        self.assertEqual(decode_record(encode_record(record)), record)
        self.assertEqual(record.schema_version,
                         'bilqis.bamf.mission-control.trainer-observation/v2')
        self.assertEqual(record.b11_provider_draw_count, 16)
        with self.assertRaises(ValueError):
            replace(record, b11_preflight_wall_seconds=-1.0)
        page = MissionControlQueryCatalog((record,)).query(
            QueryRequest(QueryFamily.RUN))
        self.assertEqual(page.records, (record,))

    def test_v3_roundtrip_preserves_completed_step_history(self):
        base = observation_v2()
        step = CandidateStepPerformance(
            candidate_step=1, candidate_optimizer_step=8,
            candidate_step_wall_seconds=1.0,
            pre_neural_source_compile_wall_seconds=0.1,
            currentness_binding_wall_seconds=0.1,
            b11_preflight_wall_seconds=0.2,
            b11_autodiff_wall_seconds=0.4,
            optimizer_admission_wall_seconds=0.1,
            motif_staging_wall_seconds=0.0,
            evidence_capture_wall_seconds=0.01,
            candidate_terminal_step=False,
            c08_gradient_launches=1,
            c08_vectorized_microbatches=1,
            c08_materialization_barriers=1,
            c08_scalar_fallback_rows=0,
            c08_logical_batch_wall_seconds=0.7,
            c08_rows_per_gradient_launch=4.0,
            b11_provider_draw_count=16,
            b11_atlas_reload_count=4,
            logical_rows=4,
            compiled_positions=32)
        record = TrainerObservationV3(
            **{field.name: getattr(base, field.name) for field in fields(TrainerObservationV2)},
            candidate_steps=(step,))
        self.assertEqual(decode_record(encode_record(record)), record)
        self.assertEqual(record.candidate_steps[0].candidate_optimizer_step, 8)

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
