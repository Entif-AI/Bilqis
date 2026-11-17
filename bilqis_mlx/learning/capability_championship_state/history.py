"""Epoch reset, archival references, and backward-readable state migration."""
from copy import deepcopy

from bilqis_mlx.semantics.domains import contract_digest

from .identity import (
    _invalid,
    _sha,
    comparison_context_sha256,
    settlement_epoch_sha256,
    validate_championship_epoch_identity,
)
from .state import (
    HISTORY_REF_SCHEMA,
    SCHEMA,
    _normalize_settled_matchups,
    _validate_history_reference,
    validate_championship_state,
)


def _history_reference(record, *, source_manifest_sha256, source_generation, reason):
    if (not _sha(source_manifest_sha256) or type(source_generation) is not int
            or source_generation < 0 or not isinstance(reason, str) or not reason):
        _invalid("CHAMPIONSHIP_HISTORY_REFERENCE_INVALID")
    payload = {
        "schema": HISTORY_REF_SCHEMA,
        "source_manifest_sha256": source_manifest_sha256,
        "source_generation": source_generation,
        "championship_state_sha256": contract_digest(record),
        "identity_sha256": contract_digest(record["identity"]),
        "settlement_epoch_sha256": settlement_epoch_sha256(record["identity"]),
        "comparison_context_sha256": comparison_context_sha256(record["identity"]),
        "settled_matchups_sha256": contract_digest(record["settled_matchups"]),
        "reason": reason,
    }
    return {**payload, "sha256": contract_digest(payload)}


def _as_v2(record):
    validate_championship_state(record)
    if record["schema"] == SCHEMA:
        return deepcopy(record)
    identity = record["identity"]
    return {
        "schema": SCHEMA,
        "identity": deepcopy(identity),
        "active_roles": deepcopy(record["active_roles"]),
        "settled_matchups": _normalize_settled_matchups(
            record["settled_matchups"], identity),
        "settlement_epoch_sha256": settlement_epoch_sha256(identity),
        "comparison_context_sha256": comparison_context_sha256(identity),
        "epoch_history": [],
    }


def upgrade_championship_state(record):
    """Operationally normalize a cold-readable v1 sidecar without rewriting it."""
    return _as_v2(record)


def archive_championship_state(
        record, *, source_manifest_sha256, source_generation, reason,
        clear_settlements=False):
    """Archive one hot epoch as a lightweight B13 reference, then clear live authority."""
    updated = _as_v2(record)
    if updated["active_roles"] or updated["settled_matchups"]:
        reference = _history_reference(
            record, source_manifest_sha256=source_manifest_sha256,
            source_generation=source_generation, reason=reason)
        if reference["sha256"] not in {
                item["sha256"] for item in updated["epoch_history"]}:
            updated["epoch_history"].append(reference)
    updated["active_roles"] = {}
    if clear_settlements:
        updated["settled_matchups"] = {}
    return updated


def empty_championship_state(identity, *, epoch_history=()):
    """Start a new semantic epoch with no inherited title authority."""
    validate_championship_epoch_identity(identity)
    history = [deepcopy(item) for item in epoch_history]
    for reference in history:
        _validate_history_reference(reference)
    return {
        "schema": SCHEMA,
        "identity": deepcopy(identity),
        "active_roles": {},
        "settled_matchups": {},
        "settlement_epoch_sha256": settlement_epoch_sha256(identity),
        "comparison_context_sha256": comparison_context_sha256(identity),
        "epoch_history": history,
    }


def reset_championship_state(
        prior, identity, *, source_manifest_sha256=None, source_generation=None,
        reason="CHAMPIONSHIP_IDENTITY_RESET"):
    """Reset roles and carry only settlements still inside the same championship epoch."""
    validate_championship_state(prior)
    validate_championship_epoch_identity(identity)
    prior_v2 = _as_v2(prior)
    if source_manifest_sha256 is not None or source_generation is not None:
        prior_v2 = archive_championship_state(
            prior, source_manifest_sha256=source_manifest_sha256,
            source_generation=source_generation, reason=reason)
    reset = empty_championship_state(
        identity, epoch_history=prior_v2["epoch_history"])
    if settlement_epoch_sha256(prior_v2["identity"]) == settlement_epoch_sha256(identity):
        reset["settled_matchups"] = deepcopy(prior_v2["settled_matchups"])
    return reset


def clear_active_championship_titles(
        record, *, source_manifest_sha256=None, source_generation=None,
        reason="CHAMPIONSHIP_ACTIVE_TITLES_CLEARED"):
    """Clear live title custody while retaining epoch-local settled receipts."""
    validate_championship_state(record)
    if source_manifest_sha256 is not None or source_generation is not None:
        return archive_championship_state(
            record, source_manifest_sha256=source_manifest_sha256,
            source_generation=source_generation, reason=reason)
    cleared = _as_v2(record)
    cleared["active_roles"] = {}
    return cleared


def clear_championship_epoch(
        record, *, source_manifest_sha256, source_generation,
        reason="NEW_SEMANTIC_ADMISSION"):
    """Archive and clear all live competition authority at a semantic boundary."""
    return archive_championship_state(
        record, source_manifest_sha256=source_manifest_sha256,
        source_generation=source_generation, reason=reason,
        clear_settlements=True)
