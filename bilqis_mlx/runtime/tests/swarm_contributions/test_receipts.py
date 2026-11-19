from dataclasses import replace
import copy
import unittest

from bilqis_mlx.errors import BilqisError
from bilqis_mlx.runtime.swarm_contributions import (
    ContributionArtifact, ContributionClass, EnvironmentIdentity, ReplayLedger,
    ResourceUsage, verify_remote_receipt,
)
from bilqis_mlx.runtime.tests.swarm_contributions.fixtures import (
    GENERATION, SOURCE, digest, manifest, receipt, remote_worker_receipt,
)


class SwarmReceiptTests(unittest.TestCase):
    def test_signed_content_addressed_receipt_roundtrips(self):
        work = manifest()
        result = remote_worker_receipt(work.canonical_json)
        self.assertEqual(result.manifest_digest, work.digest)
        self.assertEqual(result.artifact.digest, digest(b"public synthetic result"))
        verified = verify_remote_receipt(
            work, result, now=1_600, replay_ledger=ReplayLedger())
        self.assertEqual(verified.replay_ledger.consumed_replay_ids, (work.replay_id,))


    def test_manifest_and_receipt_have_strict_canonical_wire_roundtrip(self):
        work = manifest()
        result = receipt(work)
        decoded_work = type(work).from_canonical_json(work.canonical_json)
        decoded_result = type(result).from_canonical_json(result.canonical_json)
        self.assertEqual(decoded_work, work)
        self.assertEqual(decoded_work.digest, work.digest)
        self.assertEqual(decoded_result, result)
        self.assertEqual(decoded_result.digest, result.digest)
        verify_remote_receipt(
            decoded_work, decoded_result, now=1_600, replay_ledger=ReplayLedger())
        with self.assertRaises(BilqisError):
            type(work).from_canonical_json(work.canonical_json + " ")

    def test_replay_expiry_wrong_generation_source_and_tamper_reject(self):
        work = manifest()
        result = receipt(work)
        verified = verify_remote_receipt(
            work, result, now=1_600, replay_ledger=ReplayLedger())
        with self.assertRaises(BilqisError):
            verify_remote_receipt(
                work, result, now=1_601,
                replay_ledger=verified.replay_ledger)
        with self.assertRaises(BilqisError):
            verify_remote_receipt(
                work, result, now=2_001, replay_ledger=ReplayLedger())
        for changed in (
            replace(work, retained_generation="9" * 64),
            replace(work, source_release="8" * 64),
        ):
            with self.assertRaises(BilqisError):
                verify_remote_receipt(
                    changed, result, now=1_600, replay_ledger=ReplayLedger())
        tampered = copy.copy(result)
        object.__setattr__(tampered, "claimed_score", 0.99)
        with self.assertRaises(BilqisError):
            verify_remote_receipt(
                work, tampered, now=1_600, replay_ledger=ReplayLedger())


    def test_manifest_mlx_identity_must_match_signed_worker_environment(self):
        work = replace(manifest(), mlx_identity="mlx:wrong-runtime")
        result = receipt(work)
        with self.assertRaises(BilqisError):
            verify_remote_receipt(
                work, result, now=1_600, replay_ledger=ReplayLedger())

    def test_environment_and_usage_are_signed_and_budget_bounded(self):
        work = manifest()
        result = receipt(work)
        changed = copy.copy(result)
        object.__setattr__(changed.worker, "environment", replace(
            result.worker.environment, hardware="forged-hardware"))
        with self.assertRaises(BilqisError):
            verify_remote_receipt(
                work, changed, now=1_600, replay_ledger=ReplayLedger())

        over = replace(result, usage=ResourceUsage(
            examples=33, steps=1, seconds=3,
            payload_bytes=len(result.artifact.payload)))
        with self.assertRaises(BilqisError):
            verify_remote_receipt(
                work, over, now=1_600, replay_ledger=ReplayLedger())

    def test_adapter_requires_exact_base_binding_and_parameter_scope(self):
        work = manifest(ContributionClass.ADAPTER_DELTA)
        result = receipt(work)
        verify_remote_receipt(
            work, result, now=1_600, replay_ledger=ReplayLedger())
        wrong = receipt(work, artifact=ContributionArtifact(
            work.expected_artifact_type, b"wrong",
            base_binding_digest="7" * 64,
            affected_parameter_ids=("adapter.0.A",)))
        with self.assertRaises(BilqisError):
            verify_remote_receipt(
                work, wrong, now=1_600, replay_ledger=ReplayLedger())

    def test_fixture_constants_are_distinct_authority_identities(self):
        self.assertNotEqual(GENERATION, SOURCE)


if __name__ == "__main__":
    unittest.main()
