"""Observed snapshots remain bounded, non-authoritative and current-only."""
import json
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest
from unittest.mock import patch

from bilqis_mlx.control_plane.observed import observed_records, publish_observed_events
from bilqis_mlx.mission_control.tests.samples import RUN


def visit(**changes):
    return {
        'observation_id': 'visit-1', 'revision': 1, 'process_id': 42,
        'run_id': RUN.run_id, 'parent_manifest_sha256': RUN.generation_manifest_sha256,
        'visit_index': 1, 'observed_at': 100000, 'elapsed_ms': 1400,
        'phase': 'RETENTION', 'outcome': 'RUNNING', 'capability_id': 'A.IDENTITY',
        'candidate_optimizer_step': 8, 'candidate_step': 1, 'candidate_horizon': 1,
        'retention_completed': 1, 'retention_total': 4,
        'retention_subject': 'A.IDENTITY', 'retention_role': 'parent',
        'cpu_seconds': 0.5, 'peak_rss_bytes': 4096, 'disk_free_bytes': 100000,
        **changes,
    }


def performance():
    return {
        'candidate_step_wall_seconds': 1.2,
        'pre_neural_source_compile_wall_seconds': 0.1,
        'currentness_binding_wall_seconds': 0.2,
        'b11_preflight_wall_seconds': 0.3,
        'b11_autodiff_wall_seconds': 0.4,
        'optimizer_admission_wall_seconds': 0.1,
        'motif_staging_wall_seconds': 0.0,
        'evidence_capture_wall_seconds': 0.01,
        'candidate_terminal_step': False,
        'c08_gradient_launches': 1,
        'c08_vectorized_microbatches': 1,
        'c08_materialization_barriers': 1,
        'c08_scalar_fallback_rows': 0,
        'c08_logical_batch_wall_seconds': 0.7,
        'c08_rows_per_gradient_launch': 4.0,
        'b11_provider_draw_count': 16,
        'b11_atlas_reload_count': 4,
        'logical_rows': 4,
        'compiled_positions': 32,
        'retention_wall_seconds': None,
        'evidence_finalization_wall_seconds': None,
        'publishing_wall_seconds': None,
    }


