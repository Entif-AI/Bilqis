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
    C05_PROBE_EACH, C05_PROTECTED_REFERENCE_LOSS, _cohort, _earned_protected_capabilities,
    _fresh_rows, _instruments, _owner_seed, _policy_and_cohorts,
)
from bilqis_mlx.runtime._factory_identity_evaluation import _require_factory_evaluation
from bilqis_mlx.runtime.baseline.lifecycle import (
    BaselineComparisonIdentity, BaselineLedger, _issue_factory_baseline_transition,
    apply_factory_baseline_transition,
)
from bilqis_mlx.runtime.factory_complete_solver import factory_complete_solver


def foundation_retention_screen(
    source_context, parent, candidate_bundle, artifact_path, target_capability,
    release, groups, training, fixed_instruments, cache, evidence_stage, *, observer=None,
):
    fixed_cases = tuple(item.case for item in fixed_instruments)
    protected = _earned_protected_capabilities(parent, target_capability)
    admitted = {capability for capability, _ in groups}
    if not set(protected) <= admitted - {target_capability}:
        _invalid("BAMF_C05_EARNED_PROTECTION_NOT_ADMITTED")
    policy = FoundationRetentionPolicy(
        groups, tuple(dict.fromkeys(group for _, group in groups)),
        tuple((capability, C05_PROTECTED_REFERENCE_LOSS) for capability in protected),
        C05_PROBE_EACH, case_census_digest(fixed_cases))
    fixed_cohort = _cohort(
        EvidenceKind.FIXED_SCHOOL, fixed_instruments, groups, release, policy, training,
        evidence_stage=evidence_stage)
    parent_solver, parent_generation = factory_complete_solver(
        source_context, parent, artifact_path, fixed_instruments)
    parent_identity = factory_parent_assessment_identity(
        source_context, parent, cache, fixed_cohort, parent_solver, parent_generation)
    parent_assessment, parent_assessment_cache = use_parent_assessment(
        parent_identity, parent_solver, fixed_cohort, parent_generation, scope=cache)
    comparison = BaselineComparisonIdentity(
        target_capability, parent_identity.factory_release_sha256,
        parent_identity.semantic_catalog_sha256, fixed_cohort.rubric_sha256,
        fixed_cohort.scope_sha256, fixed_cohort.policy_sha256, fixed_cohort.source_sha256,
        parent_identity.source_authority_registry_sha256,
        parent_identity.correction_frontier_sha256,
        parent_identity.evaluation_contract_sha256, parent_identity.fixed_cohort_sha256,
        fixed_cohort.evidence_stage.value)
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
    policy, cohorts = _policy_and_cohorts(
        release, groups, target_capability, target_group, training, target_instruments,
        lesson_instruments, fixed_instruments, evidence_stage=evidence_stage)
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
    return decision, parent, candidate_bundle, cache, None


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
