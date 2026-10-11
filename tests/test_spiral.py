"""Focused spiral-contract proof without spending a training update."""
from __future__ import annotations

from collections import Counter
import copy
import gzip
import json
from pathlib import Path
import unittest
import torch

from bilqis_development.continuation import load as load_checkpoint
from bilqis_development.kernel import encode
from bilqis_micro.graph import STATES
from bilqis_ref.model import batch as model_batch, state_hash
from bilqis_spiral.run import verify as verify_freeze

from bilqis_spiral.sampler import (MIX, Sampler, build_pools, check_row, dev_signals,
                                   existing_ids, family_key)

RUN = Path(__file__).resolve().parents[1] / "docs/evidence/u5-u6/run-01"


def load(name):
    return json.loads(gzip.decompress((RUN / name).read_bytes()))


class SpiralTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.data = load("data.json.gz")
        cls.pools = build_pools(cls.data, seed=11819, updates=8)
        cls.baseline = load("after-U6.json.gz")
        cls.signals = dev_signals(cls.baseline, cls.baseline)

    def test_all_training_rows_are_disjoint_from_every_frozen_eval_row(self):
        frozen_eval = {r["id"] for stage in self.data["stages"].values()
                       for rows in stage["eval"].values() for r in rows}
        self.assertFalse(frozen_eval & {r["id"] for category in ("fresh", "cross", "weak")
                                       for group in self.pools[category].values() for r in group})
        for category in ("fresh", "cross", "weak"):
            for rows in self.pools[category].values():
                for r in rows:
                    check_row(r)

    def test_new_prior_comes_from_canonical_old_generators_and_never_repeats(self):
        ancestor = existing_ids(self.data)
        self.assertTrue(all(0 <= r["stage"] <= 4 for rows in self.pools["fresh"].values() for r in rows))
        self.assertFalse(ancestor & {r["id"] for rows in self.pools["fresh"].values() for r in rows})
        sampler = Sampler(self.data, self.pools, 11820, self.signals)
        fresh = []
        for _ in range(8):
            rows, categories, _ = sampler.batch()
            fresh.extend(r["id"] for r, category in zip(rows, categories) if category == "fresh_prior")
        self.assertEqual(len(fresh), 32)
        self.assertEqual(len(set(fresh)), 32)

    def test_cross_stage_is_causally_active_on_both_branches(self):
        self.assertEqual({k: len(v) for k, v in self.pools["cross"].items()}, {"5": 48, "6": 48})
        self.assertEqual(len(self.pools["causal"]), 96)
        for p in self.pools["causal"]:
            self.assertNotEqual(p["base_gold"], p["old_changed_gold"])
            self.assertNotEqual(p["base_gold"], p["new_changed_gold"])
            check_row(p["old_contrast"])
            check_row(p["new_contrast"])
            self.assertEqual({p["old_contrast"]["id"], p["new_contrast"]["id"]},
                             {p["old_changed"], p["new_changed"]})

    def test_exact_counts_old_reinforcement_floors_and_weak_family_ceiling(self):
        sampler = Sampler(self.data, self.pools, 11820, self.signals)
        frozen_eval = {r["id"] for stage in self.data["stages"].values()
                       for pool in stage["eval"].values() for r in pool}
        for _ in range(8):
            rows, categories, targeted = sampler.batch()
            self.assertEqual(Counter(categories), Counter(MIX))
            self.assertEqual(len(rows), 32)
            self.assertFalse({r["id"] for r in rows} & frozen_eval)
            cross = [r for r, category in zip(rows, categories) if category == "cross_stage"]
            self.assertEqual(Counter(r["stage"] for r in cross), {5: 4, 6: 4})
            weak = [(r, f) for r, category, f in zip(rows, categories, targeted)
                    if category == "weak_reinforcement"]
            self.assertGreaterEqual(sum(r["stage"] < 5 for r, _ in weak), 2)
            self.assertGreaterEqual(sum(r["stage"] >= 5 for r, _ in weak), 2)
            self.assertLessEqual(max(Counter(f for _, f in weak).values()), 3)
            self.assertTrue(all(f == f'{r["stage"]}:{family_key(r["stage"], r["family"])}'
                                for r, f in weak))

    def test_dev_signals_shift_with_diagnostic_errors_only(self):
        altered = copy.deepcopy(self.baseline)
        row = altered["6"]["varied"]["predictions"][0]
        original_key = f'6:{family_key(6, row["family"])}'
        row["prediction"] = "FALSE" if row["gold"] != "FALSE" else "TRUE"
        shifted = dev_signals(altered, self.baseline)
        if self.baseline["6"]["varied"]["predictions"][0]["prediction"] == row["gold"]:
            self.assertGreater(shifted[original_key]["weight"], self.signals[original_key]["weight"])
        self.assertEqual(set(shifted), set(self.pools["weak"]))

    def test_final_evaluation_is_fresh_and_never_used_by_sampler(self):
        parent = existing_ids(self.data)
        training = {r["id"] for category in ("fresh", "cross", "weak")
                    for rows in self.pools[category].values() for r in rows}
        final = [r for s in self.pools["final"].values() for rows in s.values() for r in rows]
        self.assertEqual(len(final), 448)
        self.assertEqual(len({r["id"] for r in final}), 448)
        self.assertFalse({r["id"] for r in final} & (training | parent))

    def test_independent_oracle_rejects_corrupt_gold(self):
        row = copy.deepcopy(self.pools["cross"]["6"][0])
        row["gold"] = "CONFLICT" if row["gold"] != "CONFLICT" else "FALSE"
        with self.assertRaisesRegex(ValueError, "oracle"):
            check_row(row)

    def test_frozen_successor_executes_a_real_no_update_model_batch(self):
        policy, pools, corpus = verify_freeze(RUN.parents[1] / "spiral-u7/run-01")
        self.assertEqual(policy["categories"], MIX)
        self.assertEqual(policy["parent_optimizer"]["steps"], [13400])
        sampler = Sampler(corpus, pools, policy["seed"] + 1, self.signals)
        rows, categories, _ = sampler.batch()
        ids, lengths = model_batch([encode(r["input"]) for r in rows])
        checkpoint, _, _ = load_checkpoint(RUN / "after-U6.pt")
        before = state_hash(checkpoint)
        with torch.no_grad():
            logits = checkpoint(ids, lengths)
            loss = torch.nn.functional.cross_entropy(logits, torch.tensor(
                [STATES.index(r["gold"]) for r in rows]))
        self.assertEqual(tuple(logits.shape), (32, len(STATES)))
        self.assertTrue(bool(torch.isfinite(loss)))
        self.assertEqual(state_hash(checkpoint), before)
        self.assertEqual(Counter(categories), Counter(MIX))


if __name__ == "__main__":
    unittest.main()
