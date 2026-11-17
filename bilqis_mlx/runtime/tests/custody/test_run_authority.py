"""R17 typed native BAMF run authority and cold-resume custody guards."""
from __future__ import annotations

from pathlib import Path
from tempfile import TemporaryDirectory
from types import SimpleNamespace
import unittest
from unittest.mock import patch

from bilqis_mlx.errors import BilqisError, SCHOOL
from bilqis_mlx.runtime.experiment_runs import ExperimentRunBudget
from bilqis_mlx.runtime.run_authority import (
    bind_native_run_authority,
    issue_experiment_run_authority,
)


class NativeRunAuthorityTests(unittest.TestCase):
    def setUp(self):
        self.temporary = TemporaryDirectory()
        self.root = Path(self.temporary.name)
        self.owner = ExperimentRunBudget(self.root, max_bytes=4_000_000)
        self.run = self.owner.create("future-grade-run")
        self.run_id = "run:future-generated-grade"
        self.inspection = SimpleNamespace(
            run_id=self.run_id, run_identity_sha256="a" * 64)

    def tearDown(self):
        self.temporary.cleanup()

    def _bind(self, authority, **kwargs):
        with patch(
                "bilqis_mlx.runtime.run_authority.binding.inspect_accepted_generation",
                return_value=self.inspection):
            return bind_native_run_authority(self.run, authority, **kwargs)

    def test_registered_authority_binds_exactly_and_cold_resume_reuses_identity(self):
        first = issue_experiment_run_authority(
            self.owner, self.run, self.run_id)
        bound = self._bind(first)
        self.assertEqual(bound.record.authority.digest, first.identity.digest)
        self.assertEqual(bound.record.run_identity_sha256, "a" * 64)

        cold = issue_experiment_run_authority(
            ExperimentRunBudget(self.root, max_bytes=4_000_000),
            self.run, self.run_id)
        rebound = self._bind(cold)
        self.assertEqual(rebound.record.digest, bound.record.digest)

    def test_unregistered_authority_fails_closed(self):
        rogue = self.root / "rogue"
        rogue.mkdir()
        with self.assertRaisesRegex(RuntimeError, "EXPERIMENT_RUN_UNREGISTERED_PATH"):
            issue_experiment_run_authority(self.owner, rogue, self.run_id)

    def test_expired_authority_fails_before_binding(self):
        authority = issue_experiment_run_authority(
            self.owner, self.run, self.run_id, expires_at_unix_seconds=10)
        with self.assertRaises(BilqisError) as caught:
            self._bind(authority, now=10)
        self.assertIs(caught.exception.spec, SCHOOL.BAMF_RUN_AUTHORITY.INVALID)
        self.assertEqual(caught.exception.context["reason"], "BAMF_RUN_AUTHORITY_EXPIRED")

    def test_collective_budget_exhaustion_fails_before_binding(self):
        owner = ExperimentRunBudget(self.root / "budget", max_bytes=128_000)
        run = owner.create("future-grade-run")
        authority = issue_experiment_run_authority(owner, run, self.run_id)
        (run / "allocation.bin").write_bytes(b"x" * 256_000)
        with patch(
                "bilqis_mlx.runtime.run_authority.binding.inspect_accepted_generation",
                return_value=self.inspection):
            with self.assertRaisesRegex(
                    RuntimeError, "EXPERIMENT_DISK_BUDGET_EXHAUSTED"):
                bind_native_run_authority(run, authority)

    def test_cold_resume_rejects_different_owner_identity(self):
        first = issue_experiment_run_authority(
            self.owner, self.run, self.run_id)
        self._bind(first)
        changed = issue_experiment_run_authority(
            self.owner, self.run, self.run_id,
            owner_identity="experiment:other-owner")
        with self.assertRaises(BilqisError) as caught:
            self._bind(changed)
        self.assertIs(caught.exception.spec, SCHOOL.BAMF_RUN_AUTHORITY.INVALID)
        self.assertEqual(
            caught.exception.context["reason"], "BAMF_RUN_AUTHORITY_RESUME_DRIFT")


if __name__ == "__main__":
    unittest.main()
