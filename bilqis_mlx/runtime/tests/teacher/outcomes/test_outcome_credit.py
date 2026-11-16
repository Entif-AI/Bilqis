"""Real HOW policy credit from measured native candidate outcomes."""
from copy import deepcopy
import random

import pytest

from bilqis_mlx.compatibility import historical_teacher_policy as engine
from bilqis_mlx.errors import BilqisError
from bilqis_mlx.learning.teacher_strategy_population import effective_policy_key
from bilqis_mlx.runtime import state
from bilqis_mlx.runtime.outcomes.observations import apply_outcome


def teacher_fixture():
    policy = {'lr': .00013, 'old': 4, 'preview': 0, 'depth': 1,
              'contrast': 0., 'distill': 0.}
    return {'strategies': {'policy': policy}, 'events': 0, 'mutations': 0,
            'global_stats': {'policy': engine._stats()}, 'grade_stats': {}}


def outcome(teacher, ordinal=1, *, retained=False, grade='Z', capability='opaque:next'):
    policy = teacher['strategies']['policy']
    value = {
        'schema': 'bilqis.bamf.teacher-outcome/v1', 'attempt_id': f'attempt:{ordinal}',
        'proposal_id': 'a' * 64, 'candidate_evidence': {'sha256': 'e' * 64},
        'teacher_visit': {'accepted_manifest_sha256': 'b' * 64,
                          'student_sha256': 'c' * 64, 'policy_key': 'policy',
                          'capability_id': capability},
        'context': {'grade': grade, 'phase': 'MAIN', 'curriculum_scope': 'factory/test',
                    'rubric_sha256': 'd' * 64, 'diagnostics': {}},
        'selected_teacher': deepcopy(teacher), 'selected_policy': deepcopy(policy),
        'effective_policy_key': effective_policy_key(policy), 'realized_action': None,
        'attempted_steps': 1, 'retained_steps': int(retained),
        'decision': {'decision': 'PROVISIONAL' if retained else 'REJECT',
                     'reason': 'PAIRED_SCREEN_WITHIN_BUDGET' if retained else 'NO_MEASURABLE_TARGET_GAIN',
                     'evidence_sha256': 'e' * 64},
        'scores': [[capability, 1, 2 if retained else 1, 4]],
        'protected_capabilities': [],
    }
    value['outcome_sha256'] = state._fingerprint(value)
    return value


def test_rejected_and_retained_observations_credit_once_without_mutating_inputs():
    parent = teacher_fixture()
    rejected = outcome(parent)
    credited = apply_outcome(parent, rejected)
    assert parent == teacher_fixture()
    assert credited['events'] == 1
    assert credited['global_stats']['policy']['latest'] < 0
    assert credited['grade_stats']['Z']['policy']['trials'] == 1
    assert apply_outcome(credited, rejected) == credited
    retained = outcome(credited, 2, retained=True)
    final = apply_outcome(credited, retained)
    assert final['events'] == 2
    assert final['global_stats']['policy']['latest'] == .25
    assert apply_outcome(final, retained) == final
    channel = final['causal_experiment']
    assert channel['events'] == 2
    assert channel['contexts']['opaque:next|MAIN|factory/test']['policy']['retained'] == 1
    stagnation = channel['capability_stagnation']['opaque:next|factory/test']
    assert stagnation['rejection_streak'] == 0
    assert stagnation['total_rejections'] == 1
    assert stagnation['total_retained'] == 1


def test_changed_duplicate_or_forked_snapshot_fails_closed():
    parent = teacher_fixture()
    first = outcome(parent)
    credited = apply_outcome(parent, first)
    changed = deepcopy(first)
    changed['attempted_steps'] += 1
    changed['outcome_sha256'] = state._fingerprint({k:v for k,v in changed.items() if k != 'outcome_sha256'})
    with pytest.raises(BilqisError):
        apply_outcome(credited, changed)
    with pytest.raises(BilqisError):
        apply_outcome(credited, outcome(parent, 2))


def test_repeated_no_gain_drives_existing_checkpoint_cooldown_and_debt():
    teacher = teacher_fixture()
    for ordinal in range(1, 5):
        teacher = apply_outcome(teacher, outcome(teacher, ordinal))
    channel = teacher['causal_experiment']
    record = channel['contexts']['opaque:next|MAIN|factory/test']['policy']
    assert record['no_target_gain_streak'] == 4
    assert record['unsafe'] == 4
    assert channel['capability_stagnation']['opaque:next|factory/test']['rejection_streak'] == 4
    assert teacher['global_stats']['policy']['trials'] == 4
    assert teacher['global_stats']['policy']['reward_sum'] < -.2


def signed(value, **changes):
    value.update(changes)
    value['outcome_sha256'] = state._fingerprint({k:v for k,v in value.items() if k != 'outcome_sha256'})
    return value


