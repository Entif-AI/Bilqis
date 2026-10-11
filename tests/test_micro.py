"""Small-world semantics, immutable coordinates and genuinely neural inference."""
import copy
import itertools
import tempfile
import unittest
from pathlib import Path

from bilqis_micro.kernel import (
    world, entity, bound, relation, logic, compare, quantify, compose,
    entails, rule_step, countermodel, observe, evidence_logic, record,
    evaluate, independent_evaluate, encode, decode, RULE,
)
from bilqis_micro.graph import catalog, append_catalog, compile_embeddings


class MicroKernelTests(unittest.TestCase):
    def setUp(self):
        self.a, self.b, self.c = map(entity, "ABC")
        self.w = world(list("ABC"), [("PARENT", "A", "B"), ("PARENT", "B", "C")])

    def check(self, expression, expected, w=None):
        r = record(w or self.w, expression)
        self.assertEqual(evaluate(r), expected)
        self.assertEqual(independent_evaluate(r), expected)
        self.assertEqual(decode(encode(r)), r)
        return r

    def test_inverse_direction_and_no_parent_transitivity(self):
        self.check(relation("PARENT", self.a, self.b), "TRUE")
        self.check(relation("PARENT", self.b, self.a), "FALSE")
        self.check(relation("CHILD", self.b, self.a), "TRUE")
        self.check(relation("PARENT", self.a, self.c), "FALSE")
        self.check(logic("XOR", relation("PARENT", self.a, self.b), relation("PARENT", self.b, self.a)), "TRUE")

    def test_quantifier_binding_and_edge_perturbation(self):
        two_hop = quantify("EXISTS", logic("AND", relation("PARENT", self.a, bound(0)), relation("PARENT", bound(0), self.c)))
        self.check(two_hop, "TRUE")
        reversed_edge = world(list("ABC"), [("PARENT", "A", "B"), ("PARENT", "C", "B")])
        self.check(two_hop, "FALSE", reversed_edge)
        self.check(compose("PARENT", "PARENT", self.a, self.c), "TRUE")
        self.check(quantify("FORALL", quantify("EXISTS", compare("EQ", bound(1), bound(0)))), "TRUE")
        self.check(quantify("EXISTS", quantify("FORALL", compare("EQ", bound(1), bound(0)))), "FALSE")

    def test_rule_derivation_and_countermodel(self):
        w = world(list("ABC"), self.w["facts"], rules=[RULE])
        conclusion = relation("GRANDPARENT", self.a, self.c)
        self.check(entails(conclusion), "TRUE", w)
        self.check(entails(relation("GRANDPARENT", self.c, self.a)), "FALSE", w)
        p1, p2 = relation("PARENT", self.a, self.b), relation("PARENT", self.b, self.c)
        self.check(rule_step([p1, p2], conclusion), "TRUE", w)
        self.check(rule_step([p2, p1], conclusion), "FALSE", w)
        self.check(countermodel([p1, p2], conclusion), "FALSE", w)
        self.check(countermodel([p1, p2], relation("PARENT", self.a, self.c)), "TRUE", w)
        self.check(entails(conclusion), "FALSE")

    def test_distinct_evidence_and_interpretations(self):
        evidence_cases = [([], [0], "UNKNOWN"),
                          ([("S0", "J0", "refute", 0)], [0], "FALSE"),
                          ([("S0", "J0", "support", 0)], [0], "TRUE"),
                          ([("S0", "J0", "support", 0), ("S1", "J0", "refute", 0)], [0], "CONFLICT"),
                          ([("S0", "J0", "support", 0)], [0, 1], "AMBIGUOUS")]
        for reports, live, expected in evidence_cases:
            w = world(list("ABC"), self.w["facts"], reports=reports, live=live,
                      propositions={"J0": relation("PARENT", self.a, self.b)})
            self.check(observe("J0"), expected, w)
        empty = world(list("ABC"), self.w["facts"], live=[0], propositions={"J0": relation("PARENT", self.a, self.b)})
        self.check(evidence_logic("AND", observe("J0"), relation("PARENT", self.b, self.a)), "FALSE", empty)
        self.check(evidence_logic("NOT", observe("J0")), "UNKNOWN", empty)

    def test_reject_unbound_wrong_type_and_encoded_gold(self):
        for expression in [relation("PARENT", bound(0), self.a), compare("EQ", {"kind":"literal","value":True}, self.a)]:
            with self.assertRaises(ValueError):
                record(self.w, expression)
        r = record(self.w, relation("PARENT", self.a, self.b))
        with self.assertRaises(ValueError):
            encode(dict(r, gold="TRUE"))
        r = copy.deepcopy(r)
        r["world"]["facts"].append(["PARENT", "A", "Z"])
        with self.assertRaises(ValueError):
            encode(r)

    def test_exhaustive_small_world_oracle_agreement_and_lossless_codec(self):
        possible = [(name, a, b) for name in ("PARENT", "CHILD", "LINK") for a, b in (("A", "B"), ("B", "A"))]
        queries = [relation(name, self.a, self.b) for name in ("PARENT", "CHILD", "LINK", "GRANDPARENT")]
        queries += [quantify("FORALL", quantify("EXISTS", relation("CHILD", bound(0), bound(1)))),
                    compose("PARENT", "CHILD", self.a, self.a)]
        for flags in itertools.product((False, True), repeat=len(possible)):
            for rules in ([], [RULE]):
                w = world(list("AB"), [f for f, keep in zip(possible, flags) if keep], rules=rules)
                for q in queries:
                    r = record(w, q)
                    self.assertEqual(evaluate(r), independent_evaluate(r))
                    self.assertEqual(decode(encode(r)), r)
        r = record(self.w, queries[0])
        for bad in (encode(r)[:-1], encode(r) + [5], [0] + encode(r)):
            with self.assertRaises(ValueError):
                decode(bad)

    def test_evidence_algebra_all_states_and_correlated_interpretations(self):
        states = [[], [("S0", "J0", "support", 0)], [("S0", "J0", "refute", 0)],
                  [("S0", "J0", "support", 0), ("S1", "J0", "refute", 0)]]
        for first, second in itertools.product(states, repeat=2):
            reports = first + [(s, "J1", p, i) for s, _, p, i in second]
            w = world(list("AB"), propositions={"J0": compare("EQ", self.a, self.b), "J1": compare("EQ", self.a, self.a)}, reports=reports)
            for op in ("AND", "OR"):
                r = record(w, evidence_logic(op, observe("J0"), observe("J1")))
                self.assertEqual(evaluate(r), independent_evaluate(r))
        w = world(list("AB"), propositions={"J0": compare("EQ", self.a, self.b)}, live=[0, 1],
                  reports=[("S0", "J0", "support", 0), ("S0", "J0", "refute", 1)])
        self.check(observe("J0"), "AMBIGUOUS", w)
        self.check(evidence_logic("OR", observe("J0"), evidence_logic("NOT", observe("J0"))), "TRUE", w)


