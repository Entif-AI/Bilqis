import unittest
import torch

from bilqis_alpha.codec import token_manifest as historical_tokens
from bilqis_alpha.features import compile_embeddings as historical_embeddings
from bilqis_alpha.semantics import sid
from bilqis_alpha.decision_features import compile_embeddings, feature_map, token_manifest


class DecisionFeaturesTest(unittest.TestCase):
    def test_historical_collision_preserved_and_new_roles_distinct(self):
        old, _ = historical_embeddings(64)
        ids = historical_tokens()['tokens']
        self.assertTrue(torch.equal(old[ids.index(sid('role-source'))], old[ids.index(sid('role-target'))]))
        new, manifest = compile_embeddings(64)
        ids = token_manifest()['tokens']
        self.assertFalse(torch.equal(new[ids.index(sid('role-source'))], new[ids.index(sid('role-target'))]))
        again, repeated = compile_embeddings(64)
        self.assertTrue(torch.equal(new, again))
        self.assertEqual(manifest, repeated)
        self.assertFalse(manifest['pretrained_vectors'])
        self.assertIn('role-position:directed', feature_map()[2]['basis'])

    def test_geometry_comes_from_identity_and_control_tokens_are_versioned(self):
        table, manifest = compile_embeddings(64)
        self.assertEqual(table.shape, (len(token_manifest()['tokens']), 64))
        self.assertTrue(torch.isfinite(table).all())
        self.assertEqual(float(table[0].abs().sum()), 0.)
        self.assertEqual(manifest['semantic_abi'], 'bilqis-alpha-cogal-0.1.0')
        self.assertNotEqual(manifest['version'], 'alpha-dct-initializer-0.1.0')
        self.assertEqual(len(set(token_manifest()['tokens'])), len(table))
