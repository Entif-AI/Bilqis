"""Strict-only ADR-114 utility and hard certified-debt vetoes."""
from fractions import Fraction

from ..capability_evaluation import _invalid
from .records import (
    CertifiedSurfaceDebt,
    HARD_DEBT_LIMIT,
    PlasticityEscapeState,
    REPAIR_THRESHOLD,
)


def _mastery_debt_utility(pair, capabilities) -> Fraction:
    utility = Fraction()
    selected = tuple(capabilities)
    for capability in selected:
        before, total = pair.parent.score(capability)
        after, candidate_total = pair.candidate.score(capability)
        if candidate_total != total or total <= 0:
            _invalid("BAMF_PLASTICITY_COMPARABLE_SCORE_REQUIRED")
        before_debt = Fraction(total - before, total)
        after_debt = Fraction(total - after, total)
        utility += before_debt ** 2 - after_debt ** 2
    return utility


def projected_debt(
        state: PlasticityEscapeState, fixed_school) -> tuple[CertifiedSurfaceDebt, ...]:
    result = []
    available = set(dict(fixed_school.parent.cohort.capability_groups))
    for item in state.debt:
        amount = item.amount
        capability = item.surface.capability_id
        if capability in available:
            _before, total = fixed_school.parent.score(capability)
            after, candidate_total = fixed_school.candidate.score(capability)
            if total == candidate_total == item.total:
                amount = max(0, item.certified_correct - after)
            else:
                amount = max(0, amount - fixed_school.delta(capability))
        if amount:
            result.append(CertifiedSurfaceDebt(
                item.surface, amount, item.certified_correct, item.total))
    return tuple(result)


def debt_limit_exceeded(state: PlasticityEscapeState, fixed_school) -> bool:
    available = set(dict(fixed_school.parent.cohort.capability_groups))
    for item in state.debt:
        capability = item.surface.capability_id
        current, projected = item.amount, item.amount
        if capability in available:
            before, total = fixed_school.parent.score(capability)
            after, candidate_total = fixed_school.candidate.score(capability)
            if total == candidate_total == item.total:
                current = max(0, item.certified_correct - before)
                projected = max(0, item.certified_correct - after)
            else:
                projected = max(0, item.amount - fixed_school.delta(capability))
        if projected > HARD_DEBT_LIMIT and projected > current:
            return True
    return False


def repair_due_without_progress(state: PlasticityEscapeState, fixed_school) -> bool:
    """Debt may constrain escape, but never selects or authorizes a repair target."""
    due = tuple(item for item in state.debt if item.amount >= REPAIR_THRESHOLD)
    if not due:
        return False
    projected = {item.surface: item.amount for item in projected_debt(state, fixed_school)}
    changes = tuple(
        (item.amount, projected.get(item.surface, 0))
        for item in due)
    return (
        any(after > before for before, after in changes)
        or not any(after < before for before, after in changes)
    )


def relaxed_strict_reason(reason, evidence, state: PlasticityEscapeState | None) -> str:
    """Apply relaxed economics only inside owner-proven activated strict state."""
    if state is None or not state.active:
        return reason
    target = evidence.target_capability
    if state.target_capability_id != target:
        _invalid("BAMF_PLASTICITY_TARGET_IDENTITY_DRIFT")
    from bilqis_mlx.runtime.retention.protection_plan_compiler import policy_epoch_sha256
    stage = evidence.target.parent.cohort.evidence_stage
    if state.policy_epoch_sha256 != policy_epoch_sha256(stage):
        _invalid("BAMF_PLASTICITY_POLICY_EPOCH_DRIFT")
    coverage = evidence.policy.baseline_coverage
    if coverage is not None and target not in set(coverage.measured_capabilities):
        return "PLASTICITY_TARGET_BASELINE_UNMEASURED"
    if evidence.target.delta(target) <= 0:
        return reason
    fixed_ids = dict(evidence.fixed_school.parent.cohort.capability_groups)
    if any(capability in fixed_ids and evidence.fixed_school.delta(capability) < 0
           for capability in state.unqualified_debt_capability_ids):
        return "CERTIFIED_SURFACE_DEBT_IDENTITY_REQUIRED"
    if debt_limit_exceeded(state, evidence.fixed_school):
        return "CERTIFIED_SURFACE_DEBT_LIMIT"
    if repair_due_without_progress(state, evidence.fixed_school):
        return "CERTIFIED_SURFACE_REPAIR_DUE"
    relaxable = {
        "PROTECTED_CAPABILITY_REGRESSION", "SAME_GRADE_NET_REGRESSION",
        "FIXED_LESSON_GRADE_REGRESSION", "ACTIVE_SCHOOL_GRADE_REGRESSION",
        "WHOLE_SCHOOL_NET_REGRESSION"}
    if reason not in relaxable:
        return reason
    census = dict(evidence.policy.capability_groups)
    measured = (tuple(coverage.measured_capabilities)
                if coverage is not None else tuple(census))
    lesson = tuple(capability for capability in measured
                   if census[capability] == census[target])
    if (_mastery_debt_utility(evidence.fixed_school, measured) <= 0
            or _mastery_debt_utility(evidence.fresh_lesson, lesson) <= 0):
        return reason
    return "PAIRED_SCREEN_WITHIN_BUDGET"
