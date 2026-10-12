import copy
from collections import Counter
from pathlib import Path
import unittest
import torch

from bilqis_development.continuation import load
from bilqis_micro.run import optimizer_receipt
from bilqis_ref.model import state_hash
from bilqis_spiral.run import read, PARENT, CURRENT
from bilqis_spiral.sampler import Sampler, MIX, build_pools, dev_signals
from bilqis_u7b.run import teaching_panel, apply_choice, preserved_start


class U7BTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.corpus = read(PARENT / 'data.json.gz')
        cls.dev = read(PARENT / 'after-U6.json.gz')
        cls.scores = {s: {split: p[split] for split in ('varied', 'composite')} for s, p in cls.dev.items()}
        cls.signals = dev_signals(cls.scores)
        cls.pools = build_pools(cls.corpus, 73971, 8)

    def test_teacher_choice_is_consequential_without_a_pedagogical_gold(self):
        panel = teaching_panel(6, self.signals, 0)
        self.assertEqual(panel['decision_class'], 'pedagogical_selection')
        self.assertNotIn('gold', panel)
        self.assertEqual(len(panel['candidates']), 4)
        ids = [r['id'] for r in panel['candidates'] if r['id'] != 'REVIEW']
        cross = [{'id': 'row'+str(i), 'teacher_spec_id': identity} for i, identity in enumerate(ids)]
        def trace(choice): return {'status': 'OK', 'choice': choice, 'margin': .5}
        one, disposition = apply_choice(panel, trace(ids[0]), cross)
        two, _ = apply_choice(panel, trace(ids[1]), cross)
        self.assertNotEqual(one, two)
        self.assertEqual(disposition, 'accepted')
        fallback, disposition = apply_choice(panel, trace('REVIEW'), cross)
        self.assertEqual(fallback, cross); self.assertEqual(disposition, 'review-fallback')

    def test_each_batch_keeps_allocations_and_weak_coverage(self):
        sampler = Sampler(self.corpus, self.pools, 73972, self.signals)
        for _ in range(8):
            rows, categories, keys = sampler.batch()
            self.assertEqual(Counter(categories), Counter(MIX))
            weak = [(r, key) for r, cat, key in zip(rows, categories, keys) if cat == 'weak_reinforcement']
            self.assertGreaterEqual(sum(r['stage'] < 5 for r, _ in weak), 2)
            self.assertGreaterEqual(sum(r['stage'] >= 5 for r, _ in weak), 2)
            self.assertLessEqual(max(Counter(key for _, key in weak).values()), 3)

    def test_real_checkpoint_and_all_adamw_moments_are_preserved_before_gradients(self):
        model, optimizer, payload = load(CURRENT)
        before = state_hash(model), optimizer_receipt(optimizer)
        receipt = preserved_start(model, optimizer, payload)
        self.assertEqual(receipt['optimizer']['steps'], [13400])
        self.assertEqual((state_hash(model), optimizer_receipt(optimizer)), before)
        changed = copy.deepcopy(payload); changed['optimizer_receipt']['state_sha256'] = 'fake'
        with self.assertRaises(ValueError): preserved_start(model, optimizer, changed)


if __name__ == '__main__': unittest.main()
