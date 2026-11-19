"""Shared C16.1b first-student foundation test fixture."""
from __future__ import annotations

from dataclasses import asdict
import os
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest
from unittest.mock import patch

import mlx.core as mx

import bilqis_mlx.runtime.mlx_checkpoint as mlx_checkpoint
from bilqis_mlx.learning.champions import Checkpoint
from bilqis_mlx.runtime.admission import _executable_factory_admission
from bilqis_mlx.runtime.atlas_optimizer import AdamWHyperparameters
from bilqis_mlx.runtime.bamf_first_student import (
    BAMF_DASHBOARD_METRICS_SCHEMA,
    BAMF_FOUNDATION_CONFIG_SCHEMA,
    BAMF_LAUNCH_RECEIPT_SCHEMA,
    BamfFoundationConfig,
    load_bamf_foundation_dashboard_projection,
    preflight_bamf_foundation,
)
from bilqis_mlx.runtime.state import _fingerprint
from bilqis_mlx.runtime.tests.custody.bamf_bundle.genesis_authority_fixtures import (
    ATLAS_BUNDLE,
    ATLAS_RELEASE,
    SOURCE_BUNDLE,
    genesis_feature_source_patch,
)
from bilqis_mlx.runtime.tests.custody.bamf_bundle.helpers import shape_patch
from bilqis_mlx.runtime.tests.operator.test_admission import _executable_fixture
from bilqis_mlx.semantics.atlas.snapshot import (
    AtlasArtifactIdentity,
    AtlasArtifactSelection,
)
from bilqis_mlx.state_dag import persist


