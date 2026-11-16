"""Accepted-run C09 context revalidation stops at material equality."""
from dataclasses import replace

from bilqis_mlx.errors import BilqisError
from bilqis_mlx.runtime.accepted_corrections import (
    AcceptedRuntimeHost, ContextRevalidationFrontier, _reset_accepted_correction_runtime_for_tests,
    register_accepted_target,
)
from bilqis_mlx.runtime.accepted_correction_ledger import (
    append_record, context_invalidation_record,
)
from bilqis_mlx.runtime.accepted_correction_runtime import (
    deliver_accepted_context_invalidation, require_pending_corrections,
)
from bilqis_mlx.runtime._atlas_owner_ingress import _route
from bilqis_mlx.runtime.bamf_bundle import admission
from bilqis_mlx.runtime.bamf_bundle.accepted_runtime import _reset_execution_cache_owner_for_tests
from bilqis_mlx.runtime.bamf_bundle.admission import bind_accepted_execution_cache
from bilqis_mlx.runtime.tests.custody.bamf_bundle.helpers import shape_patch
from bilqis_mlx.runtime.tests.custody.bamf_bundle.authority.accepted_context_revalidation_support import (
    AUTHORITY, AcceptedContextFixture, ArtifactKind, ArtifactNode, ContextOwner,
    DependencyIndex, DependencyKind, DependencyRef, signed_context_result,
)
from bilqis_mlx.runtime.tests.custody.bamf_bundle.authority.correction_runtime.temporal_support import (
    source_owned_temporal_case,
)
from bilqis_mlx.semantics.context_eligibility import C09ContextInvalidation

# Compatibility names retained for the ordering companion while the shared
# fixture moved out of this test module.
_ContextOwner = ContextOwner
_signed_context_result = signed_context_result


class AcceptedContextRevalidationTests(AcceptedContextFixture):
    def test_equal_direct_context_revalidation_releases_and_stops(self):
        _case, owner, host, invalidation, accepted_event_id = self.registered_owner()
        direct = owner.index.node("frame:context-direct")
        descendant = owner.index.node("motif:context-descendant")
        with self.assertRaises(BilqisError):
            require_pending_corrections(owner, direct.artifact_id)
        self.assertIsNone(require_pending_corrections(owner, descendant.artifact_id))

        new_time = DependencyRef(
            DependencyKind.TIME,
            "time:asof:context:" + invalidation.new_context_digest)
        result = signed_context_result(
            direct, invalidation=invalidation,
            accepted_event_id=accepted_event_id, dependencies=(new_time,))
        with shape_patch(AUTHORITY):
            host.record_context_revalidation(ContextRevalidationFrontier((result,)))

        self.assertIsNone(require_pending_corrections(owner, direct.artifact_id))
        self.assertIsNone(require_pending_corrections(owner, descendant.artifact_id))
        self.assertEqual(
            owner.index.node(direct.artifact_id).immediate_dependencies, (new_time,))

        _reset_execution_cache_owner_for_tests()
        _reset_accepted_correction_runtime_for_tests()
        cold_owner = ContextOwner((replace(direct), replace(descendant)))
        with shape_patch(AUTHORITY):
            cold_cache = bind_accepted_execution_cache(self.run)
            register_accepted_target(
                self.run, cold_cache.accepted_manifest_sha256,
                "TEST_CONTEXT", cold_owner)
        self.assertIsNone(require_pending_corrections(cold_owner, direct.artifact_id))
        self.assertEqual(
            cold_owner.index.node(direct.artifact_id).immediate_dependencies,
            (new_time,))

    def test_context_revalidation_rejects_wrong_invalidation_receipt(self):
        _case, owner, host, invalidation, _accepted_event_id = self.registered_owner()
        direct = owner.index.node("frame:context-direct")
        result = signed_context_result(
            direct, invalidation=invalidation, accepted_event_id="9" * 64,
            dependencies=(DependencyRef(
                DependencyKind.TIME,
                "time:asof:context:" + invalidation.new_context_digest),))
        with shape_patch(AUTHORITY), self.assertRaises(BilqisError) as rejected:
            host.record_context_revalidation(ContextRevalidationFrontier((result,)))
        self.assertEqual(
            rejected.exception.context["reason"],
            "BAMF_C09_CONTEXT_REVALIDATION_INVALIDATION_MISSING")

    def test_revalidation_for_late_artifact_stays_deferred_until_materialized(self):
        case = source_owned_temporal_case()
        owner = ContextOwner(())
        cache = self.publish()
        with shape_patch(AUTHORITY):
            register_accepted_target(
                self.run, cache.accepted_manifest_sha256,
                "TEST_CONTEXT_LATE", owner)
            host = AcceptedRuntimeHost(self.run)
        invalidation = C09ContextInvalidation(
            old_context_digest=case.previous.digest,
            new_context_digest="e" * 64,
            reason_codes=("BAMF_CONTEXT_APPROVED_VIEW_CHANGED",),
            principal_id=case.task.principal_id,
            tenant_id=case.task.tenant_id,
            scope=case.task.scope,
            semantic_release=case.task.semantic_release,
            policy_epoch=case.policy.policy_epoch,
            rights_epoch=case.frontier.rights_epoch,
            correction_generation=case.frontier.correction_generation,
            causal_prefix_end=case.task.causal_prefix_end,
            invalidated_handles=tuple(sorted({
                handle
                for frame in case.previous.eligible.frames
                for handle in (frame.frame_handle, *frame.member_handles)
            })),
        )
        with shape_patch(AUTHORITY):
            record = context_invalidation_record(
                cache.accepted_manifest_sha256, invalidation)
            append_record(self.run, cache.accepted_manifest_sha256, record)
            deliver_accepted_context_invalidation(
                self.run, cache.accepted_manifest_sha256,
                record["event_id"], invalidation)
        old_time = DependencyRef(
            DependencyKind.TIME, "time:asof:context:" + case.previous.digest)
        new_time = DependencyRef(
            DependencyKind.TIME, "time:asof:context:" + invalidation.new_context_digest)
        late = ArtifactNode(
            "frame:late-context", ArtifactKind.PACKED_FRAME,
            "a" * 64, True, (old_time,), impact=3, exigency=3)
        result = signed_context_result(
            late, invalidation=invalidation,
            accepted_event_id=record["event_id"], dependencies=(new_time,))
        with shape_patch(AUTHORITY):
            evidence_id = host.record_context_revalidation(
                ContextRevalidationFrontier((result,)))
        owner._index = DependencyIndex.build((late,))
        self.assertIsNone(require_pending_corrections(owner, late.artifact_id))
        self.assertEqual(
            owner.index.node(late.artifact_id).immediate_dependencies,
            (new_time,),
        )
