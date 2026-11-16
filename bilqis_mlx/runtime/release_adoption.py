"""Executable release, profile and JIT adoption transactions."""
from __future__ import annotations

from .topology_lifecycle import topology_for_checkpoint as _topology_for_checkpoint

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


def _ensure_factory_admission(run_dir, receipt, course, graph):
    """Neural-inert migration for historical runs that predate FactoryRelease."""
    if receipt.get("factory_admission") is not None:
        _runtime_admission._require_factory_admission(run_dir, receipt, course)
        return receipt
    school = _runtime_state._state_from_json(receipt["school"], _schedule_for_receipt(run_dir, receipt, course))
    release, release_file, admission = _runtime_admission._factory_admission(
        run_dir, course, school.current_student, _runtime_state._fingerprint(graph))
    migrated = {**receipt,
                "factory_release_sha256": release.release_sha256,
                "factory_release_file": release_file,
                "factory_admission": _dataclasses.asdict(admission)}
    record = _runtime_checkpoints._advance(run_dir, migrated, school, persist=False)
    event = {"event": "SCHOOL_FACTORY_RELEASE_MIGRATED",
             "generation": record["generation"],
             "grade": school.grade,
             "factory_release_sha256": release.release_sha256,
             "student_sha256": school.current_student.sha256,
             "optimizer_step": school.current_student.optimizer_step,
             "actual_neural_updates": 0}
    record = _runtime_checkpoints._persist(run_dir, _runtime_checkpoints._with_delivery_outbox(record, (event,)))
    _runtime_checkpoints._reconcile_delivery_outbox(run_dir, record)
    _runtime_admission._require_factory_admission(run_dir, record, course)
    return record


def _migrate_executable_release(run_dir, receipt, course, grade_a_course, source_root, graph):
    school = _runtime_state._state_from_json(receipt["school"], _schedule_for_receipt(run_dir, receipt, course))
    release, program, _ = _compatibility_executable_projection.compile_projected_executable_release(
        course, grade_a_course, source_root, graph)
    rebound = _dataclasses.replace(school, course_digest=program.digest())
    _runtime_state._state_from_json(_dataclasses.asdict(rebound), program)
    release, release_file, admission = _runtime_admission._executable_factory_admission(
        run_dir, release, rebound.current_student,
        receipt["semantic_graph_sha256"], graph)
    migrated = dict(receipt)
    migrated.update({
        "factory_release_sha256": release.release_sha256,
        "factory_release_file": release_file,
        "factory_release_schema": release.schema,
        "factory_admission_v2": _dataclasses.asdict(admission),
        "live_rubric_sha256": program.grades[rebound.grade_index].assessment_sha256,
        **_compatibility_executable_projection.legacy_execution_metadata(course),
    })
    return migrated, release, program, rebound


def _ensure_executable_release(run_dir, receipt, course, grade_a_course, source_root, graph):
    if receipt.get("factory_admission_v2") is None:
        migrated, release, program, rebound = _migrate_executable_release(
            run_dir, receipt, course, grade_a_course, source_root, graph)
        receipt = _runtime_checkpoints._advance(run_dir, migrated, rebound)
        _runtime_admission._require_executable_factory_admission(run_dir, receipt, graph)
        return receipt, release, program
    release = _runtime_admission._require_executable_factory_admission(run_dir, receipt, graph)
    return receipt, release, _factory_schedule.schedule_program_from_executable_release(release)


@_functools.lru_cache(maxsize=32)
def _cached_schedule_program(run_dir_string, release_sha256, release_file):
    release = _runtime_admission._read_executable_factory_release_artifact(
        _pathlib.Path(run_dir_string), {
            "factory_release_sha256": release_sha256,
            "factory_release_file": release_file,
        })
    return _factory_schedule.schedule_program_from_executable_release(release)


def _schedule_for_receipt(run_dir, receipt, course):
    if receipt.get("factory_admission_v2") is not None:
        return _cached_schedule_program(
            str(_pathlib.Path(run_dir).resolve()),
            receipt["factory_release_sha256"],
            receipt["factory_release_file"],
        )
    if isinstance(course, _factory_schedule.ScheduleProgram):
        return course
    from bilqis_mlx.compatibility.schedule_program import schedule_program_from_legacy_course

    if receipt.get("factory_admission") is not None:
        # A v1 run already owns an immutable admitted course. Reconstruct the
        # scheduler from that sealed artifact instead of asking today's source
        # constructors to reproduce yesterday's byte identity.
        release = _runtime_admission._read_factory_release(_pathlib.Path(run_dir), receipt)
        return schedule_program_from_legacy_course(release.course)
    return schedule_program_from_legacy_course(course)


