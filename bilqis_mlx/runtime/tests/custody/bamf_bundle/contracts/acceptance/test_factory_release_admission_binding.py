from bilqis_mlx.runtime.tests.custody.bamf_bundle.contracts.acceptance.factory_release_admission_binding_support import *

class FactoryReleaseAdmissionBindingTests(FactoryReleaseAdmissionBindingSupport):
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
