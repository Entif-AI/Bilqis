from pathlib import Path
from tempfile import TemporaryDirectory
from types import SimpleNamespace as NS
import unittest

from bilqis_mlx.runtime.bamf_operator.evidence import prepare_candidate_evidence_root
from bilqis_mlx.runtime.teacher_observation_capture import store_sidecar
from bilqis_mlx.runtime.bamf_operator.evidence_projection import (
    apply_candidate_evidence, selected_visit_evidence, unknown_generated_grade_evidence,
)


class VisitEvidenceProjectionTests(unittest.TestCase):
    def test_grade_identity_is_schema_neutral_and_missing_grade_rationale_is_unknown(self):
        cap = NS(capability_id='Z.NOVEL', semantic_ids=('sem:z',), prerequisites=('Y.PREV',),
                 semantic_prerequisites=('sem:y',), constituents=('Y.PREV',))
        frontier = NS(frontier_sha256='1' * 64, a09_snapshot_sha256='2' * 64,
                      a09_closure_sha256='3' * 64, capabilities=(cap,))
        selection = NS(
            lesson_grade='Z', offer=NS(capability_id='Z.NOVEL'), _lawful_frontier=frontier,
            visit=NS(identity=NS(visit_id='visit-z', policy_key='how-z')),
            option_id='option-z', ranking_evidence={
                'policy_digest': '4' * 64, 'ordinals': [0, 1, 2],
                'known': [False, True, True], 'dispatch_tier': 2,
                'eligible_since': 7, 'downstream_unlocks': 3, 'stable_id': 'option-z'})
        evidence = selected_visit_evidence(selection)
        self.assertEqual(evidence['grade_id'], 'Z')
        self.assertEqual(evidence['semantic_ids'], ['sem:z'])
        self.assertEqual(evidence['prerequisites'], ['Y.PREV'])
        grade = unknown_generated_grade_evidence('Z')
        self.assertEqual(grade['state'], 'UNKNOWN')
        self.assertEqual(grade['developmental_slope_state'], 'UNKNOWN')
        self.assertIsNone(grade['definition_id'])

    def test_content_addressed_candidate_sidecar_replays_lesson_roles_and_decision(self):
        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            prepare_candidate_evidence_root(root)
            payload = {
                'schema': 'bilqis.bamf.c16.3-candidate-evidence/v1',
                'proposal': {
                    'visit_id': 'visit-1', 'selected_policy_key': 'how-1',
                    'selected_option': 'option-1', 'capability': 'A.IDENTITY'},
                'steps': [{
                    'positions': [{'roles': ['selected_option']}],
                    'mentors': []}],
                'outcome': {'accepted': False, 'decision': {
                    'decision': 'REJECT', 'reason': 'NO_MEASURABLE_TARGET_GAIN',
                    'blocking_capability': 'A.IDENTITY', 'blocking_scope': None,
                    'policy_sha256': 'd' * 64, 'baseline_coverage': None}},
            }
            object_ref = store_sidecar(root, payload)
            receipt = {'schema': 'bilqis.bamf.c16.3-candidate-evidence-reference/v1',
                       'object': object_ref}
            first = apply_candidate_evidence(root, {'schema': 'bilqis.bamf.visit-evidence/v1'}, receipt)
            cold = apply_candidate_evidence(root, {'schema': 'bilqis.bamf.visit-evidence/v1'}, receipt)
            self.assertEqual(first, cold)
            self.assertEqual(first['lesson_roles']['selected_option'], 1)
            self.assertEqual(first['reason'], 'NO_MEASURABLE_TARGET_GAIN')
            self.assertEqual(first['candidate_evidence_sha256'], receipt['object']['sha256'])



if __name__ == '__main__':
    unittest.main()
