"""#542 production BAMF create/resume operator contract."""
from __future__ import annotations

import json
from unittest.mock import patch

import bilqis_mlx.runtime.mlx_checkpoint as mlx_checkpoint
from bilqis_mlx.runtime.tests.custody.bamf_bundle.genesis_authority_fixtures import (
    genesis_feature_source_patch,
)
from bilqis_mlx.runtime.tests.custody.bamf_bundle.helpers import shape_patch
from bilqis_mlx.state_dag import persist, read_current

from .create_resume_support import BamfCreateResumeCase, TOPOLOGY


class BamfCreateResumeTests(BamfCreateResumeCase):
    def test_fresh_bamf_dry_run_is_ready_and_does_not_create_run(self):
        target = self.root / "new-bamf"
        manifest = self.root / "manifest.json"
        manifest.write_text("{}", encoding="utf-8")
        with self.foundation_create_context():
            code, output, errors = self.invoke([
                "--dry-run", "--model-topology", str(TOPOLOGY),
                "--atlas-release-manifest", str(manifest),
                "--run-dir", str(target), "--source-prefetch-workers", "0",
                *self.FOUNDATION_ARGS,
            ])

        self.assertEqual((code, errors), (0, ""))
        report = json.loads(output)
        self.assertEqual(report["schema"], "bilqis.bamf.operator-lifecycle/v1")
        self.assertEqual(report["result"], "READY_TO_CREATE")
        self.assertEqual(report["admission_policy"], "staged")
        self.assertEqual(report["run_id"], "operator-first-student")
        self.assertEqual(report["run_seed"], 543)
        self.assertEqual(report["optimizer_hyperparameters"], {
            "learning_rate": 0.0007,
            "betas": [0.88, 0.97],
            "eps": 1e-7,
            "weight_decay": 0.03,
        })
        self.assertEqual(report["source_prefetch_workers"], 0)
        self.assertEqual(report["neural_updates"], 0)
        self.assertFalse(report["ready_for_training"])
        self.assertEqual(report["run_identity"]["run_id"], report["run_id"])
        self.assertFalse(target.exists())

    def test_dry_run_uses_persisted_source_foundation_owner_without_lifecycle_stub(self):
        target = self.root / "real-source-dry-run"
        manifest = self.root / "manifest.json"
        manifest.write_text("{}", encoding="utf-8")
        source_bundle = self.source / "bundles/source-fixture"
        source_bundle.mkdir(parents=True)
        (source_bundle / "manifest.json").write_text(
            json.dumps({"semantic_catalog": {}}), encoding="utf-8")
        source_state = read_current(self.source)
        source_state["generation"] += 1
        source_state["model_bundle"] = "bundles/source-fixture"
        persist(self.source, source_state)
        with patch(
                "bilqis_mlx.presentation.operator_cli.bamf_lifecycle_inputs.active_run_dir",
                side_effect=AssertionError("explicit source run must bypass active default")), patch(
                "bilqis_mlx.runtime.mlx_checkpoint._read_catalog",
                return_value=self.graph), patch(
                "bilqis_mlx.presentation.operator_cli.bamf_lifecycle.atlas_manifest_identity",
                return_value=self.identity), shape_patch(), genesis_feature_source_patch(), patch(
                "bilqis_mlx.semantics.atlas.snapshot.resolve_atlas_artifact_selection",
                return_value=self.selection), patch(
                "bilqis_mlx.runtime.bamf_first_student.resolve_atlas_artifact_selection",
                return_value=self.selection):
            code, output, errors = self.invoke([
                "--dry-run", "--model-topology", str(TOPOLOGY),
                "--atlas-release-manifest", str(manifest),
                "--source-run-dir", str(self.source),
                "--run-dir", str(target), *self.FOUNDATION_ARGS,
            ])
        self.assertEqual((code, errors), (0, ""))
        report = json.loads(output)
        self.assertEqual(report["result"], "READY_TO_CREATE")
        self.assertEqual(report["run_id"], "operator-first-student")
        self.assertFalse(report["ready_for_training"])
        self.assertFalse(target.exists())

    def test_fresh_bamf_atlas_release_requires_scope_before_any_run_write(self):
        target = self.root / "new-bamf"
        manifest = self.root / "manifest.json"
        manifest.write_text("{}", encoding="utf-8")
        with self.foundation_create_context():
            code, output, errors = self.invoke([
                "--human-run", "--model-topology", str(TOPOLOGY),
                "--admission-policy", "atlas-release",
                "--atlas-release-manifest", str(manifest),
                "--run-dir", str(target), *self.FOUNDATION_ARGS,
            ])

        self.assertEqual((code, output), (2, ""))
        self.assertIn("BAMF_ATLAS_EXPLICIT_SCOPE_FILE_REQUIRED", errors)
        self.assertFalse(target.exists())

    def test_fresh_bamf_dry_run_rejects_invalid_optimizer_before_writes(self):
        target = self.root / "new-bamf"
        manifest = self.root / "manifest.json"
        manifest.write_text("{}", encoding="utf-8")
        code, output, errors = self.invoke([
            "--dry-run", "--model-topology", str(TOPOLOGY),
            "--atlas-release-manifest", str(manifest),
            "--run-dir", str(target),
            "--run-id", "operator-first-student", "--run-seed", "543",
            "--learning-rate", "-0.1", "--adam-beta1", "0.88",
            "--adam-beta2", "0.97", "--adam-eps", "1e-7",
            "--weight-decay", "0.03",
        ])

        self.assertEqual((code, output), (2, ""))
        self.assertIn("BAMF_OPERATOR_FOUNDATION_OPTIMIZER_INVALID", errors)
        self.assertFalse(target.exists())

    def test_human_create_publishes_generation_zero_without_optimizer_update(self):
        target = self.root / "created-bamf"
        manifest = self.root / "manifest.json"
        manifest.write_text("{}", encoding="utf-8")
        with self.foundation_create_context():
            code, output, errors = self.invoke([
                "--human-run", "--model-topology", str(TOPOLOGY),
                "--atlas-release-manifest", str(manifest),
                "--run-dir", str(target), *self.FOUNDATION_ARGS,
            ])

        self.assertEqual((code, errors), (0, ""))
        self.assertIn('"result": "CREATED"', output)
        self.assertTrue((target / "bamf-state.json").is_file())
        self.assertFalse((target / "autonomy/atlas-admission/current.json").exists())
        with self.accepted_read_context():
            from bilqis_mlx.runtime.bamf_bundle import load_bamf_generation_authority
            student, _manifest_sha = load_bamf_generation_authority(
                target / "bamf-state.json")
        self.assertEqual(student.run_id, "operator-first-student")
        self.assertEqual(student.run_identity.run_seed, 543)
        self.assertEqual(student.retained_state.optimizer_step, 0)
        self.assertEqual(student.optimizer_hyperparameters, self.hp)

    def test_non_directory_target_rejects_before_source_reconstruction(self):
        target = self.root / "occupied-target"
        target.write_text("occupied", encoding="utf-8")
        manifest = self.root / "atlas-manifest.json"
        manifest.write_text("{}", encoding="utf-8")
        with patch(
                "bilqis_mlx.presentation.operator_cli.bamf_lifecycle.atlas_manifest_identity",
                return_value=self.identity), patch(
                "bilqis_mlx.presentation.operator_cli.bamf_lifecycle_inputs.active_run_dir",
                return_value=self.source), patch(
                "bilqis_mlx.presentation.operator_cli.bamf_lifecycle.source_foundation",
                side_effect=AssertionError("target shape must reject before source read")):
            code, output, errors = self.invoke([
                "--human-run", "--model-topology", str(TOPOLOGY),
                "--atlas-release-manifest", str(manifest),
                "--run-dir", str(target), *self.FOUNDATION_ARGS,
            ])
        self.assertEqual((code, output), (2, ""))
        self.assertIn("BAMF_FIRST_STUDENT_RUN_DIRECTORY_OCCUPIED", errors)

    def test_overlap_precedes_occupied_target_classification(self):
        target = self.source / "occupied-inside-source"
        target.write_text("occupied", encoding="utf-8")
        manifest = self.root / "atlas-manifest-overlap.json"
        manifest.write_text("{}", encoding="utf-8")
        with patch(
                "bilqis_mlx.presentation.operator_cli.bamf_lifecycle.atlas_manifest_identity",
                return_value=self.identity), patch(
                "bilqis_mlx.presentation.operator_cli.bamf_lifecycle_inputs.active_run_dir",
                return_value=self.source), patch(
                "bilqis_mlx.presentation.operator_cli.bamf_lifecycle.source_foundation",
                side_effect=AssertionError("overlap must reject before source reconstruction")):
            code, output, errors = self.invoke([
                "--human-run", "--model-topology", str(TOPOLOGY),
                "--atlas-release-manifest", str(manifest),
                "--run-dir", str(target), *self.FOUNDATION_ARGS,
            ])
        self.assertEqual((code, output), (2, ""))
        self.assertIn("BAMF_FIRST_STUDENT_TARGET_OVERLAPS_SOURCE", errors)


if __name__ == "__main__":
    import unittest
    unittest.main()
