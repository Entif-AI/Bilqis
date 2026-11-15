"""#1240 compact frontier-history complexity and cold-audit proofs."""
from dataclasses import replace
import hashlib
import unittest

from bilqis_mlx.errors import BilqisError
from bilqis_mlx.factory.atlas_frontier_progress import plan_frontier_progress
from bilqis_mlx.factory.atlas_frontier_progress_audit import (
    rebuild_frontier_history, rehydrate_frontier_progress,
)
from bilqis_mlx.factory.atlas_frontier_progress_metrics import (
    frontier_verification_measurement,
)
from bilqis_mlx.factory.tests.curriculum.frontier.atlas_frontier_closure_fixtures import (
    rehash,
)
from bilqis_mlx.factory.tests.curriculum.frontier.test_atlas_frontier_progress import (
    ProjectionAuthorityFixture, _ready, _staged_ready,
)
from bilqis_mlx.factory.tests.curriculum.frontier.test_atlas_frontier_selection import (
    _candidate, _closure,
)
from bilqis_mlx.runtime.priority_qualification import (
    PriorityPlanningInput, _planning,
)


def _closure_for(snapshot):
    return _closure(snapshot, tuple(
        _candidate(snapshot, identity)
        for identity in snapshot.source_eligible_concept_ids))


def _held_root():
    release, snapshot, _closure_value, _selection = _ready()
    snapshot = rehash(
        snapshot,
        source_eligible_concept_ids=(),
        required_source_family_ids=(),
        coverage_rows=(),
        prerequisite_edges=(),
        cursor=0,
    )
    return release, snapshot, _closure(snapshot, ())


def _successor(snapshot, index: int, *, admission: bool = False):
    changes = {
        "correction_generation": snapshot.correction_generation + 1,
        "event_generation": snapshot.event_generation + 1,
        "predecessor_sha256": snapshot.snapshot_sha256,
    }
    if admission:
        changes.update(
            admitted_factory_release_sha256=hashlib.sha256(
                f"release:{index}".encode()).hexdigest(),
            admission_receipt_sha256=hashlib.sha256(
                f"admission:{index}".encode()).hexdigest(),
        )
    return rehash(snapshot, **changes)


def _lineage(steps: int, *, admission: bool = False):
    release, snapshot, closure = _held_root()
    progress = plan_frontier_progress(snapshot, closure)
    totals = [0, 0, 0]
    snapshots = [snapshot]
    for index in range(1, steps + 1):
        snapshot = _successor(snapshot, index, admission=admission)
        closure = _closure_for(snapshot)
        observed = []
        with frontier_verification_measurement(observed.append):
            progress = plan_frontier_progress(
                snapshot, closure, prior=progress)
        metrics = observed[0]
        totals[0] += metrics.snapshots_rehashed
        totals[1] += metrics.historical_bytes_serialized
        totals[2] += metrics.receipt_history_lookups
        snapshots.append(snapshot)
    return release, progress, closure, tuple(snapshots), tuple(totals)


class FrontierHistoryIndexTests(ProjectionAuthorityFixture, unittest.TestCase):
    def test_hot_progress_holds_only_current_payloads_and_compact_head(self):
        _release, progress, _closure, snapshots, _totals = _lineage(32)
        self.assertFalse(hasattr(progress, "snapshot_history"))
        self.assertFalse(hasattr(progress, "staged_receipts"))
        self.assertEqual(progress.history_head.snapshot_count, len(snapshots))
        self.assertEqual(progress.history_head.receipt_count, 0)
        self.assertEqual(
            progress.history_head.head_snapshot_sha256,
            progress.planning_snapshot.snapshot_sha256)

    def test_synthetic_admission_lineage_has_near_linear_history_work(self):
        _r1, small, _c1, _s1, small_work = _lineage(32, admission=True)
        _r2, large, _c2, _s2, large_work = _lineage(64, admission=True)
        self.assertEqual(small_work[1], 0)
        self.assertEqual(large_work[1], 0)
        self.assertLessEqual(large_work[0], small_work[0] * 2 + 4)
        self.assertLessEqual(large_work[2], small_work[2] * 2 + 4)
        self.assertEqual(small.history_head.snapshot_count, 33)
        self.assertEqual(large.history_head.snapshot_count, 65)

    def test_ordinary_priority_verification_is_history_length_invariant(self):
        release, progress, closure, _snapshots, _work = _lineage(64)
        observed = []
        with frontier_verification_measurement(observed.append):
            _planning(PriorityPlanningInput(progress, closure, None, None), release)
        metrics = observed[0]
        self.assertEqual(metrics.snapshots_rehashed, 1)
        self.assertEqual(metrics.historical_bytes_serialized, 0)
        self.assertEqual(metrics.receipt_history_lookups, 0)

    def test_cold_rebuild_matches_hot_head_and_rehydrates_detached_progress(self):
        _release, snapshot, _closure, selection, receipt = _staged_ready()
        progress = plan_frontier_progress(
            snapshot, _closure_for(snapshot), selection,
            staged_receipt=receipt)
        observed = []
        with frontier_verification_measurement(observed.append):
            _owner, rebuilt = rebuild_frontier_history(
                (snapshot,), (receipt,))
        self.assertEqual(rebuilt, progress.history_head)
        self.assertGreater(observed[0].historical_bytes_serialized, 0)
        detached = replace(progress)
        rehydrate_frontier_progress(detached, (snapshot,), (receipt,))
        detached.verify()

    def test_cold_rebuild_of_long_lineage_reproduces_exact_compact_head(self):
        _release, progress, _closure, snapshots, _work = _lineage(16)
        observed = []
        with frontier_verification_measurement(observed.append):
            _owner, rebuilt = rebuild_frontier_history(snapshots, ())
        self.assertEqual(rebuilt, progress.history_head)
        self.assertEqual(observed[0].snapshots_rehashed, len(snapshots))
        self.assertGreater(observed[0].historical_bytes_serialized, 0)

    def test_cold_audit_rejects_corrupt_predecessor_duplicate_and_altered_root(self):
        _release, snapshot, closure = _held_root()
        progress = plan_frontier_progress(snapshot, closure)
        child = _successor(snapshot, 1)
        bad_link = rehash(child, predecessor_sha256="f" * 64)
        with self.assertRaises(BilqisError):
            rebuild_frontier_history((snapshot, bad_link), ())
        with self.assertRaises(BilqisError):
            rebuild_frontier_history((snapshot, snapshot), ())
        altered = rehash(snapshot, cursor=snapshot.cursor + 1)
        with self.assertRaises(BilqisError):
            rehydrate_frontier_progress(replace(progress), (altered,), ())

    def test_cold_audit_rejects_receipt_whose_historical_ancestor_is_missing(self):
        _release, snapshot, _closure, selection, receipt = _staged_ready()
        progress = plan_frontier_progress(
            snapshot, _closure_for(snapshot), selection,
            staged_receipt=receipt)
        unrelated = rehash(snapshot, cursor=snapshot.cursor + 1)
        with self.assertRaises(BilqisError):
            rehydrate_frontier_progress(
                replace(progress), (unrelated,), (receipt,))


if __name__ == "__main__":
    unittest.main()
