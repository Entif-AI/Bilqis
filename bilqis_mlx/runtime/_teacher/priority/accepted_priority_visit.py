"""Accepted C03 priority selection and one Factory candidate execution."""
from dataclasses import replace
from bilqis_mlx.errors import ErrorBus, SCHOOL
import json
from pathlib import Path
import time

from bilqis_mlx.learning.atlas_acceptance import candidate_identity_digest
from bilqis_mlx.learning.atlas_salience import salience_priority_features
from bilqis_mlx.learning.salience_contracts import ActionKind
from bilqis_mlx.learning.salience_teacher import _teacher
from bilqis_mlx.learning.learning_experiment import Settings
from bilqis_mlx.learning.teacher_lineage import restore_teacher_lineage
from bilqis_mlx.learning.teacher_visit_identity import (
    derive_teacher_visit_identity, record_teacher_visit_authority,
    record_teacher_visit_identity,
)
from bilqis_mlx.runtime.atlas_memory_retry import OOM_EXHAUSTED
from bilqis_mlx.runtime.teacher_policy_selection import select_visit_policy
from bilqis_mlx.semantics.domains import contract_digest
from .accepted_teacher_custody import (
    _accepted_parent, _c03_projection, _issue_bound_visit, _require_current_visit,
    _selection_projection, current_teacher_projection,
)
from .priority_qualification import _grade, requalify_priority
from bilqis_mlx.runtime.outcomes.issuance import context_for_selection
from .accepted_priority_candidate import execute_accepted_priority_candidate
from .accepted_priority_visit_contracts import (
    PriorityVisitResult,
    _issue_result,
    accepted_priority_school,
)

def _invalid(reason):
    ErrorBus.Raise(SCHOOL.BAMF_CURRICULUM.INVALID, reason=reason)


def _action_required_hold_reason(action_kind):
    return ('CORRECTION_ACTION_REQUIRED'
            if action_kind == ActionKind.CORRECTION
            else 'PROCEDURE_REPAIR_ACTION_REQUIRED')

def _selected_priority_result(
        run_dir, source_context, parent, cache, projection, epoch, teacher,
        qualified, option, offer, school, engine, rng, learning_settings,
        program, grade, evidence, holds, lawful_frontier, total_capabilities,
        plasticity_escape, priority_features, cadence_authorization,
        source_materialization_wall_seconds):
    capability = option.context.capability_id
    key, policy, metadata = select_visit_policy(
        engine, teacher, capability, school, rng, learning_settings,
        option.context.scope,
        {'salience_evidence': evidence[option.stable_id],
         'teacher_epoch_digest': contract_digest(epoch)},
        grade, total_capabilities=total_capabilities,
        plasticity_escape=plasticity_escape)
    metadata = {**metadata, 'how_context': context_for_selection(
        source_context.release, program, grade, school, option, teacher, metadata)}
    if cadence_authorization is not None:
        metadata = {**metadata, 'cadence': cadence_authorization.to_record()}
    selected_epoch = replace(
        epoch, current_json=json.dumps(teacher, sort_keys=True, allow_nan=False))
    selected = _selection_projection(projection, selected_epoch)
    identity = derive_teacher_visit_identity(
        selected.teacher_state,
        run_identity_sha256=parent.run_identity.digest,
        run_seed=parent.run_identity.run_seed,
        generation=parent.generation,
        accepted_manifest_sha256=cache.accepted_manifest_sha256,
        capability_id=capability,
        policy_key=key)
    recorded = record_teacher_visit_identity(selected.teacher_state, identity)
    ranking_evidence = {
        **priority_features,
        'dispatch_tier': int(dict(qualified.ranked.tiers)[option.stable_id]),
        'eligible_since': option.eligible_since,
        'downstream_unlocks': option.downstream_unlocks,
        'stable_id': option.stable_id,
    }
    recorded = record_teacher_visit_authority(recorded, identity)
    visit = _issue_bound_visit(recorded, identity)
    return _issue_result(
        'TEACHER_SELECTED', option.stable_id, offer, visit, policy,
        metadata, grade, sorted(holds), run_dir, lawful_frontier,
        ranking_evidence=ranking_evidence,
        source_materialization_wall_seconds=source_materialization_wall_seconds,
        cadence_authorization=cadence_authorization)


def _accepted_context(run_dir, source_context, school, lawful_frontier,
                      accepted_parent, planning_generation):
    if planning_generation is None:
        parent, cache = _accepted_parent(Path(run_dir))
        expected = candidate_identity_digest(parent.retained_state)
    else:
        from bilqis_mlx.runtime.priority_source_offer import _require_planning_generation
        parent = accepted_parent
        cache, _authenticated = _require_planning_generation(
            planning_generation, source_context, parent)
        if getattr(lawful_frontier, '_planning_generation', None) is not planning_generation:
            _invalid('BAMF_PRIORITY_LAWFUL_FRONTIER_BINDING_DRIFT')
        expected = planning_generation.parent_candidate_identity_sha256
    if getattr(getattr(school, 'current_student', None), 'sha256', None) != expected:
        _invalid('BAMF_PRIORITY_STUDENT_DRIFT')
    return parent, cache


