"""Public operator contracts preserve the human-run boundary."""
from contextlib import redirect_stdout, redirect_stderr
import io
import json
from pathlib import Path
import signal
import tempfile
import unittest
from unittest.mock import patch
from bilqis_mlx import cli
from bilqis_mlx.cli import main, parse_args


class PublicTests(unittest.TestCase):
    def test_human_sigint_guard_raises_once_then_ignores_duplicate_cleanup_signal(self):
        previous = signal.getsignal(signal.SIGINT)
        with cli._human_sigint_guard():
            handler = signal.getsignal(signal.SIGINT)
            with self.assertRaises(KeyboardInterrupt):
                handler(signal.SIGINT, None)
            handler(signal.SIGINT, None)
        self.assertEqual(signal.getsignal(signal.SIGINT), previous)

    def test_human_training_interrupt_reports_resume_point_once_without_traceback(self):
        from bilqis_mlx import trainer
        with tempfile.TemporaryDirectory() as tmp, patch('bilqis_mlx.runtime.operating_loop.operate', side_effect=KeyboardInterrupt), \
                redirect_stderr(io.StringIO()) as errors:
            code = main([
                "train", "--human-run", "--resume", "--run-dir", tmp,
            ])
        self.assertEqual(code, 130)
        output = errors.getvalue()
        self.assertEqual(output.count("HUMAN TRAINING INTERRUPTED"), 1)
        self.assertIn("last completed visit/checkpoint remains the resume point", output)
        self.assertNotIn("Traceback", output)

    def test_retention_defaults_on_and_explicit_independent_opt_out(self):
        self.assertFalse(parse_args(["train", "--resume"]).no_retention)
        self.assertTrue(parse_args(["train", "--resume"]).full_grade_b)
        self.assertFalse(parse_args([
            "train", "--resume", "--reduced-grade-b"]
        ).full_grade_b)
        self.assertTrue(parse_args([
            "train", "--resume", "--boolean-association-bridge"]
        ).boolean_association_bridge)
        grace = parse_args([
            "train", "--resume", "--stagnation-grace-grade", "B",
            "--stagnation-grace-steps", "100000"])
        self.assertEqual(grace.stagnation_grace_grade, "B")
        self.assertEqual(grace.stagnation_grace_steps, 100000)
        debt = parse_args([
            "train", "--resume", "--admit-next-grade-with-debt"])
        self.assertTrue(debt.admit_next_grade_with_debt)
        with tempfile.TemporaryDirectory() as tmp, patch(
                "bilqis_mlx.presentation.operator_cli.command.ROOT", Path(tmp)):
            run = str(Path(tmp) / "runs" / "aspirant")
            out=io.StringIO()
            with redirect_stdout(out), redirect_stderr(io.StringIO()):
                self.assertEqual(main(["train", "--dry-run", "--run-dir", run]), 0)
            self.assertEqual(json.loads(out.getvalue())["retention_mode"], "DEFAULT_PROTECTED")
            out=io.StringIO()
            with redirect_stdout(out), redirect_stderr(io.StringIO()):
                self.assertEqual(main(["train", "--dry-run", "--no-retention",
                                       "--run-dir", run]), 0)
            self.assertEqual(json.loads(out.getvalue())["retention_mode"], "EXPLICIT_UNPROTECTED")
            out=io.StringIO()
            with redirect_stdout(out), redirect_stderr(io.StringIO()):
                self.assertEqual(main(["train", "--dry-run", "--experimental-retention",
                                       "--run-dir", run]), 0)
            self.assertEqual(json.loads(out.getvalue())["retention_mode"], "DEFAULT_PROTECTED")
            with redirect_stderr(io.StringIO()), self.assertRaises(SystemExit):
                parse_args(["train", "--experimental-retention", "--no-retention"])

    def test_explicit_resume_only_and_training_is_hard_blocked(self):
        with tempfile.TemporaryDirectory() as tmp, patch(
                "bilqis_mlx.presentation.operator_cli.command.ROOT", Path(tmp)):
            run = Path(tmp) / "runs" / "aspirant"
            output=io.StringIO()
            with redirect_stdout(output):
                code=main(["train","--dry-run","--run-dir",str(run)])
            self.assertEqual(code,0)
            report = json.loads(output.getvalue())
            self.assertEqual(report["start_behavior"], "GRADE_A_NEW_RUN")
            self.assertEqual(report["result"], "PREFLIGHT_ONLY_NO_NEURAL_UPDATES")
            self.assertFalse(report["human_live_grade_a_trainer_end_to_end_qualified"])
            self.assertEqual(report["disposable_full_student_optimizer_continuation"]["scope"],
                             "ONE_DETACHED_STEP_AND_COMPLETE_39_TENSOR_ADAMW_RESTART")
            self.assertEqual(report["blockers"], [])
            self.assertTrue(report["source_grounded_grade_a_admitted"])
            self.assertEqual(report["grade_a_release"],
                             "bilqis.mlx.grade-a-live/20261015")
            self.assertEqual(report["historical_source_release"],
                             "bilqis.mlx.grade-a-user-accepted/20261015")
            self.assertEqual(len(report["experimental_risks"]), 2)
            self.assertEqual(report["operator_constraint"], "HUMAN_ONLY_NEURAL_OPTIMIZER_UPDATES")
            self.assertNotIn("HUMAN_ONLY_NEURAL_OPTIMIZER_UPDATES", report["blockers"])
            with redirect_stderr(io.StringIO()):
                self.assertEqual(main(["train","--dry-run","--resume","--run-dir",str(run)]),2)
                self.assertEqual(main(["train","--run-dir",str(run)]),2)
            self.assertEqual(list(Path(tmp).iterdir()),[])
