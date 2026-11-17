"""Compile provider-declared, neural-inert dimension progression."""
from __future__ import annotations

from dataclasses import dataclass, replace

from .execution import CapabilityProfile, CurriculumProfile, GradeProfile
from .executable_release import (
    ExecutableFactoryRelease, compile_successor_profile_release)
from .model import ProviderDimensionError
from .profile_expansion import verify_profile_expansion


@dataclass(frozen=True)
class ProviderDimensionState:
    provider_id: str
    dimension_id: str
    parameter_name: str
    value: str
    terminal: bool
    telemetry_projection: str


@dataclass(frozen=True)
class ProviderDimensionTransition:
    previous: ProviderDimensionState
    current: ProviderDimensionState
    profile: CurriculumProfile
    release: ExecutableFactoryRelease


def _policy(release, dimension_id):
    policies = tuple(
        item for item in release.provider_dimension_policies
        if item.dimension_id == dimension_id)
    if len(policies) != 1:
        raise ValueError(ProviderDimensionError.POLICY_REQUIRED.value)
    return policies[0]


def _descriptor(release, provider_id):
    descriptors = tuple(
        item for item in release.source_adapters if item.adapter_id == provider_id)
    if len(descriptors) != 1:
        raise ValueError(ProviderDimensionError.PROVIDER_REQUIRED.value)
    return descriptors[0]


def _selected_values(policy, domain, value):
    try:
        index = domain.index(value)
    except ValueError as exc:
        raise ValueError(ProviderDimensionError.VALUE_OUTSIDE_DOMAIN.value) from exc
    return domain[:index + 1]


def _execution_value(execution, policy, descriptor):
    domain = dict(descriptor.profile_dimensions)[policy.parameter_name]
    selected = dict(execution.provider_parameters).get(policy.parameter_name, domain)
    if not selected:
        raise ValueError(ProviderDimensionError.SELECTION_EMPTY.value)
    if selected != domain[:len(selected)]:
        raise ValueError(ProviderDimensionError.SELECTION_DRIFT.value)
    value = selected[-1]
    if value not in policy.progression_values:
        raise ValueError(ProviderDimensionError.PROGRESS_STATE_INVALID.value)
    if policy.answer_family_kind is not None:
        answers = {
            family.kind: family.values for family in execution.answer_families}
        if answers.get(policy.answer_family_kind) != selected:
            raise ValueError(ProviderDimensionError.ANSWER_STATE_DRIFT.value)
    return value


def provider_dimension_state(
        release: ExecutableFactoryRelease, dimension_id: str) -> ProviderDimensionState:
    """Project one exact current dimension value from immutable release state."""
    if not isinstance(release, ExecutableFactoryRelease):
        raise TypeError(ProviderDimensionError.RELEASE_REQUIRED.value)
    release.verify()
    policy = _policy(release, dimension_id)
    descriptor = _descriptor(release, policy.provider_id)
    executions = tuple(
        item for item in release.execution_plan.capabilities
        if item.provider_id == policy.provider_id)
    if not executions:
        raise ValueError(ProviderDimensionError.EXECUTION_REQUIRED.value)
    values = {
        _execution_value(item, policy, descriptor) for item in executions}
    if len(values) != 1:
        raise ValueError(ProviderDimensionError.EXECUTION_DRIFT.value)
    value = next(iter(values))
    return ProviderDimensionState(
        policy.provider_id, policy.dimension_id, policy.parameter_name, value,
        value == policy.terminal_value, policy.telemetry_projection)


def provider_dimension_states(
        release: ExecutableFactoryRelease) -> tuple[ProviderDimensionState, ...]:
    return tuple(
        provider_dimension_state(release, policy.dimension_id)
        for policy in release.provider_dimension_policies)


def provider_dimension_telemetry(release: ExecutableFactoryRelease) -> tuple[dict, ...]:
    """Render typed telemetry directly from the certified release state."""
    return tuple({
        "provider_id": state.provider_id,
        "provider_dimension_id": state.dimension_id,
        "provider_dimension_value": state.value,
        "provider_dimension_terminal": state.terminal,
        "telemetry_projection": state.telemetry_projection,
    } for state in provider_dimension_states(release))


def _capability_profile(release, policy, execution, selected):
    grade = next((
        item for item in release.profile.grades
        if item.grade_id == execution.grade_id), None)
    current = next(
        (item for item in grade.capabilities
         if item.capability_id == execution.capability_id), None) if grade else None
    current = current or CapabilityProfile(execution.capability_id)
    descriptor = _descriptor(release, policy.provider_id)
    parameters = dict(current.provider_parameters)
    parameters[policy.parameter_name] = selected
    ordered_parameters = tuple(
        (name, parameters[name]) for name, _ in descriptor.profile_dimensions
        if name in parameters)
    answers = dict(current.answer_family_values)
    if policy.answer_family_kind is not None:
        answers[policy.answer_family_kind] = selected
    canonical = release.curriculum.capability_map[execution.capability_id]
    ordered_answers = tuple(
        (family.kind, answers[family.kind]) for family in canonical.answer_families
        if family.kind in answers)
    return replace(
        current, provider_parameters=ordered_parameters,
        answer_family_values=ordered_answers)


