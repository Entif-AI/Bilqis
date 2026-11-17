"""Focused custody proof for issue 349 disposable experiment directories."""
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest

from bilqis_mlx.runtime.experiment_runs import ExperimentRunBudget, require_training_run


class ExperimentRunBudgetTests(unittest.TestCase):
    def test_registered_issue_run_can_use_a_separate_executable_checkout(self):
        owner = self.budget()
        run = owner.create("primary")
        require_training_run(run, self.base / "code-checkout/runs", issue_budget=owner)
        require_training_run(run, self.base / "code-checkout/runs")

    def test_normal_operator_run_is_not_location_scoped_without_issue_budget(self):
        external = self.base / "durable-runs" / "aspirant"
        external.mkdir(parents=True)
        require_training_run(external, self.base / "code-checkout/runs")

    def test_external_historical_run_and_anonymous_guards_cannot_claim_issue_custody(self):
        owner = self.budget()
        owner.create("primary")
        historical = self.base / "historical"
        historical.mkdir()
        with self.assertRaisesRegex(RuntimeError, "UNREGISTERED_PATH"):
            require_training_run(historical, self.base / "code/runs", issue_budget=owner)
        with self.assertRaisesRegex(TypeError, "EXPERIMENT_BUDGET_GUARD_INVALID"):
            require_training_run(historical, self.base / "code/runs", issue_budget=lambda _: None)

    def test_issue_custody_does_not_bypass_measured_disk_limit(self):
        owner = self.budget()
        run = owner.create("primary")
        self.allocated_file(run / "scratch", 2_000_000)
        with self.assertRaisesRegex(RuntimeError, "DISK_BUDGET_EXHAUSTED"):
            require_training_run(run, self.base / "code/runs", issue_budget=owner)

    def setUp(self) -> None:
        self.temporary = TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.base = Path(self.temporary.name)

    def budget(self, root: str = "issue-349", **kwargs) -> ExperimentRunBudget:
        max_bytes = kwargs.pop("max_bytes", 1_000_000)
        return ExperimentRunBudget(self.base / root, max_bytes=max_bytes, **kwargs)

    @staticmethod
    def allocated_file(path: Path, size: int = 32) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(b"x" * size)

    def test_create_registers_an_issue_owned_run_and_measures_blocks(self) -> None:
        owner = self.budget()
        run = owner.create("primary")
        self.allocated_file(run / "checkpoint.bin")
        report = owner.check()
        self.assertTrue(run.is_dir())
        self.assertEqual(1, report["run_count"])
        self.assertGreaterEqual(report["used_bytes"], 32)
        self.assertTrue(report["within_budget"])

    def test_create_refuses_third_run_and_existing_unregistered_path(self) -> None:
        owner = self.budget()
        owner.create("primary")
        owner.create("challenger")
        with self.assertRaisesRegex(RuntimeError, "EXPERIMENT_RUN_LIMIT"):
            owner.create("third")
        other = self.budget("other")
        other.root.mkdir(parents=True)
        (other.root / "unregistered").mkdir()
        with self.assertRaisesRegex(RuntimeError, "EXPERIMENT_RUN_UNREGISTERED_PATH"):
            other.create("unregistered")

    def test_create_rejects_alias_escape_before_creating_a_lock(self) -> None:
        target = self.base / "target"
        target.mkdir()
        alias = self.base / "alias"
        alias.symlink_to(target, target_is_directory=True)
        owner = self.budget("alias")
        with self.assertRaisesRegex(RuntimeError, "EXPERIMENT_RUN_SYMLINK"):
            owner.create("primary")
        self.assertFalse((target / ".issue349-experiment-runs.lock").exists())

    def test_preflight_refusal_leaves_no_new_run_or_registry(self) -> None:
        owner = ExperimentRunBudget(self.base / "tight", max_bytes=8, reserve_bytes=8)
        with self.assertRaisesRegex(RuntimeError, "EXPERIMENT_DISK_PRECHECK_EXHAUSTED"):
            owner.create("primary", required_bytes=1)
        self.assertFalse((owner.root / "primary").exists())
        self.assertFalse(owner.registry_path.exists())

    def test_registry_budget_and_reserve_are_immutable_after_creation(self) -> None:
        owner = self.budget(reserve_bytes=64)
        owner.create("primary")
        restarted = ExperimentRunBudget(owner.root, max_bytes=999_999, reserve_bytes=64)
        with self.assertRaisesRegex(RuntimeError, "EXPERIMENT_RUN_BUDGET_DRIFT"):
            restarted.check()

    def test_hardlinks_are_charged_conservatively_and_enforced(self) -> None:
        owner = self.budget(max_bytes=1)
        run = owner.create("primary")
        self.allocated_file(run / "one", 32)
        (run / "two").hardlink_to(run / "one")
        report = owner.check()
        self.assertGreaterEqual(report["used_bytes"], 64)
        self.assertFalse(report["within_budget"])
        with self.assertRaisesRegex(RuntimeError, "EXPERIMENT_DISK_BUDGET_EXHAUSTED"):
            owner.enforce()

    def test_prewrite_guard_accounts_collective_usage_and_required_bytes(self) -> None:
        owner = self.budget(max_bytes=100_000)
        run = owner.create("primary")
        self.allocated_file(run / "scratch.bin", 32)
        report = owner.assert_can_allocate(1)
        self.assertEqual(report["run_count"], 1)
        self.assertEqual(report["required_bytes"], 1)
        with self.assertRaisesRegex(
                RuntimeError, "EXPERIMENT_DISK_PRECHECK_EXHAUSTED"):
            owner.assert_can_allocate(100_000)

    def test_prune_only_explicit_disposable_files_and_writes_receipt(self) -> None:
        owner = self.budget()
        run = owner.create("primary")
        self.allocated_file(run / "current", 32)
        self.allocated_file(run / "scratch.bin", 32)
        receipt = owner.prune(run, ["scratch.bin"])
        self.assertTrue((run / "current").exists())
        self.assertFalse((run / "scratch.bin").exists())
        self.assertTrue(receipt.exists())

    def test_prune_protects_default_descendants_and_recorded_requirements(self) -> None:
        owner = self.budget()
        run = owner.create("primary", required_paths=["referenced/model.bundle"])
        protected = [
            "current/checkpoint.bin", "best/checkpoint.bin", "recovery/adamw.bin",
            "state/current.json", "manifests/source.json", "bundles/model.bin",
            "autonomy/current.json", "factory-releases/release.json",
            "state.json", "events.jsonl", "referenced/model.bundle",
        ]
        for relative in protected:
            self.allocated_file(run / relative)
            with self.assertRaisesRegex(RuntimeError, "EXPERIMENT_RUN_PROTECTED_ARTIFACT"):
                owner.prune(run, [relative])
        with self.assertRaisesRegex(RuntimeError, "EXPERIMENT_RUN_PATH_ESCAPE"):
            owner.prune(run, ["../outside"])

    def test_prune_never_follows_intermediate_symlink_outside_run(self) -> None:
        owner = self.budget()
        run = owner.create("primary")
        outside = self.base / "canonical-evidence"
        self.allocated_file(outside / "checkpoint.bin")
        (run / "escape").symlink_to(outside, target_is_directory=True)
        with self.assertRaisesRegex(RuntimeError, "EXPERIMENT_RUN_SYMLINK"):
            owner.prune(run, ["escape/checkpoint.bin"])
        self.assertTrue((outside / "checkpoint.bin").exists())


if __name__ == "__main__":
    unittest.main()
