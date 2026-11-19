"""Release structure, provider, evidence, and lineage checks."""
from __future__ import annotations

from .release import ExecutableFactoryRelease

from .. import executable_release as _api


def _verify_release_structure(release: ExecutableFactoryRelease) -> tuple[str, ...]:
    _api._require(
        release.release_sha256 == release.expected_digest(),
        "FACTORY_EXECUTABLE_RELEASE_CONTENT_DRIFT",
    )
    answer_kinds = tuple(item.kind for item in release.answer_modalities)
    _api._require(
        len(set(answer_kinds)) == len(answer_kinds),
        _api._ReleaseError.MODALITY_DRIFT,
    )
    _api.validate_curriculum_definition(release.curriculum, answer_kinds=answer_kinds)
    _api.validate_source_bindings(release.curriculum, release.source_bindings)
    _api._require(
        release.profile.profile_id == release.execution_plan.profile_id,
        "FACTORY_EXECUTABLE_RELEASE_PROFILE_DRIFT",
    )
    _api._require(
        release.curriculum.digest() == release.execution_plan.curriculum_sha256 and
        release.source_bindings.digest() == release.execution_plan.source_binding_sha256,
        "FACTORY_EXECUTABLE_RELEASE_PLAN_BINDING_DRIFT",
    )
    if release._foundation_capability_wire:
        foundation = release.foundation_capability_ids
        inventory = release.execution_plan.active_capability_inventory
        _api._require(
            type(foundation) is tuple and bool(foundation) and
            all(isinstance(item, str) and item for item in foundation) and
            len(set(foundation)) == len(foundation) and
            foundation == inventory,
            _api._ReleaseError.FOUNDATION_CAPABILITY_DRIFT,
        )
    return answer_kinds


def _verify_release_providers(release: ExecutableFactoryRelease) -> None:
    providers = {item.adapter_id: item for item in release.source_adapters}
    _api._require(
        len(providers) == len(release.source_adapters),
        _api._ReleaseError.PROVIDER_DRIFT,
    )
    bindings = release.source_bindings.by_capability
    for execution in release.execution_plan.capabilities:
        provider = providers.get(execution.provider_id)
        binding = bindings.get(execution.capability_id)
        _api._require(
            provider is not None and binding is not None and
            execution.provider_implementation_sha256 == provider.implementation_sha256 and
            binding.source_anchor == execution.source_anchor and
            binding.generator_id == provider.generator_id and
            execution.oracle_id == binding.oracle_id and
            binding.oracle_id in provider.accepted_oracle_ids,
            _api._ReleaseError.PROVIDER_DRIFT,
        )
        provider.validate_profile_parameters(execution.provider_parameters)
    policy_keys = set()
    for policy in release.provider_dimension_policies:
        key = (policy.provider_id, policy.dimension_id)
        provider = providers.get(policy.provider_id)
        _api._require(
            key not in policy_keys and provider is not None,
            _api._ReleaseError.PROVIDER_DRIFT,
        )
        policy_keys.add(key)
        dimensions = dict(provider.profile_dimensions)
        domain = dimensions.get(policy.parameter_name)
        _api._require(
            domain is not None and
            set(policy.progression_values) <= set(domain) and
            policy.progression_values == tuple(
                value for value in domain if value in policy.progression_values),
            _api._ReleaseError.PROVIDER_DRIFT,
        )


def _verify_release_answers(
        release: ExecutableFactoryRelease, answer_kinds: tuple[str, ...]) -> None:
    used_kinds = tuple(dict.fromkeys(
        family.kind for capability in release.execution_plan.capabilities
        for family in capability.answer_families))
    _api._require(
        set(used_kinds) <= set(answer_kinds) and
        used_kinds == tuple(kind for kind in answer_kinds if kind in set(used_kinds)),
        _api._ReleaseError.MODALITY_DRIFT,
    )
    modalities = {item.kind: item for item in release.answer_modalities}
    heads = {item.kind: item for item in release.answer_heads}
    _api._require(tuple(heads) == used_kinds, _api._ReleaseError.ANSWER_HEAD_DRIFT)
    for kind, head in heads.items():
        descriptor = modalities[kind]
        _api._require(
            head.modality_id == descriptor.adapter_id and
            head.implementation_sha256 == descriptor.implementation_sha256,
            _api._ReleaseError.ANSWER_HEAD_DRIFT,
        )


