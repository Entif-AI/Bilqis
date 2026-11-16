"""Human root commands must not accidentally begin optimization."""
from contextlib import redirect_stdout,redirect_stderr
import io
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
from bilqis_mlx.cli import main, parse_args


class OperatorTests(unittest.TestCase):
    def test_resume_instructions_are_flag_free_at_default_retention_policy(self):
        from bilqis_mlx.trainer import _resume_command
        from bilqis_mlx.learning.learning_experiment import Settings
        from bilqis_mlx.paths import LEGACY_SOURCE, active_run_dir

        self.assertEqual(_resume_command(active_run_dir(), LEGACY_SOURCE, Settings()),
                         "npm run train -- --human-run --resume")
        stricter = _resume_command(active_run_dir(), LEGACY_SOURCE,
                                   Settings(mature_max_loss=0))
        self.assertIn("--retention-mature-max-loss 0", stricter)
        self.assertNotIn("--experimental-retention", stricter)
        with tempfile.TemporaryDirectory() as tmp:
            unprotected = _resume_command(Path(tmp), LEGACY_SOURCE, None)
            self.assertIn("--no-retention", unprotected)
            self.assertIn("--run-dir", unprotected)

        bridged = _resume_command(
            active_run_dir(), LEGACY_SOURCE, Settings(),
            boolean_association_bridge=True)
        self.assertIn("--boolean-association-bridge", bridged)
        autonomous = _resume_command(
            active_run_dir(), LEGACY_SOURCE, Settings(),
            autonomous_curriculum=True)
        self.assertIn("--autonomous-curriculum", autonomous)
        serial = _resume_command(
            active_run_dir(), LEGACY_SOURCE, Settings(), source_prefetch_workers=0)
        self.assertIn("--source-prefetch-workers 0", serial)
        one_worker = _resume_command(
            active_run_dir(), LEGACY_SOURCE, Settings(), source_prefetch_workers=1)
        self.assertIn("--source-prefetch-workers 1", one_worker)

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
