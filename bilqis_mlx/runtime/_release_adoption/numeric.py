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
from .dimensions import advance_provider_dimensions as _advance_provider_dimensions

def _reconcile_legacy_numeric_profile(
        run_dir, receipt, grade_a_course, source_root, graph,
        course, release, program, *, numeric_staircase,
        adopt_executable_profile):
    """Repair only historical numeric admission signatures before generic policy."""
    if receipt.get("qualification") is not None:
        from ..qualification_manifest import require
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
        receipt, course, release, program = adopt_executable_profile(
            run_dir, {**receipt, "numeric_scope_final_maximum": final_maximum},
            grade_a_course, source_root, graph,
            _profiles_catalog.numeric_scope_profile(current, initial_maximum))
    return receipt, course, release, program


def _advance_numeric_profile(run_dir, receipt, grade_a_course, source_root, graph,
                             course, release, program, *, numeric_staircase,
                             adopt_executable_profile):
    """Compatibility entrypoint: legacy repair followed by generic progression."""
    receipt, course, release, program = _reconcile_legacy_numeric_profile(
        run_dir, receipt, grade_a_course, source_root, graph,
        course, release, program, numeric_staircase=numeric_staircase,
        adopt_executable_profile=adopt_executable_profile)
    if receipt.get("qualification") is not None:
        return receipt, course, release, program
    final_scope = receipt.get("numeric_scope_final_maximum")
    current = _runtime_admission._require_executable_factory_admission(
        run_dir, receipt, graph)
    try:
        from bilqis_mlx.factory.provider_dimensions import provider_dimension_state
        dimension = provider_dimension_state(current, "numeric-root")
    except ValueError:
        dimension = None
    if (dimension is not None and final_scope is not None and
            int(dimension.value) >= final_scope):
        return receipt, course, release, program
    return _advance_provider_dimensions(
        run_dir, receipt, grade_a_course, source_root, graph,
        course, release, program,
        adopt_executable_profile=adopt_executable_profile)


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
        numeric_staircase, adopt_executable_profile, adopt_catalog_profile):
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
        from ..qualification import advance_frozen_boundary
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
        receipt, course, _, _ = adopt_executable_profile(
            run_dir, receipt, grade_a_course, source_root, graph, transition.profile,
            allow_mastery_debt=allow_debt)
    else:
        parameters, optimizer, graph, receipt, course = adopt_catalog_profile(
            mx, run_dir, receipt, grade_a_course, source_root, graph,
            parameters, optimizer, transition, reserve_gib=reserve_gib,
            allow_mastery_debt=allow_debt)
    return parameters, optimizer, graph, receipt, course, True
