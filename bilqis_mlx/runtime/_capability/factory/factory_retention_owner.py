"""Production C05 owner: Factory cohorts, policy, solvers and paired screen."""
from __future__ import annotations

from pathlib import Path
from dataclasses import dataclass

from bilqis_mlx.fixed_frontier import load_frontier_cohort
from bilqis_mlx.learning.atlas_candidate import CandidateTransaction, resolve_candidate
from bilqis_mlx.learning.atlas_package_import import PackageImportTransaction
from bilqis_mlx.learning.atlas_acceptance import candidate_identity_digest
from bilqis_mlx.runtime.atlas_training_authority import BamfTrainingAuthority
from bilqis_mlx.runtime.bamf_bundle import BamfBundleCandidate
from bilqis_mlx.runtime.bamf_bundle.admission import (
    bind_accepted_execution_cache, derive_successor_bundle,
    load_accepted_generation,
)
from bilqis_mlx.runtime.capability_retention import (
    Decision, EvidenceKind, EvidenceStage, EvaluationCohort, RetentionPolicy,
    case_census_digest, evaluate_capabilities, evaluate_retention_candidate,
)
from bilqis_mlx.semantics.domains import contract_digest
from bilqis_mlx.state_dag import read_current
from bilqis_mlx.fixed_frontier import frontier_exam
from bilqis_mlx.runtime.source_execution import _source_family

from .capability_evaluation import _invalid
from .capability_retention_foundation import (
    FoundationRetentionPolicy, evaluate_foundation_fixed_school_candidate,
)
from .factory_complete_solver import (
    FactoryEvaluationInstrument, _factory_evaluation_instrument, _generation,
    factory_complete_solver,
)
from .factory_fixed_school import _bamf_fixed_school_cohort


CURRENT_EVIDENCE_STAGE = EvidenceStage.FOUNDATION_ACQUISITION
SHA256_HEX_LENGTH = 64


def _new_factory_evaluation_owner():
    """Keep live C05 evaluation authority in closure-owned object identity."""
    issued = {}

    def require(value):
        if issued.get(id(value)) is not value:
            _invalid("BAMF_C05_FACTORY_EVALUATION_INVALID")
        return value

    def issue(decision, parent, candidate):
        from bilqis_mlx.runtime.bamf_bundle.genesis.records import (
            successor_candidate_identity_digest,
        )
        from bilqis_mlx.runtime.bamf_bundle.motif.transition import (
            is_motif_allocation_transition,
        )
        item = object.__new__(FactoryRetentionEvaluation)
        generation_authority = (
            successor_candidate_identity_digest(candidate)
            if is_motif_allocation_transition(getattr(candidate, "transition", {}))
            else None)
        for name, value in (
            ("decision", decision),
            ("parent_candidate_sha256", candidate_identity_digest(parent.retained_state)),
            ("candidate_candidate_sha256", candidate_identity_digest(candidate.retained_state)),
            ("candidate_generation_authority_sha256", generation_authority),
        ):
            object.__setattr__(item, name, value)
        issued[id(item)] = item
        item.__post_init__()
        return item

    return require, issue


@dataclass(frozen=True, init=False)
class FactoryRetentionEvaluation:
    """Unforgeable evidence that the Factory-owned C05 screen actually ran."""
    decision: Decision
    parent_candidate_sha256: str
    candidate_candidate_sha256: str
    candidate_generation_authority_sha256: str | None

    def __init__(self, *args, **kwargs):
        _invalid("BAMF_C05_FACTORY_EVALUATION_CALLER_CONSTRUCTION_FORBIDDEN")

    def __post_init__(self):
        _require_factory_evaluation(self)
        if (type(self.decision) is not Decision
                or not all(isinstance(value, str)
                           and len(value) == SHA256_HEX_LENGTH
                           for value in (self.parent_candidate_sha256,
                                         self.candidate_candidate_sha256))
                or (self.candidate_generation_authority_sha256 is not None
                    and (not isinstance(self.candidate_generation_authority_sha256, str)
                         or len(self.candidate_generation_authority_sha256)
                         != SHA256_HEX_LENGTH))):
            _invalid("BAMF_C05_FACTORY_EVALUATION_INVALID")


_require_factory_evaluation, _raw_issue_owner_evaluation = _new_factory_evaluation_owner()



from ._factory_retention_support import (
    C05_FRESH_LESSON_SEED_OFFSET, C05_FRESH_TARGET_SEED_OFFSET,
    C05_MAX_FRESH_DRAWS, C05_PROBE_EACH, C05_PROTECTED_REFERENCE_LOSS,
    _candidate_from_live_parent, _cohort, _fresh_rows, _instruments,
    _owner_seed, _package_import_from_live_parent, _policy_and_cohorts,
    _training_exclusions,
)

