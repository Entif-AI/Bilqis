"""Executable behavior checks for the no-reset U7E developmental loop."""
import copy
import random
import unittest

from bilqis_ref.model import state_hash
from bilqis_micro.run import optimizer_receipt
from bilqis_development.kernel import encode
from bilqis_u7e.lessons import build, paired_batch, validate_pair, without_exposed
from bilqis_u7e import run as developmental


class CumulativeDevelopmentTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.direct = build(15531, 70, compositional=False)
        cls.chained = build(15541, 70, compositional=True)

    def test_taught_world_pairs_differ_only_in_semantically_active_link(self):
        for dataset in (self.direct, self.chained):
            self.assertIn("DERIVED_FROM", dataset["episodes"])
            self.assertIn("SUPERSEDES", dataset["episodes"])
            for family, pairs in dataset["episodes"].items():
                self.assertGreaterEqual(len(pairs), 6, family)
                for a, b in pairs:
                    self.assertTrue(validate_pair(a, b))
                    self.assertLessEqual(len(encode(a["input"])), 96)
                    self.assertLessEqual(len(encode(b["input"])), 96)

    def test_instruction_orders_paired_semantics_before_composition(self):
        direct = paired_batch(self.direct, self.chained, iteration=0,
                              rng=random.Random(123))
        composite = paired_batch(self.direct, self.chained, iteration=400,
                                 rng=random.Random(123))
        self.assertEqual(len(direct), 16)
        self.assertEqual(len(composite), 16)
        self.assertEqual({r["lesson_level"] for r in direct}, {"direct"})
        self.assertEqual({r["lesson_level"] for r in composite}, {"chain"})
        for examples in (direct, composite):
            for i in range(0, 16, 2):
                self.assertTrue(validate_pair(*examples[i:i + 2]))

    def test_parent_is_existing_learned_student_not_newly_initialized(self):
        model, optimizer, payload = developmental.parent()
        self.assertEqual(optimizer_receipt(optimizer)["steps"], [13400])
        self.assertEqual(state_hash(model), developmental.PARENT_STATE)
        self.assertEqual(model.config.vocab_size, 113)
        self.assertEqual(len(payload["graph"]["nodes"]), 113)

    def test_dashboard_removes_identity_overlap_without_resetting_train(self):
        ids = {r["id"] for a, b in self.direct["episodes"]["DERIVED_FROM"][:2]
               for r in (a, b)}
        after = without_exposed(self.direct, ids)
        self.assertFalse(ids & {r["id"] for pairs in after["episodes"].values()
                                for a, b in pairs for r in (a, b)})

    def test_single_gradient_continues_real_optimizer_moments(self):
        model, optimizer, payload = developmental.parent()
        parent_state = state_hash(model)
        ancestor = copy.deepcopy(model)
        for param in ancestor.parameters():
            param.requires_grad_(False)
        corpus = developmental.spiral.read(developmental.PARENT / "data.json.gz")
        old = developmental.memory(corpus)
        training_rows = developmental.batch_rows(
            self.direct, self.chained, old, iteration=0,
            rng=random.Random(3199))
        self.assertEqual(sum(r["stage"] == 4 for r in training_rows[16:]), 6)
        self.assertEqual(sum(r["stage"] == 0 for r in training_rows[16:]), 3)
        receipt = developmental.step(model, ancestor, optimizer, training_rows)
        self.assertEqual(optimizer_receipt(optimizer)["steps"], [13401])
        self.assertNotEqual(state_hash(model), parent_state)
        self.assertGreater(receipt["new_loss"], 0)
        self.assertEqual(model.config.vocab_size, len(payload["graph"]["tokens"]))

    def test_utility_rejects_forgetting_and_does_not_hide_no_progress(self):
        baseline = {"primitives": 26, "u0_composite": 74,
                    "u4_composite": 50, "u4_varied": 81,
                    "u5_varied": 174, "u6_varied": 213,
                    "lineage_10": 4,
                    "direct_pairs": {"both": 20, "pairs": 90},
                    "chain_pairs": {"both": 18, "pairs": 90}}
        better = copy.deepcopy(baseline)
        better["direct_pairs"]["both"] += 5
        self.assertTrue(developmental.viable(better, baseline))
        self.assertGreater(developmental.utility(better, baseline),
                           developmental.utility(baseline, baseline))
        failed = copy.deepcopy(better)
        failed["u4_composite"] = 39
        self.assertFalse(developmental.viable(failed, baseline))


if __name__ == "__main__":
    unittest.main()
