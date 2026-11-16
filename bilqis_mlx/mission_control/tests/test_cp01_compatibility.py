"""CP02 consumes the accepted CP01 identity boundary without owning its transport."""
import unittest

from bilqis_mlx.control_plane.contracts import ControlPlaneState, LearnerIdentity
from bilqis_mlx.mission_control.model import RunRef
from bilqis_mlx.mission_control.tests.samples import D1, D2, D3, D4


class MissionControlCp01CompatibilityTests(unittest.TestCase):
    def test_healthy_cp01_identity_preserves_shared_cp02_run_fields_literally(self):
        cp01 = LearnerIdentity(
            state=ControlPlaneState.HEALTHY,
            run_dir="/fixture/run",
            operator_active=False,
            run_id="run-7",
            run_identity_sha256=D4,
            generation=7,
            generation_manifest_sha256=D1,
            optimizer_step=42,
            factory_release_sha256=D2,
            topology_sha256=D4,
        )
        run = RunRef(
            run_id=cp01.run_id,
            run_identity_sha256=cp01.run_identity_sha256,
            generation=cp01.generation,
            generation_manifest_sha256=cp01.generation_manifest_sha256,
            candidate_identity_sha256=D2,
            factory_release_sha256=cp01.factory_release_sha256,
            semantic_release_sha256=D3,
            topology_sha256=cp01.topology_sha256,
        )
        self.assertEqual(
            (
                run.run_id,
                run.run_identity_sha256,
                run.generation,
                run.generation_manifest_sha256,
                run.factory_release_sha256,
                run.topology_sha256,
            ),
            (
                cp01.run_id,
                cp01.run_identity_sha256,
                cp01.generation,
                cp01.generation_manifest_sha256,
                cp01.factory_release_sha256,
                cp01.topology_sha256,
            ),
        )

    def test_cp01_identity_does_not_invent_cp02_candidate_or_semantic_release(self):
        cp01_fields = set(LearnerIdentity.__dataclass_fields__)
        self.assertNotIn("candidate_identity_sha256", cp01_fields)
        self.assertNotIn("semantic_release_sha256", cp01_fields)
        self.assertIn("candidate_identity_sha256", RunRef.__dataclass_fields__)
        self.assertIn("semantic_release_sha256", RunRef.__dataclass_fields__)


if __name__ == "__main__":
    unittest.main()
