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
    _exam_patches, _exam_receipt, _fake_executable_release, _synthetic_exam_cohort,
    _synthetic_program, _take_inert_exam,
)


class ChampionshipExamFreshTitleRolesTests(TestCase):
    def test_fresh_battery_batches_verified_segments_into_one_model_inference(self):
        graph = {"tokens": ["PAD", "TRUE"], "nodes": [0, 1],
                 "row_contract_sha256": {}}
        receipt = {"source_manifest_sha256": "c" * 64,
                   "config": {}, "answer_ids": [1]}
        contexts = []
        cohorts = []
        for seed, prefix in ((1, "x"), (2, "y")):
            rows = [
                {"id": prefix + "0", "capability": "A.X",
                 "gold": "TRUE", "tokens": [1]},
                {"id": prefix + "1", "capability": "A.X",
                 "gold": "FALSE", "tokens": [1]},
            ]
            cohort = make_cohort(
                rows, generator_version="fixture", seed=seed,
                rubric_version="fixture")
            context = {
                "cohort_sha256": cohort.digest,
                "rubric_sha256": "d" * 64,
                "cohort_rubric_sha256": "d" * 64,
                "assessment_scope_sha256": "e" * 64,
                "source_graph_sha256": trainer._fingerprint(graph),
                "source_oracle_sha256": "c" * 64,
                "scores": {"A.X": {"correct": 2, "total": 2}},
                "questions": {"A.X": [
                    {"id": row["id"], "gold": row["gold"]} for row in rows]},
                "correct_questions": {"A.X": [
                    {"id": row["id"], "gold": row["gold"]} for row in rows]},
            }
            contexts.append(context)
            cohorts.append((cohort, rows))
        role = {
            "capability": "A.X",
            "surviving_battery": list(
                battery_from_exam(contexts[0], ("A.X",)) +
                battery_from_exam(contexts[1], ("A.X",))),
        }
        with TemporaryDirectory() as temp:
            root = Path(temp)
            (root / "cohorts").mkdir()
            for cohort, rows in cohorts:
                (root / "cohorts" / (cohort.digest + ".json")).write_text(
                    json.dumps({
                        "cohort_sha256": cohort.digest,
                        "rubric_sha256": "d" * 64,
                        "source_manifest_sha256": "c" * 64,
                        "schema": "fixture",
                        "generator_version": "fixture",
                        "seed": cohort.seed,
                        "rows": rows,
                    }))
            answers = {"x0": "TRUE", "x1": "FALSE",
                       "y0": "TRUE", "y1": "FALSE"}
            with patch('bilqis_mlx.learning.student_ops._predictions', return_value=answers) as infer:
                result = trainer._fresh_battery_results(
                    None, root, receipt, role, {}, graph)

        self.assertEqual(infer.call_count, 1)
        self.assertEqual(len(infer.call_args.args[2]), 4)
        self.assertEqual(set(result), {
            segment["sha256"] for segment in role["surviving_battery"]})
        self.assertTrue(all(len(correct) == 2 for correct in result.values()))

    def test_title_match_reinfers_both_models_for_current_panel_and_battery(self):
        graph = {"tokens": ["PAD", "TRUE"], "nodes": [0, 1],
                 "row_contract_sha256": {}}
        rows = [{"id": "x0", "capability": "A.X", "gold": "TRUE", "tokens": [1]},
                {"id": "x1", "capability": "A.X", "gold": "FALSE", "tokens": [1]}]
        cohort = make_cohort(rows, generator_version="fixture", seed=1,
                             rubric_version="d" * 64)
        incumbent = {"filename": "bundles/old", "sha256": "a" * 64,
                     "optimizer_step": 10, "model_and_native_adamw": True}
        challenger_pointer = {"filename": "bundles/new", "sha256": "b" * 64,
                              "optimizer_step": 11, "model_and_native_adamw": True}
        context = {
            "cohort_sha256": cohort.digest, "rubric_sha256": "d" * 64,
            "cohort_rubric_sha256": "d" * 64,
            "assessment_scope_sha256": "e" * 64,
            "source_graph_sha256": trainer._fingerprint(graph),
            "source_oracle_sha256": "c" * 64,
        }
        earning = {
            **context, "checkpoint": incumbent,
            "scores": {"A.X": {"correct": 2, "total": 2}},
            "questions": {"A.X": [{"id": r["id"], "gold": r["gold"]} for r in rows]},
            "correct_questions": {
                "A.X": [{"id": r["id"], "gold": r["gold"]} for r in rows]},
        }
        role = {
            "capability": "A.X", "checkpoint": incumbent,
            "surviving_battery": list(battery_from_exam(earning, ("A.X",))),
        }
        epoch = {"active_roles": {"A.X": role}}
        challenger = {
            **context, "checkpoint": challenger_pointer,
            "scores": {"A.X": {"correct": 2, "total": 2}},
            "questions": earning["questions"],
            "correct_questions": earning["correct_questions"],
        }
        receipt = {"source_manifest_sha256": "c" * 64,
                   "config": {}, "answer_ids": [1]}
        with TemporaryDirectory() as temp:
            root = Path(temp)
            (root / "cohorts").mkdir()
            (root / "cohorts" / (cohort.digest + ".json")).write_text(json.dumps({
                "cohort_sha256": cohort.digest, "rubric_sha256": "d" * 64,
                "source_manifest_sha256": "c" * 64, "schema": "d" * 64,
                "generator_version": "fixture", "seed": 1, "rows": rows}))
            predictions = [
                {"x0": "TRUE", "x1": "FALSE"},   # incumbent fresh current
                {"x0": "WRONG", "x1": "FALSE"},  # contender fresh current
                {"x0": "WRONG", "x1": "FALSE"},  # incumbent fresh battery
                {"x0": "TRUE", "x1": "FALSE"},   # contender fresh battery
            ]
            with (patch('bilqis_mlx.runtime.mlx_checkpoint.load_semantically_bound_bundle', return_value=(
                    {}, None, {"safetensors_sha256": "a" * 64,
                               "optimizer_step": 10}, graph)),
                  patch('bilqis_mlx.learning.student_ops._predictions', side_effect=predictions) as infer):
                match = trainer._fresh_title_match(
                    None, root, receipt, epoch, cohort, challenger, {}, graph, "A.X")
        self.assertEqual(infer.call_count, 4)
        self.assertEqual(match["incumbent_current_exam"]["scores"]["A.X"]["correct"], 2)
        self.assertEqual(match["challenger_current_exam"]["scores"]["A.X"]["correct"], 1)
        segment = role["surviving_battery"][0]["sha256"]
        self.assertEqual(len(match["battery_results"]["a" * 64][segment]), 1)
        self.assertEqual(len(match["battery_results"]["b" * 64][segment]), 2)

    def test_fresh_nonflash_exam_earns_roles_and_max_votes_without_graduation(self):
        root = Path(__file__).resolve().parents[2]
        manifest = json.loads((root / "docs/provenance/GRADE_A_CANDIDATE_MANIFEST_V2.json").read_text())
        course = initial_course(accepted_grade_a(manifest))
        student = Checkpoint("a" * 64, "bundles/disposable", 10, True)
        school = replace(start_new(course, student), stage="ASSESS_MAIN", queue=())
        rubric, release, generator, _ = trainer._cohort_contract(course)
        cohort_rubric = course.grades[-1].assessment_sha256
        caps = tuple(cap.id for cap in course.grades[0].capabilities)
        candidate = _synthetic_exam_cohort(
            caps, seed=1, generator_version=generator,
            rubric_version=cohort_rubric)
        routine = _synthetic_exam_cohort(
            caps, seed=2, generator_version=generator,
            rubric_version=cohort_rubric)
        program = schedule_program_from_legacy_course(course)
        executable_release = _fake_executable_release(course)

        def predict(_mx, _parameters, rows, *_):
            return {r["id"]: r["gold"] if (
                int(r["id"].split(":")[-1]) < 8 or
                (r["id"].startswith("2:") and r["capability"] == caps[0]))
                else "WRONG" for r in rows}

        def soups(_mx, _run, _receipt, frontier, _course, _graph, **_kwargs):
            recipe = grade_soup_recipe(frontier, "A", caps)
            return {"A": recipe}, ("A",)

        graph = {"tokens": ["PAD"]}
        parameter_shapes = {"embedding.weight": [1, 1]}
        release_sha = "f" * 64
        receipt = _exam_receipt(
            school=school, run_id="inert", release=release, manifest=manifest,
            course=course, graph=graph, parameter_shapes=parameter_shapes,
            release_sha=release_sha, championship_origins={})
        patches = _exam_patches(
            executable_release=executable_release, program=program,
            routine=routine, candidate=candidate, school=school,
            predict=predict, cook_soups=soups)
        with TemporaryDirectory() as temp:
            completed = _take_inert_exam(
                temp=temp, receipt=receipt, manifest=manifest, course=course,
                root=root, graph=graph, patches=patches,
                rubric_sha256=cohort_rubric)
        self.assertEqual(completed["last_exam"]["exam_plane"], "ROUTINE")
        self.assertEqual(
            set(completed["mentor_epoch"]["active_roles"]),
            {caps[0]},
            "sub-90% measurements must not mint championship roles",
        )
        self.assertEqual(completed["school"]["champions"], {})
        epoch = completed["mentor_epoch"]
        votes = perfect_role_roster(active_frontier(epoch), epoch["active_grade_soups"])
        self.assertEqual(votes[0]["capabilities"], (caps[0],))
        self.assertIn(caps[0], completed["last_exam"]["championship_roles"])



if __name__ == "__main__":
    import unittest
    unittest.main()
