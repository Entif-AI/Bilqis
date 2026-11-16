"""Selection boundaries for bespoke policies."""
import unittest
from bilqis_mlx.learning.teacher_breeding import filter_active_effective
from bilqis_mlx.learning.teacher_strategy_population import effective_policy_key, effective_strategy_inventory
from bilqis_mlx.learning.tests.teacher_strategy.support import teacher_fixture


class BreedingSelectionTests(unittest.TestCase):
    def test_unproven_bespoke_policy_stays_capability_local_until_retained(self):
        teacher, strong, weak = teacher_fixture()
        channel = teacher["causal_experiment"]
        channel["live_effective_strategies"] = [strong, weak]
        channel["strategy_births"] = {
            weak: {
                "origin_capability": "C.ADD", "origin_grade": "C",
                "curriculum_scope": "factory/7", "birth_event": 12,
                "proven_retained": False,
            },
        }
        inventory = effective_strategy_inventory(teacher)

        local = filter_active_effective(
            teacher, grade="C", capability="C.ADD",
            curriculum_scope="factory/7", active_effective=(strong, weak),
            inventory=inventory)
        sibling = filter_active_effective(
            teacher, grade="C", capability="C.SUB",
            curriculum_scope="factory/7", active_effective=(strong, weak),
            inventory=inventory)

        self.assertIn(weak, local)
        self.assertNotIn(weak, sibling)

    def test_empty_capability_live_population_reseeds_from_compatible_archive(self):
        teacher, strong, weak = teacher_fixture()
        channel = teacher["causal_experiment"]
        other = effective_policy_key(teacher["strategies"]["p-other"])
        channel["live_effective_strategies"] = [strong, weak]
        channel["strategy_births"] = {
            strong: {
                "origin_capability": "A.IDENTITY", "origin_grade": "A",
                "curriculum_scope": "factory/7", "birth_event": 12,
                "proven_retained": False,
            },
            weak: {
                "origin_capability": "B.AND", "origin_grade": "B",
                "curriculum_scope": "factory/7", "birth_event": 13,
                "proven_retained": False,
            },
        }
        inventory = effective_strategy_inventory(teacher)

        recovered = filter_active_effective(
            teacher, grade="A", capability="A.EDGE",
            curriculum_scope="factory/7", active_effective=(strong, weak),
            inventory=inventory)

        self.assertEqual(recovered, (other,))

    def test_proven_bespoke_policy_is_grade_portable_across_numeric_scope_revision(self):
        teacher, strong, weak = teacher_fixture()
        channel = teacher["causal_experiment"]
        channel["live_effective_strategies"] = [strong, weak]
        channel["strategy_births"] = {
            weak: {
                "origin_capability": "C.ADD", "origin_grade": "C",
                "curriculum_scope": "factory/10", "birth_event": 12,
                "proven_retained": True,
            },
        }
        inventory = effective_strategy_inventory(teacher)

        revised_scope = filter_active_effective(
            teacher, grade="C", capability="C.SUB",
            curriculum_scope="factory/4", active_effective=(strong, weak),
            inventory=inventory)

        self.assertIn(weak, revised_scope)
