"""Prove the next round really compounds the best learned U7E checkpoint."""
import copy
from pathlib import Path
import random
import unittest

import torch

from bilqis_micro.run import optimizer_receipt
from bilqis_ref.model import state_hash
from bilqis_u7e import run as u7e
from bilqis_u7e.lessons import build
from bilqis_u7f import run as u7f


class MemoryContinuationTests(unittest.TestCase):
    # Historical source and CPU behavior tests run in CI. Actual neural
    # resumption needs the ignored local U7E checkpoint and must not
    # download a model or pretend to initialize equivalent scratch weights.
    @unittest.skipUnless((u7e.RUN / "result.json").is_file(),
                         "Local continued U7E checkpoint is not in public Git.")
    def test_parent_is_actual_selected_U7E_optimizer_not_prior_U6(self):
        model, optimizer, payload, chosen = u7f.resume()
        self.assertEqual(chosen["step"], 13528)
        self.assertEqual(optimizer_receipt(optimizer)["steps"], [13528])
        self.assertEqual(state_hash(model),
                         "c118c6086bef09b862bfc7e19a544ac2081506c115fb09f203e47127c944a401")
        self.assertTrue(torch.equal(torch.get_rng_state(), payload["torch_rng"]))

    @unittest.skipUnless((u7e.RUN / "result.json").is_file(),
                         "Local continued U7E checkpoint is not in public Git.")
    def test_old_and_new_compose_one_meaningful_update(self):
        model, optimizer, payload, _ = u7f.resume()
        reference = copy.deepcopy(model)
        for param in reference.parameters():
            param.requires_grad_(False)
        old = u7e.memory(u7e.spiral.read(u7e.PARENT / "data.json.gz"))
        easy = build(14831, 100, compositional=False)
        hard = build(14837, 100, compositional=True)
        examples = u7f.batch_rows(easy, hard, old, iteration=0, rng=random.Random(211))
        self.assertEqual(len(examples), 32)
        self.assertEqual(sum(row["stage"] == 0 for row in examples[12:]), 5)
        self.assertEqual(sum(row["stage"] == 4 for row in examples[12:]), 8)
        old_sha = state_hash(model)
        self.assertGreater(u7f.learn(model, reference, optimizer, examples), 0)
        self.assertNotEqual(state_hash(model), old_sha)
        self.assertEqual(optimizer_receipt(optimizer)["steps"], [13529])
        self.assertEqual(model.config.vocab_size, len(payload["graph"]["tokens"]))

    def test_no_tradeoff_disguised_as_improvement(self):
        baseline = {"primitives": 26, "u0_composite": 72,
                    "u4_composite": 47, "u4_varied": 84,
                    "u5_varied": 163, "u6_varied": 213,
                    "lineage_10": 5,
                    "direct_pairs": {"both": 30}, "chain_pairs": {"both": 27}}
        better = copy.deepcopy(baseline)
        better["u4_composite"] = 50
        self.assertTrue(u7f.viable(better, baseline))
        self.assertGreater(u7f.utility(better, baseline),
                           u7f.utility(baseline, baseline))
        broken = copy.deepcopy(better)
        broken["primitives"] = 25
        self.assertFalse(u7f.viable(broken, baseline))
        broken["primitives"] = 26
        broken["u0_composite"] = 69
        self.assertFalse(u7f.viable(broken, baseline))
        traded = copy.deepcopy(baseline)
        traded["u4_composite"] = 61
        traded["u5_varied"] = 153
        traded["u6_varied"] = 205
        traded["direct_pairs"]["both"] = 35
        traded["chain_pairs"]["both"] = 40
        traded["lineage_10"] = 7
        self.assertTrue(u7f.viable(traded, baseline))
        self.assertGreater(u7f.utility(traded, baseline),
                           u7f.utility(baseline, baseline))


if __name__ == "__main__":
    unittest.main()
