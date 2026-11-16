from dataclasses import replace
import unittest

from bilqis_mlx.runtime.capability_retention import EvidenceStage, evaluate_retention_candidate
from bilqis_mlx.runtime.tests.capability.capability_retention_helpers import _screen_inputs

PARENT = 'a' * 64
CANDIDATE = 'b' * 64


class RetentionObservationTests(unittest.TestCase):
    def assert_scores_match_card(self, decision, events):
        card = next(event['retention_scorecard'] for event in events
                    if 'retention_scorecard' in event)
        scores = {cap: (before, after, total)
                  for cap, before, after, total in decision.outcome_scores}
        self.assertEqual(len(scores), 3)
        for entry in (card['target'], *card['protected']):
            self.assertEqual(scores[entry['capability_id']],
                             (entry['before'], entry['after'], entry['total']))

    def test_outcome_scores_survive_acceptance_and_target_regression(self):
        parent, candidate, target, policy, cohorts = _screen_inputs(protected_loss=0)
        cohorts = tuple(replace(c, evidence_stage=EvidenceStage.FOUNDATION_ACQUISITION)
                        for c in cohorts)
        for first, second, reason in ((parent, candidate, 'PAIRED_SCREEN_WITHIN_BUDGET'),
                                      (candidate, parent, 'TARGET_BASELINE_REGRESSION')):
            events = []
            decision = evaluate_retention_candidate(first, second, target, policy, cohorts,
                                                     PARENT, CANDIDATE, observer=events.append)
            self.assertEqual(decision.reason, reason)
            self.assert_scores_match_card(decision, events)

    def test_foundation_rejection_reports_each_completed_assessment(self):
        parent, candidate, target, policy, cohorts = _screen_inputs(protected_loss=12)
        cohorts = tuple(replace(c, evidence_stage=EvidenceStage.FOUNDATION_ACQUISITION) for c in cohorts)
        events = []
        result = evaluate_retention_candidate(parent, candidate, target, policy, cohorts, PARENT, CANDIDATE, observer=events.append)
        self.assertEqual(result.reason, 'PROTECTED_CAPABILITY_REGRESSION')
        self.assert_scores_match_card(result, events)
        self.assertEqual([(e['retention_completed'], e['retention_total'], e['retention_role']) for e in events if 'retention_completed' in e],
                         [(0, 4, 'parent'), (1, 4, 'parent'),
                          (1, 4, 'candidate'), (2, 4, 'candidate'),
                          (2, 4, 'candidate'), (3, 4, 'candidate'),
                          (3, 4, 'candidate'), (4, 4, 'candidate')])
        self.assertEqual(
            [e['retention_subject'] for e in events if 'retention_completed' in e],
            ['fixed_school', 'fixed_school', 'protected', 'protected',
             'other', 'other', 'target', 'target'])

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
        parent, candidate, target, _, cohorts = _screen_inputs(protected_loss=12)
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
        self.assert_scores_match_card(result, events)
        self.assertEqual([(e['retention_completed'], e['retention_total'], e['retention_role']) for e in events if 'retention_completed' in e],
                         [(0, 3, 'candidate'), (1, 3, 'candidate'),
                          (1, 3, 'candidate'), (2, 3, 'candidate'),
                          (2, 3, 'candidate'), (3, 3, 'candidate')])
        self.assertEqual(
            [e['retention_subject'] for e in events if 'retention_completed' in e],
            ['protected', 'protected', 'other', 'other', 'target', 'target'])
