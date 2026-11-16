"""Mutation selection preserves retained ancestry and adaptive refinement."""
from bilqis_mlx.learning.tests.test_learning_experiment import (
    CausalTeacherExperimentTests, _diagnostic_context, _effective_policy_key, contextual_pick,
    effective_policy_features, patch, random, strategy_population_teacher,
)


class BreedingMutationTests(CausalTeacherExperimentTests):
    def test_bespoke_exploration_uses_matching_retained_parent_at_nominal_capacity(self):
        import bilqis_mlx.compatibility.historical_teacher_policy as policy_engine
        teacher = strategy_population_teacher(count=12)
        # Fill the legacy nominal ceiling with behaviorally duplicate preview
        # aliases. Effective capacity remains available.
        for index, (key, policy) in enumerate(list(teacher["strategies"].items())):
            alias = dict(policy, preview=2)
            alias_key = f"alias-{index:03d}"
            teacher["strategies"][alias_key] = alias
            teacher["global_stats"][alias_key] = dict(teacher["global_stats"][key])
            teacher["grade_stats"]["C"][alias_key] = dict(teacher["grade_stats"]["C"][key])
        self.assertEqual(len(teacher["strategies"]), 24)
        parent = "policy-007"
        # The retained recipe is proven for this capability in another phase.
        # Current-phase pressure has no retained incumbent, so this visit is an
        # actual exploration visit and should breed from that proven ancestry.
        context = "C.ADD|RECOVERY_1|scope"
        diagnostics = {"champion_candidate_count": 2, "unresolved_miss_count": 1,
                       "warnings": ()}
        channel = teacher["causal_experiment"]
        channel["capability_stagnation"] = {
            "C.ADD|scope": {
                "rejection_streak": 4, "no_target_gain_streak": 4,
                "attempts_since_retained": 4, "total_rejections": 4,
                "total_retained": 0,
                "current_rejection_reasons": {"NO_MEASURABLE_TARGET_GAIN": 4},
            },
        }
        diagnostic_key, _ = _diagnostic_context(
            channel, "C.ADD", "scope", diagnostics)
        channel["contexts"][context] = {
            parent: {
                "trials": 6, "reward_sum": 1.2, "unsafe": 2, "retained": 3,
                "latest": .2, "no_target_gain_streak": 0,
                "diagnostic_stats": {
                    diagnostic_key: {
                        "trials": 2, "reward_sum": .6, "unsafe": 0, "retained": 2,
                    },
                },
            },
            "policy-008": {
                "trials": 12, "reward_sum": 4., "unsafe": 2, "retained": 6,
                "latest": .3, "no_target_gain_streak": 0,
            },
        }
        before = {_effective_policy_key(p) for p in teacher["strategies"].values()}

        with patch.object(policy_engine, "MAX_STRATEGIES", 24):
            key, policy, metadata = contextual_pick(
                policy_engine, teacher, "C.ADD", "MAIN", random.Random(11),
                curriculum_scope="scope", diagnostics=diagnostics,
                return_metadata=True)

        self.assertEqual(metadata["selection_reason"], "FRESH_MUTATED_CHALLENGER")
        self.assertEqual(metadata["mutation_parent_policy_key"], parent)
        self.assertEqual(metadata["mutation_parent_basis"], "CAPABILITY_DIAGNOSTIC_RETAINED")
        self.assertNotIn(_effective_policy_key(policy), before)
        parent_features = effective_policy_features(teacher["strategies"][parent])
        child_features = effective_policy_features(policy)
        self.assertEqual(sum(parent_features[k] != child_features[k]
                             for k in parent_features), 1)
        self.assertEqual(
            teacher["causal_experiment"]["strategy_births"][_effective_policy_key(policy)]["origin_capability"],
            "C.ADD")

    def test_saturated_legacy_lattice_refines_one_numeric_gene(self):
        import bilqis_mlx.compatibility.historical_teacher_policy as policy_engine
        teacher = strategy_population_teacher(count=400)
        parent = "policy-000"
        channel = teacher["causal_experiment"]
        channel["contexts"]["C.ADD|MAIN|scope"] = {
            parent: {
                "trials": 8, "reward_sum": 2., "unsafe": 8, "retained": 0,
                "latest": .25, "no_target_gain_streak": 0,
            },
        }
        teacher["grade_stats"]["C"][parent]["reward_sum"] = 10.
        teacher["global_stats"][parent]["reward_sum"] = 10.
        channel["capability_stagnation"] = {
            "C.ADD|scope": {
                "rejection_streak": 4, "no_target_gain_streak": 4,
                "attempts_since_retained": 4, "total_rejections": 4,
                "total_retained": 0,
                "current_rejection_reasons": {"NO_MEASURABLE_TARGET_GAIN": 4},
            },
        }
        before = {_effective_policy_key(p) for p in teacher["strategies"].values()}
        self.assertEqual(len(before), 400)

        key, policy, metadata = contextual_pick(
            policy_engine, teacher, "C.ADD", "MAIN", random.Random(7),
            curriculum_scope="scope", return_metadata=True)

        self.assertEqual(metadata["selection_reason"], "FRESH_MUTATED_CHALLENGER")
        self.assertEqual(metadata["mutation_mode"], "ADAPTIVE_LOCAL_REFINEMENT")
        self.assertNotIn(_effective_policy_key(policy), before)
        parent_policy = teacher["strategies"][parent]
        parent_features = effective_policy_features(parent_policy)
        child_features = effective_policy_features(policy)
        changed = [name for name in parent_features
                   if parent_features[name] != child_features[name]]
        self.assertEqual(len(changed), 1)
        self.assertIn(changed[0], {"old", "lr", "distill"})
        self.assertGreaterEqual(policy["old"], min(policy_engine.KNOBS["old"]))
        self.assertLessEqual(policy["old"], max(policy_engine.KNOBS["old"]))
        self.assertGreaterEqual(policy["lr"], min(policy_engine.KNOBS["lr"]))
        self.assertLessEqual(policy["lr"], max(policy_engine.KNOBS["lr"]))
        self.assertGreaterEqual(policy["distill"], min(policy_engine.KNOBS["distill"]))
        self.assertLessEqual(policy["distill"], max(policy_engine.KNOBS["distill"]))
        self.assertEqual(teacher["strategies"][key], policy)
