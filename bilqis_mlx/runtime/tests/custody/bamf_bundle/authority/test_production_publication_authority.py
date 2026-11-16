"""Publication and retention authority witnesses for accepted BAMF generations."""
import json
import os
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest
from unittest.mock import patch

import bilqis_mlx.runtime.mlx_checkpoint as mlx_checkpoint
from bilqis_mlx.errors import BilqisError
from bilqis_mlx.learning.atlas_acceptance import (
    AcceptedCandidateBinding, mint_acceptance_binding,
)
from bilqis_mlx.learning.atlas_retention_decision import (
    CandidateRetentionDecision, decide_candidate_retention,
)
from bilqis_mlx.runtime.bamf_bundle import (
    load_bamf_generation, publish_bamf_generation,
)
from bilqis_mlx.runtime.tests.custody.bamf_bundle.helpers import (
    accepted_state, candidate, parent_state, publish_candidate,
    retention_decision, shape_patch,
)


class ProductionPublicationAuthorityTests(unittest.TestCase):
    def setUp(self):
        self.temporary = TemporaryDirectory()
        self.root = Path(self.temporary.name)
        self.run = self.root / "run"
        self.environment = patch.dict(
            os.environ, {"BILQIS_DATA_PLANE": str(self.root / "plane.sqlite3")})
        self.environment.start()

    def tearDown(self):
        self.environment.stop()
        self.temporary.cleanup()

    def publish(self, source):
        with shape_patch(), patch.object(mlx_checkpoint, "assert_headroom"):
            return publish_candidate(self.run, source)

    def test_caller_created_candidate_cannot_publish_without_the_decision_owner(self):
        source = candidate(parent_state())
        with shape_patch(), patch.object(mlx_checkpoint, "assert_headroom"):
            with self.assertRaises(BilqisError):
                publish_bamf_generation(self.run, source)
        self.assertFalse((self.run / "bamf-state.json").exists())

    def test_caller_cannot_mint_a_retention_decision(self):
        decision = retention_decision()
        with self.assertRaises(BilqisError):
            CandidateRetentionDecision(
                decision.decision, decision.reason, decision.parent_generation,
                decision.candidate_generation, decision.evidence_sha256,
                decision.policy_sha256)

    def test_primitive_retention_claims_cannot_issue_authority(self):
        with self.assertRaises(TypeError):
            decide_candidate_retention(
                no_target_gain=False, same_grade_net_gain=1,
                fixed_grade_regression=False, active_grade_regression=False,
                whole_school_regression=False, frontier_measured=True,
                fragile_losses=0, exceeded=False)

    def test_caller_selected_c05_screen_cannot_issue_live_authority(self):
        from bilqis_mlx.runtime.tests.capability.capability_retention_helpers import (
            _screen_inputs,
        )
        screen = _screen_inputs()
        with self.assertRaises(BilqisError) as failure:
            decide_candidate_retention(
                parent_solver=screen[0], candidate_solver=screen[1],
                target_capability=screen[2], policy=screen[3], cohorts=screen[4],
                parent_state=parent_state(),
                candidate_state=accepted_state(parent_state()))
        self.assertEqual(failure.exception.context["reason"],
                         "BAMF_C05_SOURCE_OWNER_REQUIRED")

    def test_acceptance_requires_an_accepted_decision(self):
        source = candidate(parent_state())
        rejected = retention_decision(
            accepted=False, retained=source.retained_state)
        with self.assertRaises(BilqisError):
            mint_acceptance_binding(
                rejected, source.retained_state, run_id=source.run_id,
                generation=source.generation,
                feature_sha256=source.extents.factor_map_digest)

    def test_step_proofs_survive_publication_and_cold_readback(self):
        initial = parent_state()
        first = self.publish(candidate(initial))
        retained = accepted_state(initial)
        second = self.publish(candidate(retained, 1, first["manifest_sha256"]))
        with shape_patch():
            student = load_bamf_generation(self.run / "bamf-state.json")
        proofs = student.retained_state.step_proofs
        self.assertEqual(len(proofs), 1)
        binding = AcceptedCandidateBinding.from_record(json.loads(
            (self.run / "bamf-acceptance" / f"{second['manifest_sha256']}.json")
            .read_text()))
        self.assertEqual(list(binding.step_proof_sha256),
                         [proof.digest for proof in proofs])

    def test_tampered_step_proof_fails_custody_validation(self):
        initial = parent_state()
        first = self.publish(candidate(initial))
        retained = accepted_state(initial)
        second = self.publish(candidate(retained, 1, first["manifest_sha256"]))
        proofs = (self.run / "bamf-bundles" / second["manifest_sha256"]
                  / "step-proofs.json")
        record = json.loads(proofs.read_text())
        record["proofs"][0]["mask_sha256"] = "0" * 64
        proofs.write_text(json.dumps(record))
        with shape_patch():
            with self.assertRaises(BilqisError):
                load_bamf_generation(self.run / "bamf-state.json")


if __name__ == "__main__":
    unittest.main()
