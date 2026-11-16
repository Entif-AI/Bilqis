"""Split B13.5 acceptance-provenance witnesses."""
from ._generation_acceptance_support import *


class GenerationAcceptancePublicationTests(GenerationAcceptanceFixture, unittest.TestCase):
    def test_publication_without_retention_acceptance_is_refused(self):
        source = self.source()
        with self.assertRaises(BilqisError) as failure:
            self.publish(source)
        self.assertEqual(
            failure.exception.context["reason"],
            "BAMF_GENERATION_ACCEPTANCE_REQUIRED")
        self.assertEqual(
            json.loads((self.run / "bamf-state.json").read_text()),
            self._parent_pointer,
        )

    def test_acceptance_for_another_candidate_state_is_refused(self):
        source = self.source()
        other = self.binding(self.source(alternate=True))
        with self.assertRaises(BilqisError) as failure:
            self.publish(source, acceptance=other)
        self.assertEqual(
            failure.exception.context["reason"],
            "BAMF_GENERATION_ACCEPTANCE_DRIFT")

    def test_acceptance_with_another_feature_identity_is_refused(self):
        source = self.source()
        binding = mint_acceptance_binding(
            retention_decision(
                parent=self.parent().retained_state,
                retained=source.retained_state),
            source.retained_state, run_id=source.run_id,
            generation=source.generation, feature_sha256="a" * 64)
        with self.assertRaises(BilqisError) as failure:
            self.publish(source, acceptance=binding)
        self.assertEqual(
            failure.exception.context["reason"],
            "BAMF_GENERATION_ACCEPTANCE_DRIFT")

    def test_motif_acceptance_with_teacher_anchor_uses_portable_exact_schema(self):
        source = self.source()
        decision = retention_decision(
            parent=self.parent().retained_state,
            retained=source.retained_state,
        )
        generation_authority = "f" * 64
        teacher_anchor = "e" * 64
        with patch(
                "bilqis_mlx.learning.atlas_retention_decision."
                "_issued_decision_generation_authority",
                return_value=generation_authority), patch(
                "bilqis_mlx.learning.atlas_retention_decision."
                "_require_issued_decision_generation_authority"):
            binding = mint_acceptance_binding(
                decision, source.retained_state,
                run_id=source.run_id, generation=source.generation,
                feature_sha256=source.extents.factor_map_digest,
                teacher_state_sha256=teacher_anchor,
                generation_authority_sha256=generation_authority,
            )
        self.assertEqual(binding.schema_version, EXACT_MOTIF_ACCEPTANCE_SCHEMA)
        self.assertEqual(binding.teacher_state_sha256, teacher_anchor)
        self.assertEqual(
            AcceptedCandidateBinding.from_record(binding.to_record()).schema_version,
            EXACT_MOTIF_ACCEPTANCE_SCHEMA,
        )

    def test_c09_source_qualified_schema_family_tracks_exact_rollout(self):
        from bilqis_mlx.learning.atlas_acceptance import (
            ACCEPTANCE_SCHEMA, CLOSURE_ACCEPTANCE_SCHEMA,
            EXACT_ACCEPTANCE_SCHEMA, EXACT_CLOSURE_ACCEPTANCE_SCHEMA,
            EXACT_MOTIF_CLOSURE_ACCEPTANCE_SCHEMA, MOTIF_CLOSURE_ACCEPTANCE_SCHEMA,
        )
        from bilqis_mlx.runtime.capability_support_loading import (
            _SOURCE_QUALIFIED_ACCEPTANCE_SCHEMAS,
        )

        self.assertEqual(
            _SOURCE_QUALIFIED_ACCEPTANCE_SCHEMAS,
            (
                ACCEPTANCE_SCHEMA,
                CLOSURE_ACCEPTANCE_SCHEMA,
                MOTIF_CLOSURE_ACCEPTANCE_SCHEMA,
                EXACT_ACCEPTANCE_SCHEMA,
                EXACT_CLOSURE_ACCEPTANCE_SCHEMA,
                EXACT_MOTIF_CLOSURE_ACCEPTANCE_SCHEMA,
            ),
        )
        self.assertNotIn(
            EXACT_MOTIF_ACCEPTANCE_SCHEMA,
            _SOURCE_QUALIFIED_ACCEPTANCE_SCHEMAS,
        )

    def test_publication_refuses_binding_with_foreign_step_proof(self):
        source = self.source()
        forged = self.binding(source)
        object.__setattr__(forged, "step_proof_sha256", ("0" * 64,))
        with self.assertRaises(BilqisError) as failure:
            self.publish(source, acceptance=forged)
        self.assertEqual(failure.exception.context["reason"],
                         "BAMF_GENERATION_ACCEPTANCE_DRIFT")

    def test_historical_binding_with_matching_identity_cannot_authorize_publication(self):
        source = self.source()
        parsed = AcceptedCandidateBinding.from_record(self.binding(source).to_record())
        self.assertNotEqual(type(parsed), AcceptedCandidateBinding)
        self.assertEqual(parsed.digest, self.binding(source).digest)
        with self.assertRaises(BilqisError) as failure:
            self.publish(source, acceptance=parsed)
        self.assertEqual(failure.exception.context["reason"],
                         "BAMF_GENERATION_ACCEPTANCE_REQUIRED")

    def test_v1_acceptance_record_remains_readable_but_not_authoritative(self):
        source = self.source()
        issued = self.binding(source)
        fields = (
            "run_id", "generation", "candidate_identity_sha256",
            "feature_sha256", "optimizer_step", "retention_reason",
            "step_proof_sha256", "decision_sha256",
        )
        legacy = {name: getattr(issued, name) for name in fields}
        legacy["schema_version"] = LEGACY_ACCEPTANCE_SCHEMA
        legacy["binding_sha256"] = hashlib.sha256(canonical(legacy)).hexdigest()
        parsed = AcceptedCandidateBinding.from_record(legacy)
        self.assertEqual(parsed.to_record(), legacy)
        with self.assertRaises(BilqisError):
            self.publish(source, acceptance=parsed)

    def test_v3_source_anchor_record_remains_readable_but_not_authoritative(self):
        source = self.source()
        issued = self.binding(source)
        record = issued.to_record()
        record["schema_version"] = PREVIOUS_SOURCE_ACCEPTANCE_SCHEMA
        record["source_anchors"] = []
        record.pop("source_authority_registry_sha256")
        record.pop("teacher_state_sha256")
        record.pop("generation_authority_sha256")
        record["binding_sha256"] = hashlib.sha256(canonical({
            key: value for key, value in record.items()
            if key != "binding_sha256"
        })).hexdigest()
        parsed = AcceptedCandidateBinding.from_record(record)
        self.assertEqual(parsed.schema_version, PREVIOUS_SOURCE_ACCEPTANCE_SCHEMA)
        with self.assertRaises(BilqisError):
            self.publish(source, acceptance=parsed)

    def test_replay_cannot_replace_immutable_acceptance_evidence(self):
        source = self.source()
        first = self.publish(source, acceptance=self.binding(source))
        altered = self.binding(source)
        object.__setattr__(altered, "policy_sha256", "0" * 64)
        with self.assertRaises(BilqisError) as failure:
            self.publish(source, acceptance=altered)
        self.assertEqual(failure.exception.context["reason"],
                         "DATA_PLANE_BUNDLE_IDENTITY_CONFLICT")
        self.assertEqual(json.loads((self.run / "bamf-state.json").read_text()), first)

    def test_cold_readback_refuses_resigned_foreign_step_proof(self):
        features = source_features()
        source = self.feature_source(features)
        self.publish(source, acceptance=self.binding(source))
        path = self.run / "bamf-acceptance" / f"{json_manifest_sha(self.run)}.json"
        record = json.loads(path.read_text())
        record["step_proof_sha256"] = ["0" * 64]
        record["binding_sha256"] = hashlib.sha256(canonical({
            key: value for key, value in record.items()
            if key != "binding_sha256"
        })).hexdigest()
        path.write_text(json.dumps(record))
        with shape_patch(), \
                patch("bilqis_mlx.runtime.bamf_bundle.feature_authority."
                      "build_feature_manifest", return_value=features), \
                patch("bilqis_mlx.runtime.bamf_bundle.feature_authority."
                      "load_pinned_atlas_snapshot", side_effect=lambda selection: selection):
            with self.assertRaises(BilqisError) as failure:
                read_accepted_generation_feature_receipt(
                    self.run / "bamf-state.json")
        self.assertEqual(failure.exception.context["reason"],
                         "BAMF_GENERATION_ACCEPTANCE_DRIFT")

    def test_cold_readback_refuses_rehashed_retention_policy(self):
        features = source_features()
        source = self.feature_source(features)
        self.publish(source, acceptance=self.binding(source))
        path = self.run / "bamf-acceptance" / f"{json_manifest_sha(self.run)}.json"
        record = json.loads(path.read_text())
        record["policy_sha256"] = "0" * 64
        record["binding_sha256"] = hashlib.sha256(canonical({
            key: value for key, value in record.items()
            if key != "binding_sha256"
        })).hexdigest()
        path.write_text(json.dumps(record))
        with shape_patch(), \
                patch("bilqis_mlx.runtime.bamf_bundle.feature_authority."
                      "build_feature_manifest", return_value=features), \
                patch("bilqis_mlx.runtime.bamf_bundle.feature_authority."
                      "load_pinned_atlas_snapshot", side_effect=lambda selection: selection):
            with self.assertRaises(BilqisError) as failure:
                read_accepted_generation_feature_receipt(
                    self.run / "bamf-state.json")
        self.assertEqual(failure.exception.context["reason"],
                         "BAMF_GENERATION_ACCEPTANCE_DRIFT")

    def test_historical_pointer_can_cold_load_without_minting_new_authority(self):
        features = source_features()
        source = self.feature_source(features)
        self.publish(source, acceptance=self.binding(source))
        pointer_path = self.run / "bamf-state.json"
        pointer = json.loads(pointer_path.read_text())
        pointer["schema"] = LEGACY_BAMF_POINTER_SCHEMA
        pointer.pop("acceptance_sha256")
        pointer_path.write_text(json.dumps(pointer))
        with shape_patch():
            self.assertEqual(
                load_bamf_generation(pointer_path).run_id, source.run_id)
        with shape_patch(), \
                patch("bilqis_mlx.runtime.bamf_bundle.feature_authority."
                      "build_feature_manifest", return_value=features), \
                patch("bilqis_mlx.runtime.bamf_bundle.feature_authority."
                      "load_pinned_atlas_snapshot", side_effect=lambda selection: selection):
            with self.assertRaises(BilqisError):
                read_accepted_generation_feature_receipt(pointer_path)


if __name__ == "__main__":
    unittest.main()
