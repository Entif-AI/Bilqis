"""Shared deterministic teacher fixtures for strategy-owner tests."""

from bilqis_mlx.learning.teacher_strategy_population import effective_policy_key


def teacher_fixture():
    strategies = {
        "p-strong": {"lr": 0.00013, "old": 8, "preview": 0,
                     "depth": 3, "contrast": 0.5, "distill": 0.15},
        "p-weak": {"lr": 0.00004, "old": 4, "preview": 0,
                   "depth": 1, "contrast": 0.0, "distill": 0.0},
        "p-other": {"lr": 0.00030, "old": 12, "preview": 0,
                    "depth": 1, "contrast": 0.0, "distill": 0.0},
    }
    strong = effective_policy_key(strategies["p-strong"])
    weak = effective_policy_key(strategies["p-weak"])
    return {
        "strategies": strategies,
        "causal_experiment": {
            "events": 11,
            "contexts": {
                "C.ADD|RECOVERY_1|factory/7": {
                    "p-strong": {
                        "trials": 16, "retained": 12, "reward_sum": 8.0,
                        "unsafe": 4, "no_target_gain_streak": 0,
                        "target_delta_sum": 24.0,
                        "protected_net_delta_sum": 0.0,
                        "worst_protected_loss_sum": 0.0,
                        "attempted_steps_sum": 160,
                    },
                    "p-weak": {
                        "trials": 16, "retained": 1, "reward_sum": -4.0,
                        "unsafe": 15, "no_target_gain_streak": 3,
                        "target_delta_sum": 3.0,
                        "protected_net_delta_sum": -8.0,
                        "worst_protected_loss_sum": 8.0,
                        "attempted_steps_sum": 256,
                    },
                },
            },
            "capability_stagnation": {},
        },
    }, strong, weak