def _verify_profile_successor(predecessor, successor, graph, profile):
    """Require the compiled successor to match the requested catalog and profile."""
    successor.verify_successor_of(predecessor)
    successor.verify_semantic_catalog(graph)
    if successor.profile != profile:
        raise ValueError("FACTORY_EXECUTABLE_PROFILE_TRANSITION_MISMATCH")


_UNSPECIFIED_DEBT_CADENCE_POLICY = object()


SOURCE_PRESENTATION_ADMITTED_PROVIDER_MISSING = (
    "FACTORY_SOURCE_PRESENTATION_ADMITTED_PROVIDER_MISSING")


def _grade_a_member_context_revision_required(predecessor, registry=None) -> bool:
    """Detect the authorized neural-inert expansion of MEMBER source context."""
    from bilqis_mlx.source_adapters.grade_a_presentation import (
        IRRELEVANT_CONTEXT_VARIATION, MEMBER_CONTEXT_VARIATION,
    )
    capability = "A.MEMBER"
    execution = predecessor.execution_plan.capability_map.get(capability)
    binding = predecessor.source_bindings.by_capability.get(capability)
    if execution is None or binding is None:
        return False
    admitted = next((
        provider for provider in predecessor.source_adapters
        if provider.adapter_id == execution.provider_id
    ), None)
    if admitted is None:
        raise ValueError(SOURCE_PRESENTATION_ADMITTED_PROVIDER_MISSING)
    registry = registry or _source_adapters_school.live_source_registry()
    current = registry.require(
        binding.generator_id, binding.oracle_id).descriptor
    authorized = (MEMBER_CONTEXT_VARIATION, IRRELEVANT_CONTEXT_VARIATION)
    return any(
        variation in current.variation_axes and variation not in admitted.variation_axes
        for variation in authorized
    )


def _source_presentation_revision_required(predecessor, registry=None) -> bool:
    """Collect explicitly authorized neural-inert source-presentation revisions."""
    registry = registry or _source_adapters_school.live_source_registry()
    return _grade_a_member_context_revision_required(predecessor, registry)


def _profile_transition(previous_program, successor_program, school, *,
                        mastery_debt=None,
                        debt_cadence_policy=_UNSPECIFIED_DEBT_CADENCE_POLICY):
    topology = _curriculum_scheduler.classify_schedule_topology(previous_program, successor_program)
    appended = topology is _curriculum_scheduler.ScheduleTopology.APPEND_GRADE
    explicit_policy = debt_cadence_policy is not _UNSPECIFIED_DEBT_CADENCE_POLICY
    policy = school.debt_cadence_policy if not explicit_policy else debt_cadence_policy
    if (policy is not None and not isinstance(
            policy, _curriculum_scheduler.DebtCadencePolicy)):
        raise ErrorBus.legacy_error(SCHOOL.SCHEDULE.INVALID_DEBT_CADENCE_POLICY)
    if topology is _curriculum_scheduler.ScheduleTopology.UNCHANGED and mastery_debt is None:
        next_state = (school if policy == school.debt_cadence_policy else
                      _dataclasses.replace(school, debt_cadence_policy=policy))
        _curriculum_scheduler.verify_state(successor_program, next_state)
        return next_state, None, False
    revised = topology in (
        _curriculum_scheduler.ScheduleTopology.UNCHANGED,
        _curriculum_scheduler.ScheduleTopology.SAME_GRADE_EXPANSION,
        _curriculum_scheduler.ScheduleTopology.SAME_GRADE_REVISION)
    if appended:
        if mastery_debt is None and school.stage == "AWAITING_NEXT_GRADE_WITH_DEBT":
            mastery_debt = school.carried_mastery_debt
        next_state = (_curriculum_scheduler.append_next_grade_with_debt(
                previous_program, successor_program, school, mastery_debt)
             if mastery_debt is not None else
             _curriculum_scheduler.adopt_appended_program(
                 previous_program, successor_program, school))
        if explicit_policy:
            next_state = _dataclasses.replace(
                next_state, debt_cadence_policy=policy)
        _curriculum_scheduler.verify_state(successor_program, next_state)
        return next_state, None, True
    if revised and mastery_debt is None:
        changed = tuple(
            index for index, (old_grade, new_grade) in
            enumerate(zip(previous_program.grades, successor_program.grades))
            if (old_grade.capabilities != new_grade.capabilities or
                old_grade.teaching_stages != new_grade.teaching_stages))
        if len(changed) == 1 and changed[0] < school.grade_index:
            next_state, revised_grade = _curriculum_scheduler.adopt_expanded_prior_grade(
                previous_program, successor_program, school)
        else:
            next_state, revised_grade = _curriculum_scheduler.adopt_revised_program(
                previous_program, successor_program, school)
        next_state = _dataclasses.replace(
            next_state, debt_cadence_policy=policy)
        _curriculum_scheduler.verify_state(successor_program, next_state)
        return next_state, revised_grade, False
    raise ErrorBus.legacy_error(FACTORY.EXECUTION.EXECUTABLE_PROFILE_TRANSITION_UNSUPPORTED)


