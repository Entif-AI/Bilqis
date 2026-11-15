import json
from pathlib import Path
from tempfile import TemporaryDirectory
import time
import unittest

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
            self.assertEqual(len(data['visits']), 8)
            self.assertEqual(data['visits'][-1]['outcome'], 'HELD')
            self.assertGreater(data['visits'][-1]['revision'], 3)
            self.assertEqual(data['visits'][-1]['candidate_step'], 1)
            self.assertEqual(data['visits'][-1]['run_id'], 'run')
            with self.assertRaises(KeyboardInterrupt):
                with TrainerObservation(root, 10):
                    raise KeyboardInterrupt()
            self.assertEqual(json.loads((root / 'trainer-observed.json').read_text())['visits'][-1]['outcome'], 'INTERRUPTED')

    def test_write_failure_does_not_escape(self):
        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / 'trainer-observed.json').mkdir()
            with TrainerObservation(root, 1) as obs:
                obs.update(phase='SELECTING')
                obs.finish('HELD')
