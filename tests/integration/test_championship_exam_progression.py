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


class ChampionshipExamProgressionTests(TestCase):
    def test_spiral_grade_transition_is_not_promotion_authority(self):
        # Ordinary debt/recovery scheduling may move between grades without
        # satisfying the grade's qualification criterion. Only the scheduler's
        # authoritative exam-epoch advance may open promotion.
        before = SimpleNamespace(
            grade="C", stage="ASSESS_RECOVERY_2",
            revalidation_target_grade=None, grade_exam_epoch=7)
        after = SimpleNamespace(grade="A", revalidation_target_grade=None,
                                stage="MAIN", grade_exam_epoch=7)
        self.assertFalse(trainer._promotion_due_after_routine(before, after))
        self.assertFalse(trainer._promotion_due_after_routine(
            before, after, complete_assessment=False))

        qualified = SimpleNamespace(
            grade="A", revalidation_target_grade=None,
            stage="MAIN", grade_exam_epoch=8)
        self.assertTrue(trainer._promotion_due_after_routine(before, qualified))

    def test_mean_stability_debt_progression_is_not_championship_promotion(self):
        before = SimpleNamespace(
            grade="A", stage="ASSESS_PROMOTION_SWEEP",
            revalidation_target_grade=None, grade_exam_epoch=7)
        debt_advanced = SimpleNamespace(
            grade="B", stage="MAIN", revalidation_target_grade=None,
            champions={}, grade_exam_epoch=7)
        mastered = SimpleNamespace(
            grade="B", stage="MAIN", revalidation_target_grade=None,
            champions={"A": SimpleNamespace()}, grade_exam_epoch=8)

        self.assertFalse(
            trainer._promotion_due_after_routine(before, debt_advanced))
        self.assertTrue(
            trainer._promotion_due_after_routine(before, mastered))

    def test_developmental_promotion_does_not_launch_generalization(self):
        program = ScheduleProgram(
            program_digest="d" * 64,
            grades=(ScheduleGrade(
                "A", (ScheduleCapability("A.X", 12),), (), "e" * 64),),
            program_complete=False,
        )
        student = Checkpoint("a" * 64, "bundles/disposable", 10, True)
        school = replace(
            start_new(program, student),
            stage="ASSESS_PROMOTION_SWEEP", queue=(),
            promotion_sweep_scope=("A.X",),
            promotion_sweep_return_stage="ASSESS_MAIN",
            promotion_sweep_scores=(("A.X", 12, 12),),
            promotion_sweep_attempt_student_sha256=student.sha256,
            promotion_sweep_attempt_scope=("A.X",))
        rubric = program.grades[0].assessment_sha256
        routine = _synthetic_exam_cohort(
            ("A.X",), seed=1, generator_version="g" * 64,
            rubric_version=rubric)
        candidate = _synthetic_exam_cohort(
            ("A.X",), seed=2, generator_version="g" * 64,
            rubric_version=rubric)
        executable_release = SimpleNamespace(
            execution_plan=SimpleNamespace(capability_map={}))
        manifest = {"manifest_sha256": "b" * 64}
        graph = {"tokens": ["PAD"]}
        parameter_shapes = {"embedding.weight": [1, 1]}
        receipt = _exam_receipt(
            school=school, run_id="no-developmental-generalization",
            release="factory-test", manifest=manifest, course=program,
            graph=graph, parameter_shapes=parameter_shapes,
            release_sha="f" * 64, championship_origins={})

        def no_generalization(*_args, **_kwargs):
            raise AssertionError("developmental runtime invoked GENERALIZATION")

        def advance_stagnation(**kwargs):
            return kwargs["stagnation"], [], kwargs["routine_advanced"], ()

        patches = _exam_patches(
            executable_release=executable_release, program=program,
            routine=routine, candidate=candidate, school=school,
            predict=_perfect_predictions,
            extra={
                "_promotion_executable_cohort":
                    lambda *_a, **_k: (
                        routine, _cohort_pointer(routine, program)),
                "_generalization_executable_cohort": no_generalization,
                "_advance_stagnation_after_routine": advance_stagnation,
                "_bind_checkpoint_origin": lambda saved, *_a, **_k: saved,
                "_hydrate_championship_witnesses":
                    lambda _mx, _run, _receipt, epoch, _graph: epoch,
                "_advance_exam_championships":
                    lambda _mx, _run, _receipt, epoch, *_a, **_k:
                    (epoch, (), ()),
            })
        with TemporaryDirectory() as temp:
            completed = _take_inert_exam(
                temp=temp, receipt=receipt, manifest=manifest, course=program,
                root=Path(temp), graph=graph, patches=patches,
                rubric_sha256=rubric)

        self.assertEqual(completed["last_exam"]["exam_plane"], "PROMOTION")
        self.assertNotIn("generalization_cohort_sha256", completed["last_exam"])
        self.assertNotIn("generalization_passed", completed["last_exam"])

    def test_c_era_config_rebuilds_only_idboolops_heads_for_prefix_incumbent(self):
        root = Path(__file__).resolve().parents[2]
        source = root / "vendor/legacy-v16"
        _, _, prefix_graph, _, _ = read_sources(source)
        grown_graph = numeric_registry_graph()
        current_heads = numeric_answer_heads(grown_graph, 3)
        current_heads["boolean_operator"] = idboolops_answer_heads(grown_graph)[
            "boolean_operator"]
        current = {
            "heads": 3,
            "layers": 1,
            "answer_heads": current_heads,
        }

        compatible = trainer._compatible_answer_config(current, prefix_graph)
        rebuilt = compatible["answer_heads"]
        self.assertNotIn("numeric_active", rebuilt)
        self.assertEqual(rebuilt["boolean_operator"],
                         idboolops_answer_heads(prefix_graph)["boolean_operator"])
        self.assertEqual(len(rebuilt["semantic_token"]["values"]),
                         len(prefix_graph["tokens"]))
        self.assertTrue(all(
            token_id < len(prefix_graph["tokens"])
            for head in rebuilt.values() for token_id in head["token_ids"]))

    def test_idboolops_panel_is_readable_by_compatible_historical_graph(self):
        root = Path(__file__).resolve().parents[2]
        source = root / "vendor/legacy-v16"
        manifest = json.loads((
            root / "docs/provenance/GRADE_A_CANDIDATE_MANIFEST_V2.json").read_text())
        a = initial_course(accepted_grade_a(manifest))
        b = boolean_successor(a, source)
        course = build_idboolops(build_composite(b, source), source)
        _, _, graph, _, _ = read_sources(source)
        rows = draw_identification(source, graph, seed=113)
        cohort = make_cohort(
            rows, generator_version=course.grades[-1].capabilities[-1].lesson_generator,
            seed=113, rubric_version=course.grades[-1].assessment_sha256)
        receipt = {
            "answer_ids": [6, 7],
            "config": {"answer_heads": idboolops_answer_heads(graph)},
        }
        readable = trainer._readable_championship_rows(cohort, graph, receipt)
        self.assertEqual(readable, cohort.rows)
        self.assertEqual({row["answer_kind"] for row in readable}, {"boolean_operator"})
        self.assertEqual({row["capability"] for row in readable}, {"B.IDBOOLOPS"})

    def test_idboolops_live_exam_factor_guard_checks_declared_domain_not_provider_balance(self):
        root = Path(__file__).resolve().parents[2]
        source = root / "vendor/legacy-v16"
        manifest = json.loads((
            root / "docs/provenance/GRADE_A_CANDIDATE_MANIFEST_V2.json").read_text())
        course = build_idboolops(
            build_composite(boolean_successor(
                initial_course(accepted_grade_a(manifest)), source), source), source)
        _, _, graph, _, _ = read_sources(source)
        rows = draw_identification(source, graph, seed=117)
        cohort = make_cohort(
            rows, generator_version=course.grades[-1].capabilities[-1].lesson_generator,
            seed=117, rubric_version=course.grades[-1].assessment_sha256)
        idboolops = course.grades[-1].capabilities[-1]
        family = idboolops.answer_families[0]
        self.assertEqual(family.kind, "boolean_operator")
        self.assertEqual({row["gold"] for row in cohort.rows}, set(family.values))
        self.assertEqual(
            {value: sum(row["gold"] == value for row in cohort.rows)
             for value in family.values},
            {value: 2 for value in family.values})
        release = _fake_executable_release(course)
        self.assertTrue(trainer._live_exam_factors_complete(
            release, cohort, {"B.IDBOOLOPS": 12}))

        broken_rows = list(cohort.rows)
        broken_rows[-1] = {**broken_rows[-1], "gold": "XNOR"}
        broken = make_cohort(
            broken_rows, generator_version=cohort.generator_version,
            seed=cohort.seed, rubric_version=cohort.rubric_version)
        self.assertFalse(trainer._live_exam_factors_complete(
            release, broken, {"B.IDBOOLOPS": 12}))



if __name__ == "__main__":
    import unittest
    unittest.main()
