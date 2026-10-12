"""Actual behavior and failure-policy tests for the versioned v0.5 controller."""
from __future__ import annotations

import json
from pathlib import Path
import random
import tempfile
import unittest
from unittest.mock import patch

import torch

from bilqis_formal.controller_v5 import (
    ARMS, BUDGET, Budget, decide_after_block, family, formative_mastered,
    run_stage, sample_balanced, weakest_retained, declined_prior,
    optimizer_digest)
from bilqis_formal.curriculum_v5 import (
    DEPENDENCIES, STAGES, literal_coverage_rows, split, validate)
from bilqis_formal.dialogue_v3 import (
    CompletedTurn, IDS, encode_completed, encode_prompt)
from bilqis_formal.pilot_v5 import (
    SOURCE_FILES, VERSION, replay, run, run_arm, source_sha256)
from bilqis_formal.student_v3 import initialize


def observed(dev=0, dev_total=2, literal=0, literal_total=0,
             old_retention=None, baseline=None, dev_nll=1.):
    retained = old_retention or {}
    start = baseline or {
        name: {key: {"correct": item["n"], "n": item["n"]}
               for key, item in parts.items()} for name, parts in retained.items()}
    damaged = declined_prior(retained, start)
    healthy = not damaged
    return {
        "dev": {"correct": dev, "n": dev_total},
        "literal_coverage_taught_domain": {"correct": literal, "n": literal_total},
        "retention": retained,
        "retention_baseline": start,
        "declined_prior": damaged,
        "retention_healthy": healthy,
        "combined_correct": dev + literal + sum(
            part["correct"] for parts in retained.values() for part in parts.values()),
        "combined_n": dev_total + literal_total + sum(
            part["n"] for parts in retained.values() for part in parts.values()),
        "dev_nll": dev_nll,
        "dev_by_gold": {},
    }


class SplitAndInputTests(unittest.TestCase):
    def test_v05_disjoint_splits_and_literal_not_train(self):
        self.assertTrue(validate())
        self.assertEqual(STAGES, ("V00.BOOLEAN", "V01.NOT", "V02.AND"))
        self.assertEqual(DEPENDENCIES["V02.AND"], ("V00.BOOLEAN",))
        for stage in STAGES:
            pools = split(stage)
            ids = [set(r["id"] for r in pools[part])
                   for part in ("train", "dev", "gate")]
            self.assertTrue(all(ids))
            self.assertFalse(ids[0] & ids[1])
            self.assertFalse(ids[0] & ids[2])
            self.assertFalse(ids[1] & ids[2])
            self.assertEqual({r["gold"] for r in pools["train"]},
                             {"ATOM.TRUE", "ATOM.FALSE"})
        literals = {str(r["input"]["expression"]) for r
                    in literal_coverage_rows("V01.NOT")}
        self.assertEqual(literals, {"('NOT', 'TRUE')", "('NOT', 'FALSE')"})
        self.assertEqual(len(split("V01.NOT")["gate"]), 2)

    def test_roles_and_teacher_corrective_feedback_are_typed_not_prose(self):
        q = {"task": "evaluate", "expression": ("NOT", "TRUE"), "valuation": {}}
        completed = encode_completed(CompletedTurn(q, "ATOM.TRUE"))
        names = [list(IDS)[i] for i in completed]
        self.assertEqual(names[:2], ["ROLE.TEACHER", "ACT.QUESTION"])
        self.assertIn("ROLE.STUDENT", names)
        self.assertIn("FEEDBACK.INCORRECT", names)
        self.assertEqual(names[names.index("ACT.CORRECT_ANSWER") + 1], "ATOM.FALSE")
        current = encode_prompt(q, mode="none")
        self.assertEqual([list(IDS)[i] for i in current[-2:]],
                         ["ROLE.STUDENT", "ACT.ANSWER"])
        self.assertNotIn(IDS["FEEDBACK.INCORRECT"], current)

    def test_balancer_gives_both_truth_labels_and_family_floors(self):
        rng = random.Random(1)
        for stage in STAGES:
            rows = split(stage)["train"]
            sampled = sample_balanced(rng, rows, 32, {
                "variable": 4, "literal": 4, "mixed": 4})
            self.assertEqual(len(sampled), 32)
            self.assertEqual(sum(r["gold"] == "ATOM.TRUE" for r in sampled), 16)
            self.assertEqual(sum(r["gold"] == "ATOM.FALSE" for r in sampled), 16)
            for gold in ("ATOM.TRUE", "ATOM.FALSE"):
                available = {family(r) for r in rows if r["gold"] == gold}
                covered = {family(r) for r in sampled if r["gold"] == gold}
                self.assertEqual(available, covered)

    def test_source_lock_covers_new_controller_and_dependencies(self):
        root = Path(__file__).resolve().parent.parent
        required = {
            "bilqis_formal/pilot_v5.py", "bilqis_formal/controller_v5.py",
            "bilqis_formal/curriculum_v5.py", "bilqis_formal/pilot_v4.py",
            "bilqis_formal/pilot_v3.py", "bilqis_formal/course_v3.py",
            "bilqis_ref/model.py", "bilqis_ref/codec.py",
            "bilqis_ref/semantics.py", "tests/test_formal_adaptive_v5.py",
            "docs/formal/ADAPTIVE_V05_PROTOCOL.md",
        }
        self.assertTrue(required <= set(SOURCE_FILES))
        self.assertTrue(all((root / file).is_file() for file in SOURCE_FILES))
        self.assertEqual(len(source_sha256()), 64)