class ObservedSourceTests(unittest.TestCase):
    def setUp(self):
        self.temp = TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)

    def write(self, *rows, schema='bilqis.bamf.trainer-observed/v1'):
        (self.root / 'trainer-observed.json').write_text(json.dumps({
            'schema': schema, 'visits': list(rows),
        }))

    def test_live_snapshot_has_measured_posture_without_accepted_receipts(self):
        self.write(visit())
        with patch('bilqis_mlx.control_plane.observed.source.process_exists', return_value=True):
            records = observed_records(self.root, (RUN,), now_ms=101000)
        self.assertEqual(len(records), 1)
        row = records[0]
        self.assertEqual(row.posture, 'OBSERVED')
        self.assertEqual(row.connection_state, 'LIVE')
        self.assertEqual(row.meta.receipt_refs, ())
        self.assertEqual(row.meta.run, RUN)

    def test_v2_snapshot_projects_stage_metrics_without_changing_v1_reader(self):
        self.write(
            visit(**performance()), schema='bilqis.bamf.trainer-observed/v2')
        with patch('bilqis_mlx.control_plane.observed.source.process_exists', return_value=True):
            row = observed_records(self.root, (RUN,), now_ms=101000)[0]
        self.assertEqual(
            row.schema_version,
            'bilqis.bamf.mission-control.trainer-observation/v2')
        self.assertEqual(row.b11_provider_draw_count, 16)
        self.assertEqual(row.c08_gradient_launches, 1)
        self.assertEqual(row.compiled_positions, 32)

    def test_v3_snapshot_projects_bounded_step_history(self):
        step = {key: value for key, value in performance().items()
                if key not in {'retention_wall_seconds',
                               'evidence_finalization_wall_seconds',
                               'publishing_wall_seconds'}}
        step.update(candidate_step=1, candidate_optimizer_step=8)
        self.write(
            visit(**performance(), candidate_steps=[step]),
            schema='bilqis.bamf.trainer-observed/v3')
        with patch('bilqis_mlx.control_plane.observed.source.process_exists', return_value=True):
            row = observed_records(self.root, (RUN,), now_ms=101000)[0]
        self.assertEqual(row.schema_version,
                         'bilqis.bamf.mission-control.trainer-observation/v3')
        self.assertEqual(len(row.candidate_steps), 1)
        self.assertEqual(row.candidate_steps[0].candidate_step, 1)
        self.assertEqual(row.candidate_steps[0].b11_provider_draw_count, 16)

    def test_millisecond_heartbeat_projects_unix_seconds_without_changing_liveness_age(self):
        heartbeat_ms = 1_763_218_800_123
        self.write(visit(observed_at=heartbeat_ms))
        with patch('bilqis_mlx.control_plane.observed.source.process_exists', return_value=True):
            row = observed_records(self.root, (RUN,), now_ms=heartbeat_ms + 9_999)[0]
        self.assertEqual(row.connection_state, 'LIVE')
        self.assertEqual(row.meta.observed_at, heartbeat_ms // 1000)
        self.assertEqual(row.meta.materialized_at, heartbeat_ms // 1000)
        with patch('bilqis_mlx.control_plane.observed.source.process_exists', return_value=True):
            stale = observed_records(self.root, (RUN,), now_ms=heartbeat_ms + 10_001)[0]
        self.assertEqual(stale.connection_state, 'DISCONNECTED')

    def test_dead_or_expired_producer_is_disconnected_and_terminal_is_finished(self):
        self.write(visit())
        with patch('bilqis_mlx.control_plane.observed.source.process_exists', return_value=False):
            self.assertEqual(observed_records(self.root, (RUN,), now_ms=100001)[0].connection_state,
                             'DISCONNECTED')
        with patch('bilqis_mlx.control_plane.observed.source.process_exists', return_value=True):
            self.assertEqual(observed_records(self.root, (RUN,), now_ms=111000)[0].connection_state,
                             'DISCONNECTED')
        self.write(visit(phase='COMPLETED', outcome='REJECTED'))
        self.assertEqual(observed_records(self.root, (RUN,), now_ms=999000)[0].connection_state,
                         'FINISHED')

    def test_invalid_rows_do_not_hide_valid_rows_or_enter_authority(self):
        self.write(visit(), visit(observation_id='wrong-run', run_id='elsewhere'),
                   visit(observation_id='wrong-parent', parent_manifest_sha256='f' * 64),
                   visit(observation_id='invalid', retention_completed=99))
        rows = observed_records(self.root, (RUN,), now_ms=100000)
        self.assertEqual([row.observation_id for row in rows], ['visit-1'])
        for content in ('x' * 65537, '{'):
            (self.root / 'trainer-observed.json').write_text(content)
            self.assertEqual(observed_records(self.root, (RUN,)), ())

    def test_excess_history_keeps_newest_bounded_observations(self):
        rows = [visit(observation_id=f'visit-{index}', revision=index)
                for index in range(1, 11)]
        self.write(*rows)
        projected = observed_records(self.root, (RUN,), now_ms=100000)
        self.assertEqual(len(projected), 8)
        self.assertEqual(projected[0].observation_id, 'visit-3')
        self.assertEqual(projected[-1].observation_id, 'visit-10')

    def test_liveness_transition_publishes_without_new_producer_revision(self):
        from types import SimpleNamespace
        emitted = []
        service = SimpleNamespace(publish_event=lambda *args, **kw: emitted.append((args, kw)))
        self.write(visit())
        with patch('bilqis_mlx.control_plane.observed.source.process_exists', return_value=True):
            live = observed_records(self.root, (RUN,), now_ms=100000)
        dead = observed_records(self.root, (RUN,), now_ms=111000)
        publish_observed_events(service, live)
        publish_observed_events(service, live)
        publish_observed_events(service, dead)
        publish_observed_events(service, dead)
        self.assertEqual(len(emitted), 2)
        self.assertNotEqual(emitted[0][1]['event_id'], emitted[1][1]['event_id'])
