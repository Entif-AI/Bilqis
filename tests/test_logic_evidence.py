"""Published attempt must account for every optimizer input and every gold row."""
from collections import Counter
import json
from pathlib import Path
import unittest

from bilqis_logic.data import audit_splits
from bilqis_logic.kernel import encode
from bilqis_logic.pilot import file_hash


class EvidenceTests(unittest.TestCase):
    def test_complete_fixed_attempt_and_training_isolation(self):
        root = Path(__file__).resolve().parents[1] / "docs/evidence/logic-t0-t1/epoch-01"
        data = json.loads((root / "data.json").read_text())
        result = json.loads((root / "result.json").read_text())
        audit_splits(data)
        train = {r["id"]: r for s in data if s.startswith("TRAIN") for r in data[s]}
        heldout = {r["id"] for s in data if not s.startswith("TRAIN") for r in data[s]}
        trace = [json.loads(line) for line in (root / "training.jsonl").read_text().splitlines()]
        self.assertEqual(len(trace), 1024)
        counts = Counter()
        tokens, padded = 0, 0
        for i, step in enumerate(trace, 1):
            self.assertEqual(step["step"], i)
            self.assertEqual(step["phase"], "A" if i <= 256 else "B")
            self.assertEqual(len(step["row_ids"]), 32)
            self.assertFalse(set(step["row_ids"]) & heldout)
            self.assertTrue(set(step["row_ids"]) <= set(train))
            lengths = [len(encode(train[r]["input"])) for r in step["row_ids"]]
            self.assertEqual(sum(lengths), step["tokens"])
            self.assertEqual(max(lengths) * 32, step["padded_positions"])
            tokens += step["tokens"]
            padded += step["padded_positions"]
            counts.update(step["row_ids"])
        self.assertEqual(dict(counts), result["exposures_by_row"])
        self.assertEqual(sum(counts.values()), result["examples"])
        self.assertEqual(tokens, result["nonpadding_tokens"])
        self.assertEqual(padded, result["padded_positions"])
        self.assertEqual(file_hash(root / "training.jsonl"), result["evidence_sha256"]["training.jsonl"])

    def test_published_pretraining_freeze_and_replay_bindings(self):
        root = Path(__file__).resolve().parents[1] / "docs/evidence/logic-t0-t1/epoch-01"
        freeze = json.loads((root / "freeze.json").read_text())
        result = json.loads((root / "result.json").read_text())
        replay = json.loads((root / "replay.json").read_text())
        for name, expected in freeze["artifacts"].items():
            if not name.endswith(".pt"):
                self.assertEqual(file_hash(root / name), expected, name)
        for name, expected in result["evidence_sha256"].items():
            self.assertEqual(file_hash(root / name), expected, name)
        self.assertEqual(file_hash(root / "freeze.json"), result["freeze_sha256"])
        self.assertEqual(replay["checkpoint_sha256"], result["checkpoint_sha256"])
        self.assertEqual(replay["predictions"], 936)
        self.assertEqual(replay["max_absolute_error"], 0)
