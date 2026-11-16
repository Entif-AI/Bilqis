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
                         [(0, 4, 'parent'), (1, 4, 'parent'), (1, 4, 'candidate'), (2, 4, 'candidate')])
        self.assertEqual([e['retention_subject'] for e in events], ['fixed_school', 'fixed_school', 'protected', 'protected'])

    def test_adaptive_reports_each_completed_assessment(self):
        parent, candidate, target, policy, cohorts = _screen_inputs(protected_loss=0)
        events = []
        evaluate_retention_candidate(parent, candidate, target, policy, cohorts, PARENT, CANDIDATE, observer=events.append)
        self.assertEqual([e['retention_completed'] for e in events if 'retention_completed' in e], [0, 1, 1, 2, 2, 3, 3, 4, 4, 5, 5, 6])
        self.assertTrue(all(e['retention_total'] == 6 for e in events if 'retention_total' in e))

    def test_cached_parent_is_not_reported_as_solver_execution(self):
        from bilqis_mlx.runtime.capability_retention import evaluate_capabilities
        from bilqis_mlx.runtime.capability_retention_foundation import (
            FoundationRetentionPolicy, evaluate_foundation_fixed_school_candidate,
        )
        parent, candidate, target, _, cohorts = _screen_inputs(protected_loss=3)
        fixed = cohorts[2]
        groups = fixed.capability_groups
        policy = FoundationRetentionPolicy(
            groups, tuple(dict.fromkeys(group for _, group in groups)),
            tuple((capability, 1) for capability, _ in groups if capability != target),
            6, fixed.expected_case_digest)
        fixed = replace(fixed, policy_sha256=policy.digest(),
                        evidence_stage=EvidenceStage.FOUNDATION_ACQUISITION)
        cached = evaluate_capabilities(parent, fixed, PARENT)
        events = []
        result = evaluate_foundation_fixed_school_candidate(
            parent, candidate, target, policy, fixed, PARENT, CANDIDATE,
            parent_assessment=cached, observer=events.append)
        self.assertEqual(result.reason, 'PROTECTED_CAPABILITY_REGRESSION')
        self.assertEqual([(e['retention_completed'], e['retention_total'], e['retention_role']) for e in events],
                         [(0, 3, 'candidate'), (1, 3, 'candidate')])