def _verify_release_evidence(release: ExecutableFactoryRelease) -> None:
    verification = release.verification
    _api._require(
        _api._digest(release.semantic_catalog) == release.semantic_catalog_sha256 and
        verification.semantic_catalog_sha256 == release.semantic_catalog_sha256,
        _api._ReleaseError.CATALOG_DRIFT,
    )
    _api._require(
        verification.execution_plan_sha256 == release.execution_plan.digest() and
        verification.source_binding_sha256 == release.source_bindings.digest() and
        verification.provider_descriptors_sha256 ==
            _api._digest([
                _api._source_adapter_record(item)
                for item in release.source_adapters]) and
        verification.answer_modalities_sha256 ==
            _api._digest([_api.asdict(item) for item in release.answer_modalities]) and
        verification.answer_heads_sha256 ==
            _api._digest([_api.asdict(item) for item in release.answer_heads]),
        _api._ReleaseError.VERIFICATION_DRIFT,
    )
    capability_ids = tuple(
        item.capability_id for item in release.execution_plan.capabilities)
    receipts = verification.capabilities
    _api._require(
        tuple(item.capability_id for item in receipts) == capability_ids,
        _api._ReleaseError.VERIFICATION_DRIFT,
    )
    projections = {
        item.capability_id: item
        for item in release.execution_plan.capability_projection_digests}
    executions = release.execution_plan.capability_map
    for receipt in receipts:
        execution = executions[receipt.capability_id]
        projection = projections[receipt.capability_id]
        _api._require(
            receipt.verification_seed == verification.verification_seed and
            receipt.specimen_count == execution.exam_item_count and
            receipt.source_projection_sha256 == projection.source and
            receipt.coverage_projection_sha256 == projection.coverage and
            receipt.answer_schema_projection_sha256 == projection.answer_schema,
            _api._ReleaseError.VERIFICATION_DRIFT,
        )


def _verify_release_assessments(release: ExecutableFactoryRelease) -> None:
    verification = release.verification
    receipt_map = {
        item.capability_id: item for item in verification.capabilities}
    _api._require(
        tuple(item.grade_id for item in verification.assessments) ==
        tuple(item.grade_id for item in release.execution_plan.grades),
        _api._ReleaseError.ASSESSMENT_DRIFT,
    )
    for seal, grade in zip(verification.assessments, release.execution_plan.grades):
        expected_receipts = tuple(
            receipt_map[capability].digest() for capability in grade.cumulative_scope)
        _api._require(
            seal.cumulative_scope == grade.cumulative_scope and
            seal.assessment_blueprint_sha256 == grade.assessment_blueprint_sha256 and
            seal.capability_receipt_sha256s == expected_receipts and
            seal.seal_sha256 == seal.expected_digest(),
            _api._ReleaseError.ASSESSMENT_DRIFT,
        )


def _verify_release_lineage(release: ExecutableFactoryRelease) -> None:
    if release.predecessor_release_sha256 is None:
        _api._require(release.transition is None, _api._ReleaseError.LINEAGE_DRIFT)
        return
    transition = release.transition
    _api._require(
        transition is not None and
        transition.next_plan_sha256 == release.execution_plan.digest() and
        transition.next_curriculum_sha256 == release.execution_plan.curriculum_sha256 and
        transition.next_source_binding_sha256 == release.execution_plan.source_binding_sha256 and
        transition.semantic_geometry != _api.SemanticGeometryChange.INCOMPATIBLE.value,
        _api._ReleaseError.LINEAGE_DRIFT,
    )
