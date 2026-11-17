"""Synthetic Grade Z Factory fixture with no production grade-specific code."""
from dataclasses import replace

from bilqis_mlx.curriculum import AnswerFamily, BINARY
from bilqis_mlx.factory.adapters import RegisteredSourceAdapter, SourceAdapterRegistry
from bilqis_mlx.factory.answers import (
    AnswerModality, AnswerModalityRegistry, RegisteredAnswerModality, fixed_domain,
)
from bilqis_mlx.factory.curriculum_definition import (
    CapabilitySourceBinding, CapabilitySpec, CurriculumDefinition, GradeSpec,
    SourceBindingSet,
)
from bilqis_mlx.factory.executable_release import compile_executable_factory_release
from bilqis_mlx.factory.execution import CurriculumProfile
from bilqis_mlx.factory.model import SourceAdapter


CAPABILITIES = tuple(f"Z.C{index}" for index in range(12))


def rows(*, capability, seed, each, **_):
    return tuple({
        "id": f"{capability}:{seed}:{index}",
        "capability": capability,
        "answer_kind": "binary",
        "gold": "TRUE" if index % 2 else "FALSE",
    } for index in range(each))


def check(row, **_):
    try:
        index = int(row["id"].rsplit(":", 1)[1])
    except (KeyError, ValueError):
        return False
    return row.get("gold") == ("TRUE" if index % 2 else "FALSE")


def fixture():
    capabilities = tuple(CapabilitySpec(
        capability_id=identity,
        difficulty="disposable-z",
        taught_roots=("z.semantic." + identity.rsplit(".", 1)[1],),
        examined_roots=("z.semantic." + identity.rsplit(".", 1)[1],),
        prerequisites=(), composed_of=(),
        answer_families=(AnswerFamily("binary", BINARY),),
    ) for identity in CAPABILITIES)
    grade = GradeSpec(
        "Z", capabilities,
        exam_item_counts=tuple((identity, 4) for identity in CAPABILITIES),
    )
    curriculum = CurriculumDefinition(
        "fixture.grade-z/v2", (grade,), program_complete=True)
    bindings = SourceBindingSet(tuple(CapabilitySourceBinding(
        identity, "repo:fixture/grade-z", "fixture.z-generator/v1",
        "fixture.z-oracle/v1") for identity in CAPABILITIES),
        source_attestation_sha256="b" * 64)
    adapter = SourceAdapter(
        "fixture.z-adapter/v1", "fixture.z-generator/v1",
        ("fixture.z-oracle/v1",), "d" * 64,
        variation_axes=("fresh-seed", "balanced-gold"),
    )
    source_registry = SourceAdapterRegistry((
        RegisteredSourceAdapter(
            adapter, rows, check,
            semantic_footprint=lambda row: (
                "z.semantic." + row["capability"].rsplit(".", 1)[1],)),
    ))
    answer_registry = AnswerModalityRegistry((
        RegisteredAnswerModality(
            AnswerModality("binary", "answer.binary/z-fixture", "e" * 64),
            fixed_domain(BINARY),
            lambda value: {
                "FALSE": "cogal.value.false",
                "TRUE": "cogal.value.true",
            }[value],
        ),
    ))
    graph = {
        "tokens": [
            "fixture.padding",
            "cogal.value.false",
            "cogal.value.true",
        ],
    }
    release = compile_executable_factory_release(
        curriculum, bindings, CurriculumProfile.full(),
        source_registry, answer_registry,
        source_root=None, graph=graph,
        verification_seed=20261019,
    )
    return source_registry, graph, release


__all__ = ("CAPABILITIES", "fixture")
