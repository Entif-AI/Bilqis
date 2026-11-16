"""Shared pure retention precedence and stage-authoritative decision policy."""
from dataclasses import dataclass
from enum import Enum
from fractions import Fraction
from bilqis_mlx.errors import ErrorBus, SCHOOL


MASTERY_DEBT_POWER = 2


class RetentionDecisionLaw(str, Enum):
    FOUNDATION_MASTERY_DEBT = "FOUNDATION_MASTERY_DEBT"
    STRICT_PROPORTIONAL = "STRICT_PROPORTIONAL"


@dataclass(frozen=True)
class RetentionStagePolicy:
    """Versioned mapping from declared evidence stage to retention economics."""

    stage_laws: tuple[tuple[str, RetentionDecisionLaw], ...] = (
        ("FOUNDATION_ACQUISITION", RetentionDecisionLaw.FOUNDATION_MASTERY_DEBT),
        ("STRICT_GENERALIZATION", RetentionDecisionLaw.STRICT_PROPORTIONAL),
    )
    schema_version: str = "bilqis.c05.stage-retention-policy/v1"

    def __post_init__(self):
        if (self.schema_version != "bilqis.c05.stage-retention-policy/v1"
                or len(self.stage_laws) != len(dict(self.stage_laws))
                or any(not isinstance(stage, str) or not stage
                       or not isinstance(law, RetentionDecisionLaw)
                       for stage, law in self.stage_laws)):
            _invalid("retention stage policy invalid")

    def law_for(self, evidence_stage) -> RetentionDecisionLaw:
        stage = getattr(evidence_stage, "value", evidence_stage)
        law = dict(self.stage_laws).get(stage)
        if law is None:
            _invalid("retention evidence stage unsupported")
        return law


def stage_retention_policy() -> RetentionStagePolicy:
    """Return the immutable current C05 evidence-stage decision contract."""
    return RetentionStagePolicy()


def decision_law_for_stage(evidence_stage) -> RetentionDecisionLaw:
    return stage_retention_policy().law_for(evidence_stage)


def _invalid(reason: str) -> None:
    ErrorBus.Raise(SCHOOL.MODEL_TOPOLOGY.INVALID, reason=reason)


def scaled_loss_allowance(total: int, reference_loss: int, probe_each: int) -> int:
    return min(total, total * reference_loss // probe_each)


def _mastery_debt_utility(scores: dict, capabilities=None) -> tuple[Fraction, dict]:
    """Value one normalized vote per capability by squared distance from mastery."""
    if not isinstance(scores, dict):
        _invalid("retention mastery-debt scores invalid")
    selected = tuple(sorted(scores if capabilities is None else capabilities))
    if not selected or any(capability not in scores for capability in selected):
        _invalid("retention mastery-debt scope invalid")
    net = Fraction()
    details = {}
    for capability in selected:
        score = scores[capability]
        if not isinstance(score, dict):
            _invalid("retention mastery-debt score invalid")
        before, after, total = (score.get(name) for name in ("before", "after", "total"))
        if (any(type(value) is not int for value in (before, after, total))
                or total <= 0 or not 0 <= before <= total
                or not 0 <= after <= total):
            _invalid("retention mastery-debt score invalid")
        before_accuracy = Fraction(before, total)
        after_accuracy = Fraction(after, total)
        before_debt = Fraction(1) - before_accuracy
        after_debt = Fraction(1) - after_accuracy
        utility = before_debt ** MASTERY_DEBT_POWER - after_debt ** MASTERY_DEBT_POWER
        net += utility
        details[capability] = {
            "before_accuracy": round(float(before_accuracy), 12),
            "after_accuracy": round(float(after_accuracy), 12),
            "before_debt": round(float(before_debt), 12),
            "after_debt": round(float(after_debt), 12),
            "utility_delta": round(float(utility), 12),
        }
    return net, {
        "net": round(float(net), 12),
        "positive": net > 0,
        "capability_count": len(selected),
        "capabilities": details,
    }


def mastery_debt_utility(scores: dict, capabilities=None) -> dict:
    """JSON-safe normalized quadratic mastery-debt utility."""
    _net, result = _mastery_debt_utility(scores, capabilities)
    return {"power": MASTERY_DEBT_POWER, **result}


def retention_reason(*, no_target_gain, same_grade_net_gain,
                      fixed_grade_regression, active_grade_regression,
                      whole_school_regression, frontier_measured,
                      fragile_losses, exceeded):
    if no_target_gain:
        return "NO_MEASURABLE_TARGET_GAIN"
    if not frontier_measured and fragile_losses:
        return "FRAGILE_COMPOSITION_REPLAY_REGRESSION"
    if exceeded: return "PROTECTED_CAPABILITY_REGRESSION"
    if not frontier_measured:
        if same_grade_net_gain < 0:
            return "SAME_GRADE_NET_REGRESSION"
        if same_grade_net_gain == 0:
            return "NO_POSITIVE_SAME_GRADE_GAIN"
        if fixed_grade_regression:
            return "FIXED_GRADE_COHORT_REGRESSION"
        return "PAIRED_SCREEN_WITHIN_BUDGET"
    if same_grade_net_gain < 0:
        return "SAME_GRADE_NET_REGRESSION"
    if fixed_grade_regression:
        return "FIXED_LESSON_GRADE_REGRESSION"
    if active_grade_regression:
        return "ACTIVE_SCHOOL_GRADE_REGRESSION"
    if whole_school_regression:
        return "WHOLE_SCHOOL_NET_REGRESSION"
    return "PAIRED_SCREEN_WITHIN_BUDGET"
