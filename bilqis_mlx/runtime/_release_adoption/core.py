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
