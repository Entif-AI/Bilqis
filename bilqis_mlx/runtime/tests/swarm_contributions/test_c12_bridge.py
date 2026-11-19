import json
from pathlib import Path
from unittest.mock import patch

from bilqis_mlx.errors import BilqisError
from bilqis_mlx.runtime import mlx_checkpoint
from bilqis_mlx.runtime.cognitive_package.tests.adoption_harness import AdoptionHarness
from bilqis_mlx.runtime.tests.custody.bamf_bundle.helpers import NAME, shape_patch
from bilqis_mlx.runtime.swarm_contributions import (
    AcceptanceContract, CanonicalPackageAdmissionContext,
    ContributionArtifact, ContributionClass, ContributionDisposition,
    EnvironmentIdentity, RemoteWorkManifest, ResourceBudget,
    ResourceUsage, WorkerIdentity, WorkerReceipt, admit_remote_cognitive_package,
    package_binding_digest,
)
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey


KEY = Ed25519PrivateKey.from_private_bytes(bytes.fromhex("44" * 32))


class SwarmC12BridgeTests(AdoptionHarness):
    def _remote(self, package, *, policy_sha256):
        binding = package_binding_digest(package.binding)
        work = RemoteWorkManifest.create(
            manifest_id="work:c12-fixture", retained_generation=self.pointer["manifest_sha256"],
            source_release=self.initial.provenance.release_digest,
            capability_id=self.factory_release.execution_plan.capabilities[0].capability_id,
            seed=91, partition_id="partition:c12", resource_budget=ResourceBudget(
                max_examples=64, max_steps=8, max_seconds=120,
                max_bytes=max(1_000_000, len(package.canonical_json.encode()))),
            model_identity=self.initial.implementation_sha256,
            topology_identity=self.initial.topology.digest,
            mlx_identity="mlx:fixture", rights_scope="PUBLIC_DERIVED",
            contribution_class=ContributionClass.ADAPTER_DELTA,
            acceptance=AcceptanceContract(policy_sha256, 0.0, True),
            expires_at=2_000, replay_id="replay:c12-fixture",
            base_binding_digest=binding)
        artifact = ContributionArtifact(
            work.expected_artifact_type, package.canonical_json.encode(),
            base_binding_digest=binding, affected_parameter_ids=(NAME,))
        worker = WorkerIdentity(
            "worker:c12-fixture", KEY.public_key().public_bytes_raw().hex(),
            EnvironmentIdentity("fixture", "fixture", "fixture", "fixture", 1))
        unsigned = WorkerReceipt.unsigned(
            manifest=work, worker=worker, artifact=artifact, claimed_score=1.0,
            usage=ResourceUsage(1, 1, 1, len(artifact.payload)), completed_at=1_500)
        return work, unsigned.with_signature(KEY.sign(unsigned.signing_bytes()).hex())

    def _context(self, receipt):
        return CanonicalPackageAdmissionContext(
            self.root / "remote-inbox", self.root / "remote-staging", self.run,
            2_000_000, self.source_context(), self.root / "artifact",
            self.factory_release.execution_plan.capabilities[0].capability_id,
            receipt, self.selection, self.frontier, reserve_gib=0.0)

    def test_c05_rejection_never_reaches_b13_publication(self):
        screened, clearance = self.screened(accepted=False)
        package = screened.candidate.package
        work, remote = self._remote(
            package, policy_sha256=screened.decision.policy_sha256)
        before = self.pointer["manifest_sha256"]
        with shape_patch(), patch(
            "bilqis_mlx.runtime.swarm_contributions.c12_bridge.screen_received_package",
            return_value=screened,
        ), patch(
            "bilqis_mlx.runtime.swarm_contributions.c12_bridge.publish_screened_delta_import",
            side_effect=AssertionError("rejected remote contribution reached publication"),
        ):
            decision = admit_remote_cognitive_package(
                work, remote, now=1_600, context=self._context(clearance))
        self.assertIs(decision.disposition, ContributionDisposition.REJECTED)
        pointer = json.loads((self.run / "bamf-state.json").read_text())
        self.assertEqual(pointer["manifest_sha256"], before)
        self.assertTrue((self.run / "swarm-contribution-replay").is_dir())

    def test_c05_accepted_remote_package_publishes_only_through_b13(self):
        screened, clearance = self.screened(accepted=True)
        package = screened.candidate.package
        work, remote = self._remote(
            package, policy_sha256=screened.decision.policy_sha256)
        with shape_patch(), patch(
            "bilqis_mlx.runtime.swarm_contributions.c12_bridge.screen_received_package",
            return_value=screened,
        ), patch.object(mlx_checkpoint, "assert_headroom"):
            context = self._context(clearance)
            decision = admit_remote_cognitive_package(
                work, remote, now=1_600, context=context)
        self.assertIs(decision.disposition, ContributionDisposition.ADMITTED)
        pointer = json.loads((self.run / "bamf-state.json").read_text())
        self.assertEqual(decision.canonical_generation, pointer["manifest_sha256"])
        self.assertTrue((context.sender_dir / f"{package.digest}.json").is_file())

    def test_declared_parameter_scope_must_match_package_delta(self):
        screened, clearance = self.screened(accepted=True)
        package = screened.candidate.package
        work, remote = self._remote(
            package, policy_sha256=screened.decision.policy_sha256)
        from dataclasses import replace
        forged_artifact = replace(
            remote.artifact, affected_parameter_ids=("not-the-package-parameter",))
        unsigned = replace(remote, artifact=forged_artifact, signature_hex="0" * 128)
        forged = unsigned.with_signature(KEY.sign(unsigned.signing_bytes()).hex())
        with shape_patch(), patch(
            "bilqis_mlx.runtime.swarm_contributions.c12_bridge.screen_received_package",
            side_effect=AssertionError("forged parameter scope reached C05"),
        ):
            with self.assertRaises(BilqisError):
                admit_remote_cognitive_package(
                    work, forged, now=1_600, context=self._context(clearance))

    def test_stale_manifest_generation_rejects_before_c05_screen(self):
        screened, clearance = self.screened(accepted=True)
        package = screened.candidate.package
        work, remote = self._remote(
            package, policy_sha256=screened.decision.policy_sha256)
        from dataclasses import replace
        stale = replace(work, retained_generation="7" * 64)
        remote = replace(remote, manifest_digest=stale.digest)
        unsigned = replace(remote, signature_hex="0" * 128)
        remote = unsigned.with_signature(KEY.sign(unsigned.signing_bytes()).hex())
        with shape_patch(), patch(
            "bilqis_mlx.runtime.swarm_contributions.c12_bridge.screen_received_package",
            side_effect=AssertionError("stale manifest reached C05"),
        ):
            with self.assertRaises(BilqisError):
                admit_remote_cognitive_package(
                    stale, remote, now=1_600, context=self._context(clearance))

    def test_manifest_capability_must_match_canonical_target(self):
        screened, clearance = self.screened(accepted=True)
        package = screened.candidate.package
        work, remote = self._remote(
            package, policy_sha256=screened.decision.policy_sha256)
        from dataclasses import replace
        wrong = replace(work, capability_id="capability:wrong-target")
        unsigned = replace(
            remote, manifest_digest=wrong.digest, signature_hex="0" * 128)
        remote = unsigned.with_signature(KEY.sign(unsigned.signing_bytes()).hex())
        with shape_patch(), patch(
            "bilqis_mlx.runtime.swarm_contributions.c12_bridge.screen_received_package",
            side_effect=AssertionError("wrong capability reached C05"),
        ):
            with self.assertRaises(BilqisError):
                admit_remote_cognitive_package(
                    wrong, remote, now=1_600, context=self._context(clearance))

    def test_wrong_c05_policy_digest_rejects_before_publication(self):
        screened, clearance = self.screened(accepted=True)
        package = screened.candidate.package
        work, remote = self._remote(package, policy_sha256="8" * 64)
        with shape_patch(), patch(
            "bilqis_mlx.runtime.swarm_contributions.c12_bridge.screen_received_package",
            return_value=screened,
        ), patch(
            "bilqis_mlx.runtime.swarm_contributions.c12_bridge.publish_screened_delta_import",
            side_effect=AssertionError("wrong policy reached publication"),
        ):
            with self.assertRaises(BilqisError):
                admit_remote_cognitive_package(
                    work, remote, now=1_600, context=self._context(clearance))


if __name__ == "__main__":
    import unittest
    unittest.main()
