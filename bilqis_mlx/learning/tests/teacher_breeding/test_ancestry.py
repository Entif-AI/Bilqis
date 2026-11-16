"""Policy ancestry ranking and grade-neutral compatibility."""
import unittest
from bilqis_mlx.learning.tests.test_learning_experiment import _effective_policy_key
from bilqis_mlx.learning.tests.test_teacher_vnext_replay import _teacher


class BreedingAncestryTests(unittest.TestCase):
    def teacher(self):
        from bilqis_mlx.learning.teacher_strategy_population import BAMF_SUCCESSOR_SELECTION
        teacher, _, _ = _teacher()
        teacher['selection_contract'] = BAMF_SUCCESSOR_SELECTION
        from bilqis_mlx.learning.learning_experiment import VERSION
        teacher['causal_experiment']['version'] = VERSION
        teacher['events'] = 100
        teacher['global_stats'] = {key: {'trials': 10, 'reward_sum': index, 'reward_ema': index}
                                   for index, key in enumerate(teacher['strategies'])}
        teacher['grade_stats'] = {
            'A': {'p-strong': {'trials': 1, 'reward_sum': 1000., 'reward_ema': 1000.}},
            'B': {'p-weak': {'trials': 1, 'reward_sum': 1000., 'reward_ema': 1000.}}}
        return teacher

    def test_realized_action_novelty_breaks_otherwise_equal_parent_tie(self):
        from bilqis_mlx.learning.teacher_breeding import _retained_parent_candidates

        first = {"old": 4, "preview": 0, "depth": 1, "contrast": 0.,
                 "lr": .00004, "distill": 0.}
        second = dict(first, lr=.00008)
        first_effective = _effective_policy_key(first)
        second_effective = _effective_policy_key(second)
        record = {
            "trials": 8, "reward_sum": 2., "unsafe": 2, "retained": 4,
            "latest": .25, "no_target_gain_streak": 0,
        }
        teacher = {
            "strategies": {"first": first, "second": second},
            "global_stats": {}, "grade_stats": {},
            "causal_experiment": {
                "contexts": {"C.ADD|MAIN|scope": {
                    "first": dict(record), "second": dict(record),
                }},
                "strategy_births": {
                    first_effective: {"novel_realized_action_count": 0},
                    second_effective: {
                        "novel_realized_action_count": 2,
                        "retained_novel_realized_action_count": 1,
                    },
                },
            },
        }

        candidates = list(_retained_parent_candidates(
            teacher, "C.ADD", "scope", diagnostic_key=None))

        self.assertEqual(candidates[0][0], "second")

    def test_retained_breeding_ancestry_excludes_grade_reward_fallback(self):
        from bilqis_mlx.learning.teacher_breeding import _retained_parent_candidates
        candidates = list(_retained_parent_candidates(self.teacher(), 'A.UNKNOWN', 'factory/7', None))
        self.assertTrue(candidates)
        self.assertFalse(any(basis.startswith('GRADE') for _, basis in candidates))
