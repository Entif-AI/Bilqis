"""Disposable C05/B13 fixture issuance. This module is excluded from the wheel.

The fixture keeps a test-process identity registry instead of importing any
production issuer credential. Exact-type clones therefore remain unissued even
inside the test harness. Never import this module from a production runtime path.
"""
from __future__ import annotations

from weakref import WeakValueDictionary

from bilqis_mlx.learning import atlas_retention_decision as owner
from bilqis_mlx.learning.atlas_acceptance import candidate_identity_digest
from bilqis_mlx.runtime.capability_retention import (
    DecisionStatus, evaluate_retention_candidate,
)

_TEST_ISSUED = WeakValueDictionary()
_OWNER_GLOBALS = owner.CandidateRetentionDecision.__post_init__.__globals__
_PRODUCTION_REQUIRE = _OWNER_GLOBALS["_require_issued_decision"]


def _require_test_or_production(value):
    if _TEST_ISSUED.get(id(value)) is value:
        return value
    return _PRODUCTION_REQUIRE(value)


_OWNER_GLOBALS["_require_issued_decision"] = _require_test_or_production


def issue_disposable_screen(screen, parent_state, candidate_state):
    parent_id = candidate_identity_digest(parent_state)
    candidate_id = candidate_identity_digest(candidate_state)
    result = evaluate_retention_candidate(
        screen[0], screen[1], screen[2], screen[3], screen[4],
        parent_id, candidate_id,
    )
    decision = object.__new__(owner.CandidateRetentionDecision)
    for name, value in (
            ("decision", owner.ACCEPTED_DECISION
             if result.status is DecisionStatus.ELIGIBLE else owner.REJECTED_DECISION),
            ("reason", result.reason),
            ("parent_generation", parent_id),
            ("candidate_generation", candidate_id),
            ("evidence_sha256", result.evidence_sha256),
            ("policy_sha256", result.policy_sha256),
            ("blocking_capability", result.blocking_capability),
            ("blocking_scope", result.blocking_scope),
            ("baseline_coverage", (
                result.baseline_coverage.to_record()
                if result.baseline_coverage is not None else None)),
            ("schema_version", owner.DECISION_SCHEMA)):
        object.__setattr__(decision, name, value)
    _TEST_ISSUED[id(decision)] = decision
    decision.__post_init__()
    return decision
