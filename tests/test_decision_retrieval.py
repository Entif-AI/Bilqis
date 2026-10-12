import math
import unittest
from unittest.mock import patch

from bilqis_alpha.eg2_retrieval import _direct_url, filter_retrieval, normalize, project, rank


class DecisionRetrievalTest(unittest.TestCase):
    def test_normalize_and_project_reject_non_finite_vectors(self):
        self.assertEqual(normalize([3, 4]), [0.6, 0.8])
        self.assertEqual(project([3, 4, 0], dimensions=2), [0.6, 0.8])
        for vector in ([0, 0], [1, math.inf], [math.nan, 1]):
            with self.assertRaises(ValueError):
                normalize(vector)

    def test_rank_is_deterministic_and_breaks_ties_by_candidate_id(self):
        rows = rank([1, 0], [
            {'candidate_id': 'z', 'vector': [1, 0]},
            {'candidate_id': 'a', 'vector': [1, 0]},
            {'candidate_id': 'away', 'vector': [0, 1]},
        ])
        self.assertEqual([row['candidate_id'] for row in rows], ['a', 'z', 'away'])
        self.assertEqual([row['rank'] for row in rows], [1, 2, 3])

    def test_recall_miss_does_not_force_or_inject_gold(self):
        rows = rank([1, 0], [{'candidate_id': 'present', 'vector': [1, 0]}])
        self.assertEqual([row['candidate_id'] for row in rows], ['present'])
        self.assertNotIn('gold', rows[0])

    def test_filter_cannot_bypass_legality_and_preserves_rejection(self):
        result = filter_retrieval([
            {'candidate_id': 'legal', 'similarity': 0.9, 'rank': 1},
            {'candidate_id': 'illegal', 'similarity': 0.8, 'rank': 2},
        ], {'legal'})
        self.assertEqual(result['accepted'], [{'candidate_id': 'legal', 'similarity': 0.9, 'rank': 1}])
        self.assertEqual(result['rejected'][0]['candidate_id'], 'illegal')
        self.assertEqual(result['rejected'][0]['rejection'], 'ILLEGAL_CANDIDATE_ID')

    def test_direct_url_receipt_retains_vcs_metadata(self):
        class Distribution:
            def read_text(self, name):
                self.name = name
                return '{"url":"https://example.invalid/mlx-vlm","vcs_info":{"commit_id":"3d87e884"}}'
        with patch('bilqis_alpha.eg2_retrieval.importlib.metadata.distribution', return_value=Distribution()):
            self.assertEqual(_direct_url()['vcs_info']['commit_id'], '3d87e884')

    def test_hard_negative_margin_is_measured_even_when_gold_is_outside_top_k(self):
        from bilqis_alpha.eg2_retrieval import hard_negative_separation
        docs=[{'candidate_id':'gold','vector':[0,1]}, {'candidate_id':'inverse','vector':[1,0]}]
        result=hard_negative_separation([1,0],docs,'gold',['inverse','missing'])
        self.assertEqual(result['gold']['rank'],2)
        self.assertEqual(result['margin'],-1.)
        self.assertFalse(result['beats_all_hard_negatives'])
        self.assertEqual(result['missing_hard_negative_ids'],['missing'])
        missing=hard_negative_separation([1,0],docs,'absent',['inverse'])
        self.assertIsNone(missing['gold']); self.assertIsNone(missing['margin'])

