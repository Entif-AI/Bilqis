"""Ordinary C05 screen over one target's generation-bound protection plan."""
import time
from bilqis_mlx.learning._atlas_candidate.identity_binding import (
    candidate_identity_for_canonical_consumer,
)
from bilqis_mlx.runtime._factory_parent_assessment_cache import (
    factory_parent_assessment_identity,
    use_parent_assessment,
)
from bilqis_mlx.runtime._factory_retention_support import (
    C05_PROBE_EACH,
    C05_PROTECTED_REFERENCE_LOSS,
    C05_FRESH_TARGET_SEED_OFFSET,
    _cohort, _fresh_rows, _instruments, _owner_seed,
)
from bilqis_mlx.runtime.baseline.currentness import (
    BaselineComparisonEpoch, BaselineCoverage, baseline_coverage,
)
from bilqis_mlx.runtime.baseline.lifecycle import BaselineLedger
from bilqis_mlx.runtime.capability_evaluation import _invalid
from bilqis_mlx.runtime.capability_retention import (
    AssessmentPair, EvidenceKind,
    case_census_digest, evaluate_capabilities,
)
from bilqis_mlx.runtime.capability_retention_foundation import FoundationRetentionPolicy
from bilqis_mlx.runtime.capability_retention_foundation_runtime import (
    observed_assessment,
)
from bilqis_mlx.runtime.factory_complete_solver import factory_complete_solver
from bilqis_mlx.semantics.domains import contract_digest

from .local_evaluation import (
    evaluate_target_gate, finalize_target_first_local_candidate,
)


def _observe(observer, **fields):
    if observer is None:
        return
    try:
        observer(fields)
    except Exception:
        # Retention profiling is observational and cannot gate C05 authority.
        pass


def _elapsed(observer, field, started):
    _observe(observer, **{field: max(0.0, time.perf_counter() - started)})


def _solver_profile(observer, prefix, *solvers):
    shared = scalar = 0
    for solver in solvers:
        telemetry_for = getattr(solver, "telemetry_for", None)
        if not callable(telemetry_for):
            continue
        try:
            telemetry = telemetry_for()
        except Exception:
            continue
        if not isinstance(telemetry, dict):
            continue
        shared += int(telemetry.get("shared_backbone_launches", 0) or 0)
        scalar += int(telemetry.get("scalar_neural_launches", 0) or 0)
    _observe(
        observer,
        **{f"{prefix}_shared_backbone_launches": shared,
           f"{prefix}_scalar_neural_launches": scalar},
    )


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


def _split_cached_rows(cached_rows, target_plan):
    by_capability = {capability: (seed, rows)
                     for capability, seed, rows in cached_rows}
    if (set(by_capability) != set(target_plan.evaluated_capability_ids)
            or len(by_capability) != len(cached_rows)):
        _invalid("BAMF_C05_RETENTION_SOURCE_CACHE_INVALID")
    target = target_plan.target_capability_id
    return by_capability[target], tuple(
        (capability, *by_capability[capability])
        for capability in target_plan.protected_capability_ids)


def _cached_instruments(
        source_context, candidate_bundle, artifact_path, cached_rows):
    result = []
    for _capability, seed, rows in cached_rows:
        result.extend(_instruments(
            source_context, candidate_bundle, artifact_path, rows,
            seed=seed, each=C05_PROBE_EACH, release_prevalidated=True))
    return tuple(result)


def _policy(groups, protected, cases, coverage):
    return FoundationRetentionPolicy(
        groups,
        tuple(dict.fromkeys(group for _capability, group in groups)),
        tuple((capability, C05_PROTECTED_REFERENCE_LOSS) for capability in protected),
        C05_PROBE_EACH, case_census_digest(cases), coverage)


def _coverage_for_groups(coverage, groups):
    capabilities = tuple(capability for capability, _group in groups)
    measured = tuple(capability for capability in capabilities
                     if capability in set(coverage.measured_capabilities))
    measured_set = set(measured)
    unmeasured = tuple(capability for capability in capabilities
                       if capability not in measured_set)
    group_names = tuple(dict.fromkeys(group for _capability, group in groups))
    return BaselineCoverage(
        measured, unmeasured,
        tuple((
            group,
            sum(capability in measured_set for capability, member in groups
                if member == group),
            sum(member == group for _capability, member in groups),
        ) for group in group_names),
        len(measured), len(capabilities), coverage.epoch_sha256)


