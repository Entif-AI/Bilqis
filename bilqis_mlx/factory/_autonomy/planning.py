"""Autonomy-plan compilation and validation."""
from __future__ import annotations
from ..model import FactoryRelease
from .contracts import (AutonomyPlan, ProjectionEvidenceSpec, SupplementalEvidenceSpec,
                        SourceCompositionEdge, release_capabilities)

def compile_autonomy_plan(
    release: FactoryRelease, composition_report: dict | None = None,
    *, projection_evidence: tuple[ProjectionEvidenceSpec, ...] = (),
    projection_coverage_debt: tuple[str, ...] = (),
    supplemental_evidence: tuple[SupplementalEvidenceSpec, ...] = (),
    remediation_failure_limit: int = 3,
) -> AutonomyPlan:
    """Bind learner planning to verified typed composition coverage when present.

    Type-compatible edges are not learner work until a source adapter has
    discharged the semantic-coverage debt.  Unresolved or partially witnessed
    consumers remain explicitly blocked instead of being silently omitted.
    """
    release.verify()
    capability_ids = tuple(item.capability_id for item in release_capabilities(release))
    if (type(remediation_failure_limit) is not int or
            remediation_failure_limit < 1 or
            any(not isinstance(item, ProjectionEvidenceSpec)
            for item in projection_evidence) or
            len({(item.capability_id, item.projection_id)
                 for item in projection_evidence}) != len(projection_evidence) or
            any(item.capability_id not in capability_ids
                for item in projection_evidence) or
            len(set(projection_coverage_debt)) != len(projection_coverage_debt) or
            any(not isinstance(item, str) or not item
                for item in projection_coverage_debt)):
        raise ValueError("AUTONOMY_PROJECTION_EVIDENCE_SCOPE_INVALID")
    if (any(not isinstance(item, SupplementalEvidenceSpec)
            for item in supplemental_evidence) or
            len({(item.capability_id, item.kind, item.key)
                 for item in supplemental_evidence}) !=
            len(supplemental_evidence) or
            any(item.capability_id not in capability_ids or
                not set(item.requires_capabilities) <= set(capability_ids)
                for item in supplemental_evidence)):
        raise ValueError("AUTONOMY_SUPPLEMENTAL_EVIDENCE_SCOPE_INVALID")
    projection_blocked = set()
    for item in projection_coverage_debt:
        capability = item.split(":", 1)[0]
        if capability not in capability_ids:
            raise ValueError("AUTONOMY_PROJECTION_COVERAGE_DEBT_SCOPE_INVALID")
        projection_blocked.add(capability)
    if composition_report is None:
        return AutonomyPlan(
            release.release_sha256,
            False,
            coverage_debt=projection_coverage_debt,
            blocked_capabilities=tuple(
                item for item in capability_ids if item in projection_blocked),
            projection_evidence=projection_evidence,
            supplemental_evidence=supplemental_evidence,
        )
    from ...curriculum_compiler import compile_ast
    from ...semantic_coverage import SCHEMA

    if (not isinstance(composition_report, dict) or
            composition_report.get("schema") != SCHEMA or
            composition_report.get("ast_sha256") != compile_ast(release.course).digest()):
        raise ValueError("AUTONOMY_COMPOSITION_REPORT_BINDING_INVALID")
    if set(composition_report.get("capabilities", ())) != set(capability_ids):
        raise ValueError("AUTONOMY_COMPOSITION_REPORT_SCOPE_INVALID")

    source_cohort = composition_report.get("source_witness_cohort_sha256")
    edges = []
    debt = list(projection_coverage_debt)
    blocked = set(projection_blocked)
    deferred = []
    for unresolved in composition_report.get("unresolved", ()):
        capability = unresolved.get("capability") if isinstance(unresolved, dict) else None
        failure = unresolved.get("failure") if isinstance(unresolved, dict) else None
        if not capability or capability not in capability_ids or not failure:
            raise ValueError("AUTONOMY_COMPOSITION_REPORT_UNRESOLVED_INVALID")
        # Typed discovery is advisory.  Multi-root, inverse, and domain-level
        # capabilities may have explicit factory dependencies that the generic
        # signature projection cannot represent.  Preserve that diagnostic
        # without turning parser incompleteness into learner debt.
        deferred.append(f"{capability}:UNRESOLVED:{failure}")

    for raw in composition_report.get("obligations", ()):
        if not isinstance(raw, dict):
            raise ValueError("AUTONOMY_COMPOSITION_REPORT_EDGE_INVALID")
        consumer, producer = raw.get("consumer"), raw.get("producer")
        slot, status = raw.get("operand_slot"), raw.get("status")
        if (consumer not in capability_ids or producer not in capability_ids or
                type(slot) is not int or slot < 0 or not status):
            raise ValueError("AUTONOMY_COMPOSITION_REPORT_EDGE_INVALID")
        covered = status == "SOURCE_CONTRAST_COVERED" and not raw.get("coverage_debt", True)
        if covered:
            edges.append(SourceCompositionEdge(
                consumer=consumer, producer=producer, operand_slot=slot,
                witness_ids=tuple(raw.get("witness_ids", ())),
                source_cohort_sha256=source_cohort,
            ))
        elif not raw.get("declared_prerequisite", False):
            # Type compatibility is only a candidate composition edge.  Until
            # source evidence or an explicit semantic declaration elevates it,
            # keep it visible but do not block the learner on speculative debt.
            deferred.append(f"{consumer}:{producer}:{slot}:{status}")
        else:
            debt.append(f"{consumer}:{producer}:{slot}:{status}")
            blocked.add(consumer)
    edges = sorted(edges, key=lambda item: (item.consumer, item.producer, item.operand_slot))
    deferred = list(dict.fromkeys(deferred))
    return AutonomyPlan(
        release.release_sha256, True, tuple(edges), tuple(debt),
        tuple(item for item in capability_ids if item in blocked),
        tuple(deferred),
        projection_evidence,
        supplemental_evidence,
        remediation_failure_limit,
    )


def next_source_coverage_debt(plan: AutonomyPlan) -> str | None:
    if not isinstance(plan, AutonomyPlan):
        raise TypeError("AUTONOMY_INVALID_PLAN")
    return plan.coverage_debt[0] if plan.coverage_debt else None


def _require_plan_release(factory_release_sha256: str, plan: AutonomyPlan) -> None:
    if plan.factory_release_sha256 != factory_release_sha256:
        raise ValueError("AUTONOMY_PLAN_RELEASE_MISMATCH")


def _resolve_plan(release: FactoryRelease, plan: AutonomyPlan | None) -> AutonomyPlan:
    resolved = compile_autonomy_plan(release) if plan is None else plan
    if not isinstance(resolved, AutonomyPlan):
        raise TypeError("AUTONOMY_INVALID_PLAN")
    _require_plan_release(release.release_sha256, resolved)
    return resolved