def _fixed_school_instruments(
    source_context, candidate_bundle, artifact_path, run_dir, release, *,
    parent, cache,
):
    if parent.run_identity is not None:
        fixed = _bamf_fixed_school_cohort(
            source_context, run_dir,
            expected_parent_manifest_sha256=cache.accepted_manifest_sha256)
    else:
        receipt = read_current(run_dir)
        if receipt.get("factory_release_sha256") != release.release_sha256:
            _invalid("BAMF_C05_FACTORY_RELEASE_DRIFT")
        fixed_exam = frontier_exam(receipt)
        fixed = load_frontier_cohort(run_dir, fixed_exam)
        if fixed is None:
            _invalid("BAMF_C05_FIXED_SCHOOL_COHORT_REQUIRED")
        if fixed_exam.get("factory_release_sha256") != release.release_sha256:
            _invalid("BAMF_C05_FIXED_SCHOOL_RELEASE_DRIFT")
    return _instruments(
        source_context, candidate_bundle, artifact_path, fixed.rows,
        seed=fixed.seed)


def _foundation_retention_screen(
    source_context, parent, candidate_bundle, artifact_path, target_capability,
    release, groups, training, fixed_instruments,
):
    fixed_cases = tuple(item.case for item in fixed_instruments)
    policy = FoundationRetentionPolicy(
        groups, tuple(dict.fromkeys(group for _, group in groups)),
        tuple((capability, C05_PROTECTED_REFERENCE_LOSS)
              for capability, _ in groups if capability != target_capability),
        C05_PROBE_EACH, case_census_digest(fixed_cases))
    fixed_cohort = _cohort(
        EvidenceKind.FIXED_SCHOOL, fixed_instruments, groups,
        release, policy, training, evidence_stage=CURRENT_EVIDENCE_STAGE)
    parent_solver, parent_generation = factory_complete_solver(
        source_context, parent, artifact_path, fixed_instruments)
    candidate_solver, candidate_generation = factory_complete_solver(
        source_context, candidate_bundle, artifact_path, fixed_instruments)
    decision = evaluate_foundation_fixed_school_candidate(
        parent_solver, candidate_solver, target_capability, policy, fixed_cohort,
        parent_generation, candidate_generation)
    return decision, parent, candidate_bundle


def _adaptive_retention_screen(
    source_context, parent, candidate_bundle, candidate_state, artifact_path,
    target_capability, target_group, lesson_capabilities, release, groups,
    training, fixed_instruments, cache,
):
    candidate_sha256 = candidate_identity_digest(candidate_state)
    fresh_seed = _owner_seed(
        release.release_sha256, cache, target_capability, candidate_sha256)
    target_draw = _fresh_rows(
        source_context, (target_capability,),
        seed=fresh_seed + C05_FRESH_TARGET_SEED_OFFSET, training=training)
    lesson_draw = _fresh_rows(
        source_context, lesson_capabilities,
        seed=fresh_seed + C05_FRESH_LESSON_SEED_OFFSET, training=training)
    target_instruments = _instruments(
        source_context, candidate_bundle, artifact_path, target_draw.rows,
        seed=target_draw.seed, each=C05_PROBE_EACH)
    lesson_instruments = _instruments(
        source_context, candidate_bundle, artifact_path, lesson_draw.rows,
        seed=lesson_draw.seed, each=C05_PROBE_EACH)
    policy, cohorts = _policy_and_cohorts(
        release, groups, target_capability, target_group, training,
        target_instruments, lesson_instruments, fixed_instruments,
        evidence_stage=CURRENT_EVIDENCE_STAGE)
    all_instruments = tuple(dict(
        (item.case.case_id, item)
        for item in (*target_instruments, *lesson_instruments, *fixed_instruments)
    ).values())
    parent_solver, parent_generation = factory_complete_solver(
        source_context, parent, artifact_path, all_instruments)
    candidate_solver, candidate_generation = factory_complete_solver(
        source_context, candidate_bundle, artifact_path, all_instruments)
    decision = evaluate_retention_candidate(
        parent_solver, candidate_solver, target_capability, policy,
        cohorts, parent_generation, candidate_generation)
    return decision, parent, candidate_bundle


def _bind_factory_evaluation_issuer(raw_issue):
    """Bind issuance to the two Factory-owned screens without exporting a mint."""
    def foundation(*args, **kwargs):
        return raw_issue(*_foundation_retention_screen(*args, **kwargs))

    def adaptive(*args, **kwargs):
        return raw_issue(*_adaptive_retention_screen(*args, **kwargs))

    return foundation, adaptive


_foundation_retention_evaluation, _adaptive_retention_evaluation = (
    _bind_factory_evaluation_issuer(_raw_issue_owner_evaluation))
del _raw_issue_owner_evaluation