def _profile_championship_state(
        receipt, predecessor, successor, school, next_state, *, appended,
        mastery_debt=None):
    exam = (receipt.get("debt_admission_boundary_exam") if mastery_debt is not None
            else receipt.get("last_exam")) or {}
    history = list(receipt.get("championship_epoch_history", ()))
    identity = _learning_championship_identity.build_school_identity(
        course_sha256=successor.execution_plan.curriculum_sha256,
        semantic_graph_sha256=receipt["semantic_graph_sha256"],
        parameter_shapes=receipt["parameter_shapes"],
        factory_release_sha256=successor.release_sha256)
    if appended:
        from bilqis_mlx.learning.mentor_epoch import begin_epoch, begin_debt_epoch
        boundary = {
            "checkpoint_sha256": exam.get("student_sha256"),
            "rubric_sha256": exam.get("exam_rubric_sha256"),
            "cohort_sha256": exam.get("cohort_sha256"),
            "scores": exam.get("scores"),
        }
        arguments = dict(
            admitted_baseline=_dataclasses.asdict(next_state.current_student),
            introduced_grade=next_state.grade,
            source_graph_sha256=receipt["semantic_graph_sha256"],
            previous_capabilities=tuple(
                item.capability_id for item in predecessor.execution_plan.capabilities))
        if mastery_debt is not None:
            epoch = begin_debt_epoch(**arguments,
                previous_checkpoint=_dataclasses.asdict(school.current_student),
                previous_boundary_exam=boundary, previous_mastery_debt=mastery_debt)
        else:
            epoch = begin_epoch(**arguments,
                previous_graduate=_dataclasses.asdict(school.current_student),
                previous_graduation_exam=boundary)
        if receipt.get("mentor_epoch") is not None:
            history.append(receipt["mentor_epoch"])
        epoch["settled_matchups"] = _copy.deepcopy(
            (receipt.get("mentor_epoch") or {}).get("settled_matchups", {}))
        epoch["championship_school_identity"] = identity
        return identity, epoch, history
    epoch = receipt.get("mentor_epoch")
    if epoch is not None:
        epoch, identity_event = _learning_championship_identity.enforce_school_identity(
            epoch, identity,
            generation=receipt["generation"] + 1,
            student=_dataclasses.asdict(school.current_student))
        if identity_event:
            history.append(receipt["mentor_epoch"])
    return identity, epoch, history


def _profile_adoption_receipt(
        receipt, compatibility_course, successor, successor_program,
        release_file, admission, identity, epoch, history, revised_grade,
        graph, *, invalidate_assessment_evidence=False):
    heads = _factory_executable_release.answer_heads_from_executable_release(successor, graph)
    numeric_values = heads.get("numeric_active", {}).get("values")
    candidate = {
        **receipt,
        "curriculum_mode": compatibility_course.version,
        "config": {**receipt["config"], "answer_heads": heads},
        "live_rubric_sha256": successor_program.grades[-1].assessment_sha256,
        "factory_release_sha256": successor.release_sha256,
        "factory_release_file": release_file,
        "factory_release_schema": successor.schema,
        "factory_admission_v2": _dataclasses.asdict(admission),
        "championship_school_identity": identity,
        "mentor_epoch": epoch,
        "championship_epoch_history": history,
        "last_exam": (
            None if revised_grade is not None or invalidate_assessment_evidence
            else receipt.get("last_exam")),
    }
    if numeric_values is not None:
        candidate["numeric_maximum"] = len(numeric_values) - 1
    candidate.pop("qualification_cohort_v2", None)
    if invalidate_assessment_evidence:
        candidate.pop("fixed_frontier_exam", None)
        candidate.pop("last_generalization_cohort_v2", None)
    return candidate


