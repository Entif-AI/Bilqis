"""Human root commands must not accidentally begin optimization."""
from contextlib import redirect_stderr
import io
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
from bilqis_mlx.cli import main
from bilqis_mlx.errors import ErrorBus, SCHOOL
from bilqis_mlx.presentation.dashboard import build
from bilqis_mlx.presentation.operator_cli.terminal import (
    _report_operator_blocked, human_stop_summary,
)


class OperatorTests(unittest.TestCase):
    def test_blocked_report_surfaces_structured_reason(self):
        try:
            ErrorBus.Raise(
                SCHOOL.MODEL_TOPOLOGY.INVALID,
                reason="BAMF_PRIORITY_REJECTION_ORDER_INVALID")
        except ValueError as error:
            stderr = io.StringIO()
            with redirect_stderr(stderr):
                self.assertEqual(_report_operator_blocked(error, None), 2)
        self.assertIn(
            "DETAILS: reason=BAMF_PRIORITY_REJECTION_ORDER_INVALID",
            stderr.getvalue())

    def test_cold_resume_stop_explains_accepted_generation_restart(self):
        summary = human_stop_summary({
            "stop_reason": "ATLAS_ADMISSION_ADOPTED_COLD_RESUME",
            "visits_this_command": 0,
            "elapsed_seconds": 1.25,
            "optimizer_step": 17,
            "safe_resume_command": "npm run train -- --human-run --resume",
        })
        self.assertIn("accepted B13", summary)
        self.assertIn("--resume", summary)

    def test_resume_terminal_clears_previous_session_stop_before_training(self):
        class Terminal(io.StringIO):
            def isatty(self):
                return True

        with tempfile.TemporaryDirectory() as tmp:
            run = Path(tmp)
            event = {"event": "SCHOOL_SESSION_STOPPED", "grade": "B",
                     "stop_reason": "TIME_LIMIT_REACHED", "generation": 6809,
                     "optimizer_step": 203880, "visits_this_command": 1599,
                     "elapsed_seconds": 5409.7}
            original = json.dumps(event) + "\n"
            (run / "events.jsonl").write_text(original)
            old_view = build(run, stream=io.StringIO())
            self.assertEqual(old_view.state["stop"], "TIME_LIMIT_REACHED")

            terminal = Terminal()
            with patch("bilqis_mlx.presentation.operator_cli.terminal.sys.stdout", terminal), patch(
                    'bilqis_mlx.runtime.operating_loop.operate',
                    side_effect=ValueError("DISPOSABLE_TEST_NO_NEURAL_TRAINING")), \
                    redirect_stderr(io.StringIO()):
                result = main(["train", "--human-run", "--resume",
                               "--minutes", "90", "--run-dir", tmp])
            self.assertEqual(result, 2)  # Stub prevents any training call.
            self.assertIn("RUNTIME", terminal.getvalue())
            self.assertIn("MAX TIME", terminal.getvalue())
            self.assertNotIn("TIME_LIMIT_REACHED", terminal.getvalue())
            self.assertEqual((run / "events.jsonl").read_text(), original)
            # Historical dashboard continues to report the actual old stop.
            self.assertEqual(build(run, stream=io.StringIO()).state["stop"],
                             "TIME_LIMIT_REACHED")
