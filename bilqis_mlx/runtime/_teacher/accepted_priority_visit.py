"""Accepted C03 priority selection and one Factory candidate execution."""
from dataclasses import dataclass, replace
from bilqis_mlx.errors import ErrorBus, SCHOOL
import hashlib
import json
import math
from pathlib import Path
import time
from weakref import WeakKeyDictionary

from bilqis_mlx.factory.teaching import describe_delivered_teaching
from bilqis_mlx.learning.atlas_acceptance import candidate_identity_digest
from bilqis_mlx.learning.atlas_salience import salience_priority_features
from bilqis_mlx.learning.salience_contracts import ActionKind
from bilqis_mlx.learning.salience_teacher import _teacher
from bilqis_mlx.learning.salience_teacher import PrioritySchoolContext, PriorityStudentIdentity
from bilqis_mlx.learning.learning_experiment import Settings
from bilqis_mlx.learning.teacher_lineage import restore_teacher_lineage
from bilqis_mlx.learning.teacher_visit_identity import (
    derive_teacher_visit_identity, record_teacher_visit_authority,
    record_teacher_visit_identity,
)
from bilqis_mlx.runtime.atlas_optimizer import AdamWHyperparameters
from bilqis_mlx.runtime.atlas_training_contracts import BamfVisitProvenance
from bilqis_mlx.runtime.factory_candidate_training import execute_factory_candidate_step
from bilqis_mlx.runtime.teacher_policy_selection import select_visit_policy
from bilqis_mlx.semantics.domains import contract_digest
from .accepted_teacher_custody import (
    _accepted_parent, _c03_projection, _issue_bound_visit, _require_current_visit,
    _selection_projection,
)
from .priority_qualification import _grade, requalify_priority

def _invalid(reason):
    ErrorBus.Raise(SCHOOL.MODEL_TOPOLOGY.INVALID, reason=reason)



_ISSUED = WeakKeyDictionary()


def _json(value):
    return json.dumps(value, sort_keys=True, separators=(',', ':'), allow_nan=False)


def _digest(value):
    return hashlib.sha256(value.encode('utf-8')).hexdigest()


@dataclass(frozen=True, init=False, eq=False)
class PriorityVisitResult:
    status: str
    option_id: str | None
    offer: object | None
    visit: object | None
    _policy_json: str | None
    _metadata_json: str | None
    lesson_grade: str | None
    holds: tuple
    _run_dir: str

    def __init__(self, *args, **kwargs):
        _invalid('BAMF_PRIORITY_RESULT_CALLER_CONSTRUCTION_FORBIDDEN')

    @property
    def policy(self):
        return None if self._policy_json is None else json.loads(self._policy_json)

    @property
    def metadata(self):
        return None if self._metadata_json is None else json.loads(self._metadata_json)


def _issue_result(status, option_id, offer, visit, policy, metadata, grade, holds, run_dir):
    result = object.__new__(PriorityVisitResult)
    policy_json = None if policy is None else _json(policy)
    metadata_json = None if metadata is None else _json(metadata)
    for name, value in (('status', status), ('option_id', option_id), ('offer', offer),
            ('visit', visit), ('_policy_json', policy_json), ('_metadata_json', metadata_json),
            ('lesson_grade', grade), ('holds', tuple(holds)), ('_run_dir', str(run_dir))):
        object.__setattr__(result, name, value)
    visit_digest = None if visit is None else _digest(_json(visit.identity.to_record()))
    _ISSUED[result] = (status, option_id, id(offer), id(visit), visit_digest,
                       None if policy_json is None else _digest(policy_json),
                       metadata_json, grade, tuple(holds), str(run_dir))
    return result


def _require_issued(result):
    if type(result) is not PriorityVisitResult or result not in _ISSUED:
        _invalid('BAMF_PRIORITY_RESULT_NOT_ISSUED')
    visit_digest = None if result.visit is None else _digest(_json(result.visit.identity.to_record()))
    actual = (result.status, result.option_id, id(result.offer), id(result.visit), visit_digest,
              None if result._policy_json is None else _digest(result._policy_json),
              result._metadata_json, result.lesson_grade, result.holds, result._run_dir)
    if actual != _ISSUED[result]:
        _invalid('BAMF_PRIORITY_RESULT_DRIFT')