def _adopt_executable_profile(
        run_dir, receipt, grade_a_course, source_root, graph, profile, *,
        compiled_successor=None, allow_mastery_debt=False,
        debt_cadence_policy=_UNSPECIFIED_DEBT_CADENCE_POLICY,
        invalidate_assessment_evidence=False):
    """Adopt one same-ABI v2 profile change without release-name dispatch."""
    predecessor = _runtime_admission._require_executable_factory_admission(run_dir, receipt, graph)
    previous_program = _factory_schedule.schedule_program_from_executable_release(predecessor)
    school = _runtime_state._state_from_json(receipt["school"], previous_program)
    compatibility_course = _compatibility_executable_projection.legacy_course_for_profile(
        grade_a_course, source_root, profile)
    successor = compiled_successor or _factory_executable_release.compile_successor_profile_release(
        predecessor,
        profile,
        _source_adapters_school.live_source_registry(),
        _factory_live_answers.live_answer_registry(),
        source_root=source_root,
        graph=graph,
        verification_seed=2026101906)
    _verify_profile_successor(predecessor, successor, graph, profile)
    successor_program = _factory_schedule.schedule_program_from_executable_release(successor)
    mastery_debt = None
    if allow_mastery_debt:
        _, mastery_debt = _catalog_boundary_evidence(
            predecessor, previous_program, school, receipt, allow_mastery_debt=True)
    next_state, revised_grade, appended = _profile_transition(
        previous_program, successor_program, school, mastery_debt=mastery_debt,
        debt_cadence_policy=debt_cadence_policy)
    successor, release_file, admission = _runtime_admission._executable_factory_admission(
        run_dir, successor, next_state.current_student,
        receipt["semantic_graph_sha256"], graph)
    identity, epoch, history = _profile_championship_state(
        receipt, predecessor, successor, school, next_state, appended=appended,
        mastery_debt=mastery_debt)
    candidate = _profile_adoption_receipt(
        receipt, compatibility_course, successor, successor_program,
        release_file, admission, identity, epoch, history, revised_grade, graph,
        invalidate_assessment_evidence=invalidate_assessment_evidence)
    if allow_mastery_debt:
        candidate["last_exam"] = receipt["debt_admission_boundary_exam"]
        candidate.pop("fixed_frontier_exam", None)
    record = _runtime_checkpoints._advance(
        run_dir, candidate, next_state,
        result="ACTIVE_GRADE_" + next_state.grade, persist=False)
    event = {
        "event": "SCHOOL_EXECUTION_PROFILE_ADOPTED",
        "generation": record["generation"],
        "grade": next_state.grade,
        "profile_id": successor.profile.profile_id,
        "transition_kind": (
            "APPEND_GRADE" if appended else
            "REVISE_SOURCE" if (
                revised_grade is None and successor.profile == predecessor.profile and
                previous_program == successor_program) else
            "REVISE_PROFILE"),
        "revised_grade": revised_grade,
        "debt_admission": allow_mastery_debt,
        "carried_mastery_debt": list(next_state.carried_mastery_debt),
        "previous_factory_release_sha256": predecessor.release_sha256,
        "factory_release_sha256": successor.release_sha256,
        "student_sha256": school.current_student.sha256,
        "optimizer_step": school.current_student.optimizer_step,
        "numeric_maximum": record.get("numeric_maximum"),
        "actual_neural_updates": 0,
    }
    record = _runtime_checkpoints._persist(
        run_dir, _runtime_checkpoints._with_delivery_outbox(record, (event,)))
    _runtime_checkpoints._reconcile_delivery_outbox(run_dir, record)
    return record, compatibility_course, successor, successor_program


