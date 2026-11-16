"""Whole-student scoring and transactional stop-boundary commits."""
from __future__ import annotations

from .topology_lifecycle import topology_for_checkpoint as _topology_for_checkpoint

import bilqis_mlx.curriculum.scheduler as _curriculum_scheduler
import bilqis_mlx.factory.schedule as _factory_schedule
import bilqis_mlx.generated_assessment as _bilqis_mlx_generated_assessment
import bilqis_mlx.learning.capability_frontier as _learning_capability_frontier
import bilqis_mlx.learning.championship_runtime as _learning_championship_runtime
import bilqis_mlx.learning.stagnation_control as _learning_stagnation_control
import bilqis_mlx.learning.student_ops as _learning_student_ops
import bilqis_mlx.learning.whole_student_retention as _learning_whole_student_retention
import bilqis_mlx.runtime.admission as _runtime_admission
import bilqis_mlx.runtime.assessment as _runtime_assessment
import bilqis_mlx.runtime.checkpoints as _runtime_checkpoints
import bilqis_mlx.runtime.exam_execution as _runtime_exam_execution
import bilqis_mlx.runtime.frontier_refresh as _runtime_frontier_refresh
import bilqis_mlx.runtime.release_adoption as _runtime_release_adoption
import bilqis_mlx.runtime.state as _runtime_state
import bilqis_mlx.source_adapters.school as _source_adapters_school
import dataclasses as _dataclasses
import uuid as _uuid


def _live_exam_factors_complete(executable_release, cohort, expected) -> bool:
    """Validate declared answer-domain coverage without knowing modality names.

    Source/construction-specific invariants belong to the registered provider
    and its independent oracle.  The generic trainer verifies only what the
    executable plan declares: exact cohort size, admitted answer kind, admitted
    gold label, representation of every declared answer modality, and complete
    target coverage only when the admitted provider declares a balancing axis.
    A numeric output *vocabulary* is not a guarantee that every arithmetic
    result appears in every finite exam.
    """
    balancing_axes = frozenset((
        "balanced-gold", "balanced-operator-targets", "runtime-answer-balance"))
    capability_map = executable_release.execution_plan.capability_map
    for cap, total in expected.items():
        rows = [row for row in cohort.rows if row["capability"] == cap]
        if len(rows) != total:
            return False
        families = capability_map[cap].answer_families
        family_map = {family.kind: family for family in families}
        if (not family_map or any(
                row.get("answer_kind", "binary") not in family_map or
                row["gold"] not in family_map[
                    row.get("answer_kind", "binary")].values
                for row in rows)):
            return False
        for family in families:
            observed = {
                row["gold"] for row in rows
                if row.get("answer_kind", "binary") == family.kind}
            if (not observed or
                    (balancing_axes.intersection(
                        getattr(capability_map[cap], "variation_axes", ()))
                     and observed != set(family.values))):
                return False
    return True


def _verify_live_rubric_lineage(run_dir, receipt, program) -> None:
    """Resolve the active rubric to the exact immutable exam that minted it.

    A migrated student may retain a signed v1 assessment; subsequent v2 exams
    carry exact-scope rubrics that are *not* whole-grade blueprint hashes.
    Neither kind may be relabeled into the other or accepted without its own
    source-bound cohort proof.
    """
    live_rubric = receipt.get("live_rubric_sha256")
    known_rubrics = {grade.assessment_sha256 for grade in program.grades}
    if live_rubric is None or live_rubric in known_rubrics:
        return
    exam = receipt.get("last_exam") or {}
    if (exam.get("factory_release_sha256") ==
            receipt.get("factory_release_sha256") and
            exam.get("factory_release_sha256") is not None and
            live_rubric == exam.get("rubric_sha256") ==
            exam.get("exam_rubric_sha256")):
        # Do not trust a matching label alone. Reconstruct the scope contract,
        # content-addressed cohort and saved source/oracle evidence from disk.
        from bilqis_mlx.runtime.assessment import _verify_saved_cohort
        if _verify_saved_cohort(run_dir, receipt, None) is None:
            raise ValueError("HUMAN_TRAINER_LIVE_RUBRIC_EVIDENCE_MISSING")
        return
    from bilqis_mlx.runtime.admission import _verified_historical_cohort_release
    previous = _verified_historical_cohort_release(run_dir, receipt)
    if (previous is not None and
            live_rubric in set(previous.assessment_rubric_sha256s)):
        return
    raise ValueError("HUMAN_TRAINER_LIVE_RUBRIC_IDENTITY_DRIFT")


