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
    _perfect_predictions, _synthetic_exam_cohort,
    _synthetic_program, _take_inert_exam,
)


class ChampionshipExamScopeQuarantineTests(TestCase):
    def test_assessment_scope_hash_tracks_actual_scored_capabilities(self):
        full = ("A.IDENTITY", "A.LINK", "B.AND", "B.IFF")
        partial = {"A.IDENTITY": {}, "A.LINK": {}, "B.AND": {}}
        complete = {cap: {} for cap in full}
        self.assertEqual(
            trainer._assessment_scope_sha256(full, partial),
            trainer._fingerprint(("A.IDENTITY", "A.LINK", "B.AND")))
        self.assertEqual(
            trainer._assessment_scope_sha256(full, complete),
            trainer._fingerprint(full))
        self.assertNotEqual(
            trainer._assessment_scope_sha256(full, partial),
            trainer._assessment_scope_sha256(full, complete))

    def test_quarantine_b_and_does_not_suppress_complete_a_identity_title(self):
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
        blocked = "B.AND"
        identity_cap = "A.IDENTITY"
        routine = _synthetic_exam_cohort(
            caps, seed=12, generator_version=generator,
            rubric_version=cohort_rubric)
        program = schedule_program_from_legacy_course(course)
        executable_release = _fake_executable_release(course)
        routine_active = make_cohort(
            [row for row in routine.rows if row["capability"] != blocked],
            generator_version=routine.generator_version, seed=routine.seed,
            rubric_version=routine.rubric_version)

        graph = {"tokens": ["PAD"]}
        parameter_shapes = {"embedding.weight": [1, 1]}
        release_sha = "f" * 64
        receipt = _exam_receipt(
            school=school, run_id="inert-quarantine", release=release,
            manifest=manifest, course=course, graph=graph,
            parameter_shapes=parameter_shapes, release_sha=release_sha,
            championship_origins={student.sha256: "A"})
        patches = _exam_patches(
            executable_release=executable_release, program=program,
            routine=routine_active, candidate=routine_active, school=school,
            predict=_perfect_predictions,
            extra={"quarantined_capabilities": lambda *_: (blocked,)})
        with TemporaryDirectory() as temp:
            completed = _take_inert_exam(
                temp=temp, receipt=receipt, manifest=manifest, course=course,
                root=root, graph=graph, patches=patches,
                rubric_sha256=cohort_rubric)
        self.assertIn(identity_cap, completed["mentor_epoch"]["active_roles"])
        self.assertNotIn(blocked, completed["mentor_epoch"]["active_roles"])
        b_roles = [role for cap, role in completed["mentor_epoch"]["active_roles"].items()
                   if cap.startswith("B.") and cap != blocked]
        self.assertTrue(b_roles)
        protected = {item["sha256"] for item in trainer._mentor_epoch_references(completed)}
        self.assertTrue(all(role["checkpoint"]["sha256"] in protected
                            for role in b_roles))
        self.assertIn(blocked, completed["last_exam"]["withheld_capabilities"])



if __name__ == "__main__":
    import unittest
    unittest.main()
