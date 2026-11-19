"""Private owner for unforgeable C05 retention-evaluation evidence."""
from __future__ import annotations

from dataclasses import dataclass

from bilqis_mlx.learning._atlas_candidate.identity_binding import CandidateIdentityBinding
from bilqis_mlx.runtime.capability_retention import (
    Assessment, Decision, EvaluationCohort,
)

from .capability_evaluation import _invalid
from ._factory_parent_assessment_cache import ParentAssessmentCacheReceipt
from .baseline.lifecycle import BaselineLedger, FactoryBaselineTransition


SHA256_HEX_LENGTH = 64


def _new_factory_evaluation_owner():
    """Keep live C05 evaluation authority in closure-owned object identity."""
    issued = {}

    def require(value):
        if issued.get(id(value)) is not value:
            _invalid("BAMF_C05_FACTORY_EVALUATION_INVALID")
        return value

    def issue(decision, parent_candidate_sha256, candidate_candidate_sha256,
              candidate_generation_authority_sha256,
              parent_assessment_cache=None, *, parent_state=None, candidate_state=None,
              parent_binding=None, candidate_binding=None,
              baseline_transition=None, baseline_ledger=None,
              championship_cohort=None, championship_assessment=None):
        item = object.__new__(FactoryRetentionEvaluation)
        for name, value in (
            ("decision", decision),
            ("parent_candidate_sha256", parent_candidate_sha256),
            ("candidate_candidate_sha256", candidate_candidate_sha256),
            ("candidate_generation_authority_sha256",
             candidate_generation_authority_sha256),
            ("parent_assessment_cache", parent_assessment_cache),
            ("parent_state", parent_state),
            ("candidate_state", candidate_state),
            ("parent_binding", parent_binding),
            ("candidate_binding", candidate_binding),
            ("baseline_transition", baseline_transition),
            ("baseline_ledger", baseline_ledger),
            ("championship_cohort", championship_cohort),
            ("championship_assessment", championship_assessment),
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
    parent_assessment_cache: ParentAssessmentCacheReceipt | None
    parent_state: object
    candidate_state: object
    parent_binding: CandidateIdentityBinding | None
    candidate_binding: CandidateIdentityBinding | None
    baseline_transition: FactoryBaselineTransition | None
    baseline_ledger: BaselineLedger
    championship_cohort: EvaluationCohort | None
    championship_assessment: Assessment | None

    def __init__(self, *args, **kwargs):
        _invalid("BAMF_C05_FACTORY_EVALUATION_CALLER_CONSTRUCTION_FORBIDDEN")

    def __post_init__(self):
        _require_factory_evaluation(self)
        cache = getattr(self, "parent_assessment_cache", None)
        if (type(self.decision) is not Decision
                or not all(isinstance(value, str)
                           and len(value) == SHA256_HEX_LENGTH
                           for value in (self.parent_candidate_sha256,
                                         self.candidate_candidate_sha256))
                or (self.candidate_generation_authority_sha256 is not None
                    and (not isinstance(self.candidate_generation_authority_sha256, str)
                         or len(self.candidate_generation_authority_sha256)
                         != SHA256_HEX_LENGTH))
                or (cache is not None
                    and type(cache) is not ParentAssessmentCacheReceipt)
                or (self.parent_binding is not None
                    and (type(self.parent_binding) is not CandidateIdentityBinding
                         or self.parent_binding.digest != self.parent_candidate_sha256
                         or self.parent_binding.state_ref() is not self.parent_state))
                or (self.candidate_binding is not None
                    and (type(self.candidate_binding) is not CandidateIdentityBinding
                         or self.candidate_binding.digest != self.candidate_candidate_sha256
                         or self.candidate_binding.state_ref() is not self.candidate_state))
                or type(self.baseline_ledger) is not BaselineLedger
                or (self.championship_cohort is not None
                    and type(self.championship_cohort) is not EvaluationCohort)
                or (self.championship_assessment is not None
                    and (type(self.championship_assessment) is not Assessment
                         or self.championship_cohort is None
                         or self.championship_assessment.cohort != self.championship_cohort
                         or self.championship_assessment.generation_digest
                         != self.decision.candidate_generation))
                or (self.baseline_transition is not None
                    and type(self.baseline_transition) is not FactoryBaselineTransition)):
            _invalid("BAMF_C05_FACTORY_EVALUATION_INVALID")
        if cache is not None:
            cache.__post_init__()
        self.baseline_ledger.__post_init__()
        if self.baseline_transition is not None:
            self.baseline_transition.__post_init__()


_require_factory_evaluation, _raw_issue_owner_evaluation = (
    _new_factory_evaluation_owner())


def _finalize_factory_generation_authority(
        evaluation, decision, parent, candidate_transaction, successor):
    """Finalize exact motif generation authority after accepted owner projections."""
    _require_factory_evaluation(evaluation)
    evaluation.__post_init__()
    screened_authority = evaluation.candidate_generation_authority_sha256
    if screened_authority is None:
        return decision

    from bilqis_mlx.learning.atlas_candidate import CandidateTransaction
    from bilqis_mlx.learning.atlas_retention_decision import (
        CandidateRetentionDecision, _finalize_issued_decision_generation_authority,
    )
    from bilqis_mlx.learning._atlas_candidate.identity_binding import (
        candidate_identity_for_canonical_consumer,
    )
    from bilqis_mlx.runtime.bamf_bundle.admission import derive_motif_successor_bundle
    from bilqis_mlx.runtime.bamf_bundle.genesis.records import (
        successor_candidate_identity_digest,
    )
    from bilqis_mlx.runtime.bamf_bundle.motif.transition import (
        is_motif_allocation_transition,
    )
    from bilqis_mlx.runtime.bamf_bundle.records import BamfBundleCandidate, CompleteStudent
    from bilqis_mlx.runtime.bamf_bundle.records import sidecar_records

    if (type(decision) is not CandidateRetentionDecision or not decision.accepted
            or type(parent) is not CompleteStudent
            or type(candidate_transaction) is not CandidateTransaction
            or candidate_transaction.motif_transition is None
            or type(successor) is not BamfBundleCandidate
            or not is_motif_allocation_transition(successor.transition)
            or successor.retained_state is not evaluation.candidate_state
            or decision.parent_generation != evaluation.parent_candidate_sha256
            or decision.candidate_generation != evaluation.candidate_candidate_sha256
            or candidate_identity_for_canonical_consumer(successor.retained_state)
            != evaluation.candidate_candidate_sha256):
        _invalid("BAMF_C05_FACTORY_EVALUATION_INVALID")

    screened = derive_motif_successor_bundle(
        parent, candidate_transaction, retained_state=evaluation.candidate_state,
        parent_manifest_sha256=successor.parent_manifest_sha256,
        delivery_events=())
    def protected(item):
        return (
            item.run_id, item.generation, item.parent_manifest_sha256,
            item.implementation_sha256, item.topology, item.extents,
            item.optimizer_hyperparameters, dict(item.semantic_abi),
            dict(item.compiler_features), dict(item.correction_frontier),
            dict(item.evaluation_contract), dict(item.transition), item.run_identity,
            item.provenance.source_identity, item.provenance.release_digest,
        )
    if (screened.retained_state is not evaluation.candidate_state
            or successor_candidate_identity_digest(screened) != screened_authority
            or protected(screened) != protected(successor)):
        _invalid("BAMF_C05_FACTORY_EVALUATION_INVALID")

    sidecar_records(successor)
    final_authority = successor_candidate_identity_digest(successor)
    _finalize_issued_decision_generation_authority(
        decision, screened_authority, final_authority)
    return decision


__all__ = (
    "FactoryRetentionEvaluation", "_raw_issue_owner_evaluation",
    "_require_factory_evaluation",
)
