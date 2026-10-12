"""Behavior-level regressions for the teacher-first v0.3 formal curriculum."""
from __future__ import annotations

from dataclasses import replace
import json
from pathlib import Path
import tempfile
import unittest

import torch

from bilqis_formal.course_v2 import mandatory_train as old_train
from bilqis_formal.course_v3 import (
    STAGE, STAGES, fixed_gate, mandatory_train, missing_prerequisites,
    panels, structural_transfer_probe, validate_course,
    validate_panels)
from bilqis_formal.dialogue import question_prompt
from bilqis_formal.dialogue_v3 import (
    IDS, TOKENS_V3, CompletedTurn, answer_domain, counterfactual_feedback_prompt,
    encode_completed, encode_prompt, gold_label, paired_valid_primers, verify_protocol)
from bilqis_formal.kev_v3 import choose, selected_panel
from bilqis_formal.pilot_v3 import (
    ARMS, DEFAULT_SEEDS, diagnostic_probe, evaluate_gate, replay, run, run_arm,
    score, source_sha256, train_steps)
from bilqis_formal.student_v3 import (
    initialize, inputs_for, load_checkpoint, predict, typed_logits)


class TeacherStudentIdentityTests(unittest.TestCase):
    def test_teachers_can_grade_from_day_one_without_early_student_grading(self):
        self.assertTrue(verify_protocol())
        self.assertEqual(len(TOKENS_V3), 46)
        self.assertNotEqual(IDS["FEEDBACK.CORRECT"], IDS["JUDGMENT.CORRECT"])
        self.assertNotEqual(IDS["FEEDBACK.INCORRECT"], IDS["JUDGMENT.INCORRECT"])
        self.assertEqual({r["input"]["task"] for r in old_train("D00.PROTOCOL")},
                         {"evaluate", "judge_answer"})  # Exact old conflation.
        for stage in STAGES[:-1]:
            self.assertEqual(stage.student_task, "evaluate")
            self.assertEqual({r["input"]["task"] for r in mandatory_train(stage.id)},
                             {"evaluate"})
            self.assertEqual({r["gold"] for r in mandatory_train(stage.id)},
                             {"ATOM.TRUE", "ATOM.FALSE"})
        self.assertEqual(STAGES[-1].student_task, "judge_answer")
        self.assertEqual({r["input"]["task"] for r in mandatory_train(STAGES[-1].id)},
                         {"judge_answer"})
        self.assertEqual({r["gold"] for r in mandatory_train(STAGES[-1].id)},
                         {"JUDGMENT.CORRECT", "JUDGMENT.INCORRECT"})

    def test_correctness_judgment_is_independent_boolean_semantics(self):
        gold = {}
        for truth in (False, True):
            for claim in (False, True):
                case = {"task": "judge_answer", "expression": "TRUE" if truth else "FALSE",
                        "valuation": {}, "proposed_answer": claim}
                gold[(truth, claim)] = gold_label(case)
        self.assertEqual(gold, {
            (False, False): "JUDGMENT.CORRECT",
            (False, True): "JUDGMENT.INCORRECT",
            (True, False): "JUDGMENT.INCORRECT",
            (True, True): "JUDGMENT.CORRECT",
        })
        self.assertEqual(gold_label({"task": "evaluate", "expression": "FALSE",
                                     "valuation": {}}), "ATOM.FALSE")

    def test_wrong_early_student_answer_invokes_teacher_not_student_judgment(self):
        item = {"task": "evaluate", "expression": "FALSE", "valuation": {}}
        turn = CompletedTurn(item, "ATOM.TRUE")
        seq = encode_completed(turn)
        self.assertIn(IDS["FEEDBACK.INCORRECT"], seq)
        self.assertIn(IDS["ACT.CORRECT_ANSWER"], seq)
        self.assertIn(IDS["ATOM.FALSE"], seq)
        self.assertNotIn(IDS["JUDGMENT.CORRECT"], seq)
        self.assertNotIn(IDS["JUDGMENT.INCORRECT"], seq)
        good = encode_completed(CompletedTurn(item, "ATOM.FALSE"))
        self.assertIn(IDS["FEEDBACK.CORRECT"], good)
        self.assertNotIn(IDS["ACT.CORRECT_ANSWER"], good)

    def test_history_uses_previous_corrected_turn_not_current_answer(self):
        previous = {"task": "evaluate", "expression": "TRUE", "valuation": {}}
        current = {"task": "evaluate", "expression": "FALSE", "valuation": {}}
        last = CompletedTurn(previous, "ATOM.FALSE")
        sequence = encode_prompt(current, [last])
        expected_tail = question_prompt(current)
        self.assertEqual(sequence[-len(expected_tail):], expected_tail)
        self.assertEqual(sequence[-1], IDS["ACT.ANSWER"])
        self.assertIn(IDS["ACT.CORRECT_ANSWER"], sequence)
        self.assertEqual(encode_prompt(current, [CompletedTurn(current, "ATOM.TRUE")]),
                         expected_tail)  # A prior answer to current question is forbidden.
        self.assertEqual(encode_prompt(current, [last], context=len(expected_tail)),
                         expected_tail)  # Never take half a prior exchange.


