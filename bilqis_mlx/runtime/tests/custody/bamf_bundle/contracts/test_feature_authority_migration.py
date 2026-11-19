"""Post-cap migration proofs for B13.5 accepted feature authority."""
import os
from dataclasses import replace
from unittest.mock import patch

import bilqis_mlx.runtime.mlx_checkpoint as mlx_checkpoint
from bilqis_mlx.data_plane import data_plane
from bilqis_mlx.learning.atlas_acceptance import mint_acceptance_binding
from bilqis_mlx.runtime.bamf_bundle import (
    publish_bamf_generation, read_accepted_generation_feature_lineage,
    save_bamf_bundle,
)
from bilqis_mlx.runtime.bamf_bundle import feature_authority
from bilqis_mlx.runtime.bamf_bundle.records import (
    BAMF_BUNDLE_SCHEMA, BAMF_POINTER_SCHEMA, canonical, sha,
)
from bilqis_mlx.runtime.tests.custody.bamf_bundle.contracts.feature_authority_lineage_support import (
    FeatureLineageCase, SUCCESSOR_ATLAS_BUNDLE, SUCCESSOR_RELEASE,
    SUCCESSOR_SOURCE_BUNDLE, frozen_snapshot,
)
from bilqis_mlx.runtime.tests.custody.bamf_bundle.contracts.test_feature_authority import (
    feature_bound, source_features,
)
from bilqis_mlx.runtime.tests.custody.bamf_bundle.helpers import (
    acceptance, accepted_state, candidate, next_accepted_step, parent_state,
    retention_decision, shape_patch,
)
from bilqis_mlx.semantics.atlas.snapshot import load_atlas_snapshot
from bilqis_mlx.semantics.atlas_features import FeatureSchema, build_feature_manifest
from bilqis_mlx.semantics.atlas_projection import (
    compile_atlas_release, persist_atlas_release,
)
from bilqis_mlx.semantics.tests.atlas.projection.helpers import (
    PRIOR_ABI, _bindings, _fixture_bundle,
)


