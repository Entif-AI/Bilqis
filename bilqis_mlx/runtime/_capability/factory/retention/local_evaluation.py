"""Ordinary C05 foundation evaluation over exact local protection scope."""
from bilqis_mlx.semantics.domains import contract_digest

from bilqis_mlx.runtime.capability_evaluation import Assessment, _invalid, _sha
from bilqis_mlx.runtime.capability_retention import Decision
from bilqis_mlx.runtime.capability_retention_foundation import (
    FoundationRetentionPolicy,
    _evaluate_fixed_school,
    _fixed_cohort_contract,
)


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


__all__ = ("evaluate_foundation_local_candidate",)
