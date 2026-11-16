"""Accepted-run production ingress for post-remediation stale replay faults."""
from pathlib import Path
from dataclasses import replace
from tempfile import TemporaryDirectory
from unittest.mock import patch
import os
import unittest

import bilqis_mlx.runtime.mlx_checkpoint as mlx_checkpoint
from bilqis_mlx.errors import BilqisError
from bilqis_mlx.runtime.accepted_corrections import (
    AcceptedRuntimeHost,
    _reset_accepted_correction_runtime_for_tests, record_accepted_correction, record_accepted_derived_claim,
    record_accepted_remediation, record_accepted_revalidation,
    register_solve_context,
)
from bilqis_mlx.runtime.akasha_outbox import pending_events
from bilqis_mlx.runtime.atlas_capability_support_owner import (
    load_capability_support_owner,
)
from bilqis_mlx.runtime.bamf_bundle.admission import (
    accept_and_publish,
    bind_accepted_execution_cache, derive_successor_bundle, load_accepted_generation,
)
from bilqis_mlx.runtime.cognitive_solver import QualifiedComposition, SolveContext
from bilqis_mlx.runtime.tests.capability.factory.solver_helpers import _fixture
from bilqis_mlx.runtime.tests.custody.bamf_bundle.helpers import (
    candidate, parent_state, provision_source_authority_registry, publish_candidate,
    publish_genesis, retention_decision, shape_patch, with_source_authority_registry,
)
from bilqis_mlx.runtime.tests.correction.capability_support_owner_support import (
    SOURCE_ROW, TARGET, source_qualified_state,
)
from bilqis_mlx.runtime.tests.test_atlas_revalidation import (
    AUTHORITY, _event, _result,
)
from bilqis_mlx.runtime.atlas_stale_replay import (
    DerivedClaim, RemediationReceipt, RemediationStatus,
)
from bilqis_mlx.semantics.cognitive_dependencies import DependencyKind, DependencyRef
from bilqis_mlx.semantics.domains import contract_digest


