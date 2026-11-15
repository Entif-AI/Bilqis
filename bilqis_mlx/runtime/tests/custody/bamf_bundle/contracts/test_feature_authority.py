"""B13.5 accepted-generation feature authority witnesses.

A caller-created candidate must never ratify its own factor-map digest. The
receipt is minted from custody and from the replayed admitted source release.
"""
from __future__ import annotations

import unittest
from dataclasses import replace
from unittest.mock import patch

import bilqis_mlx.runtime.mlx_checkpoint as mlx_checkpoint
from bilqis_mlx.errors import BilqisError
from bilqis_mlx.runtime.bamf_bundle import (
    authenticate_bamf_candidate_features, load_bamf_generation,
    publish_bamf_generation, read_accepted_generation_feature_receipt,
    verify_accepted_generation_feature_receipt,
)
from bilqis_mlx.runtime.bamf_bundle import feature_authority
from bilqis_mlx.runtime.bamf_bundle.genesis import _issue_binding
from bilqis_mlx.semantics.atlas.snapshot import AtlasArtifactSelection

from bilqis_mlx.runtime.tests.custody.bamf_bundle.helpers import (
    acceptance, accepted_state, genesis_preparation, publish_candidate, candidate,
    parent_state, shape_patch,
)
from bilqis_mlx.runtime.bamf_bundle.admission import derive_successor_bundle
from .feature_authority_support import (
    ARBITRARY, ATLAS_BUNDLE, ATLAS_RELEASE, RELEASE, SOURCE_BUNDLE,
    FeatureAuthorityTestBase, feature_bound, frozen_snapshot, source_features,
)


