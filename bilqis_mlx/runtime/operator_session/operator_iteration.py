"""Advance and assess one operator loop iteration."""
import bilqis_mlx.operator_vocabulary as _operator_vocabulary
import bilqis_mlx.factory.schedule as _factory_schedule
import bilqis_mlx.runtime.admission as _runtime_admission
import bilqis_mlx.runtime.boundary_commit as _runtime_boundary_commit
import bilqis_mlx.runtime.checkpoints as _runtime_checkpoints
import bilqis_mlx.runtime.exam_execution as _runtime_exam_execution
import bilqis_mlx.runtime.reconciliation as _runtime_reconciliation
import bilqis_mlx.runtime.release_adoption as _runtime_release_adoption
import bilqis_mlx.runtime.session as _runtime_session
import bilqis_mlx.runtime.state as _runtime_state
import bilqis_mlx.runtime.timing_trace as _runtime_timing_trace
import time as _time
from bilqis_mlx.errors import ErrorBus, SCHOOL
from .operator_autonomy import DispatchControl


def _dispatch_atlas_frontier_attempt(
        run_dir, receipt, proposal, proposal_file,
        *, record=_runtime_checkpoints._record):
    from bilqis_mlx.runtime.atlas_admission import dispatch_atlas_frontier_proposal
    from bilqis_mlx.runtime.atlas_admission_policy import AdmissionResult, AdmissionStatus

    result = dispatch_atlas_frontier_proposal(run_dir, proposal)
    if not isinstance(result, AdmissionResult):
        ErrorBus.raise_(
            SCHOOL.BAMF_ATLAS_ADMISSION.INVALID,
            reason="BAMF_ATLAS_ADMISSION_RESULT_REQUIRED",
        )
    adopted = result.status is AdmissionStatus.ADOPTED
    if adopted:
        return (
            DispatchControl.COLD_RESUME,
            _operator_vocabulary.ATLAS_ADMISSION_ADOPTED_COLD_RESUME.code,
        )
    record(run_dir, {
        "event": "SCHOOL_ATLAS_ADMISSION_STAGED",
        "generation": receipt["generation"],
        "proposal_sha256": result.proposal_sha256,
        "proposal_file": proposal_file,
        "lease_sha256": result.lease_sha256,
        "reason": result.reason,
        "operator_action": result.operator_action,
        "actual_neural_updates": result.actual_neural_updates,
    })
    control = (
        DispatchControl.PROCEED
        if result.reason == "OUT_OF_LEASE_SCOPE"
        else DispatchControl.STOP
    )
    return control, _operator_vocabulary.ATLAS_ADMISSION_STAGED.code


