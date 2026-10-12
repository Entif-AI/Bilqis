"""Behavior-level checks of the separate formal semantic space."""
from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from bilqis_formal.curriculum import (STAGES, fixed_gate, mandatory_train, panels,
                                      validate_course)
from bilqis_formal.kevlab import choose, select_panel
from bilqis_formal.semantics import (LAWS, TOKENS, TOKEN_ID, app, encode, equivalent,
                                     evaluate, law_applies, match, rewrite, truth, verify_registry)


class FoundationSemanticTests(unittest.TestCase):
    def test_registry_has_actual_named_token_identities(self):
        self.assertTrue(verify_registry())
        for name in ("OP.NOT", "OP.AND", "OP.IMPLIES", "LAW.AND.ASSOCIATIVITY",
                     "LAW.AND.ANNIHILATOR.RIGHT", "META.UNIFORM_SUBSTITUTION"):
            self.assertIn(name, TOKEN_ID)
        self.assertEqual(len(TOKENS), len(set(TOKENS)))

    def test_oracle_truth_and_equivalence(self):
        self.assertFalse(evaluate(app("AND", "P", "Q"), {"P": True, "Q": False}))
        self.assertTrue(evaluate(app("IMPLIES", "P", "Q"), {"P": False, "Q": False}))
        self.assertTrue(equivalent(app("AND", "P", "FALSE"), "FALSE"))
        self.assertFalse(equivalent(app("IMPLIES", "P", "Q"), app("IMPLIES", "Q", "P")))

    def test_finite_pattern_metavariable_occurrence_constraints(self):
        self.assertIsNone(match(("AND", "$A", "$A"), app("AND", "P", "Q")))
        self.assertEqual(match(("AND", "$A", "$A"), app("AND", "P", "P")), {"$A": "P"})
        self.assertIsNone(match(("AND", "$A", "TRUE"), app("AND", "P", "FALSE")))

    def test_law_identity_is_not_just_truth_equivalence(self):
        source = app("AND", "P", "FALSE")
        self.assertTrue(law_applies(source, "FALSE", "LAW.AND.ANNIHILATOR.RIGHT"))
        self.assertFalse(law_applies(source, "FALSE", "LAW.AND.IDENTITY.RIGHT"))
        self.assertFalse(law_applies(app("AND", "FALSE", "P"), "FALSE",
                                     "LAW.AND.ANNIHILATOR.RIGHT"))
        source = app("AND", app("AND", "P", "Q"), "R")
        target = app("AND", "P", app("AND", "Q", "R"))
        self.assertTrue(law_applies(source, target, "LAW.AND.ASSOCIATIVITY"))
        self.assertFalse(law_applies(source, target, "LAW.AND.IDENTITY.RIGHT"))

    def test_nested_context_law_application(self):
        source = app("NOT", app("AND", "P", "FALSE"))
        target = app("NOT", "FALSE")
        self.assertEqual(rewrite(source, "LAW.AND.ANNIHILATOR.RIGHT", (0,)), target)
        self.assertTrue(law_applies(source, target, "LAW.AND.ANNIHILATOR.RIGHT", (0,)))
        self.assertFalse(law_applies(source, target, "LAW.AND.ANNIHILATOR.RIGHT", ()))

    def test_progression_split_balance_and_no_answer_leak(self):
        self.assertTrue(validate_course())
        for stage in STAGES:
            lessons = mandatory_train(stage.id) + [r for p in panels(stage.id, "lesson") for r in p.rows]
            gate = fixed_gate(stage.id)
            self.assertFalse({r["id"] for r in lessons} & {r["id"] for r in gate})
            self.assertEqual({r["gold"] for r in gate}, {True, False})
            self.assertTrue(all("gold" not in r["input"] for r in lessons + gate))
            for row in lessons + gate:
                self.assertEqual(row["gold"], truth(row["input"]))
                self.assertGreater(len(encode(row["input"])), 2)
                self.assertLessEqual(len(encode(row["input"])), 96)

    def test_first_gate_has_no_unlearned_composition(self):
        self.assertFalse(panels("F01.NOT", "lesson"))
        self.assertFalse(panels("F01.NOT", "exam"))
        gate = fixed_gate("F01.NOT")
        self.assertEqual(len(gate), 2)
        self.assertTrue(all(row["input"]["expression"] == ("NOT", "R") for row in gate))
        self.assertTrue(any(row["input"].get("expression") == ("NOT", ("NOT", "R"))
                            for row in fixed_gate("F03.NOT_INVOLUTION")))


