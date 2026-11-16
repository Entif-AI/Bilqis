"""C09 capability-support provenance and accepted-lineage tests."""
from __future__ import annotations

import json
from dataclasses import replace
from unittest.mock import patch

import bilqis_mlx.runtime.mlx_checkpoint as mlx_checkpoint
from bilqis_mlx.errors import BilqisError
from bilqis_mlx.runtime.atlas_capability_support_owner import CapabilitySupportArtifactOwner
from bilqis_mlx.runtime.atlas_training_authority import extend_training_dependencies
from bilqis_mlx.runtime.accepted_corrections import (
    AcceptedRuntimeHost, ContextRevalidationFrontier, _reset_accepted_correction_runtime_for_tests,
    record_accepted_correction,
)
from bilqis_mlx.runtime.accepted_correction_runtime import (
    deliver_accepted_context_invalidation,
)
from bilqis_mlx.runtime.accepted_correction_ledger import (
    CONTEXT_INVALIDATION_EVENT, CORRECTION_EVENT,
    append_record, context_invalidation_record, read_records,
)
from bilqis_mlx.runtime.capability_support_loading import accepted_support_census
from bilqis_mlx.runtime.atlas_revalidation import (
    SourceAuthorityKey, SourceAuthorityRegistry, SourceAuthorityScope,
)
from bilqis_mlx.runtime._atlas_owner_ingress import apply_capability_support_correction
from bilqis_mlx.runtime.context_revalidation import ContextStateTransition
from bilqis_mlx.runtime.atlas_requalification_contracts import (
    RequalificationStatus,
)
from bilqis_mlx.runtime.bamf_bundle.admission import (
    accept_and_publish, derive_successor_bundle, load_accepted_generation,
)
from bilqis_mlx.runtime.bamf_bundle import admission
from bilqis_mlx.runtime.bamf_bundle.accepted_runtime import _reset_execution_cache_owner_for_tests
from bilqis_mlx.runtime.tests.custody.bamf_bundle.helpers import (
    retention_decision, shape_patch,
)
from bilqis_mlx.runtime.tests.test_atlas_revalidation import (
    AUTHORITY, _SOURCE_OWNER, _TEST_PUBLIC, _event, _ref,
)
from bilqis_mlx.semantics.cognitive_dependencies import (
    DependencyIndex, DependencyKind, DependencyRef,
)
from bilqis_mlx.semantics.context_eligibility import C09ContextInvalidation

from .capability_support_owner_support import (
    CapabilitySupportOwnerFixture, GENERATION, IMMEDIATE_DEPENDENCIES,
    SOURCE_ID, SOURCE_ROW, TARGET, source_qualified_state, training_authority,
)
from . import capability_support_owner_support as support_fixture
from bilqis_mlx.runtime.tests.custody.bamf_bundle.authority.test_accepted_context_revalidation import (
    _signed_context_result,
)
from bilqis_mlx.runtime.tests.custody.bamf_bundle.authority.correction_runtime.temporal_support import (
    source_owned_temporal_case,
)


