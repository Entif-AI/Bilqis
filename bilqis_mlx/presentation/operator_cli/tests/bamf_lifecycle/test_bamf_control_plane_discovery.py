"""Mission Control discovery is live for the full human BAMF operator visit."""
from contextlib import contextmanager, redirect_stderr, redirect_stdout
import io
import json
import os
from unittest.mock import patch

from bilqis_mlx.cli import main
from bilqis_mlx.runtime.tests.bamf_first_student._bamf_first_student_support import (
    BamfFirstStudentCase,
)
from bilqis_mlx.runtime.tests.custody.bamf_bundle.genesis_authority_fixtures import (
    source_features,
)
from bilqis_mlx.runtime.tests.custody.bamf_bundle.helpers import shape_patch


class BamfControlPlaneDiscoveryTests(BamfFirstStudentCase):
    def invoke(self, argv):
        output, errors = io.StringIO(), io.StringIO()
        with redirect_stdout(output), redirect_stderr(errors):
            code = main(["train", *argv])
        return code, output.getvalue(), errors.getvalue()

    @contextmanager
    def accepted_read_context(self):
        with shape_patch(), patch(
            "bilqis_mlx.runtime.bamf_bundle.feature_authority._authenticate_features",
            return_value=source_features(),
        ):
            yield

    def test_human_resume_advertises_control_plane_target_during_operator_visit(self):
        target = self.root / "accepted-bamf"
        self.preflight(target)
        socket_path = target.parent / f".{target.name}.control-plane.sock"
        from bilqis_mlx.runtime.bamf_operator import BamfOperatorResult

        def observe_control_plane_target(run_dir, **_kwargs):
            from bilqis_mlx.control_plane.active_endpoint import discover_active_endpoint
            endpoint = discover_active_endpoint(run_dir=target)
            self.assertIsNotNone(endpoint)
            self.assertEqual(endpoint.run_dir, target.resolve())
            self.assertEqual(endpoint.socket_path, socket_path.resolve())
            return BamfOperatorResult("VISIT_LIMIT", 1, 1, 0, 1, 1)

        registry = self.root / "control-plane-discovery"
        with patch.dict(os.environ, {"BILQIS_ACTIVE_CONTROL_PLANE_DIR": str(registry)}), \
                self.accepted_read_context(), patch(
                "bilqis_mlx.presentation.operator_cli.command._invoke_learner",
                side_effect=AssertionError("legacy learner must remain untouched")), patch(
                "bilqis_mlx.runtime.bamf_operator.operate_bamf",
                side_effect=observe_control_plane_target):
            code, output, errors = self.invoke([
                "--human-run", "--resume", "--run-dir", str(target),
                "--max-visits", "1",
            ])

        self.assertEqual((code, errors), (0, ""))
        self.assertEqual(json.loads(output)["status"], "VISIT_LIMIT")
        self.assertEqual(tuple(registry.glob("*.json")), ())
