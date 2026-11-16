"""Deterministic HOW credit; callers supply live-issued or committed evidence."""
from copy import deepcopy

from bilqis_mlx.compatibility import historical_teacher_policy
from bilqis_mlx.errors import ErrorBus, SCHOOL
from bilqis_mlx.learning import learning_experiment, plasticity_escape
from bilqis_mlx.learning.teacher_strategy_population import effective_policy_key
from bilqis_mlx.runtime.state import _fingerprint

SCHEMA = 'bilqis.bamf.teacher-outcome/v1'
SCORE_FIELDS = ('capability', 'before', 'after', 'total')


def invalid():
    ErrorBus.Raise(SCHOOL.TEACHER_OBSERVATION.INVALID)


def outcome_digest(observation):
    return _fingerprint({key: value for key, value in observation.items()
                         if key != 'outcome_sha256'})


def ledger(teacher, manifest):
    record = teacher.get('how_outcomes', {})
    if record.get('parent_manifest_sha256') != manifest:
        return {'parent_manifest_sha256': manifest, 'head': None, 'applied': {}}
    return deepcopy(record)


def _deltas(observation):
    scores = observation['scores']
    deltas = {}
    for row in scores:
        if not isinstance(row, (list, tuple)) or len(row) != len(SCORE_FIELDS):
            invalid()
        cap, before, after, total = row
        if (not isinstance(cap, str) or not cap or cap in deltas
                or any(type(value) is not int for value in (before, after, total))
                or total <= 0 or not 0 <= before <= total or not 0 <= after <= total):
            invalid()
        deltas[cap] = (after - before) / total
    return deltas


def _apply_outcome(teacher, observation):
    """Return a credited copy, or the unchanged copy for identical delivery."""
    if (not isinstance(observation, dict) or observation.get('schema') != SCHEMA
            or observation.get('outcome_sha256') != outcome_digest(observation)):
        invalid()
    visit, context = observation['teacher_visit'], observation['context']
    manifest = visit['accepted_manifest_sha256']
    prior = ledger(teacher, manifest)
    attempt, digest = observation['attempt_id'], observation['outcome_sha256']
    if attempt in prior['applied']:
        if prior['applied'][attempt] != digest:
            invalid()
        return deepcopy(teacher)
    selected = deepcopy(observation['selected_teacher'])
    if ledger(selected, manifest) != prior:
        invalid()
    key, cap = visit['policy_key'], visit['capability_id']
    policy = selected.get('strategies', {}).get(key)
    if (policy != observation['selected_policy']
            or effective_policy_key(policy) != observation['effective_policy_key']):
        invalid()
    deltas = _deltas(observation)
    protected = observation['protected_capabilities']
    decision = observation['decision']
    retained = decision['decision'] == 'PROVISIONAL'
    if (cap not in deltas or not set(protected) <= set(deltas) - {cap}
            or decision['decision'] not in {'REJECT', 'PROVISIONAL'}
            or type(observation['attempted_steps']) is not int
            or observation['attempted_steps'] < 1
            or type(observation['retained_steps']) is not int
            or observation['retained_steps'] != (observation['attempted_steps'] if retained else 0)):
        invalid()
    causal = {
        'version': learning_experiment.VERSION, 'active_capability': cap,
        'phase': context['phase'], 'decision': decision['decision'],
        'reason': decision['reason'], 'deltas': deltas,
        'protected_capabilities': protected,
        'paired_scores_sha256': decision['evidence_sha256'],
        'source_cohort_sha256': context['rubric_sha256'],
    }
    feedback = learning_experiment.observe_context(
        selected, capability=cap, phase=context['phase'], policy_key=key,
        decision=causal, local_gain=deltas[cap],
        curriculum_scope=context['curriculum_scope'], diagnostics=context['diagnostics'],
        realized_action=observation['realized_action'],
        student_checkpoint_sha256=visit['student_sha256'], lesson_grade=context['grade'],
        diagnostic_context_key=context.get('diagnostic_context_key'))
    credit = learning_experiment.selection_credit(deltas[cap], causal, feedback)
    historical_teacher_policy.observe(selected, context['grade'], key, credit)
    plasticity_escape.record_school_visit(selected, retained=retained)
    record = selected['causal_experiment']['contexts'][
        cap + '|' + context['phase'] + '|' + context['curriculum_scope']][key]
    for name, value in (
            ('target_delta_sum', deltas[cap]),
            ('protected_net_delta_sum', sum(deltas[name] for name in protected)),
            ('worst_protected_loss_sum', max((max(0., -deltas[name]) for name in protected), default=0.)),
            ('attempted_steps_sum', observation['attempted_steps'])):
        record[name] = record.get(name, 0) + value
    prior['applied'][attempt] = digest
    prior['head'] = digest
    selected['how_outcomes'] = prior
    return selected


def apply_outcome(teacher, observation):
    """Validate one observation before returning any changed teacher state."""
    try:
        return _apply_outcome(teacher, observation)
    except (KeyError, TypeError, ValueError, AttributeError):
        invalid()
