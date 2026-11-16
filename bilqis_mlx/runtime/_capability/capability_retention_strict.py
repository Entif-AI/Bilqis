"""Strict-generalization paired C05 decision logic."""
from __future__ import annotations

from dataclasses import replace

from ..learning.retention_policy import retention_reason, scaled_loss_allowance
from .capability_evaluation import EvidenceStage, _invalid
from .capability_retention import (
    Decision, DecisionStatus, PairedRetentionEvidence,
)


def _retain_candidate(parent, candidate, paired_assessment) -> Decision:
    evidence = paired_assessment
    if (not isinstance(evidence, PairedRetentionEvidence)
            or parent != evidence.target.parent.generation_digest
            or candidate != evidence.target.candidate.generation_digest):
        _invalid("BAMF_RETENTION_GENERATION_DRIFT")
    target = evidence.target_capability
    census = dict(evidence.policy.capability_groups)
    fixed = evidence.fixed_school
    coverage = evidence.policy.baseline_coverage
    measured = (tuple(coverage.measured_capabilities) if coverage is not None
                else tuple(census))

    def net(pair, capabilities):
        return sum(pair.delta(capability) for capability in capabilities)

    lesson = tuple(cap for cap in measured if census[cap] == census[target])
    stage = evidence.target.parent.cohort.evidence_stage
    target_delta = evidence.target.delta(target)
    if target in set(measured) and target_delta < 0:
        return Decision(
            DecisionStatus.REJECT,
            "TARGET_BASELINE_REGRESSION",
            parent,
            candidate,
            evidence.digest(),
            evidence.policy.digest(),
            blocking_capability=target,
            baseline_coverage=coverage,
        )
    protected_pairs = (
        (fixed,) if stage is EvidenceStage.FOUNDATION_ACQUISITION
        else (evidence.fresh_lesson, fixed))
    exceeded = tuple(
        capability
        for pair in protected_pairs
        for capability, reference in evidence.policy.protected_reference_losses
        if capability in dict(pair.parent.cohort.capability_groups)
        and -pair.delta(capability) > scaled_loss_allowance(
            pair.parent.score(capability)[1], reference, evidence.policy.probe_each))
    active_block = next((
        protected for protected in evidence.policy.protected_groups
        if (grade := tuple(cap for cap in measured if census[cap] == protected))
        and net(fixed, grade) < 0
    ), None)
    reason = retention_reason(
        no_target_gain=(stage is EvidenceStage.STRICT_GENERALIZATION
                        and target_delta <= 0),
        same_grade_net_gain=(0 if stage is EvidenceStage.FOUNDATION_ACQUISITION
                             else net(evidence.fresh_lesson, lesson)),
        fixed_grade_regression=net(fixed, lesson) < 0,
        active_grade_regression=active_block is not None,
        whole_school_regression=bool(measured) and net(fixed, measured) < 0,
        frontier_measured=True, fragile_losses=False, exceeded=bool(exceeded))
    return Decision(
        DecisionStatus.ELIGIBLE if reason == "PAIRED_SCREEN_WITHIN_BUDGET"
        else DecisionStatus.REJECT,
        reason, parent, candidate, evidence.digest(), evidence.policy.digest(),
        blocking_capability=(exceeded[0]
                             if reason == "PROTECTED_CAPABILITY_REGRESSION"
                             and exceeded else None),
        blocking_scope=(
            "fresh_group:" + census[target]
            if reason == "SAME_GRADE_NET_REGRESSION" else
            "fixed_group:" + census[target]
            if reason == "FIXED_LESSON_GRADE_REGRESSION" else
            "fixed_group:" + active_block
            if reason == "ACTIVE_SCHOOL_GRADE_REGRESSION" and active_block else
            "fixed_school" if reason == "WHOLE_SCHOOL_NET_REGRESSION" else None),
        baseline_coverage=coverage)


def retain_candidate(parent, candidate, paired_assessment) -> Decision:
    decision = _retain_candidate(parent, candidate, paired_assessment)
    target = paired_assessment.target_capability
    pairs = {cap: paired_assessment.fixed_school
             for cap, _ in paired_assessment.policy.capability_groups}
    pairs[target] = paired_assessment.target
    scores = tuple((cap, *pair.parent.score(cap)[:1], *pair.candidate.score(cap))
                   for cap, pair in pairs.items())
    return replace(decision, outcome_scores=scores)


__all__ = ("retain_candidate",)
