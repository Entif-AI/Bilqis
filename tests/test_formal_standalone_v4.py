"""Behavior checks for e7's standalone-first, no teacher-LLM experiment."""
from __future__ import annotations

import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from bilqis_formal.course_v3 import (
    STAGES, fixed_gate, mandatory_train, missing_prerequisites,
    structural_transfer_probe, validate_course)
from bilqis_formal.dialogue_v3 import answer_domain, gold_label
from bilqis_formal.pilot_v4 import (
    SEEDS, SOURCE_FILES, STAGE_IDS, STEPS_PER_STAGE, VERSION, fixed_formative, fixed_lesson,
    replay, run, run_seed, source_sha256, standalone_admitted)
from bilqis_formal.student_v3 import load_checkpoint, predict
from bilqis_formal.pilot_v3 import score


class StandalonePlanTests(unittest.TestCase):
    def test_source_fingerprint_includes_transitively_imported_code(self):
        root = Path(__file__).resolve().parent.parent
        required = {
            "bilqis_formal/pilot_v4.py", "bilqis_formal/pilot_v3.py",
            "bilqis_formal/kev_v3.py", "bilqis_formal/kev_v2.py",
            "bilqis_formal/kev_teacher.py", "bilqis_ref/codec.py",
            "bilqis_ref/semantics.py", "bilqis_formal/course_v2.py",
            "bilqis_ref/model.py", "bilqis_formal/student_v3.py",
            "bilqis_formal/semantics.py", "docs/formal/DIALOGUE_V04_STANDALONE.md",
        }
        self.assertTrue(required <= set(SOURCE_FILES))
        self.assertTrue(all((root / path).is_file() for path in SOURCE_FILES))
        self.assertEqual(len(source_sha256()), 64)

    def test_metacognition_laws_and_dialogue_history_are_not_training_targets(self):
        self.assertTrue(validate_course())
        self.assertEqual(len(STAGE_IDS), 6)
        self.assertNotIn("J00.PROPOSED_ANSWER", STAGE_IDS)
        for stage in STAGE_IDS:
            questions = fixed_lesson(stage)
            self.assertTrue(questions)
            self.assertEqual(len({row["id"] for row in questions}), len(questions))
            self.assertEqual({r["input"]["task"] for r in questions}, {"evaluate"})
            self.assertTrue(all(r["gold"] in answer_domain(r["input"]) for r in questions))
            self.assertTrue(all(r["gold"] == gold_label(r["input"]) for r in questions))
            self.assertFalse({r["id"] for r in questions} &
                             {r["id"] for r in fixed_gate(stage)})

    def test_formative_structural_and_gate_are_all_sealed(self):
        for stage in STAGE_IDS:
            sampled = {r["id"] for r in fixed_lesson(stage)}
            formative = {r["id"] for r in fixed_formative(stage)}
            self.assertEqual(len(formative), len(fixed_formative(stage)))
            structural = {r["id"] for r in structural_transfer_probe(stage)}
            gate = {r["id"] for r in fixed_gate(stage)}
            self.assertFalse(sampled & formative)
            self.assertFalse(sampled & structural)
            self.assertFalse(sampled & gate)
            self.assertFalse(formative & gate)
            self.assertFalse(structural & gate)

    def test_atomic_and_independently_eligible_after_failed_not(self):
        admitted = {"V00.BOOLEAN"}
        self.assertEqual(missing_prerequisites("V02.AND", admitted), ())
        self.assertEqual(set(missing_prerequisites("V03.AND_NOT_RIGHT", admitted)),
                         {"V01.NOT", "V02.AND"})

    def test_dialogue_performance_cannot_veto_truth_promotion(self):
        perfect = {"correct": 4, "n": 4}
        failed_history = {"correct": 0, "n": 4}
        self.assertTrue(standalone_admitted(perfect, {"V00.BOOLEAN": perfect}))
        self.assertTrue(standalone_admitted(perfect, {}))
        self.assertFalse(standalone_admitted(failed_history, {}))
        self.assertFalse(standalone_admitted(perfect, {"V00.BOOLEAN": failed_history}))

    def test_scoped_epoch_rejects_seed_shopping_wrong_path_and_budget(self):
        with tempfile.TemporaryDirectory() as dirname:
            folder = Path(dirname) / "unapproved"
            with self.assertRaisesRegex(ValueError, "PREREGISTERED_SCOPE_DRIFT"):
                run(folder, seeds=SEEDS[:1], steps=STEPS_PER_STAGE)
            with self.assertRaisesRegex(ValueError, "PREREGISTERED_SCOPE_DRIFT"):
                run(folder, seeds=SEEDS, steps=STEPS_PER_STAGE + 1)
            with self.assertRaisesRegex(ValueError, "PREREGISTERED_OUTPUT_PATH"):
                run(folder)
            self.assertFalse(folder.exists())
            folder.mkdir()
            (folder / "original-evidence.json").write_text('{"source":"unrelated"}')
            with self.assertRaisesRegex(ValueError, "PREREGISTERED_OUTPUT_PATH"):
                run(folder)
            self.assertEqual((folder / "original-evidence.json").read_text(),
                             '{"source":"unrelated"}')
            self.assertFalse((folder / "aborted.json").exists())