def measure_factory_foundation_progress(
    source_context, artifact_path: str, *, run_dir: Path,
):
    """Measure the accepted parent on C05's immutable whole-school fixture.

    This is observation only.  It grants no admission or retention authority;
    C16.3 uses the scores solely to choose the next prerequisite-lawful target
    from the admitted Factory plan.
    """
    if not isinstance(run_dir, Path):
        _invalid("BAMF_C05_FACTORY_OWNER_INPUT_INVALID")
    source_context.__post_init__()
    source_context.require_accepted_runtime(run_dir)
    parent = load_accepted_generation(run_dir)
    cache = bind_accepted_execution_cache(run_dir)
    release = source_context.release
    groups = tuple(
        (item.capability_id, item.grade_id)
        for item in release.execution_plan.capabilities)
    fixed = _fixed_school_instruments(
        source_context, parent, artifact_path, run_dir, release,
        parent=parent, cache=cache)
    cases = tuple(item.case for item in fixed)
    policy = FoundationRetentionPolicy(
        groups, tuple(dict.fromkeys(group for _, group in groups)), (),
        C05_PROBE_EACH, case_census_digest(cases))
    cohort = _cohort(
        EvidenceKind.FIXED_SCHOOL, fixed, groups, release, policy, ((), ()),
        evidence_stage=CURRENT_EVIDENCE_STAGE)
    solver, generation = factory_complete_solver(
        source_context, parent, artifact_path, fixed)
    return evaluate_capabilities(solver, cohort, generation)


def evaluate_factory_retention_candidate(
    source_context,
    candidate: CandidateTransaction,
    artifact_path: str,
    target_capability: str,
    *,
    run_dir: Path,
):
    """Run C05 with no caller-selected solver, cohort, policy or coverage map."""
    if (type(candidate) is not CandidateTransaction
            or not isinstance(target_capability, str) or not target_capability
            or not isinstance(run_dir, Path)):
        _invalid("BAMF_C05_FACTORY_OWNER_INPUT_INVALID")
    source_context.__post_init__()
    source_context.require_accepted_runtime(run_dir)
    release = source_context.release
    capability_map = release.execution_plan.capability_map
    if target_capability not in capability_map:
        _invalid("BAMF_C05_TARGET_CAPABILITY_NOT_ADMITTED")
    groups = tuple((item.capability_id, item.grade_id)
                   for item in release.execution_plan.capabilities)
    target_group = capability_map[target_capability].grade_id
    lesson_capabilities = tuple(capability for capability, group in groups
                                if group == target_group)
    training = _training_exclusions(candidate)
    if (any(authority.delivery_capability != target_capability
            or authority.release_sha256 != release.release_sha256
            for authority in candidate.training_authorities
            if authority is not None)):
        _invalid("BAMF_C05_TARGET_NOT_OWNED_BY_TRAINING")
    parent, candidate_bundle, candidate_state, cache = _candidate_from_live_parent(
        run_dir, candidate)
    fixed_instruments = _fixed_school_instruments(
        source_context, candidate_bundle, artifact_path, run_dir, release,
        parent=parent, cache=cache)

    if CURRENT_EVIDENCE_STAGE is EvidenceStage.FOUNDATION_ACQUISITION:
        return _foundation_retention_evaluation(
            source_context, parent, candidate_bundle, artifact_path,
            target_capability, release, groups, training, fixed_instruments)
    return _adaptive_retention_evaluation(
        source_context, parent, candidate_bundle, candidate_state, artifact_path,
        target_capability, target_group, lesson_capabilities, release, groups,
        training, fixed_instruments, cache)


def evaluate_factory_package_import(
    source_context,
    transaction: PackageImportTransaction,
    artifact_path: str,
    target_capability: str,
    *,
    run_dir: Path,
):
    """Run the same C05 owner over a B12 package-import state proposal."""
    if (type(transaction) is not PackageImportTransaction
            or not isinstance(target_capability, str) or not target_capability
            or not isinstance(run_dir, Path)):
        _invalid("BAMF_C05_PACKAGE_IMPORT_INPUT_INVALID")
    source_context.__post_init__()
    source_context.require_accepted_runtime(run_dir)
    release = source_context.release
    capability_map = release.execution_plan.capability_map
    if target_capability not in capability_map:
        _invalid("BAMF_C05_TARGET_CAPABILITY_NOT_ADMITTED")
    groups = tuple((item.capability_id, item.grade_id)
                   for item in release.execution_plan.capabilities)
    target_group = capability_map[target_capability].grade_id
    lesson_capabilities = tuple(capability for capability, group in groups
                                if group == target_group)
    # A package import is not a training episode. C05 still owns every source draw
    # and complete-solver comparison, but there is no neural-training provenance
    # to exclude from those draws.
    training = ((), ())
    parent, candidate_bundle, candidate_state, cache = _package_import_from_live_parent(
        run_dir, transaction)
    fixed_instruments = _fixed_school_instruments(
        source_context, candidate_bundle, artifact_path, run_dir, release,
        parent=parent, cache=cache)

    if CURRENT_EVIDENCE_STAGE is EvidenceStage.FOUNDATION_ACQUISITION:
        return _foundation_retention_evaluation(
            source_context, parent, candidate_bundle, artifact_path,
            target_capability, release, groups, training, fixed_instruments)
    return _adaptive_retention_evaluation(
        source_context, parent, candidate_bundle, candidate_state, artifact_path,
        target_capability, target_group, lesson_capabilities, release, groups,
        training, fixed_instruments, cache)


__all__ = (
    "FactoryRetentionEvaluation", "evaluate_factory_package_import",
    "evaluate_factory_retention_candidate",
)
