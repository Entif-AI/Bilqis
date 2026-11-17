"""School policy for append-only semantic-catalog admission."""
from __future__ import annotations

from dataclasses import dataclass
from functools import cache

from ..factory.executable_release import ExecutableFactoryRelease
from ..factory.model import ProviderDimensionError
from ..factory.execution import (
    CapabilityProfile,
    CurriculumProfile,
    GradeProfile,
)
from ..live_grade_c import expanded_graph
from ..semantics.core import Literal
from ..semantics.numeric import evaluate
from ..source_adapters.numeric import decode
from .school import (
    boolean_entry_profile,
    numeric_foundation_profile,
    with_disabled_future_grades,
)


NUMERIC_GRADE_PREFIX_SIZE = 3


@dataclass(frozen=True)
class CatalogProfileTransition:
    profile: CurriculumProfile
    graph: dict
    numeric_scope_final_maximum: int | None = None


def numeric_scope_bounds() -> tuple[int, int]:
    from ..source_adapters.school import live_source_registry
    policies = live_source_registry().dimension_policies("source.finite-numeric/v2")
    if len(policies) != 1 or policies[0].dimension_id != "numeric-root":
        raise ValueError(ProviderDimensionError.POLICY_REQUIRED.value)
    values = policies[0].progression_values
    try:
        return int(values[0]), int(values[-1])
    except (TypeError, ValueError) as exc:
        raise ValueError(ProviderDimensionError.POLICY_INVALID.value) from exc


def displayed_numeric_maximum(state: dict | None):
    """Project the canonical pending entry rung for a one-shot wide C receipt."""
    if not isinstance(state, dict):
        return None
    maximum = state.get("numeric_maximum")
    initial, final = numeric_scope_bounds()
    active = tuple((state.get("school") or {}).get("active_grades", ()))
    if (state.get("numeric_scope_final_maximum") is None and
            maximum == final and len(active) >= NUMERIC_GRADE_PREFIX_SIZE):
        return initial
    return maximum


def next_school_transition(release, graph, *, full_boolean, numeric_staircase,
                           final_scope=None):
    """Author the existing school's next profile; runtime consumes the value."""
    active = tuple(grade.grade_id for grade in release.execution_plan.grades)
    next_index = len(active)
    next_grade = (release.curriculum.grades[next_index].grade_id
                  if next_index < len(release.curriculum.grades) else None)
    if active == ("A",) and next_grade == "B":
        profile = with_disabled_future_grades(
            boolean_entry_profile(full=full_boolean),
            tuple(grade.grade_id for grade in release.curriculum.grades[2:]))
        return CatalogProfileTransition(profile, graph)
    if active == ("A", "B") and next_grade == "C":
        initial_scope, terminal_scope = numeric_scope_bounds()
        transition = numeric_entry_transition(
            release, graph, full_boolean=full_boolean,
            maximum=initial_scope)
        from dataclasses import replace
        transition = replace(
            transition,
            numeric_scope_final_maximum=(
                terminal_scope if final_scope is None else final_scope))
        return transition
    return None


def numeric_entry_transition(
        release: ExecutableFactoryRelease, graph: dict, *,
        full_boolean: bool, maximum: int | None = None) -> CatalogProfileTransition:
    """Build the next canonical grade-prefix profile plus its admitted ABI."""
    if not isinstance(release, ExecutableFactoryRelease):
        raise TypeError("FACTORY_CATALOG_RELEASE_REQUIRED")
    release.verify()
    if maximum is None:
        maximum = numeric_scope_bounds()[0]
    next_index = len(release.execution_plan.grades)
    if not 0 <= next_index < len(release.curriculum.grades):
        raise ValueError("FACTORY_CATALOG_NO_DISABLED_GRADE")
    next_grade = release.curriculum.grades[next_index]
    boolean = boolean_entry_profile(full=True) if full_boolean else release.profile
    profile = numeric_foundation_profile(
        boolean,
        maximum=maximum,
        grade_id=next_grade.grade_id,
        capability_ids=tuple(
            capability.capability_id for capability in next_grade.capabilities),
    )
    future = tuple(
        grade.grade_id
        for grade in release.curriculum.grades[next_index + 1:])
    profile = with_disabled_future_grades(profile, future)
    _, final_maximum = numeric_scope_bounds()
    return CatalogProfileTransition(
        profile=profile,
        graph=expanded_graph(graph),
        numeric_scope_final_maximum=(
            final_maximum if maximum < final_maximum else None),
    )


