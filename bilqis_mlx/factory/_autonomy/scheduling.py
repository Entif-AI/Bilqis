"""Deterministic autonomy work selection and action routing."""
from __future__ import annotations
from dataclasses import dataclass
from enum import Enum
from ..model import FactoryRelease
from .contracts import AutonomyPlan, release_capabilities
from .evidence_contracts import (CurriculumWorkItem, EvidenceLedger, EvidenceObligation,
                                 TeachingWorkItem)
from .obligations import (_capability_definitions, _latest_interventions, _latest_receipts,
                          _receipt_is_current, _validate_current_context, _validate_ledger,
                          closed_obligations, evidence_complete_capabilities,
                          obligations_for_capability)
from .planning import _resolve_plan, next_source_coverage_debt

def _work_item(
    release: FactoryRelease, obligation: EvidenceObligation,
    mastered: tuple[str, ...],
) -> CurriculumWorkItem:
    definition = _capability_definitions(release)[obligation.capability_id]
    options = (tuple(item.option_id for item in release.teaching_options
                     if item.capability_id == obligation.capability_id)
               if isinstance(release, FactoryRelease) else
               release.execution_plan.capability_map[obligation.capability_id].teaching_option_ids)
    return CurriculumWorkItem(
        capability_id=obligation.capability_id,
        obligation=obligation,
        teaching_option_ids=options,
        evidence_complete_prerequisites=tuple(
            item for item in mastered if item in definition.prerequisites),
    )


def _failed_remediation_cycles(
    ledger: EvidenceLedger, obligation_id: str,
) -> int:
    """Count retained interventions that still failed fresh child evidence.

    A later pass resets the bounded-remediation budget. Rejected challengers
    never appear in the intervention ledger and therefore cannot consume it.
    """
    relevant_receipts = tuple(
        item for item in ledger.receipts
        if item.obligation_id == obligation_id)
    last_pass_index = max(
        (index for index, item in enumerate(relevant_receipts)
         if item.passed), default=-1)
    failed_receipts = tuple(
        item for index, item in enumerate(relevant_receipts)
        if index > last_pass_index and not item.passed)
    failed_evidence_ids = {item.evidence_id for item in failed_receipts}
    failed_children = {
        (item.checkpoint_sha256, item.optimizer_step)
        for item in failed_receipts
    }
    retained_failures = sum(
        1 for item in ledger.interventions
        if (item.obligation_id == obligation_id and
            (item.checkpoint_sha256, item.optimizer_step) in failed_children))
    rejected = sum(
        1 for item in ledger.rejected_attempts
        if (item.obligation_id == obligation_id and
            item.parent_evidence_id in failed_evidence_ids))
    return retained_failures + rejected


def _next_work_decision(
    release: FactoryRelease, ledger: EvidenceLedger, *,
    plan: AutonomyPlan | None = None,
    current_checkpoint_sha256: str | None = None,
    current_optimizer_step: int | None = None,
) -> tuple[CurriculumWorkItem | None, tuple[str, ...]]:
    """Choose useful work while bounding repeated remediation monopolies."""
    _validate_ledger(release, ledger, plan=plan)
    resolved_plan = _resolve_plan(release, plan)
    latest = _latest_receipts(ledger)
    closed = set(closed_obligations(
        release, ledger, plan=resolved_plan,
        current_checkpoint_sha256=current_checkpoint_sha256,
        current_optimizer_step=current_optimizer_step))
    mastered = evidence_complete_capabilities(
        release, ledger, plan=resolved_plan,
        current_checkpoint_sha256=current_checkpoint_sha256,
        current_optimizer_step=current_optimizer_step)
    mastered_set = set(mastered)
    definitions = _capability_definitions(release)
    blocked = set(resolved_plan.blocked_capabilities)

    def eligible(obligation: EvidenceObligation) -> bool:
        definition = definitions[obligation.capability_id]
        return (obligation.obligation_id not in closed and
                obligation.capability_id not in blocked and
                set(definition.prerequisites) <= mastered_set and
                set(obligation.requires_capabilities) <= mastered_set)

    ordered_open: list[EvidenceObligation] = []
    for definition in release_capabilities(release):
        if definition.capability_id in mastered_set:
            continue
        if definition.capability_id in blocked:
            continue
        if not set(definition.prerequisites) <= mastered_set:
            continue
        ordered_open.extend(
            obligation for obligation in obligations_for_capability(
                release, definition.capability_id, plan=resolved_plan)
            if eligible(obligation)
        )
    if not ordered_open:
        return None, ()

    deferred = tuple(
        obligation.obligation_id
        for obligation in ordered_open
        if _failed_remediation_cycles(
            ledger, obligation.obligation_id) >=
            resolved_plan.remediation_failure_limit
    )
    deferred_set = set(deferred)
    selectable = tuple(
        item for item in ordered_open
        if item.obligation_id not in deferred_set)
    if not selectable:
        return None, deferred
    selectable_ids = {item.obligation_id for item in selectable}

    # Failed work outranks new breadth until the bounded remediation limit.
    for receipt in reversed(ledger.receipts):
        if receipt.passed or receipt.obligation_id not in selectable_ids:
            continue
        obligation = next(
            item for item in selectable
            if item.obligation_id == receipt.obligation_id)
        if latest[receipt.obligation_id] == receipt:
            return _work_item(release, obligation, mastered), deferred

    return _work_item(release, selectable[0], mastered), deferred


