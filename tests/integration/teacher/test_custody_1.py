"""Teacher integration contracts; original evidence and boundaries preserved."""
from bilqis_mlx.state_dag import read_current
from contextlib import redirect_stdout
import io
import json
from dataclasses import asdict
import unittest
from unittest.mock import patch
from bilqis_mlx import trainer as storage
from bilqis_mlx.learning.learning_experiment import Settings
from tests.system import test_grade_c_trainer as fixtures
from tests.integration.teacher.fixtures import TeacherFixture


class CustodyTests(TeacherFixture, unittest.TestCase):
    def test_tighter_policy_resume_is_metadata_only_and_durable(self):
        school = storage._state_from_json(
            self.receipt["school"], self.schedule_program)
        old = asdict(Settings(mature_max_loss=2))
        previous = storage._advance(self.fixture.root,
            {**self.receipt, "learning_experiment": {
                "version": storage.LEARNING_EXPERIMENT_VERSION, "settings": old}},
            school, persist=False)
        previous = storage._persist(self.fixture.root, storage._with_delivery_outbox(
            previous, ({"event": "FIXTURE_PREVIOUS_POLICY",
                        "generation": previous["generation"]},)))
        student = dict(previous["school"]["current_student"])
        updated = storage._reconcile_learning_settings(
            self.fixture.root, previous, self.course, Settings(), self.fixture.optimizer)
        self.assertEqual(updated["generation"], previous["generation"] + 1)
        self.assertEqual(updated["school"]["current_student"], student)
        self.assertEqual(updated["learning_experiment"]["settings"]["mature_max_loss"], 1)
        self.assertEqual(updated["learning_policy_revisions"][0]["from"], old)
        self.assertEqual(storage._reconcile_learning_settings(
            self.fixture.root, updated, self.course, Settings(), self.fixture.optimizer), updated)
        with self.assertRaisesRegex(ValueError, "IDENTICAL_OPT_IN"):
            storage._reconcile_learning_settings(
                self.fixture.root, updated, self.course,
                Settings(mature_max_loss=2), self.fixture.optimizer)
        with redirect_stdout(io.StringIO()):
            _, own, _, reloaded = self.resume()
        self.assertEqual(reloaded, updated)
        self.assertEqual(int(own.state["step"].item()), student["optimizer_step"])

    def test_existing_exam_peak_is_seeded_before_any_new_training(self):
        school = storage._state_from_json(
            self.receipt["school"], self.schedule_program)
        pointer = dict(self.receipt["school"]["current_student"])
        prior = {"student_sha256": pointer["sha256"],
                 "optimizer_step": pointer["optimizer_step"],
                 "exam_rubric_sha256": "rubric", "cohort_sha256": "cohort",
                 "assessment_scope_sha256": "scope",
                 "scores": {"A.EDGE": {"correct": 11, "total": 12}}}
        saved = storage._advance(self.fixture.root, self.receipt, school,
                                 last_exam=prior, persist=True)
        seeded = storage._seed_saved_whole_student_peak(
            self.fixture.root, saved, self.course, self.fixture.optimizer)
        self.assertEqual(seeded["generation"], saved["generation"] + 1)
        self.assertEqual(seeded["school"]["current_student"], pointer)
        self.assertEqual(seeded["whole_student_peaks"][0]["checkpoint"], pointer)
        self.assertEqual(storage._seed_saved_whole_student_peak(
            self.fixture.root, seeded, self.course, self.fixture.optimizer), seeded)
        storage._verify_best_custody(self.fixture.root, seeded)
        self.assertEqual(read_current(self.fixture.root), seeded)

    def test_retention_peak_is_protected_at_retirement_boundary(self):
        pointer = dict(self.receipt["school"]["current_student"])
        protected = {**self.receipt, "whole_student_peaks": [{
            "schema": "bilqis.mlx.whole-student-retention/v1",
            "checkpoint": pointer, "scope_sha256": "fixture"}]}
        storage._verify_best_custody(self.fixture.root, protected)
        with patch('bilqis_mlx.learning.capability_frontier.retire_bundles', return_value=()) as retired:
            storage._publish_boundary(self.fixture.root, protected, (), ())
        self.assertIn(pointer["filename"], retired.call_args.args[1])

    def test_retained_operator_external_run_is_not_rejected_by_pathname_custody(self):
        # Ordinary retained operation may live outside the checkout. The first
        # downstream source-preparation boundary proves pathname custody did not
        # block the run before normal operator preflight completed.
        from unittest.mock import patch
        with patch('bilqis_mlx.runtime.session.prepare_source',
                          side_effect=AssertionError("SOURCE_SHOULD_NOT_BE_LOADED")):
            with self.assertRaisesRegex(
                    AssertionError, "SOURCE_SHOULD_NOT_BE_LOADED"):
                storage.operate(
                    self.fixture.root, fixtures.SOURCE, fixtures.PARENT,
                    self.fixture.fixture.manifest, retention_enabled=True)

    def test_metadata_advance_never_carries_prior_generation_outbox(self):
        school = storage._state_from_json(self.receipt["school"], self.schedule_program)
        prior = list(self.receipt["delivery_outbox"])
        advanced = storage._advance(self.fixture.root, self.receipt, school)
        storage._reconcile_delivery_outbox(self.fixture.root, advanced)
        self.assertEqual(advanced["generation"], self.receipt["generation"] + 1)
        self.assertEqual(advanced["school"]["current_student"],
                         self.receipt["school"]["current_student"])
        self.assertEqual(self.receipt["delivery_outbox"], prior)
        self.assertEqual(advanced["delivery_outbox"][0]["generation"], advanced["generation"])

    def test_retained_parent_refresh_is_durable_and_leaves_routine_history_intact(self):
        from bilqis_mlx.generated_assessment import make_cohort
        from bilqis_mlx.fixed_frontier import load_frontier

        rows = [{"id": "fixed-0", "capability": "A.LINK", "gold": "TRUE"}]
        cohort = make_cohort(rows, generator_version="fixture", seed=7,
                             rubric_version="fixture-rubric")
        path = self.fixture.root / "cohorts" / (cohort.digest + ".json")
        path.parent.mkdir(exist_ok=True)
        path.write_text(json.dumps(dict(schema="fixture-rubric", rows=rows, seed=7,
            generator_version="fixture", cohort_sha256=cohort.digest)))
        student = self.receipt["school"]["current_student"]
        historical = dict(student_sha256="a"*64, optimizer_step=0,
            scores={"A.LINK": {"correct": 1, "total": 1}}, misses_for_teacher=[],
            cohort_sha256=cohort.digest, cohort_file=f"cohorts/{cohort.digest}.json")
        saved = {**self.receipt, "last_exam": historical}
        with patch('bilqis_mlx.learning.student_ops._predictions', return_value={"fixed-0": "FALSE"}):
            updated = storage._refresh_fixed_frontier(
                self.mx, self.fixture.root, saved, self.course,
                self.fixture.params, self.fixture.optimizer)
        self.assertEqual(updated["last_exam"], historical)
        self.assertEqual(updated["school"]["current_student"], student)
        self.assertEqual(updated, read_current(self.fixture.root))
        _, predictions = load_frontier(self.fixture.root, updated,
            parent_sha256=student["sha256"], parent_optimizer_step=student["optimizer_step"])
        self.assertEqual(predictions, {"fixed-0": "FALSE"})
        self.assertEqual(storage._refresh_fixed_frontier(
            self.mx, self.fixture.root, updated, self.course,
            self.fixture.params, self.fixture.optimizer), updated)
        school = storage._state_from_json(updated["school"], self.schedule_program)
        replaced = storage._advance(self.fixture.root, updated, school,
                                    last_exam=historical, persist=False)
        self.assertNotIn("fixed_frontier_exam", replaced)

    def test_first_staircase_visit_stop_and_resume_persists_context_and_own_adamw(self):
        # Regression for a pre-existing ff64 bug: before its first Grade C
        # exam, last_exam is legitimately None. A human stop must still
        # publish the complete live model/optimizer and candidate receipts.
        with redirect_stdout(io.StringIO()):
            changed=self.visit()
            saved=storage._flush_working_student(
                self.mx,self.fixture.root,changed,self.fixture.fixture.manifest,
                self.course,self.fixture.params,self.fixture.optimizer,
                self.fixture.graph,reserve_gib=0.,source_root=self.source_root)
            parameters,own_adamw,graph,reloaded=self.resume()
        self.assertEqual(saved,reloaded)
        self.assertEqual(reloaded["teacher"]["causal_experiment"]["events"],1)
        self.assertEqual(reloaded["learning_experiment"]["version"],
                         "bilqis.mlx.causal-teacher-experiment/v1")
        self.assertEqual(int(own_adamw.state["step"].item()),
                         int(self.fixture.optimizer.state["step"].item()))
        self.assertEqual(set(parameters),set(self.fixture.params))
        self.assertEqual(graph,self.fixture.graph)
