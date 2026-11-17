"""Neural-inert C-to-H runway over one precompiled, fixed-ABI lineage."""
from dataclasses import asdict
import io
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from tests.system.factory_grade_z.fixture import check as _check, rows as _rows
from bilqis_mlx.curriculum import AnswerFamily, BINARY
from bilqis_mlx.curriculum.scheduler import (
    Assessment, Score, assess, assessment_capabilities, start_new, visit,
)
from bilqis_mlx.factory.adapters import RegisteredSourceAdapter, SourceAdapterRegistry
from bilqis_mlx.factory.answers import (
    AnswerModality, AnswerModalityRegistry, RegisteredAnswerModality, fixed_domain,
)
from bilqis_mlx.factory.curriculum_definition import (
    CapabilitySourceBinding, CapabilitySpec, CurriculumDefinition, GradeSpec,
    SourceBindingSet,
)
from bilqis_mlx.factory.executable_release import compile_executable_factory_release
from bilqis_mlx.factory.execution import CurriculumProfile, GradeProfile
from bilqis_mlx.factory.model import SourceAdapter
from bilqis_mlx.factory.schedule import schedule_program_from_executable_release
from bilqis_mlx.learning.champions import Checkpoint
from bilqis_mlx.learning.epoch_championships import advance_epoch
from bilqis_mlx.learning.mentor_epoch import begin_initial_epoch
from bilqis_mlx.presentation.school_telemetry import LETTER_TABLES, SchoolTelemetry
from bilqis_mlx.presentation.spiral_dashboard import Dashboard
from bilqis_mlx.runtime.admission import (
    _executable_factory_admission, _require_executable_factory_admission,
)
from bilqis_mlx.runtime.assessment import _routine_executable_cohort
from bilqis_mlx.runtime.release_adoption import _profile_transition
from bilqis_mlx.runtime.state import _fingerprint, _state_from_json


SIZES = (("C", 8), ("D", 9), ("E", 10), ("F", 11), ("G", 12), ("H", 8))


def _prepare_runway():
    grades = tuple(GradeSpec(
        grade, tuple(CapabilitySpec(
            f"{grade}.S{index}", "synthetic-runway",
            (f"runway.{grade}.{index}",), (f"runway.{grade}.{index}",),
            (), (), (AnswerFamily("binary", BINARY),))
            for index in range(size)),
        tuple((f"{grade}.S{index}", 12) for index in range(size)))
        for grade, size in SIZES)
    curriculum = CurriculumDefinition("fixture.runway/v2", grades, program_complete=True)
    bindings = SourceBindingSet(tuple(CapabilitySourceBinding(
        capability.capability_id, "repo:fixture/runway", "runway.generator/v1",
        "runway.oracle/v1") for grade in grades for capability in grade.capabilities),
        source_attestation_sha256="b" * 64)
    registry = SourceAdapterRegistry((RegisteredSourceAdapter(
        SourceAdapter("runway.adapter/v1", "runway.generator/v1",
                      ("runway.oracle/v1",), "d" * 64),
        _rows, _check, semantic_footprint=lambda row:
        curriculum.capability_map[row["capability"]].taught_roots),))
    answers = AnswerModalityRegistry((RegisteredAnswerModality(
        AnswerModality("binary", "runway.binary/v1", "e" * 64),
        fixed_domain(BINARY), lambda value: "cogal.value." + value.lower()),))
    graph = {"tokens": ["fixture.padding", "cogal.value.false", "cogal.value.true"]}
    releases = []
    for cutoff in range(1, len(grades) + 1):
        release = compile_executable_factory_release(
            curriculum, bindings,
            CurriculumProfile(f"runway/{cutoff}", tuple(
                GradeProfile(grade.grade_id, enabled_capabilities=(
                    None if position < cutoff else ()))
                for position, grade in enumerate(grades))),
            registry, answers, source_root=None, graph=graph,
            verification_seed=101, predecessor=releases[-1] if releases else None)
        releases.append(release)
    return tuple(releases), registry, graph


