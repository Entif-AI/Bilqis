"""Append validated evidence and teaching outcomes."""
from __future__ import annotations

from ..model import FactoryRelease
from .evidence_contracts import (
    EvidenceLedger,
    EvidenceReceipt,
    RejectedTeachingAttemptReceipt,
    TeachingReceipt,
)
from .ledger import (
    _latest_receipts,
    _require_known_obligation,
    _validate_current_context,
    _validate_ledger,
    _receipt_is_current,
    evidence_complete_capabilities,
)
from .obligations import _capability_definitions, _coverage_by_capability, _work_item
from .plan_contracts import AutonomyPlan


def record_evidence(
    release: FactoryRelease, ledger: EvidenceLedger, receipt: EvidenceReceipt, *,
    plan: AutonomyPlan | None = None,
    current_checkpoint_sha256: str | None = None,
    current_optimizer_step: int | None = None,
) -> EvidenceLedger:
    obligations = _validate_ledger(release, ledger, plan=plan)
    if not isinstance(receipt, EvidenceReceipt):
        raise TypeError("AUTONOMY_INVALID_EVIDENCE_RECEIPT")
    obligation = _require_known_obligation(obligations, receipt.obligation_id)
    if receipt.passed and receipt.specimen_count < obligation.minimum_specimens:
        raise ValueError("AUTONOMY_INSUFFICIENT_EVIDENCE_SPECIMENS")
    if receipt.evidence_id in {item.evidence_id for item in ledger.receipts}:
        raise ValueError("AUTONOMY_DUPLICATE_EVIDENCE_RECEIPT")
    current = _validate_current_context(current_checkpoint_sha256, current_optimizer_step)
    if current is not None and not _receipt_is_current(receipt, current):
        raise ValueError("AUTONOMY_EVIDENCE_CURRENT_CHECKPOINT_MISMATCH")
    return EvidenceLedger(
        ledger.factory_release_sha256, ledger.autonomy_plan_sha256,
        (*ledger.receipts, receipt), ledger.interventions, ledger.rejected_attempts)


def record_teaching_intervention(
    release: FactoryRelease, ledger: EvidenceLedger, receipt: TeachingReceipt, *,
    plan: AutonomyPlan | None = None,
    current_checkpoint_sha256: str | None = None,
    current_optimizer_step: int | None = None,
) -> EvidenceLedger:
    obligations = _validate_ledger(release, ledger, plan=plan)
    if not isinstance(receipt, TeachingReceipt):
        raise TypeError("AUTONOMY_INVALID_TEACHING_RECEIPT")
    obligation = _require_known_obligation(obligations, receipt.obligation_id)
    latest = _latest_receipts(ledger).get(receipt.obligation_id)
    if latest is None or latest.passed:
        raise ValueError("AUTONOMY_TEACHING_REQUIRES_FAILED_EVIDENCE")
    if (receipt.parent_checkpoint_sha256 != latest.checkpoint_sha256 or
            receipt.parent_optimizer_step != latest.optimizer_step):
        raise ValueError("AUTONOMY_TEACHING_PARENT_EVIDENCE_MISMATCH")
    current = _validate_current_context(current_checkpoint_sha256, current_optimizer_step)
    if current is not None and (
            receipt.parent_checkpoint_sha256 != current[0] or
            receipt.parent_optimizer_step != current[1]):
        raise ValueError("AUTONOMY_TEACHING_CURRENT_CHECKPOINT_MISMATCH")
    work = _work_item(
        release, obligation, evidence_complete_capabilities(release, ledger, plan=plan))
    if receipt.teaching_option_id not in work.teaching_option_ids:
        raise ValueError("AUTONOMY_TEACHING_OPTION_NOT_RELEASED")
    definition = _capability_definitions(release)[obligation.capability_id]
    provider = {item.adapter_id: item for item in release.source_adapters}[
        definition.source_adapter_id]
    coverage = _coverage_by_capability(release)[obligation.capability_id]
    if (not receipt.selected_provider_id or
            not receipt.provider_implementation_sha256 or
            not receipt.specimen_ids or not receipt.specimen_content_sha256 or
            not receipt.variation_axes or receipt.optimizer_step_delta is None):
        raise ValueError("AUTONOMY_TEACHING_PROVENANCE_UNPROVEN")
    if (receipt.selected_provider_id != provider.adapter_id or
            receipt.provider_implementation_sha256 != provider.implementation_sha256):
        raise ValueError("AUTONOMY_TEACHING_PROVIDER_MISMATCH")
    if receipt.variation_axes != coverage.variation_axes:
        raise ValueError("AUTONOMY_TEACHING_VARIATION_AXES_MISMATCH")
    if receipt.intervention_id in {
            item.intervention_id for item in ledger.interventions}:
        raise ValueError("AUTONOMY_DUPLICATE_TEACHING_RECEIPT")
    return EvidenceLedger(
        ledger.factory_release_sha256, ledger.autonomy_plan_sha256,
        ledger.receipts, (*ledger.interventions, receipt), ledger.rejected_attempts)


def record_rejected_teaching_attempt(
    release: FactoryRelease, ledger: EvidenceLedger,
    receipt: RejectedTeachingAttemptReceipt, *,
    plan: AutonomyPlan | None = None,
    current_checkpoint_sha256: str | None = None,
    current_optimizer_step: int | None = None,
) -> EvidenceLedger:
    obligations = _validate_ledger(release, ledger, plan=plan)
    if not isinstance(receipt, RejectedTeachingAttemptReceipt):
        raise TypeError("AUTONOMY_INVALID_REJECTED_TEACHING_ATTEMPT")
    obligation = _require_known_obligation(obligations, receipt.obligation_id)
    latest = _latest_receipts(ledger).get(receipt.obligation_id)
    if (latest is None or latest.passed or
            receipt.parent_evidence_id != latest.evidence_id or
            receipt.retained_checkpoint_sha256 != latest.checkpoint_sha256 or
            receipt.retained_optimizer_step != latest.optimizer_step):
        raise ValueError("AUTONOMY_REJECTED_ATTEMPT_PARENT_EVIDENCE_MISMATCH")
    current = _validate_current_context(current_checkpoint_sha256, current_optimizer_step)
    if current is not None and (
            receipt.retained_checkpoint_sha256 != current[0] or
            receipt.retained_optimizer_step != current[1]):
        raise ValueError("AUTONOMY_REJECTED_ATTEMPT_CURRENT_CHECKPOINT_MISMATCH")
    work = _work_item(
        release, obligation, evidence_complete_capabilities(release, ledger, plan=plan))
    if receipt.teaching_option_id not in work.teaching_option_ids:
        raise ValueError("AUTONOMY_REJECTED_ATTEMPT_OPTION_NOT_RELEASED")
    definition = _capability_definitions(release)[obligation.capability_id]
    provider = {item.adapter_id: item for item in release.source_adapters}[
        definition.source_adapter_id]
    if (receipt.selected_provider_id != provider.adapter_id or
            receipt.provider_implementation_sha256 != provider.implementation_sha256):
        raise ValueError("AUTONOMY_REJECTED_ATTEMPT_PROVIDER_MISMATCH")
    if receipt.attempt_id in {item.attempt_id for item in ledger.rejected_attempts}:
        return ledger
    return EvidenceLedger(
        ledger.factory_release_sha256, ledger.autonomy_plan_sha256,
        ledger.receipts, ledger.interventions, (*ledger.rejected_attempts, receipt))
