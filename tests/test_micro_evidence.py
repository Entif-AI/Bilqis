"""Bind the portable developmental result to its frozen sources and checkpoints."""
import unittest
from pathlib import Path

from bilqis_ref.model import state_hash
from bilqis_micro.run import file_hash, read_json, verify_freeze, make_optimizer, optimizer_receipt
from bilqis_micro.model import load_checkpoint

RUN = Path(__file__).resolve().parents[1] / "docs/evidence/micro-universes/run-01"


class CommittedMicroEvidenceTests(unittest.TestCase):
    def test_frozen_sources_samples_and_initial_weights(self):
        frozen, cfg, _ = verify_freeze(RUN)
        model, initial = load_checkpoint(RUN / "initial.pt")
        self.assertEqual(state_hash(model), frozen["initial_state_sha256"])
        self.assertFalse(initial["initializer"]["pretrained_neural_transfer"])
        self.assertEqual(cfg["model"]["vocab_size"], 68)
        samples = read_json(RUN / "samples.json")
        self.assertTrue({1, 2, 3, 4} <= {s["stage"] for s in samples})
        self.assertEqual([s["gold"] for s in samples[3:5]], ["TRUE", "FALSE"])

    def test_result_lineage_and_complete_portable_checksums(self):
        result = read_json(RUN / "result.json")
        cfg = read_json(RUN / "config.json")
        self.assertEqual(result["parameter_or_optimizer_resets"], 0)
        self.assertEqual(result["steps"], sum(cfg["stage_steps"]))
        self.assertEqual(result["examples"], 32 * result["steps"])
        parent = file_hash(RUN / "initial.pt")
        previous = None
        for r in result["stages"]:
            model, payload = load_checkpoint(RUN / r["checkpoint"])
            optimizer = make_optimizer(model, cfg)
            optimizer.load_state_dict(payload["optimizer"])
            self.assertEqual(payload["metadata"]["parent_checkpoint_sha256"], parent)
            self.assertEqual(optimizer_receipt(optimizer), r["optimizer_after"])
            self.assertEqual(optimizer_receipt(optimizer)["steps"], [r["end_step"]])
            if previous:
                self.assertEqual(r["start_state_sha256"], previous["end_state_sha256"])
                self.assertEqual(r["optimizer_before"], previous["optimizer_after"])
            parent, previous = file_hash(RUN / r["checkpoint"]), r
        replay = read_json(RUN / "replay.json")
        self.assertEqual(replay["status"], "REPRODUCED")
        self.assertTrue(replay["different_process_than_training"])
        self.assertEqual(replay["final_state_sha256"], result["final_state_sha256"])
        checksums = {name: h for h, name in (line.split() for line in (RUN / "CHECKSUMS.sha256").read_text().splitlines())}
        self.assertTrue({"gallery.json", "result.json", "replay.json", "after-U4.pt", "initial.pt"} <= checksums.keys())
        self.assertEqual(set(checksums), {p.name for p in RUN.iterdir() if p.is_file() and p.name != "CHECKSUMS.sha256"})
        for name, expected in checksums.items():
            self.assertEqual(file_hash(RUN / name), expected, name)


if __name__ == "__main__":
    unittest.main()
