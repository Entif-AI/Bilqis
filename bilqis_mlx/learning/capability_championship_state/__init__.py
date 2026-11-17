"""Authenticated B13 sidecar for per-capability championship lifecycle state."""

from .history import (
    archive_championship_state,
    clear_active_championship_titles,
    clear_championship_epoch,
    empty_championship_state,
    reset_championship_state,
    upgrade_championship_state,
)
from .identity import (
    IDENTITY_SCHEMA,
    championship_epoch_identity,
    comparison_context_sha256,
    settlement_epoch_sha256,
    validate_championship_epoch_identity,
)
from .state import (
    HISTORY_REF_SCHEMA,
    SCHEMA,
    SCHEMA_V1,
    active_checkpoint_references,
    compact_championship_state,
    validate_championship_state,
)


__all__ = (
    "HISTORY_REF_SCHEMA",
    "IDENTITY_SCHEMA",
    "SCHEMA",
    "SCHEMA_V1",
    "active_checkpoint_references",
    "archive_championship_state",
    "championship_epoch_identity",
    "clear_active_championship_titles",
    "clear_championship_epoch",
    "compact_championship_state",
    "comparison_context_sha256",
    "empty_championship_state",
    "reset_championship_state",
    "settlement_epoch_sha256",
    "upgrade_championship_state",
    "validate_championship_epoch_identity",
    "validate_championship_state",
)
