"""Lifecycle and qualification helpers for the disposable Grade Z proof."""
from dataclasses import asdict
import json

from bilqis_mlx.curriculum.scheduler import (
    Assessment, Score, assess, assess_withheld, start_new, visit,
)
from bilqis_mlx.factory.assessment import qualification_complete
from bilqis_mlx.factory.generation import draw_executable_release_rows
from bilqis_mlx.factory.model import AssessmentClass, LearningEvidence
from bilqis_mlx.factory.schedule import schedule_program_from_executable_release
from bilqis_mlx.learning.stagnation_control import (
    begin_recovery_cycle, complete_recovery_cycle, quarantined_capabilities,
    record_visit, start_session,
)
from bilqis_mlx.learning.teacher_feedback import reconcile_unresolved_misses
from bilqis_mlx.runtime.admission import (
    _executable_factory_admission, _require_executable_factory_admission,
)
from bilqis_mlx.runtime.assessment import (
    _generalization_executable_cohort, _promotion_executable_cohort,
    _routine_executable_cohort,
)
from bilqis_mlx.runtime.state import _fingerprint, _state_from_json
from bilqis_mlx.trainer import session_stop_reason

from .fixture import CAPABILITIES


def assert_compiler_and_generation(case, registry, graph, release):
    case.assertEqual(
        tuple(item.grade_id for item in release.execution_plan.grades),
        ("Z",))
    binary_head = next(
        item for item in release.answer_heads if item.kind == "binary")
    case.assertEqual(binary_head.values, ("FALSE", "TRUE"))
    rows = draw_executable_release_rows(
        None, graph, release, registry, seed=3)
    case.assertEqual(len(rows), 48)
    case.assertEqual({row["capability"] for row in rows}, set(CAPABILITIES))


def admit_and_schedule(case, root, graph, release, student, manifest):
    graph_sha = _fingerprint(graph)
    _, release_file, admission = _executable_factory_admission(
        root, release, student, graph_sha, graph)
    program = schedule_program_from_executable_release(release)
    school = start_new(program, student)
    receipt = {
        "run_id": "disposable-grade-z",
        "generation": 1,
        "source_manifest_sha256": manifest["manifest_sha256"],
        "semantic_graph_sha256": graph_sha,
        "factory_release_sha256": release.release_sha256,
        "factory_release_file": release_file,
        "factory_admission_v2": asdict(admission),
        "qualification_cohort_v2": None,
        "burned_generalization_cohorts_v2": [],
        "school": asdict(school),
    }
    for capability in CAPABILITIES[:5]:
        case.assertEqual(school.queue[0], capability)
        school = visit(program, school, capability, student)
    receipt["school"] = asdict(school)
    state_file = root / "grade-z-state.json"
    state_file.write_text(json.dumps(receipt), encoding="utf-8")
    cold_receipt = json.loads(state_file.read_text(encoding="utf-8"))
    restored = _require_executable_factory_admission(root, cold_receipt, graph)
    case.assertEqual(restored, release)
    resumed_program = schedule_program_from_executable_release(restored)
    school = _state_from_json(cold_receipt["school"], resumed_program)
    case.assertEqual(school.queue, tuple(CAPABILITIES[5:]))
    case.assertEqual(resumed_program.digest(), program.digest())
    for capability in CAPABILITIES[5:]:
        case.assertEqual(school.queue[0], capability)
        school = visit(resumed_program, school, capability, student)
    case.assertEqual(school.stage, "ASSESS_MAIN")
    return receipt, program, school, graph_sha


