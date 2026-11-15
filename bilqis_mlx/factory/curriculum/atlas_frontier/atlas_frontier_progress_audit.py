"""Cold full-lineage audit and rehydration for compact A09 progress heads."""
from __future__ import annotations

from .atlas_frontier_contracts import CurriculumSnapshot, _fail
from .atlas_frontier_progress_contracts import (
    FrontierProgress, StagedSelectionReceipt, _issue_frontier_progress,
)
from .atlas_frontier_progress_index import FrontierHistoryOwner


def rebuild_frontier_history(
    snapshots: tuple[CurriculumSnapshot, ...],
    receipts: tuple[StagedSelectionReceipt, ...],
):
    """Replay complete durable lineage into the same compact authenticated head."""
    if (type(snapshots) is not tuple or not snapshots
            or any(type(item) is not CurriculumSnapshot for item in snapshots)
            or type(receipts) is not tuple
            or any(type(item) is not StagedSelectionReceipt for item in receipts)):
        _fail("BAMF_PLANNER_COLD_HISTORY_INPUT_INVALID")
    owner = FrontierHistoryOwner(snapshots[0], historical=True)
    head = owner.initial_head
    for snapshot in snapshots[1:]:
        head = owner.append_snapshot(
            head, snapshot, strict_duplicate=True, historical=True)
    for receipt in receipts:
        head = owner.append_receipt(head, receipt, historical=True)
    return owner, head


def rehydrate_frontier_progress(
    progress: FrontierProgress,
    snapshots: tuple[CurriculumSnapshot, ...],
    receipts: tuple[StagedSelectionReceipt, ...],
) -> FrontierProgress:
    """Cold-audit detached progress and restore its process-local history owner."""
    if type(progress) is not FrontierProgress:
        _fail("BAMF_PLANNER_COLD_PROGRESS_INVALID")
    owner, head = rebuild_frontier_history(snapshots, receipts)
    if head != progress.history_head:
        _fail("BAMF_PLANNER_COLD_HISTORY_HEAD_MISMATCH")
    _issue_frontier_progress(progress, owner)
    progress.verify()
    return progress


__all__ = ("rebuild_frontier_history", "rehydrate_frontier_progress")
