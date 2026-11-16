"""C07 display keeps exact status and its raw authority fields."""
from contextlib import nullcontext, redirect_stdout
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