class StableGeometryTests(unittest.TestCase):
    def test_append_never_reinterprets_or_moves_old_coordinates(self):
        original = catalog()
        initial, manifest = compile_embeddings(96, original)
        extra = {"id": "micro.entity.F", "family":"entity", "subtype":"individual", "signature":"Entity",
                 "arity":0, "stage":5, "edges":[{"kind":"prerequisite", "target":"cogal.value.true"}]}
        extended = append_catalog(original, [extra])
        again, receipt = compile_embeddings(96, extended)
        import torch
        self.assertTrue(torch.equal(initial, again[:len(initial)]))
        self.assertEqual(original["tokens"], extended["tokens"][:len(original["tokens"])] )
        self.assertEqual(manifest["row_sha256"], {k:v for k,v in receipt["row_sha256"].items() if k in manifest["row_sha256"]})
        with self.assertRaises(ValueError):
            append_catalog(original, [dict(extra, id="cogal.value.true")])


class DevelopmentalPathTests(unittest.TestCase):
    def test_stage_lineage_replay_and_fail_closed_evidence(self):
        from bilqis_micro.run import default_config, freeze, train, replay, read_json
        cfg = default_config()
        cfg["model"].update(width=24, layers=1, heads=3)
        cfg["stage_steps"] = [1] * 5
        with tempfile.TemporaryDirectory() as directory:
            out = Path(directory) / "run"
            freeze(cfg, out)
            train(out)
            result = replay(out)
            self.assertEqual(result["status"], "REPRODUCED")
            stages = read_json(out / "result.json")["stages"]
            for previous, current in zip(stages, stages[1:]):
                self.assertEqual(previous["end_state_sha256"], current["start_state_sha256"])
                self.assertEqual(previous["optimizer_after"], current["optimizer_before"])
                self.assertEqual(previous["end_step"], current["start_step"])
            with self.assertRaises(FileExistsError):
                train(out)
            with (out / "samples.json").open("a") as stream:
                stream.write(" ")
            with self.assertRaises(ValueError):
                replay(out)

    def test_generated_lessons_stages_and_evaluation_are_bound(self):
        from bilqis_micro.data import build_data, audit_data
        data = build_data()
        manifest = audit_data(data)
        self.assertEqual(set(data["stages"]), {str(i) for i in range(5)})
        self.assertGreater(manifest["max_input_tokens"], 17)
        all_train = {r["id"] for stage in data["stages"].values() for pool in stage["train"].values() for r in pool}
        for stage in data["stages"].values():
            for split in ("varied", "composite"):
                self.assertFalse(all_train & {r["id"] for r in stage["eval"][split]})
        self.assertEqual(build_data(), data)

    def test_neural_prediction_never_calls_oracles_and_checkpoint_keeps_optimizer(self):
        import torch
        from unittest.mock import patch
        from bilqis_ref.model import ModelConfig, batch, state_hash
        from bilqis_micro.model import initialize, predict, save_checkpoint, load_checkpoint
        model, initializer = initialize(ModelConfig(vocab_size=len(catalog()["tokens"]), width=24, layers=1, heads=3, context=96, precision="fp32"), 7)
        optimizer = torch.optim.AdamW(model.parameters(), lr=.01)
        r = record(world(list("AB"), [("PARENT", "A", "B")]), relation("PARENT", entity("A"), entity("B")))
        before = state_hash(model)
        logits = model(*batch([encode(r)]))
        torch.nn.functional.cross_entropy(logits, torch.tensor([1])).backward()
        optimizer.step()
        self.assertNotEqual(before, state_hash(model))
        with patch("bilqis_micro.kernel.evaluate", side_effect=AssertionError("oracle in inference")), patch("bilqis_micro.kernel.independent_evaluate", side_effect=AssertionError("oracle in inference")):
            predicted = predict(model, [r])
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "student.pt"
            save_checkpoint(path, model, initializer, {"step": 1, "parent_checkpoint_sha256": "genesis"}, optimizer)
            restored, payload = load_checkpoint(path)
            resumed = torch.optim.AdamW(restored.parameters(), lr=.01)
            resumed.load_state_dict(payload["optimizer"])
            self.assertEqual(state_hash(restored), state_hash(model))
            self.assertEqual(predict(restored, [r]), predicted)
            self.assertEqual({int(s["step"]) for s in resumed.state.values()}, {1})


if __name__ == "__main__":
    unittest.main()
