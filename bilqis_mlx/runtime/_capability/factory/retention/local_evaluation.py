"""Ordinary C05 target-first evaluation over exact local protection scope."""
from dataclasses import replace

from bilqis_mlx.semantics.domains import contract_digest

from bilqis_mlx.runtime.capability_evaluation import Assessment, _invalid, _sha
from bilqis_mlx.runtime.capability_retention import (
    AssessmentPair, Decision, DecisionStatus,
)
from bilqis_mlx.runtime.capability_retention_foundation import (
    FoundationRetentionPolicy,
    _evaluate_fixed_school,
    _fixed_cohort_contract,
)
from bilqis_mlx.runtime.capability_retention_foundation_runtime import (
    final_fixed_school_decision,
)


def _target_evidence_digest(target_capability, policy, pair, plan_sha256):
    return contract_digest({
        "schema": "bilqis.c05.foundation-target-first-evidence/v1",
        "target_capability": target_capability,
        "policy_sha256": policy.digest(),
        "retention_protection_plan_sha256": plan_sha256,
        "parent_assessment_sha256": pair.parent.digest(),
        "candidate_assessment_sha256": pair.candidate.digest(),
    })


def evaluate_target_gate(
        target_capability: str, policy: FoundationRetentionPolicy,
        pair: AssessmentPair, *, retention_protection_plan_sha256: str,
) -> Decision | None:
    """Reject a comparable no-gain target before any protected inference runs."""
    if (type(policy) is not FoundationRetentionPolicy
            or type(pair) is not AssessmentPair
            or not _sha(retention_protection_plan_sha256)
            or pair.parent.cohort.capability_groups
            != ((target_capability, dict(policy.capability_groups)[target_capability]),)):
        _invalid("BAMF_C05_TARGET_FIRST_EVIDENCE_INVALID")
    coverage = policy.baseline_coverage
    if coverage is None:
        _invalid("BAMF_C05_TARGET_FIRST_BASELINE_REQUIRED")
    before, total = pair.parent.score(target_capability)
    after, candidate_total = pair.candidate.score(target_capability)
    if candidate_total != total:
        _invalid("BAMF_C05_TARGET_FIRST_SCORE_TOTAL_DRIFT")
    if target_capability not in set(coverage.measured_capabilities) or after > before:
        return None
    reason = ("TARGET_BASELINE_REGRESSION"
              if after < before else "NO_MEASURABLE_TARGET_GAIN")
    return Decision(
        DecisionStatus.REJECT, reason,
        pair.parent.generation_digest, pair.candidate.generation_digest,
        _target_evidence_digest(
            target_capability, policy, pair, retention_protection_plan_sha256),
        policy.digest(),
        blocking_capability=(target_capability if after < before else None),
        baseline_coverage=coverage,
        outcome_scores=((target_capability, before, after, total),),
        evaluated_capability_ids=(target_capability,),
        retention_protection_plan_sha256=retention_protection_plan_sha256,
    )


def _assessment_maps(assessment):
    return (
        {case.case_id: result for case, result in zip(
            assessment.cohort.cases, assessment.results)},
        {case.case_id: contract for case, contract in zip(
            assessment.cohort.cases, assessment.solver_contracts)},
    )


