"""Compile provider, answer-head, and verification evidence."""
from __future__ import annotations

from ..adapters import SourceAdapterRegistry
from ..answers import AnswerModality, AnswerModalityRegistry
from ..curriculum_definition import CurriculumDefinition, SourceBindingSet
from ..execution import ExecutionPlan
from ..model import SourceAdapter
from .primitives import AnswerHeadBinding, ExecutableVerificationReceipt

from .. import executable_release as _api


def _provider_descriptors(
        plan: ExecutionPlan, bindings: SourceBindingSet,
        registry: SourceAdapterRegistry) -> tuple[SourceAdapter, ...]:
    result = []
    seen = set()
    by_capability = bindings.by_capability
    for execution in plan.capabilities:
        binding = by_capability[execution.capability_id]
        descriptor = registry.require(
            binding.generator_id, binding.oracle_id).descriptor
        if descriptor.adapter_id not in seen:
            seen.add(descriptor.adapter_id)
            result.append(descriptor)
    return tuple(result)


def _answer_head_bindings(
        plan: ExecutionPlan, graph: dict,
        registry: AnswerModalityRegistry) -> tuple[AnswerHeadBinding, ...]:
    compiled = _api.compile_answer_heads(plan, graph, registry)
    result = []
    for descriptor in registry.descriptors_for(plan):
        head = compiled[descriptor.kind]
        modality = registry.require(descriptor.kind)
        values = tuple(head["values"])
        result.append(_api.AnswerHeadBinding(
            kind=descriptor.kind,
            values=values,
            semantic_identities=tuple(
                modality.resolve_identity(value) for value in values),
            token_ids=tuple(head["token_ids"]),
            modality_id=descriptor.adapter_id,
            implementation_sha256=descriptor.implementation_sha256,
        ))
    return tuple(result)


def _verification_receipt(
        curriculum: CurriculumDefinition, bindings: SourceBindingSet,
        plan: ExecutionPlan, source_registry: SourceAdapterRegistry,
        answer_modalities: tuple[AnswerModality, ...],
        answer_heads: tuple[AnswerHeadBinding, ...], *, source_root, graph: dict,
        verification_seed: int) -> ExecutableVerificationReceipt:
    projection_map = {
        item.capability_id: item for item in plan.capability_projection_digests}
    receipts = []
    for execution in plan.capabilities:
        rows = _api.draw_execution_rows(
            source_root, graph, curriculum, plan, source_registry,
            source_bindings=bindings,
            seed=verification_seed, capability=execution.capability_id,
            each=execution.exam_item_count)
        row_ids = tuple(row["id"] for row in rows)
        if len(set(row_ids)) != len(row_ids):
            raise ValueError(
                "FACTORY_EXECUTABLE_RELEASE_DUPLICATE_SPECIMEN:"
                + execution.capability_id)
        projection = projection_map[execution.capability_id]
        receipts.append(_api.CapabilityVerificationReceipt(
            capability_id=execution.capability_id,
            verification_seed=verification_seed,
            specimen_count=len(rows),
            specimen_ids_sha256=_api._digest(row_ids),
            specimen_content_sha256=_api._digest(rows),
            source_projection_sha256=projection.source,
            coverage_projection_sha256=projection.coverage,
            answer_schema_projection_sha256=projection.answer_schema,
        ))
    receipt_map = {item.capability_id: item for item in receipts}
    assessments = []
    for grade in plan.grades:
        receipt_hashes = tuple(
            receipt_map[capability].digest()
            for capability in grade.cumulative_scope)
        seal = _api.VerifiedAssessmentSeal(
            grade_id=grade.grade_id,
            cumulative_scope=grade.cumulative_scope,
            assessment_blueprint_sha256=grade.assessment_blueprint_sha256,
            capability_receipt_sha256s=receipt_hashes,
            seal_sha256="0" * 64,
        )
        assessments.append(_api.replace(seal, seal_sha256=seal.expected_digest()))
    descriptors = _api._provider_descriptors(plan, bindings, source_registry)
    names = graph.get("tokens") if isinstance(graph, dict) else None
    _api._require(
        isinstance(names, list) and bool(names) and
        all(isinstance(name, str) and name for name in names),
        _api._ReleaseError.SEMANTIC_CATALOG_REQUIRED,
    )
    return _api.ExecutableVerificationReceipt(
        verification_seed=verification_seed,
        execution_plan_sha256=plan.digest(),
        source_binding_sha256=bindings.digest(),
        provider_descriptors_sha256=_api._digest(
            [_api._source_adapter_record(item) for item in descriptors]),
        answer_modalities_sha256=_api._digest(
            [_api.asdict(item) for item in answer_modalities]),
        semantic_catalog_sha256=_api._digest(tuple(names)),
        answer_heads_sha256=_api._digest(
            [_api.asdict(item) for item in answer_heads]),
        capabilities=tuple(receipts),
        assessments=tuple(assessments),
    )
