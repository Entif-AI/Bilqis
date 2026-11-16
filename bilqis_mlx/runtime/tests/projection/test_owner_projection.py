"""Production C10 owner projections consume accepted authority, never lookalikes."""
from dataclasses import replace
from pathlib import Path
import random
import tempfile
from types import SimpleNamespace
import unittest
from unittest.mock import patch

import bilqis_mlx.runtime.mlx_checkpoint as mlx_checkpoint
from bilqis_mlx.compatibility import historical_teacher_policy
from bilqis_mlx.learning.atlas_acceptance import candidate_identity_digest
from bilqis_mlx.learning.atlas_acceptance import EXACT_MOTIF_CLOSURE_ACCEPTANCE_SCHEMA
from bilqis_mlx.learning.learning_experiment import Settings

from bilqis_mlx.errors import BilqisError
from bilqis_mlx.runtime.akasha_outbox import (
    AkashaEvent, AkashaEventKind, append_outbox, read_outbox,
)
from bilqis_mlx.runtime.akasha_staging import build_staging_projection
from bilqis_mlx.runtime.bamf_projection import read_projection_outbox
from bilqis_mlx.runtime.tests.projection.test_bamf_projection import _contract, _projected
from bilqis_mlx.runtime.owner_projection import (
    append_accepted_bamf_generation,
    append_public_package_export,
    event_from_public_package_export,
    events_from_accepted_bamf_generation,
)
from bilqis_mlx.runtime.bamf_bundle.atlas_admission import _issue_atlas_admission_binding
from bilqis_mlx.runtime.bamf_bundle.factory_release.admission import (
    _issue_factory_release_admission_binding,
)
from bilqis_mlx.runtime.bamf_bundle.factory_release_adoption import (
    _issue_factory_release_adoption_transition,
    derive_factory_release_adoption_candidate,
)
from bilqis_mlx.runtime.bamf_bundle.publication import (
    publish_atlas_admission_generation,
    publish_factory_release_adoption_generation,
)
from bilqis_mlx.runtime.bamf_bundle.admission import derive_successor_bundle
from bilqis_mlx.runtime.bamf_bundle import load_bamf_generation, publish_bamf_generation
from bilqis_mlx.runtime.accepted_teacher_custody import (
    derive_c03_successor_bundle, select_accepted_teacher_visit,
)
from bilqis_mlx.runtime.cognitive_package import export_capability
from bilqis_mlx.runtime.cognitive_package.exchange import publish_package
from bilqis_mlx.runtime.cognitive_package.staging import authorize_public_export
from bilqis_mlx.runtime.cognitive_package.tests.export_authority_fixtures import (
    REGISTRY as EXPORT_REGISTRY,
    frontier as export_frontier,
    receipt as export_receipt,
    selection as export_selection,
)
from bilqis_mlx.runtime.cognitive_package.tests.fixtures import snapshot
from bilqis_mlx.runtime.tests.custody.bamf_bundle.contracts.acceptance._generation_acceptance_support import (
    GenerationAcceptanceFixture,
)
from bilqis_mlx.runtime.tests.custody.bamf_bundle.contracts.acceptance.test_atlas_admission_publication import (
    AtlasAdmissionPublicationTests,
)
from bilqis_mlx.runtime.tests.custody.bamf_bundle.helpers import accepted_state, shape_patch
from bilqis_mlx.runtime.tests.custody.bamf_bundle.helpers import next_accepted_step
from bilqis_mlx.runtime.tests.custody.bamf_bundle.publication.publication_helpers import (
    acceptance,
)
from bilqis_mlx.runtime.tests.custody.bamf_bundle.teacher_custody_fixtures import (
    adaptation, selection_teacher,
)


