"""Human root commands must not accidentally begin optimization."""
from contextlib import redirect_stderr
import io
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
from bilqis_mlx.cli import main


class OperatorTests(unittest.TestCase):
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

    def test_direct_operator_refuses_protected_opt_out_before_source_or_gpu(self):
        from bilqis_mlx import trainer as trainer

        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp)
            state=root/"state.json"
            payload=json.dumps({"learning_experiment":{"version":"protected"}}).encode()
            state.write_bytes(payload)
            with patch('bilqis_mlx.runtime.session.prepare_source', side_effect=AssertionError(
                    "NO_SOURCE_OR_GPU_BEFORE_POLICY_REFUSAL")):
                with self.assertRaisesRegex(
                        ValueError, "LEARNING_EXPERIMENT_PROTECTED_RESUME_REQUIRES_RETENTION"):
                    trainer.operate(root, root, root, root, resume=True,
                                    retention_enabled=False)
            self.assertEqual(state.read_bytes(),payload)

    def test_human_operator_receives_default_protected_mode_without_opt_in(self):
        from bilqis_mlx import trainer as trainer
        no_neural_work = "TEST_BLOCKS_ANY_NEURAL_WORK"
        with tempfile.TemporaryDirectory() as tmp:
            with patch('bilqis_mlx.runtime.operating_loop.operate', side_effect=ValueError(
                    no_neural_work)) as operate, \
                    redirect_stderr(io.StringIO()):
                self.assertEqual(main(["train", "--human-run", "--resume",
                                       "--run-dir", tmp]), 2)
            self.assertTrue(operate.call_args.kwargs["retention_enabled"])
            self.assertEqual(operate.call_args.kwargs["source_prefetch_workers"], 2)
            with patch('bilqis_mlx.runtime.operating_loop.operate', side_effect=ValueError(
                    no_neural_work)) as operate, \
                    redirect_stderr(io.StringIO()):
                self.assertEqual(main(["train", "--human-run", "--resume",
                                       "--source-prefetch-workers", "0",
                                       "--run-dir", tmp]), 2)
            self.assertEqual(operate.call_args.kwargs["source_prefetch_workers"], 0)
            with patch('bilqis_mlx.runtime.operating_loop.operate', side_effect=ValueError(
                    no_neural_work)) as operate, \
                    patch('bilqis_mlx.presentation.operator_cli.command.ROOT', Path(tmp)), \
                    redirect_stderr(io.StringIO()):
                self.assertEqual(main(["train", "--human-run", "--no-retention",
                                       "--run-dir", str(Path(tmp) / "runs" / "independent")]), 2)
            self.assertFalse(operate.call_args.kwargs["retention_enabled"])

    def test_explicit_source_verification_is_the_only_fresh_external_inspection_escape(self):
        from bilqis_mlx.presentation.operator_cli.command import (
            _reject_fresh_external_legacy_fallthrough,
        )
        from bilqis_mlx.presentation.operator_cli.parser import parse_args

        with tempfile.TemporaryDirectory() as tmp:
            target = Path(tmp) / "external"
            verify = parse_args([
                "train", "--dry-run", "--verify-source", "--run-dir", str(target),
            ])
            _reject_fresh_external_legacy_fallthrough(verify, target)
            ordinary = parse_args(["train", "--dry-run", "--run-dir", str(target)])
            with self.assertRaises(ValueError):
                _reject_fresh_external_legacy_fallthrough(ordinary, target)

    def test_issue_launcher_passes_registered_budget_owner(self):
        from bilqis_mlx import trainer
        from bilqis_mlx.runtime.experiment_runs import ExperimentRunBudget

        with tempfile.TemporaryDirectory() as directory:
            owner = ExperimentRunBudget(Path(directory).resolve() / "issue349")
            run = owner.create("primary")
            with patch('bilqis_mlx.runtime.operating_loop.operate', side_effect=ValueError(
                    "TEST_BLOCKS_ANY_NEURAL_WORK")) as operate, \
                    redirect_stderr(io.StringIO()):
                self.assertEqual(main([
                    "train", "--human-run", "--resume", "--run-dir", str(run),
                    "--issue-349-experiment-root", str(owner.root)]), 2)
            passed = operate.call_args.kwargs["experiment_budget"]
            self.assertIsInstance(passed, ExperimentRunBudget)
            self.assertEqual(passed.register(run)["run_name"], "primary")
            self.assertTrue(operate.call_args.kwargs["retention_enabled"])

    def test_human_operator_forwards_explicit_debt_grade_admission(self):
        from bilqis_mlx import trainer as trainer
        no_neural_work = "TEST_BLOCKS_ANY_NEURAL_WORK"
        with tempfile.TemporaryDirectory() as tmp:
            with patch('bilqis_mlx.runtime.operating_loop.operate', side_effect=ValueError(
                    no_neural_work)) as operate, redirect_stderr(io.StringIO()):
                self.assertEqual(main([
                    "train", "--human-run", "--resume",
                    "--admit-next-grade-with-debt", "--run-dir", tmp,
                ]), 2)
            self.assertTrue(
                operate.call_args.kwargs["admit_next_grade_with_debt"])

    def test_human_operator_explicitly_passes_autonomous_curriculum_mode(self):
        from bilqis_mlx import trainer as trainer
        with tempfile.TemporaryDirectory() as tmp, patch('bilqis_mlx.runtime.operating_loop.operate', side_effect=ValueError(
                    "AUTONOMY_TEST_NO_NEURAL_TRAINING")) as operate, \
                redirect_stderr(io.StringIO()):
            self.assertEqual(main([
                "train", "--human-run", "--resume",
                "--autonomous-curriculum", "--run-dir", tmp]), 2)
        self.assertTrue(operate.call_args.kwargs["autonomous_curriculum"])
        self.assertTrue(operate.call_args.kwargs["retention_enabled"])

    def test_autonomous_curriculum_flag_cannot_start_optimizer_without_human_run(self):
        from bilqis_mlx import trainer as trainer
        with tempfile.TemporaryDirectory() as tmp, patch('bilqis_mlx.runtime.operating_loop.operate',
                side_effect=AssertionError("AUTONOMY_MUST_NOT_REACH_OPERATE")) as operate, \
                redirect_stderr(io.StringIO()) as errors:
            self.assertEqual(main([
                "train", "--autonomous-curriculum", "--resume",
                "--run-dir", tmp]), 2)
        operate.assert_not_called()
        self.assertIn(
            "TRAINING REQUIRES EXPLICIT HUMAN OPERATOR",
            errors.getvalue(),
        )

    def test_autonomous_curriculum_cannot_disable_retention_before_source_or_gpu(self):
        from bilqis_mlx import trainer as trainer
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            with patch('bilqis_mlx.runtime.session.prepare_source',
                    side_effect=AssertionError("NO_SOURCE_OR_GPU_BEFORE_AUTONOMY_GUARD")):
                with self.assertRaisesRegex(
                        ValueError, "AUTONOMOUS_CURRICULUM_REQUIRES_RETENTION"):
                    trainer.operate(
                        root, root, root, root,
                        autonomous_curriculum=True,
                        retention_enabled=False)

    def test_human_operator_passes_flash_mode_without_changing_retention(self):
        from bilqis_mlx import trainer as trainer
        with tempfile.TemporaryDirectory() as tmp, patch('bilqis_mlx.runtime.operating_loop.operate', side_effect=ValueError(
                    "FLASH_TEST_NO_NEURAL_TRAINING")) as operate, \
                redirect_stderr(io.StringIO()):
            self.assertEqual(main([
                "train", "--human-run", "--resume", "--flash-mode",
                "--run-dir", tmp]), 2)
        self.assertTrue(operate.call_args.kwargs["flash_mode"])
        self.assertTrue(operate.call_args.kwargs["retention_enabled"])
