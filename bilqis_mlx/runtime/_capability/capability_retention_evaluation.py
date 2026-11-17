"""Owner-run C05 cohort evaluation and retention scorecard projection."""
from __future__ import annotations

import time

from bilqis_mlx.runtime.bamf_operator.telemetry import emit

from .capability_evaluation import (
    CompleteSolver,
    EvaluationCohort,
    EvidenceKind,
    _invalid,
    evaluate_capabilities,
)
from .capability_retention import (
    AssessmentPair,
    Decision,
    PairedRetentionEvidence,
    RetentionPolicy,
    retain_candidate,
)


def _observed_retention_pairs(
        parent_solver, candidate_solver, target_capability, cohorts,
        parent_generation, candidate_generation, observer):
    pairs = []
    completed, total = 0, 2 * len(cohorts)
    for cohort in cohorts:
        assessments = []
        for role, solver, generation in (
                ("parent", parent_solver, parent_generation),
                ("candidate", candidate_solver, candidate_generation)):
            timing_subject = (target_capability
                              if cohort.kind is EvidenceKind.FRESH_TARGET
                              else cohort.kind.value)
            emit(observer, retention_completed=completed, retention_total=total,
                 retention_subject=cohort.kind.value, retention_role=role)
            started = time.perf_counter()
            assessments.append(evaluate_capabilities(solver, cohort, generation))
            elapsed = max(0.0, time.perf_counter() - started)
            completed += 1
            emit(observer, retention_completed=completed, retention_total=total,
                 retention_subject=cohort.kind.value, retention_role=role,
                 retention_stage_timing={
                     "subject": timing_subject, "role": role, "wall_seconds": elapsed})
        pairs.append(AssessmentPair(*assessments))
    return tuple(pairs)


def _emit_retention_scorecard(
        observer, target_capability, policy, stage,
        target_pair, fixed_school_pair):
    from bilqis_mlx.diagnostics.assessment_signals import optional_prediction_signals
    measured = (set(policy.baseline_coverage.measured_capabilities)
                if policy.baseline_coverage is not None
                else set(dict(policy.capability_groups)))
    emit(observer, retention_scorecard={
        "schema": "bilqis.bamf.retention-scorecard/v1",
        "fixed_cohort_sha256": fixed_school_pair.parent.cohort.expected_case_digest,
        "rubric_sha256": fixed_school_pair.parent.cohort.rubric_sha256,
        "source_sha256": fixed_school_pair.parent.cohort.source_sha256,
        "evidence_stage": stage.value,
        "target_capability": target_capability,
        "learning_signals": optional_prediction_signals(
            observer, fixed_school_pair.candidate, target_capability),
        "learning_target": {
            "capability_id": target_capability,
            "state": ("MEASURED" if target_capability in measured else "NOT_MEASURED"),
            "before": fixed_school_pair.parent.score(target_capability)[0],
            "after": fixed_school_pair.candidate.score(target_capability)[0],
            "total": fixed_school_pair.parent.score(target_capability)[1],
        },
        "target": {
            "capability_id": target_capability,
            "state": ("MEASURED" if target_capability in measured else "NOT_MEASURED"),
            "baseline": target_pair.parent.score(target_capability)[0],
            "before": target_pair.parent.score(target_capability)[0],
            "after": target_pair.candidate.score(target_capability)[0],
            "total": target_pair.parent.score(target_capability)[1],
            "delta": target_pair.delta(target_capability),
        },
        "protected": [
            {
                "capability_id": capability,
                "state": ("MEASURED" if capability in measured else "NOT_MEASURED"),
                "baseline": fixed_school_pair.parent.score(capability)[0],
                "before": fixed_school_pair.parent.score(capability)[0],
                "after": fixed_school_pair.candidate.score(capability)[0],
                "total": fixed_school_pair.parent.score(capability)[1],
                "delta": fixed_school_pair.delta(capability),
                "loss_allowance": reference,
            }
            for capability, reference in policy.protected_reference_losses
        ],
        "policy_sha256": policy.digest(),
        "probe_each": policy.probe_each,
        "baseline_coverage": (
            policy.baseline_coverage.to_record()
            if policy.baseline_coverage is not None else None),
    })


def evaluate_retention_candidate(
        parent_solver, candidate_solver, target_capability, policy, cohorts,
        parent_generation, candidate_generation, *, observer=None,
        plasticity_escape=None) -> Decision:
    """Run the authoritative C05 cohorts before deciding candidate retention."""
    required_kinds = (
        EvidenceKind.FRESH_TARGET, EvidenceKind.FRESH_LESSON,
        EvidenceKind.FIXED_SCHOOL,
    )
    if (not isinstance(parent_solver, CompleteSolver)
            or not isinstance(candidate_solver, CompleteSolver)
            or not isinstance(policy, RetentionPolicy)
            or not isinstance(target_capability, str) or not target_capability
            or not isinstance(cohorts, tuple)
            or not all(isinstance(cohort, EvaluationCohort) for cohort in cohorts)
            or tuple(cohort.kind for cohort in cohorts) != required_kinds):
        _invalid("BAMF_RETENTION_SCREEN_INPUT_INVALID")
    stages = {cohort.evidence_stage for cohort in cohorts}
    if len(stages) != 1:
        _invalid("BAMF_RETENTION_EVIDENCE_STAGE_DRIFT")
    from ..learning.retention_policy import (
        RetentionDecisionLaw, decision_law_for_stage,
    )
    law = decision_law_for_stage(next(iter(stages)))
    if law is RetentionDecisionLaw.FOUNDATION_MASTERY_DEBT:
        from .capability_retention_foundation import evaluate_foundation_retention_candidate
        return evaluate_foundation_retention_candidate(
            parent_solver, candidate_solver, target_capability, policy, cohorts,
            parent_generation, candidate_generation,
            **({"observer": observer} if observer is not None else {}))

    target_pair, fresh_lesson_pair, fixed_school_pair = _observed_retention_pairs(
        parent_solver, candidate_solver, target_capability, cohorts,
        parent_generation, candidate_generation, observer)
    evidence = PairedRetentionEvidence(
        target_capability, policy,
        target_pair, fresh_lesson_pair, fixed_school_pair)
    _emit_retention_scorecard(
        observer, target_capability, policy, next(iter(stages)),
        target_pair, fixed_school_pair)
    return retain_candidate(
        parent_generation, candidate_generation, evidence,
        plasticity_escape=plasticity_escape)


__all__ = ("evaluate_retention_candidate",)