def next_work(
    release: FactoryRelease, ledger: EvidenceLedger, *, plan: AutonomyPlan | None = None,
    current_checkpoint_sha256: str | None = None,
    current_optimizer_step: int | None = None,
) -> CurriculumWorkItem | None:
    """Return the next legal semantic proof target, never a training command."""
    return _next_work_decision(
        release, ledger, plan=plan,
        current_checkpoint_sha256=current_checkpoint_sha256,
        current_optimizer_step=current_optimizer_step)[0]

class AutonomyActionKind(str, Enum):
    SOURCE_COVERAGE = "SOURCE_COVERAGE"
    TEACHING = "TEACHING"
    LEARNING_EVIDENCE = "LEARNING_EVIDENCE"
    SAFE_HOLD = "SAFE_HOLD"
    QUALIFICATION = "QUALIFICATION"


@dataclass(frozen=True)
class AutonomyAction:
    kind: AutonomyActionKind
    source_coverage_debt: str | None = None
    evidence_work: CurriculumWorkItem | None = None
    teaching_work: TeachingWorkItem | None = None
    deferred_obligation_ids: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        if not isinstance(self.kind, AutonomyActionKind):
            raise ValueError("AUTONOMY_ACTION_KIND_INVALID")
        if (len(set(self.deferred_obligation_ids)) !=
                len(self.deferred_obligation_ids) or
                any(not isinstance(item, str) or not item
                    for item in self.deferred_obligation_ids)):
            raise ValueError("AUTONOMY_ACTION_DEFERRAL_INVALID")
        if self.kind is AutonomyActionKind.SOURCE_COVERAGE:
            if (not self.source_coverage_debt or self.evidence_work is not None or
                    self.teaching_work is not None or
                    self.deferred_obligation_ids):
                raise ValueError("AUTONOMY_SOURCE_ACTION_INVALID")
        elif self.kind is AutonomyActionKind.TEACHING:
            if (self.source_coverage_debt is not None or self.evidence_work is not None or
                    self.teaching_work is None):
                raise ValueError("AUTONOMY_TEACHING_ACTION_INVALID")
        elif self.kind is AutonomyActionKind.LEARNING_EVIDENCE:
            if (self.source_coverage_debt is not None or self.evidence_work is None or
                    self.teaching_work is not None):
                raise ValueError("AUTONOMY_LEARNING_ACTION_INVALID")
        elif self.kind is AutonomyActionKind.SAFE_HOLD:
            if (self.source_coverage_debt is not None or
                    self.evidence_work is not None or
                    self.teaching_work is not None or
                    not self.deferred_obligation_ids):
                raise ValueError("AUTONOMY_SAFE_HOLD_ACTION_INVALID")
        elif (self.source_coverage_debt is not None or self.evidence_work is not None or
              self.teaching_work is not None or self.deferred_obligation_ids):
            raise ValueError("AUTONOMY_QUALIFICATION_ACTION_INVALID")


def next_action(
    release: FactoryRelease, ledger: EvidenceLedger, *, plan: AutonomyPlan | None = None,
    current_checkpoint_sha256: str | None = None,
    current_optimizer_step: int | None = None,
) -> AutonomyAction:
    """Route one autonomous iteration without performing the selected work."""
    _validate_ledger(release, ledger, plan=plan)
    resolved_plan = _resolve_plan(release, plan)
    debt = next_source_coverage_debt(resolved_plan)
    if debt is not None:
        return AutonomyAction(AutonomyActionKind.SOURCE_COVERAGE,
                              source_coverage_debt=debt)
    work, deferred = _next_work_decision(
        release, ledger, plan=resolved_plan,
        current_checkpoint_sha256=current_checkpoint_sha256,
        current_optimizer_step=current_optimizer_step)
    if work is None and deferred:
        return AutonomyAction(
            AutonomyActionKind.SAFE_HOLD,
            deferred_obligation_ids=deferred)
    if work is not None:
        latest_failed = _latest_receipts(ledger).get(work.obligation.obligation_id)
        current = _validate_current_context(
            current_checkpoint_sha256, current_optimizer_step)
        if (latest_failed is not None and not latest_failed.passed and
                _receipt_is_current(latest_failed, current)):
            latest_intervention = _latest_interventions(ledger).get(
                work.obligation.obligation_id)
            if (latest_intervention is None or
                    latest_intervention.parent_checkpoint_sha256 !=
                    latest_failed.checkpoint_sha256 or
                    latest_intervention.parent_optimizer_step !=
                    latest_failed.optimizer_step):
                return AutonomyAction(
                    AutonomyActionKind.TEACHING,
                    teaching_work=TeachingWorkItem(
                        work.capability_id, work.obligation,
                        work.teaching_option_ids, latest_failed),
                    deferred_obligation_ids=deferred)
        return AutonomyAction(AutonomyActionKind.LEARNING_EVIDENCE,
                              evidence_work=work,
                              deferred_obligation_ids=deferred)
    return AutonomyAction(AutonomyActionKind.QUALIFICATION)
