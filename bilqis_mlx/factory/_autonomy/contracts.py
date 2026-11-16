"""Autonomy planning contracts and release projections."""
from __future__ import annotations
from dataclasses import asdict, dataclass
import hashlib
import json
from ..model import CapabilityDefinition, FactoryRelease

def _digest(value) -> str:
    return hashlib.sha256(json.dumps(
        value, sort_keys=True, separators=(",", ":"), ensure_ascii=False,
        allow_nan=False).encode()).hexdigest()


@dataclass(frozen=True)
class SourceCompositionEdge:
    consumer: str
    producer: str
    operand_slot: int
    witness_ids: tuple[str, ...]
    source_cohort_sha256: str

    def __post_init__(self) -> None:
        if (not self.consumer or not self.producer or
                type(self.operand_slot) is not int or self.operand_slot < 0 or
                not self.witness_ids or len(set(self.witness_ids)) != len(self.witness_ids) or
                any(not isinstance(item, str) or not item for item in self.witness_ids) or
                not isinstance(self.source_cohort_sha256, str) or
                len(self.source_cohort_sha256) != 64 or
                any(char not in "0123456789abcdef" for char in self.source_cohort_sha256)):
            raise ValueError("AUTONOMY_SOURCE_COMPOSITION_EDGE_INVALID")


@dataclass(frozen=True)
class ProjectionEvidenceSpec:
    """One source-supported learner-proof projection bound into a plan."""

    capability_id: str
    projection_id: str
    minimum_specimens: int
    proof_axes: tuple[str, ...]

    def __post_init__(self) -> None:
        if (not isinstance(self.capability_id, str) or not self.capability_id or
                not isinstance(self.projection_id, str) or not self.projection_id or
                type(self.minimum_specimens) is not int or
                self.minimum_specimens < 1 or not self.proof_axes or
                len(set(self.proof_axes)) != len(self.proof_axes) or
                any(not isinstance(item, str) or not item
                    for item in self.proof_axes)):
            raise ValueError("AUTONOMY_PROJECTION_EVIDENCE_SPEC_INVALID")


@dataclass(frozen=True)
class SupplementalEvidenceSpec:
    """Provider-owned proof dependency that does not rewrite Course semantics."""

    capability_id: str
    kind: str
    key: str
    requires_capabilities: tuple[str, ...]
    minimum_specimens: int = 1

    def __post_init__(self) -> None:
        if (not isinstance(self.capability_id, str) or not self.capability_id or
                self.kind not in {"PREREQUISITE", "COMPOSITION"} or
                not isinstance(self.key, str) or not self.key or
                not self.requires_capabilities or
                len(set(self.requires_capabilities)) !=
                len(self.requires_capabilities) or
                any(not isinstance(item, str) or not item
                    for item in self.requires_capabilities) or
                type(self.minimum_specimens) is not int or
                self.minimum_specimens < 1):
            raise ValueError("AUTONOMY_SUPPLEMENTAL_EVIDENCE_SPEC_INVALID")


@dataclass(frozen=True)
class AutonomyPlan:
    factory_release_sha256: str
    source_composition_audited: bool
    source_composition_edges: tuple[SourceCompositionEdge, ...] = ()
    coverage_debt: tuple[str, ...] = ()
    blocked_capabilities: tuple[str, ...] = ()
    deferred_composition_candidates: tuple[str, ...] = ()
    projection_evidence: tuple[ProjectionEvidenceSpec, ...] = ()
    supplemental_evidence: tuple[SupplementalEvidenceSpec, ...] = ()
    remediation_failure_limit: int = 3

    def __post_init__(self) -> None:
        if (not isinstance(self.factory_release_sha256, str) or
                len(self.factory_release_sha256) != 64 or
                any(char not in "0123456789abcdef" for char in self.factory_release_sha256) or
                type(self.source_composition_audited) is not bool or
                any(not isinstance(item, SourceCompositionEdge)
                    for item in self.source_composition_edges) or
                len(set(self.coverage_debt)) != len(self.coverage_debt) or
                any(not isinstance(item, str) or not item for item in self.coverage_debt) or
                len(set(self.blocked_capabilities)) != len(self.blocked_capabilities) or
                any(not isinstance(item, str) or not item
                    for item in self.blocked_capabilities) or
                len(set(self.deferred_composition_candidates)) !=
                len(self.deferred_composition_candidates) or
                any(not isinstance(item, str) or not item
                    for item in self.deferred_composition_candidates) or
                any(not isinstance(item, ProjectionEvidenceSpec)
                    for item in self.projection_evidence) or
                len({(item.capability_id, item.projection_id)
                     for item in self.projection_evidence}) !=
                len(self.projection_evidence) or
                any(not isinstance(item, SupplementalEvidenceSpec)
                    for item in self.supplemental_evidence) or
                len({(item.capability_id, item.kind, item.key)
                     for item in self.supplemental_evidence}) !=
                len(self.supplemental_evidence) or
                type(self.remediation_failure_limit) is not int or
                self.remediation_failure_limit < 1):
            raise ValueError("AUTONOMY_PLAN_INVALID")

    def digest(self) -> str:
        payload = asdict(self)
        # Preserve all existing v1 plan identities when no projection contract
        # has been attached. Old durable autonomy snapshots therefore remain
        # readable without a state migration merely because this capability
        # was added.
        if not self.projection_evidence:
            payload.pop("projection_evidence", None)
        if not self.supplemental_evidence:
            payload.pop("supplemental_evidence", None)
        if self.remediation_failure_limit == 3:
            payload.pop("remediation_failure_limit", None)
        return _digest(payload)


def is_factory_release(release) -> bool:
    from ..executable_release import ExecutableFactoryRelease
    return isinstance(release, (FactoryRelease, ExecutableFactoryRelease))


def release_capabilities(release):
    """Project autonomy facts from the admitted executable plan or historical v1."""
    if isinstance(release, FactoryRelease):
        return release.capabilities
    return tuple(CapabilityDefinition(
        item.capability_id, item.grade_id, item.prerequisites,
        item.provider_id, item.oracle_id,
        tuple(family.kind for family in item.answer_families))
        for item in release.execution_plan.capabilities)

