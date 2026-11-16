"""Changed or non-applicable C09 context evidence stays replay-safe."""
from dataclasses import replace

from bilqis_mlx.errors import BilqisError
from bilqis_mlx.runtime.accepted_corrections import (
    AcceptedRuntimeHost, ContextRevalidationFrontier, _reset_accepted_correction_runtime_for_tests,
    register_accepted_target,
)
from bilqis_mlx.runtime.accepted_correction_ledger import read_records
from bilqis_mlx.runtime.accepted_correction_runtime import require_pending_corrections
from bilqis_mlx.runtime._atlas_owner_ingress import _route
from bilqis_mlx.runtime.bamf_bundle import admission
from bilqis_mlx.runtime.bamf_bundle.accepted_runtime import _reset_execution_cache_owner_for_tests
from bilqis_mlx.runtime.bamf_bundle.admission import bind_accepted_execution_cache
from bilqis_mlx.runtime.tests.custody.bamf_bundle.helpers import shape_patch
from bilqis_mlx.runtime.tests.custody.bamf_bundle.authority.accepted_context_revalidation_support import (
    AUTHORITY, AcceptedContextFixture, ArtifactKind, ArtifactNode, ContextOwner,
    DependencyKind, DependencyRef, source_owned_temporal_case,
    signed_context_result,
)


class AcceptedContextChangeTests(AcceptedContextFixture):
    def test_changed_content_stays_held_until_real_rematerialization(self):
        _case, owner, host, invalidation, accepted_event_id = self.registered_owner()
        direct = owner.index.node("frame:context-direct")
        new_time = DependencyRef(
            DependencyKind.TIME,
            "time:asof:context:" + invalidation.new_context_digest)
        changed = signed_context_result(
            direct, invalidation=invalidation,
            accepted_event_id=accepted_event_id,
            dependencies=(new_time,), digest="d" * 64)
        with shape_patch(AUTHORITY):
            host.record_context_revalidation(ContextRevalidationFrontier((changed,)))
        for artifact_id in (direct.artifact_id, "motif:context-descendant"):
            with self.assertRaises(BilqisError) as held:
                require_pending_corrections(owner, artifact_id)
            self.assertEqual(held.exception.context["reason"], "BAMF_C09_ARTIFACT_HELD")

        replacement_direct = replace(
            direct, content_digest="d" * 64, immediate_dependencies=(new_time,))
        replacement_descendant = owner.index.node("motif:context-descendant")
        _reset_execution_cache_owner_for_tests()
        _reset_accepted_correction_runtime_for_tests()
        replacement = ContextOwner((replacement_direct, replacement_descendant))
        with shape_patch(AUTHORITY):
            cache = bind_accepted_execution_cache(self.run)
            register_accepted_target(
                self.run, cache.accepted_manifest_sha256, "TEST_CONTEXT", replacement)
        self.assertIsNone(
            require_pending_corrections(replacement, replacement_direct.artifact_id))

    def test_non_applicable_evidence_is_durable_but_cannot_poison_replay(self):
        _case, owner, host, invalidation, accepted_event_id = self.registered_owner()
        descendant = owner.index.node("motif:context-descendant")
        ignored = signed_context_result(
            descendant, invalidation=invalidation,
            accepted_event_id=accepted_event_id)
        with shape_patch(AUTHORITY):
            cache = bind_accepted_execution_cache(self.run)
        before = len(read_records(self.run, cache.accepted_manifest_sha256))
        with shape_patch(AUTHORITY):
            host.record_context_revalidation(ContextRevalidationFrontier((ignored,)))
        self.assertEqual(
            len(read_records(self.run, cache.accepted_manifest_sha256)), before + 1)

        direct = owner.index.node("frame:context-direct")
        _reset_execution_cache_owner_for_tests()
        _reset_accepted_correction_runtime_for_tests()
        cold_owner = ContextOwner((replace(direct), replace(descendant)))
        with shape_patch(AUTHORITY):
            cold_cache = bind_accepted_execution_cache(self.run)
            register_accepted_target(
                self.run, cold_cache.accepted_manifest_sha256, "TEST_CONTEXT", cold_owner)
        with self.assertRaises(BilqisError) as held:
            require_pending_corrections(cold_owner, direct.artifact_id)
        self.assertEqual(held.exception.context["reason"], "BAMF_C09_ARTIFACT_HELD")

    def test_expired_content_stays_held_and_propagates(self):
        case = source_owned_temporal_case()
        source_ref = DependencyRef(DependencyKind.SOURCE, "source:expiry-direct")
        direct = ArtifactNode(
            "frame:expiry-direct", ArtifactKind.PACKED_FRAME, "a" * 64, True,
            tuple(sorted((source_ref, DependencyRef(
                DependencyKind.TIME,
                "time:asof:context:" + case.previous.digest)))),
            impact=3, exigency=3)
        child = ArtifactNode(
            "motif:expiry-child", ArtifactKind.MOTIF, "b" * 64, True,
            (direct.reference,), impact=2, exigency=2)
        owner = ContextOwner((direct, child))
        cache = self.publish()
        with shape_patch(AUTHORITY):
            register_accepted_target(
                self.run, cache.accepted_manifest_sha256, "TEST_EXPIRY", owner)
            host = AcceptedRuntimeHost(self.run)
            transition = host.record_context_transition(case.previous, case.contexts)
        invalidation = transition.invalidations[0]
        accepted_event_id = read_records(
            self.run, cache.accepted_manifest_sha256)[-1]["event_id"]
        expired = signed_context_result(
            direct, invalidation=invalidation,
            accepted_event_id=accepted_event_id,
            dependencies=(source_ref,), eligible=False)
        with shape_patch(AUTHORITY):
            host.record_context_revalidation(ContextRevalidationFrontier((expired,)))
        self.assertTrue(owner.index.node(direct.artifact_id).eligible)
        for artifact_id in (direct.artifact_id, child.artifact_id):
            with self.assertRaises(BilqisError) as held:
                require_pending_corrections(owner, artifact_id)
            self.assertEqual(held.exception.context["reason"], "BAMF_C09_ARTIFACT_HELD")
