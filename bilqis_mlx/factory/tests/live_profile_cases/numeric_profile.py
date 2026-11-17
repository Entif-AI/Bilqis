"""Live-profile subprocess fixture: numeric profile."""
PROBE = r'''numeric_transition = numeric_entry_transition(
    projected_release, graph,
    full_boolean=False)
numeric_course = legacy_course_for_profile(
    grade_a, source, numeric_transition.profile)
numeric_release = compile_successor_profile_release(
    projected_release,
    numeric_transition.profile,
    registry,
    answers,
    source_root=source,
    graph=numeric_transition.graph,
    verification_seed=2026101905)
assert numeric_release.transition.semantic_geometry == (
    "APPEND_ONLY_EXPANSION")
assert tuple(
    grade.grade_id
    for grade in numeric_release.execution_plan.grades
) == ("A", "B", "C")
assert numeric_release.execution_plan.grade_map["C"].capabilities == (
    "C.COUNT", "C.NUMBER", "C.SUCCESSOR", "C.ADD", "C.SUB",
    "C.MUL", "C.DIV")
numeric_heads = answer_heads_from_executable_release(
    numeric_release, numeric_transition.graph)
assert numeric_heads["numeric_active"]["values"] == [
    "0", "1", "2", "3", "4"]
numeric_rows = []
for capability in numeric_release.execution_plan.grade_map["C"].capabilities:
    numeric_rows.extend(draw_executable_release_rows(
        source, numeric_transition.graph, numeric_release, registry,
        seed=20261019,
        capability=capability))
assert numeric_rows
assert all(
    row["gold"] in {"0", "1", "2", "3"}
    or row["gold"] == "4"
    for row in numeric_rows
    if row.get("answer_kind") == "numeric_active")
assert "source.micro.boolean-minimal/v1" not in {
    cap.provider_id
    for cap in numeric_release.execution_plan.capabilities}

numeric_state = provider_dimension_state(numeric_release, "numeric-root")
assert (numeric_state.value, numeric_state.terminal) == ("4", False)
numeric_step = compile_provider_dimension_successor(
    numeric_release,
    "numeric-root",
    registry,
    answers,
    source_root=source,
    graph=numeric_transition.graph,
    verification_seed=2026101906)
assert numeric_step is not None
assert (numeric_step.previous.value, numeric_step.current.value) == ("4", "5")
numeric_five = numeric_step.release
assert numeric_five.transition.semantic_geometry == "UNCHANGED"
assert answer_heads_from_executable_release(
    numeric_five, numeric_transition.graph
)["numeric_active"]["values"] == ["0", "1", "2", "3", "4", "5"]
from bilqis_mlx.factory.schedule import (
    schedule_program_from_executable_release,
)
assert (
    schedule_program_from_executable_release(numeric_five).digest()
    != schedule_program_from_executable_release(numeric_release).digest()
)
print("LIVE_PROFILE_EXECUTION_OK")
'''