class CurriculumTests(unittest.TestCase):
    def test_independent_not_and_paths_and_separate_downstream_judgment(self):
        self.assertTrue(validate_course())
        self.assertEqual(STAGE["V01.NOT"].prerequisite, ("V00.BOOLEAN",))
        self.assertEqual(STAGE["V02.AND"].prerequisite, ("V00.BOOLEAN",))
        self.assertEqual(set(STAGE["V03.AND_NOT_RIGHT"].prerequisite),
                         {"V01.NOT", "V02.AND"})
        self.assertEqual(set(STAGE["J00.PROPOSED_ANSWER"].prerequisite),
                         {s.id for s in STAGES[:-1]})
        self.assertEqual(missing_prerequisites("V02.AND", {"V00.BOOLEAN"}), ())
        self.assertEqual(missing_prerequisites("V03.AND_NOT_RIGHT", {"V00.BOOLEAN", "V02.AND"}),
                         ("V01.NOT",))
        self.assertIn("V01.NOT", missing_prerequisites("J00.PROPOSED_ANSWER", {"V00.BOOLEAN"}))

    def test_no_training_formative_or_lesson_item_leaks_sealed_gate(self):
        for s in STAGES:
            groups = [
                {r["id"] for r in mandatory_train(s.id)},
                {r["id"] for p in panels(s.id, "lesson") for r in p.rows},
                {r["id"] for p in panels(s.id, "exam") for r in p.rows},
                {r["id"] for r in fixed_gate(s.id)},
                {r["id"] for r in structural_transfer_probe(s.id)},
            ]
            for i in range(len(groups)):
                for j in range(i + 1, len(groups)):
                    self.assertFalse(groups[i] & groups[j], (s.id, i, j))
            for item in fixed_gate(s.id):
                self.assertEqual(item["gold"], gold_label(item["input"]))
                self.assertIn(item["gold"], answer_domain(item["input"]))
            for item in structural_transfer_probe(s.id):
                self.assertEqual(item["gold"], gold_label(item["input"]))

    def test_later_grading_exam_covers_all_previously_taught_operator_shapes(self):
        def shapes(rows):
            from bilqis_formal.course_v3 import shape
            return {shape(r["input"]["expression"]) for r in rows}
        needed = {"v", "NOT(v)", "AND(v,v)",
                  "AND(v,NOT(v))", "AND(NOT(v),v)", "NOT(AND(v,v))"}
        self.assertEqual(shapes(mandatory_train("J00.PROPOSED_ANSWER")), needed)
        self.assertEqual(shapes(fixed_gate("J00.PROPOSED_ANSWER")), needed)
        self.assertEqual({r["input"]["task"] for r in fixed_gate("J00.PROPOSED_ANSWER")},
                         {"judge_answer"})

    def test_post_gate_structural_transfer_is_real_and_never_training(self):
        from bilqis_formal.course_v3 import shape
        for stage in ("V02.AND", "V03.AND_NOT_RIGHT", "V04.AND_NOT_LEFT",
                      "V05.NOT_AND", "J00.PROPOSED_ANSWER"):
            probes = structural_transfer_probe(stage)
            self.assertGreaterEqual(len(probes), 4)
            old_shapes = {shape(r["input"]["expression"]) for r in mandatory_train(stage)}
            new_shapes = {shape(r["input"]["expression"]) for r in probes}
            self.assertTrue(new_shapes - old_shapes, stage)
            self.assertEqual({r["role"] for r in probes}, {"structural_diagnostic"})

    def test_kev_panels_never_offer_grading_before_grading_stage(self):
        for stage in ("V03.AND_NOT_RIGHT", "V04.AND_NOT_LEFT", "V05.NOT_AND"):
            for role in ("lesson", "exam"):
                offered = panels(stage, role)
                self.assertTrue(validate_panels(stage, role, offered))
                self.assertEqual(len(offered), 2)
                self.assertEqual(len({x.structure for x in offered}), 1)
                for p in offered:
                    self.assertEqual({x["gold"] for x in p.rows},
                                     {"ATOM.TRUE", "ATOM.FALSE"})
                    self.assertEqual({x["input"]["task"] for x in p.rows},
                                     {"evaluate"})
        p = panels("V03.AND_NOT_RIGHT", "lesson")
        with self.assertRaisesRegex(ValueError, "MIXED_PANEL"):
            validate_panels("V03.AND_NOT_RIGHT", "lesson",
                            (p[0], replace(p[1], tier="easy")))
        original, sibling = p[0].rows
        forged = {**original, "gold": sibling["gold"]}
        forged_other = {**sibling, "gold": original["gold"]}
        with self.assertRaisesRegex(ValueError, "WRONG_PANEL_COMPETENCY"):
            validate_panels("V03.AND_NOT_RIGHT", "lesson",
                            (replace(p[0], rows=(forged, forged_other)), p[1]))


