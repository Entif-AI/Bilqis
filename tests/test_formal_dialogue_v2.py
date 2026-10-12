"""Observable dialogue/teacher/assessment contracts; no real Kev calls."""
from __future__ import annotations

from dataclasses import replace
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import torch

from bilqis_formal.course_v2 import (STAGE, STAGES, _expr, fixed_gate, mandatory_train,
                                    panels, validate_course, validate_panels)
from bilqis_formal.dialogue import (IDS, CompletedTurn, TOKENS_V2, encode_completed,
                                   encode_prompt, gold_label, question_prompt,
                                   verify_protocol)
from bilqis_formal.kev_v2 import choose, error_witnesses, selected_panel
from bilqis_formal.pilot_v2 import (formative, replay, run_arm, score,
                                   standard_primer, train_steps)
from bilqis_formal.student_v2 import (initialize, inputs_for, load_checkpoint, predict,
                                      save_checkpoint, typed_logits)


class ProtocolTests(unittest.TestCase):
    def test_truth_values_and_teacher_judgments_are_separate(self):
        self.assertTrue(verify_protocol())
        self.assertNotEqual(IDS["ATOM.FALSE"], IDS["FEEDBACK.INCORRECT"])
        self.assertNotEqual(IDS["ATOM.TRUE"], IDS["FEEDBACK.CORRECT"])
        observed = {}
        for truth in (False, True):
            for answer in (False, True):
                row = {"task": "judge_answer", "expression": "TRUE" if truth else "FALSE",
                       "valuation": {}, "proposed_answer": answer}
                observed[(truth, answer)] = gold_label(row)
        self.assertEqual(observed, {
            (False, False): "FEEDBACK.CORRECT",
            (False, True): "FEEDBACK.INCORRECT",
            (True, False): "FEEDBACK.INCORRECT",
            (True, True): "FEEDBACK.CORRECT",
        })

    def test_completed_wrong_answer_has_distinct_feedback_and_correction(self):
        q = {"task": "evaluate", "expression": "FALSE", "valuation": {}}
        wrong = encode_completed(CompletedTurn(q, "ATOM.TRUE"))
        right = encode_completed(CompletedTurn(q, "ATOM.FALSE"))
        self.assertIn(IDS["FEEDBACK.INCORRECT"], wrong)
        self.assertIn(IDS["ACT.CORRECT_ANSWER"], wrong)
        self.assertIn(IDS["ATOM.FALSE"], wrong)
        self.assertIn(IDS["FEEDBACK.CORRECT"], right)
        self.assertNotIn(IDS["ACT.CORRECT_ANSWER"], right)
        self.assertEqual(right[-1], IDS["ACT.TURN_END"])

    def test_history_is_in_attention_but_current_gold_and_correction_are_hidden(self):
        previous = {"task": "evaluate", "expression": "TRUE", "valuation": {}}
        current = {"task": "evaluate", "expression": "FALSE", "valuation": {}}
        completed = CompletedTurn(previous, "ATOM.FALSE")  # mistaken, teacher corrects
        prompt = encode_prompt(current, [completed], context=96)
        self.assertTrue(prompt[:2] == [IDS["ROLE.TEACHER"], IDS["ACT.QUESTION"]])
        self.assertIn(IDS["FEEDBACK.INCORRECT"], prompt)
        self.assertIn(IDS["ACT.CORRECT_ANSWER"], prompt)
        self.assertEqual(prompt[-len(question_prompt(current)):], question_prompt(current))
        self.assertEqual(prompt[-1], IDS["ACT.ANSWER"])
        self.assertEqual(encode_prompt(current, [CompletedTurn(current, "ATOM.TRUE")]),
                         question_prompt(current))  # exact current-question answer cannot leak
        self.assertEqual(encode_prompt(current, [completed], context=len(question_prompt(current))),
                         question_prompt(current))  # no half-turn truncation
        answer_only = encode_prompt(current, [completed], history_mode="answer_only")
        self.assertGreater(len(answer_only), len(question_prompt(current)))
        self.assertNotIn(IDS["ACT.FEEDBACK"], answer_only)
        self.assertNotIn(IDS["ACT.CORRECT_ANSWER"], answer_only)
        self.assertEqual(encode_prompt(current, [completed], history_mode="none"),
                         question_prompt(current))