def _cadence_context(cadence_authorization, lawful_frontier):
    if cadence_authorization is None:
        return None, None
    from bilqis_mlx.runtime.active_grade_cadence_contracts import (
        ActiveGradeCadenceAuthorization,
    )
    if not isinstance(cadence_authorization, ActiveGradeCadenceAuthorization):
        _invalid('BAMF_ACTIVE_GRADE_CADENCE_AUTHORITY_INVALID')
    cadence_ids = tuple(cadence_authorization.authorized_capability_ids)
    if not set(cadence_ids) <= set(lawful_frontier.ready_capability_ids):
        _invalid('BAMF_ACTIVE_GRADE_CADENCE_AUTHORITY_DRIFT')
    return cadence_ids, {'cadence': cadence_authorization.to_record()}


def _empty_priority_result(run_dir, source_context, parent, frontier, history,
                           lawful_frontier, cadence_authorization,
                           cadence_ids, cadence_metadata):
    from bilqis_mlx.runtime.lawful_teaching_frontier import (
        require_bound_lawful_teaching_frontier,
    )
    require_bound_lawful_teaching_frontier(lawful_frontier, source_context, parent)
    if (frontier is not None or history is not None
            or (lawful_frontier.ready_capability_ids and cadence_ids is None)
            or cadence_ids):
        _invalid('BAMF_PRIORITY_EMPTY_AUTHORITY_DRIFT')
    holds = sorted(
        (item.capability_id, item.code.value) for item in lawful_frontier.exclusions)
    if cadence_authorization is not None:
        disposition = cadence_authorization.disposition.value
        if disposition != 'TEACHING':
            holds.append(('__active_grade__', 'CADENCE_' + disposition))
    return _issue_result(
        'NO_ADMISSIBLE_TEACHING', None, None, None, None, cadence_metadata, None,
        holds, run_dir, lawful_frontier,
        cadence_authorization=cadence_authorization)


def select_accepted_priority_visit(
        run_dir, source_context, frontier, history, planning, offers,
        engine, school, rng, learning_settings, *, program, now,
        lawful_frontier,
        cadence_authorization=None,
        total_capabilities=None, plasticity_escape=None,
        legacy_receipt=None, adaptation=None, prior_region=None,
        accepted_parent=None, planning_generation=None, resource_holds=frozenset()):
    parent, cache = _accepted_context(
        run_dir, source_context, school, lawful_frontier,
        accepted_parent, planning_generation)
    cadence_ids, cadence_metadata = _cadence_context(
        cadence_authorization, lawful_frontier)
    if not offers and frontier is None:
        return _empty_priority_result(
            run_dir, source_context, parent, frontier, history, lawful_frontier,
            cadence_authorization, cadence_ids, cadence_metadata)
    projection = _c03_projection(parent, legacy_receipt=legacy_receipt,
                                 adaptation=adaptation, prior_region=prior_region)
    projection = current_teacher_projection(run_dir, parent, cache, projection)
    epoch = restore_teacher_lineage(projection.teacher_state)
    teacher = _teacher(epoch, school)
    if not isinstance(learning_settings, Settings):
        _invalid('BAMF_SALIENCE_CONTEXTUAL_SETTINGS_REQUIRED')
    qualified = requalify_priority(run_dir, source_context, parent, frontier, history,
                                   planning, offers, program, school, epoch, now=now,
                                   lawful_frontier=lawful_frontier,
                                   planning_generation=planning_generation)
    if cadence_ids is not None and not set(dict(qualified.offers)) <= set(cadence_ids):
        _invalid('BAMF_ACTIVE_GRADE_CADENCE_OFFER_DRIFT')
    by_id, evidence = dict(qualified.offers), dict(frontier.evidence)
    holds = [
        (item.capability_id, item.code.value)
        for item in lawful_frontier.exclusions
    ]
    holds.extend(qualified.holds)
    action_required_option_id = None
    for option in qualified.ranked.ordered:
        priority_features = salience_priority_features(
            evidence[option.stable_id], option.context.capability_id,
            option.context.scope, contract_digest(epoch))
        if option.action_kind in (ActionKind.CORRECTION, ActionKind.PROCEDURE_REPAIR):
            holds.append((option.stable_id, _action_required_hold_reason(option.action_kind)))
            if action_required_option_id is None:
                action_required_option_id = option.stable_id
            continue
        if option.context.capability_id in resource_holds:
            holds.append((option.stable_id, OOM_EXHAUSTED))
            continue
        offer = by_id[option.stable_id]
        materialization_started = time.perf_counter()
        try:
            offer.require_current(source_context, parent)
        except ValueError:
            holds.append((option.stable_id, 'SOURCE_OFFER_HELD'))
            continue
        grade = _grade(program, school, option.context.capability_id)
        if grade is None:
            _invalid('BAMF_PRIORITY_PROGRAM_INVALID')
        source_materialization_wall_seconds = max(
            0.0, time.perf_counter() - materialization_started)
        return _selected_priority_result(
            run_dir, source_context, parent, cache, projection, epoch, teacher,
            qualified, option, offer, school, engine, rng, learning_settings,
            program, grade, evidence, holds, lawful_frontier, total_capabilities,
            plasticity_escape, priority_features, cadence_authorization,
            source_materialization_wall_seconds)
    if action_required_option_id is not None:
        return _issue_result(
            'ACTION_REQUIRED', action_required_option_id, None, None, None,
            cadence_metadata, None, sorted(holds), run_dir, lawful_frontier,
            cadence_authorization=cadence_authorization)
    return _issue_result(
        'NO_ADMISSIBLE_TEACHING', None, None, None, None, cadence_metadata,
        None, sorted(holds), run_dir, lawful_frontier,
        cadence_authorization=cadence_authorization)

