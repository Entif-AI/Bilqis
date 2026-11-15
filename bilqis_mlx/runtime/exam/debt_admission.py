"""Exact debt-admission boundary measurement."""
from __future__ import annotations

import dataclasses as _dataclasses

import bilqis_mlx.factory.schedule as _factory_schedule
import bilqis_mlx.generated_assessment as _bilqis_mlx_generated_assessment
import bilqis_mlx.learning.student_ops as _learning_student_ops
import bilqis_mlx.runtime.admission as _runtime_admission
import bilqis_mlx.runtime.assessment as _runtime_assessment
import bilqis_mlx.runtime.state as _runtime_state
import bilqis_mlx.source_adapters.school as _source_adapters_school


def _measure_debt_admission_boundary(mx, run_dir, receipt, manifest, course,
                                     source_root, parameters, graph):
    """Measure the exact complete admitted plan before explicit debt admission."""
    release = _runtime_admission._require_executable_factory_admission(
        run_dir, receipt, graph)
    program = _factory_schedule.schedule_program_from_executable_release(release)
    school = _runtime_state._state_from_json(receipt["school"], program)
    full_scope = tuple(
        cap.capability_id for cap in release.execution_plan.capabilities)
    cohort, pointer = _runtime_assessment._routine_executable_cohort(
        run_dir, receipt, manifest, release,
        _source_adapters_school.live_source_registry(),
        source_root, graph, capabilities=full_scope,
        assessment_epoch=school.grade_exam_epoch)
    guesses = _learning_student_ops._predictions(
        mx, parameters, list(cohort.rows), receipt["config"],
        receipt["answer_ids"])
    measured = _bilqis_mlx_generated_assessment.score(
        cohort, guesses, _dataclasses.asdict(school.current_student))
    return {**receipt, "debt_admission_boundary_exam": {
        **pointer,
        "boundary_schema": "bilqis.mlx.debt-admission-boundary/v2",
        "student_sha256": school.current_student.sha256,
        "optimizer_step": school.current_student.optimizer_step,
        "exam_rubric_sha256": pointer["rubric_sha256"],
        "assessment_scope_sha256": _runtime_state._fingerprint(full_scope),
        "source_exam_plane": "DEBT_ADMISSION_BOUNDARY",
        "scores": measured["scores"],
        "misses_for_teacher": list(measured["misses_for_teacher"]),
    }}
