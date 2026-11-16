"""Build HOW observations only from live C03 selection and C05 evaluation."""
from dataclasses import asdict, replace
import json
import weakref

from bilqis_mlx.learning.teacher_lineage import restore_teacher_lineage
from bilqis_mlx.learning.teacher_realized_action import describe
from bilqis_mlx.learning.teacher_strategy_population import effective_policy_key
from bilqis_mlx.runtime.state import _fingerprint

from .observations import SCHEMA, apply_outcome, invalid


class _IssuedOutcome(dict):
    __slots__ = ('__weakref__',)


def _new_outcome_issuer():
    issued = {}

    def register(value):
        identifier = id(value)
        issued[identifier] = (weakref.ref(value, lambda _ref: issued.pop(identifier, None)),
                              value['outcome_sha256'])

    def require(value):
        from .observations import outcome_digest
        record = issued.get(id(value))
        if (record is None or record[0]() is not value
                or record[1] != outcome_digest(value)
                or value['outcome_sha256'] != record[1]):
            invalid()

    return register, require


_register_outcome, _require_outcome = _new_outcome_issuer()


def require_issued_outcome(value, evidence):
    _require_outcome(value)
    if (value['teacher_visit'] != evidence.get('teacher_visit')
            or value['decision'] != evidence.get('decision')
            or value['decision']['reason'] != evidence.get('retention_reason')
            or evidence.get('candidate_optimizer_step', 0) - evidence.get('retained_optimizer_step', 0) != value['attempted_steps']
            or value['retained_steps'] != 0
            or value['candidate_evidence'] != evidence.get('candidate_evidence', {}).get('object')):
        invalid()


def require_context(context):
    if (not isinstance(context, dict)
            or any(not isinstance(context.get(key), str) or not context[key]
                   for key in ('grade', 'phase', 'curriculum_scope'))
            or not isinstance(context.get('diagnostics'), dict)
            or any(not isinstance(context.get(key), str) or len(context[key]) != 64
                   or any(c not in '0123456789abcdef' for c in context[key])
                   for key in ('grade_definition_sha256', 'source_binding_sha256',
                               'factory_release_sha256', 'rubric_sha256'))):
        invalid()


def selection_context(release, program, grade, phase, scope, diagnostics, capability):
    definition = next(item for item in program.grades if item.id == grade)
    context = {
        'grade': grade, 'phase': phase, 'curriculum_scope': scope,
        'grade_definition_sha256': _fingerprint(asdict(definition)),
        'source_binding_sha256': _fingerprint(asdict(release.source_bindings.by_capability[capability])),
        'factory_release_sha256': release.release_sha256,
        'rubric_sha256': definition.assessment_sha256,
        'diagnostics': diagnostics,
    }
    require_context(context)
    return context