class AcceptedStaleReplayRuntimeTests(unittest.TestCase):
    def setUp(self):
        self.temporary = TemporaryDirectory()
        self.root = Path(self.temporary.name)
        self.run = self.root / "run"
        self.environment = patch.dict(
            os.environ, {"BILQIS_DATA_PLANE": str(self.root / "plane.sqlite3")})
        self.environment.start()
        provision_source_authority_registry(self.run, AUTHORITY)
        source = with_source_authority_registry(candidate(parent_state()), AUTHORITY)
        with shape_patch(AUTHORITY), patch.object(mlx_checkpoint, "assert_headroom"):
            publish_candidate(self.run, source)

    def tearDown(self):
        self.environment.stop()
        self.temporary.cleanup()

    def _publish_source_qualified_support(self, run):
        with shape_patch(AUTHORITY), patch.object(mlx_checkpoint, "assert_headroom"):
            publish_genesis(run, source_authority_registry=AUTHORITY)
            accepted_parent = load_accepted_generation(run)
            parent_manifest = bind_accepted_execution_cache(
                run).accepted_manifest_sha256
        provision_source_authority_registry(run, AUTHORITY)
        parent, transaction, retained, _authority = source_qualified_state(
            accepted_parent.retained_state, extents=accepted_parent.extents)
        bundle = derive_successor_bundle(
            accepted_parent, retained, parent_manifest_sha256=parent_manifest,
            delivery_events=({"event": "FIXTURE_SOURCE_QUALIFIED"},))
        bundle = with_source_authority_registry(bundle, AUTHORITY)
        decision = retention_decision(parent=parent, retained=retained)
        with shape_patch(AUTHORITY), patch.object(mlx_checkpoint, "assert_headroom"):
            published = accept_and_publish(
                run, bundle, retained, decision=decision,
                feature_sha256=bundle.extents.factor_map_digest,
                training_authorities=transaction.training_authorities,
            )
            accepted_manifest = bind_accepted_execution_cache(
                run).accepted_manifest_sha256
        self.assertEqual(accepted_manifest, published["manifest_sha256"])
        return accepted_manifest

    @staticmethod
    def _late_support_evidence(accepted_manifest):
        correction = _event(DependencyRef(DependencyKind.SOURCE, SOURCE_ROW))
        artifact_id = "capability-support:" + TARGET
        remediation = RemediationReceipt(
            remediation_id="remediation:late-support",
            correction_event_id=correction.event_id,
            correction_receipt_sha256=correction.source_receipt_sha256,
            original_actor_id="actor:late-support",
            original_source_event_id="event:planned",
            original_source_time=570,
            superseded_fact_digest="a" * 64,
            superseded_source_receipt_sha256="1" * 64,
            affected_artifact_ids=(artifact_id,),
            retained_generation_sha256=accepted_manifest,
            completed_at=650,
            status=RemediationStatus.COMPLETED,
        )
        stale = DerivedClaim(
            claim_id="claim:late-support-stale", actor_id="actor:late-support",
            source_event_id="event:planned", source_time=570,
            source_receipt_sha256="1" * 64, fact_digest="a" * 64,
            observed_at=660, derived_path=(artifact_id,),
        )
        later = DerivedClaim(
            claim_id="claim:late-support-independent", actor_id="actor:independent",
            source_event_id="event:independent", source_time=720,
            source_receipt_sha256="2" * 64, fact_digest="a" * 64,
            observed_at=725, derived_path=(artifact_id,),
        )
        return correction, remediation, stale, later

    def test_post_remediation_stale_claim_enters_accepted_runtime_and_blocks_reuse(self):
        binding, generation, _budget, add, _ambiguous = _fixture()
        cached = QualifiedComposition(
            add, generation.source_binding_digest, generation.generation_digest,
            binding.frontier.rights_epoch, binding.frontier.correction_generation,
            "a" * 64)
        context = SolveContext(
            binding, qualified_compositions=(cached,),
            qualification_verifier=lambda item: True)
        with shape_patch(AUTHORITY):
            register_solve_context(self.run, context)
        dependency = DependencyRef(
            DependencyKind.SOURCE,
            "source:binding:" + contract_digest(binding),
        )
        correction = _event(dependency)
        owner = context.operator_composition_artifact_owner
        node = owner.node_for(cached)
        with shape_patch(AUTHORITY):
            AcceptedRuntimeHost(self.run).record_correction(correction)
            AcceptedRuntimeHost(self.run).record_revalidation(_result(node, digest=node.content_digest, correction=correction),
            )
        self.assertEqual(owner.require(cached, binding), node)

        remediation = RemediationReceipt(
            remediation_id="remediation:accepted-runtime",
            correction_event_id=correction.event_id,
            correction_receipt_sha256=correction.source_receipt_sha256,
            original_actor_id="actor:accepted-runtime",
            original_source_event_id="event:planned",
            original_source_time=570,
            superseded_fact_digest="a" * 64,
            superseded_source_receipt_sha256="1" * 64,
            affected_artifact_ids=(node.artifact_id,),
            retained_generation_sha256="9" * 64,
            completed_at=650,
            status=RemediationStatus.COMPLETED,
        )
        stale = DerivedClaim(
            claim_id="claim:accepted-runtime-stale",
            actor_id="actor:accepted-runtime",
            source_event_id="event:planned",
            source_time=570,
            source_receipt_sha256="1" * 64,
            fact_digest="a" * 64,
            observed_at=660,
            derived_path=(node.artifact_id,),
        )
        with shape_patch(AUTHORITY):
            AcceptedRuntimeHost(self.run).record_remediation(remediation)
            _event_id, faults = AcceptedRuntimeHost(self.run).record_derived_claim(stale)
        self.assertEqual(len(faults), 1)
        self.assertEqual(
            faults[0].fault.reason_code,
            "BAMF_C09_PROPAGATION_REPAIR_FAILED",
        )
        with self.assertRaises(BilqisError) as caught:
            owner.require(cached, binding)
        self.assertEqual(
            caught.exception.context["reason"],
            "BAMF_C09_PROPAGATION_REPAIR_FAILED",
        )

    def test_independent_later_evidence_is_not_classified_as_stale_replay(self):
        binding, generation, _budget, add, _ambiguous = _fixture()
        cached = QualifiedComposition(
            add, generation.source_binding_digest, generation.generation_digest,
            binding.frontier.rights_epoch, binding.frontier.correction_generation,
            "a" * 64)
        context = SolveContext(
            binding, qualified_compositions=(cached,),
            qualification_verifier=lambda item: True)
        with shape_patch(AUTHORITY):
            register_solve_context(self.run, context)
        dependency = DependencyRef(
            DependencyKind.SOURCE,
            "source:binding:" + contract_digest(binding),
        )
        correction = _event(dependency)
        owner = context.operator_composition_artifact_owner
        node = owner.node_for(cached)
        with shape_patch(AUTHORITY):
            AcceptedRuntimeHost(self.run).record_correction(correction)
            AcceptedRuntimeHost(self.run).record_revalidation(_result(node, digest=node.content_digest, correction=correction),
            )
            AcceptedRuntimeHost(self.run).record_remediation(RemediationReceipt(
                    remediation_id="remediation:accepted-runtime-independent",
                    correction_event_id=correction.event_id,
                    correction_receipt_sha256=correction.source_receipt_sha256,
                    original_actor_id="actor:accepted-runtime",
                    original_source_event_id="event:planned",
                    original_source_time=570,
                    superseded_fact_digest="a" * 64,
                    superseded_source_receipt_sha256="1" * 64,
                    affected_artifact_ids=(node.artifact_id,),
                    retained_generation_sha256="9" * 64,
                    completed_at=650,
                    status=RemediationStatus.COMPLETED,
                ),
            )
            _event_id, faults = AcceptedRuntimeHost(self.run).record_derived_claim(DerivedClaim(
                    claim_id="claim:accepted-runtime-independent",
                    actor_id="actor:later-independent",
                    source_event_id="event:later-independent",
                    source_time=720,
                    source_receipt_sha256="2" * 64,
                    fact_digest="a" * 64,
                    observed_at=725,
                    derived_path=(node.artifact_id,),
                ),
            )
        self.assertEqual(faults, ())
        self.assertEqual(owner.require(cached, binding), node)

    def test_stale_fault_requalifies_support_loaded_only_after_fault(self):
        run = self.root / "late-support-run"
        accepted_manifest = self._publish_source_qualified_support(run)
        correction, remediation, stale, later = self._late_support_evidence(
            accepted_manifest)
        with shape_patch(AUTHORITY):
            AcceptedRuntimeHost(run).record_correction(correction)
            AcceptedRuntimeHost(run).record_remediation(remediation)
            _event_id, faults = AcceptedRuntimeHost(run).record_derived_claim(stale)
        self.assertEqual(len(faults), 1)
        update = faults[0].requalification
        self.assertEqual(update.affected_capability_ids, (TARGET,))
        self.assertEqual(len(update.new_source_tasks), 1)
        self.assertEqual(len(update.new_c10_intents), 1)
        with shape_patch(AUTHORITY):
            self.assertEqual(
                bind_accepted_execution_cache(run).accepted_manifest_sha256,
                accepted_manifest,
            )

        with shape_patch(AUTHORITY):
            owner = load_capability_support_owner(run, TARGET)
        self.assertEqual(owner.support.status, "REQUALIFICATION_REQUIRED")
        self.assertEqual(owner.ledger.pending_source_tasks, update.ledger.pending_source_tasks)
        self.assertEqual(owner.ledger.pending_c10_intents, update.ledger.pending_c10_intents)
        with self.assertRaises(BilqisError):
            owner.require(TARGET)
        outbox = run / "akasha-outbox.sqlite3"
        self.assertEqual(len(pending_events(outbox)), 1)

        _reset_accepted_correction_runtime_for_tests()
        del owner
        with shape_patch(AUTHORITY):
            cold = load_capability_support_owner(run, TARGET)
        self.assertEqual(cold.support.status, "REQUALIFICATION_REQUIRED")
        self.assertEqual(cold.ledger.pending_source_tasks, update.ledger.pending_source_tasks)
        self.assertEqual(cold.ledger.pending_c10_intents, update.ledger.pending_c10_intents)
        self.assertEqual(len(pending_events(outbox)), 1)

        with shape_patch(AUTHORITY):
            _event_id, later_faults = AcceptedRuntimeHost(run).record_derived_claim(later)
        self.assertEqual(later_faults, ())
        with shape_patch(AUTHORITY):
            self.assertEqual(
                bind_accepted_execution_cache(run).accepted_manifest_sha256,
                accepted_manifest,
            )

    def test_fresh_source_qualified_successor_releases_ancestor_support_fault(self):
        run = self.root / "requalified-successor-run"
        first_manifest = self._publish_source_qualified_support(run)
        correction, remediation, stale, _later = self._late_support_evidence(
            first_manifest)
        with shape_patch(AUTHORITY):
            AcceptedRuntimeHost(run).record_correction(correction)
            AcceptedRuntimeHost(run).record_remediation(remediation)
            _event_id, faults = AcceptedRuntimeHost(run).record_derived_claim(stale)
        self.assertEqual(len(faults), 1)

        with shape_patch(AUTHORITY):
            accepted_parent = load_accepted_generation(run)
        parent, transaction, retained, _authority = source_qualified_state(
            accepted_parent.retained_state,
            extents=accepted_parent.extents,
            capability=TARGET,
            source_row="source:capability-support:requalified",
            source_family="source-family:capability-support:requalified",
            episode="episode:capability-support:requalified",
            generation_binding="7" * 64,
        )
        successor = derive_successor_bundle(
            accepted_parent,
            retained,
            parent_manifest_sha256=first_manifest,
            delivery_events=({"event": "FIXTURE_REQUALIFIED_SUCCESSOR"},),
        )
        decision = retention_decision(parent=parent, retained=retained)
        with shape_patch(AUTHORITY), patch.object(mlx_checkpoint, "assert_headroom"):
            second = accept_and_publish(
                run, successor, retained, decision=decision,
                feature_sha256=successor.extents.factor_map_digest,
                training_authorities=transaction.training_authorities,
            )

        _reset_accepted_correction_runtime_for_tests()
        with shape_patch(AUTHORITY):
            owner = load_capability_support_owner(run, TARGET)
        self.assertEqual(
            owner.support.retained_generation_sha256,
            second["manifest_sha256"],
        )
        self.assertEqual(owner.support.status, "QUALIFIED")
        self.assertEqual(owner.require(TARGET), owner.support)


if __name__ == "__main__":
    unittest.main()
