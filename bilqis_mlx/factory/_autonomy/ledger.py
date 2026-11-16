"""Evidence-ledger state and currentness queries."""
from __future__ import annotations

from ..model import FactoryRelease
from .evidence_contracts import EvidenceLedger, EvidenceObligation, EvidenceReceipt, TeachingReceipt
from .obligations import _obligation_map
from .plan_contracts import AutonomyPlan
from .planning import _resolve_plan, is_factory_release, release_capabilities


def _require_known_obligation(
        obligations: dict[str, EvidenceObligation], obligation_id: str,
) -> EvidenceObligation:
    obligation = obligations.get(obligation_id)
    if obligation is None:
        raise ValueError("AUTONOMY_UNKNOWN_EVIDENCE_OBLIGATION")
    return obligation


def initial_evidence_ledger(
    release: FactoryRelease, *, plan: AutonomyPlan | None = None,
) -> EvidenceLedger:
    release.verify()
    resolved_plan = _resolve_plan(release, plan)
    return EvidenceLedger(release.release_sha256, resolved_plan.digest())


def _validate_ledger(
    release: FactoryRelease, ledger: EvidenceLedger, *, plan: AutonomyPlan | None = None,
) -> dict[str, EvidenceObligation]:
    if not is_factory_release(release) or not isinstance(ledger, EvidenceLedger):
        raise TypeError("AUTONOMY_INVALID_INPUT")
    if ledger.factory_release_sha256 != release.release_sha256:
        raise ValueError("AUTONOMY_RELEASE_MISMATCH")
    resolved_plan = _resolve_plan(release, plan)
    if ledger.autonomy_plan_sha256 != resolved_plan.digest():
        raise ValueError("AUTONOMY_PLAN_MISMATCH")
    release.verify()
    obligations = _obligation_map(release, resolved_plan)
    for item in (*ledger.receipts, *ledger.interventions, *ledger.rejected_attempts):
        _require_known_obligation(obligations, item.obligation_id)
    return obligations


def _latest_receipts(ledger: EvidenceLedger) -> dict[str, EvidenceReceipt]:
    latest: dict[str, EvidenceReceipt] = {}
    for receipt in ledger.receipts:
        latest[receipt.obligation_id] = receipt
    return latest


def _latest_interventions(ledger: EvidenceLedger) -> dict[str, TeachingReceipt]:
    latest: dict[str, TeachingReceipt] = {}
    for receipt in ledger.interventions:
        latest[receipt.obligation_id] = receipt
    return latest


def _validate_current_context(
    checkpoint_sha256: str | None, optimizer_step: int | None,
) -> tuple[str, int] | None:
    if checkpoint_sha256 is None and optimizer_step is None:
        return None
    if (not isinstance(checkpoint_sha256, str) or len(checkpoint_sha256) != 64 or
            any(char not in "0123456789abcdef" for char in checkpoint_sha256) or
            type(optimizer_step) is not int or optimizer_step < 0):
        raise ValueError("AUTONOMY_CURRENT_CHECKPOINT_CONTEXT_INVALID")
    return checkpoint_sha256, optimizer_step


def _receipt_is_current(
    receipt: EvidenceReceipt, current: tuple[str, int] | None,
) -> bool:
    return current is None or (
        receipt.checkpoint_sha256 == current[0] and
        receipt.optimizer_step == current[1])


def closed_obligations(
    release: FactoryRelease, ledger: EvidenceLedger, *, plan: AutonomyPlan | None = None,
    current_checkpoint_sha256: str | None = None,
    current_optimizer_step: int | None = None,
) -> tuple[str, ...]:
    obligations = _validate_ledger(release, ledger, plan=plan)
    current = _validate_current_context(current_checkpoint_sha256, current_optimizer_step)
    latest = _latest_receipts(ledger)
    return tuple(
        identity for identity in obligations
        if identity in latest and latest[identity].passed and
        latest[identity].specimen_count >= obligations[identity].minimum_specimens and
        _receipt_is_current(latest[identity], current))


def evidence_complete_capabilities(
    release: FactoryRelease, ledger: EvidenceLedger, *, plan: AutonomyPlan | None = None,
    current_checkpoint_sha256: str | None = None,
    current_optimizer_step: int | None = None,
) -> tuple[str, ...]:
    resolved_plan = _resolve_plan(release, plan)
    obligations = _validate_ledger(release, ledger, plan=resolved_plan)
    closed = set(closed_obligations(
        release, ledger, plan=resolved_plan,
        current_checkpoint_sha256=current_checkpoint_sha256,
        current_optimizer_step=current_optimizer_step))
    blocked = set(resolved_plan.blocked_capabilities)
    mastered: list[str] = []
    mastered_set: set[str] = set()
    for definition in release_capabilities(release):
        if definition.capability_id in blocked:
            continue
        if not set(definition.prerequisites) <= mastered_set:
            continue
        required = {
            identity for identity, obligation in obligations.items()
            if obligation.capability_id == definition.capability_id}
        if required and required <= closed:
            mastered.append(definition.capability_id)
            mastered_set.add(definition.capability_id)
    return tuple(mastered)
