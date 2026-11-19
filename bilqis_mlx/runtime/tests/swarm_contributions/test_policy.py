from dataclasses import replace
from pathlib import Path
from tempfile import TemporaryDirectory
from types import SimpleNamespace
import unittest
from unittest.mock import patch

from bilqis_mlx.errors import BilqisError
from bilqis_mlx.runtime.swarm_contributions import (
    ContributionClass, ContributionDisposition, IndependentEvaluation,
    admit_remote_observation, dispatch_eligible_work,
)
from bilqis_mlx.runtime.tests.swarm_contributions.fixtures import (
    GENERATION, MODEL, SOURCE, TOPOLOGY, manifest, receipt,
)


class SwarmPolicyTests(unittest.TestCase):
    def setUp(self):
        self.temp = TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.run_dir = Path(self.temp.name) / "run"
        self.run_dir.mkdir()
        student = SimpleNamespace(
            provenance=SimpleNamespace(release_digest=SOURCE),
            implementation_sha256=MODEL,
            topology=SimpleNamespace(digest=TOPOLOGY),
        )
        self.school = patch(
            "bilqis_mlx.runtime.swarm_contributions.school._load_current_generation",
            return_value=({"manifest_sha256": GENERATION}, student),
        )
        self.school.start()
        self.addCleanup(self.school.stop)

    def test_worker_score_is_evidence_not_non_neural_authority(self):
        work = manifest()
        result = receipt(work, score=1.0)
        decision = admit_remote_observation(
            work, result, now=1_600, run_dir=self.run_dir,
            target_capability=work.capability_id,
            independent_evaluator=lambda *_: IndependentEvaluation(
                False, 0.25, "1" * 64, "retention:failed"))
        self.assertIs(decision.disposition, ContributionDisposition.REJECTED)
        self.assertEqual(result.claimed_score, 1.0)
        self.assertEqual(decision.canonical_evidence_digest, "1" * 64)

    def test_retention_requirement_cannot_be_bypassed_by_score(self):
        work = manifest()
        result = receipt(work)
        decision = admit_remote_observation(
            work, result, now=1_600, run_dir=self.run_dir,
            target_capability=work.capability_id,
            independent_evaluator=lambda *_: IndependentEvaluation(
                True, 1.0, "6" * 64, "retention:failed"))
        self.assertIs(decision.disposition, ContributionDisposition.REJECTED)

    def test_stale_non_neural_manifest_rejects_before_evaluation(self):
        work = replace(manifest(), retained_generation="7" * 64)
        result = receipt(work)
        with self.assertRaises(BilqisError):
            admit_remote_observation(
                work, result, now=1_600, run_dir=self.run_dir,
                target_capability=work.capability_id,
                independent_evaluator=lambda *_: (_ for _ in ()).throw(
                    AssertionError("stale work reached evaluator")),
            )

    def test_non_neural_manifest_capability_must_match_target(self):
        work = manifest()
        result = receipt(work)
        with self.assertRaises(BilqisError):
            admit_remote_observation(
                work, result, now=1_600, run_dir=self.run_dir,
                target_capability="capability:wrong-target",
                independent_evaluator=lambda *_: (_ for _ in ()).throw(
                    AssertionError("wrong capability reached evaluator")),
            )

    def test_dense_updates_and_private_scope_fail_closed(self):
        with self.assertRaises(BilqisError):
            manifest(ContributionClass.DENSE_UPDATE)
        with self.assertRaises(BilqisError):
            manifest(rights_scope="PRIVATE_REAL")
        with self.assertRaises(BilqisError):
            manifest(rights_scope="UNCLASSIFIED")

    def test_public_derived_scope_is_explicitly_permitted(self):
        work = manifest(rights_scope="PUBLIC_DERIVED")
        self.assertEqual(work.rights_scope, "PUBLIC_DERIVED")

    def test_swarm_dispatch_is_optional_and_deterministic(self):
        first = manifest()
        second = replace(first, manifest_id="work:fixture-002", replay_id="replay:fixture-002")
        self.assertEqual(
            dispatch_eligible_work((first,), available_workers=()), ())
        result = dispatch_eligible_work(
            (second, first), available_workers=("worker:2", "worker:1"))
        self.assertEqual(tuple(item[1] for item in result),
                         tuple(sorted((first.digest, second.digest))))


if __name__ == "__main__":
    unittest.main()
