"""C05 retention policy projection from comparable baseline coverage."""
from bilqis_mlx.runtime.capability_retention import (
    EvidenceKind,
    EvidenceStage,
    RetentionPolicy,
    case_census_digest,
)

from bilqis_mlx.runtime._factory_retention_support import (
    C05_PROBE_EACH,
    C05_PROTECTED_REFERENCE_LOSS,
    _cohort,
)
from bilqis_mlx.runtime.capability_evaluation import _invalid


def policy_and_cohorts(
    release, groups, target_capability, target_group, training,
    target_instruments, lesson_instruments, fixed_instruments, baseline_coverage,
    protected_capabilities, *, evidence_stage=EvidenceStage.FOUNDATION_ACQUISITION,
    rubric_sha256=None, scope_sha256=None, source_sha256=None,
):
    required = (
        (EvidenceKind.FRESH_TARGET,
         case_census_digest(tuple(item.case for item in target_instruments))),
        (EvidenceKind.FRESH_LESSON,
         case_census_digest(tuple(item.case for item in lesson_instruments))),
        (EvidenceKind.FIXED_SCHOOL,
         case_census_digest(tuple(item.case for item in fixed_instruments))),
    )
    protected = tuple(protected_capabilities)
    admitted = {capability for capability, _group in groups}
    if (target_capability in protected
            or len(set(protected)) != len(protected)
            or not set(protected) <= admitted - {target_capability}):
        _invalid("BAMF_C05_RETENTION_PROTECTION_SCOPE_INVALID")
    policy = RetentionPolicy(
        groups,
        tuple(dict.fromkeys(group for _, group in groups)),
        tuple((capability, C05_PROTECTED_REFERENCE_LOSS) for capability in protected),
        C05_PROBE_EACH,
        required,
        baseline_coverage,
    )
    target_cohort = _cohort(
        EvidenceKind.FRESH_TARGET, target_instruments,
        ((target_capability, target_group),), release, policy, training,
        evidence_stage=evidence_stage, rubric_sha256=rubric_sha256,
        scope_sha256=scope_sha256, source_sha256=source_sha256)
    lesson_groups = tuple(pair for pair in groups if pair[1] == target_group)
    lesson_cohort = _cohort(
        EvidenceKind.FRESH_LESSON, lesson_instruments,
        lesson_groups, release, policy, training, evidence_stage=evidence_stage,
        rubric_sha256=rubric_sha256, scope_sha256=scope_sha256,
        source_sha256=source_sha256)
    fixed_cohort = _cohort(
        EvidenceKind.FIXED_SCHOOL, fixed_instruments,
        groups, release, policy, training, evidence_stage=evidence_stage,
        rubric_sha256=rubric_sha256, scope_sha256=scope_sha256,
        source_sha256=source_sha256)
    return policy, (target_cohort, lesson_cohort, fixed_cohort)


__all__ = ("policy_and_cohorts",)
