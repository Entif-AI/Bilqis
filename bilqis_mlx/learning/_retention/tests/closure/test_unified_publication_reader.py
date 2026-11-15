import unittest
from types import SimpleNamespace
from unittest.mock import patch

from bilqis_mlx.learning.atlas_acceptance import CLOSURE_ACCEPTANCE_SCHEMA
from bilqis_mlx.runtime.bamf_bundle.publication.acceptance import _require_non_genesis_acceptance_identity


class UnifiedPublicationReaderTests(unittest.TestCase):
    def test_v7_requires_retained_proof_validation(self):
        proof = SimpleNamespace(digest='2'*64)
        state = SimpleNamespace(optimizer_step=1, step_proofs=(proof,))
        student = SimpleNamespace(run_id='run', generation=1, retained_state=state,
                                  topology=SimpleNamespace(digest='topology'),
                                  extents=SimpleNamespace(
                                      digest='extents', factor_map_digest='3'*64),
                                  correction_frontier={'source_authority_registry_sha256': None},
                                  transition={})
        acceptance = SimpleNamespace(digest='1'*64, run_id='run', generation=1,
            feature_sha256='3'*64, optimizer_step=1, candidate_identity_sha256='4'*64,
            schema_version=CLOSURE_ACCEPTANCE_SCHEMA, step_proof_sha256=('2'*64,),
            source_authority_registry_sha256=None)
        pointer = {'acceptance_sha256': '1'*64}
        with patch('bilqis_mlx.runtime.bamf_bundle.publication.acceptance.bind_candidate_identity_or_fallback', return_value='4'*64), \
             patch('bilqis_mlx.learning._retention._atlas_acceptance_records.require_closure_proofs', side_effect=ValueError('mismatched closure')) as verify:
            with self.assertRaisesRegex(ValueError, 'mismatched closure'):
                _require_non_genesis_acceptance_identity(acceptance, pointer, student)
            verify.assert_called_once_with(acceptance, (proof,))

    def test_published_retained_acceptance_checks_parent_identity(self):
        from bilqis_mlx.errors import BilqisError
        from bilqis_mlx.runtime.bamf_bundle.publication.acceptance import require_published_acceptance
        from bilqis_mlx.runtime.bamf_bundle.records import BAMF_POINTER_SCHEMA
        parent = SimpleNamespace(run_id='run', generation=0, run_identity='id',
            topology=SimpleNamespace(digest='topology'),
            extents=SimpleNamespace(digest='extents'),
            retained_state=SimpleNamespace(allocations=SimpleNamespace(digest='allocation')))
        student = SimpleNamespace(run_id='run', generation=1, run_identity='id',
            parent_manifest_sha256='a'*64, transition={},
            retained_state=SimpleNamespace(allocations=SimpleNamespace(digest='allocation')))
        binding = SimpleNamespace(parent_candidate_identity_sha256='b'*64)
        pointer = {'schema': BAMF_POINTER_SCHEMA}
        with patch('bilqis_mlx.runtime.bamf_bundle.publication.acceptance._read_published_acceptance_record', return_value={}), \
             patch('bilqis_mlx.runtime.bamf_bundle.publication.acceptance._parse_published_acceptance', return_value=binding), \
             patch('bilqis_mlx.runtime.bamf_bundle.publication.acceptance._require_non_genesis_acceptance_identity'), \
             patch('bilqis_mlx.runtime.bamf_bundle.publication.acceptance.bind_candidate_identity_or_fallback', return_value='c'*64):
            with self.assertRaises(BilqisError):
                require_published_acceptance('/tmp/test', pointer, student,
                    load_bundle=lambda *args, **kwargs: parent, live_manifest=lambda *args: {})
