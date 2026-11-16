"""Teacher feedback reuses C05's actual paired solver measurements."""
from dataclasses import replace

from bilqis_mlx.runtime.capability_retention import (
    EvidenceStage, evaluate_retention_candidate,
)
from bilqis_mlx.runtime.tests.capability.capability_retention_helpers import _screen_inputs


def test_measured_scores_are_identical_to_scored_foundation_pairs():
    parent, candidate, target, policy, cohorts = _screen_inputs(protected_loss=2, labels=('Z', 'Y'))
    cohorts = tuple(replace(c, evidence_stage=EvidenceStage.FOUNDATION_ACQUISITION) for c in cohorts)
    result = evaluate_retention_candidate(parent, candidate, target, policy, cohorts, 'a' * 64, 'b' * 64)
    assert set(result.outcome_scores) == {
        ('target', 0, 3, 3), ('protected', 12, 10, 12), ('other', 1, 1, 1)}
    assert result.reason == 'PAIRED_SCREEN_WITHIN_BUDGET'


def test_strict_feedback_uses_authoritative_target_and_fixed_protection():
    parent, candidate, target, policy, cohorts = _screen_inputs(protected_loss=3, labels=('Z', 'Y'))
    result = evaluate_retention_candidate(parent, candidate, target, policy, cohorts, 'a' * 64, 'b' * 64)
    assert set(result.outcome_scores) == {
        ('target', 0, 3, 3), ('protected', 12, 9, 12), ('other', 1, 1, 1)}
    assert result.reason == 'PROTECTED_CAPABILITY_REGRESSION'
