"""Evidence obligations and current-ledger projections."""
from __future__ import annotations
from ..model import CoveragePlan, FactoryRelease
from .contracts import AutonomyPlan, is_factory_release, release_capabilities
from .evidence_contracts import (EvidenceKind, EvidenceObligation, EvidenceReceipt,
                                 EvidenceLedger, TeachingReceipt)
from .planning import _resolve_plan

def _require_known_obligation(obligations, obligation_id):
    obligation = obligations.get(obligation_id)
    if obligation is None:
        raise ValueError("AUTONOMY_UNKNOWN_EVIDENCE_OBLIGATION")
    return obligation

def _capability_definitions(release: FactoryRelease):
    return {item.capability_id: item for item in release_capabilities(release)}


def _course_capabilities(release: FactoryRelease):
    return (release.course.capability_map if isinstance(release, FactoryRelease)
            else release.execution_plan.capability_map)


def _coverage_by_capability(release: FactoryRelease):
    if isinstance(release, FactoryRelease):
        return {item.capability_id: item for item in release.coverage_plans}
    return {item.capability_id: CoveragePlan(
        item.capability_id, item.variation_axes, item.exam_item_count)
        for item in release.execution_plan.capabilities}


def obligations_for_capability(
    release: FactoryRelease, capability_id: str, *, plan: AutonomyPlan | None = None,
) -> tuple[EvidenceObligation, ...]:
    """Derive learner evidence obligations from immutable semantic structure.

    ``CoveragePlan.variation_axes`` constrain *how* witnesses must be generated;
    they are attached to every learner obligation but are not themselves claims
    the learner has to master.
    """
    release.verify()
    resolved_plan = _resolve_plan(release, plan)
    definition = _capability_definitions(release).get(capability_id)
    if definition is None:
        raise ValueError("AUTONOMY_UNKNOWN_CAPABILITY")
    coverage = _coverage_by_capability(release)[capability_id]
    declared = _course_capabilities(release)[capability_id]
    axes = coverage.variation_axes

    obligations = [EvidenceObligation(
        obligation_id=f"{capability_id}/direct",
        capability_id=capability_id,
        kind=EvidenceKind.DIRECT,
        key="source.direct",
        minimum_specimens=coverage.minimum_specimens,
        generation_axes=axes,
    )]
    obligations.extend(EvidenceObligation(
        obligation_id=(
            f"{capability_id}/projection/{projection.projection_id}"),
        capability_id=capability_id,
        kind=EvidenceKind.PROJECTION,
        key=projection.projection_id,
        minimum_specimens=projection.minimum_specimens,
        generation_axes=axes,
        proof_axes=projection.proof_axes,
    ) for projection in resolved_plan.projection_evidence
      if projection.capability_id == capability_id)
    obligations.extend(EvidenceObligation(
        obligation_id=(
            f"{capability_id}/supplemental/{item.kind.lower()}/{item.key}"),
        capability_id=capability_id,
        kind=(EvidenceKind.PREREQUISITE
              if item.kind == "PREREQUISITE"
              else EvidenceKind.COMPOSITION),
        key=item.key,
        minimum_specimens=item.minimum_specimens,
        generation_axes=axes,
        requires_capabilities=item.requires_capabilities,
    ) for item in resolved_plan.supplemental_evidence
      if item.capability_id == capability_id)
    obligations.extend(EvidenceObligation(
        obligation_id=f"{capability_id}/prerequisite/{predecessor}",
        capability_id=capability_id,
        kind=EvidenceKind.PREREQUISITE,
        key=predecessor,
        minimum_specimens=1,
        generation_axes=axes,
        requires_capabilities=(predecessor,),
    ) for predecessor in definition.prerequisites)
    obligations.extend(EvidenceObligation(
        obligation_id=f"{capability_id}/composition/{constituent}",
        capability_id=capability_id,
        kind=EvidenceKind.COMPOSITION,
        key=constituent,
        minimum_specimens=1,
        generation_axes=axes,
        requires_capabilities=(constituent,),
    ) for constituent in declared.composed_of)
    if resolved_plan.source_composition_audited:
        obligations.extend(EvidenceObligation(
            obligation_id=(f"{capability_id}/typed-composition/{edge.producer}/"
                           f"slot/{edge.operand_slot}"),
            capability_id=capability_id,
            kind=EvidenceKind.COMPOSITION,
            key=f"{edge.producer}@{edge.operand_slot}",
            minimum_specimens=1,
            generation_axes=axes,
            requires_capabilities=(edge.producer,),
        ) for edge in resolved_plan.source_composition_edges
          if edge.consumer == capability_id)

    identities = tuple(item.obligation_id for item in obligations)
    if len(set(identities)) != len(identities):
        raise ValueError("AUTONOMY_DUPLICATE_EVIDENCE_OBLIGATION")
    return tuple(obligations)


def _obligation_map(
    release: FactoryRelease, plan: AutonomyPlan | None = None,
) -> dict[str, EvidenceObligation]:
    obligations = tuple(
        obligation
        for capability in release_capabilities(release)
        for obligation in obligations_for_capability(
            release, capability.capability_id, plan=plan)
    )
    mapping = {item.obligation_id: item for item in obligations}
    if len(mapping) != len(obligations):
        raise ValueError("AUTONOMY_DUPLICATE_EVIDENCE_OBLIGATION")
    return mapping


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
    for item in (
            *ledger.receipts, *ledger.interventions, *ledger.rejected_attempts):
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
    """Validate an explicit causal checkpoint context, if a caller supplies one."""
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
    current = _validate_current_context(
        current_checkpoint_sha256, current_optimizer_step)
    latest = _latest_receipts(ledger)
    return tuple(
        identity for identity in obligations
        if identity in latest and latest[identity].passed and
        latest[identity].specimen_count >= obligations[identity].minimum_specimens and
        _receipt_is_current(latest[identity], current)
    )


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
            if obligation.capability_id == definition.capability_id
        }
        if required and required <= closed:
            mastered.append(definition.capability_id)
            mastered_set.add(definition.capability_id)
    return tuple(mastered)