class AcceptedOwnerProjectionTests(GenerationAcceptanceFixture, unittest.TestCase):
    def test_exact_motif_closure_schema_projects_motif_candidate(self):
        from bilqis_mlx.runtime.owner_generation_projection import _motif

        binding = SimpleNamespace(
            schema_version=EXACT_MOTIF_CLOSURE_ACCEPTANCE_SCHEMA,
            digest="9" * 64,
        )
        transition = {
            "kind": "MOTIF_ALLOCATION",
            "motif_candidate_sha256": "1" * 64,
            "approved_context_sha256": "2" * 64,
            "candidate_allocation_sha256": "3" * 64,
            "added_pages": 0,
        }
        student = SimpleNamespace(
            transition=transition,
            run_id="run:fixture",
            generation=7,
        )
        source = SimpleNamespace(student=student, binding=binding)
        issued = {}

        def issue(**kwargs):
            issued.update(kwargs)
            return SimpleNamespace(**kwargs)

        with patch(
                "bilqis_mlx.runtime.bamf_bundle.motif.transition."
                "is_motif_allocation_transition", return_value=True), patch(
                "bilqis_mlx.runtime.bamf_bundle.motif.transition."
                "validate_motif_allocation_transition"):
            event = _motif(issue, lambda value: value, source)
        self.assertIs(issued["kind"], AkashaEventKind.MOTIF_CANDIDATE)
        self.assertEqual(issued["source_receipt_sha256"], binding.digest)
        self.assertEqual(event.payload["motif_candidate_sha256"], "1" * 64)

    def test_teacher_visit_projects_from_accepted_c03_custody_not_native_name(self):
        parent = self.parent()
        school = SimpleNamespace(
            stage="RECOVERY_1",
            current_student=SimpleNamespace(
                sha256=candidate_identity_digest(parent.retained_state)))
        with shape_patch():
            bound, _policy, _metadata = select_accepted_teacher_visit(
                self.run, historical_teacher_policy, school, random.Random(17),
                Settings(), "factory/7", {}, "A", capability_id="C.ADD",
                total_capabilities=20,
                legacy_receipt={"teacher": selection_teacher()},
                adaptation=adaptation(), prior_region="legacy-region")
            successor = derive_c03_successor_bundle(
                self.run,
                accepted_state(parent.retained_state, parent.extents),
                bound, next_seed=72, cursor="lesson:1",
                delivery_events=({"event": "C10_TEACHER_OWNER_FIXTURE"},))
        with shape_patch(), patch.object(mlx_checkpoint, "assert_headroom"):
            publish_bamf_generation(
                self.run, successor,
                acceptance=acceptance(successor, parent=parent.retained_state),
                reserve_gib=0.0)
        with shape_patch():
            events = events_from_accepted_bamf_generation(self.run)
        teacher = tuple(
            event for event in events if event.kind is AkashaEventKind.TEACHER_VISIT)
        self.assertEqual(len(teacher), 1)
        self.assertIn(bound.identity.visit_id, teacher[0].payload_json)
        self.assertIn(self._parent_pointer["manifest_sha256"], teacher[0].payload_json)

    def test_factory_release_projection_consumes_b13_acceptance_and_keeps_time_unknown(self):
        parent = self.parent()
        transition = _issue_factory_release_adoption_transition(
            predecessor_factory_release_sha256=parent.run_identity.factory_release_sha256,
            factory_release_sha256="2" * 64,
            handoff_sha256="3" * 64,
            proposal_sha256="4" * 64,
            staged_candidate_sha256="5" * 64,
            selection_receipt_sha256="6" * 64,
            lease_sha256="7" * 64,
            source_approval_sha256="8" * 64,
        )
        candidate = derive_factory_release_adoption_candidate(
            parent,
            parent_manifest_sha256=self._parent_pointer["manifest_sha256"],
            transition=transition,
        )
        binding = _issue_factory_release_admission_binding(
            candidate, parent, transition=transition)
        with shape_patch(), patch.object(mlx_checkpoint, "assert_headroom"):
            publish_factory_release_adoption_generation(
                self.run, candidate, admission=binding, reserve_gib=0.0)

        with shape_patch():
            events = events_from_accepted_bamf_generation(self.run)
        self.assertEqual(tuple(event.kind for event in events),
                         (AkashaEventKind.FACTORY_RELEASE,))
        event = events[0]
        self.assertEqual(
            (event.source_time, event.effective_time,
             event.observed_at, event.recorded_at),
            (None, None, None, None))
        self.assertIn(binding.digest, event.payload_json)
        with self.assertRaises(BilqisError) as caught:
            append_outbox(self.root / "unbound.sqlite3", event)
        self.assertEqual(
            caught.exception.context["reason"],
            "BAMF_C10_OWNER_PROJECTION_BINDING_REQUIRED")
        path = self.root / "factory-outbox.sqlite3"
        domain = _contract(path)
        with shape_patch():
            self.assertEqual(
                append_accepted_bamf_generation(self.run, domain).appended_count, 1)
            self.assertEqual(
                append_accepted_bamf_generation(self.run, domain).duplicate_count, 1)
        self.assertEqual(read_outbox(path), events)
        self.assertEqual(
            tuple(item.event for item in read_projection_outbox(path)), events)
        with tempfile.TemporaryDirectory() as folder:
            domain = _contract(Path(folder) / "outbox.sqlite3")
            with self.assertRaises(BilqisError):
                build_staging_projection((_projected(event, domain),), domain)

    def test_parameter_extension_projects_bank_allocation_from_c07_binding(self):
        parent, source = AtlasAdmissionPublicationTests.extension(self)
        with AtlasAdmissionPublicationTests.atlas_context(self):
            binding = _issue_atlas_admission_binding(
                source, parent,
                lease_sha256="9" * 64,
                source_approval_sha256="8" * 64,
                proposal_sha256="7" * 64,
                factory_release_sha256="6" * 64,
                staging_receipt_sha256="5" * 64,
                parent_feature_receipt_sha256="4" * 64,
            )
            publish_atlas_admission_generation(
                self.run, source, admission=binding, reserve_gib=0.0)

        with AtlasAdmissionPublicationTests.atlas_context(self):
            events = events_from_accepted_bamf_generation(self.run)
        self.assertEqual(tuple(event.kind for event in events),
                         (AkashaEventKind.BANK_ALLOCATION,))
        self.assertIn(binding.feature_sha256, events[0].payload_json)
        self.assertIn(binding.digest, events[0].payload_json)

    def test_retained_policy_change_projects_plasticity_epoch_from_accepted_generation(self):
        source = self.source(alternate=True)
        first = self.publish(source, acceptance=self.binding(source))
        with shape_patch():
            parent = load_bamf_generation(self.run / "bamf-state.json")
            retained = next_accepted_step(parent.retained_state, parent.extents)
        successor = derive_successor_bundle(
            parent,
            retained,
            parent_manifest_sha256=first["manifest_sha256"],
            delivery_events=({"event": "FIXTURE_SUCCESSOR"},),
        )
        self.publish(
            successor,
            acceptance=acceptance(successor, parent=parent.retained_state),
        )
        with shape_patch():
            events = events_from_accepted_bamf_generation(self.run)
        self.assertEqual(tuple(event.kind for event in events),
                         (AkashaEventKind.PLASTICITY_EPOCH,))
        self.assertIn('"parent_acceptance_receipt_sha256":', events[0].payload_json)
        self.assertIn('"parent_policy_sha256":', events[0].payload_json)