class BamfFirstStudentCase(unittest.TestCase):
    def setUp(self):
        self.temporary = TemporaryDirectory()
        self.root = Path(self.temporary.name)
        self.environment = patch.dict(
            os.environ, {"BILQIS_DATA_PLANE": str(self.root / "plane.sqlite3")})
        self.environment.start()
        self.release, self.graph = _executable_fixture()
        self.source = self.root / "source-run"
        origin = Checkpoint("7" * 64, "bundles/foundation-origin", 0, True)
        _, release_file, admission = _executable_factory_admission(
            self.source, self.release, origin, _fingerprint(self.graph), self.graph)
        state = {
            "generation": 0,
            "factory_release_sha256": self.release.release_sha256,
            "factory_release_file": release_file,
            "factory_admission_v2": asdict(admission),
            "semantic_graph_sha256": _fingerprint(self.graph),
            "school": {
                "current_student": asdict(origin),
                "active_grades": ["A", "B", "C"],
                "grade_index": 2,
                "visits": 11,
                "stage": "FOUNDATION",
            },
            "result": "READY_FOR_HUMAN_START",
        }
        persist(self.source, state)
        self.hp = AdamWHyperparameters(.0007, (.88, .97), 1e-7, .03)
        self.identity = AtlasArtifactIdentity(
            ATLAS_BUNDLE, ATLAS_RELEASE, SOURCE_BUNDLE)
        self.selection = AtlasArtifactSelection(
            "/fixture/atlas", ATLAS_BUNDLE, ATLAS_RELEASE, SOURCE_BUNDLE)

    def tearDown(self):
        self.environment.stop()
        self.temporary.cleanup()

    def config(self, *, run_id="bamf-first-student", run_seed=543):
        return BamfFoundationConfig(
            source_run_dir=str(self.source),
            run_id=run_id,
            run_seed=run_seed,
            semantic_graph=self.graph,
            atlas_artifact=self.identity,
            optimizer_hyperparameters=self.hp,
        )

    def preflight(self, target: Path, *, config=None, release=None):
        config = self.config() if config is None else config
        release = self.release if release is None else release
        with shape_patch(), genesis_feature_source_patch(), \
                patch("bilqis_mlx.runtime.bamf_first_student.resolve_atlas_artifact_selection",
                      return_value=self.selection), \
                patch.object(mlx_checkpoint, "assert_headroom"), \
                patch("bilqis_mlx.runtime.bamf_bundle.codec.assert_headroom"):
            return preflight_bamf_foundation(config, release, target)

    def assert_owner_identity(self, receipt, student, manifest_sha256):
        source_identity = (self.release.source_bindings.source_attestation_sha256
                           or self.release.source_bindings.digest())
        self.assertEqual(receipt.schema_version, BAMF_LAUNCH_RECEIPT_SCHEMA)
        self.assertEqual(receipt.config_schema_version, BAMF_FOUNDATION_CONFIG_SCHEMA)
        self.assertEqual(receipt.run_identity, student.run_identity)
        self.assertEqual(receipt.manifest_sha256, manifest_sha256)
        self.assertEqual(receipt.factory_release_sha256, self.release.release_sha256)
        self.assertEqual(receipt.run_identity.run_seed, 543)
        self.assertEqual(
            receipt.run_identity.initial_topology_digest, student.topology.digest)
        self.assertEqual(
            receipt.run_identity.initial_extents_digest, student.extents.digest)
        self.assertEqual(
            receipt.run_identity.initial_implementation_sha256,
            student.implementation_sha256)
        self.assertEqual(receipt.run_identity.initial_source_identity, source_identity)
        self.assertEqual(student.provenance.source_identity, source_identity)
        self.assertEqual(
            receipt.run_identity.initial_release_digest,
            student.provenance.release_digest)
        self.assertEqual(
            receipt.run_identity.initial_teacher_identity,
            student.provenance.teacher_identity)
        self.assertEqual(
            receipt.run_identity.initial_teacher_epoch,
            student.provenance.teacher_epoch)
        self.assertEqual(
            receipt.run_identity.factory_release_sha256,
            self.release.release_sha256)

    def assert_zero_optimizer_and_semantics(self, receipt, student, declared):
        self.assertEqual(receipt.optimizer_hyperparameters, self.hp)
        self.assertEqual(student.optimizer_hyperparameters, self.hp)
        self.assertEqual(student.retained_state.optimizer_step, 0)
        self.assertEqual(student.retained_state.step_proofs, ())
        self.assertEqual(student.semantic_abi["schema"], "bilqis.mlx.bamf-semantic-abi/v1")
        self.assertGreater(student.semantic_abi["semantic_bank_count"], 0)
        self.assertEqual(
            student.semantic_abi["active_set_sha256"],
            student.extents.active_semantic_digest)
        expected_shapes = {item.name: item.shape for item in declared}
        actual_shapes = {
            name: tuple(value.shape)
            for name, value in student.retained_state.optimizer.parameters.items()
        }
        self.assertEqual(actual_shapes, expected_shapes)
        self.assertEqual(
            tuple(student.retained_state.optimizer.parameters),
            tuple(item.name for item in declared))
        self.assertTrue(all(
            not bool(mx.any(moment))
            for tree in (student.retained_state.optimizer.m,
                         student.retained_state.optimizer.v)
            for moment in tree.values()))
        self.assertTrue(all(
            not bool(mx.any(count))
            for count in student.retained_state.optimizer.update_counts.values()))

    def assert_teacher_and_dashboard(self, receipt, student, target):
        self.assertEqual(
            student.teacher_state["teacher_identity"],
            self.release.execution_plan.projection_digests.teaching)
        self.assertEqual(
            student.teacher_state["teacher_identity"],
            student.provenance.teacher_identity)
        self.assertEqual(student.teacher_state["next_seed"], 543)
        self.assertEqual(receipt.atlas_artifact, self.identity)
        admitted_grades = tuple(
            grade.grade_id for grade in self.release.execution_plan.grades)
        self.assertEqual(
            tuple(student.compiler_features["factory_grade_ids"]), admitted_grades)
        self.assertEqual(receipt.dashboard_metrics.active_grades, admitted_grades)
        self.assertEqual(receipt.dashboard_metrics.current_grade, admitted_grades[0])
        self.assertEqual(receipt.dashboard_metrics.optimizer_step, 0)
        self.assertEqual(receipt.dashboard_metrics.grade_visits, 0)
        self.assertEqual(receipt.dashboard_metrics.stage, "READY_FOR_HUMAN_START")
        self.assertEqual(receipt.dashboard_metrics.last_run_status, "NOT_STARTED")
        with shape_patch():
            projection = load_bamf_foundation_dashboard_projection(target)
        self.assertIsNotNone(projection)
        self.assertEqual(
            (
                receipt.dashboard_metrics.optimizer_step,
                receipt.dashboard_metrics.grade_visits,
                receipt.dashboard_metrics.stage,
                receipt.dashboard_metrics.active_grades,
                receipt.dashboard_metrics.current_grade,
                receipt.dashboard_metrics.last_run_status,
            ),
            (
                projection.optimizer_step,
                projection.grade_visits,
                projection.stage,
                projection.active_grades,
                projection.current_grade,
                projection.last_run_status,
            ),
        )
        self.assertEqual(
            receipt.dashboard_metrics.schema_version, BAMF_DASHBOARD_METRICS_SCHEMA)
        self.assertEqual(receipt.input_schema_versions, (
            ("config", BAMF_FOUNDATION_CONFIG_SCHEMA),
            ("factory_release", self.release.schema),
            ("atlas_artifact_identity", self.identity.schema),
        ))
        self.assertEqual(
            dict(receipt.output_schema_versions)["dashboard_metrics"],
            BAMF_DASHBOARD_METRICS_SCHEMA)
        self.assertEqual(receipt.optional_services_required, ())
        for optional in ("akasha", "low-bit-cache", "private-journal"):
            self.assertFalse((target / optional).exists())