class ControllerDecisionTests(unittest.TestCase):
    def setUp(self):
        self.b = Budget(block=2, baseline=4, adaptive_cap=12,
                        repair_cap=4, patience=3, stable_checks=2)
        self.assertTrue(self.b.validate())

    def decide(self, *, arm="adaptive", updates=4, now=None,
               before=(), repair=0):
        return decide_after_block(
            arm=arm, updates=updates, observed=now or observed(),
            previous_observations=list(before),
            repair_updates=repair, budget=self.b)

    def test_fixed_never_peeks_to_change_320_budget(self):
        unhealthy = observed(old_retention={"V00.BOOLEAN": {
            "dev": {"correct": 0, "n": 2}}})
        self.assertEqual(self.decide(arm="fixed320", updates=2,
                                     now=unhealthy), "CONTINUE_CURRENT")
        self.assertEqual(self.decide(arm="fixed320", updates=4,
                                     now=unhealthy), "FINISH_FIXED")
        self.assertEqual(self.decide(arm="fixed1280", updates=4,
                                     now=unhealthy), "CONTINUE_CURRENT")
        self.assertEqual(self.decide(arm="fixed1280", updates=12,
                                     now=unhealthy), "FINISH_FIXED")

    def test_longer_training_when_improving(self):
        weak = observed(dev=0)
        growing = observed(dev=1)
        self.assertEqual(self.decide(now=growing, before=[weak]), "CONTINUE_CURRENT")
        self.assertEqual(self.decide(updates=6, now=growing, before=[
            weak, growing]), "CONTINUE_CURRENT")

    def test_stability_plateau_and_hard_cap(self):
        good = observed(dev=2)
        bad = observed(dev=0)
        self.assertTrue(formative_mastered(good))
        self.assertEqual(self.decide(now=good, before=[good]), "FINISH_STABLE")
        self.assertEqual(self.decide(updates=8, now=bad,
                                     before=[bad, bad, bad]), "FINISH_PLATEAU")
        self.assertEqual(self.decide(updates=12, now=bad), "FINISH_CAP")

    def test_recovering_accuracy_or_increasing_probability_is_not_plateau(self):
        recovery = [observed(dev=i, dev_total=4) for i in (4, 1, 2, 3)]
        self.assertEqual(self.decide(updates=8, now=recovery[-1],
                                     before=recovery[:-1]), "CONTINUE_CURRENT")
        improving_confidence = [observed(dev=1, dev_nll=x)
                                for x in (0.9, 0.8, 0.7, 0.6)]
        self.assertEqual(self.decide(updates=8, now=improving_confidence[-1],
                                     before=improving_confidence[:-1]),
                         "CONTINUE_CURRENT")
        stuck = [observed(dev=1, dev_nll=0.9) for _ in range(4)]
        self.assertEqual(self.decide(updates=8, now=stuck[-1],
                                     before=stuck[:-1]), "FINISH_PLATEAU")

    def test_retention_loss_gets_four_step_repair_and_then_rollback(self):
        broken = observed(dev=2, old_retention={
            "V00.BOOLEAN": {"dev": {"correct": 0, "n": 2},
                            "literal_coverage": {"correct": 2, "n": 2}}})
        self.assertEqual(weakest_retained(broken), "V00.BOOLEAN")
        self.assertEqual(self.decide(now=broken), "REPAIR_PRIOR")
        self.assertEqual(self.decide(now=broken, repair=4), "ROLLBACK_EXHAUSTED")
        self.assertEqual(self.decide(now=observed(dev=2)), "CONTINUE_CURRENT")

    def test_preexisting_imperfect_dev_is_not_falsely_called_forgetting(self):
        prior = {"V00.BOOLEAN": {
            "dev": {"correct": 1, "n": 2},
            "literal_coverage": {"correct": 2, "n": 2}}}
        stable = observed(dev=2, old_retention=prior, baseline=prior)
        self.assertTrue(stable["retention_healthy"])
        self.assertEqual(stable["declined_prior"], [])
        self.assertEqual(self.decide(now=stable, before=[stable]), "FINISH_STABLE")

    def test_correct_to_wrong_swap_is_detected_despite_equal_total(self):
        start = {"V00.BOOLEAN": {
            "dev": {"correct": 1, "n": 2},
            "literal_coverage": {"correct": 2, "n": 2},
            "dev_items": {"a": True, "b": False},
            "literal_items": {"t": True, "f": True}}}
        after = {"V00.BOOLEAN": {
            "dev": {"correct": 1, "n": 2},
            "literal_coverage": {"correct": 2, "n": 2},
            "dev_items": {"a": False, "b": True},
            "literal_items": {"t": True, "f": True}}}
        self.assertEqual(declined_prior(after, start), ["V00.BOOLEAN"])

    def test_no_gate_score_is_an_input_to_decision(self):
        answer = observed(dev=2, literal=2, literal_total=2)
        self.assertEqual(self.decide(now=answer, before=[answer]), "FINISH_STABLE")
        self.assertFalse("sealed" in answer or "gate" in answer)

    def test_adaptive_repair_exhaustion_restores_model_and_optimizer(self):
        model, _ = initialize(seed=71)
        opt = torch.optim.AdamW(model.parameters(), lr=.002)
        from bilqis_ref.model import state_hash
        # Populate real AdamW moments before the controlled mutation.
        opt.zero_grad(set_to_none=True)
        model.embedding.weight[1].square().sum().backward()
        opt.step()
        original = state_hash(model)
        original_optimizer = optimizer_digest(opt.state_dict())
        original_rng = torch.get_rng_state().clone()
        tiny = Budget(block=2, baseline=4, adaptive_cap=12, repair_cap=4,
                      patience=3, stable_checks=2)
        broken = observed(dev=0, old_retention={
            "V00.BOOLEAN": {"dev": {"correct": 0, "n": 2},
                            "literal_coverage": {"correct": 2, "n": 2}}})
        broken["dev_prediction"] = []
        def fake_train(*args, **kwargs):
            # Mutate weights, initialized AdamW moments, and randomness.
            with torch.no_grad():
                model.embedding.weight[1].add_(0.5)
                next(iter(opt.state.values()))["exp_avg"].add_(0.5)
                torch.rand(1)
            return {"step_count": 2, "context_exposures": 0}
        with patch("bilqis_formal.controller_v5.train_block", side_effect=fake_train), (
                patch("bilqis_formal.controller_v5.prior_formative",
                      return_value=broken["retention_baseline"])), (
                patch("bilqis_formal.controller_v5.inspect_progress",
                      return_value=broken)), (
                patch("bilqis_formal.controller_v5.accuracy",
                      side_effect=AssertionError("SEALED_GATE_EARLY"))):
            receipt = run_stage(model, opt, stage="V01.NOT",
                                accepted=["V00.BOOLEAN"], seed=71,
                                arm="adaptive", budget=tiny)
        self.assertTrue(receipt["rolled_back"])
        self.assertEqual(receipt["decision"], "ROLLBACK_EXHAUSTED")
        self.assertEqual(receipt["committed_updates"], 0)
        self.assertEqual(receipt["attempted_updates"], 6)
        self.assertEqual(state_hash(model), original)
        self.assertEqual(optimizer_digest(opt.state_dict()), original_optimizer)
        self.assertTrue(torch.equal(torch.get_rng_state(), original_rng))
        self.assertIsNone(receipt["sealed_gate"])


