"""Realized-action evidence remains attributed to its originating policy."""
from bilqis_mlx.learning.teacher_breeding import record_policy_outcome_side_effects


def test_retention_marks_origin_and_tracks_novel_action_once():
    channel = {'events': 4, 'strategy_births': {'policy': {
        'origin_capability': 'A.X', 'curriculum_scope': 'scope',
        'proven_retained': False,
    }}}
    for retained in (False, True):
        record_policy_outcome_side_effects(channel, 'policy', capability='A.X',
            curriculum_scope='scope', retained=retained, realized_action_key='action')
    birth = channel['strategy_births']['policy']
    assert birth['proven_retained'] is True
    assert birth['novel_realized_action_count'] == 1
    assert birth['realized_action_keys'] == ['action']
    assert channel['realized_action_ecology']['action']['trials'] == 2
    assert channel['realized_action_ecology']['action']['retained'] == 1
