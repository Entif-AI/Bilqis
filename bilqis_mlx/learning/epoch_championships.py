"""Capability-local defended championship ownership within one curriculum epoch.

Implementation lives in small internal modules; this facade preserves the established API.
"""
from ._epoch_championships.competition import advance_epoch
from ._epoch_championships.qualification import (
    _challenge_group, _exam_matches_capability, _fanout_scores,
    _incumbent_score, _initial_title_threshold_met, _primary_qualification,
    needed_incumbents,
)
from ._epoch_championships.receipts import (
    _battery_score, _resolve_title_match, _role_receipt, _same_current_context,
)
from ._epoch_championships.state import (
    _archive_invalid_role, _capability_group, _group_caps, _pair_key,
    _sanitize_role_groups, _settled_match, active_frontier,
    rebase_active_championships, reset_active_championships,
    sanitize_role_groups, sanitize_role_origins,
)

__all__ = (
    "active_frontier",
    "advance_epoch",
    "needed_incumbents",
    "rebase_active_championships",
    "reset_active_championships",
    "sanitize_role_groups",
    "sanitize_role_origins",
)