def _commit_scored_student(mx, run_dir, receipt, manifest, course, school,
                           cohort, predictions, parameters, optimizer, graph, *,
                           reserve_gib, allowed_capabilities=None):
    """Only evaluated best scores mint permanent capability candidates.

    If none improve, the single live student still needs a replaceable
    recovery point. This is NOT a champion or an additional archive slot.
    """
    executable_release = _runtime_admission._read_executable_factory_release_artifact(
        run_dir, receipt)
    program = _factory_schedule.schedule_program_from_executable_release(executable_release)
    full_allowed = set(_curriculum_scheduler.assessment_capabilities(program, school))
    allowed = (set(allowed_capabilities) if allowed_capabilities is not None
               else set(full_allowed))
    if not allowed or not allowed <= full_allowed:
        raise ValueError("HUMAN_TRAINER_PARTIAL_EVALUATION_SCOPE_DRIFT")
    from bilqis_mlx.factory.assessment import assessment_scope_contract
    rubric = assessment_scope_contract(
        executable_release, allowed).rubric_sha256
    _verify_live_rubric_lineage(run_dir, receipt, program)
    expected = {
        capability.id: capability.exam_item_count
        for grade in program.grades
        for capability in grade.capabilities
        if capability.id in allowed}
    if (cohort.rubric_version != rubric or
            len(cohort.rows) != sum(expected.values())):
        raise ValueError("HUMAN_TRAINER_LIVE_RUBRIC_SCOPE_DRIFT")
    grades = _bilqis_mlx_generated_assessment.score(cohort, predictions, {
        "sha256": "IN_MEMORY_CANDIDATE", "optimizer_step": int(optimizer.state["step"].item()),
        "model_and_native_adamw": True})["scores"]
    if ({cap: row["total"] for cap, row in grades.items()} != expected or
            not _live_exam_factors_complete(
                executable_release, cohort, expected)):
        raise ValueError("HUMAN_TRAINER_LIVE_EXAM_INCOMPLETE_FACTORS")
    complete_scope = allowed == full_allowed
    if complete_scope:
        replay_receipt = {**receipt, "live_rubric_sha256": rubric}
        frontier, incumbent_comparisons = _learning_championship_runtime._compare_incumbents(
            mx, run_dir, replay_receipt, cohort, receipt["config"],
            receipt["answer_ids"], graph)
        roles = _learning_capability_frontier.candidate_roles(frontier, grades, rubric)
    else:
        # A quarantined capability remains mandatory graduation debt. Partial
        # ordinary scoring protects the causal student but cannot mint or move
        # championship authority from an incomplete capability inventory.
        frontier = dict(receipt.get("capability_best", {}))
        incumbent_comparisons = []
        roles = ()
    name = ("best-" if roles else "working-") + str(school.visits) + "-" + _uuid.uuid4().hex[:12]
    candidate = _runtime_checkpoints._bundle_pointer(run_dir, name, parameters, optimizer, graph,
                                reserve_gib=reserve_gib, model_topology=_topology_for_checkpoint(receipt))
    if roles:
        proof = _runtime_state._fingerprint({"manifest": manifest["manifest_sha256"],
                              "rubric": rubric, "cohort": cohort.digest,
                              "predictions": sorted(predictions.items()),
                              "student_sha256": candidate.sha256,
                              "optimizer_step": candidate.optimizer_step})
        frontier = _learning_capability_frontier.promote(frontier, grades, rubric, _dataclasses.asdict(candidate),
                           "capability-evaluation/" + proof, roles)
    return (_dataclasses.replace(school, current_student=candidate), frontier, roles,
            incumbent_comparisons)