def _successor_profile(release, policy, next_value):
    descriptor = _descriptor(release, policy.provider_id)
    domain = dict(descriptor.profile_dimensions)[policy.parameter_name]
    selected = _selected_values(policy, domain, next_value)
    by_grade = {item.grade_id: item for item in release.profile.grades}
    order = [item.grade_id for item in release.profile.grades]
    for execution in release.execution_plan.capabilities:
        if execution.provider_id != policy.provider_id:
            continue
        grade = by_grade.get(execution.grade_id, GradeProfile(execution.grade_id))
        profiles = {item.capability_id: item for item in grade.capabilities}
        profiles[execution.capability_id] = _capability_profile(
            release, policy, execution, selected)
        capability_order = tuple(
            item.capability_id for item in release.execution_plan.capabilities
            if item.grade_id == execution.grade_id)
        grade = replace(grade, capabilities=tuple(
            profiles[capability] for capability in capability_order
            if capability in profiles))
        by_grade[execution.grade_id] = grade
        if execution.grade_id not in order:
            order.append(execution.grade_id)
    marker = "/provider-dimension/"
    base = release.profile.profile_id.split(marker, 1)[0]
    profile_id = f"{base}{marker}{policy.dimension_id}/{next_value}"
    return CurriculumProfile(profile_id, tuple(by_grade[name] for name in order))


def next_provider_dimension_profile(
        release: ExecutableFactoryRelease, dimension_id: str) -> CurriculumProfile | None:
    """Project the next adjacent profile without adopting or mutating runtime state."""
    current = provider_dimension_state(release, dimension_id)
    if current.terminal:
        return None
    policy = _policy(release, dimension_id)
    next_value = policy.progression_values[
        policy.progression_values.index(current.value) + 1]
    return _successor_profile(release, policy, next_value)


def compile_provider_dimension_successor(
        predecessor: ExecutableFactoryRelease, dimension_id: str,
        source_registry, answer_registry, *, source_root, graph: dict,
        verification_seed: int) -> ProviderDimensionTransition | None:
    """Compile exactly one authorized adjacent provider-dimension transition."""
    previous = provider_dimension_state(predecessor, dimension_id)
    if previous.terminal:
        return None
    policy = _policy(predecessor, dimension_id)
    if policy.changes_semantic_geometry:
        raise ValueError(ProviderDimensionError.GEOMETRY_OWNER_REQUIRED.value)
    index = policy.progression_values.index(previous.value)
    next_value = policy.progression_values[index + 1]
    profile = next_provider_dimension_profile(predecessor, dimension_id)
    successor = compile_successor_profile_release(
        predecessor, profile, source_registry, answer_registry,
        source_root=source_root, graph=graph, verification_seed=verification_seed)
    proof = verify_profile_expansion(predecessor, successor)
    if successor.provider_dimension_policies != predecessor.provider_dimension_policies:
        raise ValueError(ProviderDimensionError.POLICY_DRIFT.value)
    if proof.added_capabilities:
        raise ValueError(ProviderDimensionError.MEMBERSHIP_OWNER_REQUIRED.value)
    current = provider_dimension_state(successor, dimension_id)
    if current.value != next_value:
        raise ValueError(ProviderDimensionError.SUCCESSOR_DRIFT.value)
    expected_changes = set()
    if policy.changes_source_projection:
        expected_changes.add("source")
    if policy.changes_assessment_scope:
        expected_changes.add("assessment")
    if policy.changes_answer_domain:
        expected_changes.add("answer_schema")
    if set(successor.transition.projection_changes) != expected_changes:
        raise ValueError(ProviderDimensionError.PROJECTION_DRIFT.value)
    return ProviderDimensionTransition(previous, current, profile, successor)


def next_automatic_provider_dimension(release, trigger="DEVELOPMENTAL_BOUNDARY"):
    """Select one auto-progressing nonterminal dimension or fail on ambiguity."""
    candidates = tuple(
        state for state in provider_dimension_states(release)
        if not state.terminal and
        _policy(release, state.dimension_id).advance_trigger == trigger)
    if len(candidates) > 1:
        raise ValueError(ProviderDimensionError.AUTO_POLICY_AMBIGUOUS.value)
    return candidates[0] if candidates else None


__all__ = (
    "ProviderDimensionState", "ProviderDimensionTransition",
    "compile_provider_dimension_successor", "next_automatic_provider_dimension",
    "next_provider_dimension_profile",
    "provider_dimension_state", "provider_dimension_states",
    "provider_dimension_telemetry",
)
