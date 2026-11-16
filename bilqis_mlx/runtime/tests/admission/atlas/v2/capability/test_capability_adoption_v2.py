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