class SavedStudentTests(unittest.TestCase):
    def test_bounded_smoke_stops_on_gate_and_never_trains_dialogue(self):
        with tempfile.TemporaryDirectory() as dirname:
            out = Path(dirname) / "one_student"
            report = run_seed(out, seed=99, locked_source=source_sha256(), steps=2)
            self.assertGreaterEqual(report["stages_attempted"], 1)
            self.assertEqual(report["total_context_exposures"], 0)
            self.assertEqual(report["native_kev_calls"], 0)
            self.assertNotIn("J00.PROPOSED_ANSWER", report["stages_promoted"])
            self.assertFalse((out / "stage-07.pt").exists())
            manifest = json.loads((out / "manifest.json").read_text())
            self.assertFalse(manifest["student_init"]["pretrained_weights"])
            for number, stage in enumerate(report["summaries"], 1):
                self.assertEqual(stage["stage"], STAGE_IDS[number - 1])
                model, snapshot = load_checkpoint(out / f"stage-{number:02d}.pt")
                self.assertEqual(snapshot["stage"], stage["stage"])
                exam = score(predict(model, fixed_gate(stage["stage"]), mode="none"))
                self.assertEqual((exam["correct"], exam["n"]),
                                 (stage["standalone"]["correct"], stage["standalone"]["n"]))
            self.assertEqual(report["total_optimizer_updates"],
                             report["stages_attempted"] * 2)

    def test_replay_rejects_fake_source(self):
        with tempfile.TemporaryDirectory() as dirname:
            out = Path(dirname)
            (out / "preregistration.json").write_text(json.dumps({
                "version": "bilqis.formal.pilot/v0.4.0",
                "source_sha256": "0" * 64, "seeds": list(SEEDS),
                "stages": list(STAGE_IDS)}))
            with self.assertRaisesRegex(ValueError, "FROZEN_SOURCE_OR_PLAN_MISMATCH"):
                replay(out)

    def test_full_saved_micro_epoch_replays_and_detects_forged_promotion(self):
        with tempfile.TemporaryDirectory() as dirname, (
                patch("bilqis_formal.pilot_v4.SEEDS", (99,))), (
                patch("bilqis_formal.pilot_v4.STEPS_PER_STAGE", 2)):
            out = Path(dirname)
            frozen = {"version": VERSION, "source_sha256": source_sha256(),
                      "source_commit": "0" * 40, "seeds": [99],
                      "steps": 2, "stages": list(STAGE_IDS)}
            (out / "preregistration.json").write_text(json.dumps(frozen))
            report = run_seed(out / "seed-99", seed=99,
                              locked_source=frozen["source_sha256"], steps=2)
            (out / "comparison.json").write_text(json.dumps({
                "version": VERSION, "preregistration": frozen,
                "per_seed": [report]}))
            self.assertEqual(replay(out)["status"], "REPLAY_VERIFIED")
            first_stage = out / "seed-99" / "stage-01.json"
            original = json.loads(first_stage.read_text())
            tampered = {**original, "promoted": not original["promoted"]}
            first_stage.write_text(json.dumps(tampered))
            with self.assertRaisesRegex(ValueError, "PROGRESSION_RECEIPT_MISMATCH"):
                replay(out)


if __name__ == "__main__":
    unittest.main()
