"""A future worker must not silently choose a freshly initialized student."""
import copy
import json
from pathlib import Path
import tempfile
import unittest

from bilqis_micro.run import optimizer_receipt
from bilqis_active.loader import MANIFEST, load_active, locate


class ActiveStudentTests(unittest.TestCase):
    def test_active_checkpoint_reopens_same_learned_neural_history(self):
        manifest = json.loads(MANIFEST.read_text())
        self.assertEqual(manifest["optimizer_step"], 13848)
        self.assertEqual(manifest["schema"], "bilqis.active-learner/v1")
        if not (Path.home() / "Code" / "bilqis-learner-custody" /
                manifest["checkpoint_file"]).is_file():
            # The repository refuses silent scratch/U6 fallback in CI and
            # anywhere its independently custodied active weights are absent.
            with self.assertRaises(FileNotFoundError):
                locate()
            return
        checkpoint, manifest = locate()
        self.assertTrue(checkpoint.is_file())
        model, optimizer, payload, receipt = load_active()
        self.assertEqual(optimizer_receipt(optimizer)["steps"], [13848])
        self.assertEqual(model.config.vocab_size, 113)
        self.assertEqual(len(payload["graph"]["tokens"]), 113)
        self.assertEqual(receipt["checkpoint_sha256"],
                         "8752457dc6fec2ced061ee206bcec4b9473d8270347515ba8bf98f22b5c2c174")

    def test_tampered_manifest_cannot_fall_back_to_scratch_or_U6(self):
        original = json.loads(MANIFEST.read_text())
        invalid = copy.deepcopy(original)
        invalid["checkpoint_sha256"] = "0" * 64
        with tempfile.TemporaryDirectory() as temp:
            path = Path(temp) / "active.json"
            path.write_text(json.dumps(invalid))
            # Public CI may lack the active checkpoint. A malicious manifest
            # must never be accepted as a valid substitute in either case.
            if (Path.home() / "Code" / "bilqis-learner-custody" /
                    original["checkpoint_file"]).exists():
                with self.assertRaises(ValueError):
                    load_active(path)
            else:
                with self.assertRaises(FileNotFoundError):
                    load_active(path)
            invalid["checkpoint_sha256"] = original["checkpoint_sha256"]
            invalid["checkpoint_file"] = "missing-best.pt"
            path.write_text(json.dumps(invalid))
            with self.assertRaises(FileNotFoundError):
                load_active(path)


if __name__ == "__main__":
    unittest.main()
