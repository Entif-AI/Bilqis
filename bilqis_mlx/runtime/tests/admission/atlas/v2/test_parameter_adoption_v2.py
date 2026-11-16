"""Atlas v2 genuine A02 parameter-adoption tests."""

from contextlib import nullcontext

from bilqis_mlx.runtime.tests.admission.atlas.v2.policy_support import *
from bilqis_mlx.runtime.jit_adoption import _PreparedSuccessorRuntime
from bilqis_mlx.runtime.atlas_parameter_adoption_v2 import (
    _revalidate_parameter_publication,
    publish_native_staged_candidate_v2,
)


class ParameterAdoptionV2Tests(PolicyV2Support):
    def test_parameter_publisher_enters_current_v2_lease_publication_guard(self):
        _capability, semantic_id, handoff, plan, ledger, checkpoint = self._event_handoff()
        approval, lease = self._authority(handoff)
        native = self._a02_staged(semantic_id)
        pure = self._context(handoff, plan, ledger, checkpoint, approval)
        runtime = _PreparedSuccessorRuntime(
            None, pure.run_dir, {}, None, None, {}, object(), object(), 0.)
        legacy = replace(
            pure.legacy, runtime=runtime, native_staged=native,
            source_authority=object())
        current = AtlasAdmissionContextV2(legacy, pure.run_dir)
        pointer = {"generation": 1, "manifest_sha256": "f" * 64}

        with patch(
                "bilqis_mlx.runtime.atlas_admission."
                "_hold_current_atlas_lease_v2_publication",
                return_value=nullcontext()) as lease_guard, patch(
                    "bilqis_mlx.runtime.atlas_parameter_adoption_v2."
                    "_publish_native_staged_candidate_v2_locked",
                    return_value=pointer) as locked:
            actual = publish_native_staged_candidate_v2(
                runtime, handoff.staged_candidate, handoff.proposal, native, lease,
                legacy.source_authority, current=current, checkpoint=checkpoint,
                handoff=handoff)

        self.assertEqual(actual, pointer)
        lease_guard.assert_called_once_with(runtime.run_dir, lease)
        locked.assert_called_once()

    def test_parameter_extension_v2_owner_uses_exact_v2_lease_and_cold_resume(self):
        _capability, semantic_id, handoff, plan, ledger, checkpoint = self._event_handoff()
        approval, lease = self._authority(handoff)
        native = self._a02_staged(semantic_id)
        pure = self._context(handoff, plan, ledger, checkpoint, approval)
        runtime = _PreparedSuccessorRuntime(
            None, pure.run_dir, {}, None, None, {}, object(), object(), 0.)
        legacy = replace(
            pure.legacy, runtime=runtime, native_staged=native,
            source_authority=object())
        current = AtlasAdmissionContextV2(legacy, pure.run_dir)
        staged_result = AdmissionResult(
            AdmissionStatus.STAGED,
            handoff.proposal.proposal_sha256,
            lease.digest(),
            handoff.receipt.predecessor_release.release_sha256,
            handoff.staged_candidate.successor.release_sha256,
            "V2_DELTA_AUTHORITY_VERIFIED",
            "handoff",
        )
        pointer = {"generation": 1, "manifest_sha256": "f" * 64}

        with patch(
                "bilqis_mlx.runtime.atlas_parameter_adoption_v2."
                "accepted_parameter_extension_retry_v2",
                return_value=None) as retry, \
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
                    "bilqis_mlx.runtime.atlas_parameter_adoption_v2."
                    "publish_native_staged_candidate_v2",
                    return_value=pointer) as publish, \
                patch(
                    "bilqis_mlx.runtime.atlas_admission.read_atlas_lease",
                    side_effect=AssertionError("v1 lease read is forbidden")):
            result = adopt_parameter_extension_atlas_successor_v2(
                current, AtlasDeltaEnvelopeV2(handoff, native), lease)

        retry.assert_called_once_with(current, handoff, native, lease)
        verify.assert_called_once_with(current, AtlasDeltaEnvelopeV2(handoff, native), lease)
        replay.assert_called_once_with(current, handoff)
        implementations.assert_called_once()
        self.assertIs(publish.call_args.args[4], lease)
        self.assertEqual(result.status, AdmissionStatus.ADOPTED)
        self.assertEqual(result.reason, "ADOPTED_PARAMETER_EXTENSION_V2")
        self.assertEqual(result.lease_sha256, lease.digest())
        self.assertEqual(result.accepted_generation, 1)
        self.assertEqual(result.accepted_manifest_sha256, "f" * 64)
        self.assertTrue(result.requires_cold_resume)

    def test_parameter_extension_v2_forwards_generated_grade_authority(self):
        from bilqis_mlx.runtime.generated_grade import (
            _mint_generated_grade_authority,
        )
        _capability, semantic_id, handoff, plan, ledger, checkpoint = self._event_handoff()
        approval, lease = self._authority(handoff)
        native = self._a02_staged(semantic_id)
        pure = self._context(handoff, plan, ledger, checkpoint, approval)
        runtime = _PreparedSuccessorRuntime(
            None, pure.run_dir, {}, None, None, {}, object(), object(), 0.)
        legacy = replace(
            pure.legacy, runtime=runtime, native_staged=native,
            source_authority=object())
        current = AtlasAdmissionContextV2(legacy, pure.run_dir)
        staged_result = AdmissionResult(
            AdmissionStatus.STAGED, handoff.proposal.proposal_sha256,
            lease.digest(),
            handoff.receipt.predecessor_release.release_sha256,
            handoff.staged_candidate.successor.release_sha256,
            "V2_DELTA_AUTHORITY_VERIFIED", "handoff")
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
                "bilqis_mlx.runtime.atlas_parameter_adoption_v2."
                "accepted_parameter_extension_retry_v2",
                return_value=None), patch(
                    "bilqis_mlx.runtime.atlas_adoption_v2.advance_atlas_frontier_v2",
                    return_value=staged_result), patch(
                    "bilqis_mlx.runtime.atlas_adoption_v2."
                    "replay_atlas_delta_scope_handoff_v2",
                    return_value=handoff.staged_candidate), patch(
                    "bilqis_mlx.runtime.atlas_adoption_v2.verify_current_implementations"
                ), patch(
                    "bilqis_mlx.runtime.atlas_parameter_adoption_v2."
                    "publish_native_staged_candidate_v2",
                    return_value=pointer) as publish:
            adopt_parameter_extension_atlas_successor_v2(
                current, AtlasDeltaEnvelopeV2(handoff, native), lease,
                generated_grade_authority=authority)
        self.assertEqual(
            publish.call_args.kwargs["generated_grade_authority"],
            authority)

    def test_parameter_extension_v2_exact_retry_does_zero_live_publication(self):
        _capability, semantic_id, handoff, plan, ledger, checkpoint = self._event_handoff()
        approval, lease = self._authority(handoff)
        native = self._a02_staged(semantic_id)
        pure = self._context(handoff, plan, ledger, checkpoint, approval)
        runtime = _PreparedSuccessorRuntime(
            None, pure.run_dir, {}, None, None, {}, object(), object(), 0.)
        legacy = replace(
            pure.legacy, runtime=runtime, native_staged=native,
            source_authority=object())
        current = AtlasAdmissionContextV2(legacy, pure.run_dir)
        pointer = {"generation": 1, "manifest_sha256": "e" * 64}

        with patch(
                "bilqis_mlx.runtime.atlas_parameter_adoption_v2."
                "accepted_parameter_extension_retry_v2",
                return_value=pointer), \
                patch(
                    "bilqis_mlx.runtime.atlas_adoption_v2.advance_atlas_frontier_v2"
                ) as verify, \
                patch(
                    "bilqis_mlx.runtime.atlas_parameter_adoption_v2."
                    "publish_native_staged_candidate_v2"
                ) as publish:
            result = adopt_parameter_extension_atlas_successor_v2(
                current, AtlasDeltaEnvelopeV2(handoff, native), lease)

        verify.assert_not_called()
        publish.assert_not_called()
        self.assertEqual(result.reason, "ADOPTED_PARAMETER_EXTENSION_V2")
        self.assertEqual(result.accepted_manifest_sha256, "e" * 64)

    def test_parameter_extension_v2_concurrent_exact_publish_converges_after_verifier_race(self):
        _capability, semantic_id, handoff, plan, ledger, checkpoint = self._event_handoff()
        approval, lease = self._authority(handoff)
        native = self._a02_staged(semantic_id)
        pure = self._context(handoff, plan, ledger, checkpoint, approval)
        runtime = _PreparedSuccessorRuntime(
            None, pure.run_dir, {}, None, None, {}, object(), object(), 0.)
        legacy = replace(
            pure.legacy, runtime=runtime, native_staged=native,
            source_authority=object())
        current = AtlasAdmissionContextV2(legacy, pure.run_dir)
        pointer = {"generation": 1, "manifest_sha256": "d" * 64}

        def raced_verifier(*_args, **_kwargs):
            from bilqis_mlx.runtime.atlas_admission import _invalid
            _invalid("BAMF_ATLAS_V2_ACCEPTED_RUN_DRIFT")

        with patch(
                "bilqis_mlx.runtime.atlas_parameter_adoption_v2."
                "accepted_parameter_extension_retry_v2",
                side_effect=[None, pointer]) as retry, \
                patch(
                    "bilqis_mlx.runtime.atlas_adoption_v2.advance_atlas_frontier_v2",
                    side_effect=raced_verifier), \
                patch(
                    "bilqis_mlx.runtime.atlas_parameter_adoption_v2."
                    "publish_native_staged_candidate_v2") as publish:
            result = adopt_parameter_extension_atlas_successor_v2(
                current, AtlasDeltaEnvelopeV2(handoff, native), lease)

        self.assertEqual(retry.call_count, 2)
        publish.assert_not_called()
        self.assertEqual(result.reason, "ADOPTED_PARAMETER_EXTENSION_V2")
        self.assertEqual(result.accepted_manifest_sha256, "d" * 64)

    def test_parameter_publication_rechecks_v2_authority_after_parent_reload(self):
        _capability, semantic_id, handoff, plan, ledger, checkpoint = self._event_handoff()
        approval, lease = self._authority(handoff)
        native = self._a02_staged(semantic_id)
        pure = self._context(handoff, plan, ledger, checkpoint, approval)
        source_authority = object()
        runtime = _PreparedSuccessorRuntime(
            None, pure.run_dir, {"school": {}}, None, None, {}, object(), object(), 0.)
        legacy = replace(
            pure.legacy, runtime=runtime, native_staged=native,
            source_authority=source_authority)
        current = AtlasAdmissionContextV2(legacy, pure.run_dir)
        parent = SimpleNamespace(
            retained_state=SimpleNamespace(optimizer_step=checkpoint.optimizer_step))
        parent_manifest = native.candidate.parent_manifest_sha256
        accepted_current = SimpleNamespace(
            release_sha256=handoff.receipt.predecessor_release.release_sha256,
            verify_semantic_catalog=lambda _graph: None,
        )

        with patch(
                "bilqis_mlx.runtime.atlas_admission.read_accepted_atlas_lease_v2",
                return_value=lease) as read_lease, \
                patch(
                    "bilqis_mlx.runtime.atlas_parameter_adoption_v2."
                    "_require_exact_atlas_release") as exact_release, \
                patch(
                    "bilqis_mlx.runtime.atlas_parameter_adoption_v2."
                    "_authenticate_native_staged_candidate",
                    return_value=native.candidate), \
                patch(
                    "bilqis_mlx.runtime.bamf_bundle.load_bamf_generation_authority",
                    return_value=(parent, parent_manifest)), \
                patch(
                    "bilqis_mlx.runtime.atlas_admission."
                    "read_accepted_atlas_factory_release",
                    return_value=accepted_current), \
                patch(
                    "bilqis_mlx.runtime.state._state_from_json",
                    return_value=SimpleNamespace(current_student=checkpoint)), \
                patch(
                    "bilqis_mlx.factory.schedule."
                    "schedule_program_from_executable_release",
                    return_value=object()), \
                patch(
                    "bilqis_mlx.source_adapters.school.live_source_registry",
                    return_value=object()), \
                patch(
                    "bilqis_mlx.factory.live_answers.live_answer_registry",
                    return_value=object()), \
                patch(
                    "bilqis_mlx.runtime.atlas_parameter_adoption_v2."
                    "verify_current_implementations"):
            raced, actual_candidate, actual_parent = _revalidate_parameter_publication(
                runtime,
                handoff.staged_candidate,
                native,
                lease,
                source_authority,
                current=current,
                checkpoint=checkpoint,
                handoff=handoff,
            )

        self.assertIsNone(raced)
        self.assertIs(actual_candidate, native.candidate)
        self.assertIs(actual_parent, parent)
        self.assertEqual(read_lease.call_count, 2)
        self.assertEqual(exact_release.call_count, 2)
