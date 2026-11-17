"""Executable release, profile and JIT adoption transactions."""
from __future__ import annotations

from ..topology_lifecycle import topology_for_checkpoint as _topology_for_checkpoint

from bilqis_mlx.errors import ErrorBus, FACTORY, SCHOOL


import bilqis_mlx.compatibility.executable_projection as _compatibility_executable_projection
import bilqis_mlx.curriculum.scheduler as _curriculum_scheduler
import bilqis_mlx.factory.executable_release as _factory_executable_release
import bilqis_mlx.factory.live_answers as _factory_live_answers
import bilqis_mlx.factory.schedule as _factory_schedule
import bilqis_mlx.learning.championship_identity as _learning_championship_identity
import bilqis_mlx.profiles.catalog as _profiles_catalog
import bilqis_mlx.runtime.admission as _runtime_admission
import bilqis_mlx.runtime.checkpoints as _runtime_checkpoints
import bilqis_mlx.runtime.state as _runtime_state
import bilqis_mlx.source_adapters.school as _source_adapters_school
import bilqis_mlx.vocabulary_growth as _bilqis_mlx_vocabulary_growth
import copy as _copy
import dataclasses as _dataclasses
import functools as _functools
import pathlib as _pathlib
import uuid as _uuid

def _adopt_jit_proposal(mx, run_dir, receipt, grade_a_course, source_root, graph,
                       parameters, optimizer, session, proposal, *, reserve_gib,
                       adopt_prepared_successor):
    """Use the existing student/own-AdamW admission transaction for a fresh JIT choice."""
    from bilqis_mlx.runtime.jit_adoption import verify_current_implementations
    predecessor = _runtime_admission._require_executable_factory_admission(run_dir, receipt, graph)
    program = _factory_schedule.schedule_program_from_executable_release(predecessor)
    school = _runtime_state._state_from_json(receipt["school"], program)
    staged = session.resolve_ready_proposal(school.current_student, proposal)
    successor = staged.successor
    verify_current_implementations(successor, _source_adapters_school.live_source_registry(), _factory_live_answers.live_answer_registry())
    return adopt_prepared_successor(
        mx, run_dir, receipt, grade_a_course, source_root, graph,
        parameters, optimizer, staged, reserve_gib=reserve_gib)


@_dataclasses.dataclass(frozen=True)
class PreparedSuccessorMaterialization:
    """In-memory learner state for one verified prepared cutover."""
    parameters: dict
    optimizer: object
    graph: dict
    student: _curriculum_scheduler.Checkpoint
    growth: dict | None
    rebaselined_exam: dict | None


def _materialize_prepared_successor(
        mx, run_dir, receipt, current_student, successor,
        graph, parameters, optimizer, next_graph, *, reserve_gib):
    """Materialize only the released ABI geometry, without school publication."""
    if successor.transition is None:
        raise ErrorBus.legacy_error(FACTORY.EXECUTION.EXECUTABLE_PROFILE_TRANSITION_UNSUPPORTED)
    geometry = successor.transition.semantic_geometry
    if geometry == _factory_executable_release.SemanticGeometryChange.UNCHANGED:
        successor.verify_semantic_catalog(graph)
        if _runtime_state._fingerprint(next_graph) != _runtime_state._fingerprint(graph):
            raise ValueError(_factory_executable_release._ReleaseError.SEMANTIC_GRAPH_DRIFT)
        return PreparedSuccessorMaterialization(
            parameters, optimizer, graph, current_student, None, None)
    if geometry != _factory_executable_release.SemanticGeometryChange.APPEND_ONLY_EXPANSION:
        raise ErrorBus.legacy_error(FACTORY.EXECUTION.EXECUTABLE_PROFILE_TRANSITION_UNSUPPORTED)

    from ..assessment import _load_executable_cohort
    from ...learning.student_ops import _predictions
    from ...fixed_frontier import load_frontier, load_frontier_cohort, rebaseline_frontier_exam

    predecessor = _runtime_admission._require_executable_factory_admission(run_dir, receipt, graph)
    successor.verify_successor_of(predecessor)
    successor.verify_semantic_catalog(next_graph)
    exam = receipt.get("last_exam") or {}
    _load_executable_cohort(
        run_dir, {"manifest_sha256": receipt["source_manifest_sha256"]},
        predecessor, tuple(exam.get("capabilities", ())), exam)
    load_frontier(run_dir, {"last_exam": exam},
                  parent_sha256=current_student.sha256,
                  parent_optimizer_step=current_student.optimizer_step)
    preserved = load_frontier_cohort(run_dir, exam)
    if preserved is None:
        raise ValueError("FACTORY_CATALOG_BOUNDARY_COHORT_REQUIRED")
    grown, own_optimizer, growth = _bilqis_mlx_vocabulary_growth.extend_mlx_student(
        parameters, optimizer, graph, next_graph)
    pointer = _runtime_checkpoints._bundle_pointer(
        run_dir, "catalog-admission-" + _uuid.uuid4().hex[:12],
        grown, own_optimizer, next_graph, reserve_gib=reserve_gib,
        model_topology=_topology_for_checkpoint(receipt))
    config = {**receipt["config"], "vocab_size": len(next_graph["tokens"]),
              "answer_heads": _factory_executable_release.answer_heads_from_executable_release(
                  successor, next_graph)}
    exam = rebaseline_frontier_exam(
        run_dir, exam, checkpoint=_dataclasses.asdict(pointer), predictions=_predictions(
            mx, grown, list(preserved.rows), config, receipt["answer_ids"]))
    return PreparedSuccessorMaterialization(
        grown, own_optimizer, next_graph, pointer, growth, exam)


