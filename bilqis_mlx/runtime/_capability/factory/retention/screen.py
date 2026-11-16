"""Private Factory-owned C05 screening and baseline issuance."""
from bilqis_mlx.learning._atlas_candidate.identity_binding import (
    candidate_identity_binding_for_state, candidate_identity_for_canonical_consumer,
)
from bilqis_mlx.runtime.capability_retention import (
    DecisionStatus, EvidenceKind, case_census_digest, evaluate_retention_candidate,
)

from bilqis_mlx.runtime.capability_evaluation import _invalid
from bilqis_mlx.runtime.capability_retention_foundation import (
    FoundationRetentionPolicy, evaluate_foundation_fixed_school_candidate,
)
from bilqis_mlx.runtime._factory_parent_assessment_cache import (
    factory_parent_assessment_identity, use_parent_assessment,
)
from bilqis_mlx.runtime._factory_retention_support import (
    C05_FRESH_LESSON_SEED_OFFSET, C05_FRESH_TARGET_SEED_OFFSET,
    C05_PROBE_EACH, C05_PROTECTED_REFERENCE_LOSS, _cohort,
    _fresh_rows, _instruments, _owner_seed,
)
from bilqis_mlx.runtime._factory_identity_evaluation import _require_factory_evaluation
from bilqis_mlx.runtime.baseline.lifecycle import (
    BaselineComparisonIdentity, BaselineLedger, _issue_factory_baseline_transition,
    apply_factory_baseline_transition,
)
from bilqis_mlx.runtime.baseline.currentness import (
    BaselineComparisonEpoch,
    baseline_coverage,
)
from bilqis_mlx.runtime.factory_complete_solver import factory_complete_solver
from bilqis_mlx.learning.retention_policy import MASTERY_DEBT_POWER
from bilqis_mlx.semantics.domains import contract_digest

from .policy import policy_and_cohorts


def _policy_epoch_sha256(evidence_stage):
    return contract_digest({
        "schema": "bilqis.mlx.c05-retention-policy-epoch/v1",
        "evidence_stage": evidence_stage.value,
        "foundation_policy_schema": "bilqis.c05.foundation-retention-policy/v2",
        "strict_policy_schema": "bilqis.c05.retention-policy/v2",
        "probe_each": C05_PROBE_EACH,
        "protected_reference_loss": C05_PROTECTED_REFERENCE_LOSS,
        "mastery_debt_power": MASTERY_DEBT_POWER,
    })


def _comparison_epoch(
        release, groups, fixed_instruments, parent, cache, evidence_stage):
    fixed_cases = tuple(item.case for item in fixed_instruments)
    rubric = contract_digest(tuple(
        (item.grade_id, item.assessment_blueprint_sha256)
        for item in release.execution_plan.grades))
    scope = contract_digest((
        release.execution_plan.curriculum_sha256,
        release.execution_plan.profile_id,
        groups,
    ))
    return BaselineComparisonEpoch(
        release.release_sha256,
        release.semantic_catalog_sha256,
        rubric,
        scope,
        _policy_epoch_sha256(evidence_stage),
        release.execution_plan.projection_digests.source,
        cache.source_authority_registry_sha256,
        contract_digest(parent.correction_frontier),
        contract_digest(parent.evaluation_contract),
        case_census_digest(fixed_cases),
        evidence_stage.value,
    )


def foundation_retention_screen(
    source_context, parent, candidate_bundle, artifact_path, target_capability,
    release, groups, training, fixed_instruments, cache, evidence_stage, *, observer=None,
):
    fixed_cases = tuple(item.case for item in fixed_instruments)
    ledger = BaselineLedger.from_optional_record(parent.baseline_evidence)
    epoch = _comparison_epoch(
        release, groups, fixed_instruments, parent, cache, evidence_stage)
    coverage = baseline_coverage(ledger, epoch, groups)
    protected = coverage.protected_capabilities(target_capability)
    admitted = {capability for capability, _ in groups}
    if not set(protected) <= admitted - {target_capability}:
        _invalid("BAMF_C05_EARNED_PROTECTION_NOT_ADMITTED")
    policy = FoundationRetentionPolicy(
        groups, tuple(dict.fromkeys(group for _, group in groups)),
        tuple((capability, C05_PROTECTED_REFERENCE_LOSS) for capability in protected),
        C05_PROBE_EACH, case_census_digest(fixed_cases), coverage)
    fixed_cohort = _cohort(
        EvidenceKind.FIXED_SCHOOL, fixed_instruments, groups, release, policy, training,
        evidence_stage=evidence_stage)
    parent_solver, parent_generation = factory_complete_solver(
        source_context, parent, artifact_path, fixed_instruments)
    parent_identity = factory_parent_assessment_identity(
        source_context, parent, cache, fixed_cohort, parent_solver, parent_generation)
    parent_assessment, parent_assessment_cache = use_parent_assessment(
        parent_identity, parent_solver, fixed_cohort, parent_generation, scope=cache)
    comparison = epoch.identity(target_capability)
    candidate_solver, candidate_generation = factory_complete_solver(
        source_context, candidate_bundle, artifact_path, fixed_instruments)
    decision = evaluate_foundation_fixed_school_candidate(
        parent_solver, candidate_solver, target_capability, policy, fixed_cohort,
        parent_generation, candidate_generation, parent_assessment=parent_assessment,
        **({"observer": observer} if observer is not None else {}))
    return decision, parent, candidate_bundle, parent_assessment_cache, comparison


