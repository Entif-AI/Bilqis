"""Factory-only acceptance binds one exact inert child and owner event."""
from dataclasses import fields, replace
import unittest
from unittest.mock import patch

import bilqis_mlx.runtime.mlx_checkpoint as mlx_checkpoint

from bilqis_mlx.errors import BilqisError
from bilqis_mlx.runtime.bamf_bundle.factory_release.admission import (
    FACTORY_RELEASE_ADMISSION_SCHEMA_V2,
    FACTORY_RELEASE_ADMISSION_SCHEMA_V3,
    FactoryReleaseAdmissionBinding,
    ParsedFactoryReleaseAdmissionBinding,
    _issue_factory_release_admission_binding,
    require_factory_release_admission_binding,
    validate_parsed_factory_release_admission_binding,
)
from bilqis_mlx.runtime.bamf_bundle.factory_release_adoption import (
    FACTORY_RELEASE_ADOPTION_EVENT,
    FACTORY_RELEASE_ADOPTION_EVENT_SCHEMA,
    _issue_factory_release_adoption_transition,
    derive_factory_release_adoption_candidate,
)
from bilqis_mlx.runtime.bamf_bundle import load_bamf_generation_authority
from bilqis_mlx.runtime.bamf_bundle.publication import (
    publish_factory_release_adoption_generation,
)
from bilqis_mlx.runtime.bamf_bundle.records import (
    BamfBundleCandidate,
    CompleteStudent,
    canonical,
    sha,
    sidecar_records,
)
from bilqis_mlx.runtime.tests.admission.atlas.adoption.atlas_adoption_executor_support import (
    AtlasAdoptionExecutorFixture,
)
from bilqis_mlx.runtime.tests.custody.bamf_bundle.contracts.acceptance._generation_acceptance_support import (
    GenerationAcceptanceFixture,
)
from bilqis_mlx.runtime.tests.custody.bamf_bundle.helpers import shape_patch


PUBLIC_BINDING_FIELDS = frozenset({
    "run_id",
    "generation",
    "candidate_identity_sha256",
    "parent_candidate_identity_sha256",
    "feature_sha256",
    "optimizer_step",
    "lease_sha256",
    "source_approval_sha256",
    "handoff_sha256",
    "proposal_sha256",
    "selection_receipt_sha256",
    "predecessor_factory_release_sha256",
    "factory_release_sha256",
    "transition_sha256",
    "adoption_event_sha256",
    "schema_version",
})
OWNER_EVENT_FIELDS = frozenset({
    "event",
    "schema",
    "run_id",
    "generation",
    "optimizer_step",
    "predecessor_factory_release_sha256",
    "factory_release_sha256",
    "handoff_sha256",
    "proposal_sha256",
    "selection_receipt_sha256",
    "lease_sha256",
    "source_approval_sha256",
    "transition_sha256",
})


