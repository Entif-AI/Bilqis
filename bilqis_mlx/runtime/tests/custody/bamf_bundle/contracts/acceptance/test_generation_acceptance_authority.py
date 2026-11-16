"""Split B13.5 acceptance-provenance witnesses."""
from ._generation_acceptance_support import *
import bilqis_mlx.learning.atlas_acceptance as acceptance_owner
import bilqis_mlx.learning.atlas_retention_decision as retention_owner
import bilqis_mlx.runtime.bamf_bundle.feature_authority as feature_authority
import bilqis_mlx.runtime.bamf_bundle.publication as publication
import bilqis_mlx.runtime.bamf_bundle.feature.acceptance as feature_acceptance
from bilqis_mlx.runtime.tests.custody.bamf_bundle.genesis_authority_fixtures import (
    frozen_snapshot as genesis_frozen_snapshot,
    source_features as genesis_source_features,
)


class GenerationAcceptanceAuthorityTests(GenerationAcceptanceFixture, unittest.TestCase):
    def test_shared_publication_sink_rejects_arbitrary_successor_authority(self):
        source = self.source()
        before = json.loads((self.run / "bamf-state.json").read_text())
        with shape_patch(), patch.object(mlx_checkpoint, "assert_headroom"):
            with self.assertRaises(BilqisError) as failure:
                publication._publish_authorized_generation(
                    self.run, source, object(), reserve_gib=0.)
        self.assertEqual(
            failure.exception.context["reason"],
            "BAMF_GENERATION_ACCEPTANCE_REQUIRED")
        self.assertEqual(
            json.loads((self.run / "bamf-state.json").read_text()), before)

    def test_caller_cannot_construct_an_acceptance_binding(self):
        source = self.source()
        binding = self.binding(source)
        with self.assertRaises(BilqisError):
            AcceptedCandidateBinding(**binding._public_record())

    def test_exact_type_forged_retention_decision_cannot_mint_acceptance(self):
        source = candidate(parent_state())
        decision = retention_decision(retained=source.retained_state)
        forged = object.__new__(CandidateRetentionDecision)
        for name, value in decision._public_record().items():
            object.__setattr__(forged, name, value)

        with self.assertRaises(BilqisError):
            mint_acceptance_binding(
                forged, source.retained_state, run_id=source.run_id,
                generation=source.generation,
                feature_sha256=source.extents.factor_map_digest)

    def test_exact_type_forged_acceptance_binding_cannot_publish(self):
        source = self.source()
        binding = self.binding(source)
        forged = object.__new__(AcceptedCandidateBinding)
        for name, value in binding._public_record().items():
            object.__setattr__(forged, name, value)

        with self.assertRaises(BilqisError):
            self.publish(source, acceptance=forged)

    def test_reachable_decision_issuer_token_cannot_authorize_a_forgery(self):
        source = candidate(parent_state())
        decision = retention_decision(retained=source.retained_state)
        forged = object.__new__(CandidateRetentionDecision)
        for name, value in decision.__dict__.items():
            object.__setattr__(forged, name, value)

        self.assertFalse(hasattr(retention_owner, "_DECISION_ISSUER"))
        with self.assertRaises(BilqisError):
            mint_acceptance_binding(
                forged, source.retained_state, run_id=source.run_id,
                generation=source.generation,
                feature_sha256=source.extents.factor_map_digest)

    def test_reachable_binding_issuer_token_cannot_authorize_a_forgery(self):
        source = self.source()
        binding = self.binding(source)
        forged = object.__new__(AcceptedCandidateBinding)
        for name, value in binding.__dict__.items():
            object.__setattr__(forged, name, value)

        self.assertFalse(hasattr(acceptance_owner, "_BINDING_ISSUER"))
        with self.assertRaises(BilqisError):
            self.publish(source, acceptance=forged)

    def test_accepted_c05_decision_cannot_transfer_to_different_optimizer(self):
        source = candidate(parent_state())
        decision = retention_decision(retained=source.retained_state)
        another = accepted_state(parent_state())
        with self.assertRaises(BilqisError):
            mint_acceptance_binding(
                decision, another, run_id=source.run_id,
                generation=source.generation,
                feature_sha256=source.extents.factor_map_digest)

    def test_parent_custody_rejects_a_screen_for_another_parent(self):
        successor = self.source()
        wrong_parent = self.source(alternate=True).retained_state
        binding = mint_acceptance_binding(
            retention_decision(parent=wrong_parent, retained=successor.retained_state),
            successor.retained_state, run_id=successor.run_id,
            generation=successor.generation,
            feature_sha256=successor.extents.factor_map_digest)
        with self.assertRaises(BilqisError) as failure:
            self.publish(successor, acceptance=binding)
        self.assertEqual(failure.exception.context["reason"],
                         "BAMF_GENERATION_ACCEPTANCE_DRIFT")

    def test_caller_cannot_mint_acceptance_without_a_retention_decision(self):
        source = candidate(parent_state())
        with self.assertRaises(BilqisError):
            mint_acceptance_binding(
                "FIXTURE_RETENTION_ACCEPTED", source.retained_state,
                run_id=source.run_id, generation=source.generation,
                feature_sha256=source.extents.factor_map_digest)

    def test_historical_decision_cannot_mint_live_acceptance(self):
        source = candidate(parent_state())
        parsed = CandidateRetentionDecision.from_record(retention_decision().to_record())
        self.assertNotEqual(type(parsed), CandidateRetentionDecision)
        self.assertTrue(parsed.accepted)
        with self.assertRaises(BilqisError):
            mint_acceptance_binding(
                parsed, source.retained_state, run_id=source.run_id,
                generation=source.generation,
                feature_sha256=source.extents.factor_map_digest)

    def test_v1_decision_record_remains_readable_without_issuance(self):
        source = candidate(parent_state())
        legacy = {
            "decision": "PROVISIONAL",
            "reason": "PAIRED_SCREEN_WITHIN_BUDGET",
            "target_gain": True,
            "protected_net_gain": 1,
            "schema_version": LEGACY_DECISION_SCHEMA,
        }
        legacy["decision_sha256"] = hashlib.sha256(canonical(legacy)).hexdigest()
        parsed = CandidateRetentionDecision.from_record(legacy)
        self.assertEqual(parsed.to_record(), legacy)
        with self.assertRaises(BilqisError):
            mint_acceptance_binding(
                parsed, source.retained_state,
                run_id=source.run_id, generation=source.generation,
                feature_sha256=source.extents.factor_map_digest)

    def test_a_rejected_retention_decision_cannot_mint_acceptance(self):
        source = candidate(parent_state())
        rejected = retention_decision(
            accepted=False, retained=source.retained_state)
        self.assertFalse(rejected.accepted)
        with self.assertRaises(BilqisError):
            mint_acceptance_binding(
                rejected, source.retained_state, run_id=source.run_id,
                generation=source.generation,
                feature_sha256=source.extents.factor_map_digest)

    def test_receipt_refuses_a_generation_without_acceptance_custody(self):
        features = source_features()
        source = self.feature_source(features)
        self.publish(source, acceptance=self.binding(source))
        binding_path = (self.run / "bamf-acceptance"
                        / f"{json_manifest_sha(self.run)}.json")
        binding_path.unlink()
        with shape_patch(), \
                patch("bilqis_mlx.runtime.bamf_bundle.feature_authority."
                      "build_feature_manifest", return_value=features), \
                patch("bilqis_mlx.runtime.bamf_bundle.feature_authority."
                      "load_pinned_atlas_snapshot", side_effect=lambda selection: selection):
            with self.assertRaises(BilqisError) as failure:
                read_accepted_generation_feature_receipt(
                    self.run / "bamf-state.json")
        self.assertEqual(
            failure.exception.context["reason"],
            "BAMF_GENERATION_ACCEPTANCE_MISSING")

    def test_accepted_authority_loaders_require_acceptance_custody(self):
        source = self.source()
        self.publish(source, acceptance=self.binding(source))
        binding_path = (self.run / "bamf-acceptance"
                        / f"{json_manifest_sha(self.run)}.json")
        binding_path.unlink()
        pointer_path = self.run / "bamf-state.json"
        with shape_patch():
            for name, loader in (
                    ("publication authority", lambda: load_bamf_generation_authority(pointer_path)),
                    ("admission authority", lambda: admission.load_accepted_generation(self.run))):
                with self.subTest(loader=name):
                    with self.assertRaises(BilqisError) as failure:
                        loader()
                    self.assertEqual(
                        failure.exception.context["reason"],
                        "BAMF_GENERATION_ACCEPTANCE_MISSING")

    def test_accepted_authority_loaders_reject_rehashed_acceptance_drift(self):
        source = self.source()
        self.publish(source, acceptance=self.binding(source))
        binding_path = (self.run / "bamf-acceptance"
                        / f"{json_manifest_sha(self.run)}.json")
        record = json.loads(binding_path.read_text())
        record["optimizer_step"] += 1
        record["binding_sha256"] = hashlib.sha256(canonical({
            key: value for key, value in record.items()
            if key != "binding_sha256"
        })).hexdigest()
        binding_path.write_text(json.dumps(record))
        pointer_path = self.run / "bamf-state.json"
        with shape_patch():
            for name, loader in (
                    ("publication authority", lambda: load_bamf_generation_authority(pointer_path)),
                    ("admission authority", lambda: admission.load_accepted_generation(self.run))):
                with self.subTest(loader=name):
                    with self.assertRaises(BilqisError) as failure:
                        loader()
                    self.assertEqual(
                        failure.exception.context["reason"],
                        "BAMF_GENERATION_ACCEPTANCE_DRIFT")

    def test_authoritative_successor_reads_reject_run_identity_drift(self):
        features = genesis_source_features()
        source = self.source()
        self.publish(source, acceptance=self.binding(source))
        pointer_path = self.run / "bamf-state.json"
        real_load = publication.load_bamf_bundle

        def drifted_load(path, *, expected_manifest_sha256=None):
            student = real_load(
                path, expected_manifest_sha256=expected_manifest_sha256)
            if student.generation > 0:
                identity = replace(
                    student.run_identity,
                    run_seed=student.run_identity.run_seed + 1,
                )
                return replace(student, run_identity=identity)
            return student

        with shape_patch(), patch.object(
                publication, "load_bamf_bundle", side_effect=drifted_load):
            with self.assertRaises(BilqisError) as failure:
                load_bamf_generation_authority(pointer_path)
            self.assertEqual(
                failure.exception.context["reason"],
                "BAMF_GENERATION_ACCEPTANCE_DRIFT")

        real_feature_load = feature_acceptance.load_bamf_bundle

        def drifted_feature_load(path, *, expected_manifest_sha256=None):
            student = real_feature_load(
                path, expected_manifest_sha256=expected_manifest_sha256)
            if student.generation > 0:
                identity = replace(
                    student.run_identity,
                    run_seed=student.run_identity.run_seed + 1,
                )
                return replace(student, run_identity=identity)
            return student

        with shape_patch(), \
                patch.object(feature_acceptance, "load_bamf_bundle",
                             side_effect=drifted_feature_load), \
                patch.object(feature_authority, "resolve_atlas_artifact_selection",
                             side_effect=lambda identity: identity), \
                patch.object(feature_authority, "build_feature_manifest",
                             return_value=features), \
                patch.object(feature_authority, "load_pinned_atlas_snapshot",
                             side_effect=genesis_frozen_snapshot):
            with self.assertRaises(BilqisError) as failure:
                read_accepted_generation_feature_receipt(pointer_path)
            self.assertEqual(
                failure.exception.context["reason"],
                "BAMF_GENERATION_ACCEPTANCE_DRIFT")


if __name__ == "__main__":
    unittest.main()
