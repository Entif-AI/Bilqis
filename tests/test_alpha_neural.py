import copy
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import torch

from bilqis_alpha.codec import token_manifest
from bilqis_alpha.data import known_cases
from bilqis_alpha.features import compile_embeddings, feature_map, tensor_hash
from bilqis_alpha.model import AlphaStudent, initialize, predict, save_checkpoint, load_checkpoint
from bilqis_ref.model import ModelConfig, QLinear, batch, state_hash


class AlphaNeuralTests(unittest.TestCase):
    def config(self):
        return ModelConfig(vocab_size=len(token_manifest()["tokens"]), context=128,
                           width=16, layers=1, heads=2, expansion=2, precision="ternary")

    def test_semantic_geometry_is_pre_step_deterministic_and_token_equivariant(self):
        a, receipt = compile_embeddings(16, "semantic_aligned", 102)
        b, same = compile_embeddings(16, "semantic_aligned", 102)
        torch.testing.assert_close(a, b, atol=0, rtol=0)
        self.assertEqual(receipt, same)
        self.assertEqual(receipt["tensor_sha256"], tensor_hash(a))
        self.assertEqual(a[0].abs().sum().item(), 0)
        tokens = token_manifest()["tokens"]
        renamed = [tokens[0]] + list(reversed(tokens[1:]))
        permuted, _ = compile_embeddings(16, "semantic_aligned", 102, tokens=renamed)
        for i, semantic_id in enumerate(renamed):
            torch.testing.assert_close(permuted[i], a[tokens.index(semantic_id)], atol=0, rtol=0)
        misaligned, _ = compile_embeddings(16, "semantic_permuted", 102)
        self.assertEqual(sorted(tuple(r.tolist()) for r in a), sorted(tuple(r.tolist()) for r in misaligned))
        self.assertFalse(torch.equal(a, misaligned))
        ids, features, manifest = feature_map()
        self.assertEqual(features.shape[0], len(ids))
        from bilqis_alpha.semantics import sid
        self.assertFalse(torch.equal(features[ids.index(sid("unknown"))], features[ids.index(sid("conflict"))]))
        self.assertIn("role-sensitive", manifest["basis"])
        self.assertTrue(receipt["scratch_no_pretrained_weights"])
        from bilqis_alpha.semantics import registry
        renamed_registry = copy.deepcopy(registry())
        for entry in renamed_registry["entries"]:
            entry["name"] = "alternate display name"
        with patch("bilqis_alpha.features.registry", return_value=renamed_registry):
            same_ids, same_features, _ = feature_map()
        self.assertEqual(ids, same_ids)
        torch.testing.assert_close(features, same_features, atol=0, rtol=0)

    def test_true_gradient_checkpoint_and_oracle_free_inference(self):
        c = self.config()
        m, manifest = initialize(c, seed=102)
        before = state_hash(m)
        self.assertEqual(tensor_hash(m.embedding.weight), manifest["tensor_sha256"])
        self.assertEqual(m.embedding.weight.dtype, torch.float32)
        semantics = [r["semantic"] for r in known_cases()[:4]]
        outputs = predict(m, semantics)
        self.assertEqual(len(outputs), 4)
        with patch("bilqis_alpha.semantics.evaluate", side_effect=AssertionError("oracle leaked into inference")):
            self.assertEqual(outputs, predict(m, semantics))
        from bilqis_alpha.codec import encode
        x, lengths = batch([encode(s) for s in semantics])
        optimizer = torch.optim.AdamW(m.parameters(), lr=.001, foreach=False)
        optimizer.zero_grad()
        loss = torch.nn.functional.cross_entropy(m(x, lengths), torch.arange(4))
        loss.backward()
        self.assertTrue(torch.isfinite(loss))
        self.assertTrue(any(p.grad is not None and p.grad.abs().sum() > 0 for p in m.parameters()))
        optimizer.step()
        self.assertNotEqual(before, state_hash(m))
        with tempfile.TemporaryDirectory() as temp:
            path = Path(temp) / "model.pt"
            save_checkpoint(path, m, manifest, {"test": True})
            loaded, meta = load_checkpoint(path)
            self.assertEqual(state_hash(m), state_hash(loaded))
            self.assertEqual(predict(m, semantics), predict(loaded, semantics))
            # A changed ABI receipt is a rejected checkpoint, not UNKNOWN.
            raw = torch.load(path, weights_only=True)
            raw["initializer"]["token_abi_sha256"] = "bad"
            torch.save(raw, path)
            with self.assertRaisesRegex(ValueError, "binding"):
                load_checkpoint(path)

    def test_all_initialization_profiles_share_topology_and_quantized_forward_has_gradient(self):
        counts = []
        for profile in ("semantic_aligned", "iid_random", "semantic_permuted"):
            m, _ = initialize(self.config(), seed=102, profile=profile)
            counts.append(sum(p.numel() for p in m.parameters()))
        self.assertEqual(len(set(counts)), 1)
        layer = QLinear(3, 2, "ternary")
        with torch.no_grad():
            layer.weight.copy_(torch.tensor([[.1, -.4, .9], [-.7, .2, .0]]))
        x = torch.tensor([[.25, -.5, 1.]], requires_grad=True)
        scale = layer.weight.detach().abs().mean()
        w = (layer.weight.detach() / scale).round().clamp(-1, 1) * scale
        a = x.detach().abs().amax(-1, keepdim=True) / 127
        expected = torch.nn.functional.linear((x.detach() / a).round().clamp(-127, 127) * a, w)
        torch.testing.assert_close(layer(x), expected, atol=0, rtol=0)
        layer(x).sum().backward()
        self.assertGreater(layer.weight.grad.abs().sum(), 0)
        self.assertGreater(x.grad.abs().sum(), 0)


if __name__ == "__main__":
    unittest.main()
