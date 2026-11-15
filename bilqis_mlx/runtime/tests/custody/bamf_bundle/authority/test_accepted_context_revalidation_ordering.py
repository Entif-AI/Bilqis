"""Ordering and replay tests for accepted C09 context revalidation."""
from __future__ import annotations

from dataclasses import replace
import os
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest
from unittest.mock import patch

import bilqis_mlx.runtime.mlx_checkpoint as mlx_checkpoint
from bilqis_mlx.errors import BilqisError
from bilqis_mlx.runtime.accepted_corrections import (
    AcceptedRuntimeHost, ContextRevalidationFrontier, _reset_accepted_correction_runtime_for_tests,
    register_accepted_target,
)
from bilqis_mlx.runtime.accepted_correction_ledger import (
    append_record, context_invalidation_record, read_records,
)
from bilqis_mlx.runtime.accepted_correction_runtime import (
    deliver_accepted_context_invalidation, require_pending_corrections,
)
from bilqis_mlx.runtime._atlas_owner_ingress import _route
from bilqis_mlx.runtime.bamf_bundle import admission
from bilqis_mlx.runtime.bamf_bundle.accepted_runtime import _reset_execution_cache_owner_for_tests
from bilqis_mlx.runtime.bamf_bundle.admission import (
    bind_accepted_execution_cache,
)
from bilqis_mlx.runtime.tests.custody.bamf_bundle.helpers import (
    candidate, parent_state, provision_source_authority_registry,
    publish_candidate, shape_patch, with_source_authority_registry,
)
from bilqis_mlx.runtime.tests.custody.bamf_bundle.authority.correction_runtime.temporal_support import (
    source_owned_temporal_case,
)
from bilqis_mlx.runtime.tests.custody.bamf_bundle.authority.test_accepted_context_revalidation import (
    _ContextOwner, _signed_context_result,
)
from bilqis_mlx.runtime.tests.test_atlas_revalidation import AUTHORITY
from bilqis_mlx.semantics.cognitive_dependencies import (
    ArtifactKind, ArtifactNode, DependencyKind, DependencyRef,
)
from bilqis_mlx.semantics.context_eligibility import C09ContextInvalidation


