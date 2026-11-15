"""Exact-identity memoization for accepted-parent C05 fixed-school assessment."""
from __future__ import annotations

from dataclasses import dataclass
import threading

from bilqis_mlx.learning.atlas_acceptance import candidate_identity_digest
from bilqis_mlx.runtime.bamf_bundle.execution_cache import (
    require_accepted_execution_cache,
)
from bilqis_mlx.runtime.capability_retention import (
    Assessment, CompleteSolver, EvaluationCohort, evaluate_capabilities,
)
from bilqis_mlx.semantics.domains import contract_digest

from .capability_evaluation import _invalid, _sha


@dataclass(frozen=True)
class ParentAssessmentCacheIdentity:
    run_id: str
    accepted_generation: int
    accepted_manifest_sha256: str
    accepted_generation_binding: str
    parent_generation_sha256: str
    parent_candidate_sha256: str
    factory_release_sha256: str
    semantic_catalog_sha256: str
    source_authority_registry_sha256: str | None
    fixed_cohort_sha256: str
    rubric_sha256: str
    source_sha256: str
    policy_sha256: str
    implementation_sha256: str
    topology_sha256: str
    extents_sha256: str
    correction_frontier_sha256: str
    semantic_abi_sha256: str
    compiler_features_sha256: str
    evaluation_contract_sha256: str
    evaluator_contract_sha256: str
    schema_version: str = "bilqis.mlx.c05-parent-assessment-cache-identity/v1"

    def __post_init__(self):
        digests = (
            self.accepted_manifest_sha256,
            self.accepted_generation_binding,
            self.parent_generation_sha256,
            self.parent_candidate_sha256,
            self.factory_release_sha256,
            self.semantic_catalog_sha256,
            self.fixed_cohort_sha256,
            self.rubric_sha256,
            self.source_sha256,
            self.policy_sha256,
            self.implementation_sha256,
            self.topology_sha256,
            self.extents_sha256,
            self.correction_frontier_sha256,
            self.semantic_abi_sha256,
            self.compiler_features_sha256,
            self.evaluation_contract_sha256,
            self.evaluator_contract_sha256,
        )
        if (
            not isinstance(self.run_id, str) or not self.run_id
            or type(self.accepted_generation) is not int
            or self.accepted_generation < 0
            or any(not _sha(value) for value in digests)
            or (
                self.source_authority_registry_sha256 is not None
                and not _sha(self.source_authority_registry_sha256)
            )
            or self.schema_version
            != "bilqis.mlx.c05-parent-assessment-cache-identity/v1"
        ):
            _invalid("BAMF_C05_PARENT_ASSESSMENT_CACHE_IDENTITY_INVALID")

    def digest(self) -> str:
        return contract_digest(self)


@dataclass(frozen=True)
class ParentAssessmentCacheReceipt:
    identity_sha256: str
    assessment_sha256: str
    cache_entry_sha256: str
    reused: bool
    schema_version: str = "bilqis.mlx.c05-parent-assessment-cache-receipt/v1"

    def __post_init__(self):
        if (
            any(not _sha(value) for value in (
                self.identity_sha256,
                self.assessment_sha256,
                self.cache_entry_sha256,
            ))
            or type(self.reused) is not bool
            or self.schema_version
            != "bilqis.mlx.c05-parent-assessment-cache-receipt/v1"
        ):
            _invalid("BAMF_C05_PARENT_ASSESSMENT_CACHE_RECEIPT_INVALID")

    def digest(self) -> str:
        return contract_digest(self)


@dataclass(frozen=True)
class _CacheEntry:
    identity: ParentAssessmentCacheIdentity
    assessment: Assessment
    cache_entry_sha256: str


class _ParentAssessmentCache:
    def __init__(self):
        self._lock = threading.RLock()
        self._by_run: dict[str, _CacheEntry] = {}

    def use(
            self, identity: ParentAssessmentCacheIdentity, solver: CompleteSolver,
            cohort: EvaluationCohort, generation: str,
    ) -> tuple[Assessment, ParentAssessmentCacheReceipt]:
        with self._lock:
            current = self._by_run.get(identity.run_id)
            if current is not None and current.identity == identity:
                assessment = _require_assessment(
                    current.assessment, cohort, generation)
                if (_entry_digest(identity, assessment)
                        != current.cache_entry_sha256):
                    _invalid("BAMF_C05_PARENT_ASSESSMENT_CACHE_DRIFT")
                return assessment, _receipt(current, True)
            assessment = _require_assessment(
                evaluate_capabilities(solver, cohort, generation),
                cohort, generation)
            entry = _CacheEntry(
                identity, assessment, _entry_digest(identity, assessment))
            self._by_run[identity.run_id] = entry
            return assessment, _receipt(entry, False)

    def clear(self) -> None:
        with self._lock:
            self._by_run.clear()


