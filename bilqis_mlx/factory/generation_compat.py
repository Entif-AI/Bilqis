"""Compatibility-owned release generation seams kept out of the main generator."""

from .adapters import SourceAdapterRegistry
from .model import FactoryRelease
from ..compatibility.source_adapter_resume import resume_adapter_compatible


def runtime_adapter_for_release(
        source_root, graph, release, registry, execution, *,
        drift_code="FACTORY_EXECUTABLE_GENERATION_ADAPTER_DRIFT"):
    binding = release.source_bindings.by_capability[execution.capability_id]
    registered = registry.require(binding.generator_id, binding.oracle_id)
    admitted = next((item for item in release.source_adapters
                     if item.adapter_id == execution.provider_id), None)
    if (registered.descriptor != admitted and
            not resume_adapter_compatible(admitted, registered.descriptor)):
        raise ValueError(drift_code + ":" + execution.capability_id)
    return registered


def draw_release_rows(source_root, graph, release: FactoryRelease,
                      registry: SourceAdapterRegistry, *, seed: int,
                      capability: str | None = None, each: int | None = None) -> list[dict]:
    release.verify()
    if not isinstance(registry, SourceAdapterRegistry):
        raise TypeError("FACTORY_GENERATION_REGISTRY_REQUIRED")
    course = release.course
    selected = tuple(
        (grade, cap, count)
        for grade in course.grades
        for cap, (name, count) in zip(grade.capabilities, grade.exam_item_counts)
        if name == cap.id and (capability is None or cap.id == capability)
    )
    if capability is not None and capability not in course.capability_map:
        raise ValueError("FACTORY_GENERATION_UNKNOWN_CAPABILITY")
    if not selected:
        raise ValueError("FACTORY_GENERATION_EMPTY_SCOPE")
    rows = []
    for _, cap, default_count in selected:
        count = default_count if each is None else each
        if type(count) is not int or count < 1:
            raise ValueError("FACTORY_GENERATION_INVALID_COUNT")
        adapter = registry.require(cap.lesson_generator, cap.independent_oracle)
        if adapter.descriptor != release.source_adapter_map.get(adapter.descriptor.adapter_id):
            raise ValueError("FACTORY_GENERATION_ADAPTER_DRIFT:" + cap.id)
        batch = adapter.draw(source_root=source_root, graph=graph, course=course,
                             capability=cap.id, seed=seed, each=count)
        if len(batch) != count or any(row.get("capability") != cap.id for row in batch):
            raise ValueError("FACTORY_GENERATION_ADAPTER_SCOPE_DRIFT:" + cap.id)
        answers = {family.kind: family.values for family in cap.answer_families}
        for row in batch:
            if (not isinstance(row.get("id"), str) or not row["id"] or
                    row.get("gold") not in answers.get(row.get("answer_kind", "binary"), ())):
                raise ValueError("FACTORY_GENERATION_ANSWER_CONTRACT_DRIFT:" + cap.id)
            if adapter.check(row, source_root=source_root, graph=graph, course=course) is not True:
                raise ValueError("FACTORY_GENERATION_SOURCE_ORACLE_DISAGREEMENT:" + cap.id)
        rows.extend(batch)
    expected = {cap.id: (each if each is not None else count)
                for _, cap, count in selected}
    actual = {cap: sum(row.get("capability") == cap for row in rows) for cap in expected}
    if actual != expected:
        raise ValueError("FACTORY_GENERATION_INCOMPLETE_RELEASE_SCOPE")
    return rows
