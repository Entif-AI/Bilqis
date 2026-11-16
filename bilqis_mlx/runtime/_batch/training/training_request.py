"""Factory delivery validation and row extraction for C02 training."""
from __future__ import annotations

from typing import Callable

from bilqis_mlx.factory.teaching import DeliveredTeaching, describe_delivered_teaching
from bilqis_mlx.runtime.source_execution import (
    SourceBatchAuthority, SourceExecutionContext, source_content_digest,
)
from bilqis_mlx.semantics.context_eligibility import (
    ContextPolicy, SourceFrontier, TaskScope,
)

from .atlas_training_contracts import _invalid
from .training_input_authority import row_contexts


def require_compile_request(
        delivered_rows, source_context: SourceExecutionContext, *, delivery,
        delivery_capability: str, delivery_release_sha256: str,
        teacher_strategy: dict, requested_count: int, optimizer_step_seed: int,
        source_authority: SourceBatchAuthority, rehearsal_by_id: dict,
        visible_ends: dict, source_ast_for: Callable, answer_plan_for: Callable,
        frames_for_ast: Callable, task_scope, source_frontier,
        eligibility_policy, generation_binding: str, sealed_holdout_ids) -> tuple:
    if not isinstance(source_context, SourceExecutionContext):
        _invalid("SOURCE_CONTEXT_REQUIRED")
    if not isinstance(delivered_rows, (tuple, list)) or not delivered_rows:
        _invalid("DELIVERED_ROWS_REQUIRED")
    if any(not callable(fn) for fn in (
            source_ast_for, frames_for_ast, answer_plan_for)):
        _invalid("UPSTREAM_INTERFACES_REQUIRED")
    count = len(delivered_rows)
    if type(source_authority) is not SourceBatchAuthority:
        _invalid("CONTEXT_AUTHORITY_REQUIRED")
    row_contexts(task_scope, TaskScope, count, "CONTEXT_AUTHORITY_REQUIRED")
    row_contexts(source_frontier, SourceFrontier, count, "CONTEXT_AUTHORITY_REQUIRED")
    row_contexts(eligibility_policy, ContextPolicy, count, "CONTEXT_AUTHORITY_REQUIRED")
    source_context.release.verify()
    source_context.release.verify_semantic_catalog(source_context.graph)
    release = source_context.release
    capabilities = release.execution_plan.capability_map
    source_context.require_bound_rows(delivered_rows, source_authority)
    if (delivery_release_sha256 != release.release_sha256
            or not isinstance(delivery, DeliveredTeaching)
            or delivery_capability not in capabilities):
        _invalid("DELIVERY_RELEASE_INVALID")
    try:
        expected = describe_delivered_teaching(
            release, delivery_capability, delivery.option_id, delivered_rows)
    except (ValueError, KeyError, TypeError):
        _invalid("DELIVERY_INVALID")
    if delivery != expected or len(delivery.specimen_ids) != len(delivered_rows):
        _invalid("DELIVERY_CONTENT_MISMATCH")
    owner = capabilities[delivery_capability]
    if (source_authority.release_sha256 != release.release_sha256
            or source_authority.capability_id != delivery_capability
            or source_authority.provider_id != owner.provider_id
            or source_authority.provider_implementation_sha256
            != owner.provider_implementation_sha256
            or source_authority.content_sha256 != source_content_digest(delivered_rows)
            or source_authority.each != len(delivered_rows)):
        _invalid("TRAINING_SOURCE_AUTHORITY_MISMATCH")
    if (type(requested_count) is not int
            or requested_count < len(delivered_rows)
            or type(optimizer_step_seed) is not int or optimizer_step_seed < 0
            or not isinstance(teacher_strategy, dict)
            or not isinstance(rehearsal_by_id, dict)
            or not isinstance(visible_ends, dict)
            or not isinstance(generation_binding, str) or not generation_binding):
        _invalid("DELIVERY_METADATA_INVALID")
    if (not isinstance(sealed_holdout_ids, (tuple, list, frozenset))
            or any(not isinstance(identity, str)
                   for identity in sealed_holdout_ids)):
        _invalid("HOLDOUT_IDENTITIES_INVALID")
    return release, capabilities, owner


def row_source_inputs(
        row, row_index: int, *, capabilities, owner, delivery,
        delivery_capability: str, source_context: SourceExecutionContext,
        source_authority: SourceBatchAuthority, rehearsal_by_id: dict,
        visible_ends: dict, sealed_holdout_ids) -> tuple:
    if not isinstance(row, dict):
        _invalid("ROW_INVALID")
    identity, capability = row.get("id"), row.get("capability")
    if (not isinstance(identity, str) or not identity
            or not isinstance(capability, str) or capability not in capabilities):
        _invalid("ROW_IDENTITY_OR_CAPABILITY_INVALID")
    if identity in sealed_holdout_ids:
        _invalid("SEALED_HOLDOUT_IN_TRAINING")
    source_id, operation_id = row.get("source_id"), row.get("operation_id")
    family = source_authority.source_family_id
    episode = source_authority.episode_ids[row_index]
    if operation_id is None and isinstance(row.get("record"), dict):
        operation_id = row["record"].get("operator")
    if ((source_id is not None
         and (not isinstance(source_id, str) or not source_id))
            or (operation_id is not None
                and (not isinstance(operation_id, str) or not operation_id))):
        _invalid("SOURCE_OR_OPERATION_INVALID")
    if delivery.option_id == "source.direct/" + delivery_capability:
        if capability != delivery_capability:
            _invalid("DELIVERY_CAPABILITY_MISMATCH")
    elif (capability not in {delivery_capability, *owner.prerequisites}
          or capabilities[capability].provider_id != owner.provider_id
          or capabilities[capability].provider_implementation_sha256
          != owner.provider_implementation_sha256):
        _invalid("DELIVERY_CAPABILITY_MISMATCH")
    rehearsal = rehearsal_by_id.get(identity)
    if rehearsal is not None and not isinstance(rehearsal, str):
        _invalid("REHEARSAL_INVALID")
    tokens = row.get("tokens")
    end = visible_ends.get(
        identity, len(tokens) if isinstance(tokens, (list, tuple)) else None)
    if (not isinstance(tokens, (list, tuple)) or type(end) is not int
            or end < 1 or end > len(tokens)
            or any(type(token) is not int or token < 0
                   or token >= len(source_context.graph["tokens"])
                   for token in tokens[:end])):
        _invalid("SOURCE_PREFIX_INVALID")
    return (identity, capability, source_id, operation_id, family, episode,
            rehearsal, tuple(tokens[:end]))


__all__ = ("require_compile_request", "row_source_inputs")