def _flush_working_student(mx, run_dir, receipt, manifest, course, parameters,
                           optimizer, graph, *, reserve_gib, source_root):
    """Protect an unfinished grade cycle when the human stops mid-cycle."""
    pending = receipt.get("_pending_visit_events", ())
    if not pending:
        return receipt
    executable_release = _runtime_admission._read_executable_factory_release_artifact(
        run_dir, receipt)
    program = _factory_schedule.schedule_program_from_executable_release(executable_release)
    school = _runtime_state._state_from_json(receipt["school"], program)
    stagnation = receipt.get("stagnation_session")
    blocked = _learning_stagnation_control.quarantined_capabilities(stagnation)
    active_scope = tuple(
        cap for cap in _curriculum_scheduler.assessment_capabilities(program, school)
        if cap not in set(blocked))
    if not active_scope:
        raise ValueError("STAGNATION_STOP_EVALUATION_HAS_NO_ACTIVE_CAPABILITIES")
    source_registry = _source_adapters_school.live_source_registry()
    exam_cohort, _ = _runtime_assessment._routine_executable_cohort(
        run_dir, receipt, manifest, executable_release, source_registry,
        source_root, graph, capabilities=active_scope,
        assessment_epoch=school.grade_exam_epoch)
    cohort, _ = _runtime_assessment._candidate_executable_cohort(
        run_dir, receipt, manifest, executable_release, source_registry,
        source_root, graph, capabilities=active_scope)
    rubric = cohort.rubric_version
    generator = cohort.generator_version
    rows = list(cohort.rows)
    guesses = _learning_student_ops._predictions(mx, parameters, rows, receipt["config"], receipt["answer_ids"])
    current, frontier, roles, compared = _commit_scored_student(
        mx, run_dir, receipt, manifest, course, school, cohort, guesses,
        parameters, optimizer, graph, reserve_gib=reserve_gib,
        allowed_capabilities=active_scope)
    # The operator may stop between scheduled full exams. Score one fresh
    # routine cohort at this durable stop boundary; this records a recoverable
    # peak without creating or extending a promotion attempt.
    exam_guesses = _learning_student_ops._predictions(
        mx, parameters, list(exam_cohort.rows), receipt["config"], receipt["answer_ids"])
    exam_scores = _bilqis_mlx_generated_assessment.score(exam_cohort, exam_guesses,
                               _dataclasses.asdict(current.current_student))["scores"]
    peaks, retention_status = _learning_whole_student_retention.advance_peaks(
        receipt.get("whole_student_peaks", []),
        curriculum_mode=receipt["curriculum_mode"],
        numeric_maximum=receipt.get("numeric_maximum"),
        rubric_sha256=rubric, cohort_sha256=exam_cohort.digest,
        assessment_scope_sha256=_runtime_state._fingerprint(active_scope),
        scores=exam_scores, checkpoint=_dataclasses.asdict(current.current_student))
    stop_receipt = {**receipt, "legacy_frontier_pending_replay": False,
                    "whole_student_peaks": peaks,
                    "live_rubric_sha256": rubric}
    stop_receipt = _learning_championship_runtime._bind_checkpoint_origin(stop_receipt, current.current_student)
    record = _runtime_checkpoints._advance(run_dir, stop_receipt,
                      current, frontier=frontier,
                      model_bundle=current.current_student.filename, persist=False)
    record = _runtime_frontier_refresh._refresh_fixed_frontier(
        mx, run_dir, record, course, parameters, optimizer, persist=False)
    pending = tuple(record.get("_pending_visit_events", pending))
    comparison_event = {
        "event": "SCHOOL_LIVE_CANDIDATE_COMPARED", "grade": school.grade,
        "generation": record["generation"],
        "rubric": rubric,
        "cohort_sha256": cohort.digest, "generator_version": generator,
        "scores": _bilqis_mlx_generated_assessment.score(cohort, guesses,
            _dataclasses.asdict(current.current_student))["scores"],
        "student_sha256": current.current_student.sha256,
        "optimizer_step": current.current_student.optimizer_step,
        "incumbent_comparisons": compared,
        "stagnation_quarantined": list(blocked)}
    comparison_event["whole_student_retention"] = retention_status
    record = _runtime_checkpoints._persist(run_dir, _runtime_checkpoints._with_delivery_outbox(
        record, _runtime_checkpoints._boundary_delivery_events(record, pending, roles, comparison_event)))
    _runtime_checkpoints._publish_boundary(run_dir, record, pending, roles, exam_event=comparison_event)
    return record


def _flush_flash_student(run_dir, receipt, course, parameters, optimizer, graph,
                         *, reserve_gib):
    """Persist the causal student without performing qualification work."""
    pending = tuple(receipt.get("_pending_visit_events", ()))
    if not pending:
        return receipt
    school = _runtime_state._state_from_json(receipt["school"], _runtime_release_adoption._schedule_for_receipt(run_dir, receipt, course))
    due = _curriculum_scheduler.require_assessment_after_flash(_runtime_release_adoption._schedule_for_receipt(run_dir, receipt, course), school)
    optimizer_step = int(optimizer.state["step"].item())
    if optimizer_step == school.current_student.optimizer_step:
        candidate = school.current_student
    else:
        name = "flash-working-" + str(school.visits) + "-" + _uuid.uuid4().hex[:12]
        candidate = _runtime_checkpoints._bundle_pointer(
            run_dir, name, parameters, optimizer, graph, reserve_gib=reserve_gib,
            model_topology=_topology_for_checkpoint(receipt))
    due = _dataclasses.replace(due, current_student=candidate)
    receipt = _learning_championship_runtime._bind_checkpoint_origin(receipt, candidate)
    record = _runtime_checkpoints._advance(
        run_dir, receipt, due, model_bundle=candidate.filename,
        result=_runtime_exam_execution._school_result_label(due), persist=False)
    flash_event = {
        "event": "SCHOOL_FLASH_CHECKPOINT_COMMITTED",
        "grade": due.grade,
        "generation": record["generation"],
        "optimizer_step": candidate.optimizer_step,
        "student_sha256": candidate.sha256,
        "phase": due.stage,
        "assessment_deferred": True,
        "qualification_authority_changed": False,
        "champions_changed": False,
        "pending_visit_count": len(pending),
    }
    boundary_pending = (*pending, flash_event)
    record = _runtime_checkpoints._persist(run_dir, _runtime_checkpoints._with_delivery_outbox(
        record, _runtime_checkpoints._boundary_delivery_events(record, boundary_pending, (), None)))
    _runtime_checkpoints._publish_boundary(run_dir, record, boundary_pending, (), exam_event=None)
    return record
