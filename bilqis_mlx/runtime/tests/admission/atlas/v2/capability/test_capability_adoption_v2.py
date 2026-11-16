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
class CapabilityAdoptionV2Tests(CapabilityV2Support):
    def test_generated_grade_authority_is_frozen_and_handoff_bound(self):
        from bilqis_mlx.runtime.generated_grade import (
            _mint_generated_grade_authority,
        )
        from bilqis_mlx.runtime.atlas_capability_adoption_v2 import (
            _generated_grade_digest,
        )
        handoff = self._handoff()
        authority = _mint_generated_grade_authority(type(
            "Proposal", (), {
                "proposal_sha256": "a" * 64,
                "current_release_sha256":
                    handoff.receipt.predecessor_release.release_sha256,
                "a09_proposal_sha256": handoff.proposal.proposal_sha256,
            })())
        self.assertEqual(
            _generated_grade_digest(authority, handoff), "a" * 64)
        with self.assertRaises(FrozenInstanceError):
            authority.proposal_sha256 = "b" * 64
        replay = _mint_generated_grade_authority(type(
            "Proposal", (), {
                "proposal_sha256": "c" * 64,
                "current_release_sha256": "d" * 64,
                "a09_proposal_sha256": handoff.proposal.proposal_sha256,
            })())
        with self.assertRaises(BilqisError):
            _generated_grade_digest(replay, handoff)

    def test_capability_only_mutation_owner_requires_v2_production_pair(self):
        handoff = self._handoff()
        approval, lease = self._lease_authority(handoff)
        current = self._context(handoff, approval)
        with self.assertRaises(BilqisError) as caught:
            adopt_capability_only_atlas_successor_v2(
                current, AtlasDeltaEnvelopeV2(handoff, None), lease)
        self.assertEqual(
            caught.exception.context["reason"],
            "BAMF_ATLAS_V2_CAPABILITY_OWNER_UNAVAILABLE",
        )

    def test_capability_only_owner_retries_before_verifier_then_publishes_exact_child(self):
        handoff = self._handoff()
        approval, lease = self._lease_authority(handoff)
        pure = self._context(handoff, approval)
        runtime = _PreparedSuccessorRuntime(
            None, pure.run_dir, {"school": {}}, None, None, {}, object(), object(), 0.)
        current = AtlasAdmissionContextV2(
            pure.legacy, pure.run_dir, runtime=runtime, source_authority=object())
        staged_result = AdmissionResult(
            AdmissionStatus.STAGED,
            handoff.proposal.proposal_sha256,
            lease.digest(),
            handoff.receipt.predecessor_release.release_sha256,
            handoff.staged_candidate.successor.release_sha256,
            "V2_CAPABILITY_ONLY_AUTHORITY_VERIFIED",
            "handoff",
        )
        pointer = {
            "generation": 1,
            "manifest_sha256": "f" * 64,
        }
        parent_pointer = {
            "generation": 0,
            "manifest_sha256": "a" * 64,
            "acceptance_sha256": "b" * 64,
        }
        with patch(
                "bilqis_mlx.runtime.atlas_capability_adoption_v2."
                "_accepted_capability_only_retry_state_v2",
                return_value=(None, parent_pointer)) as retry, \
                patch(
                    "bilqis_mlx.runtime.atlas_adoption_v2.advance_atlas_frontier_v2",
                    return_value=staged_result) as verify, \
                patch(
                    "bilqis_mlx.runtime.atlas_adoption_v2."
                    "replay_atlas_delta_scope_handoff_v2",
                    return_value=handoff.staged_candidate) as replay, \
                patch(
                    "bilqis_mlx.runtime.atlas_adoption_v2.verify_current_implementations"
                ) as implementations, \
                patch(
                    "bilqis_mlx.runtime.atlas_capability_adoption_v2."
                    "publish_capability_only_factory_successor",
                    return_value=pointer) as publish:
            result = adopt_capability_only_atlas_successor_v2(
                current, AtlasDeltaEnvelopeV2(handoff, None), lease)

        retry.assert_called_once()
        verify.assert_called_once()
        replay.assert_called_once()
        implementations.assert_called_once()
        publish.assert_called_once_with(
            current, handoff, lease, expected_parent_pointer=parent_pointer)
        self.assertEqual(result.status, AdmissionStatus.ADOPTED)
        self.assertEqual(result.reason, "ADOPTED_CAPABILITY_ONLY")
        self.assertEqual(result.lease_sha256, lease.digest())
        self.assertEqual(result.accepted_generation, 1)
        self.assertEqual(result.accepted_manifest_sha256, "f" * 64)
        self.assertTrue(result.requires_cold_resume)

    def test_capability_only_owner_forwards_generated_grade_authority(self):
        from bilqis_mlx.runtime.generated_grade import (
            _mint_generated_grade_authority,
        )
        handoff = self._handoff()
        approval, lease = self._lease_authority(handoff)
        pure = self._context(handoff, approval)
        runtime = _PreparedSuccessorRuntime(
            None, pure.run_dir, {"school": {}}, None, None, {}, object(), object(), 0.)
        current = AtlasAdmissionContextV2(
            pure.legacy, pure.run_dir, runtime=runtime, source_authority=object())
        staged_result = AdmissionResult(
            AdmissionStatus.STAGED,
            handoff.proposal.proposal_sha256,
            lease.digest(),
            handoff.receipt.predecessor_release.release_sha256,
            handoff.staged_candidate.successor.release_sha256,
            "V2_CAPABILITY_ONLY_AUTHORITY_VERIFIED",
            "handoff",
        )
        parent_pointer = {
            "generation": 0,
            "manifest_sha256": "a" * 64,
            "acceptance_sha256": "b" * 64,
        }
        pointer = {"generation": 1, "manifest_sha256": "f" * 64}
        digest = "a" * 64
        authority = _mint_generated_grade_authority(type(
            "Proposal", (), {
                "proposal_sha256": digest,
                "current_release_sha256":
                    handoff.receipt.predecessor_release.release_sha256,
                "a09_proposal_sha256": handoff.proposal.proposal_sha256,
            })())
        with patch(
                "bilqis_mlx.runtime.atlas_capability_adoption_v2."
                "_accepted_capability_only_retry_state_v2",
                return_value=(None, parent_pointer)), patch(
                    "bilqis_mlx.runtime.atlas_adoption_v2.advance_atlas_frontier_v2",
                    return_value=staged_result), patch(
                    "bilqis_mlx.runtime.atlas_adoption_v2."
                    "replay_atlas_delta_scope_handoff_v2",
                    return_value=handoff.staged_candidate), patch(
                    "bilqis_mlx.runtime.atlas_adoption_v2.verify_current_implementations"
                ), patch(
                    "bilqis_mlx.runtime.atlas_capability_adoption_v2."
                    "publish_capability_only_factory_successor",
                    return_value=pointer) as publish:
            adopt_capability_only_atlas_successor_v2(
                current, AtlasDeltaEnvelopeV2(handoff, None), lease,
                generated_grade_authority=authority)
        publish.assert_called_once_with(
            current, handoff, lease, expected_parent_pointer=parent_pointer,
            generated_grade_authority=authority)

    def test_capability_only_exact_retry_short_circuits_live_verifier_and_publication(self):
        handoff = self._handoff()
        approval, lease = self._lease_authority(handoff)
        pure = self._context(handoff, approval)
        runtime = _PreparedSuccessorRuntime(
            None, pure.run_dir, {"school": {}}, None, None, {}, object(), object(), 0.)
        current = AtlasAdmissionContextV2(
            pure.legacy, pure.run_dir, runtime=runtime, source_authority=object())
        pointer = {"generation": 1, "manifest_sha256": "e" * 64}

        with patch(
                "bilqis_mlx.runtime.atlas_capability_adoption_v2."
                "_accepted_capability_only_retry_state_v2",
                return_value=(pointer, None)), \
                patch(
                    "bilqis_mlx.runtime.atlas_adoption_v2.advance_atlas_frontier_v2"
                ) as verify, \
                patch(
                    "bilqis_mlx.runtime.atlas_capability_adoption_v2."
                    "publish_capability_only_factory_successor") as publish:
            result = adopt_capability_only_atlas_successor_v2(
                current, AtlasDeltaEnvelopeV2(handoff, None), lease)

        verify.assert_not_called()
        publish.assert_not_called()
        self.assertEqual(result.reason, "ADOPTED_CAPABILITY_ONLY")
        self.assertEqual(result.accepted_manifest_sha256, "e" * 64)

    def test_capability_only_concurrent_exact_publish_converges_after_verifier_race(self):
        handoff = self._handoff()
        approval, lease = self._lease_authority(handoff)
        pure = self._context(handoff, approval)
        runtime = _PreparedSuccessorRuntime(
            None, pure.run_dir, {}, None, None, {}, object(), object(), 0.)
        current = AtlasAdmissionContextV2(
            pure.legacy, pure.run_dir, runtime=runtime, source_authority=object())
        pointer = {"generation": 1, "manifest_sha256": "d" * 64}

        def raced_verifier(*_args, **_kwargs):
            from bilqis_mlx.runtime.atlas_admission import _invalid
            _invalid("BAMF_ATLAS_V2_ACCEPTED_RUN_DRIFT")

        with patch(
                "bilqis_mlx.runtime.atlas_capability_adoption_v2."
                "_accepted_capability_only_retry_state_v2",
                return_value=(None, {
                    "generation": 0,
                    "manifest_sha256": "a" * 64,
                    "acceptance_sha256": "b" * 64,
                })) as retry_state, \
                patch(
                    "bilqis_mlx.runtime.atlas_capability_adoption_v2."
                    "accepted_capability_only_retry_v2",
                    return_value=pointer) as retry, \
                patch(
                    "bilqis_mlx.runtime.atlas_adoption_v2.advance_atlas_frontier_v2",
                    side_effect=raced_verifier), \
                patch(
                    "bilqis_mlx.runtime.atlas_capability_adoption_v2."
                    "publish_capability_only_factory_successor") as publish:
            result = adopt_capability_only_atlas_successor_v2(
                current, AtlasDeltaEnvelopeV2(handoff, None), lease)

        retry_state.assert_called_once()
        retry.assert_called_once()
        publish.assert_not_called()
        self.assertEqual(result.reason, "ADOPTED_CAPABILITY_ONLY")
        self.assertEqual(result.accepted_manifest_sha256, "d" * 64)