def accepted_priority_school(parent, program, *, candidate_identity_sha256=None):
    """Project B13 + admitted Factory custody into C03's minimal school view."""
    from bilqis_mlx.factory.schedule import ScheduleProgram
    if not isinstance(program, ScheduleProgram):
        _invalid('BAMF_PRIORITY_PROGRAM_INVALID')
    grades = tuple(grade.id for grade in program.grades)
    if not grades:
        _invalid('BAMF_PRIORITY_PROGRAM_INVALID')
    if candidate_identity_sha256 is None:
        candidate_identity_sha256 = candidate_identity_digest(parent.retained_state)
    return PrioritySchoolContext(
        course_digest=program.digest(),
        active_grades=grades,
        current_student=PriorityStudentIdentity(
            candidate_identity_sha256),
    )


def select_accepted_priority_visit(
        run_dir, source_context, frontier, history, planning, offers,
        engine, school, rng, learning_settings, *, program, now,
        total_capabilities=None, plasticity_escape=None,
        legacy_receipt=None, adaptation=None, prior_region=None,
        accepted_parent=None, planning_generation=None):
    if planning_generation is None:
        parent, cache = _accepted_parent(Path(run_dir))
    else:
        from bilqis_mlx.runtime.priority_source_offer import _require_planning_generation
        parent = accepted_parent
        cache, _authenticated = _require_planning_generation(
            planning_generation, source_context, parent)
    projection = _c03_projection(parent, legacy_receipt=legacy_receipt,
                                 adaptation=adaptation, prior_region=prior_region)
    epoch = restore_teacher_lineage(projection.teacher_state)
    expected_parent_identity = (
        planning_generation.parent_candidate_identity_sha256
        if planning_generation is not None
        else candidate_identity_digest(parent.retained_state)
    )
    if getattr(getattr(school, 'current_student', None), 'sha256', None) != expected_parent_identity:
        _invalid('BAMF_PRIORITY_STUDENT_DRIFT')
    teacher = _teacher(epoch, school)
    if not isinstance(learning_settings, Settings):
        _invalid('BAMF_SALIENCE_CONTEXTUAL_SETTINGS_REQUIRED')
    qualified = requalify_priority(run_dir, source_context, parent, frontier, history,
                                   planning, offers, program, school, epoch, now=now,
                                   planning_generation=planning_generation)
    by_id, evidence = dict(qualified.offers), dict(frontier.evidence)
    holds = list(qualified.holds)
    for option in qualified.ranked.ordered:
        salience_priority_features(evidence[option.stable_id], option.context.capability_id,
                                  option.context.scope, contract_digest(epoch))
        if option.action_kind in (ActionKind.CORRECTION, ActionKind.PROCEDURE_REPAIR):
            return _issue_result('ACTION_REQUIRED', option.stable_id, None, None, None,
                                 None, None, sorted(holds), run_dir)
        offer = by_id[option.stable_id]
        try:
            offer.require_current(source_context, parent)
        except ValueError:
            holds.append((option.stable_id, 'SOURCE_OFFER_HELD'))
            continue
        capability = option.context.capability_id
        grade = _grade(program, school, capability)
        key, policy, metadata = select_visit_policy(
            engine, teacher, capability, school, rng, learning_settings, option.context.scope,
            {'salience_evidence': evidence[option.stable_id], 'teacher_epoch_digest': contract_digest(epoch)},
            grade, total_capabilities=total_capabilities, plasticity_escape=plasticity_escape)
        selected_epoch = replace(epoch, current_json=json.dumps(teacher, sort_keys=True, allow_nan=False))
        selected = _selection_projection(projection, selected_epoch)
        identity = derive_teacher_visit_identity(selected.teacher_state,
            run_identity_sha256=parent.run_identity.digest, run_seed=parent.run_identity.run_seed,
            generation=parent.generation, accepted_manifest_sha256=cache.accepted_manifest_sha256,
            capability_id=capability, policy_key=key)
        recorded = record_teacher_visit_identity(selected.teacher_state, identity)
        recorded = record_teacher_visit_authority(recorded, identity)
        visit = _issue_bound_visit(recorded, identity)
        return _issue_result('TEACHER_SELECTED', option.stable_id, offer, visit, policy,
                             metadata, grade, sorted(holds), run_dir)
    return _issue_result('NO_ADMISSIBLE_TEACHING', None, None, None, None, None,
                         None, sorted(holds), run_dir)