class FactoryReleaseAdmissionBindingTests(unittest.TestCase):
    @staticmethod
    def _transition():
        return _issue_factory_release_adoption_transition(
            predecessor_factory_release_sha256="1" * 64,
            factory_release_sha256="2" * 64,
            handoff_sha256="3" * 64,
            proposal_sha256="4" * 64,
            staged_candidate_sha256="5" * 64,
            selection_receipt_sha256="6" * 64,
            lease_sha256="7" * 64,
            source_approval_sha256="8" * 64,
        )

    @staticmethod
    def _historical_student(candidate):
        records = sidecar_records(candidate)
        values = {
            item.name: getattr(candidate, item.name)
            for item in fields(BamfBundleCandidate)
        }
        values["outbox"] = tuple(records["outbox"])
        return CompleteStudent(**values)

    def setUp(self):
        helper = object.__new__(AtlasAdoptionExecutorFixture)
        self.parent, _unused = AtlasAdoptionExecutorFixture._native_parent_and_candidate(
            helper
        )
        self.transition = self._transition()
        self.candidate = derive_factory_release_adoption_candidate(
            self.parent,
            parent_manifest_sha256="a" * 64,
            transition=self.transition,
        )
        self.binding = _issue_factory_release_admission_binding(
            self.candidate,
            self.parent,
            transition=self.transition,
        )

    def _parsed(self):
        return FactoryReleaseAdmissionBinding.from_record(self.binding.to_record())

    def _parsed_with(self, **changes):
        record = self.binding.to_record()
        for name, value in changes.items():
            record[name] = value
        public = {name: record[name] for name in PUBLIC_BINDING_FIELDS}
        record["binding_sha256"] = sha(canonical(public))
        return FactoryReleaseAdmissionBinding.from_record(record)

    def test_binding_record_has_exact_keys_and_canonical_digest(self):
        record = self.binding.to_record()
        self.assertEqual(set(record), PUBLIC_BINDING_FIELDS | {"binding_sha256"})
        public = {name: record[name] for name in PUBLIC_BINDING_FIELDS}
        expected_digest = sha(canonical(public))

        self.assertEqual(self.binding.digest, expected_digest)
        self.assertEqual(record["binding_sha256"], expected_digest)
        parsed = FactoryReleaseAdmissionBinding.from_record(record)
        self.assertIsInstance(parsed, ParsedFactoryReleaseAdmissionBinding)
        self.assertEqual(parsed.to_record(), record)

    def test_v2_binding_roundtrip_seals_cumulative_obligation_keys(self):
        keys = (("semantic:event", "9" * 64),)
        binding = _issue_factory_release_admission_binding(
            self.candidate, self.parent, transition=self.transition,
            accepted_obligation_keys=keys)
        parsed = FactoryReleaseAdmissionBinding.from_record(binding.to_record())
        self.assertEqual(binding.schema_version, FACTORY_RELEASE_ADMISSION_SCHEMA_V2)
        self.assertEqual(parsed.accepted_obligation_keys, keys)
        self.assertEqual(parsed.digest, binding.digest)

    def test_v3_binding_roundtrip_seals_generated_grade_proposal(self):
        keys = (("semantic:event", "9" * 64),)
        binding = _issue_factory_release_admission_binding(
            self.candidate, self.parent, transition=self.transition,
            accepted_obligation_keys=keys,
            generated_grade_proposal_sha256="a" * 64)
        parsed = FactoryReleaseAdmissionBinding.from_record(binding.to_record())
        self.assertEqual(binding.schema_version, FACTORY_RELEASE_ADMISSION_SCHEMA_V3)
        self.assertEqual(parsed.accepted_obligation_keys, keys)
        self.assertEqual(parsed.predecessor_factory_release_sha256, "1" * 64)
        self.assertEqual(parsed.generated_grade_proposal_sha256, "a" * 64)
        self.assertEqual(parsed.digest, binding.digest)

    def test_live_binding_rejects_substituted_candidate(self):
        alternate_feature = (
            "f" * 64
            if self.candidate.extents.factor_map_digest != "f" * 64
            else "e" * 64
        )
        substituted = replace(
            self.candidate,
            extents=replace(
                self.candidate.extents,
                factor_map_digest=alternate_feature,
            ),
        )

        with self.assertRaises(BilqisError) as failure:
            require_factory_release_admission_binding(substituted, self.binding)
        self.assertEqual(
            failure.exception.context["reason"],
            "BAMF_FACTORY_RELEASE_ADMISSION_BINDING_DRIFT",
        )

    def test_owner_event_is_exactly_one_exact_shape_and_cannot_be_duplicated(self):
        self.assertEqual(len(self.candidate.outbox), 1)
        event = self.candidate.outbox[0]
        self.assertEqual(set(event), OWNER_EVENT_FIELDS)
        self.assertEqual(event["event"], FACTORY_RELEASE_ADOPTION_EVENT)
        self.assertEqual(event["schema"], FACTORY_RELEASE_ADOPTION_EVENT_SCHEMA)
        self.assertNotIn("event_id", event)
        self.assertEqual(event["transition_sha256"], self.transition.digest)

        duplicate = replace(
            self.candidate,
            outbox=(event, dict(event)),
        )
        with self.assertRaises(BilqisError) as failure:
            _issue_factory_release_admission_binding(
                duplicate,
                self.parent,
                transition=self.transition,
            )
        self.assertEqual(
            failure.exception.context["reason"],
            "BAMF_FACTORY_RELEASE_ADMISSION_BINDING_INVALID",
        )

    def test_historical_parsed_binding_validates_exact_child(self):
        student = self._historical_student(self.candidate)
        parsed = self._parsed()

        validate_parsed_factory_release_admission_binding(
            student,
            parsed,
            parsed.digest,
        )
        with self.assertRaises(BilqisError) as failure:
            validate_parsed_factory_release_admission_binding(
                student,
                parsed,
                "0" * 64,
            )
        self.assertEqual(
            failure.exception.context["reason"],
            "BAMF_FACTORY_RELEASE_ADMISSION_BINDING_DRIFT",
        )

    def test_historical_validation_rejects_transition_tamper(self):
        student = self._historical_student(self.candidate)
        parsed = self._parsed()
        proposal_sha256 = (
            "e" * 64
            if self.transition.proposal_sha256 != "e" * 64
            else "d" * 64
        )
        tampered = replace(
            student,
            transition={
                **dict(student.transition),
                "proposal_sha256": proposal_sha256,
            },
        )

        with self.assertRaises(BilqisError) as failure:
            validate_parsed_factory_release_admission_binding(
                tampered,
                parsed,
                parsed.digest,
            )
        self.assertEqual(
            failure.exception.context["reason"],
            "BAMF_FACTORY_RELEASE_ADMISSION_BINDING_DRIFT",
        )

    def test_historical_validation_rejects_binding_only_digest_tamper(self):
        student = self._historical_student(self.candidate)
        alternate_transition = (
            "0" * 64 if self.binding.transition_sha256 != "0" * 64 else "1" * 64
        )
        alternate_event = (
            "0" * 64 if self.binding.adoption_event_sha256 != "0" * 64 else "1" * 64
        )

        for label, parsed in (
            ("transition", self._parsed_with(transition_sha256=alternate_transition)),
            ("event", self._parsed_with(adoption_event_sha256=alternate_event)),
        ):
            with self.subTest(label=label), self.assertRaises(BilqisError) as failure:
                validate_parsed_factory_release_admission_binding(
                    student,
                    parsed,
                    parsed.digest,
                )
            self.assertEqual(
                failure.exception.context["reason"],
                "BAMF_FACTORY_RELEASE_ADMISSION_BINDING_DRIFT",
            )

    def test_historical_validation_rejects_event_and_event_id_tamper(self):
        student = self._historical_student(self.candidate)
        parsed = self._parsed()
        original = student.outbox[0]
        proposal_sha256 = (
            "e" * 64
            if original["proposal_sha256"] != "e" * 64
            else "d" * 64
        )
        tampered_event = {
            **original,
            "proposal_sha256": proposal_sha256,
        }
        alternate_event_id = (
            "0" * 64 if original["event_id"] != "0" * 64 else "1" * 64
        )
        tampered_event_id = {
            **original,
            "event_id": alternate_event_id,
        }

        for label, event in (
            ("provenance", tampered_event),
            ("event_id", tampered_event_id),
        ):
            with self.subTest(label=label), self.assertRaises(BilqisError) as failure:
                validate_parsed_factory_release_admission_binding(
                    replace(student, outbox=(event,)),
                    parsed,
                    parsed.digest,
                )
            self.assertEqual(
                failure.exception.context["reason"],
                "BAMF_FACTORY_RELEASE_ADMISSION_BINDING_DRIFT",
            )