def _adopt_source_presentation_revision_if_needed(
        run_dir, receipt, grade_a_course, source_root, graph, predecessor):
    """Adopt authorized source presentation revisions with zero neural updates."""
    program = _factory_schedule.schedule_program_from_executable_release(predecessor)
    compatibility_course = _compatibility_executable_projection.legacy_course_for_profile(
        grade_a_course, source_root, predecessor.profile)
    registry = _source_adapters_school.live_source_registry()
    if not _source_presentation_revision_required(predecessor, registry):
        return receipt, compatibility_course, predecessor, program
    successor = _factory_executable_release.compile_successor_profile_release(
        predecessor, predecessor.profile, registry,
        _factory_live_answers.live_answer_registry(),
        source_root=source_root, graph=graph, verification_seed=2026102701)
    return _adopt_executable_profile(
        run_dir, receipt, grade_a_course, source_root, graph,
        predecessor.profile, compiled_successor=successor,
        invalidate_assessment_evidence=True)


def _require_complete_profile_boundary(program, school, receipt):
    """Require one complete perfect cumulative exam for the admitted prefix."""
    if school.stage != "AWAITING_NEXT_GRADE":
        raise ValueError("FACTORY_PROFILE_EXPANSION_NOT_AT_GRADE_BOUNDARY")
    exam = receipt.get("last_exam") or {}
    expected = {
        capability.id: capability.exam_item_count
        for grade in program.grades for capability in grade.capabilities
    }
    if (exam.get("student_sha256") != school.current_student.sha256 or
            exam.get("optimizer_step") != school.current_student.optimizer_step or
            exam.get("scores") != {
                capability: {"correct": count, "total": count}
                for capability, count in expected.items()}):
        raise ValueError(
            "FACTORY_PROFILE_EXPANSION_REQUIRES_COMPLETE_PERFECT_PREFIX")


def _catalog_boundary_evidence(
        predecessor, previous_program, school, receipt, *, allow_mastery_debt):
    if not allow_mastery_debt:
        _require_complete_profile_boundary(previous_program, school, receipt)
        return receipt.get("last_exam") or {}, ()
    exam = receipt.get("debt_admission_boundary_exam") or {}
    expected = {
        cap.id: cap.exam_item_count
        for grade in previous_program.grades for cap in grade.capabilities
    }
    from bilqis_mlx.factory.assessment import assessment_scope_contract
    contract = assessment_scope_contract(predecessor, tuple(expected))
    if (exam.get("student_sha256") != school.current_student.sha256 or
            exam.get("optimizer_step") != school.current_student.optimizer_step or
            exam.get("factory_release_sha256") != predecessor.release_sha256 or
            exam.get("exam_rubric_sha256") != contract.rubric_sha256 or
            set(exam.get("scores", {})) != set(expected) or
            any(score.get("total") != expected[cap]
                for cap, score in exam.get("scores", {}).items())):
        raise ValueError("DEBT_ADMISSION_REQUIRES_EXACT_COMPLETE_BOUNDARY")
    mastery_debt = tuple(
        cap for cap in expected
        if exam["scores"][cap]["correct"] != expected[cap])
    return exam, mastery_debt


def _catalog_epoch_state(
        receipt, predecessor, successor, school, next_state,
        transition, grown, mastery_debt, *, allow_mastery_debt, appended):
    graph_receipt = {
        **receipt,
        "semantic_graph_sha256": _runtime_state._fingerprint(transition.graph),
        "parameter_shapes": {name: list(value.shape) for name, value in grown.items()},
    }
    identity, epoch, history = _profile_championship_state(
        graph_receipt, predecessor, successor, school, next_state,
        appended=appended,
        mastery_debt=mastery_debt if allow_mastery_debt else None)
    return epoch, history, identity