def _local_coverage(target_coverage, target_plan, plan_sha256):
    measured = set(target_plan.protected_capability_ids)
    if target_plan.target_capability_id in set(target_coverage.measured_capabilities):
        measured.add(target_plan.target_capability_id)
    groups = target_plan.evaluated_capability_groups
    capabilities = tuple(capability for capability, _group in groups)
    measured_ordered = tuple(capability for capability in capabilities
                             if capability in measured)
    measured_set = set(measured_ordered)
    unmeasured = tuple(capability for capability in capabilities
                       if capability not in measured_set)
    group_names = tuple(dict.fromkeys(group for _capability, group in groups))
    return BaselineCoverage(
        measured_ordered, unmeasured,
        tuple((
            group,
            sum(capability in measured_set for capability, member in groups
                if member == group),
            sum(member == group for _capability, member in groups),
        ) for group in group_names),
        len(measured_ordered), len(capabilities),
        contract_digest({
            "schema": "bilqis.mlx.c05-local-baseline-coverage/v1",
            "target_epoch_sha256": target_coverage.epoch_sha256,
            "retention_protection_plan_sha256": plan_sha256,
            "evaluated_capability_ids": capabilities,
        }))


def _target_stage(
        source_context, parent, candidate_bundle, candidate_state, artifact_path,
        release, plan, target_plan, training, cached_rows, cache, observer=None):
    started = time.perf_counter()
    target = target_plan.target_capability_id
    (reference_seed, reference_rows), protected_rows = _split_cached_rows(
        cached_rows, target_plan)
    reference_target = tuple(_instruments(
        source_context, candidate_bundle, artifact_path, reference_rows,
        seed=reference_seed, each=C05_PROBE_EACH, release_prevalidated=True))
    epoch = _comparison_epoch(
        release, plan, target_plan, reference_target, parent, cache)
    ledger = BaselineLedger.from_optional_record(parent.baseline_evidence)
    target_group = ((target, target_plan.target_grade_id),)
    target_coverage = baseline_coverage(ledger, epoch, target_group)
    candidate_sha256 = candidate_identity_for_canonical_consumer(candidate_state)
    fresh_seed = _owner_seed(
        release.release_sha256, cache, target, candidate_sha256)
    target_draw = _fresh_rows(
        source_context, (target,), seed=fresh_seed + C05_FRESH_TARGET_SEED_OFFSET,
        training=training, require_independent=False)
    target_instruments = tuple(_instruments(
        source_context, candidate_bundle, artifact_path, target_draw.rows,
        seed=target_draw.seed, each=C05_PROBE_EACH))
    target_cases = tuple(item.case for item in target_instruments)
    target_policy = _policy(target_group, (), target_cases, target_coverage)
    target_cohort = _cohort(
        EvidenceKind.FRESH_TARGET, target_instruments, target_group,
        release, target_policy, training,
        rubric_sha256=plan.rubric_sha256,
        scope_sha256=target_plan.comparison_scope_sha256,
        source_sha256=plan.source_sha256)
    _observe(observer, retention_target_case_count=len(target_cases))
    _elapsed(observer, "retention_target_prepare_wall_seconds", started)

    started = time.perf_counter()
    parent_solver, parent_generation = factory_complete_solver(
        source_context, parent, artifact_path, target_instruments)
    candidate_solver, candidate_generation = factory_complete_solver(
        source_context, candidate_bundle, artifact_path, target_instruments)
    _elapsed(observer, "retention_target_solver_wall_seconds", started)

    started = time.perf_counter()
    total_assessments = 2 + (2 if target_plan.protected_capability_ids else 0)
    parent_assessment = observed_assessment(
        parent_solver, target_cohort, parent_generation, observer, 0,
        total_assessments, target, "parent", evaluator=evaluate_capabilities)
    _elapsed(observer, "retention_target_parent_wall_seconds", started)
    started = time.perf_counter()
    candidate_assessment = observed_assessment(
        candidate_solver, target_cohort, candidate_generation, observer, 1,
        total_assessments, target, "candidate", evaluator=evaluate_capabilities)
    _elapsed(observer, "retention_target_candidate_wall_seconds", started)
    _solver_profile(observer, "retention_target", parent_solver, candidate_solver)
    target_pair = AssessmentPair(parent_assessment, candidate_assessment)
    decision = evaluate_target_gate(
        target, target_policy, target_pair,
        retention_protection_plan_sha256=plan.digest)
    comparison = epoch.identity(target)
    return (
        target, protected_rows, target_instruments, target_pair,
        target_coverage, comparison, decision,
    )


