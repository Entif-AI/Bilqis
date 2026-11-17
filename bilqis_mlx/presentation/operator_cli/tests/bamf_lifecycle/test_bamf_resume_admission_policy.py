"""#751 resume consumes the C07 policy owner without minting authority."""
from contextlib import redirect_stderr, redirect_stdout
import io
import json
from unittest.mock import patch

from bilqis_mlx.cli import main
from bilqis_mlx.runtime.tests.bamf_first_student._bamf_first_student_support import BamfFirstStudentCase
from bilqis_mlx.runtime.tests.custody.bamf_bundle.genesis_authority_fixtures import (
    accepted_feature_source_patch,
)
from bilqis_mlx.runtime.tests.custody.bamf_bundle.helpers import shape_patch


class BamfResumeAdmissionPolicyTests(BamfFirstStudentCase):
    def test_resume_uses_authenticated_saved_policy_result(self):
        target = self.root / "accepted-bamf"
        self.preflight(target)

        output, errors = io.StringIO(), io.StringIO()
        with shape_patch(), accepted_feature_source_patch(), patch(
                "bilqis_mlx.presentation.operator_cli.bamf_lifecycle._saved_policy",
                return_value="atlas-release"), redirect_stdout(output), redirect_stderr(errors):
            # C07 persistence/readback is independently proven in its owner suite;
            # this test owns propagation of that authenticated owner result.
            code = main([
                "train", "--dry-run", "--resume", "--run-dir", str(target)])

        self.assertEqual((code, errors.getvalue()), (0, ""))
        self.assertEqual(json.loads(output.getvalue())["admission_policy"], "atlas-release")
