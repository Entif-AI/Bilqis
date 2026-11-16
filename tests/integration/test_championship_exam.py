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


def _fake_executable_release(course):
    return SimpleNamespace(execution_plan=SimpleNamespace(
        capability_map=course.capability_map))


def _cohort_pointer(cohort, program):
    capabilities = tuple(dict.fromkeys(
        row["capability"] for row in cohort.rows))
    grade = next(
        grade for grade in reversed(program.grades)
        if any(cap.id in set(capabilities) for cap in grade.capabilities))
    return {
        "factory_release_sha256": "f" * 64,
        "capabilities": capabilities,
        "rubric_sha256": grade.assessment_sha256,
        "source_sha256": "c" * 64,
        "cohort_sha256": cohort.digest,
        "cohort_file": "cohorts/" + cohort.digest + ".json",
        "cohort_seed": cohort.seed,
    }


def _synthetic_program(grades):
    return ScheduleProgram(
        program_digest="d" * 64,
        grades=tuple(ScheduleGrade(
            grade,
            tuple(ScheduleCapability(capability, 2)
                  for capability in capabilities),
            (),
            "e" * 64,
        ) for grade, capabilities in grades),
        program_complete=False,
    )


def _synthetic_exam_cohort(capabilities, *, seed, generator_version, rubric_version):
    return make_cohort([
        {"id": f"{seed}:{capability}:{index}", "capability": capability,
         "gold": "TRUE" if index % 2 else "FALSE", "tokens": [1, 2]}
        for capability in capabilities for index in range(12)],
        generator_version=generator_version, seed=seed,
        rubric_version=rubric_version)


def _perfect_predictions(_mx, _parameters, rows, *_):
    return {row["id"]: row["gold"] for row in rows}


def _exam_receipt(*, school, run_id, release, manifest, course, graph,
                  parameter_shapes, release_sha, championship_origins):
    identity = trainer.build_school_identity(
        course_sha256=course.digest(),
        semantic_graph_sha256=trainer._fingerprint(graph),
        parameter_shapes=parameter_shapes,
        factory_release_sha256=release_sha)
    return {
        "school": asdict(school), "generation": 1, "run_id": run_id,
        "curriculum_mode": release,
        "source_manifest_sha256": manifest["manifest_sha256"],
        "config": {}, "answer_ids": [6, 7], "teacher_misses": [],
        "semantic_graph_sha256": trainer._fingerprint(graph),
        "parameter_shapes": parameter_shapes,
        "factory_release_sha256": release_sha,
        "championship_school_identity": identity,
        "championship_checkpoint_origins": championship_origins,
        "last_retained_update_grade": "A",
    }


def _patch_owner(name, **kwargs):
    if name == "_cook_new_grade_soups":
        return patch(
            "bilqis_mlx.learning.lesson_guidance._cook_new_grade_soups",
            **kwargs)
    function = getattr(trainer, name)
    return patch(function.__module__ + "." + function.__name__, **kwargs)


def _exam_patches(*, executable_release, program, routine, candidate, school,
                  predict, cook_soups=None, extra=None):
    patches = {
        "_read_executable_factory_release_artifact": lambda *_: executable_release,
        "schedule_program_from_executable_release": lambda *_: program,
        "_routine_executable_cohort":
            lambda *_a, **_k: (routine, _cohort_pointer(routine, program)),
        "_candidate_executable_cohort":
            lambda *_a, **_k: (candidate, _cohort_pointer(candidate, program)),
        "_predictions": predict,
        "_commit_scored_student": lambda *_a, **_k: (school, {}, (), []),
        "_score_parent_for_paired_s3": lambda *_: (None, "INERT_FIXTURE"),
        "summarize_completed_exam_safely":
            lambda *_: {"findings": [], "active_warnings": []},
        "apply_paired_checkpoint_s3": lambda warning, **_: warning,
        "advance_peaks": lambda *_a, **_k: ([], {}),
        "_cook_new_grade_soups": cook_soups or (lambda *_a, **_k: ({}, ())),
        "_advance": lambda _run, saved, advanced, **values: {
            **saved, "school": asdict(advanced), "last_exam": values["last_exam"]},
        "_with_delivery_outbox": lambda saved, *_: saved,
        "_boundary_delivery_events": lambda *_: [],
        "_persist": lambda _run, saved: saved,
        "_publish_boundary": lambda *_a, **_k: None,
    }
    patches.update(extra or {})
    return patches


def _take_inert_exam(*, temp, receipt, manifest, course, root, graph, patches,
                     rubric_sha256):
    with ExitStack() as stack:
        for name, function in patches.items():
            stack.enter_context(_patch_owner(name, side_effect=function))
        stack.enter_context(patch(
            "bilqis_mlx.factory.assessment.assessment_scope_contract",
            return_value=SimpleNamespace(rubric_sha256=rubric_sha256)))
        return trainer._take_exam(
            None, Path(temp), receipt, manifest, course, root, root,
            {"embedding.weight": SimpleNamespace(shape=(1, 1))},
            SimpleNamespace(state={}), graph, reserve_gib=0)