def _validate_numeric_scope_target(
        release: ExecutableFactoryRelease, maximum: int, *,
        require_active_grade: bool) -> None:
    """Keep the historical numeric-scope boundary contract in one owner."""
    is_release = isinstance(release, ExecutableFactoryRelease)
    if is_release:
        release.verify()
    active_grade_missing = (
        is_release and require_active_grade and not release.execution_plan.grades)
    _, terminal = numeric_scope_bounds()
    if (not is_release or type(maximum) is not int or
            not 1 <= maximum <= terminal or active_grade_missing):
        raise ValueError("FACTORY_NUMERIC_SCOPE_ADVANCE_INVALID")


def numeric_scope_profile(
        release: ExecutableFactoryRelease, maximum: int) -> CurriculumProfile:
    """Project one exact bounded numeric domain over the active numeric grade."""
    _validate_numeric_scope_target(
        release, maximum, require_active_grade=True)
    active_grade = release.execution_plan.grades[-1]
    canonical_grade = next(
        grade for grade in release.curriculum.grades
        if grade.grade_id == active_grade.grade_id)
    all_ids = tuple(
        capability.capability_id for capability in canonical_grade.capabilities)
    from ..numeric_staircase import FULL_OPERATION_MAXIMUM, FOUNDATIONS
    enabled = (all_ids if maximum >= FULL_OPERATION_MAXIMUM else
               all_ids[:len(FOUNDATIONS)])
    numbers = tuple(str(index) for index in range(maximum + 1))
    numeric_grade = GradeProfile(
        active_grade.grade_id,
        enabled_capabilities=enabled,
        capabilities=tuple(CapabilityProfile(
            capability_id,
            provider_parameters=(("numbers", numbers),),
            answer_family_values=(("numeric_active", numbers),),
        ) for capability_id in enabled),
    )
    prior = tuple(
        grade for grade in release.profile.grades
        if grade.grade_id != active_grade.grade_id)
    future = tuple(
        GradeProfile(grade.grade_id, enabled_capabilities=())
        for grade in release.curriculum.grades[len(release.execution_plan.grades):]
        if grade.grade_id != active_grade.grade_id)
    return CurriculumProfile(
        f"{release.profile.profile_id.rsplit('/numeric-0-', 1)[0]}"
        f"/numeric-0-{maximum}",
        grades=(*prior, numeric_grade, *future),
    )


def next_numeric_scope_profile(
        release: ExecutableFactoryRelease, *, final_maximum: int | None = None
        ) -> CurriculumProfile | None:
    """Return the next bounded numeric-domain profile, preserving other grades."""
    if final_maximum is None:
        final_maximum = numeric_scope_bounds()[1]
    _validate_numeric_scope_target(
        release, final_maximum, require_active_grade=False)
    from ..factory.provider_dimensions import (
        next_provider_dimension_profile, provider_dimension_state)
    try:
        state = provider_dimension_state(release, "numeric-root")
    except ValueError:
        return None
    if int(state.value) >= final_maximum:
        return None
    profile = next_provider_dimension_profile(release, "numeric-root")
    if profile is None:
        return None
    next_value = int(profile.profile_id.rsplit("/", 1)[-1])
    if next_value > final_maximum:
        return None
    return CurriculumProfile(
        f"{release.profile.profile_id.rsplit('/numeric-0-', 1)[0]}"
        f"/numeric-0-{next_value}", profile.grades)


@cache
def _numeric_scope_requirement(symbols: tuple[str, ...]) -> int | None:
    """Return the highest numeric value encoded by one immutable source record."""
    numeric_symbols = tuple(
        symbol for symbol in symbols
        if isinstance(symbol, str) and symbol.startswith("school.number."))
    if not numeric_symbols:
        return None
    explicit_maximum = max(
        int(symbol.removeprefix("school.number.")) for symbol in numeric_symbols)

    def required(node) -> int:
        values = []
        if node.type_name == "Number":
            values.append(evaluate(node))
        if not isinstance(node, Literal):
            values.extend(required(child) for child in node.arguments)
        return max(values, default=-1)

    # The numeric prefix codec accepts a list of catalog symbols, not the
    # immutable tuple used as the content-addressed memoization key.
    return max(explicit_maximum, required(decode(list(symbols))))


def numeric_row_in_scope(row: dict, maximum: int) -> bool:
    """Keep wider numeric mistakes deferred without grade-ID dispatch."""
    if type(maximum) is not int or maximum < 0:
        raise ValueError("FACTORY_NUMERIC_SCOPE_MAXIMUM_INVALID")
    symbols = tuple((row.get("record") or {}).get("symbols", ()))
    requirement = _numeric_scope_requirement(symbols)
    return requirement is None or requirement <= maximum


def partition_numeric_scope(rows, maximum: int) -> tuple[list[dict], list[dict]]:
    """Partition immutable numeric evidence with one semantic scope check per row."""
    active = []
    deferred = []
    for row in rows:
        (active if numeric_row_in_scope(row, maximum) else deferred).append(row)
    return active, deferred