class CourseTests(unittest.TestCase):
    def test_foundations_are_prerequisite_nodes_not_one_arbitrary_chain(self):
        self.assertTrue(validate_course())
        self.assertEqual(STAGE["D02.AND"].prerequisite, ("D00.PROTOCOL",))
        self.assertEqual(set(STAGE["D03.AND_NOT_RIGHT"].prerequisite),
                         {"D01.NOT", "D02.AND"})
        self.assertEqual(STAGE["D05.NOT_AND"].tier, "hard")

    def test_all_candidate_exams_and_gate_are_disjoint_from_training(self):
        for stage in STAGES:
            training = {r["id"] for r in mandatory_train(stage.id)}
            training.update(r["id"] for p in panels(stage.id, "lesson") for r in p.rows)
            exams = {r["id"] for p in panels(stage.id, "exam") for r in p.rows}
            gates = {r["id"] for r in fixed_gate(stage.id)}
            self.assertFalse(training & exams)
            self.assertFalse(training & gates)
            self.assertFalse(exams & gates)
            self.assertTrue(all(r["gold"] == gold_label(r["input"]) for r in fixed_gate(stage.id)))

    def test_kev_near_neighbors_are_same_tier_shape_and_balanced(self):
        for stage in ("D03.AND_NOT_RIGHT", "D04.AND_NOT_LEFT", "D05.NOT_AND"):
            for role in ("lesson", "exam"):
                p = panels(stage, role)
                self.assertTrue(validate_panels(stage, role, p))
                self.assertEqual(len(p), 2)
                self.assertEqual(len({x.structure for x in p}), 1)
                self.assertEqual({x.axis for x in p},
                                 set(p[0].rows[0]["input"]["valuation"]))
                for panel in p:
                    evaluation = [r for r in panel.rows if r["input"]["task"] == "evaluate"]
                    self.assertEqual({r["gold"] for r in evaluation},
                                     {"ATOM.TRUE", "ATOM.FALSE"})
                    a, b = (r["input"]["valuation"] for r in evaluation)
                    self.assertEqual(sum(a[n] != b[n] for n in a), 1)
                    self.assertNotEqual(a[panel.axis], b[panel.axis])
        candidates = panels("D03.AND_NOT_RIGHT", "lesson")
        mixed = (candidates[0], replace(candidates[1], tier="easy"))
        with self.assertRaisesRegex(ValueError, "UNCOMPARABLE_PANEL"):
            validate_panels("D03.AND_NOT_RIGHT", "lesson", mixed)


class StubKev:
    def __init__(self, behavior):
        self.behavior = behavior
        self.orders = []
        self.prompts = []

    def score(self, state, question, candidates, binding=None):
        self.prompts.append((state, question))
        order = [x["candidate_id"] for x in candidates]
        self.orders.append(order)
        choice = order[0] if self.behavior == "position" else sorted(order)[0]
        probabilities = {i: .1 for i in order}
        probabilities[choice] = .9
        return {"status": "OK", "choice": choice, "probabilities": probabilities,
                "margin": .8, "choice_calls": 1}


class TeacherTests(unittest.TestCase):
    def test_kev_can_choose_only_within_matched_diagnostic_band(self):
        options = panels("D03.AND_NOT_RIGHT", "lesson")
        stub = StubKev("stable")
        result = choose("D03.AND_NOT_RIGHT", "lesson", options, teacher=stub,
                        anchors={"D02.AND": {"correct": 12, "n": 12}},
                        recent_predictions=[{"task": "evaluate", "input": {
                            "task": "evaluate", "expression": _expr(
                                "D03.AND_NOT_RIGHT", ("P", "Q")),
                            "valuation": {"P": True, "Q": False}},
                            "gold": "ATOM.TRUE", "prediction": "ATOM.FALSE", "prob_gold": .03}])
        self.assertEqual(result["status"], "SELECTED")
        self.assertIsNotNone(selected_panel(options, result))
        self.assertEqual(len({tuple(row) for row in stub.orders}), 2)
        self.assertIn("observed", stub.prompts[0][0])
        self.assertIn("COMP.AND.NOT_RIGHT", stub.prompts[0][0])
        self.assertIn("12", stub.prompts[0][0])
        self.assertIn("identical AST shape", stub.prompts[0][0])
        self.assertEqual(choose("D03.AND_NOT_RIGHT", "lesson", options,
                                teacher=StubKev("position"))["status"], "ORDER_UNSTABLE")


