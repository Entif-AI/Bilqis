"""Observed progress stays outside accepted and historical authority."""
from dataclasses import fields, replace
import unittest

from bilqis_mlx.mission_control import (
    AuthorityClass, CoverageState, MissionControlQueryCatalog, QueryFamily,
    QueryMode, QueryRequest, decode_record, encode_record,
)
from bilqis_mlx.mission_control.contracts.trainer import (
    CandidateStepPerformance, GeneratedGradeEvidence, RetentionStageTiming,
    TrainerObservation, TrainerObservationV2, TrainerObservationV3, TrainerObservationV4,
    VisitCapabilityScore, VisitEvidence, VisitRankingEvidence,
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

    def test_v4_roundtrip_carries_typed_visit_evidence_and_unknown_grade_rationale(self):
        base = observation_v2()
        v3 = TrainerObservationV3(
            **{field.name: getattr(base, field.name) for field in fields(TrainerObservationV2)},
            candidate_steps=())
        score = VisitCapabilityScore('Z.NOVEL', 'MEASURED', 2, 2, 3, 4, 1, None)
        visit = VisitEvidence(
            state='COMPLETE', grade_id='Z', grade_definition_id=None,
            grade_definition_version=None, capability_id='Z.NOVEL',
            semantic_ids=('sem:z',), prerequisites=('Y.PREV',),
            semantic_prerequisites=('sem:y',), constituents=('Y.PREV',),
            lawful_frontier_sha256='1' * 64, a09_snapshot_sha256='2' * 64,
            a09_closure_sha256='3' * 64,
            ranking=VisitRankingEvidence('4' * 64, (0, 1, 2), (False, True, True),
                                         2, 7, 3, 'option-z'),
            teacher_visit_id='visit-z', teacher_policy_key='how-z',
            selected_option_id='option-z', lesson_roles=(), target=score,
            affected_scope_state='UNKNOWN', affected=(),
            protected_scope_state='PARTIAL', protected=(),
            retention_economics_state='PARTIAL',
            retention_policy_sha256='5' * 64, threshold_refs=(), budget_refs=(), probe_each=6,
            baseline_measured_capabilities=('Z.NOVEL',),
            baseline_unmeasured_capabilities=(), baseline_epoch_sha256='6' * 64,
            decision='REJECT', blocking_capability='Z.NOVEL', blocking_scope=None,
            reason='NO_MEASURABLE_TARGET_GAIN', human_reason='No measurable target gain',
            candidate_evidence_sha256='7' * 64,
            candidate_evidence_file='teacher-observations/objects/' + '7' * 64 + '.json')
        grade = GeneratedGradeEvidence(
            state='UNKNOWN', grade_id='Z', proposal_id=None, definition_id=None,
            definition_version=None, predecessor_definition_id=None,
            learner_evidence_epoch=None, factory_release_sha256=None, policy_epoch=None,
            a08_provenance=(), a09_provenance=(), selected_semantic_ids=(), members=(),
            developmental_slope_state='UNKNOWN', synthesis_dimensions=(),
            representative_coverage=None, downstream_unlocks=None, constituent_rationale=None,
            required_bridges=(), deferred_candidates=(), holds=(),
            predecessor_certification_receipt=None)
        record = TrainerObservationV4(
            **{field.name: getattr(v3, field.name) for field in fields(TrainerObservationV3)},
            planning_wall_seconds=0.1, source_materialization_wall_seconds=0.02,
            target_evaluation_wall_seconds=0.2, protected_retention_wall_seconds=0.3,
            broad_certification_wall_seconds=None, visit_evidence=visit, generated_grade_evidence=grade,
            retention_stage_timings=(RetentionStageTiming('fixed_school', 'candidate', 0.2),))
        self.assertEqual(decode_record(encode_record(record)), record)
        self.assertEqual(record.visit_evidence.grade_id, 'Z')
        self.assertEqual(record.generated_grade_evidence.state, 'UNKNOWN')

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