def finalize_target_first_local_candidate(
        target_capability: str, policy: FoundationRetentionPolicy, fixed,
        target_pair: AssessmentPair, protected_pair: AssessmentPair | None, *,
        retention_protection_plan_sha256: str,
        evaluated_capability_ids: tuple[str, ...], observer=None) -> Decision:
    """Compose the fresh target pair with later protected evidence without re-solving it."""
    _fixed_cohort_contract(target_capability, policy, fixed)
    if (not _sha(retention_protection_plan_sha256)
            or evaluated_capability_ids
            != tuple(capability for capability, _group in policy.capability_groups)
            or type(target_pair) is not AssessmentPair):
        _invalid("BAMF_C05_RETENTION_PROTECTION_SCOPE_INVALID")
    pairs = (target_pair,) + ((protected_pair,) if protected_pair is not None else ())
    if (any(type(pair) is not AssessmentPair for pair in pairs)
            or len({pair.parent.generation_digest for pair in pairs}) != 1
            or len({pair.candidate.generation_digest for pair in pairs}) != 1):
        _invalid("BAMF_C05_TARGET_FIRST_EVIDENCE_INVALID")
    parent_results, parent_contracts = {}, {}
    candidate_results, candidate_contracts = {}, {}
    for pair in pairs:
        results, contracts = _assessment_maps(pair.parent)
        parent_results.update(results)
        parent_contracts.update(contracts)
        results, contracts = _assessment_maps(pair.candidate)
        candidate_results.update(results)
        candidate_contracts.update(contracts)
    case_ids = {case.case_id for case in fixed.cases}
    if (set(parent_results) != case_ids or set(candidate_results) != case_ids):
        _invalid("BAMF_C05_TARGET_FIRST_EVIDENCE_INVALID")
    pair_digests = tuple((pair.parent.digest(), pair.candidate.digest()) for pair in pairs)
    decision = final_fixed_school_decision(
        target_capability,
        dict(policy.capability_groups)[target_capability],
        dict(policy.protected_reference_losses), policy, fixed,
        target_pair.parent.generation_digest, target_pair.candidate.generation_digest,
        lambda digests, blocking: contract_digest({
            "schema": "bilqis.c05.foundation-local-retention-evidence/v2",
            "target_capability": target_capability,
            "policy_sha256": policy.digest(),
            "retention_protection_plan_sha256": retention_protection_plan_sha256,
            "evaluated_capability_ids": evaluated_capability_ids,
            "assessment_pairs": tuple(digests),
            "blocking_capability": blocking,
        }),
        pair_digests, parent_results, parent_contracts,
        candidate_results, candidate_contracts, observer=observer, ordinary=True,
        evaluated_capability_ids=evaluated_capability_ids,
        retention_protection_plan_sha256=retention_protection_plan_sha256)
    scores = []
    for capability in evaluated_capability_ids:
        source = next(pair for pair in pairs
                      if capability in dict(pair.parent.cohort.capability_groups))
        before, total = source.parent.score(capability)
        after, _ = source.candidate.score(capability)
        scores.append((capability, before, after, total))
    return replace(decision, outcome_scores=tuple(scores))


def evaluate_foundation_local_candidate(
        parent_solver, candidate_solver, target_capability: str,
        policy: FoundationRetentionPolicy, fixed,
        parent_generation: str, candidate_generation: str, *,
        retention_protection_plan_sha256: str,
        evaluated_capability_ids: tuple[str, ...],
        parent_assessment: Assessment | None = None, observer=None) -> Decision:
    """Evaluate target plus plan-selected protection, never grade/school aggregates."""
    _fixed_cohort_contract(target_capability, policy, fixed)
    if (not _sha(retention_protection_plan_sha256)
            or evaluated_capability_ids
            != tuple(capability for capability, _group in policy.capability_groups)):
        _invalid("BAMF_C05_RETENTION_PROTECTION_SCOPE_INVALID")
    return _evaluate_fixed_school(
        parent_solver, candidate_solver, target_capability, policy, fixed,
        parent_generation, candidate_generation,
        lambda pair_digests, blocking: contract_digest({
            "schema": "bilqis.c05.foundation-local-retention-evidence/v1",
            "target_capability": target_capability,
            "policy_sha256": policy.digest(),
            "retention_protection_plan_sha256":
                retention_protection_plan_sha256,
            "evaluated_capability_ids": evaluated_capability_ids,
            "fixed_pairs": tuple(pair_digests),
            "blocking_capability": blocking,
        }),
        parent_assessment=parent_assessment, ordinary=True,
        evaluated_capability_ids=evaluated_capability_ids,
        retention_protection_plan_sha256=retention_protection_plan_sha256,
        **({"observer": observer} if observer is not None else {}))


__all__ = (
    "evaluate_foundation_local_candidate", "evaluate_target_gate",
    "finalize_target_first_local_candidate",
)
