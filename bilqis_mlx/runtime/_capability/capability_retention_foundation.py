"""Foundation-acquisition C05 screen: fixed-school authority, fresh cohorts telemetry only."""
from __future__ import annotations

from dataclasses import dataclass, replace

from ..semantics.domains import contract_digest
from .capability_evaluation import (
    Assessment, EvidenceKind, EvidenceStage, EvaluationCohort, _invalid, _names, _sha,
    case_census_digest, evaluate_capabilities,
)
from bilqis_mlx.runtime.baseline.currentness import BaselineCoverage
from .capability_retention import (
    AssessmentPair, Decision, PairedRetentionEvidence, RetentionPolicy,
)
from .capability_retention_foundation_runtime import (
    final_fixed_school_decision, observed_assessment, parent_case_index,
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
    baseline_coverage: BaselineCoverage | None = None
    schema_version: str = "bilqis.c05.foundation-retention-policy/v2"

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
                or (self.baseline_coverage is not None
                    and (type(self.baseline_coverage) is not BaselineCoverage
                         or set(self.baseline_coverage.measured_capabilities)
                         | set(self.baseline_coverage.unmeasured_capabilities)
                         != set(dict(self.capability_groups))))
                or self.schema_version != "bilqis.c05.foundation-retention-policy/v2"):
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
    protected = set(dict(policy.protected_reference_losses))
    if (target_group not in policy.protected_groups
            or not protected <= set(dict(policy.capability_groups)) - {target_capability}
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
    protected = set(dict(policy.protected_reference_losses))
    measured = (set(policy.baseline_coverage.measured_capabilities)
                if policy.baseline_coverage is not None
                else set(dict(policy.capability_groups)))
    if (target_group is None
            or target_group not in policy.protected_groups
            or not protected <= measured - {target_capability}
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


def _fixed_capability_order(target_capability, policy, fixed, *, ordinary=False):
    target_group = dict(policy.capability_groups)[target_capability]
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
    if ordinary:
        protected = tuple(dict.fromkeys((*same_grade, *other_protected)))
        return target_group, references, (target_capability, *protected)
    return target_group, references, (*same_grade, *other_protected, *remaining)


def _evaluate_fixed_school(
        parent_solver, candidate_solver, target_capability, policy, fixed,
        parent_generation, candidate_generation, evidence_digest,
        parent_assessment=None, *, observer=None, ordinary=False,
        evaluated_capability_ids=(), retention_protection_plan_sha256=None,
        broad_certification_trigger=None):
    target_group, references, capability_order = _fixed_capability_order(
        target_capability, policy, fixed, ordinary=ordinary)
    groups = dict(fixed.capability_groups)
    completed = int(parent_assessment is None)
    total = len(capability_order) + completed
    parent_by_case = parent_case_index(
        parent_solver, fixed, parent_generation, parent_assessment, observer, total,
        evaluator=evaluate_capabilities)
    parent_results, candidate_results = {}, {}
    parent_contracts, candidate_contracts = {}, {}
    pair_digests = []
    outcome_scores = []
    for capability in capability_order:
        cases = tuple(case for case in fixed.cases if case.capability_id == capability)
        cohort = replace(
            fixed, cases=cases,
            capability_groups=((capability, groups[capability]),),
            expected_case_digest=case_census_digest(cases))
        parent_subset = Assessment(
            cohort,
            parent_generation,
            tuple(parent_by_case[case.case_id][0] for case in cases),
            tuple(parent_by_case[case.case_id][1] for case in cases),
        )
        candidate_assessment = observed_assessment(
            candidate_solver, cohort, candidate_generation, observer, completed, total,
            capability, "candidate", evaluator=evaluate_capabilities)
        completed += 1
        pair = AssessmentPair(parent_subset, candidate_assessment)
        pair_digests.append((parent_subset.digest(), candidate_assessment.digest()))
        before, score_total = parent_subset.score(capability)
        after, _ = candidate_assessment.score(capability)
        outcome_scores.append((capability, before, after, score_total))
        for case, result, contract in zip(
                cases, parent_subset.results, parent_subset.solver_contracts):
            parent_results[case.case_id] = result
            parent_contracts[case.case_id] = contract
        for case, result, contract in zip(
                cases, candidate_assessment.results, candidate_assessment.solver_contracts):
            candidate_results[case.case_id] = result
            candidate_contracts[case.case_id] = contract

    decision = final_fixed_school_decision(
        target_capability, target_group, references, policy, fixed,
        parent_generation, candidate_generation,
        evidence_digest, pair_digests, parent_results, parent_contracts,
        candidate_results, candidate_contracts, observer=observer,
        ordinary=ordinary,
        evaluated_capability_ids=evaluated_capability_ids,
        retention_protection_plan_sha256=retention_protection_plan_sha256,
        broad_certification_trigger=broad_certification_trigger)
    return replace(decision, outcome_scores=tuple(outcome_scores))


def evaluate_foundation_retention_candidate(
        parent_solver, candidate_solver, target_capability: str,
        policy: RetentionPolicy, cohorts, parent_generation: str,
        candidate_generation: str, *, observer=None) -> Decision:
    """Evaluate fixed-school authority first and stop on a final protected loss."""
    _cohort_contract(target_capability, policy, cohorts)
    fixed = cohorts[2]
    return _evaluate_fixed_school(
        parent_solver, candidate_solver, target_capability, policy, fixed,
        parent_generation, candidate_generation,
        lambda pair_digests, blocking: _evidence_digest(
            target_capability, policy, cohorts, pair_digests,
            blocking_capability=blocking), **({"observer": observer} if observer is not None else {}))


def evaluate_foundation_fixed_school_candidate(
        parent_solver, candidate_solver, target_capability: str,
        policy: FoundationRetentionPolicy, fixed: EvaluationCohort,
        parent_generation: str, candidate_generation: str, *,
        parent_assessment: Assessment | None = None, observer=None) -> Decision:
    """Production foundation path: authorizing fixed school only, no fresh telemetry."""
    _fixed_cohort_contract(target_capability, policy, fixed)
    return _evaluate_fixed_school(
        parent_solver, candidate_solver, target_capability, policy, fixed,
        parent_generation, candidate_generation,
        lambda pair_digests, blocking: _fixed_evidence_digest(
            target_capability, policy, fixed, pair_digests,
            blocking_capability=blocking),
        parent_assessment=parent_assessment, **({"observer": observer} if observer is not None else {}))


def retain_foundation_candidate(parent, candidate, evidence) -> Decision:
    """Apply ADR-142 economics to already paired foundation evidence."""
    if (not isinstance(evidence, PairedRetentionEvidence)
            or parent != evidence.target.parent.generation_digest
            or candidate != evidence.target.candidate.generation_digest):
        _invalid("BAMF_RETENTION_GENERATION_DRIFT")
    from ..learning.retention_policy import (
        RetentionDecisionLaw, decision_law_for_stage,
    )
    stage = evidence.target.parent.cohort.evidence_stage
    if decision_law_for_stage(stage) is not RetentionDecisionLaw.FOUNDATION_MASTERY_DEBT:
        _invalid("BAMF_RETENTION_DECISION_LAW_DRIFT")
    fixed_pair = evidence.fixed_school
    fixed = fixed_pair.parent.cohort
    policy = evidence.policy
    groups = dict(policy.capability_groups)
    target = evidence.target_capability
    parent_results = {
        case.case_id: result
        for case, result in zip(fixed.cases, fixed_pair.parent.results)
    }
    parent_contracts = {
        case.case_id: contract
        for case, contract in zip(fixed.cases, fixed_pair.parent.solver_contracts)
    }
    candidate_results = {
        case.case_id: result
        for case, result in zip(fixed.cases, fixed_pair.candidate.results)
    }
    candidate_contracts = {
        case.case_id: contract
        for case, contract in zip(fixed.cases, fixed_pair.candidate.solver_contracts)
    }
    evaluated = tuple(capability for capability, _group in policy.capability_groups)
    decision = final_fixed_school_decision(
        target, groups[target], dict(policy.protected_reference_losses), policy, fixed,
        parent, candidate, lambda _pairs, _blocking: evidence.digest(),
        ((fixed_pair.parent.digest(), fixed_pair.candidate.digest()),),
        parent_results, parent_contracts, candidate_results, candidate_contracts,
        ordinary=True, evaluated_capability_ids=evaluated,
    )
    scores = tuple(
        (capability, *fixed_pair.parent.score(capability)[:1],
         *fixed_pair.candidate.score(capability))
        for capability in evaluated
    )
    return replace(decision, outcome_scores=scores)


__all__ = (
    "FoundationRetentionPolicy", "evaluate_foundation_fixed_school_candidate",
    "evaluate_foundation_retention_candidate", "retain_foundation_candidate",
)
