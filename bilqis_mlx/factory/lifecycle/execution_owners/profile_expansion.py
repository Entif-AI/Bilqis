"""Verify a profile-only widening of an executable Factory release."""
from dataclasses import asdict, dataclass, replace

from bilqis_mlx.errors import ErrorBus, FACTORY

from .adapters import RegisteredSourceAdapter, SourceAdapterRegistry
from .executable_release import ExecutableFactoryRelease
from .execution import (PlanLineage, _digest, _compile_profiled_grades,
                        _projection_digests, _capability_projection_digests,
                        diff_execution_plans)


@dataclass(frozen=True)
class ProfileExpansion:
    profile_sha256: str
    transition_sha256: str
    added_capabilities: tuple[str, ...]


def _verify_compiled_scope(release):
    # Compilation uses descriptor contracts only; source verification remains owned
    # by the release compiler and its verification receipt.
    def unavailable(*args, **kwargs):
        raise RuntimeError

    registry = SourceAdapterRegistry(tuple(
        RegisteredSourceAdapter(item, unavailable, unavailable)
        for item in release.source_adapters))
    grades, capabilities = _compile_profiled_grades(
        release.curriculum, release.source_bindings, release.profile, registry)
    plan = release.execution_plan
    if (grades != plan.grades or capabilities != plan.capabilities or
            _projection_digests(grades, capabilities, release.source_bindings) !=
            plan.projection_digests or
            _capability_projection_digests(capabilities, release.source_bindings) !=
            plan.capability_projection_digests):
        ErrorBus.Raise(FACTORY.PROFILE_EXPANSION.INVALID, reason="FACTORY_PROFILE_EXPANSION_COMPILED_SCOPE_DRIFT")


def verify_profile_expansion(predecessor, successor) -> ProfileExpansion:
    """Prove scope widens over the same source and semantic authorities."""
    if not isinstance(predecessor, ExecutableFactoryRelease) or not isinstance(
            successor, ExecutableFactoryRelease):
        ErrorBus.Raise(FACTORY.PROFILE_EXPANSION.INVALID, reason="FACTORY_PROFILE_EXPANSION_RELEASE_REQUIRED")
    successor.verify_successor_of(predecessor)
    _verify_compiled_scope(predecessor)
    _verify_compiled_scope(successor)
    for field in ("curriculum", "source_bindings"):
        if getattr(predecessor, field) != getattr(successor, field):
            ErrorBus.Raise(FACTORY.PROFILE_EXPANSION.INVALID, reason="FACTORY_PROFILE_EXPANSION_AUTHORITY_DRIFT", field=field)
    for field in ("source_adapters", "answer_modalities"):
        if set(getattr(predecessor, field)) != set(getattr(successor, field)):
            ErrorBus.Raise(FACTORY.PROFILE_EXPANSION.INVALID, reason="FACTORY_PROFILE_EXPANSION_AUTHORITY_DRIFT", field=field)
    if (predecessor.semantic_catalog != successor.semantic_catalog or
            predecessor.semantic_catalog_sha256 != successor.semantic_catalog_sha256 or
            predecessor.semantic_graph_sha256 != successor.semantic_graph_sha256 or
            successor.transition.semantic_geometry != "UNCHANGED"):
        ErrorBus.Raise(FACTORY.PROFILE_EXPANSION.INVALID, reason="FACTORY_PROFILE_EXPANSION_GEOMETRY_DRIFT")
    previous = predecessor.execution_plan.capability_map
    current = successor.execution_plan.capability_map
    if not previous.keys() <= current.keys():
        ErrorBus.Raise(FACTORY.PROFILE_EXPANSION.INVALID, reason="FACTORY_PROFILE_EXPANSION_NARROW_CAPABILITIES")
    providers = {item.adapter_id: item for item in predecessor.source_adapters}
    for capability_id, old in previous.items():
        new = current[capability_id]
        if replace(old, stage=new.stage, provider_parameters=new.provider_parameters,
                   answer_families=new.answer_families) != new:
            ErrorBus.Raise(FACTORY.PROFILE_EXPANSION.INVALID, reason="FACTORY_PROFILE_EXPANSION_CAPABILITY_DRIFT", capability_id=capability_id)
        dimensions = dict(providers[old.provider_id].profile_dimensions)
        old_parameters, new_parameters = dict(old.provider_parameters), dict(new.provider_parameters)
        for name, allowed in dimensions.items():
            if not set(old_parameters.get(name, allowed)) <= set(new_parameters.get(name, allowed)):
                ErrorBus.Raise(FACTORY.PROFILE_EXPANSION.INVALID, reason="FACTORY_PROFILE_EXPANSION_NARROW_DIMENSION", capability_id=capability_id, dimension=name)
        old_answers = {family.kind: set(family.values) for family in old.answer_families}
        new_answers = {family.kind: set(family.values) for family in new.answer_families}
        if old_answers.keys() != new_answers.keys() or any(
                not values <= new_answers[kind] for kind, values in old_answers.items()):
            ErrorBus.Raise(FACTORY.PROFILE_EXPANSION.INVALID, reason="FACTORY_PROFILE_EXPANSION_NARROW_ANSWER", capability_id=capability_id)
    lineage = PlanLineage.from_semantic_catalogs(
        predecessor.execution_plan, successor.execution_plan,
        predecessor.semantic_catalog, successor.semantic_catalog)
    delta = diff_execution_plans(predecessor.execution_plan, successor.execution_plan,
                                 lineage=lineage)
    if successor.transition != delta:
        ErrorBus.Raise(FACTORY.PROFILE_EXPANSION.INVALID, reason="FACTORY_PROFILE_EXPANSION_TRANSITION_DRIFT")
    profile_digest = _digest(asdict(successor.profile))
    proof_digest = _digest({"schema": "bilqis.factory.profile-expansion/v1",
                           "predecessor_release_sha256": predecessor.release_sha256,
                           "successor_release_sha256": successor.release_sha256,
                           "profile_sha256": profile_digest, "delta": asdict(delta)})
    return ProfileExpansion(profile_digest, proof_digest, delta.added_capabilities)
