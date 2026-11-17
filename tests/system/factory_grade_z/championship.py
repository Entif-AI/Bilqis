"""Championship and telemetry helpers for the disposable Grade Z proof."""
from dataclasses import asdict
import hashlib
import io
import json

from bilqis_mlx.cli import human_stop_summary
from bilqis_mlx.generated_assessment import score as score_cohort
from bilqis_mlx.learning.epoch_championships import advance_epoch
from bilqis_mlx.learning.mentor_epoch import begin_initial_epoch
from bilqis_mlx.presentation.school_telemetry import LETTER_TABLES, SchoolTelemetry
from bilqis_mlx.presentation.spiral_dashboard import Dashboard
from bilqis_mlx.runtime.assessment import load_championship_cohort

from .fixture import CAPABILITIES


def assert_championship(case, root, routine, routine_pointer, student, graph_sha, manifest):
    scores = score_cohort(
        routine,
        {row["id"]: row["gold"] for row in routine.rows},
        asdict(student))["scores"]
    questions = {
        identity: [
            {"id": row["id"], "gold": row["gold"]}
            for row in routine.rows if row["capability"] == identity]
        for identity in CAPABILITIES
    }
    scope_sha = hashlib.sha256(
        json.dumps(CAPABILITIES).encode()).hexdigest()
    challenger = {
        "cohort_sha256": routine.digest,
        "rubric_sha256": routine_pointer["rubric_sha256"],
        "cohort_rubric_sha256": routine_pointer["rubric_sha256"],
        "assessment_scope_sha256": scope_sha,
        "source_graph_sha256": graph_sha,
        "source_oracle_sha256": manifest["manifest_sha256"],
        "challenge_group": "Z",
        "checkpoint_origin_group": "Z",
        "challenge_grade": "Z",
        "checkpoint_origin_grade": "Z",
        "checkpoint": asdict(student),
        "scores": scores,
        "questions": questions,
        "correct_questions": questions,
    }
    epoch = begin_initial_epoch(
        student=asdict(student), introduced_grade="Z",
        source_graph_sha256=graph_sha, frontier={}, soups={})
    epoch, changed, _ = advance_epoch(
        epoch, capability_groups={"Z": CAPABILITIES},
        challenger_exam=challenger, incumbent_exams={})
    case.assertEqual(set(changed), set(CAPABILITIES))
    case.assertEqual(set(epoch["active_roles"]), set(CAPABILITIES))
    replayed = load_championship_cohort(root, challenger)
    case.assertEqual(replayed, routine)
    return scores, scope_sha, changed


def assert_telemetry_and_operator(
        case, routine, routine_pointer, student, mastered, scores,
        scope_sha, changed):
    board = Dashboard(
        stream=io.StringIO(), redraw=False, tables=LETTER_TABLES,
        show_all_panels=True)
    telemetry = SchoolTelemetry(board, active_grades=("Z",))
    telemetry.ingest({
        "event": "SCHOOL_LIVE_EXAM_COMMITTED",
        "grade": "Z",
        "generation": 2,
        "rubric": routine_pointer["rubric_sha256"],
        "assessment_scope_sha256": scope_sha,
        "optimizer_step": student.optimizer_step,
        "student_sha256": student.sha256,
        "cohort_sha256": routine.digest,
        "cohort_file": routine_pointer["cohort_file"],
        "generator_version": routine.generator_version,
        "scores": scores,
        "phase": mastered.stage,
        "championship_epoch": {
            "earned_roles": list(changed),
            "cross_origin_decisions": [],
        },
    })
    case.assertIn("Z", telemetry.grades)
    case.assertTrue(any(
        row.get("grade") == "Z"
        for row in board.rows["GRADES & MASTERY"]))

    stop = {
        "stop_reason": "GRADE_Z_AWAITING_NEXT_GRADE",
        "visits_this_command": 6,
        "elapsed_seconds": 1.0,
        "optimizer_step": student.optimizer_step,
    }
    case.assertIn("awaiting the next", human_stop_summary(stop))


__all__ = ("assert_championship", "assert_telemetry_and_operator")