def prepare_operator_iteration(*, experiment_budget, run_dir, receipt, course_a,
                               source_root, graph, course, executable_release,
                               schedule_program, numeric_staircase, mx, manifest,
                               params, optimizer, reserve_gib, full_grade_b,
                               autonomy_session, start, minutes, visits, max_visits,
                               flash_mode, source_checkpoint):
    if experiment_budget is not None:
        experiment_budget.assert_can_allocate(600_000_000)
    receipt, course, executable_release, schedule_program = (
        _runtime_release_adoption._advance_provider_dimensions(
            run_dir, receipt, course_a, source_root, graph, course,
            executable_release, schedule_program, numeric_staircase=numeric_staircase))
    params, optimizer, graph, receipt, course, adopted_boundary = (
        _runtime_release_adoption._auto_adopt_known_grade_boundary(
            mx, run_dir, receipt, course, course_a, source_root, manifest,
            params, optimizer, graph, reserve_gib=reserve_gib,
            full_grade_b=full_grade_b, numeric_staircase=numeric_staircase))
    if adopted_boundary:
        executable_release = _runtime_admission._read_executable_factory_release_artifact(run_dir, receipt)
        schedule_program = _factory_schedule.schedule_program_from_executable_release(executable_release)
        if autonomy_session is not None:
            autonomy_session.refresh_release(executable_release)
    course = schedule_program
    school = _runtime_state._state_from_json(receipt["school"], schedule_program)
    receipt = _runtime_reconciliation._reconcile_stagnation_scope(
        run_dir, receipt, course, school)
    school = _runtime_state._state_from_json(receipt["school"], _runtime_release_adoption._schedule_for_receipt(run_dir, receipt, course))
    autonomy_teaching_work = None
    budget_reason = _runtime_session.session_stop_reason(
        stage="MAIN", elapsed_seconds=_time.monotonic() - start, minutes=minutes,
        visits=visits, max_visits=max_visits)
    if (autonomy_session is not None and school.stage == "AWAITING_NEXT_GRADE" and
            budget_reason is None):
        autonomy_session.refresh_release(
            _runtime_admission._read_executable_factory_release_artifact(run_dir, receipt))
        proposal, proposal_file = autonomy_session.propose_source_frontier_work(
            school.current_student, graph)
        if proposal.disposition.value == "PROPOSAL":
            control, reason = _dispatch_atlas_frontier_attempt(
                run_dir, receipt, proposal, proposal_file)
            return control, reason, receipt, course, executable_release, schedule_program, params, optimizer, graph, school, autonomy_teaching_work
    reason = _runtime_session.session_stop_reason(
        stage=("MAIN" if autonomy_session is not None and
               school.stage == "AWAITING_NEXT_GRADE" else school.stage),
        elapsed_seconds=_time.monotonic() - start,
        minutes=minutes, visits=visits, max_visits=max_visits,
        grade=school.grade, flash_mode=flash_mode)
    if reason is not None:
        return DispatchControl.STOP, reason, receipt, course, executable_release, schedule_program, params, optimizer, graph, school, autonomy_teaching_work
    if school.stage.startswith("ASSESS_"):
        return _assess_iteration(
            school=school,
            flash_mode=flash_mode,
            run_dir=run_dir,
            receipt=receipt,
            course=course,
            params=params,
            optimizer=optimizer,
            graph=graph,
            reserve_gib=reserve_gib,
            mx=mx,
            manifest=manifest,
            source_root=source_root,
            source_checkpoint=source_checkpoint,
            start=start,
            experiment_budget=experiment_budget,
            reason=reason,
            executable_release=executable_release,
            schedule_program=schedule_program,
            autonomy_teaching_work=autonomy_teaching_work)
    return DispatchControl.PROCEED, reason, receipt, course, executable_release, schedule_program, params, optimizer, graph, school, autonomy_teaching_work


def _assess_iteration(*, school, flash_mode, run_dir, receipt, course, params, optimizer, graph, reserve_gib, mx, manifest, source_root, source_checkpoint, start, experiment_budget, reason, executable_release, schedule_program, autonomy_teaching_work):
    _runtime_checkpoints._notify_viewer({"_runtime_phase": "ASSESSING", "_dashboard_redraw": True})
    if flash_mode:
        # Flash may skip expensive championship/promotion work, but
        # it may not skip the fresh cumulative evidence needed to
        # choose recovery work or advance the cross-grade spiral.
        receipt = _runtime_boundary_commit._flush_flash_student(
            run_dir, receipt, course, params, optimizer, graph,
            reserve_gib=reserve_gib)
        receipt = _runtime_exam_execution._take_exam(
            mx, run_dir, receipt, manifest, course, source_root,
            source_checkpoint, params, optimizer, graph,
            reserve_gib=reserve_gib, scheduler_only=True,
            session_elapsed_seconds=_time.monotonic() - start)
        if experiment_budget is not None:
            experiment_budget.assert_can_allocate(0)
        school = _runtime_state._state_from_json(receipt["school"], _runtime_release_adoption._schedule_for_receipt(run_dir, receipt, course))
        if school.stage.startswith("ASSESS_"):
            # Scheduler-only evidence found no remaining imperfect
            # grade. Preserve the qualification debt for a full
            # authoritative exam rather than minting mastery in flash.
            reason = "FLASH_QUALIFICATION_REQUIRED"
            return DispatchControl.STOP, reason, receipt, course, executable_release, schedule_program, params, optimizer, graph, school, autonomy_teaching_work
        return DispatchControl.CONTINUE, reason, receipt, course, executable_release, schedule_program, params, optimizer, graph, school, autonomy_teaching_work
    with _runtime_timing_trace.trace_span(
            "ASSESSMENT", generation=receipt["generation"],
            phase=school.stage, grade=school.grade):
        receipt = _runtime_exam_execution._take_exam(
            mx, run_dir, receipt, manifest, course, source_root,
            source_checkpoint, params, optimizer, graph,
            reserve_gib=reserve_gib,
            session_elapsed_seconds=_time.monotonic() - start)
    if experiment_budget is not None:
        experiment_budget.assert_can_allocate(0)
    return DispatchControl.CONTINUE, reason, receipt, course, executable_release, schedule_program, params, optimizer, graph, school, autonomy_teaching_work
