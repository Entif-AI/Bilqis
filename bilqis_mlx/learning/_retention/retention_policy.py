"""Shared pure retention precedence and proportional loss arithmetic."""


def scaled_loss_allowance(total: int, reference_loss: int, probe_each: int) -> int:
    return min(total, total * reference_loss // probe_each)


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
