import unittest

from bilqis_mlx.learning.teacher_strategy_population import (
    checkpoint_active_effective_strategy_keys,
    durable_policy_cooldown_status,
    effective_strategy_inventory,
    record_checkpoint_policy_outcome,
    sibling_cooldown_penalty,
)
from bilqis_mlx.learning.tests.teacher_strategy.support import teacher_fixture


class TeacherStrategyCooldownTests(unittest.TestCase):
    def test_durable_capability_cooldown_requires_two_failed_student_epochs_and_retention_clears(self):
        teacher, strong, _weak = teacher_fixture()
        channel = teacher["causal_experiment"]
        capability_key = "C.ADD|factory/7"
        channel["capability_stagnation"] = {
            capability_key: {
                "total_rejections": 0, "total_retained": 0,
            },
        }
        context = "C.ADD|RECOVERY_1|factory/7"

        for sha in ("a" * 64, "b" * 64):
            for _ in range(4):
                channel["capability_stagnation"][capability_key]["total_rejections"] += 1
                record_checkpoint_policy_outcome(
                    channel, context, strong, sha,
                    no_target_gain=True, retained=False)
            status = durable_policy_cooldown_status(
                channel, "C.ADD", "factory/7", strong)
            if sha.startswith("a"):
                self.assertFalse(status["active"])

        self.assertTrue(status["active"])
        self.assertEqual(status["failed_student_epochs"], 2)
        self.assertEqual(status["remaining_capability_visits"], 8)
        inventory = effective_strategy_inventory(teacher)
        active, retired = checkpoint_active_effective_strategy_keys(
            teacher, "C",
            channel["contexts"][context], channel, context,
            tuple(inventory), inventory, "c" * 64)
        self.assertIn(strong, retired)
        self.assertNotIn(strong, active)
        self.assertGreater(
            sibling_cooldown_penalty(
                channel, "C.SUB", "factory/7", strong), 0.)
        self.assertFalse(durable_policy_cooldown_status(
            channel, "C.SUB", "factory/7", strong)["active"])

        channel["capability_stagnation"][capability_key]["total_retained"] += 1
        record_checkpoint_policy_outcome(
            channel, context, strong, "c" * 64,
            no_target_gain=False, retained=True)
        self.assertFalse(durable_policy_cooldown_status(
            channel, "C.ADD", "factory/7", strong)["active"])



if __name__ == "__main__":
    unittest.main()
