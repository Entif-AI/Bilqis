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
        rehearsal_authorities: dict | None,
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
    rehearsal_authorities = rehearsal_authorities or {}
    cross_capability_ids = {
        row.get("id") for row in delivered_rows
        if row.get("id") in rehearsal_by_id
        and row.get("capability") != delivery_capability
    }
    target_rows = tuple(
        row for row in delivered_rows if row.get("id") not in cross_capability_ids)
    source_context.require_bound_rows(target_rows, source_authority)
    if set(rehearsal_authorities) != cross_capability_ids:
        _invalid("REHEARSAL_AUTHORITY_COVERAGE_INVALID")
    for row in delivered_rows:
        identity = row.get("id")
        if identity not in cross_capability_ids:
            continue
        authority = rehearsal_authorities.get(identity)
        if (type(authority) is not SourceBatchAuthority
                or authority.capability_id != row.get("capability")):
            _invalid("REHEARSAL_AUTHORITY_INVALID")
        source_context.require_bound_rows((row,), authority)
    if (delivery_release_sha256 != release.release_sha256
            or not isinstance(delivery, DeliveredTeaching)
            or delivery_capability not in capabilities):
        _invalid("DELIVERY_RELEASE_INVALID")
    specimen_ids = set(delivery.specimen_ids) if isinstance(delivery, DeliveredTeaching) else set()
    option_rows = tuple(row for row in delivered_rows if row.get("id") in specimen_ids)
    try:
        expected = describe_delivered_teaching(
            release, delivery_capability, delivery.option_id, option_rows)
    except (ValueError, KeyError, TypeError):
        _invalid("DELIVERY_INVALID")
    if delivery != expected or len(option_rows) != len(delivery.specimen_ids):
        _invalid("DELIVERY_CONTENT_MISMATCH")
    owner = capabilities[delivery_capability]
    if (source_authority.release_sha256 != release.release_sha256
            or source_authority.capability_id != delivery_capability
            or source_authority.provider_id != owner.provider_id
            or source_authority.provider_implementation_sha256
            != owner.provider_implementation_sha256
            or source_authority.content_sha256 != source_content_digest(target_rows)
            or source_authority.each != len(target_rows)):
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
        rehearsal_authorities: dict,
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
    rehearsal = rehearsal_by_id.get(identity)
    row_authority = rehearsal_authorities.get(identity, source_authority)
    family = row_authority.source_family_id
    episode = row.get("episode_id")
    if not isinstance(episode, str) or not episode:
        episode = row["id"]
    if operation_id is None and isinstance(row.get("record"), dict):
        operation_id = row["record"].get("operator")
    if ((source_id is not None
         and (not isinstance(source_id, str) or not source_id))
            or (operation_id is not None
                and (not isinstance(operation_id, str) or not operation_id))):
        _invalid("SOURCE_OR_OPERATION_INVALID")
    option_row = identity in set(delivery.specimen_ids)
    if option_row and delivery.option_id == "source.direct/" + delivery_capability:
        if capability != delivery_capability:
            _invalid("DELIVERY_CAPABILITY_MISMATCH")
    elif rehearsal is not None:
        if rehearsal not in {"prior", "preservation", "retention_support"}:
            _invalid("DELIVERY_CAPABILITY_MISMATCH")
    elif (capability not in {delivery_capability, *owner.prerequisites}
          or capabilities[capability].provider_id != owner.provider_id
          or capabilities[capability].provider_implementation_sha256
          != owner.provider_implementation_sha256):
        _invalid("DELIVERY_CAPABILITY_MISMATCH")
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