def build_outcome(run_dir, selection, evaluation, decision, candidate_evidence):
    from bilqis_mlx.runtime.accepted_priority_visit import _require_issued
    from bilqis_mlx.runtime.factory_retention_owner import _require_factory_evaluation
    from bilqis_mlx.learning.atlas_retention_decision import _require_issued_decision
    from bilqis_mlx.runtime.bamf_operator.evidence_validation import read_candidate_horizon_evidence

    _require_issued(selection)
    _require_factory_evaluation(evaluation)
    _require_issued_decision(decision)
    payload = read_candidate_horizon_evidence(run_dir, candidate_evidence)
    proposal, steps = payload['proposal'], payload['steps']
    identity = selection.visit.identity
    context = selection.metadata['how_context']
    require_context(context)
    if (context['grade'] != selection.lesson_grade
            or context.get('diagnostic_context_key') != selection.metadata.get('diagnostic_context_key')):
        invalid()
    selected = restore_teacher_lineage(selection.visit.projection.teacher_state).teacher()
    if (evaluation.parent_candidate_sha256 != identity.student_sha256
            or proposal.get('teacher_visit') != identity.to_record()
            or proposal.get('selected_policy_key') != identity.policy_key
            or proposal.get('capability') != identity.capability_id
            or proposal.get('generation') != identity.generation
            or proposal.get('accepted_manifest_sha256') != identity.accepted_manifest_sha256
            or proposal.get('factory_release_sha256') != context['factory_release_sha256']
            or proposal.get('how_context') != context
            or proposal.get('selected_teacher') != selected
            or proposal.get('policy') != selection.policy
            or payload['outcome'] != {'accepted': decision.accepted, 'decision': decision.to_record()}
            or decision.evidence_sha256 != evaluation.decision.evidence_sha256
            or decision.policy_sha256 != evaluation.decision.policy_sha256
            or decision.parent_generation != evaluation.parent_candidate_sha256
            or decision.candidate_generation != evaluation.candidate_candidate_sha256
            or decision.reason != evaluation.decision.reason
            or decision.accepted != (evaluation.decision.status.value == 'ELIGIBLE')):
        invalid()
    scores = evaluation.decision.outcome_scores
    if not scores or len(steps) != steps[-1]['step'] - proposal['parent_optimizer_step']:
        invalid()
    cap = identity.capability_id
    coverage = evaluation.decision.baseline_coverage
    protected = (coverage.protected_capabilities(cap) if coverage is not None
                 else tuple(row[0] for row in scores if row[0] != cap))
    realized = describe(selection.policy, candidate_steps=len(steps),
        batch_size=len(steps[0]['positions']),
        policy_controls=[step['controls'] for step in steps],
        guidance_applied_steps=sum(step['guidance'] is not None for step in steps),
        enrichment_examples=sum('enrichment' in item['roles'] for step in steps for item in step['positions']))
    observation = _IssuedOutcome({
        'schema': SCHEMA, 'attempt_id': payload['attempt_id'],
        'proposal_id': payload['proposal_id'], 'candidate_evidence': candidate_evidence['object'],
        'teacher_visit': identity.to_record(), 'context': context,
        'selected_teacher': selected, 'selected_policy': selection.policy,
        'effective_policy_key': effective_policy_key(selection.policy),
        'realized_action': realized, 'attempted_steps': len(steps),
        'retained_steps': len(steps) if decision.accepted else 0,
        'decision': decision.to_record(), 'scores': [list(row) for row in scores],
        'protected_capabilities': list(protected),
    })
    observation['outcome_sha256'] = _fingerprint(observation)
    _register_outcome(observation)
    return observation


def credited_visit(visit, observation):
    from bilqis_mlx.runtime.accepted_teacher_custody import _selection_projection, _issue_bound_visit

    epoch = restore_teacher_lineage(visit.projection.teacher_state)
    teacher = apply_outcome(epoch.teacher(), observation)
    projection = _selection_projection(visit.projection, replace(
        epoch, current_json=json.dumps(teacher, sort_keys=True, allow_nan=False)))
    return _issue_bound_visit(projection, visit.identity)


def carry_credit_to_successor(visit, successor, parent):
    """Keep compatible causal HOW evidence while resetting checkpoint-local counts."""
    from copy import deepcopy
    from bilqis_mlx.learning.teacher_lineage import TeacherCustodyProjection
    from bilqis_mlx.runtime.accepted_teacher_custody import (
        _bank_identity, _plasticity_identity, _selection_projection,
    )
    if (_bank_identity(parent) != _bank_identity(successor)
            or _plasticity_identity(parent.retained_state) != _plasticity_identity(successor.retained_state)
            or parent.provenance.source_identity != successor.provenance.source_identity
            or parent.provenance.release_digest != successor.provenance.release_digest):
        return successor
    credited = restore_teacher_lineage(visit.projection.teacher_state).teacher()
    epoch = restore_teacher_lineage(successor.teacher_state)
    teacher = epoch.teacher()
    channel = deepcopy(credited['causal_experiment'])
    channel['student_policy_epoch'] = teacher['causal_experiment']['student_policy_epoch']
    teacher['causal_experiment'] = channel
    teacher['grade_stats'] = deepcopy(credited['grade_stats'])
    projection = TeacherCustodyProjection(successor.teacher_state,
        successor.provenance.teacher_identity, successor.provenance.teacher_epoch)
    updated = _selection_projection(projection, replace(
        epoch, current_json=json.dumps(teacher, sort_keys=True, allow_nan=False)))
    return replace(successor, teacher_state=dict(updated.teacher_state))


def context_for_selection(release, program, grade, school, option, teacher, metadata):
    key = metadata['diagnostic_context_key']
    payload = teacher['causal_experiment']['diagnostic_contexts'][key]
    context = selection_context(release, program, grade, school.stage,
        option.context.scope, payload, option.context.capability_id)
    return {**context, 'diagnostic_context_key': key}
