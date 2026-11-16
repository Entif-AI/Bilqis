"""Grade-neutral specimen generation from a verified FactoryRelease."""
from __future__ import annotations

from bilqis_mlx.b11_observation import note_provider_check

from .adapters import SourceAdapterRegistry, validate_instructional_constituents
from .model import FactoryRelease
from .execution import ExecutionPlan
from .curriculum_definition import (
    CurriculumDefinition, SourceBindingSet, from_legacy_course,
    validate_source_bindings,
)
from .generation_compat import draw_release_rows, runtime_adapter_for_release


def execute_release_family_program(
        release: FactoryRelease, registry: SourceAdapterRegistry,
        family_registry, atlas, learned_frontier, capability_id: str, *,
        construct_args: tuple = (), construct_kwargs: dict | None = None,
        check_args: tuple = (), check_kwargs: dict | None = None):
    """Explicit non-admitting A08 family execution against one verified release.

    This does not enter the admitted student draw path. It replays the current A08
    source/census authority, resolves the exact release capability/provider tuple,
    then delegates heterogeneous construction/checking to the registered family.
    """
    from .skos_curriculum.registry import (
        FamilyProgramRegistry, bind_factory_release_families,
        default_family_program_registry,
        execute_bound_family_program,
    )
    from .skos_curriculum.common import _fail
    from .skos_curriculum.curriculum import LearnedFrontier
    from .curriculum.capability_identity import (
        bind_factory_release_capability_identity,
    )
    from ..semantics.cognitive_operators.registry import default_registry

    if (type(release) is not FactoryRelease
            or not isinstance(registry, SourceAdapterRegistry)
            or type(family_registry) is not FamilyProgramRegistry
            or type(learned_frontier) is not LearnedFrontier
            or not isinstance(capability_id, str) or not capability_id):
        _fail("FACTORY_FAMILY_EXECUTION_INPUT_INVALID")
    release.verify()
    canonical_registry = default_family_program_registry()
    if family_registry.programs != canonical_registry.programs:
        _fail("FACTORY_FAMILY_EXECUTION_CANONICAL_REGISTRY_REQUIRED")
    bindings = bind_factory_release_families(
        release, canonical_registry, registry, atlas, learned_frontier)
    binding = bindings.require(capability_id)
    stable_binding = bind_factory_release_capability_identity(
        release, bindings, capability_id, atlas,
        default_registry(bindings.semantic_release))
    stable = stable_binding.stable_identity.identity
    capability = next((
        item for item in release.capabilities
        if item.capability_id == capability_id), None)
    program = next((
        item for item in release.construction_programs
        if item.capability_id == capability_id), None)
    if (capability is None or program is None
            or binding.program_key is None
            or binding.stable_semantic_id != stable.semantic_id
            or binding.program_key.family_id != stable.family_id
            or binding.program_key.signature != stable.signature
            or binding.program_key.answer_kinds != stable.answer_kinds
            or stable.answer_kinds != tuple(sorted(capability.answer_kinds))
            or (binding.semantic_operator_id is not None
                and stable.operator_id != binding.semantic_operator_id)
            or binding.source_adapter_id != capability.source_adapter_id
            or binding.generator_id != program.generator_id
            or binding.oracle_id != program.oracle_id
            or binding.capability_id != program.capability_id):
        _fail("FACTORY_FAMILY_EXECUTION_RELEASE_BINDING_DRIFT")
    registered = registry.require(program.generator_id, program.oracle_id)
    if registered.descriptor.adapter_id != binding.source_adapter_id:
        _fail("FACTORY_FAMILY_EXECUTION_SOURCE_ADAPTER_DRIFT")
    return execute_bound_family_program(
        canonical_registry, binding,
        construct_args=construct_args, construct_kwargs=construct_kwargs,
        check_args=check_args, check_kwargs=check_kwargs,
        source_registry=registry, atlas=atlas)


