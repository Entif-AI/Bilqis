"""Live-profile subprocess fixture: source setup."""
PROBE = r'''
from dataclasses import replace
import hashlib
import json
from pathlib import Path

from bilqis_mlx.boolean_composite import (
    build_course as build_composite, draw_composite)
from bilqis_mlx.boolean_identification import (
    answer_heads as boolean_answer_heads,
    build_course as build_identification,
    draw_identification)
from bilqis_mlx.compatibility.executable_projection import (
    legacy_course_for_profile, project_legacy_course,
)
from bilqis_mlx.factory.answers import (
    AnswerModality, AnswerModalityRegistry, RegisteredAnswerModality,
    fixed_domain, merge_prefix_domain,
)
from bilqis_mlx.factory.curriculum_definition import from_legacy_course
from bilqis_mlx.factory.execution import (
    CapabilityProfile, CurriculumProfile, GradeProfile,
    compile_execution_plan,
)
from bilqis_mlx.factory.executable_release import (
    ExecutableFactoryRelease,
    answer_heads_from_executable_release,
    compile_executable_factory_release,
    compile_successor_profile_release,
)
from bilqis_mlx.factory.generation import (
    draw_executable_release_rows, draw_execution_rows,
)
from bilqis_mlx.factory.provider_dimensions import (
    compile_provider_dimension_successor, provider_dimension_state,
)
from bilqis_mlx.factory.live_releases import (
    boolean_successor, initial_course, minimal_boolean_successor,
)
from bilqis_mlx.grade_a_probe import read_sources
from bilqis_mlx.grade_a_release import accepted_grade_a
from bilqis_mlx.live_grade_c import registry_graph
from bilqis_mlx.semantics.abi import HISTORICAL_PREFIX_SIZE
from bilqis_mlx.source_adapters.school import live_source_registry
from bilqis_mlx.profiles.catalog import numeric_entry_transition
from bilqis_mlx.typed_answer_training import prepare_typed_batches

root = Path.cwd()
source = root.parent / "bilqis-mlx-retention-lab" / "vendor" / "legacy-v16"
manifest = json.loads((
    root / "docs/provenance/GRADE_A_CANDIDATE_MANIFEST_V2.json").read_text())
grade_a = initial_course(accepted_grade_a(manifest))
course = grade_a
course = boolean_successor(course, source)
course = build_composite(course, source)
course = build_identification(course, source)
grade_b = replace(
    course.grades[-1],
    teaching_stages=(
        tuple(cap.id for cap in course.grades[-1].capabilities[:6]),
        ("B.COMPOSITE",),
        ("B.IDBOOLOPS",),
    ))
course = replace(course, grades=(course.grades[0], grade_b))
curriculum, bindings = from_legacy_course(course)
# Provider source still comes from the pinned legacy source root,
# while executable semantic identity follows the actual 222-row
# historical student ABI used by the human trainer.
read_sources(source)
registered = registry_graph()
graph = {
    **registered,
    "tokens": registered["tokens"][:HISTORICAL_PREFIX_SIZE],
    "nodes": registered["nodes"][:HISTORICAL_PREFIX_SIZE],
    "row_contract_sha256": {
        key: registered["row_contract_sha256"][key]
        for key in registered["tokens"][:HISTORICAL_PREFIX_SIZE]
    },
}
digest = lambda value: hashlib.sha256(json.dumps(
    value, sort_keys=True, separators=(",", ":")).encode()).hexdigest()
assert digest(draw_composite(source, graph, seed=2026101902)) == (
    "cb1d95cc8ae92afeedd33e7f1603aa41d75368f70b83ad29a797eef0a6d87a95")
assert digest(draw_identification(source, graph, seed=2026101902)) == (
    "21c5e1b95a9eaf2bdd1be49f72f4c9bc8a2d35d249349b80439c27ce4318af1e")
legacy_boolean_heads = boolean_answer_heads(graph)
assert legacy_boolean_heads["boolean_operator"]["values"] == [
    "NOT", "AND", "OR", "XOR", "IMPLIES", "IFF"]
assert [
    graph["tokens"][index]
    for index in legacy_boolean_heads["boolean_operator"]["token_ids"]
] == [
    "cogal.operator.NOT",
    "cogal.operator.AND",
    "cogal.operator.OR",
    "cogal.operator.XOR",
    "cogal.operator.IMPLIES",
    "cogal.operator.IFF",
]
registry = live_source_registry()
answers = AnswerModalityRegistry((
    RegisteredAnswerModality(
        AnswerModality("binary", "answer.binary/v1", "a" * 64),
        fixed_domain(("FALSE", "TRUE")),
        lambda value: {
            "FALSE": "cogal.value.false",
            "TRUE": "cogal.value.true",
        }[value]),
    RegisteredAnswerModality(
        AnswerModality(
            "boolean_operator", "answer.boolean-operator/v1", "b" * 64),
        fixed_domain(("NOT", "AND", "OR", "XOR", "IMPLIES", "IFF")),
        lambda value: "cogal.operator." + value),
    RegisteredAnswerModality(
        AnswerModality(
            "numeric_active", "answer.numeric-active/v1", "c" * 64),
        merge_prefix_domain,
        lambda value: "school.number." + value),
))
'''
