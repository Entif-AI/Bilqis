"""Compile an executable factory release."""
from __future__ import annotations

from ..adapters import SourceAdapterRegistry
from ..answers import AnswerModalityRegistry
from ..curriculum_definition import CurriculumDefinition, SourceBindingSet
from ..execution import CurriculumProfile, PlanLineage
from .release import ExecutableFactoryRelease

from .. import executable_release as _api


def compile_executable_factory_release(
        curriculum: CurriculumDefinition, source_bindings: SourceBindingSet,
        profile: CurriculumProfile, source_registry: SourceAdapterRegistry,
        answer_registry: AnswerModalityRegistry, *, source_root, graph: dict,
        verification_seed: int,
        predecessor: ExecutableFactoryRelease | None = None,
        lineage: PlanLineage | None = None) -> ExecutableFactoryRelease:
    """Compile and source-verify one immutable v2 FactoryRelease."""
    if (not isinstance(curriculum, _api.CurriculumDefinition) or
            not isinstance(source_bindings, _api.SourceBindingSet) or
            not isinstance(profile, _api.CurriculumProfile) or
            not isinstance(source_registry, _api.SourceAdapterRegistry) or
            not isinstance(answer_registry, _api.AnswerModalityRegistry) or
            type(verification_seed) is not int):
        raise TypeError("FACTORY_EXECUTABLE_RELEASE_INVALID_INPUT")
    semantic_graph_sha256 = _api._digest(graph)
    plan = _api.compile_execution_plan(
        curriculum, profile, source_registry,
        source_bindings=source_bindings, answer_registry=answer_registry)
    canonical_kinds = tuple(dict.fromkeys(
        family.kind
        for grade in curriculum.grades
        for capability in grade.capabilities
        for family in capability.answer_families))
    answer_modalities = tuple(
        answer_registry.require(kind).descriptor
        for kind in canonical_kinds)
    answer_heads = _api._answer_head_bindings(plan, graph, answer_registry)
    source_adapters = _api._provider_descriptors(
        plan, source_bindings, source_registry)
    provider_dimension_policies = tuple(
        policy for descriptor in source_adapters
        for policy in source_registry.dimension_policies(descriptor.adapter_id))
    semantic_catalog = tuple(
        graph.get("tokens") if isinstance(graph, dict) else ())
    _api._require(
        bool(semantic_catalog) and
        len(set(semantic_catalog)) == len(semantic_catalog) and
        all(isinstance(item, str) and item for item in semantic_catalog),
        _api._ReleaseError.SEMANTIC_CATALOG_REQUIRED,
    )
    verification = _api._verification_receipt(
        curriculum, source_bindings, plan, source_registry,
        answer_modalities, answer_heads, source_root=source_root, graph=graph,
        verification_seed=verification_seed)

    predecessor_sha, transition = _api._prepare_predecessor_transition(
        predecessor, plan, semantic_catalog, lineage)
    release = _api.ExecutableFactoryRelease(
        schema=_api.SCHEMA,
        curriculum=curriculum,
        source_bindings=source_bindings,
        profile=profile,
        execution_plan=plan,
        foundation_capability_ids=plan.active_capability_inventory,
        semantic_catalog=semantic_catalog,
        semantic_catalog_sha256=verification.semantic_catalog_sha256,
        source_adapters=source_adapters,
        answer_modalities=answer_modalities,
        answer_heads=answer_heads,
        verification=verification,
        predecessor_release_sha256=predecessor_sha,
        transition=transition,
        release_sha256="0" * 64,
        semantic_graph_sha256=semantic_graph_sha256,
        provider_dimension_policies=provider_dimension_policies,
    )
    release = _api.replace(release, release_sha256=release.expected_digest())
    release.verify()
    release.verify_semantic_catalog(graph)
    if predecessor is not None:
        release.verify_successor_of(predecessor)
    return release
