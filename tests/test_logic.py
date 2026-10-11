"""Formal contract and leakage boundaries for the exploratory T0/T1 pilot."""
import itertools
import unittest
from unittest.mock import patch

import torch

from bilqis_logic.kernel import (
    OPERATORS, TABLES, encode, decode, evaluate, equivalent, independent_evaluate,
    literal, variable, apply, evaluation_record, equivalence_record,
)
from bilqis_logic.geometry import compile_embeddings, tensor_hash, registry
from bilqis_logic.model import initialize, predict
from bilqis_logic.data import build_data, audit_splits, structure
from bilqis_logic.kernel import gold
from bilqis_ref.model import ModelConfig, batch, state_hash


class KernelTests(unittest.TestCase):
    def test_exhaustive_truth_tables(self):
        expected = {
            "NOT": [False, True], "AND": [True, False, False, False],
            "OR": [True, True, True, False], "XOR": [False, True, True, False],
            "XNOR": [True, False, False, True],
            "IMPLIES": [True, False, True, True], "IFF": [True, False, False, True],
        }
        self.assertEqual(TABLES, expected)
        for op in OPERATORS:
            for args in itertools.product((True, False), repeat=OPERATORS[op]):
                expr = apply(op, *map(literal, args))
                index = (0 if args[0] else 1) if len(args) == 1 else (
                    (0 if args[0] else 2) + (0 if args[1] else 1))
                self.assertEqual(evaluate(expr, {}), expected[op][index])
                self.assertEqual(evaluate(expr, {}), independent_evaluate(expr, {}))

    def test_codec_roundtrip_and_gold_excluded(self):
        p, q = variable("P"), variable("Q")
        records = [evaluation_record(apply("AND", literal(True), literal(True)), {}),
                   evaluation_record(apply("IMPLIES", p, q), {"P": True, "Q": False}),
                   equivalence_record(apply("XNOR", p, q), apply("IFF", p, q))]
        for row in records:
            self.assertEqual(decode(encode(row)), row)
            self.assertEqual(encode(row), encode(dict(row, gold=not row.get("gold", False))))

    def test_direction_and_equivalence(self):
        p, q = variable("P"), variable("Q")
        self.assertFalse(evaluate(apply("IMPLIES", p, q), {"P": True, "Q": False}))
        self.assertTrue(evaluate(apply("IMPLIES", q, p), {"P": True, "Q": False}))
        self.assertFalse(equivalent(apply("IMPLIES", p, q), apply("IMPLIES", q, p)))
        self.assertTrue(equivalent(apply("XNOR", p, q), apply("IFF", p, q)))

    def test_typed_rejections(self):
        for expr, env in [({"kind": "literal", "value": 1}, {}),
                          ({"kind": "literal", "value": "UNKNOWN"}, {}),
                          ({"kind": "apply", "operator": "NOT", "args": []}, {}),
                          (variable("P"), {}), (variable("P"), {"P": "TRUE"})]:
            with self.assertRaises(ValueError):
                evaluate(expr, env)
        with self.assertRaises(ValueError):
            variable("R")
        for ids in ([1, 11], [1, 7, 3, 5, 5], [999], [2, 8, 4, 8]):
            with self.assertRaises(ValueError):
                decode(ids)


class NeuralTests(unittest.TestCase):
    def test_initializer_controls_and_identity(self):
        aligned, receipt = compile_embeddings(64)
        repeated, again = compile_embeddings(64)
        self.assertTrue(torch.equal(aligned, repeated))
        self.assertEqual(receipt, again)
        permuted, perm = compile_embeddings(64, "semantic_permuted")
        self.assertEqual(sorted(tensor_hash(r) for r in aligned), sorted(tensor_hash(r) for r in permuted))
        self.assertFalse(torch.equal(aligned[1:], permuted[1:]))
        self.assertTrue(bool((aligned[0] == 0).all()))
        self.assertTrue(bool((permuted[0] == 0).all()))
        random, _ = compile_embeddings(64, "iid_random", 111)
        self.assertFalse(torch.equal(random, aligned))
        self.assertTrue(torch.equal(random, compile_embeddings(64, "iid_random", 111)[0]))
        self.assertEqual(len({tensor_hash(r) for r in aligned}), len(aligned))
        self.assertTrue(any(e["relation"] == "equivalent" for e in registry()["edges"]))

    def test_neural_oracle_separation_and_real_update(self):
        model, _ = initialize(ModelConfig(vocab_size=17, context=64, width=64, layers=2, heads=4, precision="fp32"))
        records = [evaluation_record(apply("AND", literal(True), literal(True)), {}),
                   evaluation_record(apply("XOR", literal(True), literal(True)), {})]
        before = state_hash(model)
        inputs, lengths = batch([encode(r) for r in records])
        with patch("bilqis_logic.kernel.evaluate", side_effect=AssertionError("oracle used")), \
                patch("bilqis_logic.kernel.equivalent", side_effect=AssertionError("oracle used")), \
                patch("bilqis_logic.kernel.gold", side_effect=AssertionError("gold used")):
            self.assertEqual(len(predict(model, records)), 2)
            logits = model(inputs, lengths)
        self.assertEqual(tuple(logits.shape), (2, 2))
        loss = torch.nn.functional.cross_entropy(logits, torch.tensor([1, 0]))
        optimizer = torch.optim.AdamW(model.parameters(), lr=.002, foreach=False)
        loss.backward()
        gradients = [p.grad for p in model.parameters() if p.grad is not None]
        self.assertTrue(all(bool(torch.isfinite(g).all()) for g in gradients))
        self.assertGreater(sum(float(g.abs().sum()) for g in gradients), 0)
        optimizer.step()
        self.assertNotEqual(before, state_hash(model))


class DataTests(unittest.TestCase):
    def test_frozen_splits_oracles_roundtrips_and_balance(self):
        data = build_data()
        manifest = audit_splits(data)
        self.assertEqual(len(data["TRAIN_A"]), 26)
        self.assertGreater(manifest["HELDOUT_COMPOSITION"]["structures"], 10)
        for split, rows in data.items():
            for row in rows:
                self.assertEqual(row["gold"], gold(row["input"], independent=True))
                self.assertEqual(decode(encode(row["input"])), row["input"])
        for split in ("TRAIN_B_EQUIVALENCE", "HELDOUT_EQUIVALENCE"):
            labels = [r["gold"] for r in data[split]]
            self.assertEqual(sum(labels), len(labels) // 2)
        hard = data["HARD_NEGATIVES"][0]
        self.assertFalse(hard["gold"])

    def test_split_leak_is_rejected(self):
        data = build_data()
        data["HELDOUT_COMPOSITION"].append(data["TRAIN_A"][0])
        with self.assertRaises(ValueError):
            audit_splits(data)

    def test_injected_wrong_label_is_rejected(self):
        data = build_data()
        data["TRAIN_A"][0]["gold"] = not data["TRAIN_A"][0]["gold"]
        with self.assertRaises(ValueError):
            audit_splits(data)


if __name__ == "__main__":
    unittest.main()
