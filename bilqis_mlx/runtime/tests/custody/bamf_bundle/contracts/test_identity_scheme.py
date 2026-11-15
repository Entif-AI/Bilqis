"""Manifest-selected candidate identity across historical and new custody."""
from dataclasses import replace
import json
import os
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest
from unittest.mock import patch

import mlx.core as mx

from bilqis_mlx.data_plane import data_plane
from bilqis_mlx.errors import BilqisError
from bilqis_mlx.learning.atlas_acceptance import candidate_identity_digest
from bilqis_mlx.learning._retention._atlas_candidate.identity import (
    LEGACY_IDENTITY_SCHEME, RAW_IDENTITY_SCHEME,
)
from bilqis_mlx.learning._retention.tests.test_candidate_identity import legacy_oracle
from bilqis_mlx.runtime.bamf_bundle import load_bamf_bundle, save_bamf_bundle
from bilqis_mlx.runtime.bamf_bundle.genesis.records import successor_candidate_identity_digest
from bilqis_mlx.runtime.bamf_bundle.records import canonical, sha
from bilqis_mlx.runtime.bamf_bundle.publication.acceptance import require_accepted_parent
from bilqis_mlx.runtime.tests.custody.bamf_bundle.helpers import (
    accepted_state, candidate, parent_state, rejected_state, shape_patch,
)


class IdentitySchemeCustodyTests(unittest.TestCase):
    def setUp(self):
        mx.set_cache_limit(0)
        self.temporary = TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name)
        env = patch.dict(os.environ, {'BILQIS_DATA_PLANE': str(self.root / 'plane.db')})
        env.start()
        self.addCleanup(env.stop)

    def save(self, bundle, path):
        with shape_patch(), patch('bilqis_mlx.runtime.mlx_checkpoint.assert_headroom'):
            return save_bamf_bundle(bundle, path)

    def test_old_and_new_bundles_bind_recorded_scheme_on_readback(self):
        for scheme in (LEGACY_IDENTITY_SCHEME, RAW_IDENTITY_SCHEME):
            with self.subTest(scheme=scheme):
                state = replace(parent_state(), identity_scheme=scheme)
                bundle = candidate(state)
                root = self.root / scheme.rsplit('/', 1)[1]
                saved = self.save(bundle, root)
                self.assertEqual('identity_scheme' in saved['optimizer'],
                                 scheme == RAW_IDENTITY_SCHEME)
                with shape_patch():
                    cold = load_bamf_bundle(root, expected_manifest_sha256=saved['manifest_sha256'])
                self.assertEqual(cold.retained_state.identity_scheme, scheme)
                self.assertEqual(candidate_identity_digest(cold.retained_state),
                                 candidate_identity_digest(state))
                self.assertEqual(successor_candidate_identity_digest(cold),
                                 successor_candidate_identity_digest(bundle))
                if scheme == LEGACY_IDENTITY_SCHEME:
                    self.assertEqual(candidate_identity_digest(cold.retained_state),
                                     legacy_oracle(state))

    def test_unknown_explicit_scheme_rejects_before_tensor_loading(self):
        root = self.root / 'invalid'
        self.save(candidate(parent_state()), root)
        path = root / 'manifest.json'
        manifest = json.loads(path.read_bytes())
        for scheme in (None, 'future', [], 5):
            with self.subTest(scheme=scheme):
                manifest['optimizer']['identity_scheme'] = scheme
                raw = canonical(manifest)
                path.write_bytes(raw)
                data_plane().put_node(sha(raw), raw, manifest['generation'], None)
                with patch('bilqis_mlx.runtime.mlx_checkpoint.load_bamf_state_payload',
                           side_effect=AssertionError('tensor construction reached')):
                    with self.assertRaises(BilqisError):
                        load_bamf_bundle(root)

    def test_legacy_parent_updated_child_migrates_and_rejection_returns_parent(self):
        parent = replace(parent_state(), identity_scheme=LEGACY_IDENTITY_SCHEME)
        child = accepted_state(parent)
        self.assertEqual(child.identity_scheme, RAW_IDENTITY_SCHEME)
        self.assertIs(rejected_state(parent), parent)
        self.assertEqual(candidate_identity_digest(parent), legacy_oracle(parent))
        parent_bundle = candidate(parent)
        parent_root = self.root / 'parent'
        saved = self.save(parent_bundle, parent_root)
        child_bundle = candidate(child, generation=1, parent=saved['manifest_sha256'])
        child_root = self.root / 'child'
        self.save(child_bundle, child_root)
        with shape_patch():
            cold_parent = load_bamf_bundle(parent_root)
            cold_child = load_bamf_bundle(child_root)
        from types import SimpleNamespace
        acceptance = SimpleNamespace(parent_candidate_identity_sha256=legacy_oracle(parent))
        require_accepted_parent(self.root, cold_child, acceptance,
                                load_bundle=lambda *a, **k: cold_parent)
        acceptance.parent_candidate_identity_sha256 = candidate_identity_digest(
            replace(parent, identity_scheme=RAW_IDENTITY_SCHEME))
        with self.assertRaises(BilqisError):
            require_accepted_parent(self.root, cold_child, acceptance,
                                    load_bundle=lambda *a, **k: cold_parent)

    def test_mlx_indexed_mutation_invalidates_identity(self):
        state = parent_state()
        before = candidate_identity_digest(state)
        name = next(iter(state.optimizer.parameters))
        state.optimizer.parameters[name][0, 0] = 99
        self.assertNotEqual(candidate_identity_digest(state), before)

    def test_accepted_legacy_genesis_migrates_through_publication_and_retry(self):
        from bilqis_mlx.learning.atlas_candidate import CandidateState
        from bilqis_mlx.runtime.bamf_bundle import (
            load_bamf_generation, publish_bamf_generation,
        )
        from bilqis_mlx.runtime.bamf_bundle.admission import derive_successor_bundle
        from bilqis_mlx.runtime.tests.custody.bamf_bundle.helpers import (
            acceptance, publish_genesis,
        )
        def historical_state(*args, **kwargs):
            return CandidateState(*args, **kwargs, identity_scheme=LEGACY_IDENTITY_SCHEME)
        run = self.root / 'accepted-run'
        with shape_patch(), patch('bilqis_mlx.runtime.mlx_checkpoint.assert_headroom'):
            with patch('bilqis_mlx.runtime.bamf_bundle.genesis.preparation.CandidateState',
                       side_effect=historical_state):
                pointer = publish_genesis(run)
            parent = load_bamf_generation(run / 'bamf-state.json')
            self.assertEqual(parent.retained_state.identity_scheme, LEGACY_IDENTITY_SCHEME)
            self.assertEqual(parent.run_identity.initial_candidate_identity_sha256,
                             legacy_oracle(parent.retained_state))
            child = derive_successor_bundle(
                parent, accepted_state(parent.retained_state, parent.extents),
                parent_manifest_sha256=pointer['manifest_sha256'],
                delivery_events=({'event': 'IDENTITY_MIGRATION_FIXTURE'},))
            binding = acceptance(child, parent=parent.retained_state)
            published = publish_bamf_generation(run, child, acceptance=binding, reserve_gib=0.)
            retried = publish_bamf_generation(run, child, acceptance=binding, reserve_gib=0.)
            cold = load_bamf_generation(run / 'bamf-state.json')
            self.assertEqual(retried, published)
            self.assertEqual(cold.retained_state.identity_scheme, RAW_IDENTITY_SCHEME)
            self.assertEqual(candidate_identity_digest(cold.retained_state),
                             candidate_identity_digest(child.retained_state))