class StubTeacher:
    def __init__(self, position_biased=False):
        self.position_biased = position_biased
        self.orders = []

    def score(self, state, instructions, candidates, binding=None):
        self.orders.append([c["candidate_id"] for c in candidates])
        choices = self.orders[-1]
        choice = choices[0] if self.position_biased else sorted(choices)[0]
        probabilities = {candidate: (.9 if candidate == choice else .1)
                         for candidate in choices}
        return {"status": "OK", "choice": choice, "probabilities": probabilities,
                "margin": .8, "choice_calls": 1}


class KevTests(unittest.TestCase):
    def test_same_decision_rotated_or_abstain_on_position_effect(self):
        offered = panels("V03.AND_NOT_RIGHT", "lesson")
        teacher = StubTeacher()
        result = choose("V03.AND_NOT_RIGHT", "lesson", offered, teacher=teacher)
        self.assertEqual(result["status"], "SELECTED")
        self.assertIsNotNone(selected_panel(offered, result))
        self.assertNotEqual(teacher.orders[0], teacher.orders[1])
        unstable = choose("V03.AND_NOT_RIGHT", "lesson", offered,
                          teacher=StubTeacher(position_biased=True))
        self.assertEqual(unstable["status"], "ORDER_UNSTABLE")


class CausalProbeTests(unittest.TestCase):
    def test_valid_opposite_label_feedback_turns_have_equal_length_no_gate_lookup(self):
        for s in STAGES:
            train = mandatory_train(s.id)
            a, b = paired_valid_primers(train)
            self.assertNotEqual(a.record, b.record)
            self.assertNotEqual(gold_label(a.record), gold_label(b.record))
            self.assertNotEqual(a.student_answer, gold_label(a.record))
            self.assertNotEqual(b.student_answer, gold_label(b.record))
            self.assertEqual(len(encode_completed(a)), len(encode_completed(b)))
            self.assertIn(IDS["ACT.CORRECT_ANSWER"], encode_completed(a))
            self.assertNotIn(a.record, [x["input"] for x in fixed_gate(s.id)])
            self.assertNotIn(b.record, [x["input"] for x in fixed_gate(s.id)])

    def test_corrupted_teacher_feedback_flips_one_past_token_only(self):
        for s in STAGES:
            prior, other = paired_valid_primers(mandatory_train(s.id))
            now = fixed_gate(s.id)[0]["input"]
            correct, invalid = counterfactual_feedback_prompt(now, prior)
            self.assertEqual(len(correct), len(invalid))
            self.assertEqual(sum(a != b for a, b in zip(correct, invalid)), 1)
            suffix = question_prompt(now)
            self.assertEqual(correct[-len(suffix):], invalid[-len(suffix):])
            self.assertEqual(correct[-1], IDS["ACT.ANSWER"])
            self.assertNotIn(IDS["ACT.CORRECT_ANSWER"], suffix)
            neutral = encode_prompt(now, [prior], mode="answer_only_padded")
            self.assertEqual(len(neutral), len(correct))
            self.assertNotIn(IDS["ACT.CORRECT_ANSWER"], neutral)
            right = CompletedTurn(prior.record, gold_label(prior.record))
            self.assertEqual(len(encode_completed(right)), len(encode_completed(prior)))
            self.assertEqual(
                len(encode_prompt(now, [right], mode="answer_only_padded")),
                len(encode_prompt(now, [prior], mode="answer_only_padded")))

    def test_frozen_model_probe_does_not_change_weights(self):
        model, _ = initialize(seed=9)
        before = {name: tensor.detach().clone() for name, tensor in model.state_dict().items()}
        report = diagnostic_probe(model, "V00.BOOLEAN")
        self.assertEqual(report["n"], 4)
        self.assertEqual(set(report["scores"]), {
            "valid_a", "valid_b", "counterfactual_invalid_feedback",
            "answer_only_length_matched", "no_history"})
        self.assertTrue(report["all_feedback_probes_have_equal_length"])
        self.assertTrue(report["invalid_feedback_is_diagnostic_only"])
        for name, tensor in model.state_dict().items():
            self.assertTrue(torch.equal(before[name], tensor), name)


