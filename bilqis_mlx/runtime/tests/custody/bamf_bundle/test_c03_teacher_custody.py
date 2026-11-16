"""C03 teacher-visit identity follows accepted B13 custody across restart."""
from __future__ import annotations

from dataclasses import replace
import os
import random
from pathlib import Path
from types import SimpleNamespace
from tempfile import TemporaryDirectory
import unittest
from unittest.mock import patch

import bilqis_mlx.runtime.mlx_checkpoint as mlx_checkpoint
from bilqis_mlx.compatibility import historical_teacher_policy
from bilqis_mlx.errors import BilqisError
from bilqis_mlx.learning.atlas_acceptance import candidate_identity_digest
from bilqis_mlx.learning.learning_experiment import Settings
from bilqis_mlx.learning.teacher_lineage import restore_teacher_lineage
from bilqis_mlx.runtime.accepted_teacher_custody import (
    BoundTeacherVisit, derive_c03_successor_bundle, select_accepted_teacher_visit,
)
from bilqis_mlx.runtime.bamf_bundle import BamfBundleCandidate, publish_bamf_generation
from bilqis_mlx.runtime.bamf_bundle.admission import load_accepted_generation
from bilqis_mlx.runtime.bamf_bundle.package_import_transition import (
    _issue_package_import_transition,
)
from bilqis_mlx.runtime.tests.custody.bamf_bundle.helpers import (
    acceptance, accepted_state, publish_genesis, shape_patch,
)
from bilqis_mlx.runtime.tests.custody.bamf_bundle.teacher_custody_fixtures import (
    adaptation, selection_teacher,
)


