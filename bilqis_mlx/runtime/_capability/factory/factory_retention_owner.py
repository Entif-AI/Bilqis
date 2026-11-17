"""Production C05 owner: Factory cohorts, policy, solvers and paired screen."""
from __future__ import annotations

from pathlib import Path

from bilqis_mlx.fixed_frontier import load_frontier_cohort
from bilqis_mlx.learning.atlas_candidate import CandidateTransaction
from bilqis_mlx.learning.atlas_package_import import PackageImportTransaction
from bilqis_mlx.learning._atlas_candidate.identity_binding import candidate_identity_for_canonical_consumer
from bilqis_mlx.runtime.bamf_bundle.admission import (
    bind_accepted_execution_cache, derive_successor_bundle,
    load_accepted_generation,
)
from bilqis_mlx.runtime.capability_retention import (
    EvidenceKind, EvidenceStage,
    case_census_digest, evaluate_capabilities,
)
from bilqis_mlx.state_dag import read_current
from bilqis_mlx.fixed_frontier import frontier_exam

from .capability_evaluation import _invalid
from .capability_retention_foundation import (
    FoundationRetentionPolicy, evaluate_foundation_fixed_school_candidate,
)
from .factory_complete_solver import factory_complete_solver
from .factory_fixed_school import _bamf_fixed_school_cohort
from ._factory_identity_evaluation import (
    FactoryRetentionEvaluation, _raw_issue_owner_evaluation,
    _require_factory_evaluation,
)
from .retention.screen import (
    bind_factory_baseline_successor, bind_factory_evaluation_issuer,
)
from .retention.protection_plan import BroadCertificationTrigger
from .retention.protection_plan_compiler import (
    bind_retention_protection_plan,
    policy_epoch_sha256,
    require_retention_protection_plan,
)
from bilqis_mlx.semantics.domains import contract_digest


CURRENT_EVIDENCE_STAGE = EvidenceStage.FOUNDATION_ACQUISITION


def candidate_identity_digest(state):
    """Preserve the Factory owner's test seam while reusing live bindings."""
    return candidate_identity_for_canonical_consumer(state)

from ._factory_retention_support import (
    C05_FRESH_LESSON_SEED_OFFSET, C05_FRESH_TARGET_SEED_OFFSET,
    C05_MAX_FRESH_DRAWS, C05_PROBE_EACH, C05_PROTECTED_REFERENCE_LOSS,
    _candidate_from_live_parent, _cohort, _fresh_rows, _instruments,
    _owner_seed, _package_import_from_live_parent,
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


(_foundation_retention_evaluation, _adaptive_retention_evaluation,
 _broad_foundation_retention_evaluation) = (
    bind_factory_evaluation_issuer(
        _raw_issue_owner_evaluation, CURRENT_EVIDENCE_STAGE))
del _raw_issue_owner_evaluation


def _local_retention_seed(cache, release, capability_id: str) -> int:
    digest = contract_digest({
        "schema": "bilqis.mlx.c05-local-retention-seed/v1",
        "run_id": cache.run_id,
        "factory_release_sha256": release.release_sha256,
        "semantic_catalog_sha256": release.semantic_catalog_sha256,
        "capability_id": capability_id,
    })
    return int(digest[:16], 16)


def _local_retention_instruments(
        source_context, candidate_bundle, artifact_path, cached_rows, target_plan):
    instruments = []
    for capability, seed, rows in cached_rows:
        instruments.extend(_instruments(
            source_context, candidate_bundle, artifact_path, rows,
            seed=seed, each=C05_PROBE_EACH, release_prevalidated=True))
    return tuple(instruments)


def bind_current_retention_protection_plan(source_context, parent, cache):
    """Bind ordinary C05 protection before candidate selection/training."""
    return bind_retention_protection_plan(
        cache, source_context.release, parent, CURRENT_EVIDENCE_STAGE)


def bind_current_retention_source_rows(source_context, cache, capability_id):
    """Prebind exact local C05 rows before candidate training/retention."""
    plan = require_retention_protection_plan(cache, source_context.release)
    target_plan = plan.for_target(capability_id)
    store = getattr(cache, "_retention_source_rows", None)
    if type(store) is not dict:
        _invalid("BAMF_C05_RETENTION_SOURCE_CACHE_INVALID")
    key = (plan.digest, capability_id)
    current = store.get(key)
    if current is not None:
        return current
    bound = []
    for capability in target_plan.evaluated_capability_ids:
        seed = _local_retention_seed(cache, source_context.release, capability)
        draw = _fresh_rows(
            source_context, (capability,), seed=seed, training=((), ()),
            require_independent=False)
        bound.append((capability, draw.seed, draw.rows))
    result = tuple(bound)
    store[key] = result
    return result


def require_current_retention_source_rows(cache, release, capability_id):
    plan = require_retention_protection_plan(cache, release)
    store = getattr(cache, "_retention_source_rows", None)
    if type(store) is not dict:
        _invalid("BAMF_C05_RETENTION_SOURCE_CACHE_INVALID")
    result = store.get((plan.digest, capability_id))
    if result is None:
        _invalid("BAMF_C05_RETENTION_SOURCE_PRECOMPUTE_REQUIRED")
    return plan, plan.for_target(capability_id), result


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
    from bilqis_mlx.runtime.source_execution import SourceExecutionContext
    if type(source_context) is not SourceExecutionContext:
        _invalid("BAMF_C05_FACTORY_OWNER_INPUT_INVALID")
    source_context.require_accepted_runtime(run_dir)
    parent = load_accepted_generation(run_dir)
    cache = bind_accepted_execution_cache(run_dir)
    release = source_context.release
    fixed = _fixed_school_instruments(
        source_context, parent, artifact_path, run_dir, release,
        parent=parent, cache=cache)
    cases = tuple(item.case for item in fixed)
    measured = {case.capability_id for case in cases}
    groups = tuple(
        (item.capability_id, item.grade_id)
        for item in release.execution_plan.capabilities
        if item.capability_id in measured)
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
    run_dir: Path, observer=None, plasticity_escape=None,
):
    """Run C05 with no caller-selected solver, cohort, policy or coverage map."""
    if (type(candidate) is not CandidateTransaction
            or not isinstance(target_capability, str) or not target_capability
            or not isinstance(run_dir, Path)):
        _invalid("BAMF_C05_FACTORY_OWNER_INPUT_INVALID")
    source_context.__post_init__()
    source_context.require_accepted_runtime(run_dir)
    release = source_context.release
    training = _training_exclusions(candidate)
    if (any(authority.delivery_capability != target_capability
            or authority.release_sha256 != release.release_sha256
            for authority in candidate.training_authorities
            if authority is not None)):
        _invalid("BAMF_C05_TARGET_NOT_OWNED_BY_TRAINING")
    parent, candidate_bundle, candidate_state, cache = _candidate_from_live_parent(
        run_dir, candidate)
    plan, target_plan, cached_rows = require_current_retention_source_rows(
        cache, release, target_capability)

    if CURRENT_EVIDENCE_STAGE is EvidenceStage.FOUNDATION_ACQUISITION:
        return _foundation_retention_evaluation(
            source_context, parent, candidate_bundle, candidate_state, artifact_path,
            release, plan, target_plan, training, cached_rows, cache,
            **({"observer": observer} if observer is not None else {}))
    instruments = _local_retention_instruments(
        source_context, candidate_bundle, artifact_path, cached_rows, target_plan)
    groups = target_plan.evaluated_capability_groups
    target_group = target_plan.target_grade_id
    lesson_capabilities = tuple(
        capability for capability, group in groups if group == target_group)
    return _adaptive_retention_evaluation(
        source_context, parent, candidate_bundle, candidate_state, artifact_path,
        target_capability, target_group, lesson_capabilities, release, groups,
        training, instruments, cache,
        protected_capabilities=target_plan.protected_capability_ids,
        retention_protection_plan_sha256=plan.digest,
        plasticity_escape=plasticity_escape,
        **({"observer": observer} if observer is not None else {}))


