import unittest

from bilqis_mlx.learning.teacher_population_control import (
    population_limits, rebalance_live_population,
)
from bilqis_mlx.learning.teacher_strategy_population import (
    effective_policy_key,
)
from bilqis_mlx.learning.tests.teacher_strategy.support import teacher_fixture


class TeacherStrategyPopulationTests(unittest.TestCase):
    def test_strategy_population_scales_with_capabilities_and_prunes_weak_old_effective_policy(self):
        small = population_limits(3)
        larger = population_limits(11)
        self.assertGreater(larger.max_effective, small.max_effective)
        self.assertGreater(larger.active_effective, small.active_effective)

        teacher, strong, weak = teacher_fixture()
        teacher["causal_experiment"]["contexts"]["C.ADD|RECOVERY_1|factory/7"][
            "p-other"] = {
                "trials": 10, "retained": 5, "reward_sum": 3.0,
                "unsafe": 3, "no_target_gain_streak": 0,
            }
        # Force a tiny live cap for a deterministic pruning proof. Strong has
        # retained evidence; weak is old, low-retention and negative-reward;
        # p-other is also materially productive.
        live = rebalance_live_population(
            teacher, total_capabilities=1, max_effective_override=2)

        self.assertIn(strong, live)
        self.assertNotIn(weak, live)
        self.assertIn(
            weak,
            set(teacher["causal_experiment"]["retired_effective_strategies"]),
        )

    def test_proven_retention_outranks_unproven_newborn_grace(self):
        teacher, strong, _weak = teacher_fixture()
        newborn_policy = {
            "lr": 0.00008, "old": 20, "preview": 0,
            "depth": 3, "contrast": 1.0, "distill": 0.35,
        }
        teacher["strategies"]["newborn"] = newborn_policy
        newborn = effective_policy_key(newborn_policy)
        teacher["causal_experiment"]["contexts"][
            "C.ADD|RECOVERY_1|factory/7"]["newborn"] = {
                "trials": 1, "retained": 0, "reward_sum": 1.0,
                "unsafe": 1, "no_target_gain_streak": 0,
            }
        teacher["causal_experiment"]["strategy_births"] = {
            newborn: {
                "origin_capability": "C.ADD", "origin_grade": "C",
                "curriculum_scope": "factory/7", "birth_event": 99,
                "proven_retained": False,
            },
        }

        live = rebalance_live_population(
            teacher, total_capabilities=1, max_effective_override=1)

        # A probationary one-shot child must never evict an effective strategy
        # that has already demonstrated actual candidate retention.
        self.assertEqual(live, (strong,))






if __name__ == "__main__":
    unittest.main()
