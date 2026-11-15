from dataclasses import replace
import unittest

from bilqis_mlx.runtime.capability_retention import EvidenceStage, evaluate_retention_candidate
from bilqis_mlx.runtime.tests.capability.capability_retention_helpers import _screen_inputs

PARENT = 'a' * 64
CANDIDATE = 'b' * 64


class RetentionObservationTests(unittest.TestCase):
    def test_foundation_early_rejection_reports_only_completed_assessments(self):
        parent, candidate, target, policy, cohorts = _screen_inputs(protected_loss=3)
        cohorts = tuple(replace(c, evidence_stage=EvidenceStage.FOUNDATION_ACQUISITION) for c in cohorts)
        events = []
        result = evaluate_retention_candidate(parent, candidate, target, policy, cohorts, PARENT, CANDIDATE, observer=events.append)
        self.assertEqual(result.reason, 'PROTECTED_CAPABILITY_REGRESSION')
        self.assertEqual([(e['retention_completed'], e['retention_total'], e['retention_role']) for e in events],
                         [(0, 6, 'parent'), (1, 6, 'parent'), (1, 6, 'candidate'), (2, 6, 'candidate')])
        self.assertTrue(all(e['retention_subject'] == 'protected' for e in events))

    def test_adaptive_reports_each_completed_assessment(self):
        parent, candidate, target, policy, cohorts = _screen_inputs(protected_loss=0)
        events = []
        evaluate_retention_candidate(parent, candidate, target, policy, cohorts, PARENT, CANDIDATE, observer=events.append)
        self.assertEqual([e['retention_completed'] for e in events], [0, 1, 1, 2, 2, 3, 3, 4, 4, 5, 5, 6])
        self.assertTrue(all(e['retention_total'] == 6 for e in events))
