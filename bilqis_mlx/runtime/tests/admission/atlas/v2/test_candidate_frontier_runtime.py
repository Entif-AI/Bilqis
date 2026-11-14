from pathlib import Path
from tempfile import TemporaryDirectory
import unittest

from bilqis_mlx.runtime.atlas_flywheel_runtime import _candidate_frontier


class CandidateFrontierRuntimeTests(unittest.TestCase):
    def test_production_candidate_frontier_rebuilds_into_run_custody(self):
        with TemporaryDirectory() as temporary:
            run_dir = Path(temporary)
            frontier = _candidate_frontier(run_dir)

            self.assertEqual(len(frontier.candidates), 240)
            self.assertGreater(len(frontier.senses), 0)
            self.assertTrue(
                (run_dir / "candidate-frontier" / "frontier_manifest.json").is_file())


if __name__ == "__main__":
    unittest.main()