class NeuralLoopTests(unittest.TestCase):
    def test_standard_teacher_demonstration_contains_true_correction_without_gate_leak(self):
        primer = standard_primer("D00.PROTOCOL")
        self.assertEqual(len(primer), 2)
        self.assertEqual(primer[0].student_answer, gold_label(primer[0].record))
        self.assertNotEqual(primer[1].student_answer, gold_label(primer[1].record))
        self.assertIn(IDS["ACT.CORRECT_ANSWER"], encode_completed(primer[1]))
        gate = fixed_gate("D00.PROTOCOL")
        self.assertTrue(all(x["input"] not in [t.record for t in primer] for x in gate))

    def test_typed_answers_never_cross_truth_and_feedback_domains(self):
        model, _ = initialize(seed=4)
        rows = mandatory_train("D00.PROTOCOL")
        preds = predict(model, rows)
        self.assertEqual(len(preds), len(rows))
        for r in preds:
            self.assertEqual(r["prediction"].startswith("ATOM."),
                             r["task"] == "evaluate")
        self.assertEqual(tuple(model(*inputs_for(model, rows)[0]).shape), (len(rows), 4))

    def test_actual_student_predictions_generate_prior_turn_feedback(self):
        model, _ = initialize(seed=11)
        rows = mandatory_train("D00.PROTOCOL")
        optimizer = torch.optim.AdamW(model.parameters(), lr=.002)
        baseline = train_steps(model, optimizer, rows, [], steps=3, seed=37, use_feedback=True)
        self.assertEqual(baseline["exposures"], 96)
        self.assertGreater(baseline["history_bearing_exposures"], 0)
        self.assertEqual(baseline["pre_update_correct_feedback"] +
                         baseline["pre_update_incorrect_feedback"], 96)
        control, _ = initialize(seed=11)
        opt2 = torch.optim.AdamW(control.parameters(), lr=.002)
        no_context = train_steps(control, opt2, rows, [], steps=3, seed=37,
                                 use_feedback=False)
        self.assertEqual(no_context["history_bearing_exposures"], 0)
        self.assertEqual(no_context["sampled_question_sha256"],
                         baseline["sampled_question_sha256"])

    def test_logical_lessons_actually_practice_standalone_and_dialogue(self):
        model, _ = initialize(seed=13)
        records = mandatory_train("D01.NOT")
        opt = torch.optim.AdamW(model.parameters(), lr=.002)
        stats = train_steps(model, opt, records, [], steps=4, seed=21,
                            use_feedback=True, mix_standalone=True)
        self.assertEqual(stats["exposures"], 128)
        self.assertGreater(stats["history_bearing_exposures"], 0)
        self.assertGreaterEqual(stats["standalone_exposures"], 64)
        self.assertLess(stats["standalone_exposures"], 128)
        self.assertTrue(stats["mixed_standalone_instruction"])

    def test_formative_transcript_is_scored_before_feedback(self):
        model, _ = initialize(seed=9)
        p = panels("D03.AND_NOT_RIGHT", "exam")[0]
        predictions, turns = formative(model, p.rows, use_feedback=True)
        self.assertEqual(len(turns), 6)
        self.assertEqual(score(predictions)["n"], 6)
        for row in turns:
            self.assertEqual(row["feedback"] == "FEEDBACK.CORRECT",
                             row["student_answer"] == row["oracle_answer"])
            self.assertEqual(row["correction_if_wrong"] is None,
                             row["student_answer"] == row["oracle_answer"])

    def test_versioned_checkpoint_and_very_short_arm_preserve_sealed_gate(self):
        with tempfile.TemporaryDirectory() as dirname:
            out = Path(dirname) / "feedback-context"
            report, plan = run_arm(out, use_feedback=True, seed=19, steps=2,
                                   remedy_steps=0, max_stages=1)
            self.assertEqual(report["stages_attempted"], 1)
            self.assertIn("D00.PROTOCOL", plan)
            model, payload = load_checkpoint(out / "stage-01.pt")
            self.assertEqual(payload["stage"], "D00.PROTOCOL")
            self.assertEqual(payload["state_hash"], report["state_hash"])
            stage_log = __import__("json").loads((out / "stage-01.json").read_text())
            self.assertEqual(stage_log["gate_policy"], "contextual_only")
            self.assertEqual(score(predict(model, fixed_gate("D00.PROTOCOL")))["correct"],
                             stage_log["standalone_gate"]["correct"])
            primer = standard_primer("D00.PROTOCOL")
            self.assertEqual(score(predict(model, fixed_gate("D00.PROTOCOL"),
                                            histories=[primer] * len(fixed_gate("D00.PROTOCOL"))))["correct"],
                             report["briefs"][0]["gate"]["correct"])
            with patch("bilqis_formal.pilot_v2.source_fingerprint", return_value="tampered"):
                with self.assertRaisesRegex(ValueError, "RUN_SOURCE_FINGERPRINT_MISMATCH"):
                    replay(Path(dirname))


if __name__ == "__main__":
    unittest.main()