class PackageOwnerProjectionTests(unittest.TestCase):
    def test_public_package_projection_revalidates_clearance_and_exact_published_bytes(self):
        selection = export_selection()
        source, _unused_grant = snapshot()
        source = replace(
            source,
            binding=replace(source.binding, semantic_release=selection.release_sha256),
        )
        receipt = export_receipt(source)
        frontier = export_frontier()
        grant = authorize_public_export(
            source, receipt, selection, frontier, EXPORT_REGISTRY)
        package = export_capability(source, source.signature, grant)
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            published = publish_package(package, root / "published")
            event = event_from_public_package_export(
                package, published, receipt, selection, frontier, EXPORT_REGISTRY)
            self.assertEqual(event.kind, AkashaEventKind.PACKAGE_EXPORT)
            self.assertEqual(event.source_receipt_sha256, receipt.clearance_sha256)
            self.assertEqual(
                (event.source_time, event.effective_time,
                 event.observed_at, event.recorded_at),
                (None, None, None, None))
            outbox = root / "outbox.sqlite3"
            domain = _contract(outbox)
            self.assertEqual(append_public_package_export(
                package, published, receipt, selection, frontier,
                EXPORT_REGISTRY, domain).appended_count, 1)
            self.assertEqual(append_public_package_export(
                package, published, receipt, selection, frontier,
                EXPORT_REGISTRY, domain).duplicate_count, 1)
            self.assertEqual(
                tuple(item.event for item in read_projection_outbox(outbox)),
                (event,))
            published.write_text("tampered")
            with self.assertRaises(Exception):
                event_from_public_package_export(
                    package, published, receipt, selection, frontier, EXPORT_REGISTRY)