def execute_accepted_priority_candidate(selection, source_context,
        atlas_artifact_path, feature_artifact_path, *, teacher_hparams, observation,
        optimizer_step_seed, max_norm, memory_budget=None, salience_provider=None,
        capture_diagnostics=False, candidate=None, finalize_candidate=True,
        prepared_source_rows=None, candidate_step_started_at=None,
        source_prepare_wall_seconds=0.0):
    _require_issued(selection)
    if selection.status != 'TEACHER_SELECTED':
        return selection
    planning_generation = selection.offer._planning_generation
    from bilqis_mlx.runtime.bamf_bundle.currentness_transaction import (
        refresh_accepted_currentness,
    )
    if candidate_step_started_at is None:
        candidate_step_started_at = time.perf_counter()
    currentness_started = time.perf_counter()
    refresh_accepted_currentness(
        planning_generation._accepted_currentness, planning_generation._parent)
    parent, cache = selection.offer.require_current_parent(source_context)
    semantic_context = planning_generation._authenticated_features
    _require_current_visit(
        parent, cache, selection.visit,
        candidate_identity_sha256=planning_generation.parent_candidate_identity_sha256)
    prepared_source = (
        selection.offer.require_current(source_context, parent)
        if prepared_source_rows is None else
        selection.offer.require_current(
            source_context, parent, prepared_rows=prepared_source_rows))
    currentness_wall_seconds = time.perf_counter() - currentness_started
    caller_pre_neural_started = time.perf_counter()
    policy = selection.policy
    lr = policy.get('lr') if isinstance(policy, dict) else None
    if (type(teacher_hparams) is not AdamWHyperparameters or type(lr) not in (int, float)
            or not math.isfinite(lr) or lr <= 0):
        _invalid('BAMF_PRIORITY_TEACHER_RATE_INVALID')
    hparams = replace(teacher_hparams, learning_rate=float(lr))
    offer = selection.offer
    rows = offer.rows() if prepared_source_rows is None else tuple(prepared_source_rows)
    capability = offer.capability_id
    execution = source_context.release.execution_plan.capability_map[capability]
    delivery = describe_delivered_teaching(source_context.release, capability,
                                            execution.teaching_option_ids[0], rows)
    provenance = BamfVisitProvenance.from_c03_record(selection.visit.identity.to_record())
    observation = replace(observation, option_rows=rows, seed=offer.source_seed)
    caller_pre_neural_wall_seconds = (
        float(source_prepare_wall_seconds)
        + time.perf_counter() - caller_pre_neural_started)
    return execute_factory_candidate_step(Path(selection._run_dir), source_context, parent,
        atlas_artifact_path, feature_artifact_path, rows, capability=capability,
        delivery=delivery, requested_count=len(rows), source_seed=offer.source_seed,
        source_each=offer.source_each, optimizer_step_seed=optimizer_step_seed,
        visit_provenance=provenance, teacher_strategy=policy, teacher_hparams=hparams,
        max_norm=max_norm, observation=observation, memory_budget=memory_budget,
        salience_provider=salience_provider,
        capture_diagnostics=capture_diagnostics, candidate=candidate,
        finalize_candidate=finalize_candidate,
        currentness_transaction=planning_generation._accepted_currentness,
        candidate_step_started_at=candidate_step_started_at,
        currentness_binding_wall_seconds=currentness_wall_seconds,
        upstream_pre_neural_source_compile_wall_seconds=caller_pre_neural_wall_seconds,
        semantic_context=semantic_context,
        prepared_source=prepared_source)
