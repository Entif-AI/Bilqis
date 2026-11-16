"""Plan rebind and successor-evidence reconciliation."""
from __future__ import annotations
from ..model import FactoryRelease
from .contracts import AutonomyPlan
from .evidence_contracts import EvidenceLedger
from .obligations import _obligation_map, _validate_ledger
from .planning import _require_plan_release

def rebind_evidence_ledger(
    release: FactoryRelease, ledger: EvidenceLedger, *,
    old_plan: AutonomyPlan, new_plan: AutonomyPlan,
) -> EvidenceLedger:
    """Carry forward only receipts whose semantic obligation is unchanged."""
    _validate_ledger(release, ledger, plan=old_plan)
    _require_plan_release(release.release_sha256, old_plan)
    _require_plan_release(release.release_sha256, new_plan)
    old_obligations = _obligation_map(release, old_plan)
    new_obligations = _obligation_map(release, new_plan)
    for receipt in ledger.receipts:
        old = old_obligations.get(receipt.obligation_id)
        new = new_obligations.get(receipt.obligation_id)
        if old is None or new is None or old != new:
            raise ValueError(
                "AUTONOMY_PLAN_REBIND_INVALIDATES_EVIDENCE:" + receipt.obligation_id)
    for attempt in ledger.rejected_attempts:
        old = old_obligations.get(attempt.obligation_id)
        new = new_obligations.get(attempt.obligation_id)
        if old is None or new is None or old != new:
            raise ValueError(
                "AUTONOMY_PLAN_REBIND_INVALIDATES_ATTEMPT:" +
                attempt.obligation_id)
    rebound = EvidenceLedger(
        release.release_sha256, new_plan.digest(),
        ledger.receipts, ledger.interventions, ledger.rejected_attempts)
    _validate_ledger(release, rebound, plan=new_plan)
    return rebound


def reconcile_successor_evidence(
    previous_release, current_release, ledger: EvidenceLedger, *,
    previous_plan: AutonomyPlan, current_plan: AutonomyPlan,
) -> EvidenceLedger:
    """Carry only unchanged semantic/source/answer/coverage evidence forward.

    Release identity is not evidence identity.  A successor may retain learner
    receipts for a capability only when its semantic declaration and the
    source, answer-schema, and coverage projections are byte-identical and the
    concrete learner obligation itself is unchanged.  Teaching interventions
    remain in the immutable predecessor snapshot; they are not re-authorized
    across a release boundary.
    """
    from ..executable_release import ExecutableFactoryRelease

    if (not isinstance(previous_release, ExecutableFactoryRelease) or
            not isinstance(current_release, ExecutableFactoryRelease)):
        raise TypeError("AUTONOMY_SUCCESSOR_RECONCILIATION_REQUIRES_V2")
    previous_release.verify()
    current_release.verify_successor_of(previous_release)
    _validate_ledger(previous_release, ledger, plan=previous_plan)
    _require_plan_release(current_release.release_sha256, current_plan)

    old_semantics = previous_release.curriculum.capability_map
    new_semantics = current_release.curriculum.capability_map
    old_projection = {
        item.capability_id: item
        for item in previous_release.execution_plan.capability_projection_digests
    }
    new_projection = {
        item.capability_id: item
        for item in current_release.execution_plan.capability_projection_digests
    }
    unchanged_capabilities = {
        capability_id
        for capability_id in set(old_semantics) & set(new_semantics)
        if old_semantics[capability_id] == new_semantics[capability_id]
        and all(
            getattr(old_projection[capability_id], field)
            == getattr(new_projection[capability_id], field)
            for field in ("source", "answer_schema", "coverage")
        )
    }
    old_obligations = _obligation_map(previous_release, previous_plan)
    new_obligations = _obligation_map(current_release, current_plan)
    carried = tuple(
        receipt for receipt in ledger.receipts
        if (receipt.obligation_id in old_obligations
            and receipt.obligation_id in new_obligations
            and old_obligations[receipt.obligation_id]
            == new_obligations[receipt.obligation_id]
            and old_obligations[receipt.obligation_id].capability_id
            in unchanged_capabilities)
    )
    reconciled = EvidenceLedger(
        current_release.release_sha256, current_plan.digest(), carried, ())
    _validate_ledger(current_release, reconciled, plan=current_plan)
    return reconciled