def draw_execution_rows(
        source_root, graph, curriculum, plan: ExecutionPlan,
        registry: SourceAdapterRegistry, *, seed: int,
        source_bindings: SourceBindingSet | None = None,
        capability: str | None = None,
        each: int | None = None) -> list[dict]:
    """Generate from one compiled execution contract, including profile constraints."""
    adapter_context = curriculum
    if isinstance(curriculum, CurriculumDefinition):
        if source_bindings is None:
            raise ValueError("FACTORY_EXECUTION_GENERATION_SOURCE_BINDINGS_REQUIRED")
        validate_source_bindings(curriculum, source_bindings)
    else:
        if source_bindings is not None:
            raise ValueError("FACTORY_EXECUTION_GENERATION_LEGACY_BINDINGS_AMBIGUOUS")
        curriculum, source_bindings = from_legacy_course(curriculum)
    if (not isinstance(plan, ExecutionPlan) or
            plan.curriculum_sha256 != curriculum.digest() or
            plan.source_binding_sha256 != source_bindings.digest()):
        raise ValueError("FACTORY_EXECUTION_GENERATION_PLAN_BINDING_DRIFT")
    if not isinstance(registry, SourceAdapterRegistry):
        raise TypeError("FACTORY_EXECUTION_GENERATION_REGISTRY_REQUIRED")
    selected = tuple(
        item for item in plan.capabilities
        if capability is None or item.capability_id == capability)
    if capability is not None and capability not in plan.capability_map:
        raise ValueError("FACTORY_EXECUTION_GENERATION_UNKNOWN_CAPABILITY")
    if not selected:
        raise ValueError("FACTORY_EXECUTION_GENERATION_EMPTY_SCOPE")

    rows = []
    bindings = source_bindings.by_capability
    for execution in selected:
        count = execution.exam_item_count if each is None else each
        if type(count) is not int or count < 1:
            raise ValueError("FACTORY_EXECUTION_GENERATION_INVALID_COUNT")
        binding = bindings[execution.capability_id]
        adapter = registry.require(
            binding.generator_id, binding.oracle_id)
        if adapter.descriptor.adapter_id != execution.provider_id:
            raise ValueError(
                "FACTORY_EXECUTION_GENERATION_ADAPTER_DRIFT:"
                + execution.capability_id)
        adapter.descriptor.validate_profile_parameters(
            execution.provider_parameters)
        arguments = {
            "source_root": source_root,
            "graph": graph,
            "course": adapter_context,
            "capability": execution.capability_id,
            "seed": seed,
            "each": count,
        }
        if execution.provider_parameters:
            arguments["profile_parameters"] = dict(
                execution.provider_parameters)
        batch = adapter.draw(**arguments)
        if (len(batch) != count or
                any(row.get("capability") != execution.capability_id
                    for row in batch)):
            raise ValueError(
                "FACTORY_EXECUTION_GENERATION_SCOPE_DRIFT:"
                + execution.capability_id)
        answers = {
            family.kind: family.values for family in execution.answer_families}
        for row in batch:
            kind = row.get("answer_kind", "binary")
            if (not isinstance(row.get("id"), str) or not row["id"] or
                    row.get("gold") not in answers.get(kind, ())):
                raise ValueError(
                    "FACTORY_EXECUTION_GENERATION_ANSWER_DRIFT:"
                    + execution.capability_id)
            note_provider_check()
            if adapter.check(
                    row, source_root=source_root, graph=graph,
                    course=adapter_context) is not True:
                raise ValueError(
                    "FACTORY_EXECUTION_GENERATION_SOURCE_ORACLE_DISAGREEMENT:"
                    + execution.capability_id)
            validate_instructional_constituents(
                row, curriculum=curriculum, plan=plan,
                capability=execution.capability_id, adapter=adapter)
        rows.extend(batch)
    return rows


def draw_executable_release_rows(
        source_root, graph, release, registry: SourceAdapterRegistry, *,
        seed: int, capability: str | None = None,
        each: int | None = None) -> list[dict]:
    """Generate only from one admitted v2 release and its compiled projections."""
    from .executable_release import ExecutableFactoryRelease

    if not isinstance(release, ExecutableFactoryRelease):
        raise TypeError("FACTORY_EXECUTABLE_GENERATION_RELEASE_REQUIRED")
    if not isinstance(registry, SourceAdapterRegistry):
        raise TypeError("FACTORY_EXECUTABLE_GENERATION_REGISTRY_REQUIRED")
    release.verify()
    release.verify_semantic_catalog(graph)

    if capability is None:
        selected = release.execution_plan.capabilities
    else:
        selected_item = release.execution_plan.capability_map.get(capability)
        if selected_item is None:
            raise ValueError("FACTORY_EXECUTABLE_GENERATION_UNKNOWN_CAPABILITY")
        selected = (selected_item,)
    for execution in selected:
        runtime_adapter_for_release(
            source_root, graph, release, registry, execution)

    return draw_execution_rows(
        source_root, graph, release.curriculum, release.execution_plan, registry,
        source_bindings=release.source_bindings,
        seed=seed, capability=capability, each=each)