class StubKev:
    def __init__(self, mode):
        self.mode = mode
        self.orders = []

    def score(self, state, question, candidates, binding=None):
        self.orders.append([x["candidate_id"] for x in candidates])
        ids = [x["candidate_id"] for x in candidates]
        chosen = ids[0] if self.mode == "position" else sorted(ids)[0]
        vals = {i: (1 / len(ids) if self.mode == "low" else .05) for i in ids}
        if self.mode != "low":
            vals[chosen] = 1 - .05 * (len(ids) - 1)
        return {"status": "OK", "choice": chosen, "probabilities": vals,
                "margin": 0. if self.mode == "low" else .8, "choice_calls": 1}


class KevPolicyTests(unittest.TestCase):
    def test_every_candidate_occupies_every_position(self):
        p = panels("F02.AND", "lesson")
        stub = StubKev("stable")
        result = choose("F02.AND", "lesson", p, teacher=stub)
        self.assertEqual(result["status"], "SELECTED")
        self.assertEqual(len(stub.orders), len(p))
        self.assertEqual({tuple(v) for v in stub.orders},
                         {tuple(x.id for x in p[i:] + p[:i]) for i in range(len(p))})
        self.assertIsNotNone(select_panel(p, result))
        for ident in [x.id for x in p]:
            self.assertEqual(sum(row.index(ident) == j for row in stub.orders for j in range(len(row))), len(p))

    def test_position_bias_rejected_for_lesson_and_exam(self):
        for role in ("lesson", "exam"):
            p = panels("F04.AND_IDENTITY", role)
            result = choose("F04.AND_IDENTITY", role, p, teacher=StubKev("position"))
            self.assertEqual(result["status"], "ORDER_UNSTABLE")
            self.assertIsNone(result["selected_id"])

    def test_low_margin_rejected(self):
        p = panels("F02.AND", "exam")
        self.assertEqual(choose("F02.AND", "exam", p, teacher=StubKev("low"))["status"], "LOW_MARGIN")


class ScratchModelTests(unittest.TestCase):
    def test_forward_gradient_checkpoint_and_replay(self):
        import torch
        from bilqis_ref.model import batch, state_hash
        from bilqis_formal.student import init_student, load_checkpoint, save_checkpoint, predict
        m, info = init_student(seed=117)
        rows = mandatory_train("F01.NOT")
        inputs, lengths = batch([encode(x["input"]) for x in rows])
        before = state_hash(m)
        opt = torch.optim.AdamW(m.parameters(), lr=.002)
        logits = m(inputs, lengths)
        self.assertEqual(tuple(logits.shape), (len(rows), 2))
        opt.zero_grad()
        torch.nn.functional.cross_entropy(logits, torch.tensor([int(x["gold"]) for x in rows])).backward()
        opt.step()
        self.assertNotEqual(before, state_hash(m))
        with tempfile.TemporaryDirectory() as dirname:
            p = Path(dirname) / "test.pt"
            save_checkpoint(p, m, opt, "F01.NOT", {"correct": 0}, info)
            loaded, payload = load_checkpoint(p)
            self.assertEqual(state_hash(m), state_hash(loaded))
            self.assertEqual(payload["stage"], "F01.NOT")
            self.assertEqual([x["prediction"] for x in predict(m, rows)],
                             [x["prediction"] for x in predict(loaded, rows)])


if __name__ == "__main__":
    unittest.main()
