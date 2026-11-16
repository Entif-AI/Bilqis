"""Compile and bind generation-local C05 retention protection indexes."""
from __future__ import annotations

from bilqis_mlx.semantics.domains import contract_digest

from ..baseline.lifecycle import BaselineLedger
from ..capability_evaluation import _invalid
from .protection_plan import (
    ProtectionEdge,
    ProtectionReason,
    RetentionProtectionPlan,
    RetentionTargetPlan,
)


def policy_epoch_sha256(evidence_stage) -> str:
    from bilqis_mlx.learning.retention_policy import MASTERY_DEBT_POWER
    from .._factory_retention_support import (
        C05_PROBE_EACH, C05_PROTECTED_REFERENCE_LOSS,
    )
    return contract_digest({
        "schema": "bilqis.mlx.c05-retention-policy-epoch/v1",
        "evidence_stage": evidence_stage.value,
        "foundation_policy_schema": "bilqis.c05.foundation-retention-policy/v2",
        "strict_policy_schema": "bilqis.c05.retention-policy/v2",
        "probe_each": C05_PROBE_EACH,
        "protected_reference_loss": C05_PROTECTED_REFERENCE_LOSS,
        "mastery_debt_power": MASTERY_DEBT_POWER,
    })


def _scope_sha256(release, groups) -> str:
    return contract_digest({
        "curriculum": release.execution_plan.curriculum_sha256,
        "profile": release.execution_plan.profile_id,
        "groups": tuple(groups),
    })


def _rubric_sha256(release) -> str:
    return contract_digest(tuple(
        (grade.grade_id, grade.assessment_blueprint_sha256)
        for grade in release.execution_plan.grades))


def _current_established_capabilities(
        ledger, release, *, policy_sha256, rubric_sha256,
        source_authority_registry_sha256, correction_frontier_sha256,
        evaluation_contract_sha256, evidence_stage):
    admitted = {item.capability_id for item in release.execution_plan.capabilities}
    source_sha256 = release.execution_plan.projection_digests.source
    result = set()
    for measurement in ledger.measurements:
        comparison = measurement.comparison
        if (comparison.capability_id in admitted
                and comparison.factory_release_sha256 == release.release_sha256
                and comparison.semantic_catalog_sha256
                == release.semantic_catalog_sha256
                and comparison.rubric_sha256 == rubric_sha256
                and comparison.policy_sha256 == policy_sha256
                and comparison.source_sha256 == source_sha256
                and comparison.source_authority_registry_sha256
                == source_authority_registry_sha256
                and comparison.correction_frontier_sha256
                == correction_frontier_sha256
                and comparison.evaluation_contract_sha256
                == evaluation_contract_sha256
                and comparison.evidence_stage == evidence_stage.value):
            result.add(comparison.capability_id)
    return tuple(sorted(result))


def _relation_indexes(capabilities):
    admitted = {item.capability_id for item in capabilities}
    reverse = {capability: set() for capability in admitted}
    constituent_members = {}
    for item in capabilities:
        for dependency in (*item.prerequisites, *item.composed_of):
            if dependency in admitted:
                reverse[dependency].add(item.capability_id)
        for constituent in item.composed_of:
            if constituent in admitted:
                constituent_members.setdefault(constituent, set()).add(
                    item.capability_id)
    return admitted, reverse, constituent_members


def _target_edges(item, admitted, reverse, constituent_members):
    edges = set()
    for dependency in item.prerequisites:
        if dependency in admitted:
            edges.add((dependency, ProtectionReason.PREREQUISITE,
                       item.capability_id))
    for constituent in item.composed_of:
        if constituent in admitted:
            edges.add((constituent, ProtectionReason.CONSTITUENT,
                       item.capability_id))
            for peer in constituent_members.get(constituent, ()):
                if peer != item.capability_id:
                    edges.add((peer, ProtectionReason.SHARED_CONSTITUENT,
                               constituent))
    for dependent in reverse[item.capability_id]:
        if dependent != item.capability_id:
            edges.add((dependent, ProtectionReason.DEPENDENT,
                       item.capability_id))
    return tuple(ProtectionEdge(*edge) for edge in sorted(
        edges, key=lambda value: (value[0], value[1].value, value[2])))