class AcceptedFeatureMigrationTests(FeatureLineageCase):
    def _save_legacy_bundle(self, student, stage_name):
        stage = self.run / stage_name
        with shape_patch(), patch.object(mlx_checkpoint, "assert_headroom"):
            manifest = save_bamf_bundle(student, stage)
        legacy = {
            key: value for key, value in manifest.items()
            if key not in {
                "manifest_sha256", "training_objective_ref",
                "training_objective_digest", "parent_acceptance_sha256",
            }
        }
        legacy["schema"] = BAMF_BUNDLE_SCHEMA
        raw = canonical(legacy)
        legacy_digest = sha(raw)
        (stage / "manifest.json").write_bytes(raw)
        data_plane().put_node(
            legacy_digest, raw, student.generation,
            student.parent_manifest_sha256)
        bundle_root = self.run / "bamf-bundles"
        bundle_root.mkdir(parents=True, exist_ok=True)
        stage.rename(bundle_root / legacy_digest)
        return {**legacy, "manifest_sha256": legacy_digest}

    def _legacy_changed_tip(self, root):
        genesis = feature_bound(candidate(parent_state()), root)
        first_manifest = self._save_legacy_bundle(genesis, "legacy-genesis")
        changed = replace(
            root, semantic_release=SUCCESSOR_RELEASE,
            atlas_bundle_id=SUCCESSOR_ATLAS_BUNDLE,
            source_bundle_id=SUCCESSOR_SOURCE_BUNDLE,
            predecessor_digest=root.digest)
        generation_one = feature_bound(
            candidate(
                accepted_state(parent_state()), 1,
                first_manifest["manifest_sha256"]),
            changed, release=SUCCESSOR_RELEASE,
            atlas_bundle=SUCCESSOR_ATLAS_BUNDLE,
            source_bundle=SUCCESSOR_SOURCE_BUNDLE)
        generation_one = replace(generation_one, transition={
            **generation_one.transition, "kind": "PARAMETER_EXTENSION",
            "invalidate_derived_caches": True})
        second_manifest = self._save_legacy_bundle(
            generation_one, "legacy-generation-one")
        return genesis, first_manifest, changed, generation_one, second_manifest

    def _install_legacy_acceptance_pointer(
            self, genesis, first_manifest, generation_one, second_manifest):
        first_acceptance = acceptance(genesis)
        second_acceptance = mint_acceptance_binding(
            retention_decision(
                parent=genesis.retained_state,
                retained=generation_one.retained_state),
            generation_one.retained_state, run_id=generation_one.run_id,
            generation=generation_one.generation,
            feature_sha256=generation_one.extents.factor_map_digest)
        acceptance_root = self.run / "bamf-acceptance"
        acceptance_root.mkdir()
        for manifest, binding in (
                (first_manifest, first_acceptance),
                (second_manifest, second_acceptance)):
            (acceptance_root / f"{manifest['manifest_sha256']}.json").write_bytes(
                canonical(binding.to_record()))
        self.pointer.write_bytes(canonical({
            "schema": BAMF_POINTER_SCHEMA,
            "run_id": generation_one.run_id,
            "generation": generation_one.generation,
            "parent_manifest_sha256": generation_one.parent_manifest_sha256,
            "bundle": f"bamf-bundles/{second_manifest['manifest_sha256']}",
            "manifest_sha256": second_manifest["manifest_sha256"],
            "acceptance_sha256": second_acceptance.digest,
        }))

    def test_changed_release_replays_real_sibling_atlas_bundles(self):
        source_root = self.root / "source"
        source_root.mkdir()
        bundle, coverage, *_ = _fixture_bundle(source_root)
        # A digest-looking artifact root is still a root unless it is itself a
        # persisted Atlas bundle. This guards the locator-availability edge.
        atlas_root = self.root / ("f" * 64)

        first_release = compile_atlas_release(
            bundle, coverage, PRIOR_ABI, _bindings())
        first_artifact = persist_atlas_release(first_release, atlas_root)
        first_snapshot = load_atlas_snapshot(first_artifact.path)
        first_features = build_feature_manifest(
            first_snapshot, FeatureSchema((), ()))

        second_release = compile_atlas_release(
            bundle, coverage, first_snapshot, _bindings())
        second_artifact = persist_atlas_release(second_release, atlas_root)
        second_snapshot = load_atlas_snapshot(second_artifact.path)
        second_features = build_feature_manifest(
            second_snapshot, FeatureSchema((), (), first_features))
        self.assertNotEqual(first_artifact.bundle_id, second_artifact.bundle_id)

        first = self.publish_feature_genesis(
            first_features,
            selection=__import__(
                "bilqis_mlx.semantics.atlas.snapshot",
                fromlist=["AtlasArtifactSelection"]).AtlasArtifactSelection(
                    str(first_artifact.path), first_artifact.bundle_id,
                    first_release.digest, first_release.source_bundle_id),
            snapshot=first_snapshot, schema=FeatureSchema((), ()))
        changed = feature_bound(
            candidate(accepted_state(parent_state()), 1, first["manifest_sha256"]),
            second_features, release=second_release.digest,
            atlas_bundle=second_artifact.bundle_id,
            source_bundle=second_release.source_bundle_id,
            active_set=second_snapshot.active_set_sha256)
        changed = replace(changed, transition={
            **changed.transition, "kind": "PARAMETER_EXTENSION",
            "invalidate_derived_caches": True})
        self.publish(changed)

        with patch.dict(
                os.environ, {"BILQIS_ATLAS_ARTIFACT_ROOT": str(atlas_root)}), \
                shape_patch(), patch(
                    "bilqis_mlx.semantics.atlas.snapshot._require_registered_source_pin"):
            receipt, current, predecessor = read_accepted_generation_feature_lineage(
                self.pointer)

        self.assertEqual(receipt.feature_sha256, second_features.digest)
        self.assertEqual(receipt.predecessor_feature_sha256, first_features.digest)
        self.assertEqual(
            (current, predecessor), (second_features, first_features))

    def test_live_v2_cutover_preserves_changed_feature_construction_history(self):
        root = source_features()
        genesis, first_manifest, changed, generation_one, second_manifest = (
            self._legacy_changed_tip(root))
        self._install_legacy_acceptance_pointer(
            genesis, first_manifest, generation_one, second_manifest)

        retained = feature_bound(
            candidate(
                next_accepted_step(generation_one.retained_state), 2,
                second_manifest["manifest_sha256"]),
            changed, release=SUCCESSOR_RELEASE,
            atlas_bundle=SUCCESSOR_ATLAS_BUNDLE,
            source_bundle=SUCCESSOR_SOURCE_BUNDLE)
        retained_acceptance = acceptance(
            retained, parent=generation_one.retained_state)
        with shape_patch(), patch.object(mlx_checkpoint, "assert_headroom"):
            publish_bamf_generation(
                self.run, retained, acceptance=retained_acceptance)

        def replay(snapshot, schema):
            return changed if schema.predecessor is not None else root

        with shape_patch(), patch.object(
                feature_authority, "load_pinned_atlas_snapshot",
                side_effect=frozen_snapshot), patch.object(
                feature_authority, "build_feature_manifest", side_effect=replay):
            receipt, current, predecessor = read_accepted_generation_feature_lineage(
                self.pointer)

        self.assertEqual(receipt.generation, 2)
        self.assertEqual(receipt.feature_sha256, changed.digest)
        self.assertEqual(receipt.predecessor_feature_sha256, changed.digest)
        self.assertEqual((current, predecessor), (changed, changed))
