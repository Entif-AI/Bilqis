"""Foundation-acquisition C05 screen: fixed-school authority, fresh cohorts telemetry only."""
from __future__ import annotations

from dataclasses import dataclass, replace

from ..learning.retention_policy import retention_reason, scaled_loss_allowance
from ..semantics.domains import contract_digest
from .capability_evaluation import (
    Assessment, EvidenceKind, EvidenceStage, EvaluationCohort, _invalid, _names, _sha,
    case_census_digest, evaluate_capabilities,
)
from .capability_retention import (
    AssessmentPair, Decision, DecisionStatus, RetentionPolicy,
)

_PAIR_WIDTH = 2
_MIN_PROBE_EACH = 2
_MAX_PROBE_EACH = 48


@dataclass(frozen=True)
class FoundationRetentionPolicy:
    """Authorizing foundation policy binds only fixed-school preservation evidence."""
    capability_groups: tuple[tuple[str, str], ...]
    protected_groups: tuple[str, ...]
    protected_reference_losses: tuple[tuple[str, int], ...]
    probe_each: int
    fixed_census_digest: str
    schema_version: str = "bilqis.c05.foundation-retention-policy/v1"

    def __post_init__(self):
        if (not isinstance(self.capability_groups, tuple) or not self.capability_groups
                or any(not isinstance(pair, tuple) or len(pair) != _PAIR_WIDTH
                       or not all(isinstance(item, str) and item for item in pair)
                       for pair in self.capability_groups)
                or len(dict(self.capability_groups)) != len(self.capability_groups)
                or not _names(self.protected_groups)
                or not set(self.protected_groups) <= set(dict(self.capability_groups).values())
                or type(self.probe_each) is not int
                or not _MIN_PROBE_EACH <= self.probe_each <= _MAX_PROBE_EACH
                or not isinstance(self.protected_reference_losses, tuple)
                or any(not isinstance(pair, tuple) or len(pair) != _PAIR_WIDTH
                       or pair[0] not in dict(self.capability_groups)
                       or type(pair[1]) is not int or not 0 <= pair[1] <= self.probe_each
                       for pair in self.protected_reference_losses)
                or len(dict(self.protected_reference_losses))
                != len(self.protected_reference_losses)
                or not _sha(self.fixed_census_digest)
                or self.schema_version != "bilqis.c05.foundation-retention-policy/v1"):
            _invalid("BAMF_FOUNDATION_RETENTION_POLICY_INVALID")

    def digest(self):
        return contract_digest(self)


def _cohort_contract(target_capability, policy, cohorts):
    target_group = dict(policy.capability_groups)[target_capability]
    expected = (
        {(target_capability, target_group)},
        {item for item in policy.capability_groups if item[1] == target_group},
        set(policy.capability_groups),
    )
    if (target_group not in policy.protected_groups
            or set(dict(policy.protected_reference_losses))
            != set(dict(policy.capability_groups)) - {target_capability}
            or any(set(cohort.capability_groups) != required
                   for cohort, required in zip(cohorts, expected))
            or len({(cohort.rubric_sha256, cohort.scope_sha256,
                     cohort.source_sha256, cohort.policy_sha256)
                    for cohort in cohorts}) != 1
            or any(cohort.policy_sha256 != policy.digest()
                   or cohort.expected_case_digest
                   != dict(policy.required_census_digests)[cohort.kind]
                   for cohort in cohorts)):
        _invalid("BAMF_RETENTION_COMPLETE_COVERAGE_REQUIRED")
    return target_group


def _fixed_cohort_contract(target_capability, policy, fixed):
    target_group = dict(policy.capability_groups).get(target_capability)
    if (target_group is None
            or target_group not in policy.protected_groups
            or set(dict(policy.protected_reference_losses))
            != set(dict(policy.capability_groups)) - {target_capability}
            or type(fixed) is not EvaluationCohort
            or fixed.kind is not EvidenceKind.FIXED_SCHOOL
            or fixed.evidence_stage is not EvidenceStage.FOUNDATION_ACQUISITION
            or set(fixed.capability_groups) != set(policy.capability_groups)
            or fixed.policy_sha256 != policy.digest()
            or fixed.expected_case_digest != policy.fixed_census_digest):
        _invalid("BAMF_FOUNDATION_FIXED_SCHOOL_CONTRACT_INVALID")
    return target_group


def _evidence_digest(
        target_capability, policy, cohorts, fixed_pair_digests,
        blocking_capability=None):
    return contract_digest({
        "schema": "bilqis.c05.foundation-retention-evidence/v1",
        "target_capability": target_capability,
        "policy_sha256": policy.digest(),
        "measure_only_census": tuple(
            cohort.expected_case_digest for cohort in cohorts[:2]),
        "fixed_school_census": cohorts[2].expected_case_digest,
        "fixed_pairs": tuple(fixed_pair_digests),
        "blocking_capability": blocking_capability,
    })


def _fixed_evidence_digest(
        target_capability, policy, fixed, fixed_pair_digests,
        blocking_capability=None):
    return contract_digest({
        "schema": "bilqis.c05.foundation-fixed-school-evidence/v1",
        "target_capability": target_capability,
        "policy_sha256": policy.digest(),
        "fixed_school_census": fixed.expected_case_digest,
        "fixed_pairs": tuple(fixed_pair_digests),
        "blocking_capability": blocking_capability,
    })