class SyntheticMultiSuccessorProof(unittest.TestCase):
    def _cold_admit(self, root, release, school, graph):
        _, release_file, admission = _executable_factory_admission(
            root, release, school.current_student, _fingerprint(graph), graph)
        receipt = {
            "factory_release_sha256": release.release_sha256,
            "factory_release_file": release_file,
            "factory_admission_v2": asdict(admission),
            "semantic_graph_sha256": _fingerprint(graph),
            "school": asdict(school),
        }
        path = root / "state.json"
        path.write_text(json.dumps(receipt), encoding="utf-8")
        receipt = json.loads(path.read_text(encoding="utf-8"))
        cold = _require_executable_factory_admission(root, receipt, graph)
        program = schedule_program_from_executable_release(cold)
        state = _state_from_json(receipt["school"], program)
        self.assertEqual(cold, release)
        self.assertEqual(state, school)
        return cold, program, state

    def _run_to_boundary(self, program, school, weak, student, *, stop_after_exam=False):
        expected = tuple(cap.id for grade in program.grades for cap in grade.capabilities)
        for turn in range(2000):
            self.assertEqual(school.current_student, student)
            if school.stage in ("AWAITING_NEXT_GRADE_WITH_DEBT", "WHOLE_SCHOOL_MASTERED"):
                return school
            if school.stage.startswith("ASSESS_"):
                scope = assessment_capabilities(program, school)
                self.assertEqual(scope, expected)
                scores = {cap: Score(11 if cap in weak else 12, 12) for cap in scope}
                snapshot = Assessment(
                    student.sha256, student.optimizer_step, program.digest(),
                    program.grades[-1].assessment_sha256, scores, f"runway-{turn}")
                school = assess(program, school, snapshot)
                if stop_after_exam:
                    return school
            else:
                self.assertTrue(school.queue, school.stage)
                school = visit(program, school, school.queue[0], student)
        self.fail("Runway failed to reach a bounded scheduler boundary")

    def _final_smoke(self, root, release, registry, graph, student, school):
        cohort, pointer = _routine_executable_cohort(
            root, {"run_id": "synthetic-runway", "generation": 7},
            {"manifest_sha256": "b" * 64}, release, registry, None, graph,
            capabilities=tuple(release.execution_plan.capability_map), assessment_epoch=0)
        rows = cohort.rows
        grades = {grade.grade_id: grade.capabilities
                  for grade in release.execution_plan.grades}
        scope = tuple(cap for capabilities in grades.values() for cap in capabilities)
        self.assertEqual(len(rows), sum(size for _, size in SIZES) * 12)
        self.assertTrue(all(_check(row) for row in rows))
        cohort_sha = cohort.digest
        scope_sha = _fingerprint(scope)
        program = schedule_program_from_executable_release(release)
        rubric = program.grades[-1].assessment_sha256
        scores = {cap: {"correct": 12, "total": 12} for cap in scope}
        questions = {cap: [{"id": row["id"], "gold": row["gold"]}
                           for row in rows if row["capability"] == cap] for cap in scope}
        exam = {
            "cohort_sha256": cohort_sha, "rubric_sha256": rubric,
            "cohort_rubric_sha256": rubric, "assessment_scope_sha256": scope_sha,
            "source_graph_sha256": _fingerprint(graph),
            "source_oracle_sha256": "b" * 64, "challenge_group": "H",
            "checkpoint_origin_group": "H", "challenge_grade": "H",
            "checkpoint_origin_grade": "H", "checkpoint": asdict(student),
            "scores": scores, "questions": questions, "correct_questions": questions,
        }
        epoch = begin_initial_epoch(
            student=asdict(student), introduced_grade="H",
            source_graph_sha256=_fingerprint(graph), frontier={}, soups={})
        epoch, changed, _ = advance_epoch(
            epoch, capability_groups=grades, challenger_exam=exam, incumbent_exams={})
        self.assertEqual(set(changed), set(grades["H"]))
        self.assertEqual(set(epoch["active_roles"]), set(grades["H"]))
        board = Dashboard(stream=io.StringIO(), redraw=False, tables=LETTER_TABLES,
                          show_all_panels=True)
        telemetry = SchoolTelemetry(board, active_grades=tuple(grades))
        telemetry.ingest({
            "event": "SCHOOL_LIVE_EXAM_COMMITTED", "grade": "H", "generation": 7,
            "rubric": rubric, "assessment_scope_sha256": scope_sha,
            "optimizer_step": student.optimizer_step, "student_sha256": student.sha256,
            "cohort_sha256": cohort_sha, "cohort_file": pointer["cohort_file"],
            "generator_version": cohort.generator_version,
            "scores": scores, "phase": school.stage,
            "championship_epoch": {"earned_roles": list(changed),
                                   "cross_origin_decisions": []},
        })
        self.assertIn("H", telemetry.grades)
        self.assertTrue(any(row.get("grade") == "H"
                            for row in board.rows["GRADES & MASTERY"]))

    def test_six_precompiled_successors_preserve_checkpoint_and_clear_cumulative_debt(self):
        # Every release exists before learner state and without optimizer access.
        releases, registry, graph = _prepare_runway()
        self.assertEqual(tuple(len(r.execution_plan.grades[-1].capabilities)
                               for r in releases), tuple(size for _, size in SIZES))
        student = Checkpoint("1" * 64, "bundles/runway-student", 7, True)
        program = schedule_program_from_executable_release(releases[0])
        school = start_new(program, student)
        frozen_graph = json.dumps(graph, sort_keys=True)
        weak = ()
        with tempfile.TemporaryDirectory() as directory, patch(
                "bilqis_mlx.factory.executable_release.compile_executable_factory_release",
                side_effect=AssertionError("Compilation after learner creation")):
            root = Path(directory)
            previous = None
            for index, release in enumerate(releases):
                with self.subTest(grade=SIZES[index][0]):
                    next_program = schedule_program_from_executable_release(release)
                    if previous is not None:
                        release.verify_successor_of(previous)
                        self.assertEqual(release.transition.semantic_geometry, "UNCHANGED")
                        self.assertEqual(release.semantic_catalog, previous.semantic_catalog)
                        school, revised, appended = _profile_transition(
                            program, next_program, school, mastery_debt=weak)
                        self.assertIsNone(revised)
                        self.assertTrue(appended)
                        self.assertEqual(school.carried_mastery_debt, weak)
                    cold, program, school = self._cold_admit(root, release, school, graph)
                    if previous is not None:
                        cold.verify_successor_of(previous)
                    weak += (f"{SIZES[index][0]}.S0",)
                    school = self._run_to_boundary(
                        program, school, weak, student,
                        stop_after_exam=index == len(releases) - 1)
                    if index < len(releases) - 1:
                        self.assertEqual(school.stage, "AWAITING_NEXT_GRADE_WITH_DEBT")
                    else:
                        self.assertNotEqual(school.stage, "WHOLE_SCHOOL_MASTERED")
                    self.assertEqual(school.carried_mastery_debt, weak)
                    self.assertEqual(school.champions, {})
                    cold, program, school = self._cold_admit(root, release, school, graph)
                    previous = cold
                    # The last release is complete; its weak exam cannot graduate.
                    if index == len(releases) - 1:
                        break
            school = self._run_to_boundary(program, school, (), student)
            self.assertEqual(school.stage, "WHOLE_SCHOOL_MASTERED")
            self.assertEqual(school.carried_mastery_debt, ())
            _, _, school = self._cold_admit(root, releases[-1], school, graph)
            self.assertEqual(school.current_student, student)
            self.assertEqual(json.dumps(graph, sort_keys=True), frozen_graph)
            self._final_smoke(root, releases[-1], registry, graph, student, school)
