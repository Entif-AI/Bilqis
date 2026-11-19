"""BMF v0.3.8 objective identity bindings remain explicit and versioned."""
from __future__ import annotations

from dataclasses import replace
import unittest

from bilqis_mlx.errors import BilqisError
from bilqis_mlx.learning._retention._atlas_candidate.common import (
    OBJECTIVE_STEP_PROOF_SCHEMA,
)
from bilqis_mlx.learning._retention._atlas_candidate.proofs import CandidateStepProof
from bilqis_mlx.learning._retention._atlas_candidate.state import (
    CandidateCustodyIdentity,
)
from bilqis_mlx.runtime._atlas_resources.distributed_contracts import (
    DISTRIBUTED_STEP_MANIFEST_SCHEMA,
    LEGACY_DISTRIBUTED_STEP_MANIFEST_SCHEMA,
    DistributedRank, DistributedStepManifest,
)
from bilqis_mlx.runtime.bamf_bundle.generation_manifest import (
    BAMF_BUNDLE_SCHEMA, OBJECTIVE_BOUND_BAMF_BUNDLE_SCHEMA,
    BamfGenerationManifest,
)
from bilqis_mlx.runtime.training_objective import (
    current_training_objective, require_training_objective_digest,
)


class TrainingObjectiveIdentityBindingTests(unittest.TestCase):
    def setUp(self):
        self.objective = current_training_objective()

    @staticmethod
    def _generation(**overrides):
        values = {
            "run_id": "fixture-run",
            "generation": 0,
            "parent_manifest_sha256": None,
            "implementation_sha256": "1" * 64,
            "topology": {"schema": "topology"},
            "extents": {"schema": "extents"},
            "provenance": {"schema": "provenance"},
            "tensors": {"schema": "tensors"},
            "optimizer": {"schema": "optimizer"},
            "transition": {
                "schema": "bilqis.mlx.bamf-generation-transition/v1",
                "kind": "INITIAL",
                "invalidate_derived_caches": False,
            },
            "sidecars": {"schema": "sidecars"},
        }
        values.update(overrides)
        return BamfGenerationManifest(**values)

    def test_new_generation_manifest_binds_objective_but_v2_round_trips(self):
        current = self._generation(
            training_objective_ref=self.objective.ref,
            training_objective_digest=self.objective.digest,
            schema=OBJECTIVE_BOUND_BAMF_BUNDLE_SCHEMA)
        self.assertEqual(
            BamfGenerationManifest.from_record(current.to_record()), current)
        legacy = self._generation(schema=BAMF_BUNDLE_SCHEMA)
        self.assertNotIn("training_objective_digest", legacy.to_record())
        self.assertEqual(
            BamfGenerationManifest.from_record(legacy.to_record()), legacy)
        with self.assertRaises(BilqisError):
            replace(current, training_objective_digest="f" * 64)

    def test_new_in_memory_custody_defaults_to_current_objective(self):
        custody = CandidateCustodyIdentity(
            "fixture-run", 0, "2" * 64, "3" * 64, "4" * 64)
        self.assertEqual(custody.training_objective_ref, self.objective.ref)
        self.assertEqual(
            custody.training_objective_digest, self.objective.digest)
        historical = CandidateCustodyIdentity(
            "fixture-run", 0, "2" * 64, "3" * 64, "4" * 64, None, None)
        self.assertIsNone(historical.training_objective_digest)

    def test_objective_step_proof_round_trips_digest(self):
        proof = CandidateStepProof(
            1, "1" * 64, "2" * 64, "3" * 64, ("identity.bank.0",), True,
            source_release_sha256="4" * 64,
            training_batch_sha256="5" * 64,
            target_capability_id="A.TEST",
            training_authority_sha256="6" * 64,
            source_family_id="family:a",
            episode_id="episode:a",
            training_objective_digest=self.objective.digest,
            schema_version=OBJECTIVE_STEP_PROOF_SCHEMA)
        record = proof.to_record()
        self.assertEqual(
            record["training_objective_digest"], self.objective.digest)
        self.assertEqual(CandidateStepProof.from_record(record), proof)

    def test_distributed_manifest_defaults_current_and_preserves_v1_read(self):
        current = DistributedStepManifest(
            7, "a" * 64, "factory:test", "b" * 64, "c" * 64, 17, 1,
            (DistributedRank(0, "worker-a", "M3 Ultra"),),
            "0.test", "ring", "fp32")
        self.assertEqual(current.schema_version, DISTRIBUTED_STEP_MANIFEST_SCHEMA)
        self.assertEqual(
            current.training_objective_digest, self.objective.digest)
        legacy = replace(
            current,
            training_objective_digest=None,
            schema_version=LEGACY_DISTRIBUTED_STEP_MANIFEST_SCHEMA)
        legacy.__post_init__()
        self.assertIsNone(legacy.training_objective_digest)
        with self.assertRaises(BilqisError):
            replace(current, training_objective_digest="f" * 64)

    def test_objective_digest_drift_fails_before_use(self):
        require_training_objective_digest(self.objective.digest)
        with self.assertRaises(BilqisError):
            require_training_objective_digest("f" * 64)


if __name__ == "__main__":
    unittest.main()
