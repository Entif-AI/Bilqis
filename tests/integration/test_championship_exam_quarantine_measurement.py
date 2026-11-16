"""Normal exams mint advisory champions before whole-grade graduation."""
from contextlib import ExitStack
from dataclasses import asdict, replace
import json
from pathlib import Path
from types import SimpleNamespace
from tempfile import TemporaryDirectory
from unittest import TestCase
from unittest.mock import patch

from bilqis_mlx import trainer
from bilqis_mlx.boolean_composite import build_course as build_composite
from bilqis_mlx.boolean_identification import (
    answer_heads as idboolops_answer_heads,
    build_course as build_idboolops,
    draw_identification,
)
from bilqis_mlx.generated_assessment import make_cohort
from bilqis_mlx.grade_a_probe import read_sources
from bilqis_mlx.live_grade_c import answer_heads as numeric_answer_heads
from bilqis_mlx.live_grade_c import registry_graph as numeric_registry_graph
from bilqis_mlx.grade_a_release import accepted_grade_a
from bilqis_mlx.factory.live_releases import initial_course
from bilqis_mlx.factory.live_releases import boolean_successor
from bilqis_mlx.curriculum.scheduler import start_new
from bilqis_mlx.compatibility.schedule_program import (
    schedule_program_from_legacy_course,
)
from bilqis_mlx.factory.schedule import (
    ScheduleCapability, ScheduleGrade, ScheduleProgram,
)
from bilqis_mlx.learning.champions import Checkpoint
from bilqis_mlx.learning.champion_confidence import perfect_role_roster
from bilqis_mlx.learning.epoch_championships import active_frontier
from bilqis_mlx.learning.grade_soup import grade_soup_recipe
from bilqis_mlx.learning.championship_witnesses import battery_from_exam, verified_battery

from tests.integration.test_championship_exam import (
    _cohort_pointer, _exam_patches, _exam_receipt, _fake_executable_release,
    _synthetic_exam_cohort,
    _perfect_predictions, _synthetic_program, _take_inert_exam,
)


class ChampionshipExamQuarantineMeasurementTests(TestCase):
    def test_quarantining_entire_later_grade_keeps_cumulative_grade_rubric(self):
        root = Path(__file__).resolve().parents[2]
        manifest = json.loads((root / "docs/provenance/GRADE_A_CANDIDATE_MANIFEST_V2.json").read_text())
        course_a = initial_course(accepted_grade_a(manifest))
        course = boolean_successor(course_a, root / "vendor/legacy-v16")
        student = Checkpoint("a" * 64, "bundles/disposable", 10, True)
        school = replace(
            start_new(course, student), grade_index=1, stage="ASSESS_MAIN", queue=(),
            champions={"A": student})
        rubric, release, generator, _ = trainer._cohort_contract(course)
        caps = tuple(cap.id for grade in course.grades for cap in grade.capabilities)
        blocked = tuple(cap.id for cap in course.grades[-1].capabilities)
        candidate = _synthetic_exam_cohort(
            caps, seed=31, generator_version=generator, rubric_version=release)
        routine = _synthetic_exam_cohort(
            caps, seed=32, generator_version=generator, rubric_version=release)

        def filtered(*args):
            source = args[-2]
            selected = make_cohort(
                [row for row in source.rows if row["capability"] not in set(blocked)],
                generator_version=source.generator_version, seed=source.seed,
                rubric_version=rubric)
            return selected, "unused"

        graph = {"tokens": ["PAD"]}
        parameter_shapes = {"embedding.weight": [1, 1]}
        release_sha = "f" * 64
        receipt = _exam_receipt(
            school=school, run_id="inert-whole-grade-quarantine",
            release=release, manifest=manifest, course=course, graph=graph,
            parameter_shapes=parameter_shapes, release_sha=release_sha,
            championship_origins={student.sha256: "A"})
        with TemporaryDirectory() as temp:
            for source_cohort in (candidate, routine):
                trainer._persist_live_cohort(Path(temp), manifest, course, source_cohort)
            program = schedule_program_from_legacy_course(course)
            executable_release = _fake_executable_release(course)
            selected = filtered(None, None, None, routine, None)[0]
            patches = _exam_patches(
                executable_release=executable_release, program=program,
                routine=selected, candidate=selected, school=school,
                predict=_perfect_predictions,
                extra={
                    "_routine_executable_cohort": lambda *_a, **_k: (
                        selected, {**_cohort_pointer(selected, program),
                                   "rubric_sha256": rubric}),
                    "quarantined_capabilities": lambda *_: blocked,
                })
            completed = _take_inert_exam(
                temp=temp, receipt=receipt, manifest=manifest, course=course,
                root=root, graph=graph, patches=patches, rubric_sha256=rubric)

        self.assertEqual(completed["last_exam"]["exam_rubric_sha256"], rubric)
        self.assertEqual(set(completed["last_exam"]["withheld_capabilities"]), set(blocked))

    def test_newly_quarantined_after_measurement_is_not_retroactively_unmeasured(self):
        root = Path(__file__).resolve().parents[2]
        manifest = json.loads((root / "docs/provenance/GRADE_A_CANDIDATE_MANIFEST_V2.json").read_text())
        course_a = initial_course(accepted_grade_a(manifest))
        course = boolean_successor(course_a, root / "vendor/legacy-v16")
        student = Checkpoint("a" * 64, "bundles/disposable", 10, True)
        school = replace(
            start_new(course, student), grade_index=1, stage="ASSESS_MAIN", queue=(),
            champions={"A": student})
        rubric, release, generator, _ = trainer._cohort_contract(course)
        cohort_rubric = course.grades[-1].assessment_sha256
        caps = tuple(cap.id for grade in course.grades for cap in grade.capabilities)
        blocked_after = "A.LINK"
        candidate = _synthetic_exam_cohort(
            caps, seed=21, generator_version=generator,
            rubric_version=cohort_rubric)
        routine = _synthetic_exam_cohort(
            caps, seed=22, generator_version=generator,
            rubric_version=cohort_rubric)
        program = schedule_program_from_legacy_course(course)
        executable_release = _fake_executable_release(course)

        def advance_after(**kwargs):
            return (kwargs["stagnation"], [], kwargs["routine_advanced"],
                    (blocked_after,))

        graph = {"tokens": ["PAD"]}
        parameter_shapes = {"embedding.weight": [1, 1]}
        release_sha = "f" * 64
        receipt = _exam_receipt(
            school=school, run_id="inert-blocked-after", release=release,
            manifest=manifest, course=course, graph=graph,
            parameter_shapes=parameter_shapes, release_sha=release_sha,
            championship_origins={student.sha256: "A"})
        patches = _exam_patches(
            executable_release=executable_release, program=program,
            routine=routine, candidate=candidate, school=school,
            predict=_perfect_predictions,
            extra={
                "quarantined_capabilities": lambda *_: (),
                "_advance_stagnation_after_routine": advance_after,
                "_promotion_due_after_routine": lambda *_a, **_k: False,
            })
        with TemporaryDirectory() as temp:
            completed = _take_inert_exam(
                temp=temp, receipt=receipt, manifest=manifest, course=course,
                root=root, graph=graph, patches=patches,
                rubric_sha256=cohort_rubric)

        self.assertIn(blocked_after, completed["mentor_epoch"]["active_roles"])
        self.assertNotIn(blocked_after, completed["last_exam"]["withheld_capabilities"])
        self.assertIn(blocked_after, completed["last_exam"]["stagnation_quarantined"])



if __name__ == "__main__":
    import unittest
    unittest.main()
