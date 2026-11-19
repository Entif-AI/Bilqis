import json
from pathlib import Path
from tempfile import TemporaryDirectory
import time
import unittest

from bilqis_mlx.errors import ErrorBus
from bilqis_mlx.runtime.topology_v2.spec import ModelTopologySpecV2
from bilqis_mlx.runtime.b11_source_execution_authority import (
    B11SourceExecutionAuthority, require_b11_source_execution_authority_current,
)
from bilqis_mlx.runtime.bamf_operator.telemetry import TrainerObservation


class TrainerObservationTests(unittest.TestCase):
    def test_bounded_lifecycle_and_exception(self):
        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / 'bamf-state.json').write_text(json.dumps({'run_id': 'run', 'manifest_sha256': 'a' * 64}))
            for i in range(9):
                with TrainerObservation(root, i + 1, heartbeat_seconds=0.01) as obs:
                    obs.update(phase='TRAINING', capability_id='cap', candidate_step=0, candidate_horizon=1)
                    time.sleep(0.025)
                    obs.update(candidate_step=1)
                    obs.finish('HELD')
            data = json.loads((root / 'trainer-observed.json').read_text())
            self.assertEqual(data['schema'], 'bilqis.bamf.trainer-observed/v7')
            self.assertEqual(len(data['visits']), 8)
            self.assertEqual(data['visits'][-1]['outcome'], 'HELD')
            self.assertGreater(data['visits'][-1]['revision'], 3)
            self.assertEqual(data['visits'][-1]['candidate_step'], 1)
            self.assertEqual(data['visits'][-1]['run_id'], 'run')
            self.assertIsNone(data['visits'][-1]['b11_preflight_wall_seconds'])
            self.assertEqual(data['visits'][-1]['candidate_steps'], [])
            with self.assertRaises(KeyboardInterrupt):
                with TrainerObservation(root, 10):
                    raise KeyboardInterrupt()
            interrupted = json.loads((root / 'trainer-observed.json').read_text())['visits'][-1]
            self.assertEqual(interrupted['outcome'], 'INTERRUPTED')
            self.assertEqual(interrupted['error_code'], 'KeyboardInterrupt')

            with self.assertRaises(ValueError):
                with TrainerObservation(root, 11):
                    B11SourceExecutionAuthority()
            failed = json.loads((root / 'trainer-observed.json').read_text())['visits'][-1]
            self.assertEqual(failed['outcome'], 'INTERRUPTED')
            self.assertEqual(failed['error_code'], 'SCHOOL.BAMF_B11.SOURCE_EXECUTION_AUTHORITY_INVALID')
            self.assertEqual(failed['error_detail'], 'B11_SOURCE_EXECUTION_AUTHORITY_CALLER_CONSTRUCTION_FORBIDDEN')


    def test_activity_tracks_current_progress_and_its_elapsed_clock(self):
        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            with TrainerObservation(root, 1, heartbeat_seconds=60) as obs:
                obs.update(activity='planner: compiling semantic curriculum')
                time.sleep(0.002)
                obs.update()
                current = json.loads((root / 'trainer-observed.json').read_text())['visits'][-1]
                self.assertEqual(current['activity'], 'planner: compiling semantic curriculum')
                self.assertGreater(current['activity_elapsed_ms'], 0)
                obs.update(activity='planner: ranking next bounded target')
                changed = json.loads((root / 'trainer-observed.json').read_text())['visits'][-1]
                self.assertEqual(changed['activity'], 'planner: ranking next bounded target')
                self.assertLessEqual(changed['activity_elapsed_ms'], 2)

    def test_active_step_ticks_live_and_completed_steps_are_retained(self):
        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            with TrainerObservation(root, 1, heartbeat_seconds=60) as obs:
                obs.update(phase='TRAINING', capability_id='A.IDENTITY',
                           candidate_step=0, candidate_horizon=2)
                obs.begin_step(1, 8)
                time.sleep(0.002)
                obs.update()
                running = json.loads((root / 'trainer-observed.json').read_text())['visits'][-1]
                self.assertGreater(running['candidate_step_wall_seconds'], 0)
                self.assertEqual(running['candidate_step'], 1)
                obs.complete_step(
                    candidate_step=1, candidate_optimizer_step=8,
                    candidate_step_wall_seconds=0.5,
                    pre_neural_source_compile_wall_seconds=0.1,
                    currentness_binding_wall_seconds=0.01,
                    accepted_currentness_refresh_wall_seconds=0.001,
                    accepted_parent_currentness_wall_seconds=0.001,
                    lawful_frontier_currentness_wall_seconds=0.002,
                    teacher_visit_currentness_wall_seconds=0.002,
                    source_currentness_wall_seconds=0.001,
                    candidate_binding_wall_seconds=0.003,
                    b11_preflight_wall_seconds=0.1,
                    b11_autodiff_wall_seconds=0.2,
                    optimizer_admission_wall_seconds=0.05,
                    motif_staging_wall_seconds=0.0,
                    evidence_capture_wall_seconds=0.01,
                    candidate_terminal_step=False,
                    c08_gradient_launches=1, c08_vectorized_microbatches=1,
                    c08_materialization_barriers=1, c08_scalar_fallback_rows=0,
                    c08_logical_batch_wall_seconds=0.3,
                    c08_rows_per_gradient_launch=4.0,
                    b11_provider_draw_count=4, b11_atlas_reload_count=1,
                    logical_rows=4, compiled_positions=32)
                obs.begin_step(2, 9)
                final = json.loads((root / 'trainer-observed.json').read_text())['visits'][-1]
                self.assertEqual(len(final['candidate_steps']), 1)
                self.assertEqual(final['candidate_steps'][0]['candidate_step'], 1)
                self.assertEqual(final['candidate_steps'][0]['candidate_step_wall_seconds'], 0.5)
                self.assertEqual(
                    final['candidate_steps'][0]['lawful_frontier_currentness_wall_seconds'],
                    0.002)
                self.assertEqual(final['candidate_step'], 2)

    def test_snapshot_trims_old_step_detail_before_disabling_live_observation(self):
        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / 'bamf-state.json').write_text(json.dumps({
                'run_id': 'run', 'manifest_sha256': 'a' * 64,
            }))
            with TrainerObservation(root, 1, heartbeat_seconds=60) as obs:
                obs.update(phase='TRAINING', capability_id='A.MAPS',
                           candidate_step=64, candidate_horizon=64)
                oversized_integer = int('9' * 256)
                template = {
                    'candidate_step_wall_seconds': 12345.6789012345,
                    'pre_neural_source_compile_wall_seconds': 12345.6789012345,
                    'currentness_binding_wall_seconds': 12345.6789012345,
                    'b11_preflight_wall_seconds': 12345.6789012345,
                    'b11_autodiff_wall_seconds': 12345.6789012345,
                    'optimizer_admission_wall_seconds': 12345.6789012345,
                    'motif_staging_wall_seconds': 12345.6789012345,
                    'evidence_capture_wall_seconds': 12345.6789012345,
                    'candidate_terminal_step': False,
                    'c08_gradient_launches': oversized_integer,
                    'c08_vectorized_microbatches': oversized_integer,
                    'c08_materialization_barriers': oversized_integer,
                    'c08_scalar_fallback_rows': oversized_integer,
                    'c08_logical_batch_wall_seconds': 12345.6789012345,
                    'c08_rows_per_gradient_launch': 12345.6789012345,
                    'b11_provider_draw_count': oversized_integer,
                    'b11_atlas_reload_count': oversized_integer,
                    'logical_rows': oversized_integer,
                    'compiled_positions': oversized_integer,
                }
                obs.record['candidate_steps'] = [
                    {'candidate_step': step, 'candidate_optimizer_step': step, **template}
                    for step in range(1, 65)
                ]
                obs.update()
                self.assertTrue(obs.enabled)
                snapshot = json.loads((root / 'trainer-observed.json').read_text())
                current = snapshot['visits'][-1]
                self.assertLessEqual(
                    len((root / 'trainer-observed.json').read_bytes()), 64 * 1024)
                self.assertLess(len(current['candidate_steps']), 64)
                self.assertEqual(current['candidate_steps'][-1]['candidate_step'], 64)

    def test_write_failure_does_not_escape(self):
        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / 'trainer-observed.json').mkdir()
            with TrainerObservation(root, 1) as obs:
                obs.update(phase='SELECTING')
                self.assertTrue(obs.enabled)
                obs.finish('HELD')

    def test_heartbeat_interleaved_with_phase_changes_keeps_complete_snapshots(self):
        import threading
        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            reads = []
            done = threading.Event()
            def read_snapshots():
                while not done.is_set():
                    try:
                        reads.append(json.loads((root / 'trainer-observed.json').read_bytes()))
                    except FileNotFoundError:
                        pass
            with TrainerObservation(root, 1, heartbeat_seconds=0.001) as obs:
                reader = threading.Thread(target=read_snapshots)
                reader.start()
                for i in range(12):
                    obs.update(phase='TRAINING', candidate_step=i, candidate_horizon=12)
                    time.sleep(0.001)
                obs.update(phase='RETENTION', retention_completed=2, retention_total=3)
                time.sleep(0.005)
                obs.finish('REJECTED')
                done.set()
                reader.join()
            final = json.loads((root / 'trainer-observed.json').read_bytes())['visits'][-1]
            self.assertTrue(reads)
            self.assertTrue(all(len(item['visits']) == 1 for item in reads))
            self.assertEqual((final['phase'], final['retention_completed'], final['candidate_step']),
                             ('COMPLETED', 2, 11))
            retention = [item['visits'][-1] for item in reads if item['visits'][-1]['phase'] == 'RETENTION']
            self.assertTrue(retention)
            self.assertTrue(all(item['candidate_step'] == 11 and item['retention_completed'] == 2 for item in retention))


def test_b11_authority_error_report_and_topology_negative_control():
    import pytest
    for call, reason in (
        (lambda: B11SourceExecutionAuthority(), 'B11_SOURCE_EXECUTION_AUTHORITY_CALLER_CONSTRUCTION_FORBIDDEN'),
        (lambda: require_b11_source_execution_authority_current(None, None, None, None),
         'B11_SOURCE_EXECUTION_AUTHORITY_DRIFT'),
    ):
        with pytest.raises(ValueError) as failure:
            call()
        report = ErrorBus.report(failure.value)
        assert report.code == 'SCHOOL.BAMF_B11.SOURCE_EXECUTION_AUTHORITY_INVALID'
        assert report.context['reason'] == reason
        assert report.preserve_state
        assert report.disposition == 'PRESERVE_AND_INSPECT'
    with pytest.raises(ValueError) as failure:
        ModelTopologySpecV2(layers=0)
    report = ErrorBus.report(failure.value)
    assert report.code == 'SCHOOL.MODEL_TOPOLOGY.INVALID'
    assert report.context['field'] == 'layers'
