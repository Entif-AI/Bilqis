"""Derive immutable learner evidence obligations from Factory releases."""
from __future__ import annotations

from ..model import CoveragePlan, FactoryRelease
from .evidence_contracts import EvidenceKind, EvidenceObligation
from .plan_contracts import AutonomyPlan
from .planning import _resolve_plan, release_capabilities
from .work_contracts import CurriculumWorkItem


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
    """Derive learner evidence obligations from immutable semantic structure."""
    release.verify()
    resolved_plan = _resolve_plan(release, plan)
    definition = _capability_definitions(release).get(capability_id)
    if definition is None:
        raise ValueError("AUTONOMY_UNKNOWN_CAPABILITY")
    coverage = _coverage_by_capability(release)[capability_id]
    declared = _course_capabilities(release)[capability_id]
    axes = coverage.variation_axes

    obligations = [EvidenceObligation(
        f"{capability_id}/direct", capability_id, EvidenceKind.DIRECT,
        "source.direct", coverage.minimum_specimens, axes)]
    obligations.extend(EvidenceObligation(
        f"{capability_id}/projection/{projection.projection_id}",
        capability_id, EvidenceKind.PROJECTION, projection.projection_id,
        projection.minimum_specimens, axes, proof_axes=projection.proof_axes)
        for projection in resolved_plan.projection_evidence
        if projection.capability_id == capability_id)
    obligations.extend(EvidenceObligation(
        f"{capability_id}/supplemental/{item.kind.lower()}/{item.key}",
        capability_id,
        EvidenceKind.PREREQUISITE if item.kind == "PREREQUISITE"
        else EvidenceKind.COMPOSITION,
        item.key, item.minimum_specimens, axes,
        requires_capabilities=item.requires_capabilities)
        for item in resolved_plan.supplemental_evidence
        if item.capability_id == capability_id)
    obligations.extend(EvidenceObligation(
        f"{capability_id}/prerequisite/{predecessor}", capability_id,
        EvidenceKind.PREREQUISITE, predecessor, 1, axes,
        requires_capabilities=(predecessor,))
        for predecessor in definition.prerequisites)
    obligations.extend(EvidenceObligation(
        f"{capability_id}/composition/{constituent}", capability_id,
        EvidenceKind.COMPOSITION, constituent, 1, axes,
        requires_capabilities=(constituent,))
        for constituent in declared.composed_of)
    if resolved_plan.source_composition_audited:
        obligations.extend(EvidenceObligation(
            f"{capability_id}/typed-composition/{edge.producer}/slot/{edge.operand_slot}",
            capability_id, EvidenceKind.COMPOSITION,
            f"{edge.producer}@{edge.operand_slot}", 1, axes,
            requires_capabilities=(edge.producer,))
            for edge in resolved_plan.source_composition_edges
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
            release, capability.capability_id, plan=plan))
    mapping = {item.obligation_id: item for item in obligations}
    if len(mapping) != len(obligations):
        raise ValueError("AUTONOMY_DUPLICATE_EVIDENCE_OBLIGATION")
    return mapping


def _work_item(
    release: FactoryRelease, obligation: EvidenceObligation,
    mastered: tuple[str, ...],
) -> CurriculumWorkItem:
    definition = _capability_definitions(release)[obligation.capability_id]
    options = (tuple(item.option_id for item in release.teaching_options
                     if item.capability_id == obligation.capability_id)
               if isinstance(release, FactoryRelease) else
               release.execution_plan.capability_map[
                   obligation.capability_id].teaching_option_ids)
    return CurriculumWorkItem(
        obligation.capability_id, obligation, options,
        tuple(item for item in mastered if item in definition.prerequisites))
