"""Reproducible timing witness for #1166 parent fixed-school reuse."""
from __future__ import annotations

from dataclasses import replace
import json
from time import perf_counter_ns

from bilqis_mlx.runtime.capability_retention import CompleteSolver, EvidenceStage
from bilqis_mlx.runtime.capability_retention_foundation import (
    FoundationRetentionPolicy, evaluate_foundation_fixed_school_candidate,
)
from bilqis_mlx.runtime._factory_parent_assessment_cache import (
    ParentAssessmentCacheIdentity,
    clear_parent_assessment_cache,
    use_parent_assessment,
)
from bilqis_mlx.runtime.tests.capability.capability_retention_helpers import (
    PARENT, _screen_inputs,
)
from bilqis_mlx.semantics.domains import contract_digest


def _identity(fixed):
    return ParentAssessmentCacheIdentity(
        run_id="timing-witness",
        accepted_generation=7,
        accepted_manifest_sha256="1" * 64,
        accepted_generation_binding=PARENT,
        parent_generation_sha256=PARENT,
        parent_candidate_sha256="3" * 64,
        factory_release_sha256="4" * 64,
        semantic_catalog_sha256="5" * 64,
        source_authority_registry_sha256="6" * 64,
        fixed_cohort_sha256=contract_digest(fixed),
        rubric_sha256=fixed.rubric_sha256,
        source_sha256=fixed.source_sha256,
        policy_sha256=fixed.policy_sha256,
        implementation_sha256="7" * 64,
        topology_sha256="8" * 64,
        extents_sha256="9" * 64,
        correction_frontier_sha256="a" * 64,
        semantic_abi_sha256="b" * 64,
        compiler_features_sha256="c" * 64,
        evaluation_contract_sha256="d" * 64,
        evaluator_contract_sha256="e" * 64,
    )


def main():
    parent_solver, candidate_solver, target, _, cohorts = _screen_inputs(
        protected_loss=12)
    source = cohorts[2]
    groups = source.capability_groups
    policy = FoundationRetentionPolicy(
        groups,
        tuple(dict.fromkeys(group for _, group in groups)),
        tuple((capability, 1) for capability, _ in groups
              if capability != target),
        6,
        source.expected_case_digest,
    )
    fixed = replace(
        source,
        policy_sha256=policy.digest(),
        evidence_stage=EvidenceStage.FOUNDATION_ACQUISITION,
    )
    parent_calls, candidate_calls = [], []

    def parent_context(goal, generation):
        parent_calls.append(goal.goal_id)
        return parent_solver.context_for(goal, generation)

    def candidate_context(goal, generation):
        candidate_calls.append(goal.goal_id)
        return candidate_solver.context_for(goal, generation)

    parent = CompleteSolver(parent_context, parent_solver.budget)
    candidate = CompleteSolver(candidate_context, candidate_solver.budget)
    identity = _identity(fixed)
    clear_parent_assessment_cache()

    started = perf_counter_ns()
    first_parent, first_receipt = use_parent_assessment(
        identity, parent, fixed, PARENT)
    first = evaluate_foundation_fixed_school_candidate(
        parent, candidate, target, policy, fixed, PARENT, "f" * 64,
        parent_assessment=first_parent)
    first_ns = perf_counter_ns() - started
    first_parent_calls = len(parent_calls)
    first_candidate_calls = len(candidate_calls)

    started = perf_counter_ns()
    second_parent, second_receipt = use_parent_assessment(
        identity, parent, fixed, PARENT)
    second = evaluate_foundation_fixed_school_candidate(
        parent, candidate, target, policy, fixed, PARENT, "f" * 64,
        parent_assessment=second_parent)
    second_ns = perf_counter_ns() - started

    result = {
        "schema": "bilqis.mlx.c05-parent-assessment-cache-timing/v1",
        "fixed_case_count": len(fixed.cases),
        "first_screen_ns": first_ns,
        "second_screen_ns": second_ns,
        "second_over_first": second_ns / first_ns,
        "parent_context_calls_first": first_parent_calls,
        "parent_context_calls_total": len(parent_calls),
        "candidate_context_calls_first": first_candidate_calls,
        "candidate_context_calls_total": len(candidate_calls),
        "first_cache_reused": first_receipt.reused,
        "second_cache_reused": second_receipt.reused,
        "cache_entry_stable": (
            first_receipt.cache_entry_sha256
            == second_receipt.cache_entry_sha256),
        "decision_equal": first == second,
        "evidence_sha_equal": first.evidence_sha256 == second.evidence_sha256,
    }
    print(json.dumps(result, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