def derive_current_plasticity_escape_state(parent, selection, release):
    """Derive exceptional state from accepted/replayed evidence only in strict C05."""
    if CURRENT_EVIDENCE_STAGE is not EvidenceStage.STRICT_GENERALIZATION:
        return None
    from bilqis_mlx.runtime.plasticity_escape import derive_plasticity_escape_state
    context = getattr(selection, "metadata", {}).get("how_context")
    visit = getattr(selection, "visit", None)
    projection = getattr(visit, "projection", None)
    teacher_state = getattr(projection, "teacher_state", None)
    if not isinstance(context, dict):
        _invalid("BAMF_PLASTICITY_HOW_CONTEXT_REQUIRED")
    grades = tuple(release.execution_plan.grades)
    if not grades:
        _invalid("BAMF_PLASTICITY_ACTIVE_GRADE_REQUIRED")
    return derive_plasticity_escape_state(
        teacher_state,
        getattr(parent, "learning_health_state", None),
        target_capability_id=selection.offer.capability_id,
        target_group_id=context["grade"],
        frontier_group_id=grades[-1].grade_id,
        phase=context["phase"],
        curriculum_scope=context["curriculum_scope"],
        policy_epoch_sha256=policy_epoch_sha256(CURRENT_EVIDENCE_STAGE),
    )


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

    if {(item.case.capability_id, item.case.group_id) for item in fixed_instruments} != set(groups):
        _invalid("BAMF_C05_FIXED_SCHOOL_COVERAGE_INCOMPLETE")

    if CURRENT_EVIDENCE_STAGE is EvidenceStage.FOUNDATION_ACQUISITION:
        return _broad_foundation_retention_evaluation(
            source_context, parent, candidate_bundle, artifact_path,
            target_capability, release, groups, training, fixed_instruments,
            cache,
            broad_certification_trigger=(
                BroadCertificationTrigger.DECLARED_BROAD_BLAST_RADIUS))
    return _adaptive_retention_evaluation(
        source_context, parent, candidate_bundle, candidate_state, artifact_path,
        target_capability, target_group, lesson_capabilities, release, groups,
        training, fixed_instruments, cache,
        protected_capabilities=tuple(
            capability for capability, _group in groups
            if capability != target_capability))


__all__ = (
    "FactoryRetentionEvaluation", "bind_current_retention_protection_plan",
    "bind_current_retention_source_rows",
    "bind_factory_baseline_successor",
    "derive_current_plasticity_escape_state",
    "evaluate_factory_package_import",
    "evaluate_factory_retention_candidate",
)