def _commit_prepared_successor(
        run_dir, receipt, predecessor, successor,
        previous_program, successor_program, school, next_state,
        materialization, compatibility_course, *, topology, revised_grade,
        profile_championship_state, profile_adoption_receipt,
        catalog_adoption_event):
    """Commit one materialized successor and its original transition intent."""
    student = materialization.student
    next_state = _dataclasses.replace(next_state, current_student=student)
    graph = materialization.graph
    graph_sha = _runtime_state._fingerprint(graph)
    shapes = {name: list(value.shape) for name, value in materialization.parameters.items()}
    successor, release_file, admission = _runtime_admission._executable_factory_admission(
        run_dir, successor, student, graph_sha, graph)
    appended = topology is _curriculum_scheduler.ScheduleTopology.APPEND_GRADE
    identity, epoch, history = profile_championship_state(
        {**receipt, "semantic_graph_sha256": graph_sha, "parameter_shapes": shapes},
        predecessor, successor, school, next_state, appended=appended)
    candidate = profile_adoption_receipt(
        receipt, compatibility_course, successor, successor_program,
        release_file, admission, identity, epoch, history, revised_grade, graph)
    candidate.update(semantic_graph_sha256=graph_sha, parameter_shapes=shapes,
                     config={**candidate["config"], "vocab_size": len(graph["tokens"])})
    if materialization.growth is not None:
        candidate.update(
            last_exam=materialization.rebaselined_exam,
            numeric_maximum=candidate.get("numeric_maximum"),
            numeric_scope_final_maximum=receipt.get("numeric_scope_final_maximum"))
    record = _runtime_checkpoints._advance(
        run_dir, candidate, next_state, model_bundle=student.filename,
        result="ACTIVE_GRADE_" + next_state.grade, persist=False)
    if materialization.growth is not None:
        event = catalog_adoption_event(
            record, school, student, successor, materialization.growth, next_state.grade)
    else:
        event = {
            "event": "SCHOOL_EXECUTION_PROFILE_ADOPTED",
            "generation": record["generation"],
            "grade": next_state.grade,
            "profile_id": successor.profile.profile_id,
            "transition_kind": "APPEND_GRADE" if appended else "REVISE_PROFILE",
            "revised_grade": revised_grade,
            "debt_admission": False,
            "carried_mastery_debt": list(next_state.carried_mastery_debt),
            "previous_factory_release_sha256": predecessor.release_sha256,
            "factory_release_sha256": successor.release_sha256,
            "student_sha256": school.current_student.sha256,
            "optimizer_step": school.current_student.optimizer_step,
            "numeric_maximum": record.get("numeric_maximum"),
            "provider_dimensions": record.get("provider_dimensions", []),
            "actual_neural_updates": 0,
        }
    record = _runtime_checkpoints._persist(
        run_dir, _runtime_checkpoints._with_delivery_outbox(record, (event,)))
    _runtime_checkpoints._reconcile_delivery_outbox(run_dir, record)
    return record


def _adopt_prepared_successor(
        mx, run_dir, receipt, grade_a_course, source_root, graph,
        parameters, optimizer, staged, *, reserve_gib,
        require_complete_profile_boundary, materialize_prepared_successor,
        profile_transition, commit_prepared_successor):
    """Adopt the exact compiled successor after upstream live revalidation."""
    from bilqis_mlx.factory.candidate_realizations import admitted_candidate_graph

    predecessor = _runtime_admission._require_executable_factory_admission(
        run_dir, receipt, graph)
    successor = staged.successor
    successor.verify_successor_of(predecessor)
    program = _factory_schedule.schedule_program_from_executable_release(predecessor)
    school = _runtime_state._state_from_json(receipt["school"], program)
    successor_program = _factory_schedule.schedule_program_from_executable_release(successor)
    topology = _curriculum_scheduler.classify_schedule_topology(program, successor_program)
    if topology is _curriculum_scheduler.ScheduleTopology.APPEND_GRADE:
        require_complete_profile_boundary(program, school, receipt)
    next_graph = (admitted_candidate_graph(staged, graph)
                  if successor.transition.semantic_geometry ==
                  _factory_executable_release.SemanticGeometryChange.APPEND_ONLY_EXPANSION
                  else graph)
    materialized = materialize_prepared_successor(
        mx, run_dir, receipt, school.current_student, successor,
        graph, parameters, optimizer, next_graph, reserve_gib=reserve_gib)
    next_state, revised_grade, _ = profile_transition(program, successor_program, school)
    compatibility_course = _compatibility_executable_projection.legacy_course_for_profile(
        grade_a_course, source_root, successor.profile)
    record = commit_prepared_successor(
        run_dir, receipt, predecessor, successor, program, successor_program,
        school, next_state, materialized, compatibility_course,
        topology=topology, revised_grade=revised_grade)
    return (materialized.parameters, materialized.optimizer, materialized.graph,
            record, compatibility_course)