def _protected_stage(
        source_context, parent, candidate_bundle, artifact_path,
        release, plan, target_plan, training, protected_rows, cache,
        target_coverage, observer=None):
    started = time.perf_counter()
    protected_instruments = _cached_instruments(
        source_context, candidate_bundle, artifact_path, protected_rows)
    protected_pair = parent_cache = None
    coverage = _local_coverage(target_coverage, target_plan, plan.digest)
    _observe(observer, retention_protected_case_count=len(protected_instruments))
    _elapsed(observer, "retention_protected_prepare_wall_seconds", started)
    if protected_instruments:
        groups = target_plan.evaluated_capability_groups
        protected_groups = tuple(
            pair for pair in groups if pair[0] in target_plan.protected_capability_ids)
        protected_coverage = _coverage_for_groups(coverage, protected_groups)
        protected_cases = tuple(item.case for item in protected_instruments)
        protected_policy = _policy(
            protected_groups, target_plan.protected_capability_ids,
            protected_cases, protected_coverage)
        protected_cohort = _cohort(
            EvidenceKind.FIXED_SCHOOL, protected_instruments, protected_groups,
            release, protected_policy, training,
            rubric_sha256=plan.rubric_sha256,
            scope_sha256=target_plan.evaluation_scope_sha256,
            source_sha256=plan.source_sha256)
        started = time.perf_counter()
        protected_parent_solver, protected_parent_generation = factory_complete_solver(
            source_context, parent, artifact_path, protected_instruments)
        parent_identity = factory_parent_assessment_identity(
            source_context, parent, cache, protected_cohort,
            protected_parent_solver, protected_parent_generation)
        _elapsed(observer, "retention_protected_parent_solver_wall_seconds", started)
        started = time.perf_counter()
        _observe(
            observer, retention_completed=2, retention_total=4,
            retention_subject="fixed_school", retention_role="parent")
        protected_parent, parent_cache = use_parent_assessment(
            parent_identity, protected_parent_solver, protected_cohort,
            protected_parent_generation, scope=cache)
        _observe(
            observer, retention_completed=3, retention_total=4,
            retention_subject="fixed_school", retention_role="parent",
            retention_stage_timing={
                "subject": "fixed_school", "role": "parent",
                "wall_seconds": max(0.0, time.perf_counter() - started),
            })
        _elapsed(observer, "retention_protected_parent_wall_seconds", started)
        _observe(observer, retention_parent_cache_reused=parent_cache.reused)

        started = time.perf_counter()
        protected_candidate_solver, protected_candidate_generation = factory_complete_solver(
            source_context, candidate_bundle, artifact_path, protected_instruments)
        _elapsed(observer, "retention_protected_candidate_solver_wall_seconds", started)
        started = time.perf_counter()
        protected_candidate = observed_assessment(
            protected_candidate_solver, protected_cohort, protected_candidate_generation,
            observer, 3, 4, "fixed_school", "candidate",
            evaluator=evaluate_capabilities)
        _elapsed(observer, "retention_protected_candidate_wall_seconds", started)
        _solver_profile(
            observer, "retention_protected",
            protected_parent_solver, protected_candidate_solver)
        protected_pair = AssessmentPair(protected_parent, protected_candidate)
    return protected_pair, parent_cache, protected_instruments, coverage


def foundation_local_retention_screen(
        source_context, parent, candidate_bundle, candidate_state, artifact_path,
        release, plan, target_plan, training, cached_rows, cache, *,
        observer=None):
    """Resolve a fresh target pair before any protected candidate inference."""
    (
        target, protected_rows, target_instruments, target_pair,
        target_coverage, comparison, decision,
    ) = _target_stage(
        source_context, parent, candidate_bundle, candidate_state, artifact_path,
        release, plan, target_plan, training, cached_rows, cache, observer)
    if decision is not None:
        return decision, parent, candidate_bundle, None, comparison, None, None

    protected_pair, parent_cache, protected_instruments, coverage = _protected_stage(
        source_context, parent, candidate_bundle, artifact_path,
        release, plan, target_plan, training, protected_rows, cache,
        target_coverage, observer)
    groups = target_plan.evaluated_capability_groups

    all_instruments = (*target_instruments, *protected_instruments)
    policy = _policy(
        groups, target_plan.protected_capability_ids,
        tuple(item.case for item in all_instruments), coverage)
    cohort = _cohort(
        EvidenceKind.FIXED_SCHOOL, all_instruments, groups, release, policy, training,
        rubric_sha256=plan.rubric_sha256,
        scope_sha256=target_plan.evaluation_scope_sha256,
        source_sha256=plan.source_sha256)
    started = time.perf_counter()
    decision = finalize_target_first_local_candidate(
        target, policy, cohort, target_pair, protected_pair,
        retention_protection_plan_sha256=plan.digest,
        evaluated_capability_ids=target_plan.evaluated_capability_ids,
        **({"observer": observer} if observer is not None else {}))
    _elapsed(observer, "retention_decision_finalize_wall_seconds", started)
    return (
        decision, parent, candidate_bundle, parent_cache, comparison,
        None, None,
    )


__all__ = ("foundation_local_retention_screen",)