class ReadbackTests(unittest.TestCase):
    def test_preflight_wrong_path_never_writes_to_existing_directory(self):
        with tempfile.TemporaryDirectory() as dirname:
            wrong = Path(dirname)
            file = wrong / "historical-evidence"
            file.write_text("immutable")
            with self.assertRaisesRegex(ValueError, "WRONG_PREREGISTERED_OUTPUT"):
                run(wrong)
            self.assertEqual(file.read_text(), "immutable")
            self.assertFalse((wrong / "aborted.json").exists())

    def test_tiny_three_arm_epoch_replay_and_forged_gate_failure(self):
        tiny = Budget(block=2, baseline=4, adaptive_cap=8,
                      repair_cap=4, patience=2, stable_checks=2)
        with tempfile.TemporaryDirectory() as dirname, (
                patch("bilqis_formal.pilot_v5.SEEDS", (99,))), (
                patch("bilqis_formal.pilot_v5.BUDGET", tiny)), (
                patch("bilqis_formal.pilot_v5.attest_git_source", return_value=True)):
            root = Path(dirname)
            prereg = {"version": VERSION, "source_sha256": source_sha256(),
                      "source_commit": "0" * 40, "seeds": [99],
                      "arms": list(ARMS), "atomic_stages": list(STAGES),
                      "budget": vars(tiny),
                      "training_splits": {
                          stage: {k: [r["id"] for r in value]
                                  for k, value in split(stage).items()}
                          for stage in STAGES}}
            (root / "preregistration.json").write_text(json.dumps(prereg))
            reports = [run_arm(root / f"seed-99-{arm}", seed=99, arm=arm,
                               locked_source=prereg["source_sha256"]) for arm in ARMS]
            (root / "comparison.json").write_text(json.dumps({
                "version": VERSION, "preregistration": prereg, "reports": reports}))
            self.assertEqual(replay(root)["status"], "V05_CHECKPOINTS_VERIFIED")
            first_stage = root / "seed-99-fixed320" / "stage-01.json"
            original = json.loads(first_stage.read_text())
            if original["sealed_gate"]:
                original["sealed_gate"]["correct"] = -1
                first_stage.write_text(json.dumps(original))
                with self.assertRaisesRegex(
                        ValueError, "V05_STAGE_IDENTITY_MISMATCH|V05_GATE_REPLAY_MISMATCH"):
                    replay(root)
            # Test custody and optimizer-moment tampering separately against
            # the same genuine saved epoch, restoring each artifact in between.
            original["sealed_gate"]["correct"] = reports[0]["summaries"][0]["sealed"]["correct"]
            first_stage.write_text(json.dumps(original))
            block_file = root / "seed-99-fixed320" / "stage-01-block-01.pt"
            stage_file = root / "seed-99-fixed320" / "stage-01.pt"
            stage_1 = json.loads(first_stage.read_text())
            stage_1["blocks"][0]["sample_sha256"] = "f" * 64
            first_stage.write_text(json.dumps(stage_1))
            with self.assertRaisesRegex(ValueError, "V05_TRAINING_SAMPLE_LEDGER_DRIFT"):
                replay(root)
            first_stage.write_text(json.dumps(original))
            snap = torch.load(stage_file, weights_only=True)
            state = next(s for s in snap["optimizer"]["state"].values()
                         if "exp_avg" in s)
            state["exp_avg"].add_(1)
            torch.save(snap, stage_file)
            with self.assertRaisesRegex(ValueError, "V05_OPTIMIZER_STATE_DIGEST_MISMATCH"):
                replay(root)


if __name__ == "__main__":
    unittest.main()
