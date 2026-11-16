"""Admission-facing witnesses for accepted-generation runtime custody."""
from pathlib import Path
import os
from tempfile import TemporaryDirectory
import unittest
from unittest.mock import patch

import bilqis_mlx.runtime.mlx_checkpoint as mlx_checkpoint
from bilqis_mlx.errors import BilqisError
from bilqis_mlx.runtime.bamf_bundle import admission
from bilqis_mlx.runtime.bamf_bundle.admission import admit_candidate_step
from bilqis_mlx.runtime.tests.custody.bamf_bundle.helpers import (
    candidate, parent_state, publish_candidate, shape_patch,
)


class AcceptedRuntimeAdmissionTests(unittest.TestCase):
    def setUp(self):
        self.temporary = TemporaryDirectory()
        self.root = Path(self.temporary.name)
        self.run = self.root / "run"
        self.environment = patch.dict(
            os.environ, {"BILQIS_DATA_PLANE": str(self.root / "plane.sqlite3")})
        self.environment.start()

    def tearDown(self):
        self.environment.stop()
        self.temporary.cleanup()

    def publish(self, source):
        with shape_patch(), patch.object(mlx_checkpoint, "assert_headroom"):
            return publish_candidate(self.run, source)

    def test_production_step_reaches_the_owner_binder(self):
        self.publish(candidate(parent_state()))
        with shape_patch(), patch.object(
                admission, "production_candidate_step",
                side_effect=admission.production_candidate_step) as step:
            with self.assertRaises(BilqisError):
                admit_candidate_step(
                    self.run, {}, loss_bearing_target=True,
                    teacher_hparams=None, max_norm=1.)
        self.assertTrue(step.called)

    def test_no_loss_step_cannot_promote_census_to_execution(self):
        self.publish(candidate(parent_state()))
        marker = object()
        with shape_patch(), patch.object(
                admission, "production_candidate_step", return_value=marker) as step:
            result = admit_candidate_step(
                self.run, {}, loss_bearing_target=False,
                teacher_hparams=None, max_norm=1.)
        self.assertIs(result, marker)
        for forbidden in ("motif_reads", "executed_parameter_names",
                          "visible_identity_rows", "feedback_identity_rows",
                          "local_slot_rows"):
            self.assertNotIn(forbidden, step.call_args.kwargs)

    def test_admission_forwards_b11_gradient_execution_without_rederiving_it(self):
        self.publish(candidate(parent_state()))
        owner_execution = object()
        marker = object()
        with shape_patch(), patch.object(
                admission, "production_candidate_step", return_value=marker) as step:
            result = admit_candidate_step(
                self.run, loss_bearing_target=True,
                gradient_execution=owner_execution, teacher_hparams=None,
                max_norm=1.)
        self.assertIs(result, marker)
        self.assertIs(step.call_args.kwargs["gradient_execution"], owner_execution)
        self.assertIsNone(step.call_args.args[1])


if __name__ == "__main__":
    unittest.main()
