"""Verified selection salience and outcome credit share one diagnostic key."""
from copy import deepcopy
import random

import pytest

from bilqis_mlx.compatibility import historical_teacher_policy as engine
from bilqis_mlx.errors import BilqisError
from bilqis_mlx.learning.learning_experiment import Settings
from bilqis_mlx.learning.teacher_strategy_population import effective_policy_key
from bilqis_mlx.learning.tests.test_salience_teacher import _fixture
from bilqis_mlx.runtime.outcomes.observations import apply_outcome
from bilqis_mlx.runtime.state import _fingerprint
from bilqis_mlx.runtime.teacher_policy_selection import select_visit_policy
from bilqis_mlx.semantics.domains import contract_digest


def selected_outcome():
    epoch, _, _, school, evidence = _fixture()
    teacher = epoch.teacher()
    capability, scope = evidence.scope.capability_id, evidence.scope.scope
    diagnostics = {'salience_evidence': evidence, 'teacher_epoch_digest': contract_digest(epoch)}
    key, policy, metadata = select_visit_policy(engine, teacher, capability, school,
        random.Random(12), Settings(), scope, diagnostics, 'any-grade')
    diagnostic_key = metadata['diagnostic_context_key']
    payload = teacher['causal_experiment']['diagnostic_contexts'][diagnostic_key]
    value = {
        'schema': 'bilqis.bamf.teacher-outcome/v1', 'attempt_id': 'selected:1',
        'teacher_visit': {'accepted_manifest_sha256': 'a' * 64,
            'student_sha256': epoch.student_sha256, 'policy_key': key, 'capability_id': capability},
        'context': {'grade': 'any-grade', 'phase': school.stage, 'curriculum_scope': scope,
            'rubric_sha256': 'd' * 64, 'diagnostics': payload, 'diagnostic_context_key': diagnostic_key},
        'selected_teacher': deepcopy(teacher), 'selected_policy': policy,
        'effective_policy_key': effective_policy_key(policy), 'realized_action': None,
        'attempted_steps': 1, 'retained_steps': 1,
        'decision': {'decision': 'PROVISIONAL', 'reason': 'PAIRED_SCREEN_WITHIN_BUDGET',
                     'evidence_sha256': 'e' * 64},
        'scores': [[capability, 1, 2, 4]], 'protected_capabilities': [],
    }
    value['outcome_sha256'] = _fingerprint(value)
    return teacher, value, school, diagnostics


def test_native_selection_and_feedback_preserve_verified_salience_key():
    teacher, value, school, diagnostics = selected_outcome()
    credited = apply_outcome(teacher, value)
    visit, context = value['teacher_visit'], value['context']
    scope = visit['capability_id'] + '|' + school.stage + '|' + context['curriculum_scope']
    record = credited['causal_experiment']['contexts'][scope][visit['policy_key']]
    assert record['diagnostic_stats'][context['diagnostic_context_key']]['retained'] == 1
    assert 'salience' in context['diagnostics']
    key, _, selected = select_visit_policy(engine, credited, visit['capability_id'], school,
        random.Random(12), Settings(), context['curriculum_scope'], diagnostics, 'any-grade')
    assert selected['diagnostic_context_key'] == context['diagnostic_context_key']
    assert key == visit['policy_key']


def test_changed_selected_diagnostic_payload_cannot_credit():
    teacher, value, _, _ = selected_outcome()
    value['context']['diagnostics'] = {'salience': 'changed'}
    value['outcome_sha256'] = _fingerprint({k:v for k,v in value.items() if k != 'outcome_sha256'})
    with pytest.raises(BilqisError):
        apply_outcome(teacher, value)