def _evaluate_fixed_school(
        parent_solver, candidate_solver, target_capability, policy, fixed,
        parent_generation, candidate_generation, evidence_digest):
    target_group = dict(policy.capability_groups)[target_capability]
    groups = dict(fixed.capability_groups)
    references = dict(policy.protected_reference_losses)
    same_grade = tuple(
        capability for capability, group in fixed.capability_groups
        if capability != target_capability and group == target_group
        and capability in references)
    other_protected = tuple(
        capability for capability, _group in fixed.capability_groups
        if capability not in same_grade and capability != target_capability
        and capability in references)
    remaining = tuple(
        capability for capability, _group in fixed.capability_groups
        if capability not in same_grade and capability not in other_protected)
    capability_order = (*same_grade, *other_protected, *remaining)

    parent_results, candidate_results = {}, {}
    parent_contracts, candidate_contracts = {}, {}
    pair_digests = []
    for capability in capability_order:
        cases = tuple(case for case in fixed.cases if case.capability_id == capability)
        cohort = replace(
            fixed, cases=cases,
            capability_groups=((capability, groups[capability]),),
            expected_case_digest=case_census_digest(cases))
        parent_assessment = evaluate_capabilities(parent_solver, cohort, parent_generation)
        candidate_assessment = evaluate_capabilities(
            candidate_solver, cohort, candidate_generation)
        pair = AssessmentPair(parent_assessment, candidate_assessment)
        pair_digests.append((parent_assessment.digest(), candidate_assessment.digest()))
        for case, result, contract in zip(
                cases, parent_assessment.results, parent_assessment.solver_contracts):
            parent_results[case.case_id] = result
            parent_contracts[case.case_id] = contract
        for case, result, contract in zip(
                cases, candidate_assessment.results, candidate_assessment.solver_contracts):
            candidate_results[case.case_id] = result
            candidate_contracts[case.case_id] = contract

        reference = references.get(capability)
        if (reference is not None
                and -pair.delta(capability) > scaled_loss_allowance(
                    pair.parent.score(capability)[1], reference, policy.probe_each)):
            return Decision(
                DecisionStatus.REJECT, "PROTECTED_CAPABILITY_REGRESSION",
                parent_generation, candidate_generation,
                evidence_digest(pair_digests, capability), policy.digest(),
                blocking_capability=capability)

    parent_assessment = Assessment(
        fixed, parent_generation,
        tuple(parent_results[case.case_id] for case in fixed.cases),
        tuple(parent_contracts[case.case_id] for case in fixed.cases))
    candidate_assessment = Assessment(
        fixed, candidate_generation,
        tuple(candidate_results[case.case_id] for case in fixed.cases),
        tuple(candidate_contracts[case.case_id] for case in fixed.cases))
    fixed_pair = AssessmentPair(parent_assessment, candidate_assessment)
    census = dict(policy.capability_groups)

    def net(capabilities):
        return sum(fixed_pair.delta(capability) for capability in capabilities)

    lesson = tuple(capability for capability, group in census.items()
                   if group == target_group)
    reason = retention_reason(
        no_target_gain=False, same_grade_net_gain=0,
        fixed_grade_regression=net(lesson) < 0,
        active_grade_regression=any(
            net(tuple(capability for capability, group in census.items()
                      if group == protected)) < 0
            for protected in policy.protected_groups),
        whole_school_regression=net(tuple(census)) < 0,
        frontier_measured=True, fragile_losses=False, exceeded=False)
    return Decision(
        DecisionStatus.ELIGIBLE if reason == "PAIRED_SCREEN_WITHIN_BUDGET"
        else DecisionStatus.REJECT,
        reason, parent_generation, candidate_generation,
        evidence_digest(pair_digests, None), policy.digest())


def evaluate_foundation_retention_candidate(
        parent_solver, candidate_solver, target_capability: str,
        policy: RetentionPolicy, cohorts, parent_generation: str,
        candidate_generation: str) -> Decision:
    """Evaluate fixed-school authority first and stop on a final protected loss."""
    _cohort_contract(target_capability, policy, cohorts)
    fixed = cohorts[2]
    return _evaluate_fixed_school(
        parent_solver, candidate_solver, target_capability, policy, fixed,
        parent_generation, candidate_generation,
        lambda pair_digests, blocking: _evidence_digest(
            target_capability, policy, cohorts, pair_digests,
            blocking_capability=blocking))


def evaluate_foundation_fixed_school_candidate(
        parent_solver, candidate_solver, target_capability: str,
        policy: FoundationRetentionPolicy, fixed: EvaluationCohort,
        parent_generation: str, candidate_generation: str) -> Decision:
    """Production foundation path: authorizing fixed school only, no fresh telemetry."""
    _fixed_cohort_contract(target_capability, policy, fixed)
    return _evaluate_fixed_school(
        parent_solver, candidate_solver, target_capability, policy, fixed,
        parent_generation, candidate_generation,
        lambda pair_digests, blocking: _fixed_evidence_digest(
            target_capability, policy, fixed, pair_digests,
            blocking_capability=blocking))


__all__ = (
    "FoundationRetentionPolicy", "evaluate_foundation_fixed_school_candidate",
    "evaluate_foundation_retention_candidate",
)
