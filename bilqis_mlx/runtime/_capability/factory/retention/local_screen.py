"""Ordinary C05 screen over one target's generation-bound protection plan."""
from bilqis_mlx.runtime._factory_parent_assessment_cache import (
    factory_parent_assessment_identity,
    use_parent_assessment,
)
from bilqis_mlx.runtime._factory_retention_support import (
    C05_PROBE_EACH,
    C05_PROTECTED_REFERENCE_LOSS,
    _cohort,
)
from bilqis_mlx.runtime.baseline.currentness import (
    BaselineComparisonEpoch, baseline_coverage,
)
from bilqis_mlx.runtime.baseline.lifecycle import BaselineLedger
from bilqis_mlx.runtime.capability_evaluation import _invalid
from bilqis_mlx.runtime.capability_retention import EvidenceKind, case_census_digest
from bilqis_mlx.runtime.capability_retention_foundation import FoundationRetentionPolicy
from bilqis_mlx.runtime.factory_complete_solver import factory_complete_solver
from bilqis_mlx.semantics.domains import contract_digest

from .local_evaluation import evaluate_foundation_local_candidate


def _comparison_epoch(release, plan, target_plan, instruments, parent, cache):
    target_cases = tuple(
        item.case for item in instruments
        if item.case.capability_id == target_plan.target_capability_id)
    if not target_cases:
        _invalid("BAMF_C05_RETENTION_PROTECTION_SCOPE_INVALID")
    return BaselineComparisonEpoch(
        release.release_sha256,
        release.semantic_catalog_sha256,
        plan.rubric_sha256,
        target_plan.comparison_scope_sha256,
        plan.policy_epoch_sha256,
        plan.source_sha256,
        cache.source_authority_registry_sha256,
        contract_digest(parent.correction_frontier),
        contract_digest(parent.evaluation_contract),
        case_census_digest(target_cases),
        plan.evidence_stage,
    )


def foundation_local_retention_screen(
        source_context, parent, candidate_bundle, artifact_path,
        release, plan, target_plan, training, instruments, cache, *,
        observer=None):
    """Evaluate exactly target + compiled local protected capabilities."""
    groups = target_plan.evaluated_capability_groups
    expected = set(target_plan.evaluated_capability_ids)
    observed = {item.case.capability_id for item in instruments}
    if observed != expected:
        _invalid("BAMF_C05_RETENTION_PROTECTION_SCOPE_INVALID")
    epoch = _comparison_epoch(
        release, plan, target_plan, instruments, parent, cache)
    ledger = BaselineLedger.from_optional_record(parent.baseline_evidence)
    coverage = baseline_coverage(
        ledger, epoch, target_plan.evaluated_capability_groups)
    policy = FoundationRetentionPolicy(
        groups,
        tuple(dict.fromkeys(group for _capability, group in groups)),
        tuple((capability, C05_PROTECTED_REFERENCE_LOSS)
              for capability in target_plan.protected_capability_ids),
        C05_PROBE_EACH,
        case_census_digest(tuple(item.case for item in instruments)),
        coverage,
    )
    cohort = _cohort(
        EvidenceKind.FIXED_SCHOOL, instruments, groups, release, policy, training,
        rubric_sha256=plan.rubric_sha256,
        scope_sha256=target_plan.evaluation_scope_sha256,
        source_sha256=plan.source_sha256)
    parent_solver, parent_generation = factory_complete_solver(
        source_context, parent, artifact_path, instruments)
    parent_identity = factory_parent_assessment_identity(
        source_context, parent, cache, cohort, parent_solver, parent_generation)
    parent_assessment, parent_cache = use_parent_assessment(
        parent_identity, parent_solver, cohort, parent_generation, scope=cache)
    candidate_solver, candidate_generation = factory_complete_solver(
        source_context, candidate_bundle, artifact_path, instruments)
    decision = evaluate_foundation_local_candidate(
        parent_solver, candidate_solver, target_plan.target_capability_id,
        policy, cohort, parent_generation, candidate_generation,
        retention_protection_plan_sha256=plan.digest,
        evaluated_capability_ids=target_plan.evaluated_capability_ids,
        parent_assessment=parent_assessment,
        **({"observer": observer} if observer is not None else {}))
    return (
        decision, parent, candidate_bundle, parent_cache,
        epoch.identity(target_plan.target_capability_id),
    )


__all__ = ("foundation_local_retention_screen",)
