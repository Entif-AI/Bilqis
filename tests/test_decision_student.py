import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import torch

from bilqis_alpha.decision_features import token_manifest
from bilqis_alpha.decision_student import (
    DecisionStudent,
    VERSION,
    initialize,
    load_checkpoint,
    save_checkpoint,
)
from bilqis_ref.model import ModelConfig, state_hash


class DecisionStudentTests(unittest.TestCase):
    def config(self):
        return ModelConfig(vocab_size=len(token_manifest()["tokens"]), context=16,
                           width=16, layers=1, heads=2, expansion=2, precision="ternary")

    def inputs(self):
        states = torch.tensor([[1, 2, 3], [3, 2, 0]], dtype=torch.long)
        state_lengths = torch.tensor([3, 2], dtype=torch.long)
        candidates = torch.tensor([
            [[4, 5], [6, 0], [7, 8]],
            [[8, 9], [10, 11], [0, 0]],
        ], dtype=torch.long)
        candidate_lengths = torch.tensor([[2, 1, 2], [2, 2, 0]], dtype=torch.long)
        candidate_mask = torch.tensor([[True, True, True], [True, True, False]])
        return states, state_lengths, candidates, candidate_lengths, candidate_mask

    def test_seeded_scratch_initialization_is_exact_and_uses_compiled_geometry(self):
        a, receipt_a = initialize(self.config(), seed=202)
        b, receipt_b = initialize(self.config(), seed=202)
        self.assertEqual(VERSION, "decision-student-0.1.0")
        self.assertEqual(receipt_a, receipt_b)
        self.assertEqual(state_hash(a), state_hash(b))
        self.assertEqual(receipt_a["tensor_sha256"], receipt_b["tensor_sha256"])

    def test_candidate_permutation_is_equivariant_and_panel_size_is_not_architecture(self):
        model, _ = initialize(self.config(), seed=202)
        state, state_lengths, candidates, candidate_lengths, mask = self.inputs()
        logits = model(state, state_lengths, candidates, candidate_lengths, mask)
        permutation = torch.tensor([2, 0, 1])
        permuted = model(state, state_lengths, candidates[:, permutation], candidate_lengths[:, permutation], mask[:, permutation])
        torch.testing.assert_close(permuted, logits[:, permutation], atol=1e-6, rtol=0)
        two = model(state[:, :2], state_lengths.clamp(max=2), candidates[:, :2], candidate_lengths[:, :2], mask[:, :2])
        self.assertEqual(two.shape, (2, 2))

    def test_masks_and_invalid_panels_are_explicit(self):
        model, _ = initialize(self.config(), seed=202)
        state, state_lengths, candidates, candidate_lengths, mask = self.inputs()
        logits = model(state, state_lengths, candidates, candidate_lengths, mask)
        self.assertTrue(torch.isneginf(logits[1, 2]))
        with self.assertRaisesRegex(ValueError, "offered"):
            model(state, state_lengths, candidates, candidate_lengths, torch.zeros_like(mask))
        with self.assertRaisesRegex(ValueError, "decision"):
            model(state, state_lengths, candidates[:, :, :1], candidate_lengths, mask)
        with self.assertRaisesRegex(ValueError, "CONTEXT_OVERFLOW"):
            model(torch.ones((2, 17), dtype=torch.long), torch.tensor([17, 17]), candidates, candidate_lengths, mask)

    def test_gradient_checkpoint_reload_and_oracle_free_score_path(self):
        model, initializer = initialize(self.config(), seed=202)
        state, state_lengths, candidates, candidate_lengths, mask = self.inputs()
        before = state_hash(model)
        optimizer = torch.optim.AdamW(model.parameters(), lr=.001, foreach=False)
        loss = torch.nn.functional.cross_entropy(model(state, state_lengths, candidates, candidate_lengths, mask), torch.tensor([1, 0]))
        loss.backward()
        optimizer.step()
        self.assertNotEqual(before, state_hash(model))
        with tempfile.TemporaryDirectory() as temp:
            path = Path(temp) / "decision.pt"
            save_checkpoint(path, model, initializer, {"test": True}, optimizer=optimizer)
            loaded, payload = load_checkpoint(path)
            torch.testing.assert_close(
                model(state, state_lengths, candidates, candidate_lengths, mask),
                loaded(state, state_lengths, candidates, candidate_lengths, mask), atol=0, rtol=0,
            )
            self.assertIn("optimizer_state_dict", payload)
        with patch("bilqis_alpha.decision_student.compile_embeddings", side_effect=AssertionError("oracle leaked")):
            model(state, state_lengths, candidates, candidate_lengths, mask)


if __name__ == "__main__":
    unittest.main()