def adaptive_retention_screen(
    source_context, parent, candidate_bundle, candidate_state, artifact_path,
    target_capability, target_group, lesson_capabilities, release, groups, training,
    fixed_instruments, cache, evidence_stage, *, observer=None,
):
    candidate_sha256 = candidate_identity_for_canonical_consumer(candidate_state)
    fresh_seed = _owner_seed(release.release_sha256, cache, target_capability, candidate_sha256)
    target_draw = _fresh_rows(
        source_context, (target_capability,), seed=fresh_seed + C05_FRESH_TARGET_SEED_OFFSET,
        training=training)
    lesson_draw = _fresh_rows(
        source_context, lesson_capabilities, seed=fresh_seed + C05_FRESH_LESSON_SEED_OFFSET,
        training=training)
    target_instruments = _instruments(
        source_context, candidate_bundle, artifact_path, target_draw.rows,
        seed=target_draw.seed, each=C05_PROBE_EACH)
    lesson_instruments = _instruments(
        source_context, candidate_bundle, artifact_path, lesson_draw.rows,
        seed=lesson_draw.seed, each=C05_PROBE_EACH)
    ledger = BaselineLedger.from_optional_record(parent.baseline_evidence)
    epoch = _comparison_epoch(
        release, groups, fixed_instruments, parent, cache, evidence_stage)
    coverage = baseline_coverage(ledger, epoch, groups)
    policy, cohorts = policy_and_cohorts(
        release, groups, target_capability, target_group, training, target_instruments,
        lesson_instruments, fixed_instruments, coverage, evidence_stage=evidence_stage)
    all_instruments = tuple(dict(
        (item.case.case_id, item)
        for item in (*target_instruments, *lesson_instruments, *fixed_instruments)).values())
    parent_solver, parent_generation = factory_complete_solver(
        source_context, parent, artifact_path, all_instruments)
    candidate_solver, candidate_generation = factory_complete_solver(
        source_context, candidate_bundle, artifact_path, all_instruments)
    decision = evaluate_retention_candidate(
        parent_solver, candidate_solver, target_capability, policy, cohorts,
        parent_generation, candidate_generation,
        **({"observer": observer} if observer is not None else {}))
    return decision, parent, candidate_bundle, cache, epoch.identity(target_capability)


def bind_factory_evaluation_issuer(raw_issue, evidence_stage):
    """Bind issuance to Factory-owned screens without exporting a mint."""
    def issue(result):
        from bilqis_mlx.runtime.bamf_bundle.genesis.records import (
            successor_candidate_identity_digest,
        )
        from bilqis_mlx.runtime.bamf_bundle.motif.transition import (
            is_motif_allocation_transition,
        )
        decision, parent, candidate, cache, comparison = result
        generation_authority = (
            successor_candidate_identity_digest(candidate)
            if is_motif_allocation_transition(getattr(candidate, "transition", {})) else None)
        baseline = BaselineLedger.from_optional_record(parent.baseline_evidence)
        baseline_transition = None
        if decision.status is DecisionStatus.ELIGIBLE and comparison is not None:
            baseline_transition = _issue_factory_baseline_transition(
                comparison, run_id=parent.run_id, accepted_generation=parent.generation + 1,
                accepted_parent_manifest_sha256=candidate.parent_manifest_sha256,
                accepted_candidate_sha256=candidate_identity_for_canonical_consumer(
                    candidate.retained_state),
                decision_evidence_sha256=decision.evidence_sha256,
                parent_ledger_sha256=baseline.digest)
            baseline = apply_factory_baseline_transition(baseline, baseline_transition)
        return raw_issue(
            decision, candidate_identity_for_canonical_consumer(parent.retained_state),
            candidate_identity_for_canonical_consumer(candidate.retained_state),
            generation_authority, cache, parent_state=parent.retained_state,
            candidate_state=candidate.retained_state,
            parent_binding=candidate_identity_binding_for_state(parent.retained_state),
            candidate_binding=candidate_identity_binding_for_state(candidate.retained_state),
            baseline_transition=baseline_transition, baseline_ledger=baseline)

    def foundation(*args, **kwargs):
        return issue(foundation_retention_screen(
            *args, evidence_stage=evidence_stage, **kwargs))

    def adaptive(*args, **kwargs):
        return issue(adaptive_retention_screen(
            *args, evidence_stage=evidence_stage, **kwargs))
    return foundation, adaptive


def bind_factory_baseline_successor(evaluation, candidate):
    """Attach only the C05-owned prospective baseline result to its exact successor."""
    from dataclasses import replace
    from bilqis_mlx.runtime.bamf_bundle.records import BamfBundleCandidate

    _require_factory_evaluation(evaluation)
    evaluation.__post_init__()
    if type(candidate) is not BamfBundleCandidate:
        _invalid("BAMF_C05_BASELINE_SUCCESSOR_INVALID")
    transition = evaluation.baseline_transition
    if transition is not None:
        measurement = transition.measurement
        if (candidate.run_id != measurement.run_id
                or candidate.generation != measurement.accepted_generation
                or candidate.parent_manifest_sha256 != measurement.accepted_parent_manifest_sha256
                or candidate_identity_for_canonical_consumer(candidate.retained_state)
                != measurement.accepted_candidate_sha256):
            _invalid("BAMF_C05_BASELINE_SUCCESSOR_INVALID")
    return replace(candidate, baseline_evidence=evaluation.baseline_ledger.to_record())