def _compile_plan(
        release, *, established_capability_ids, retained_evidence_sha256,
        policy_sha256, accepted_generation, accepted_manifest_sha256,
        evidence_stage):
    capabilities = tuple(release.execution_plan.capabilities)
    if not capabilities:
        _invalid("BAMF_C05_RETENTION_PROTECTION_PLAN_INVALID")
    by_id = {item.capability_id: item for item in capabilities}
    if len(by_id) != len(capabilities):
        _invalid("BAMF_C05_RETENTION_PROTECTION_PLAN_INVALID")
    established = set(established_capability_ids)
    admitted, reverse, constituent_members = _relation_indexes(capabilities)
    if not established <= admitted:
        _invalid("BAMF_C05_RETENTION_PROTECTION_PLAN_INVALID")

    targets = []
    for item in capabilities:
        affected_edges = _target_edges(
            item, admitted, reverse, constituent_members)
        protected = tuple(sorted({
            edge.capability_id for edge in affected_edges
            if edge.capability_id in established
        }))
        evaluated = (item.capability_id, *protected)
        groups = tuple((capability, by_id[capability].grade_id)
                       for capability in evaluated)
        targets.append(RetentionTargetPlan(
            item.capability_id, item.grade_id, affected_edges, protected, groups,
            _scope_sha256(release, groups),
            _scope_sha256(release, ((item.capability_id, item.grade_id),))))

    grade_definition_sha256 = contract_digest(tuple(
        (
            grade.grade_id,
            grade.capabilities,
            grade.teaching_stages,
            grade.cumulative_scope,
            grade.assessment_blueprint_sha256,
        )
        for grade in release.execution_plan.grades))
    return RetentionProtectionPlan(
        release.release_sha256, release.execution_plan.digest(),
        grade_definition_sha256, retained_evidence_sha256, policy_sha256,
        _rubric_sha256(release), release.execution_plan.projection_digests.source,
        accepted_generation, accepted_manifest_sha256, evidence_stage.value,
        tuple(sorted(established)), tuple(targets))


def bind_retention_protection_plan(cache, release, parent, evidence_stage):
    """Compile once per accepted generation, then serve direct target lookups."""
    from bilqis_mlx.runtime.bamf_bundle.execution_cache import (
        require_accepted_execution_cache,
    )

    cache = require_accepted_execution_cache(cache)
    ledger = BaselineLedger.from_optional_record(parent.baseline_evidence)
    policy_sha256 = policy_epoch_sha256(evidence_stage)
    rubric_sha256 = _rubric_sha256(release)
    correction_sha256 = contract_digest(parent.correction_frontier)
    evaluation_sha256 = contract_digest(parent.evaluation_contract)
    retained_evidence_sha256 = contract_digest({
        "schema": "bilqis.mlx.c05-retained-evidence-generation/v1",
        "baseline_ledger_sha256": ledger.digest,
        "correction_frontier_sha256": correction_sha256,
        "evaluation_contract_sha256": evaluation_sha256,
        "source_authority_registry_sha256":
            cache.source_authority_registry_sha256,
    })
    current = getattr(cache, "_retention_protection_plan", None)
    if current is not None:
        if (type(current) is not RetentionProtectionPlan
                or current.factory_release_sha256 != release.release_sha256
                or current.retained_evidence_sha256 != retained_evidence_sha256
                or current.accepted_generation != cache.generation
                or current.accepted_manifest_sha256
                != cache.accepted_manifest_sha256):
            _invalid("BAMF_C05_RETENTION_PROTECTION_PLAN_DRIFT")
        return current
    established = _current_established_capabilities(
        ledger, release,
        policy_sha256=policy_sha256, rubric_sha256=rubric_sha256,
        source_authority_registry_sha256=cache.source_authority_registry_sha256,
        correction_frontier_sha256=correction_sha256,
        evaluation_contract_sha256=evaluation_sha256,
        evidence_stage=evidence_stage)
    result = _compile_plan(
        release, established_capability_ids=established,
        retained_evidence_sha256=retained_evidence_sha256,
        policy_sha256=policy_sha256, accepted_generation=cache.generation,
        accepted_manifest_sha256=cache.accepted_manifest_sha256,
        evidence_stage=evidence_stage)
    object.__setattr__(cache, "_retention_protection_plan", result)
    return result


def require_retention_protection_plan(cache, release):
    """Ordinary retention may only consume a precompiled accepted-generation plan."""
    from bilqis_mlx.runtime.bamf_bundle.execution_cache import (
        require_accepted_execution_cache,
    )

    cache = require_accepted_execution_cache(cache)
    current = getattr(cache, "_retention_protection_plan", None)
    if (type(current) is not RetentionProtectionPlan
            or current.factory_release_sha256 != release.release_sha256
            or current.accepted_generation != cache.generation
            or current.accepted_manifest_sha256 != cache.accepted_manifest_sha256):
        _invalid("BAMF_C05_RETENTION_PROTECTION_PLAN_PRECOMPUTE_REQUIRED")
    return current


__all__ = (
    "bind_retention_protection_plan", "policy_epoch_sha256",
    "require_retention_protection_plan",
)
