"""Executable release-adoption facade over cohesive transaction owners."""
from __future__ import annotations

import bilqis_mlx.compatibility.executable_projection as _compatibility_executable_projection
import bilqis_mlx.curriculum.scheduler as _curriculum_scheduler
import bilqis_mlx.factory.executable_release as _factory_executable_release
import bilqis_mlx.factory.live_answers as _factory_live_answers
import bilqis_mlx.runtime.admission as _runtime_admission
import bilqis_mlx.runtime.checkpoints as _runtime_checkpoints
import bilqis_mlx.runtime.state as _runtime_state
import bilqis_mlx.source_adapters.school as _source_adapters_school
import bilqis_mlx.vocabulary_growth as _bilqis_mlx_vocabulary_growth

from ._release_adoption import catalog as _catalog
from ._release_adoption import core as _core
from ._release_adoption import numeric as _numeric
from ._release_adoption import prepared as _prepared
from ._release_adoption import profile as _profile


_UNSPECIFIED_DEBT_CADENCE_POLICY = _core._UNSPECIFIED_DEBT_CADENCE_POLICY
SOURCE_PRESENTATION_ADMITTED_PROVIDER_MISSING = (
    _core.SOURCE_PRESENTATION_ADMITTED_PROVIDER_MISSING)

_ensure_factory_admission = _core._ensure_factory_admission
_migrate_executable_release = _core._migrate_executable_release
_ensure_executable_release = _core._ensure_executable_release
_cached_schedule_program = _core._cached_schedule_program
_schedule_for_receipt = _core._schedule_for_receipt
_verify_profile_successor = _core._verify_profile_successor
_grade_a_member_context_revision_required = (
    _core._grade_a_member_context_revision_required)
_source_presentation_revision_required = (
    _core._source_presentation_revision_required)
_profile_transition = _core._profile_transition

_profile_championship_state = _profile._profile_championship_state
_profile_adoption_receipt = _profile._profile_adoption_receipt

_require_complete_profile_boundary = _catalog._require_complete_profile_boundary
_catalog_boundary_evidence = _catalog._catalog_boundary_evidence
_catalog_adoption_receipt = _catalog._catalog_adoption_receipt
_catalog_adoption_event = _catalog._catalog_adoption_event

PreparedSuccessorMaterialization = _prepared.PreparedSuccessorMaterialization
_materialize_prepared_successor = _prepared._materialize_prepared_successor
_wide_numeric_entry_rebind_due = _numeric._wide_numeric_entry_rebind_due


def _adopt_executable_profile(
        run_dir, receipt, grade_a_course, source_root, graph, profile, *,
        compiled_successor=None, allow_mastery_debt=False,
        debt_cadence_policy=_UNSPECIFIED_DEBT_CADENCE_POLICY,
        invalidate_assessment_evidence=False):
    # Keep the admission guard explicit at the public transaction boundary.
    # The private owner revalidates it again before mutation.
    _runtime_admission._require_executable_factory_admission(
        run_dir, receipt, graph)
    return _profile._adopt_executable_profile(
        run_dir, receipt, grade_a_course, source_root, graph, profile,
        compiled_successor=compiled_successor,
        allow_mastery_debt=allow_mastery_debt,
        debt_cadence_policy=debt_cadence_policy,
        invalidate_assessment_evidence=invalidate_assessment_evidence,
        catalog_boundary_evidence=_catalog_boundary_evidence,
        profile_transition=_profile_transition,
        verify_profile_successor=_verify_profile_successor)


def _adopt_source_presentation_revision_if_needed(
        run_dir, receipt, grade_a_course, source_root, graph, predecessor):
    return _profile._adopt_source_presentation_revision_if_needed(
        run_dir, receipt, grade_a_course, source_root, graph, predecessor,
        source_presentation_revision_required=_source_presentation_revision_required,
        adopt_executable_profile=_adopt_executable_profile)


def _catalog_epoch_state(
        receipt, predecessor, successor, school, next_state,
        transition, grown, mastery_debt, *, allow_mastery_debt, appended):
    return _catalog._catalog_epoch_state(
        receipt, predecessor, successor, school, next_state,
        transition, grown, mastery_debt,
        allow_mastery_debt=allow_mastery_debt, appended=appended,
        profile_championship_state=_profile_championship_state)


def _adopt_catalog_profile(
        mx, run_dir, receipt, grade_a_course, source_root, graph,
        parameters, optimizer, transition, *, reserve_gib, allow_mastery_debt=False,
        compiled_successor=None):
    return _catalog._adopt_catalog_profile(
        mx, run_dir, receipt, grade_a_course, source_root, graph,
        parameters, optimizer, transition, reserve_gib=reserve_gib,
        allow_mastery_debt=allow_mastery_debt,
        compiled_successor=compiled_successor,
        verify_profile_successor=_verify_profile_successor,
        profile_transition=_profile_transition,
        materialize_prepared_successor=_materialize_prepared_successor,
        profile_championship_state=_profile_championship_state)


def _adopt_jit_proposal(mx, run_dir, receipt, grade_a_course, source_root, graph,
                        parameters, optimizer, session, proposal, *, reserve_gib):
    return _prepared._adopt_jit_proposal(
        mx, run_dir, receipt, grade_a_course, source_root, graph,
        parameters, optimizer, session, proposal, reserve_gib=reserve_gib,
        adopt_prepared_successor=_adopt_prepared_successor)


def _commit_prepared_successor(
        run_dir, receipt, predecessor, successor,
        previous_program, successor_program, school, next_state,
        materialization, compatibility_course, *, topology, revised_grade):
    return _prepared._commit_prepared_successor(
        run_dir, receipt, predecessor, successor,
        previous_program, successor_program, school, next_state,
        materialization, compatibility_course,
        topology=topology, revised_grade=revised_grade,
        profile_championship_state=_profile_championship_state,
        profile_adoption_receipt=_profile_adoption_receipt,
        catalog_adoption_event=_catalog_adoption_event)


def _adopt_prepared_successor(
        mx, run_dir, receipt, grade_a_course, source_root, graph,
        parameters, optimizer, staged, *, reserve_gib):
    return _prepared._adopt_prepared_successor(
        mx, run_dir, receipt, grade_a_course, source_root, graph,
        parameters, optimizer, staged, reserve_gib=reserve_gib,
        require_complete_profile_boundary=_require_complete_profile_boundary,
        materialize_prepared_successor=_materialize_prepared_successor,
        profile_transition=_profile_transition,
        commit_prepared_successor=_commit_prepared_successor)


def _advance_numeric_profile(run_dir, receipt, grade_a_course, source_root, graph,
                             course, release, program, *, numeric_staircase):
    return _numeric._advance_numeric_profile(
        run_dir, receipt, grade_a_course, source_root, graph,
        course, release, program, numeric_staircase=numeric_staircase,
        adopt_executable_profile=_adopt_executable_profile)


def _auto_adopt_known_grade_boundary(
        mx, run_dir, receipt, course, grade_a_course, source_root, manifest,
        parameters, optimizer, graph, *, reserve_gib, full_grade_b,
        numeric_staircase):
    return _numeric._auto_adopt_known_grade_boundary(
        mx, run_dir, receipt, course, grade_a_course, source_root, manifest,
        parameters, optimizer, graph, reserve_gib=reserve_gib,
        full_grade_b=full_grade_b, numeric_staircase=numeric_staircase,
        adopt_executable_profile=_adopt_executable_profile,
        adopt_catalog_profile=_adopt_catalog_profile)