def _catalog_adoption_receipt(
        receipt, compatibility_course, successor, successor_program,
        release_file, admission, transition, grown, epoch, history,
        identity):
    graph_sha = _runtime_state._fingerprint(transition.graph)
    heads = _factory_executable_release.answer_heads_from_executable_release(successor, transition.graph)
    numeric_values = heads.get("numeric_active", {}).get("values")
    updated = {
        **receipt,
        "curriculum_mode": compatibility_course.version,
        "semantic_graph_sha256": graph_sha,
        "factory_release_sha256": successor.release_sha256,
        "factory_release_file": release_file,
        "factory_release_schema": successor.schema,
        "factory_admission_v2": _dataclasses.asdict(admission),
        "parameter_shapes": {
            name: list(value.shape) for name, value in grown.items()},
        "championship_school_identity": identity,
        "config": {
            **receipt["config"],
            "vocab_size": len(transition.graph["tokens"]),
            "answer_heads": heads,
        },
        "live_rubric_sha256": successor_program.grades[-1].assessment_sha256,
        "numeric_maximum": (
            len(numeric_values) - 1 if numeric_values is not None else
            receipt.get("numeric_maximum")),
        "numeric_scope_final_maximum": transition.numeric_scope_final_maximum,
        "mentor_epoch": epoch,
        "championship_epoch_history": history,
        "last_exam": None,
    }
    updated.pop("qualification_cohort_v2", None)
    return updated


def _catalog_adoption_event(
        record, school, pointer, successor, growth, grade: str) -> dict:
    return {
        "event": "SCHOOL_SEMANTIC_CATALOG_PROFILE_ADOPTED",
        "generation": record["generation"],
        "grade": grade,
        "profile_id": successor.profile.profile_id,
        "semantic_geometry": successor.transition.semantic_geometry,
        "growth": growth,
        "previous_student_sha256": school.current_student.sha256,
        "student_sha256": pointer.sha256,
        "optimizer_step": pointer.optimizer_step,
        "numeric_maximum": record.get("numeric_maximum"),
        "factory_release_sha256": successor.release_sha256,
        "actual_neural_updates": 0,
    }


def _adopt_catalog_profile(
        mx, run_dir, receipt, grade_a_course, source_root, graph,
        parameters, optimizer, transition, *, reserve_gib, allow_mastery_debt=False,
        compiled_successor=None):
    """Adopt one append-only semantic ABI/profile expansion with zero updates."""
    predecessor = _runtime_admission._require_executable_factory_admission(run_dir, receipt, graph)
    previous_program = _factory_schedule.schedule_program_from_executable_release(predecessor)
    school = _runtime_state._state_from_json(receipt["school"], previous_program)
    exam, mastery_debt = _catalog_boundary_evidence(
        predecessor, previous_program, school, receipt,
        allow_mastery_debt=allow_mastery_debt)
    compatibility_course = _compatibility_executable_projection.legacy_course_for_profile(
        grade_a_course, source_root, transition.profile)
    successor = compiled_successor or _factory_executable_release.compile_successor_profile_release(
        predecessor,
        transition.profile,
        _source_adapters_school.live_source_registry(),
        _factory_live_answers.live_answer_registry(),
        source_root=source_root,
        graph=transition.graph,
        verification_seed=2026101907)
    _verify_profile_successor(predecessor, successor, transition.graph, transition.profile)
    if (successor.transition is None or
            successor.transition.semantic_geometry != "APPEND_ONLY_EXPANSION"):
        raise ValueError("FACTORY_CATALOG_TRANSITION_NOT_APPEND_ONLY")
    successor_program = _factory_schedule.schedule_program_from_executable_release(successor)
    next_state, _, appended = _profile_transition(
        previous_program, successor_program, school,
        mastery_debt=mastery_debt if allow_mastery_debt else None)

    materialized = _materialize_prepared_successor(
        mx, run_dir, {**receipt, "last_exam": exam}, school.current_student, successor,
        graph, parameters, optimizer, transition.graph, reserve_gib=reserve_gib)
    grown, own_optimizer, growth = (
        materialized.parameters, materialized.optimizer, materialized.growth)
    pointer = materialized.student
    next_state = _dataclasses.replace(next_state, current_student=pointer)
    successor, release_file, admission = _runtime_admission._executable_factory_admission(
        run_dir, successor, pointer, _runtime_state._fingerprint(transition.graph),
        transition.graph)
    epoch, history, identity = _catalog_epoch_state(
        receipt, predecessor, successor, school, next_state,
        transition, grown, mastery_debt,
        allow_mastery_debt=allow_mastery_debt, appended=appended)
    updated = _catalog_adoption_receipt(
        receipt, compatibility_course, successor, successor_program,
        release_file, admission, transition, grown, epoch, history,
        identity)
    updated["last_exam"] = materialized.rebaselined_exam
    record = _runtime_checkpoints._advance(
        run_dir, updated, next_state, model_bundle=pointer.filename,
        result="ACTIVE_GRADE_" + next_state.grade, persist=False)
    event = _catalog_adoption_event(
        record, school, pointer, successor, growth, next_state.grade)
    record = _runtime_checkpoints._persist(
        run_dir, _runtime_checkpoints._with_delivery_outbox(record, (event,)))
    _runtime_checkpoints._reconcile_delivery_outbox(run_dir, record)
    return grown, own_optimizer, transition.graph, record, compatibility_course