class OwnerProjectionContractTests(unittest.TestCase):
    def test_generic_owner_issuer_and_source_stamper_are_not_exposed(self):
        import bilqis_mlx.runtime.owner_projection as owner_projection
        self.assertFalse(hasattr(owner_projection, "_issue_accepted_source"))
        self.assertFalse(hasattr(owner_projection, "_issue_owner_payload"))
        self.assertFalse(hasattr(owner_projection, "_accepted_generation"))
        self.assertFalse(hasattr(owner_projection, "_motif_event"))

    def test_unknown_time_requires_complete_null_quartet_and_stays_internal(self):
        payload = {
            "run_id": "fixture-run",
            "generation": 1,
            "transition_kind": "PARAMETER_EXTENSION",
            "feature_sha256": "1" * 64,
            "factory_release_sha256": "2" * 64,
            "admission_receipt_sha256": "3" * 64,
        }
        with self.assertRaises(BilqisError):
            AkashaEvent.from_payload(
                kind=AkashaEventKind.BANK_ALLOCATION,
                subject_id="feature-allocation:" + "1" * 64,
                source_receipt_sha256="3" * 64,
                payload=payload,
                source_time=None,
                effective_time=None,
                observed_at=None,
                recorded_at=None,
            )
        with self.assertRaises(BilqisError):
            AkashaEvent(
                event_id="4" * 64,
                payload_digest="5" * 64,
                kind=AkashaEventKind.BANK_ALLOCATION,
                subject_id="feature-allocation:" + "1" * 64,
                source_receipt_sha256="3" * 64,
                payload_json="{}",
                source_time=None,
                effective_time=None,
                observed_at=None,
                recorded_at=None,
            )
        with self.assertRaises(BilqisError):
            AkashaEvent.from_payload(
                kind=AkashaEventKind.BANK_ALLOCATION,
                subject_id="feature-allocation:" + "1" * 64,
                source_receipt_sha256="3" * 64,
                payload=payload,
                source_time=None,
                effective_time=1,
                observed_at=None,
                recorded_at=None,
            )

    def test_legacy_native_event_still_requires_concrete_time(self):
        payload = {
            "native_event_id": "1" * 64,
            "native_event_digest": "2" * 64,
            "run_id": "fixture-run",
            "generation": 1,
            "native_event_type": "SCHOOL_TEACHER_VISIT_COMMITTED",
        }
        with self.assertRaises(BilqisError):
            AkashaEvent.from_payload(
                kind=AkashaEventKind.TEACHER_VISIT,
                subject_id="teacher-visit:fixture",
                source_receipt_sha256="3" * 64,
                payload=payload,
                source_time=None,
                effective_time=None,
                observed_at=None,
                recorded_at=None,
            )

if __name__ == "__main__":
    unittest.main()