class C03AcceptedTeacherCustodyTests(unittest.TestCase):
    def setUp(self):
        self.temporary = TemporaryDirectory()
        self.root = Path(self.temporary.name)
        self.run = self.root / "run"
        self.environment = patch.dict(
            os.environ, {"BILQIS_DATA_PLANE": str(self.root / "plane.sqlite3")})
        self.environment.start()

    def tearDown(self):
        self.environment.stop()
        self.temporary.cleanup()

    def _assert_bound_visit(self, bound, parent, pointer, current_student):
        self.assertEqual(bound.identity.run_identity_sha256, parent.run_identity.digest)
        self.assertEqual(bound.identity.run_seed, 71)
        self.assertEqual(bound.identity.generation, 0)
        self.assertEqual(bound.identity.accepted_manifest_sha256, pointer["manifest_sha256"])
        self.assertEqual(bound.identity.student_sha256, current_student)
        self.assertEqual(bound.identity.selection_seed, 71)
        self.assertEqual(bound.identity.cursor, "GENESIS")
        self.assertEqual(bound.projection.teacher_state["last_visit"], bound.identity.to_record())
        self.assertEqual(
            bound.projection.teacher_state["last_visit_receipt"]["visit_id"],
            bound.identity.visit_id)

    def _assert_cold_visit(self, cold, bound, restored):
        self.assertEqual(cold.teacher_state["last_visit"], bound.identity.to_record())
        self.assertEqual(
            cold.teacher_state["last_visit_receipt"],
            bound.projection.teacher_state["last_visit_receipt"])
        self.assertEqual(cold.teacher_state["next_seed"], 72)
        self.assertEqual(cold.teacher_state["cursor"], "lesson:1")
        self.assertEqual(cold.teacher_state["teacher_epoch"], 1)
        self.assertEqual(
            restored.student_sha256, candidate_identity_digest(cold.retained_state))

    def test_genesis_visit_and_accepted_successor_cold_resume_exact_c03_identity(self):
        with shape_patch(), patch.object(mlx_checkpoint, "assert_headroom"):
            pointer = publish_genesis(self.run, run_seed=71)
        with shape_patch():
            parent = load_accepted_generation(self.run)

        teacher = selection_teacher()
        current_student = candidate_identity_digest(parent.retained_state)
        school = SimpleNamespace(
            stage="RECOVERY_1",
            current_student=SimpleNamespace(sha256=current_student))
        with shape_patch():
            bound, policy, metadata = select_accepted_teacher_visit(
                self.run, historical_teacher_policy, school, random.Random(17),
                Settings(), "factory/7", {}, "A", capability_id="C.ADD",
                total_capabilities=20, legacy_receipt={"teacher": teacher},
                adaptation=adaptation(), prior_region="legacy-region")
        self.assertIsInstance(policy, dict)
        self.assertIsInstance(metadata, dict)
        self._assert_bound_visit(bound, parent, pointer, current_student)

        retained = accepted_state(parent.retained_state, parent.extents)
        with shape_patch():
            successor = derive_c03_successor_bundle(
                self.run, retained, bound,
                next_seed=72, cursor="lesson:1",
                delivery_events=({"event": "C03_TEST_VISIT", "optimizer_step": 1},))
        self.assertEqual(successor.provenance.teacher_identity,
                         successor.teacher_state["teacher_identity"])
        self.assertEqual(successor.provenance.teacher_epoch,
                         successor.teacher_state["teacher_epoch"])
        self.assertEqual(successor.teacher_state["last_visit"],
                         bound.identity.to_record())

        with shape_patch(), patch.object(mlx_checkpoint, "assert_headroom"):
            publish_bamf_generation(
                self.run, successor,
                acceptance=acceptance(successor, parent=parent.retained_state),
                reserve_gib=0.)
        with shape_patch():
            cold = load_accepted_generation(self.run)
        restored = restore_teacher_lineage(cold.teacher_state)
        self._assert_cold_visit(cold, bound, restored)

        cold_school = SimpleNamespace(
            stage="RECOVERY_1",
            current_student=SimpleNamespace(sha256=restored.student_sha256))
        with shape_patch():
            rebound, _policy, _metadata = select_accepted_teacher_visit(
                self.run, historical_teacher_policy, cold_school, random.Random(18),
                Settings(), "factory/7", {}, "A", capability_id="C.ADD",
                total_capabilities=20)
        self.assertEqual(rebound.identity.generation, 1)
        self.assertEqual(rebound.identity.run_seed, 71)
        self.assertEqual(rebound.identity.selection_seed, 72)
        self.assertEqual(rebound.identity.cursor, "lesson:1")
        self.assertEqual(rebound.identity.student_sha256, restored.student_sha256)

        with self.assertRaises(BilqisError) as caller_failure:
            BoundTeacherVisit(bound.projection, bound.identity)
        self.assertEqual(
            caller_failure.exception.context["reason"],
            "TEACHER_VISIT_CALLER_CONSTRUCTION_FORBIDDEN")

        with shape_patch(), self.assertRaises(BilqisError) as stale_failure:
            derive_c03_successor_bundle(
                self.run, retained, bound,
                next_seed=73, cursor="lesson:2",
                delivery_events=({"event": "C03_STALE_VISIT", "optimizer_step": 1},))
        self.assertEqual(
            stale_failure.exception.context["reason"],
            "TEACHER_VISIT_ACCEPTED_GENERATION_DRIFT")

    def test_prebootstrap_package_import_does_not_strand_c03_bootstrap(self):
        with shape_patch(), patch.object(mlx_checkpoint, "assert_headroom"):
            pointer = publish_genesis(self.run, run_seed=73)
        with shape_patch():
            parent = load_accepted_generation(self.run)
        transition = _issue_package_import_transition(
            package_sha256="1" * 64,
            screened_candidate_sha256="2" * 64,
            reset_policy_sha256="3" * 64,
            c05_evidence_sha256="4" * 64,
            c05_policy_sha256="5" * 64,
            source_clearance_sha256="6" * 64,
        )
        imported = BamfBundleCandidate(
            parent.run_id, 1, pointer["manifest_sha256"],
            parent.implementation_sha256, parent.topology, parent.extents,
            parent.retained_state, parent.optimizer_hyperparameters,
            parent.provenance, parent.semantic_abi, parent.compiler_features,
            parent.correction_frontier, parent.teacher_state,
            parent.evaluation_contract, transition,
            ({"event": "C12_PREBOOTSTRAP_IMPORT", "optimizer_step": 0},),
            parent.run_identity)
        with shape_patch(), patch.object(mlx_checkpoint, "assert_headroom"):
            imported_pointer = publish_bamf_generation(
                self.run, imported,
                acceptance=acceptance(imported, parent=parent.retained_state),
                reserve_gib=0.)
        with shape_patch():
            cold = load_accepted_generation(self.run)
        self.assertEqual(cold.generation, 1)
        self.assertEqual(cold.retained_state.optimizer_step, 0)
        self.assertNotIn("c03_lineage", cold.teacher_state)

        student = candidate_identity_digest(cold.retained_state)
        school = SimpleNamespace(
            stage="RECOVERY_1",
            current_student=SimpleNamespace(sha256=student))
        with shape_patch():
            bound, _policy, _metadata = select_accepted_teacher_visit(
                self.run, historical_teacher_policy, school, random.Random(19),
                Settings(), "factory/7", {}, "A", capability_id="C.ADD",
                total_capabilities=20,
                legacy_receipt={"teacher": selection_teacher()},
                adaptation=adaptation(), prior_region="legacy-region")
        self.assertEqual(bound.identity.generation, 1)
        self.assertEqual(
            bound.identity.accepted_manifest_sha256,
            imported_pointer["manifest_sha256"])
        self.assertEqual(bound.identity.student_sha256, student)


if __name__ == "__main__":
    unittest.main()
