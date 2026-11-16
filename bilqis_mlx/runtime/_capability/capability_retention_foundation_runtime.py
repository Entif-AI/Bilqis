"""Foundation-retention evaluation runtime and observational score projection."""
from __future__ import annotations

import time

from bilqis_mlx.runtime.bamf_operator.telemetry import emit

from ..learning.retention_policy import _mastery_debt_utility
from .capability_evaluation import Assessment, _invalid
from .capability_retention import AssessmentPair, Decision, DecisionStatus


def observed_assessment(
        solver, cohort, generation, observer, completed, total, subject, role,
        *, evaluator):
    emit(observer, retention_completed=completed, retention_total=total,
         retention_subject=subject, retention_role=role)
    started = time.perf_counter()
    result = evaluator(solver, cohort, generation)
    elapsed = max(0.0, time.perf_counter() - started)
    emit(observer, retention_completed=completed + 1, retention_total=total,
         retention_subject=subject, retention_role=role,
         retention_stage_timing={
             "subject": subject, "role": role, "wall_seconds": elapsed})
    return result


def parent_case_index(
        parent_solver, fixed, parent_generation, parent_assessment, observer, total,
        *, evaluator):
    if parent_assessment is None:
        parent_assessment = observed_assessment(
            parent_solver, fixed, parent_generation, observer, 0, total,
            "fixed_school", "parent", evaluator=evaluator)
    elif (type(parent_assessment) is not Assessment
            or parent_assessment.cohort != fixed
            or parent_assessment.generation_digest != parent_generation):
        _invalid("BAMF_C05_PARENT_ASSESSMENT_CACHE_DRIFT")
    return {
        case.case_id: (result, contract)
        for case, result, contract in zip(
            fixed.cases, parent_assessment.results,
            parent_assessment.solver_contracts)
    }


def _fixed_school_score_context(
        target_capability, references, policy, fixed,
        parent_generation, candidate_generation,
        parent_results, parent_contracts, candidate_results, candidate_contracts,
        observer):
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
    coverage = policy.baseline_coverage
    measured = (tuple(coverage.measured_capabilities) if coverage is not None
                else tuple(census))
    measured_set = set(measured)
    scores = {}
    for capability in census:
        before, total = fixed_pair.parent.score(capability)
        after, after_total = fixed_pair.candidate.score(capability)
        if total != after_total:
            _invalid("BAMF_FOUNDATION_FIXED_SCHOOL_SCORE_TOTAL_DRIFT")
        scores[capability] = {"before": before, "after": after, "total": total}
    target_delta = fixed_pair.delta(target_capability)
    emit(observer, retention_scorecard={
        "schema": "bilqis.bamf.retention-scorecard/v1",
        "evidence_stage": fixed.evidence_stage.value,
        "target_capability": target_capability,
        "target": {
            "capability_id": target_capability,
            "state": ("MEASURED" if target_capability in measured_set else "NOT_MEASURED"),
            "baseline": scores[target_capability]["before"],
            **scores[target_capability],
            "delta": target_delta,
        },
        "protected": [
            {
                "capability_id": capability,
                "state": ("MEASURED" if capability in measured_set else "NOT_MEASURED"),
                "baseline": scores[capability]["before"],
                **scores[capability],
                "delta": fixed_pair.delta(capability),
                "loss_allowance": references.get(capability),
            }
            for capability in references
        ],
        "policy_sha256": policy.digest(),
        "probe_each": policy.probe_each,
        "baseline_coverage": (coverage.to_record() if coverage is not None else None),
    })
    return fixed_pair, census, coverage, measured, measured_set, scores, target_delta


def final_fixed_school_decision(
        target_capability, target_group, references, policy, fixed,
        parent_generation, candidate_generation,
        evidence_digest, pair_digests, parent_results, parent_contracts,
        candidate_results, candidate_contracts, observer=None):
    (fixed_pair, census, coverage, measured, measured_set, scores,
     target_delta) = _fixed_school_score_context(
        target_capability, references, policy, fixed,
        parent_generation, candidate_generation,
        parent_results, parent_contracts, candidate_results, candidate_contracts,
        observer)

    def net(capabilities):
        return sum(fixed_pair.delta(capability) for capability in capabilities)
    if target_delta < 0 and target_capability in measured_set:
        return Decision(
            DecisionStatus.REJECT, "TARGET_BASELINE_REGRESSION",
            parent_generation, candidate_generation,
            evidence_digest(pair_digests, target_capability), policy.digest(),
            blocking_capability=target_capability,
            baseline_coverage=coverage)
    if target_delta <= 0:
        reason = "NO_MEASURABLE_TARGET_GAIN"
    else:
        protected = tuple(references)
        losses = tuple(capability for capability in protected
                       if fixed_pair.delta(capability) < 0)
        authoritative = (target_capability, *protected)
        reason = "PAIRED_SCREEN_WITHIN_BUDGET"
        if losses and _mastery_debt_utility(scores, authoritative)[0] <= 0:
            return Decision(
                DecisionStatus.REJECT, "PROTECTED_CAPABILITY_REGRESSION",
                parent_generation, candidate_generation,
                evidence_digest(pair_digests, losses[0]), policy.digest(),
                blocking_capability=losses[0], baseline_coverage=coverage)

        lesson = tuple(
            capability for capability in measured
            if census[capability] == target_group)
        if net(lesson) < 0 and _mastery_debt_utility(scores, lesson)[0] <= 0:
            reason = "FIXED_LESSON_GRADE_REGRESSION"
            blocking_scope = "fixed_group:" + target_group
        else:
            blocking_scope = None
            for group in policy.protected_groups:
                grade = tuple(capability for capability in measured
                              if census[capability] == group)
                if (grade and net(grade) < 0
                        and _mastery_debt_utility(scores, grade)[0] <= 0):
                    reason = "ACTIVE_SCHOOL_GRADE_REGRESSION"
                    blocking_scope = "fixed_group:" + group
                    break
            if (reason == "PAIRED_SCREEN_WITHIN_BUDGET"
                    and measured
                    and net(measured) < 0
                    and _mastery_debt_utility(scores, measured)[0] <= 0):
                reason = "WHOLE_SCHOOL_NET_REGRESSION"
                blocking_scope = "fixed_school"
    return Decision(
        DecisionStatus.ELIGIBLE if reason == "PAIRED_SCREEN_WITHIN_BUDGET"
        else DecisionStatus.REJECT,
        reason, parent_generation, candidate_generation,
        evidence_digest(pair_digests, None), policy.digest(),
        blocking_scope=(blocking_scope if target_delta > 0 else None),
        baseline_coverage=coverage)


__all__ = ("final_fixed_school_decision", "observed_assessment", "parent_case_index")