class AcceptedGenerationFeatureAuthorityTests(FeatureAuthorityTestBase):

    def test_accepted_generation_mints_source_replayed_receipt(self):
        features = source_features()
        published = self.publish_feature_genesis(features)
        receipt = self.read_receipt(features)
        self.assertEqual(receipt.run_id, "fixture-run")
        self.assertEqual(receipt.generation, 0)
        self.assertEqual(receipt.generation_manifest_sha256, published["manifest_sha256"])
        self.assertEqual(receipt.feature_sha256, features.digest)
        self.assertEqual(receipt.semantic_release, RELEASE)
        self.assertEqual(receipt.source_atlas_bundle_id, ATLAS_BUNDLE)
        self.assertIsNone(receipt.predecessor_feature_sha256)

    def test_generation_context_materializes_snapshot_and_features_once(self):
        features = source_features()
        self.publish_feature_genesis(features)
        counts = {"atlas": 0, "features": 0}

        def load_snapshot(selection):
            counts["atlas"] += 1
            return frozen_snapshot(selection)

        def build_features(snapshot, schema):
            counts["features"] += 1
            return features

        with shape_patch():
            student = load_bamf_generation(self.pointer)
        with shape_patch(), patch.object(
                feature_authority, "resolve_atlas_artifact_selection",
                side_effect=lambda identity: AtlasArtifactSelection(
                    "/artifact", identity.bundle_id, identity.release_sha256,
                    identity.source_bundle_id)), patch.object(
                feature_authority, "load_pinned_atlas_snapshot",
                side_effect=load_snapshot), patch.object(
                    feature_authority, "build_feature_manifest",
                    side_effect=build_features):
            context = feature_authority.authenticate_bamf_generation_feature_context(
                student, "/artifact", self.pointer)

        self.assertEqual(counts, {"atlas": 1, "features": 1})
        self.assertEqual(context.features, features)
        self.assertEqual(context.atlas_reload_count, 1)
        self.assertEqual(context.feature_manifest_rebuild_count, 1)

    def test_genesis_preserves_distinct_atlas_release_and_active_set_identity(self):
        features = source_features(release=ATLAS_RELEASE)
        authority = self.foundation_authority(features)
        with shape_patch(), self.foundation_replay(features):
            prepared = genesis_preparation(foundation_features=authority)
        snapshot = frozen_snapshot(authority.selection)
        self.assertNotEqual(prepared.release.release_sha256, ATLAS_RELEASE)
        self.assertEqual(prepared.candidate.provenance.release_digest, ATLAS_RELEASE)
        self.assertEqual(
            prepared.candidate.semantic_abi["active_set_sha256"],
            snapshot.active_set_sha256)
        self.assertEqual(
            prepared.candidate.extents.active_semantic_digest,
            snapshot.active_set_sha256)

    def test_unaccepted_candidate_can_only_replay_its_recorded_source_features(self):
        features = source_features()
        proposed = feature_bound(candidate(parent_state()), features)
        with self.source_replay(features):
            replayed = authenticate_bamf_candidate_features(proposed, "/artifact")
        self.assertEqual(replayed, features)

        forged = feature_bound(proposed, features, digest=ARBITRARY)
        with self.source_replay(features), self.assertRaises(BilqisError) as failure:
            authenticate_bamf_candidate_features(forged, "/artifact")
        self.assertEqual(
            failure.exception.context["reason"],
            "BAMF_FEATURE_SOURCE_REPLAY_MISMATCH")

    def test_arbitrary_digest_candidate_cannot_self_ratify(self):
        features = source_features()
        authority = self.foundation_authority(features)
        with shape_patch(), self.foundation_replay(features):
            prepared = genesis_preparation(foundation_features=authority)
        adversary = replace(
            prepared.candidate,
            extents=replace(prepared.candidate.extents, factor_map_digest=ARBITRARY),
            compiler_features={
                **prepared.candidate.compiler_features,
                "factor_map_sha256": ARBITRARY})
        with shape_patch(), self.foundation_replay(features), \
                self.assertRaises(BilqisError) as failure:
            _issue_binding(
                adversary, release=prepared.release, admission=prepared.admission,
                graph=prepared.graph, origin_checkpoint=prepared.origin_checkpoint,
                factory_authority=prepared.factory_authority,
                foundation_features=prepared.foundation_features)
        self.assertEqual(
            failure.exception.context["reason"],
            "BAMF_INITIAL_GENERATION_SOURCE_AUTHORITY_DRIFT")
        with self.assertRaises(BilqisError) as preparation_failure:
            replace(prepared, candidate=adversary)
        self.assertEqual(
            preparation_failure.exception.context["reason"],
            "BAMF_INITIAL_GENERATION_PREPARATION_REQUIRED")

    def test_forged_receipt_is_rejected_by_live_verification(self):
        features = source_features()
        self.publish_feature_genesis(features)
        receipt = self.read_receipt(features)
        forged = replace(receipt, feature_sha256=ARBITRARY)
        with shape_patch(), self.source_replay(features):
            with self.assertRaises(BilqisError) as failure:
                verify_accepted_generation_feature_receipt(
                    self.pointer, forged)
        self.assertEqual(
            failure.exception.context["reason"], "BAMF_FEATURE_RECEIPT_MISMATCH")

    def test_production_genesis_always_records_replayable_source_binding(self):
        features = source_features()
        self.publish(candidate(parent_state()))
        with shape_patch():
            student = load_bamf_generation(self.pointer)
        self.assertIn("feature_source", student.compiler_features)
        self.assertIn("feature_schema", student.compiler_features)

    def test_release_drift_between_custody_and_source_refuses_receipt(self):
        features = source_features()
        authority = self.foundation_authority(features)
        with shape_patch(), self.foundation_replay(features):
            prepared = genesis_preparation(foundation_features=authority)
        adversary = replace(
            prepared.candidate,
            compiler_features={
                **prepared.candidate.compiler_features,
                "feature_source": {
                    **prepared.candidate.compiler_features["feature_source"],
                    "release_sha256": "4" * 64}})
        with shape_patch(), self.foundation_replay(features), \
                self.assertRaises(BilqisError) as failure:
            _issue_binding(
                adversary, release=prepared.release, admission=prepared.admission,
                graph=prepared.graph, origin_checkpoint=prepared.origin_checkpoint,
                factory_authority=prepared.factory_authority,
                foundation_features=prepared.foundation_features)
        self.assertEqual(
            failure.exception.context["reason"],
            "BAMF_INITIAL_GENERATION_SOURCE_AUTHORITY_DRIFT")
        with self.assertRaises(BilqisError) as preparation_failure:
            replace(prepared, candidate=adversary)
        self.assertEqual(
            preparation_failure.exception.context["reason"],
            "BAMF_INITIAL_GENERATION_PREPARATION_REQUIRED")

    def test_active_set_drift_between_custody_and_source_refuses_receipt(self):
        features = source_features()
        self.publish_feature_genesis(features)
        drifted = replace(frozen_snapshot(AtlasArtifactSelection(
            "/artifact", ATLAS_BUNDLE, features.semantic_release, SOURCE_BUNDLE)),
            active_set_sha256=ARBITRARY)
        with shape_patch(), patch.multiple(
                feature_authority,
                resolve_atlas_artifact_selection=lambda identity: AtlasArtifactSelection(
                    "/artifact", identity.bundle_id, identity.release_sha256,
                    identity.source_bundle_id),
                load_pinned_atlas_snapshot=lambda selection: drifted,
                build_feature_manifest=lambda snapshot, schema: features), \
                self.assertRaises(BilqisError) as failure:
            read_accepted_generation_feature_receipt(self.pointer)
        self.assertEqual(
            failure.exception.context["reason"], "BAMF_FEATURE_ACTIVE_SET_DRIFT")

    def test_same_feature_child_active_set_drift_requires_c07_admission(self):
        features = source_features()
        first = self.publish_feature_genesis(features)
        with shape_patch():
            parent = load_bamf_generation(self.pointer)
            retained = accepted_state(parent.retained_state, parent.extents)
            child = derive_successor_bundle(
                parent, retained, parent_manifest_sha256=first["manifest_sha256"],
                delivery_events=({"event": "FIXTURE_CHILD"},))
            child = replace(
                child,
                extents=replace(
                    child.extents, active_semantic_digest=ARBITRARY),
                semantic_abi={
                    **child.semantic_abi, "active_set_sha256": ARBITRARY},
                transition={
                    **child.transition, "kind": "PARAMETER_EXTENSION",
                    "invalidate_derived_caches": True})
            with patch.object(mlx_checkpoint, "assert_headroom"), \
                    self.assertRaises(BilqisError) as failure:
                publish_bamf_generation(
                    self.run, child,
                    acceptance=acceptance(
                        child, parent=parent.retained_state), reserve_gib=0.)
        self.assertEqual(
            failure.exception.context["reason"],
            "BAMF_ATLAS_ADMISSION_EXECUTOR_REQUIRED")
        receipt = self.read_receipt(features)
        self.assertEqual(receipt.generation, 0)
        self.assertEqual(receipt.generation_manifest_sha256, first["manifest_sha256"])

    def test_cold_resume_reproduces_the_same_receipt_identity(self):
        features = source_features()
        self.publish_feature_genesis(features)
        first = self.read_receipt(features)
        second = self.read_receipt(features)
        self.assertEqual(first.digest, second.digest)
        self.assertEqual(first, second)

    def test_receipt_record_round_trip_detects_tampering(self):
        features = source_features()
        self.publish_feature_genesis(features)
        receipt = self.read_receipt(features)
        record = receipt.to_record()
        self.assertEqual(
            feature_authority.AcceptedGenerationFeatureReceipt.from_record(record),
            receipt)
        tampered = {**record, "feature_sha256": ARBITRARY}
        with self.assertRaises(BilqisError) as failure:
            feature_authority.AcceptedGenerationFeatureReceipt.from_record(tampered)
        self.assertEqual(
            failure.exception.context["reason"], "BAMF_FEATURE_RECEIPT_INVALID")


if __name__ == "__main__":
    unittest.main()