_CACHE = _ParentAssessmentCache()


def _entry_digest(identity: ParentAssessmentCacheIdentity,
                  assessment: Assessment) -> str:
    return contract_digest({
        "schema": "bilqis.mlx.c05-parent-assessment-cache-entry/v1",
        "identity_sha256": identity.digest(),
        "assessment_sha256": assessment.digest(),
    })


def _receipt(entry: _CacheEntry, reused: bool) -> ParentAssessmentCacheReceipt:
    return ParentAssessmentCacheReceipt(
        entry.identity.digest(),
        entry.assessment.digest(),
        entry.cache_entry_sha256,
        reused,
    )


def _require_assessment(
        assessment: Assessment, cohort: EvaluationCohort, generation: str,
) -> Assessment:
    if (
        type(assessment) is not Assessment
        or assessment.cohort != cohort
        or assessment.generation_digest != generation
    ):
        _invalid("BAMF_C05_PARENT_ASSESSMENT_CACHE_DRIFT")
    assessment.__post_init__()
    return assessment


def use_parent_assessment(
        identity: ParentAssessmentCacheIdentity,
        solver: CompleteSolver,
        cohort: EvaluationCohort,
        generation: str,
) -> tuple[Assessment, ParentAssessmentCacheReceipt]:
    """Reuse only one exact accepted-parent assessment per run identity."""
    if (
        type(identity) is not ParentAssessmentCacheIdentity
        or type(solver) is not CompleteSolver
        or type(cohort) is not EvaluationCohort
        or not _sha(generation)
        or generation != identity.parent_generation_sha256
        or identity.fixed_cohort_sha256 != contract_digest(cohort)
        or identity.rubric_sha256 != cohort.rubric_sha256
        or identity.source_sha256 != cohort.source_sha256
        or identity.policy_sha256 != cohort.policy_sha256
    ):
        _invalid("BAMF_C05_PARENT_ASSESSMENT_CACHE_INPUT_INVALID")
    identity.__post_init__()
    return _CACHE.use(identity, solver, cohort, generation)


def factory_parent_assessment_identity(
        source_context, parent, accepted_cache, cohort, parent_solver,
        parent_generation: str,
) -> ParentAssessmentCacheIdentity:
    """Bind every authority-bearing input that can change parent solver truth."""
    accepted_cache = require_accepted_execution_cache(accepted_cache)
    release = source_context.release
    if (
        parent.run_id != accepted_cache.run_id
        or parent.generation != accepted_cache.generation
        or accepted_cache.generation_binding != parent_generation
    ):
        _invalid("BAMF_C05_PARENT_ASSESSMENT_ACCEPTED_GENERATION_DRIFT")
    return ParentAssessmentCacheIdentity(
        run_id=accepted_cache.run_id,
        accepted_generation=accepted_cache.generation,
        accepted_manifest_sha256=accepted_cache.accepted_manifest_sha256,
        accepted_generation_binding=accepted_cache.generation_binding,
        parent_generation_sha256=parent_generation,
        parent_candidate_sha256=candidate_identity_digest(
            parent.retained_state),
        factory_release_sha256=release.release_sha256,
        semantic_catalog_sha256=release.semantic_catalog_sha256,
        source_authority_registry_sha256=(
            accepted_cache.source_authority_registry_sha256),
        fixed_cohort_sha256=contract_digest(cohort),
        rubric_sha256=cohort.rubric_sha256,
        source_sha256=cohort.source_sha256,
        policy_sha256=cohort.policy_sha256,
        implementation_sha256=parent.implementation_sha256,
        topology_sha256=parent.topology.digest,
        extents_sha256=parent.extents.digest,
        correction_frontier_sha256=contract_digest(
            parent.correction_frontier),
        semantic_abi_sha256=contract_digest(parent.semantic_abi),
        compiler_features_sha256=contract_digest(parent.compiler_features),
        evaluation_contract_sha256=contract_digest(
            parent.evaluation_contract),
        evaluator_contract_sha256=contract_digest({
            "schema": "bilqis.mlx.c05-factory-complete-solver/v1",
            "assessment_schema": "bilqis.c05.assessment/v1",
            "solve_budget_sha256": contract_digest(parent_solver.budget),
            "source_context_graph_sha256": contract_digest(
                source_context.graph),
        }),
    )


def clear_parent_assessment_cache() -> None:
    """Test/recovery hook; production invalidation normally occurs by identity."""
    _CACHE.clear()


__all__ = (
    "ParentAssessmentCacheIdentity",
    "ParentAssessmentCacheReceipt",
    "clear_parent_assessment_cache",
    "factory_parent_assessment_identity",
    "use_parent_assessment",
)