class FactoryReleasePublicationTests(GenerationAcceptanceFixture, unittest.TestCase):
    def test_real_factory_release_child_publishes_and_cold_loads_exactly(self):
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
            candidate,
            parent,
            transition=transition,
        )

        with shape_patch(), patch.object(mlx_checkpoint, "assert_headroom"):
            pointer = publish_factory_release_adoption_generation(
                self.run,
                candidate,
                admission=binding,
                reserve_gib=0.0,
            )
            cold, manifest_sha256 = load_bamf_generation_authority(
                self.run / "bamf-state.json"
            )

        self.assertEqual(pointer["generation"], parent.generation + 1)
        self.assertEqual(pointer["manifest_sha256"], manifest_sha256)
        self.assertEqual(cold.parent_manifest_sha256, self._parent_pointer["manifest_sha256"])
        self.assertEqual(cold.retained_state.optimizer_step, parent.retained_state.optimizer_step)
        self.assertEqual(cold.topology.digest, parent.topology.digest)
        self.assertEqual(cold.extents.digest, parent.extents.digest)
        self.assertEqual(cold.transition["kind"], "FACTORY_RELEASE_ADOPTION")
        self.assertEqual(cold.transition["factory_release_sha256"], "2" * 64)


if __name__ == "__main__":
    unittest.main()
