"""Private owner for unforgeable C05 retention-evaluation evidence."""
from __future__ import annotations

from dataclasses import dataclass

from bilqis_mlx.runtime.capability_retention import Decision

from .capability_evaluation import _invalid
from ._factory_parent_assessment_cache import ParentAssessmentCacheReceipt


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
              parent_assessment_cache=None, *, parent_state=None, candidate_state=None):
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
                    and type(cache) is not ParentAssessmentCacheReceipt)):
            _invalid("BAMF_C05_FACTORY_EVALUATION_INVALID")
        if cache is not None:
            cache.__post_init__()


_require_factory_evaluation, _raw_issue_owner_evaluation = (
    _new_factory_evaluation_owner())


__all__ = (
    "FactoryRetentionEvaluation", "_raw_issue_owner_evaluation",
    "_require_factory_evaluation",
)
