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


class ChampionshipExamIncumbentWitnessesTests(TestCase):
    def test_older_incumbent_competes_on_complete_readable_grade_without_claiming_school_score(self):
        old = {"tokens": ["PAD", "TRUE"], "nodes": [0, 1], "row_contract_sha256": {}}
        graph = {"tokens": ["PAD", "TRUE", "NEW"], "nodes": [0, 1, 2], "row_contract_sha256": {}}
        pointer = {"filename": "bundles/old", "sha256": "a" * 64,
                   "optimizer_step": 10, "model_and_native_adamw": True}
        current = Checkpoint("b" * 64, "bundles/current", 20, True)
        course = SimpleNamespace(grades=[
            SimpleNamespace(id=g, assessment_sha256="d" * 64,
                            capabilities=[SimpleNamespace(id=c)])
            for g, c in (("A", "A.X"), ("C", "C.NEW"))])
        cohort = make_cohort([
            {"id": f"{cap}:{i}", "capability": cap, "gold": "TRUE", "tokens": [token]}
            for cap, token in (("A.X", 1), ("C.NEW", 2)) for i in range(2)],
            generator_version="fixture", seed=7, rubric_version="fixture")
        receipt = {"config": {}, "answer_ids": [1], "source_manifest_sha256": "c" * 64,
                   "championship_school_identity": {"sha256": "f" * 64},
                   "championship_checkpoint_origins": {"b" * 64: "A"},
                   "mentor_epoch": {"introduced_grade": "C", "source_graph_sha256": trainer._fingerprint(graph),
                                    "championship_school_identity": {"sha256": "f" * 64},
                                    "active_roles": {"A.X": {"capability": "A.X", "correct": 1, "total": 2,
                                                               "origin_grade": "A",
                                                               "checkpoint": pointer}}}}
        scores = {cap: {"correct": 2, "total": 2} for cap in ("A.X", "C.NEW")}
        program = _synthetic_program(
            (("A", ("A.X",)), ("C", ("C.NEW",))))
        with (
            TemporaryDirectory() as temp,
            patch('bilqis_mlx.curriculum.scheduler.assessment_capabilities', return_value=tuple(scores)),
            patch('bilqis_mlx.runtime.admission._read_executable_factory_release_artifact',
                return_value=SimpleNamespace()),
            patch('bilqis_mlx.factory.schedule.schedule_program_from_executable_release',
                return_value=program),
            patch(
                "bilqis_mlx.factory.assessment.assessment_scope_contract",
                return_value=SimpleNamespace(rubric_sha256="d" * 64)),
            patch('bilqis_mlx.runtime.mlx_checkpoint.load_semantically_bound_bundle', return_value=(
                {}, None, {"safetensors_sha256": "a" * 64, "optimizer_step": 10}, old)),
            patch('bilqis_mlx.learning.student_ops._predictions', side_effect=lambda _m, _w, rows, *_: {
                row["id"]: row["gold"] for row in rows}) as inference,
        ):
            _, _, incumbents = trainer._epoch_paired_examinations(
                None, Path(temp), receipt, course,
                SimpleNamespace(current_student=current, grade="A"),
                cohort, scores, {r["id"]: r["gold"] for r in cohort.rows}, graph)
        self.assertEqual(set(incumbents["a" * 64]["scores"]), {"A.X"})
        self.assertEqual({r["capability"] for r in inference.call_args.args[2]}, {"A.X"})

    def test_title_grade_selects_incumbent_panel_independent_of_checkpoint_origin(self):
        old = {"tokens": ["PAD", "TRUE"], "nodes": [0, 1], "row_contract_sha256": {}}
        graph = {"tokens": ["PAD", "TRUE"], "nodes": [0, 1], "row_contract_sha256": {}}
        incumbent = {"filename": "bundles/old", "sha256": "a" * 64,
                     "optimizer_step": 10, "model_and_native_adamw": True}
        current = Checkpoint("b" * 64, "bundles/current", 20, True)
        course = SimpleNamespace(grades=[
            SimpleNamespace(id="A", assessment_sha256="d" * 64,
                            capabilities=[SimpleNamespace(id="A.X")]),
            SimpleNamespace(id="B", assessment_sha256="d" * 64,
                            capabilities=[SimpleNamespace(id="B.X")]),
        ])
        cohort = make_cohort([
            {"id": f"{cap}:{i}", "capability": cap, "gold": "TRUE", "tokens": [1]}
            for cap in ("A.X", "B.X") for i in range(2)],
            generator_version="fixture", seed=8, rubric_version="fixture")
        receipt = {
            "config": {}, "answer_ids": [1], "source_manifest_sha256": "c" * 64,
            "championship_school_identity": {"sha256": "f" * 64},
            "championship_checkpoint_origins": {"b" * 64: "A"},
            "mentor_epoch": {
                "introduced_grade": "B",
                "source_graph_sha256": trainer._fingerprint(graph),
                "championship_school_identity": {"sha256": "f" * 64},
                "active_roles": {
                    "B.X": {"capability": "B.X", "correct": 1, "total": 2,
                            "origin_grade": "B", "checkpoint": incumbent},
                },
            },
        }
        scores = {cap: {"correct": 2, "total": 2} for cap in ("A.X", "B.X")}
        program = _synthetic_program(
            (("A", ("A.X",)), ("B", ("B.X",))))
        with (
            TemporaryDirectory() as temp,
            patch('bilqis_mlx.curriculum.scheduler.assessment_capabilities', return_value=tuple(scores)),
            patch('bilqis_mlx.runtime.admission._read_executable_factory_release_artifact',
                return_value=SimpleNamespace()),
            patch('bilqis_mlx.factory.schedule.schedule_program_from_executable_release',
                return_value=program),
            patch(
                "bilqis_mlx.factory.assessment.assessment_scope_contract",
                return_value=SimpleNamespace(rubric_sha256="d" * 64)),
            patch('bilqis_mlx.runtime.mlx_checkpoint.load_semantically_bound_bundle', return_value=(
                {}, None, {"safetensors_sha256": "a" * 64, "optimizer_step": 10}, old)),
            patch('bilqis_mlx.learning.student_ops._predictions', side_effect=lambda _m, _w, rows, *_: {
                row["id"]: row["gold"] for row in rows}) as inference,
        ):
            _, challenger, incumbents = trainer._epoch_paired_examinations(
                None, Path(temp), receipt, course,
                SimpleNamespace(current_student=current, grade="A"),
                cohort, scores, {r["id"]: r["gold"] for r in cohort.rows}, graph,
                challenge_grade="B")
        self.assertEqual(challenger["challenge_grade"], "B")
        self.assertEqual(challenger["checkpoint_origin_grade"], "A")
        self.assertEqual(set(incumbents["a" * 64]["scores"]), {"B.X"})
        self.assertEqual({r["capability"] for r in inference.call_args.args[2]}, {"B.X"})

    def test_legacy_earning_witness_preserves_compatible_historical_graph(self):
        old = {"tokens": ["PAD", "TRUE"], "nodes": [0, 1],
               "row_contract_sha256": {"PAD": "p", "TRUE": "t"}}
        current = {"tokens": old["tokens"] + ["NEW"], "nodes": [0, 1, 2],
                   "row_contract_sha256": {**old["row_contract_sha256"], "NEW": "n"}}
        rows = [{"id": "x0", "capability": "A.X", "gold": "TRUE", "tokens": [1]},
                {"id": "x1", "capability": "A.X", "gold": "FALSE", "tokens": [1]}]
        cohort = make_cohort(rows, generator_version="fixture", seed=1, rubric_version="fixture")
        pointer = {"filename": "bundles/old", "sha256": "a" * 64,
                   "optimizer_step": 10, "model_and_native_adamw": True}
        role = {"capability": "A.X", "cohort_sha256": cohort.digest,
                "rubric": "b" * 64, "correct": 1, "total": 2, "checkpoint": pointer}
        epoch = {"active_roles": {"A.X": role}}
        receipt = {"source_manifest_sha256": "c" * 64, "config": {}, "answer_ids": [1]}
        with TemporaryDirectory() as temp:
            root = Path(temp)
            (root / "cohorts").mkdir()
            (root / "cohorts" / (cohort.digest + ".json")).write_text(json.dumps({
                "cohort_sha256": cohort.digest, "rubric_sha256": "b" * 64,
                "source_manifest_sha256": "c" * 64, "schema": "fixture",
                "generator_version": "fixture", "seed": 1, "rows": rows}))
            bundle = root / pointer["filename"]
            bundle.mkdir(parents=True)
            (bundle / "model-and-own-adamw.safetensors").write_bytes(b"inert fixture")
            with (patch('bilqis_mlx.learning.lesson_guidance._cached_frozen_champion', return_value=({}, old)),
                  patch('bilqis_mlx.learning.student_ops._predictions', return_value={"x0": "TRUE", "x1": "WRONG"})):
                hydrated = trainer._hydrate_championship_witnesses(
                    None, root, receipt, epoch, current)
            proof = hydrated["active_roles"]["A.X"]["qualification_witnesses"][0]
            self.assertEqual(proof["source_graph_sha256"], trainer._fingerprint(old))
            self.assertEqual({q["id"] for q in proof["questions"]}, {"x0", "x1"})
            self.assertNotIn("qualification_witnesses", role)
            role = hydrated["active_roles"]["A.X"]
            battery = verified_battery(role)
            self.assertEqual({q["id"] for segment in battery for q in segment["questions"]},
                             {"x0", "x1"})
            with patch('bilqis_mlx.learning.student_ops._predictions', side_effect=[
                    {"x0": "TRUE", "x1": "FALSE"},
                    {"x0": "WRONG", "x1": "FALSE"}]) as infer:
                first = trainer._fresh_battery_results(None, root, receipt, role, {}, old)
                second = trainer._fresh_battery_results(None, root, receipt, role, {}, old)
            self.assertEqual(infer.call_count, 2)
            self.assertNotEqual(first, second)



if __name__ == "__main__":
    import unittest
    unittest.main()