def test_two_checkpoint_cooldown_expires_by_target_visits_and_retention_clears():
    from bilqis_mlx.learning.teacher_strategy_population import durable_policy_cooldown_status

    teacher = teacher_fixture()
    effective = effective_policy_key(teacher['strategies']['policy'])
    for checkpoint in ('c', 'f'):
        for ordinal in range(1, 5):
            value = outcome(teacher, ordinal)
            value['teacher_visit']['student_sha256'] = checkpoint * 64
            value['teacher_visit']['accepted_manifest_sha256'] = checkpoint * 64
            teacher = apply_outcome(teacher, signed(value))
    status = lambda: durable_policy_cooldown_status(
        teacher['causal_experiment'], 'opaque:next', 'factory/test', effective)
    assert status()['active']
    assert status()['failed_student_epochs'] == 2
    assert status()['remaining_capability_visits'] == 8
    other = outcome(teacher, 5, retained=True, capability='other:capability')
    other['teacher_visit']['accepted_manifest_sha256'] = 'f' * 64
    teacher = apply_outcome(teacher, signed(other))
    assert status()['remaining_capability_visits'] == 8
    teacher['strategies']['alternative'] = {**teacher['strategies']['policy'], 'lr': .0002}
    teacher['global_stats']['alternative'] = engine._stats()
    for ordinal in range(6, 14):
        value = outcome(teacher, ordinal, retained=True)
        value['teacher_visit'].update(policy_key='alternative', accepted_manifest_sha256='f' * 64)
        value.update(selected_policy=teacher['strategies']['alternative'],
                     effective_policy_key=effective_policy_key(teacher['strategies']['alternative']))
        teacher = apply_outcome(teacher, signed(value))
    assert not status()['active']
    assert status()['failed_student_epochs'] == 1
    value = outcome(teacher, 14, retained=True)
    value['teacher_visit']['accepted_manifest_sha256'] = 'f' * 64
    teacher = apply_outcome(teacher, signed(value))
    assert status()['failed_student_epochs'] == 0


def test_retained_context_outranks_newborn_pressure_in_real_selector():
    from bilqis_mlx.learning.learning_experiment import contextual_pick
    from bilqis_mlx.learning.teacher_strategy_population import active_effective_strategy_keys

    teacher = apply_outcome(teacher_fixture(), outcome(teacher_fixture(), retained=True))
    teacher['strategies']['bad'] = {**teacher['strategies']['policy'], 'lr': .0003}
    teacher['global_stats']['bad'] = engine._stats()
    for ordinal in range(2, 6):
        value = outcome(teacher, ordinal)
        value['teacher_visit']['policy_key'] = 'bad'
        value.update(selected_policy=teacher['strategies']['bad'],
                     effective_policy_key=effective_policy_key(teacher['strategies']['bad']))
        teacher = apply_outcome(teacher, signed(value))
    teacher['strategies']['newborn'] = {**teacher['strategies']['policy'], 'lr': .0002}
    teacher['global_stats']['newborn'] = engine._stats()
    key, _, metadata = contextual_pick(engine, teacher, 'opaque:next', 'MAIN', random.Random(2),
        curriculum_scope='factory/test', student_checkpoint_sha256='c' * 64,
        lesson_grade='Z', return_metadata=True)
    assert key == 'policy'
    assert metadata['selection_reason'] == 'PROVEN_RETAINED_CONTEXT'
    scope = teacher['causal_experiment']['contexts']['opaque:next|MAIN|factory/test']
    active, _ = active_effective_strategy_keys(teacher, 'Z', scope)
    assert effective_policy_key(teacher['strategies']['policy']) in active


def test_opaque_capability_uses_explicit_grade_for_inherited_exploration():
    teacher = teacher_fixture()
    teacher['events'] = 30
    teacher['global_stats']['policy'].update(trials=20)
    teacher['grade_stats']['Z'] = {'policy': {**engine._stats(), 'trials': 2}}
    opaque = apply_outcome(teacher, outcome(teacher))
    named = apply_outcome(teacher, outcome(teacher, capability='Z.NEXT'))
    assert opaque['global_stats'] == named['global_stats']


@pytest.mark.parametrize('scores', [[], [['opaque:next', 1, 1, 0]], [['opaque:next', 1, 5, 4]]])
def test_invalid_measurement_cannot_credit(scores):
    teacher = teacher_fixture()
    with pytest.raises(BilqisError):
        apply_outcome(teacher, signed(outcome(teacher), scores=scores))


def test_unknown_grade_context_uses_admitted_projection_and_native_selector():
    from dataclasses import dataclass
    from types import SimpleNamespace
    from bilqis_mlx.factory.schedule import ScheduleGrade, ScheduleCapability, ScheduleProgram
    from bilqis_mlx.learning.learning_experiment import Settings
    from bilqis_mlx.runtime.outcomes.issuance import selection_context
    from bilqis_mlx.runtime.teacher_policy_selection import select_visit_policy

    @dataclass(frozen=True)
    class Binding:
        source: str

    capability = 'opaque:next'
    grade = ScheduleGrade('Z', (ScheduleCapability(capability, 4),), (), 'a' * 64)
    program = ScheduleProgram('b' * 64, (grade,), False)
    release = SimpleNamespace(release_sha256='c' * 64,
        source_bindings=SimpleNamespace(by_capability={capability: Binding('source:qualified')}))
    context = selection_context(release, program, 'Z', 'MAIN', 'factory/test', {}, capability)
    assert context['grade'] == 'Z'
    assert context['rubric_sha256'] == 'a' * 64
    teacher = teacher_fixture()
    school = SimpleNamespace(stage='MAIN', current_student=SimpleNamespace(sha256='d' * 64))
    key, policy, _ = select_visit_policy(engine, teacher, capability, school, random.Random(3),
        Settings(), 'factory/test', {}, 'Z', total_capabilities=1)
    assert teacher['strategies'][key] == policy
