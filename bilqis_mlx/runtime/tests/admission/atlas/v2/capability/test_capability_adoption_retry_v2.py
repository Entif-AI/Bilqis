"""Capability-only Atlas v2 adoption and retry tests."""

from dataclasses import FrozenInstanceError

from bilqis_mlx.runtime.tests.admission.atlas.v2.capability.capability_support import *
from bilqis_mlx.runtime.jit_adoption import _PreparedSuccessorRuntime
from bilqis_mlx.runtime.atlas_capability_adoption_v2 import (
    _accepted_capability_only_retry_state_v2,
)
from bilqis_mlx.factory.atlas_frontier_progress_validation import requested_keys
from bilqis_mlx.runtime.bamf_bundle.factory_release.admission import (
    FACTORY_RELEASE_ADMISSION_SCHEMA_V2,
)

class CapabilityAdoptionRetryV2Tests(CapabilityV2Support):
    def test_historical_retry_rejects_later_nonmatching_factory_successor(self):
        handoff = self._handoff()
        approval, lease = self._lease_authority(handoff)
        pure = self._context(handoff, approval)
        current = replace(
            pure,
            runtime=_PreparedSuccessorRuntime(
                None, pure.run_dir, {"school": {}}, None, None, {},
                object(), object(), 0.),
            source_authority=object(),
        )
        pointer = {
            "generation": 2,
            "manifest_sha256": "d" * 64,
            "acceptance_sha256": "e" * 64,
        }
        accepted = SimpleNamespace(
            retained_state=SimpleNamespace(
                optimizer_step=pure.legacy.checkpoint.optimizer_step),
        )
        foreign_release = SimpleNamespace(release_sha256="f" * 64)

        with patch(
                "bilqis_mlx.runtime.bamf_bundle.feature.acceptance.accepted_generation",
                return_value=(pointer, accepted)), patch(
                "bilqis_mlx.runtime.atlas_admission.read_accepted_atlas_factory_release",
                return_value=foreign_release), patch(
                "bilqis_mlx.runtime.atlas_admission._accepted_run_lease_identity",
                return_value=pure.legacy.run_identity), patch(
                "bilqis_mlx.runtime.atlas_admission.read_accepted_atlas_lease_v2",
                return_value=lease), patch(
                "bilqis_mlx.runtime.atlas_capability_adoption_v2."
                "_require_exact_atlas_release"), self.assertRaises(BilqisError) as caught:
            _accepted_capability_only_retry_state_v2(current, handoff, lease)

        self.assertEqual(
            caught.exception.context["reason"],
            "BAMF_ATLAS_V2_CAPABILITY_RETRY_CONFLICT",
        )

    def test_historical_retry_rejects_tampered_factory_binding_before_live_verifier(self):
        handoff = self._handoff()
        approval, lease = self._lease_authority(handoff)
        pure = self._context(handoff, approval)
        current = replace(
            pure,
            runtime=_PreparedSuccessorRuntime(
                None, pure.run_dir, {"school": {}}, None, None, {},
                object(), object(), 0.),
            source_authority=object(),
        )
        successor = handoff.staged_candidate.successor.release_sha256
        pointer = {
            "generation": 1,
            "manifest_sha256": "d" * 64,
            "acceptance_sha256": "e" * 64,
        }
        accepted = SimpleNamespace(
            run_id="fixture-v2-capability",
            parent_manifest_sha256="a" * 64,
            retained_state=SimpleNamespace(
                optimizer_step=pure.legacy.checkpoint.optimizer_step),
            transition={
                "staged_candidate_sha256": handoff.staged_candidate.staged_sha256,
            },
        )

        class ParsedFactoryBinding:
            run_id = accepted.run_id
            handoff_sha256 = handoff.handoff_sha256
            proposal_sha256 = "f" * 64
            selection_receipt_sha256 = handoff.receipt.receipt_sha256
            lease_sha256 = lease.digest()
            source_approval_sha256 = __import__(
                "bilqis_mlx.semantics.domains", fromlist=["contract_digest"]
            ).contract_digest(lease.source_approval)
            predecessor_factory_release_sha256 = (
                handoff.receipt.predecessor_release.release_sha256
            )
            factory_release_sha256 = successor

        host = SimpleNamespace(source_authority=lambda: object())
        with patch(
                "bilqis_mlx.runtime.bamf_bundle.feature.acceptance.accepted_generation",
                return_value=(pointer, accepted)), patch(
                "bilqis_mlx.runtime.atlas_admission.read_accepted_atlas_factory_release",
                return_value=SimpleNamespace(release_sha256=successor)), patch(
                "bilqis_mlx.runtime.atlas_admission._accepted_run_lease_identity",
                return_value=pure.legacy.run_identity), patch(
                "bilqis_mlx.runtime.atlas_admission.read_accepted_atlas_lease_v2",
                return_value=lease), patch(
                "bilqis_mlx.runtime.accepted_corrections.AcceptedRuntimeHost",
                return_value=host), patch(
                "bilqis_mlx.runtime.bamf_bundle.factory_release.admission."
                "ParsedFactoryReleaseAdmissionBinding",
                ParsedFactoryBinding), patch(
                "bilqis_mlx.runtime.bamf_bundle.feature.acceptance."
                "accepted_binding_for_manifest",
                return_value=ParsedFactoryBinding()), patch(
                "bilqis_mlx.runtime.atlas_capability_adoption_v2."
                "_require_exact_atlas_release"), self.assertRaises(BilqisError) as caught:
            _accepted_capability_only_retry_state_v2(current, handoff, lease)

        self.assertEqual(
            caught.exception.context["reason"],
            "BAMF_FACTORY_RELEASE_ADMISSION_BINDING_DRIFT",
        )

    def test_exact_retry_rebinds_c09_authority_after_accepted_generation_advances(self):
        handoff = self._handoff()
        approval, lease = self._lease_authority(handoff)
        pure = self._context(handoff, approval)
        stale_authority = object()
        fresh_authority = object()
        current = AtlasAdmissionContextV2(
            pure.legacy, pure.run_dir,
            runtime=_PreparedSuccessorRuntime(
                None, pure.run_dir, {"school": {}}, None, None, {},
                object(), object(), 0.),
            source_authority=stale_authority,
        )
        successor = handoff.staged_candidate.successor.release_sha256
        predecessor = handoff.receipt.predecessor_release.release_sha256
        pointer = {
            "generation": 1,
            "manifest_sha256": "d" * 64,
            "acceptance_sha256": "e" * 64,
        }
        accepted = SimpleNamespace(
            run_id="fixture-v2-capability",
            parent_manifest_sha256="a" * 64,
            retained_state=SimpleNamespace(
                optimizer_step=pure.legacy.checkpoint.optimizer_step),
            transition={"staged_candidate_sha256": handoff.staged_candidate.staged_sha256},
        )

        class ParsedFactoryBinding:
            run_id = accepted.run_id
            handoff_sha256 = handoff.handoff_sha256
            proposal_sha256 = handoff.proposal.proposal_sha256
            selection_receipt_sha256 = handoff.receipt.receipt_sha256
            lease_sha256 = lease.digest()
            source_approval_sha256 = __import__(
                "bilqis_mlx.semantics.domains", fromlist=["contract_digest"]
            ).contract_digest(lease.source_approval)
            predecessor_factory_release_sha256 = predecessor
            factory_release_sha256 = successor
            schema_version = FACTORY_RELEASE_ADMISSION_SCHEMA_V2
            accepted_obligation_keys = tuple(requested_keys((handoff.receipt,)))

        def accepted_lease(_run_dir, *, source_authority):
            if source_authority is not fresh_authority:
                raise AssertionError
            return lease

        host = SimpleNamespace(source_authority=lambda: fresh_authority)
        with patch(
                "bilqis_mlx.runtime.atlas_admission.read_accepted_atlas_lease_v2",
                side_effect=accepted_lease), \
                patch(
                    "bilqis_mlx.runtime.atlas_admission.read_accepted_atlas_factory_release",
                    return_value=SimpleNamespace(release_sha256=successor)), \
                patch(
                    "bilqis_mlx.runtime.accepted_corrections.AcceptedRuntimeHost",
                    return_value=host), \
                patch(
                    "bilqis_mlx.runtime.bamf_bundle.feature.acceptance.accepted_generation",
                    return_value=(pointer, accepted)), \
                patch(
                    "bilqis_mlx.runtime.bamf_bundle.feature.acceptance."
                    "accepted_binding_for_manifest",
                    return_value=ParsedFactoryBinding()), \
                patch(
                    "bilqis_mlx.runtime.bamf_bundle.factory_release.admission."
                    "ParsedFactoryReleaseAdmissionBinding",
                    ParsedFactoryBinding), \
                patch(
                    "bilqis_mlx.runtime.bamf_bundle.feature.acceptance."
                    "parent_acceptance_anchor_from_manifest",
                    return_value="f" * 64), \
                patch(
                    "bilqis_mlx.runtime.bamf_bundle.codec.load_bamf_bundle",
                    return_value=SimpleNamespace()), \
                patch(
                    "bilqis_mlx.runtime.atlas_capability_adoption_v2."
                    "_historical_factory_release_sha256",
                    return_value=predecessor), \
                patch(
                    "bilqis_mlx.runtime.atlas_capability_adoption_v2."
                    "_require_exact_atlas_release"):
            actual = accepted_capability_only_retry_v2(current, handoff, lease)

        self.assertEqual(actual, pointer)