def _event(case, old_digest: str, new_digest: str) -> C09ContextInvalidation:
    return C09ContextInvalidation(
        old_context_digest=old_digest,
        new_context_digest=new_digest,
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


class AcceptedContextOrderingTests(unittest.TestCase):
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

    def _publish(self):
        provision_source_authority_registry(self.run, AUTHORITY)
        source = with_source_authority_registry(candidate(parent_state()), AUTHORITY)
        with shape_patch(AUTHORITY), patch.object(mlx_checkpoint, "assert_headroom"):
            publish_candidate(self.run, source)
            return bind_accepted_execution_cache(self.run)

    def _persist_invalidation(self, cache, event):
        with shape_patch(AUTHORITY):
            record = context_invalidation_record(
                cache.accepted_manifest_sha256, event)
            append_record(self.run, cache.accepted_manifest_sha256, record)
            deliver_accepted_context_invalidation(
                self.run, cache.accepted_manifest_sha256,
                record["event_id"], event)
        return record["event_id"]

    def test_overlapping_contexts_and_premature_evidence_replay_in_order(self):
        case = source_owned_temporal_case()
        x_digest, y_digest, z_digest = case.previous.digest, "e" * 64, "f" * 64
        source_ref = DependencyRef(DependencyKind.SOURCE, "source:ordering")
        x_time = DependencyRef(
            DependencyKind.TIME, "time:asof:context:" + x_digest)
        y_time = DependencyRef(
            DependencyKind.TIME, "time:asof:context:" + y_digest)
        z_time = DependencyRef(
            DependencyKind.TIME, "time:asof:context:" + z_digest)
        direct = ArtifactNode(
            "frame:ordering", ArtifactKind.PACKED_FRAME, "a" * 64, True,
            tuple(sorted((source_ref, x_time))), impact=3, exigency=3)
        owner = _ContextOwner((direct,))
        cache = self._publish()
        with shape_patch(AUTHORITY):
            register_accepted_target(
                self.run, cache.accepted_manifest_sha256, "ORDERING", owner
            )
            host = AcceptedRuntimeHost(self.run)

        event_a = _event(case, x_digest, y_digest)
        event_b = _event(case, y_digest, z_digest)
        receipt_a = self._persist_invalidation(cache, event_a)
        receipt_b = self._persist_invalidation(cache, event_b)

        result_b = _signed_context_result(
            direct, invalidation=event_b, accepted_event_id=receipt_b,
            dependencies=tuple(sorted((source_ref, z_time))))
        with shape_patch(AUTHORITY):
            host.record_context_revalidation(
                ContextRevalidationFrontier((result_b,)))
        with self.assertRaises(BilqisError):
            require_pending_corrections(owner, direct.artifact_id)

        result_a = _signed_context_result(
            direct, invalidation=event_a, accepted_event_id=receipt_a,
            dependencies=tuple(sorted((source_ref, y_time))))
        with shape_patch(AUTHORITY):
            host.record_context_revalidation(
                ContextRevalidationFrontier((result_a,)))

        self.assertIsNone(
            require_pending_corrections(owner, direct.artifact_id))
        self.assertEqual(
            owner.index.node(direct.artifact_id).immediate_dependencies,
            tuple(sorted((source_ref, z_time))),
        )

        _reset_execution_cache_owner_for_tests()
        _reset_accepted_correction_runtime_for_tests()
        cold_owner = _ContextOwner((direct,))
        with shape_patch(AUTHORITY):
            cold_cache = bind_accepted_execution_cache(self.run)
            register_accepted_target(
                self.run, cold_cache.accepted_manifest_sha256,
                "ORDERING", cold_owner
            )
        self.assertIsNone(
            require_pending_corrections(cold_owner, direct.artifact_id))
        self.assertEqual(
            cold_owner.index.node(direct.artifact_id).immediate_dependencies,
            tuple(sorted((source_ref, z_time))),
        )

    def test_same_context_lower_priority_evidence_defers_until_priority_frontier(self):
        case = source_owned_temporal_case()
        old_digest, new_digest = case.previous.digest, "e" * 64
        old_time = DependencyRef(
            DependencyKind.TIME, "time:asof:context:" + old_digest)
        new_time = DependencyRef(
            DependencyKind.TIME, "time:asof:context:" + new_digest)
        high = ArtifactNode(
            "frame:priority-high", ArtifactKind.PACKED_FRAME, "a" * 64, True,
            (old_time,), impact=3, exigency=3)
        low = ArtifactNode(
            "frame:priority-low", ArtifactKind.PACKED_FRAME, "b" * 64, True,
            (old_time,), impact=1, exigency=1)
        owner = _ContextOwner((high, low))
        cache = self._publish()
        with shape_patch(AUTHORITY):
            register_accepted_target(
                self.run, cache.accepted_manifest_sha256, "PRIORITY", owner
            )
            host = AcceptedRuntimeHost(self.run)
        invalidation = _event(case, old_digest, new_digest)
        receipt = self._persist_invalidation(cache, invalidation)

        low_result = _signed_context_result(
            low, invalidation=invalidation, accepted_event_id=receipt,
            dependencies=(new_time,))
        with shape_patch(AUTHORITY):
            low_record = host.record_context_revalidation(
                ContextRevalidationFrontier((low_result,)))
        with self.assertRaises(BilqisError):
            require_pending_corrections(owner, low.artifact_id)

        high_result = _signed_context_result(
            high, invalidation=invalidation, accepted_event_id=receipt,
            dependencies=(new_time,))
        with shape_patch(AUTHORITY):
            host.record_context_revalidation(
                ContextRevalidationFrontier((high_result,)))
        self.assertIsNone(require_pending_corrections(owner, high.artifact_id))
        self.assertIsNone(require_pending_corrections(owner, low.artifact_id))

        _reset_execution_cache_owner_for_tests()
        _reset_accepted_correction_runtime_for_tests()
        cold_owner = _ContextOwner((high, low))
        with shape_patch(AUTHORITY):
            cold_cache = bind_accepted_execution_cache(self.run)
            register_accepted_target(
                self.run, cold_cache.accepted_manifest_sha256,
                "PRIORITY", cold_owner
            )
        self.assertIsNone(
            require_pending_corrections(cold_owner, high.artifact_id))
        self.assertIsNone(
            require_pending_corrections(cold_owner, low.artifact_id))

    def test_equal_context_revalidation_keeps_real_packed_frame_readable(self):
        case = source_owned_temporal_case()
        owner = case.owner()
        cache = self._publish()
        with shape_patch(AUTHORITY):
            register_accepted_target(
                self.run, cache.accepted_manifest_sha256,
                "PACKED_FRAME", owner
            )
            host = AcceptedRuntimeHost(self.run)
        invalidation = _event(case, case.previous.digest, "e" * 64)
        receipt = self._persist_invalidation(cache, invalidation)
        held = owner.index.nodes[0]
        old_time = DependencyRef(
            DependencyKind.TIME,
            "time:asof:context:" + invalidation.old_context_digest)
        new_time = DependencyRef(
            DependencyKind.TIME,
            "time:asof:context:" + invalidation.new_context_digest)
        dependencies = tuple(sorted(
            (set(held.immediate_dependencies) - {old_time}) | {new_time}))
        result = _signed_context_result(
            held, invalidation=invalidation, accepted_event_id=receipt,
            dependencies=dependencies)
        with shape_patch(AUTHORITY):
            host.record_context_revalidation(
                ContextRevalidationFrontier((result,)))
        self.assertTrue(owner.require_row(case.row))

    def test_expired_real_packed_frame_reports_ineligible_not_content_drift(self):
        case = source_owned_temporal_case()
        owner = case.owner()
        cache = self._publish()
        with shape_patch(AUTHORITY):
            register_accepted_target(
                self.run, cache.accepted_manifest_sha256,
                "PACKED_FRAME", owner
            )
            host = AcceptedRuntimeHost(self.run)
            transition = host.record_context_transition(
                case.previous, case.contexts)
        invalidation = transition.invalidations[0]
        record = next(
            item for item in read_records(
                self.run, cache.accepted_manifest_sha256)
            if item["event"] == "BAMF_C09_CONTEXT_INVALIDATION")
        held = owner.index.nodes[0]
        old_time = DependencyRef(
            DependencyKind.TIME,
            "time:asof:context:" + invalidation.old_context_digest)
        dependencies = tuple(
            ref for ref in held.immediate_dependencies if ref != old_time)
        result = _signed_context_result(
            held, invalidation=invalidation,
            accepted_event_id=record["event_id"],
            dependencies=dependencies, eligible=False)
        with shape_patch(AUTHORITY):
            host.record_context_revalidation(
                ContextRevalidationFrontier((result,)))
        with self.assertRaises(BilqisError) as caught:
            owner.require_row(case.row)
        self.assertEqual(
            caught.exception.context["reason"], "BAMF_C09_ARTIFACT_HELD")


if __name__ == "__main__":
    unittest.main()