class CapabilitySupportOwnerTests(CapabilitySupportOwnerFixture):
    def test_b13_acceptance_persists_exact_source_anchor_and_materializes_owner(self):
        published, authority = self.publish_support(authority_registry=AUTHORITY)
        acceptance_path = (
            self.run / "bamf-acceptance" / f"{published['manifest_sha256']}.json")
        record = json.loads(acceptance_path.read_text())
        self.assertEqual(record["source_anchors"][0][0], TARGET)
        self.assertEqual(record["source_anchors"][0][1], SOURCE_ROW)
        self.assertEqual(record["source_anchors"][0][2], authority.source_row_sha256)
        self.assertEqual(record["source_anchors"][0][8], authority.digest)
        self.assertEqual(
            tuple(map(tuple, record["source_anchors"][0][9])),
            tuple((ref.kind.value, ref.key)
                  for ref in authority.immediate_dependencies))

        owner = self.load_support(AUTHORITY)
        self.assertEqual(owner.support.source_anchor_ids, (SOURCE_ROW,))
        self.assertEqual(
            owner.support.retained_generation_sha256,
            published["manifest_sha256"])
        self.assertIn(
            DependencyRef(DependencyKind.SOURCE, SOURCE_ROW),
            owner.current_node.immediate_dependencies)
        self.assertIn(
            DependencyRef(
                DependencyKind.SOURCE,
                "source-proof:" + authority.digest,
            ),
            owner.current_node.immediate_dependencies)
        self.assertIn(
            DependencyRef(
                DependencyKind.RELEASE,
                "source-generation:" + GENERATION,
            ),
            owner.current_node.immediate_dependencies)
        self.assertIn(
            DependencyRef(
                DependencyKind.SOURCE,
                "training-batch:" + authority.training_batch_sha256,
            ),
            owner.current_node.immediate_dependencies)
        for dependency in IMMEDIATE_DEPENDENCIES:
            self.assertIn(dependency, owner.current_node.immediate_dependencies)
        self.assertEqual(
            self.load_support(AUTHORITY).support,
            owner.support)
        with self.assertRaises(BilqisError):
            CapabilitySupportArtifactOwner()

    def test_operator_correction_holds_lossless_learned_support(self):
        authority = SourceAuthorityRegistry((SourceAuthorityKey(
            _SOURCE_OWNER,
            _TEST_PUBLIC,
            (SourceAuthorityScope(DependencyKind.OPERATOR, "operator:"),),
        ),))
        self.publish_support(authority_registry=authority)
        owner = self.load_support(authority)
        dependency = next(
            ref for ref in owner.current_node.immediate_dependencies
            if ref.kind is DependencyKind.OPERATOR)
        with shape_patch(authority):
            AcceptedRuntimeHost(self.run).record_correction(_event(dependency))
        with self.assertRaises(BilqisError) as caught:
            owner.require(TARGET)
        self.assertEqual(
            caught.exception.context["reason"], "BAMF_C09_ARTIFACT_HELD")

    def test_concrete_source_correction_holds_learned_support_across_row_identity(self):
        authority = SourceAuthorityRegistry((SourceAuthorityKey(
            _SOURCE_OWNER,
            _TEST_PUBLIC,
            (SourceAuthorityScope(DependencyKind.SOURCE, SOURCE_ID),),
        ),))
        self.publish_support(authority_registry=authority)
        owner = self.load_support(authority)
        self.assertIn(
            DependencyRef(DependencyKind.SOURCE, SOURCE_ID),
            owner.current_node.immediate_dependencies,
        )
        self.assertNotEqual(SOURCE_ID, SOURCE_ROW)
        with shape_patch(authority):
            AcceptedRuntimeHost(self.run).record_correction(_event(DependencyRef(DependencyKind.SOURCE, SOURCE_ID)))
        with self.assertRaises(BilqisError) as caught:
            owner.require(TARGET)
        self.assertEqual(
            caught.exception.context["reason"], "BAMF_C09_ARTIFACT_HELD")

    def test_execution_observed_source_dependency_reaches_learned_support(self):
        motif_source = DependencyRef(
            DependencyKind.SOURCE, "source:retained-motif-independent")
        authority = extend_training_dependencies(
            training_authority(), (motif_source,))
        registry = SourceAuthorityRegistry((SourceAuthorityKey(
            _SOURCE_OWNER,
            _TEST_PUBLIC,
            (SourceAuthorityScope(
                DependencyKind.SOURCE, "source:retained-motif-independent"),),
        ),))
        self.publish_support(authority=authority, authority_registry=registry)
        owner = self.load_support(registry)
        self.assertIn(motif_source, owner.current_node.immediate_dependencies)
        with shape_patch(registry):
            AcceptedRuntimeHost(self.run).record_correction(_event(motif_source))
        with self.assertRaises(BilqisError) as caught:
            owner.require(TARGET)
        self.assertEqual(
            caught.exception.context["reason"], "BAMF_C09_ARTIFACT_HELD")

    def test_changed_context_revalidation_requires_capability_requalification(self):
        self.publish_support(authority_registry=AUTHORITY)
        owner = self.load_support(AUTHORITY)
        prior = owner.current_node
        updated = replace(prior, content_digest="d" * 64)
        transition = ContextStateTransition(
            artifact_id=prior.artifact_id,
            previous_content_digest=prior.content_digest,
            new_content_digest=updated.content_digest,
            previous_eligible=prior.eligible,
            new_eligible=updated.eligible,
            previous_dependencies=prior.immediate_dependencies,
            new_dependencies=updated.immediate_dependencies,
            source_receipt_sha256="c" * 64,
            context_event_id="context-event:fixture",
            context_invalidation_receipt_sha256="e" * 64,
            source_owner=_SOURCE_OWNER,
            source_signature_hex="0" * 128,
            changed=True,
        )
        owner._install_context_revalidation(
            DependencyIndex.build((updated,)), transition)
        self.assertIs(
            owner.support.status,
            RequalificationStatus.REQUALIFICATION_REQUIRED)
        self.assertEqual(len(owner.ledger.pending_source_tasks), 1)
        self.assertEqual(owner.ledger.pending_c10_intents, ())
        task = owner.ledger.pending_source_tasks[0]
        self.assertIsNone(task.correction_event_id)
        self.assertEqual(task.context_event_id, transition.context_event_id)
        self.assertEqual(task.reason_code, "CONTEXT_SUPPORT_REQUALIFICATION")
        with self.assertRaises(BilqisError) as caught:
            owner.require(TARGET)
        self.assertEqual(
            caught.exception.context["reason"],
            "BAMF_C09_CAPABILITY_SUPPORT_REQUALIFICATION_REQUIRED")

    def test_context_requalification_survives_cold_accepted_replay(self):
        case = source_owned_temporal_case()
        context_dependency = DependencyRef(
            DependencyKind.TIME,
            "time:asof:context:" + case.previous.digest)
        dependencies = tuple(sorted((
            *(ref for ref in IMMEDIATE_DEPENDENCIES
              if ref.kind is not DependencyKind.TIME),
            context_dependency,
        )))
        with patch.object(
            support_fixture, "immediate_dependencies",
            return_value=dependencies,
        ):
            published, _authority = self.publish_support(authority_registry=AUTHORITY)
        owner = self.load_support(AUTHORITY)
        with self._shape_patch():
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
        with self._shape_patch():
            record = context_invalidation_record(
                published["manifest_sha256"], invalidation)
            append_record(
                self.run, published["manifest_sha256"], record)
            deliver_accepted_context_invalidation(
                self.run, published["manifest_sha256"],
                record["event_id"], invalidation)
        prior = owner.current_node
        new_time = DependencyRef(
            DependencyKind.TIME,
            "time:asof:context:" + invalidation.new_context_digest)
        result = _signed_context_result(
            prior,
            invalidation=invalidation,
            accepted_event_id=record["event_id"],
            dependencies=tuple(sorted((
                *(ref for ref in prior.immediate_dependencies
                  if ref != context_dependency),
                new_time,
            ))),
            digest="d" * 64,
        )
        with self._shape_patch():
            host.record_context_revalidation(
                ContextRevalidationFrontier((result,)))
        self.assertIs(
            owner.support.status,
            RequalificationStatus.REQUALIFICATION_REQUIRED)

        _reset_execution_cache_owner_for_tests()
        _reset_accepted_correction_runtime_for_tests()
        cold_owner = self.load_support(AUTHORITY)
        self.assertIs(
            cold_owner.support.status,
            RequalificationStatus.REQUALIFICATION_REQUIRED)
        self.assertEqual(len(cold_owner.ledger.pending_source_tasks), 1)
        self.assertEqual(cold_owner.ledger.pending_c10_intents, ())
        self.assertEqual(
            cold_owner.ledger.pending_source_tasks[0].context_event_id,
            invalidation.event_id)
        with self.assertRaises(BilqisError):
            cold_owner.require(TARGET)
        records = read_records(self.run, published["manifest_sha256"])
        self.assertIn(CONTEXT_INVALIDATION_EVENT, {
            item["event"] for item in records})
        self.assertNotIn(CORRECTION_EVENT, {
            item["event"] for item in records})

    def test_retained_capability_provenance_survives_unrelated_successor_acceptance(self):
        first, _authority_a = self.publish_support(authority_registry=AUTHORITY)
        first_manifest = first["manifest_sha256"]
        with self._shape_patch():
            accepted_parent = load_accepted_generation(self.run)
        capability_b = "capability:unrelated-b"
        source_b = "source:capability-support:row-b"
        parent_state_b, transaction_b, retained_b, _authority_b = source_qualified_state(
            accepted_parent.retained_state,
            extents=accepted_parent.extents,
            spec=accepted_parent.topology,
            capability=capability_b,
            source_row=source_b,
            source_family="source-family:capability-support-b",
            episode="episode:capability-support-b",
            generation_binding="6" * 64,
        )
        successor = derive_successor_bundle(
            accepted_parent,
            retained_b,
            parent_manifest_sha256=first_manifest,
            delivery_events=({"event": "FIXTURE_SUCCESSOR_B"},),
        )
        decision = retention_decision(parent=parent_state_b, retained=retained_b)
        with self._shape_patch(), patch.object(mlx_checkpoint, "assert_headroom"):
            second = accept_and_publish(
                self.run, successor, retained_b, decision=decision,
                feature_sha256=successor.extents.factor_map_digest,
                training_authorities=transaction_b.training_authorities,
            )

        with self._shape_patch():
            ledger, _nodes = accepted_support_census(
                self.run, second["manifest_sha256"])
        self.assertEqual(
            tuple(item.capability_id for item in ledger.capabilities),
            (TARGET, capability_b),
        )
        inherited = self.load_support(AUTHORITY)
        self.assertEqual(inherited.support.source_anchor_ids, (SOURCE_ROW,))
        self.assertEqual(
            inherited.support.retained_generation_sha256,
            first_manifest,
        )
        correction = _event(_ref(DependencyKind.SOURCE, SOURCE_ROW))
        with self._shape_patch():
            AcceptedRuntimeHost(self.run).record_correction(correction)
        with self.assertRaises(BilqisError):
            inherited.require(TARGET)



if __name__ == "__main__":
    import unittest
    unittest.main()
