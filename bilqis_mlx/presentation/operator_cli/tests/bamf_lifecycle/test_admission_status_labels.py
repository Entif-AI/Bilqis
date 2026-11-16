"""C07 display keeps exact status and its raw authority fields."""
from contextlib import ExitStack, nullcontext, redirect_stdout
import io
import json
from pathlib import Path
from types import SimpleNamespace
import unittest
from unittest.mock import patch

from bilqis_mlx.presentation.operator_cli.command import _dispatch_bamf_resume
from bilqis_mlx.presentation.operator_cli.inspection import _print_status
from bilqis_mlx.runtime.bamf_operator import BamfOperatorResult


class AdmissionStatusLabelsTests(unittest.TestCase):
    def test_continued_operator_output_keeps_c07_details(self):
        args = SimpleNamespace(human_run=True, dry_run=False, minutes=1, max_visits=1,
                               steps_per_visit=1, reserve_gib=100, source_prefetch_workers=0)
        report = {"result": "WAITING_FOR_EVIDENCE", "admission_policy": "atlas-release",
                  "admission_reason": "EXACT_REASON", "admission_advances": 2}
        output = io.StringIO()
        with patch("bilqis_mlx.control_plane.active_endpoint.advertise_active_endpoint",
                   return_value=nullcontext()), patch("bilqis_mlx.runtime.bamf_operator.operate_bamf",
                   return_value=BamfOperatorResult("VISIT_LIMIT", 1, 1, 0, 1, 1)), redirect_stdout(output):
            _dispatch_bamf_resume(args, Path("/run"), report)
        shown = json.loads(output.getvalue())
        self.assertEqual(shown["admission_reason"], "EXACT_REASON")
        self.assertEqual(shown["admission_advances"], 2)
        self.assertEqual(shown["admission_label"], "C07 waiting for learner evidence")

    def test_lifecycle_preserves_flywheel_details_before_dispatch(self):
        from bilqis_mlx.presentation.operator_cli import bamf_lifecycle as lifecycle
        from bilqis_mlx.runtime.atlas_flywheel import AdmissionFlywheelStatus

        args = SimpleNamespace(run_dir="/unused", atlas_admission_scope=None,
                               admission_policy_explicit=False, human_run=True,
                               dry_run=False, source_run_dir="/source", reserve_gib=100,
                               source_prefetch_workers=0)
        student = SimpleNamespace(run_identity=object(), topology=object(),
                                  optimizer_hyperparameters=object())
        with ExitStack() as stack:
            stack.enter_context(patch(
                "bilqis_mlx.runtime.bamf_bundle.load_bamf_generation_authority",
                return_value=(student, "manifest")))
            for name, value in (("_accepted_atlas", object()),
                                ("_validate_resume_overrides", student.run_identity),
                                ("_validate_resume_atlas_override", None),
                                ("_saved_policy", "atlas-release"),
                                ("_validated_resume_parent_graph", (None, None, {}))):
                stack.enter_context(patch.object(lifecycle, name, return_value=value))
            stack.enter_context(patch.object(lifecycle, "_report", side_effect=lambda **kw: kw))
            flywheel = stack.enter_context(patch(
                "bilqis_mlx.runtime.atlas_flywheel_runtime.run_accepted_atlas_flywheel"))
            for status in AdmissionFlywheelStatus:
                with self.subTest(status=status):
                    flywheel.return_value = SimpleNamespace(
                        status=status, reason="EXACT_REASON", advances=2)
                    result = lifecycle._resume(args, None)
                    self.assertEqual(result["result"], status.value)
                    self.assertEqual(result["admission_reason"], "EXACT_REASON")
                    self.assertEqual(result["admission_advances"], 2)

    def test_known_terminal_statuses_are_labeled_without_mutating_input(self):
        labels = set()
        for status in ("LEASE_REQUIRED", "WAITING_FOR_EVIDENCE", "HELD",
                       "IMPLEMENTATION_UNCOVERED", "FIXED_POINT"):
            with self.subTest(status=status):
                original = {"result": status, "admission_policy": "atlas-release",
                            "admission_reason": "EXACT_REASON", "admission_advances": 2}
                output = io.StringIO()
                with redirect_stdout(output):
                    _print_status(original)
                shown = json.loads(output.getvalue())
                self.assertEqual(shown["result"], status)
                self.assertEqual(shown["admission_reason"], "EXACT_REASON")
                self.assertEqual(shown["admission_advances"], 2)
                self.assertNotIn("admission_label", original)
                labels.add(shown["admission_label"])
        self.assertEqual(len(labels), 5)

    def test_unknown_and_other_policies_remain_unchanged(self):
        for original in ({"result": "FUTURE_REASON", "admission_policy": "atlas-release"},
                         {"result": "HELD", "admission_policy": "staged"}):
            output = io.StringIO()
            with redirect_stdout(output):
                _print_status(original)
            self.assertEqual(json.loads(output.getvalue()), original)