class StudentAndRunnerTests(unittest.TestCase):
    def test_early_model_logits_are_restricted_to_truth_domain(self):
        model, init = initialize(seed=7)
        rows = mandatory_train("V00.BOOLEAN")
        result = predict(model, rows)
        self.assertEqual(len(result), len(rows))
        self.assertTrue(all(p["prediction"].startswith("ATOM.") for p in result))
        (ids, lengths), _ = inputs_for(model, rows)
        masked = typed_logits(model(ids, lengths), rows)
        self.assertTrue(torch.all(masked[:, 2:] < -1e8))
        self.assertFalse(init["pretrained_weights"])

    def test_all_arms_use_identical_question_sampler_and_no_hidden_promotion(self):
        with tempfile.TemporaryDirectory() as dirname:
            root = Path(dirname)
            shared = None
            results = {}
            for arm in ARMS:
                report, plan = run_arm(
                    root / arm, arm=arm, seed=23, steps=2, remedy_steps=0,
                    max_stages=1, locked_source=source_sha256(), shared_choices=shared)
                if shared is None:
                    shared = plan
                results[arm] = report
                self.assertEqual(report["attempted"], 1)
                self.assertEqual(report["optimizer_updates"], 2)
                if not report["briefs"][0]["promoted"]:
                    self.assertNotIn("V01.NOT", report["promoted"])
                saved = json.loads((root / arm / "stage-01.json").read_text())
                self.assertEqual(saved["task"], "evaluate")
                self.assertIn("standalone", saved["gate"])
                self.assertIn("contextual", saved["gate"])
                self.assertEqual(len(saved["gate"]["primer"]), 2)
                teacher_turns = [
                    encode_completed(CompletedTurn(t["input"], t["student"]))
                    for t in saved["gate"]["primer"]]
                self.assertIn(IDS["FEEDBACK.CORRECT"], teacher_turns[0])
                self.assertIn(IDS["FEEDBACK.INCORRECT"], teacher_turns[1])
                self.assertIn(IDS["ACT.CORRECT_ANSWER"], teacher_turns[1])
                model, snapshot = load_checkpoint(root / arm / "stage-01.pt")
                self.assertEqual(snapshot["stage"], "V00.BOOLEAN")
                self.assertEqual(score(predict(model, fixed_gate("V00.BOOLEAN")))["correct"],
                                 saved["gate"]["standalone"]["correct"])
            sample_hashes = {
                r["briefs"][0]["training_sha256"] for r in results.values()}
            self.assertEqual(len(sample_hashes), 1)
            self.assertEqual(
                json.loads((root / "no_history" / "stage-01.json").read_text())["train"]["context_exposures"],
                0)

    def test_experiment_refuses_seed_or_budget_shopping(self):
        with tempfile.TemporaryDirectory() as dirname:
            out = Path(dirname) / "e6"
            with self.assertRaisesRegex(ValueError, "PREREGISTRATION_DRIFT"):
                run(out, seeds=(401,), steps=320)
            self.assertFalse(out.exists())
            with self.assertRaisesRegex(ValueError, "PREREGISTRATION_DRIFT"):
                run(out, seeds=DEFAULT_SEEDS, steps=321)
            self.assertFalse(out.exists())
            with self.assertRaisesRegex(ValueError, "PREREGISTERED_OUTPUT_PATH"):
                run(out, seeds=DEFAULT_SEEDS, steps=320)
            self.assertFalse(out.exists())

    def test_replay_rejects_source_or_protocol_hash_mismatch(self):
        with tempfile.TemporaryDirectory() as dirname:
            out = Path(dirname)
            (out / "preregistration.json").write_text(json.dumps({
                "version": "bilqis.formal.pilot/v0.3.0",
                "source_sha256": "0" * 64, "seeds": list(DEFAULT_SEEDS)}))
            with self.assertRaisesRegex(ValueError, "SOURCE_OR_PROTOCOL_REPLAY_MISMATCH"):
                replay(out)
            (out / "preregistration.json").write_text(json.dumps({
                "version": "bilqis.formal.pilot/v0.3.0",
                "source_sha256": source_sha256(), "seeds": list(DEFAULT_SEEDS),
                "arms": list(ARMS)}))
            with self.assertRaisesRegex(ValueError, "INCOMPLETE_EXPERIMENT_NO_AGGREGATE_RECEIPT"):
                replay(out)


if __name__ == "__main__":
    unittest.main()