def assert_cohort_lifecycle(case, root, receipt, manifest, registry, graph, release):
    routine, routine_pointer = _routine_executable_cohort(
        root, receipt, manifest, release, registry, None, graph,
        capabilities=CAPABILITIES, assessment_epoch=0)
    promotion, promotion_pointer = _promotion_executable_cohort(
        root, receipt, manifest, release, registry, None, graph,
        capabilities=CAPABILITIES, assessment_epoch=0)
    fixed_promotion, fixed_pointer = _promotion_executable_cohort(
        root, {**receipt, "qualification_cohort_v2": promotion_pointer},
        manifest, release, registry, None, graph,
        capabilities=CAPABILITIES, assessment_epoch=0)
    case.assertEqual(fixed_promotion, promotion)
    case.assertEqual(fixed_pointer, promotion_pointer)
    generalization, generalization_pointer = _generalization_executable_cohort(
        root, receipt, manifest, release, registry, None, graph,
        capabilities=CAPABILITIES, assessment_epoch=0,
        promotion_pointer=promotion_pointer)
    case.assertFalse(
        {row["id"] for row in promotion.rows} &
        {row["id"] for row in generalization.rows})
    next_generalization, next_pointer = _generalization_executable_cohort(
        root,
        {**receipt,
         "burned_generalization_cohorts_v2": [generalization_pointer]},
        manifest, release, registry, None, graph,
        capabilities=CAPABILITIES, assessment_epoch=0,
        promotion_pointer=promotion_pointer)
    case.assertNotEqual(next_generalization.digest, generalization.digest)
    case.assertNotEqual(next_pointer, generalization_pointer)
    return routine, routine_pointer, promotion, generalization


def assert_mastery_debt_and_teacher(
        case, program, school, student, routine, routine_pointer,
        promotion, generalization):
    perfect = Assessment(
        checkpoint_sha256=student.sha256,
        optimizer_step=student.optimizer_step,
        course_digest=program.digest(),
        rubric_digest=routine_pointer["rubric_sha256"],
        scores={identity: Score(4, 4) for identity in CAPABILITIES},
        evaluation_id="grade-z-perfect",
    )
    mastered = assess(program, school, perfect)
    while mastered.stage == "PROMOTION_SWEEP":
        mastered = visit(program, mastered, mastered.queue[0], student)
        mastered = assess(program, mastered, perfect)
    case.assertEqual(mastered.stage, "WHOLE_SCHOOL_MASTERED")
    case.assertEqual(
        session_stop_reason(
            stage=mastered.stage, elapsed_seconds=0, minutes=90,
            visits=mastered.visits, max_visits=0, grade="Z"),
        "WHOLE_SCHOOL_MASTERED")

    withheld = CAPABILITIES[-1]
    partial = Assessment(
        checkpoint_sha256=student.sha256,
        optimizer_step=student.optimizer_step,
        course_digest=program.digest(),
        rubric_digest=routine_pointer["rubric_sha256"],
        scores={identity: Score(4, 4)
                for identity in CAPABILITIES if identity != withheld},
        evaluation_id="grade-z-withheld",
    )
    contained = assess_withheld(
        program, school, partial, (withheld,),
        rubric_capabilities=CAPABILITIES)
    case.assertNotEqual(contained.stage, "WHOLE_SCHOOL_MASTERED")

    control = start_session(
        session_id="z-stagnation", generation=1,
        required_capabilities=CAPABILITIES)
    control = begin_recovery_cycle(control, first_recovery=(withheld,))
    for phase in ("RECOVERY_1", "RECOVERY_2"):
        control = record_visit(
            control, capability=withheld, phase=phase,
            decision="REJECT", retained_optimizer_updates=0,
            generation=2)
    control, events = complete_recovery_cycle(
        control, weakest_tail=(withheld,),
        scores={withheld: {"correct": 0, "total": 4}},
        generation=3)
    case.assertEqual(quarantined_capabilities(control), (withheld,))
    case.assertEqual(events[0]["capability"], withheld)

    predictions = {row["id"]: row["gold"] for row in routine.rows}
    predictions[routine.rows[0]["id"]] = (
        "FALSE" if routine.rows[0]["gold"] == "TRUE" else "TRUE")
    misses = reconcile_unresolved_misses([], routine.rows, predictions)
    case.assertEqual(len(misses), 1)
    case.assertTrue(misses[0]["capability"].startswith("Z."))

    promotion_evidence = LearningEvidence(
        AssessmentClass.PROMOTION, promotion.digest,
        student.sha256, student.optimizer_step, True)
    generalization_evidence = LearningEvidence(
        AssessmentClass.GENERALIZATION, generalization.digest,
        student.sha256, student.optimizer_step, True)
    case.assertTrue(qualification_complete(
        promotion_evidence, generalization_evidence))
    return mastered


__all__ = (
    "admit_and_schedule", "assert_cohort_lifecycle",
    "assert_compiler_and_generation", "assert_mastery_debt_and_teacher",
)