def _adopt_jit_proposal(mx, run_dir, receipt, grade_a_course, source_root, graph,
                       parameters, optimizer, session, proposal, *, reserve_gib):
    """Use the existing student/own-AdamW admission transaction for a fresh JIT choice."""
    from bilqis_mlx.runtime.jit_adoption import verify_current_implementations
    predecessor = _runtime_admission._require_executable_factory_admission(run_dir, receipt, graph)
    program = _factory_schedule.schedule_program_from_executable_release(predecessor)
    school = _runtime_state._state_from_json(receipt["school"], program)
    staged = session.resolve_ready_proposal(school.current_student, proposal)
    successor = staged.successor
    verify_current_implementations(successor, _source_adapters_school.live_source_registry(), _factory_live_answers.live_answer_registry())
    return _adopt_prepared_successor(
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

    from .assessment import _load_executable_cohort
    from ..learning.student_ops import _predictions
    from ..fixed_frontier import load_frontier, load_frontier_cohort, rebaseline_frontier_exam

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
        materialization, compatibility_course, *, topology, revised_grade):
    """Commit one materialized successor and its original transition intent."""
    student = materialization.student
    next_state = _dataclasses.replace(next_state, current_student=student)
    graph = materialization.graph
    graph_sha = _runtime_state._fingerprint(graph)
    shapes = {name: list(value.shape) for name, value in materialization.parameters.items()}
    successor, release_file, admission = _runtime_admission._executable_factory_admission(
        run_dir, successor, student, graph_sha, graph)
    appended = topology is _curriculum_scheduler.ScheduleTopology.APPEND_GRADE
    identity, epoch, history = _profile_championship_state(
        {**receipt, "semantic_graph_sha256": graph_sha, "parameter_shapes": shapes},
        predecessor, successor, school, next_state, appended=appended)
    candidate = _profile_adoption_receipt(
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
        event = _catalog_adoption_event(
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
            "actual_neural_updates": 0,
        }
    record = _runtime_checkpoints._persist(
        run_dir, _runtime_checkpoints._with_delivery_outbox(record, (event,)))
    _runtime_checkpoints._reconcile_delivery_outbox(run_dir, record)
    return record


def _adopt_prepared_successor(
        mx, run_dir, receipt, grade_a_course, source_root, graph,
        parameters, optimizer, staged, *, reserve_gib):
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
        _require_complete_profile_boundary(program, school, receipt)
    next_graph = (admitted_candidate_graph(staged, graph)
                  if successor.transition.semantic_geometry ==
                  _factory_executable_release.SemanticGeometryChange.APPEND_ONLY_EXPANSION
                  else graph)
    materialized = _materialize_prepared_successor(
        mx, run_dir, receipt, school.current_student, successor,
        graph, parameters, optimizer, next_graph, reserve_gib=reserve_gib)
    next_state, revised_grade, _ = _profile_transition(program, successor_program, school)
    compatibility_course = _compatibility_executable_projection.legacy_course_for_profile(
        grade_a_course, source_root, successor.profile)
    record = _commit_prepared_successor(
        run_dir, receipt, predecessor, successor, program, successor_program,
        school, next_state, materialized, compatibility_course,
        topology=topology, revised_grade=revised_grade)
    return (materialized.parameters, materialized.optimizer, materialized.graph,
            record, compatibility_course)


def _advance_numeric_profile(run_dir, receipt, grade_a_course, source_root, graph,
                             course, release, program, *, numeric_staircase):
    """Rebind a wide historical scope, then advance the admitted staircase."""
    if receipt.get("qualification") is not None:
        from .qualification_manifest import require
        require(release.release_sha256 in receipt["qualification"].get("allowed_releases", [receipt["qualification"]["release_sha256"]]), "FROZEN_RELEASE_DRIFT")
        return receipt, course, release, program
    initial_maximum, final_maximum = _profiles_catalog.numeric_scope_bounds()
    current = _runtime_admission._require_executable_factory_admission(
        run_dir, receipt, graph)
    active = _factory_schedule.schedule_program_from_executable_release(current)
    school = _runtime_state._state_from_json(receipt["school"], active)
    wide_unscoped_entry = _wide_numeric_entry_rebind_due(
        receipt, current, final_maximum=final_maximum)
    legacy_oversized_scope = (
        numeric_staircase and receipt.get("numeric_maximum", 0) > final_maximum)
    if ((wide_unscoped_entry or legacy_oversized_scope) and
            school.grade == active.grades[-1].id):
        receipt, course, release, program = _adopt_executable_profile(
            run_dir, {**receipt, "numeric_scope_final_maximum": final_maximum},
            grade_a_course, source_root, graph,
            _profiles_catalog.numeric_scope_profile(current, initial_maximum))
    final_scope = receipt.get("numeric_scope_final_maximum")
    if final_scope is not None:
        current = _runtime_admission._require_executable_factory_admission(
            run_dir, receipt, graph)
        active = _factory_schedule.schedule_program_from_executable_release(current)
        school = _runtime_state._state_from_json(receipt["school"], active)
        next_profile = _profiles_catalog.next_numeric_scope_profile(
            current, final_maximum=final_scope)
        if next_profile is not None and school.stage in ("AWAITING_NEXT_GRADE", "AWAITING_NEXT_GRADE_WITH_DEBT"):
            receipt, course, release, program = _adopt_executable_profile(
                run_dir, receipt, grade_a_course, source_root, graph, next_profile)
    return receipt, course, release, program


def _wide_numeric_entry_rebind_due(receipt, release, *, final_maximum: int) -> bool:
    """Recognize one-shot wide C admission, not a legitimately completed staircase."""
    profile_id = getattr(getattr(release, "profile", None), "profile_id", None)
    return (
        receipt.get("numeric_scope_final_maximum") is None and
        receipt.get("numeric_maximum") == final_maximum and
        isinstance(profile_id, str) and
        profile_id.endswith(f"/numeric-0-{final_maximum}"))


def _auto_adopt_known_grade_boundary(
        mx, run_dir, receipt, course, grade_a_course, source_root, manifest,
        parameters, optimizer, graph, *, reserve_gib, full_grade_b,
        numeric_staircase):
    """Dispatch known historical grade boundaries through runtime-owned policy."""
    import bilqis_mlx.runtime.exam_execution as _runtime_exam_execution

    release = _runtime_admission._require_executable_factory_admission(
        run_dir, receipt, graph)
    program = _factory_schedule.schedule_program_from_executable_release(release)
    school = _runtime_state._state_from_json(receipt["school"], program)
    if school.stage not in (
            "AWAITING_NEXT_GRADE", "AWAITING_NEXT_GRADE_WITH_DEBT"):
        return parameters, optimizer, graph, receipt, course, False

    if receipt.get("qualification") is not None:
        from .qualification import advance_frozen_boundary
        return advance_frozen_boundary(mx, run_dir, receipt, course, grade_a_course,
            source_root, parameters, optimizer, graph, release, school, manifest)
    transition = _profiles_catalog.next_school_transition(
        release, graph, full_boolean=full_grade_b,
        numeric_staircase=numeric_staircase,
        final_scope=receipt.get("numeric_scope_final_maximum"))
    if transition is None:
        return parameters, optimizer, graph, receipt, course, False
    allow_debt = school.stage == "AWAITING_NEXT_GRADE_WITH_DEBT"
    if allow_debt:
        receipt = _runtime_exam_execution._measure_debt_admission_boundary(
            mx, run_dir, receipt, manifest, course, source_root, parameters, graph)
    if transition.graph == graph:
        receipt, course, _, _ = _adopt_executable_profile(
            run_dir, receipt, grade_a_course, source_root, graph, transition.profile,
            allow_mastery_debt=allow_debt)
    else:
        parameters, optimizer, graph, receipt, course = _adopt_catalog_profile(
            mx, run_dir, receipt, grade_a_course, source_root, graph,
            parameters, optimizer, transition, reserve_gib=reserve_gib,
            allow_mastery_debt=allow_debt)
    return parameters, optimizer, graph, receipt, course, True
