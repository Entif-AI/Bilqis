"""A09.4 regressions for adjudicated replay and cursor defects."""
from dataclasses import replace
import unittest

from bilqis_mlx.errors import BilqisError
from bilqis_mlx.factory.atlas_frontier_closure import ClosureReason, ClosureStatus
from bilqis_mlx.factory.atlas_frontier_contracts import PrerequisiteEdge
from bilqis_mlx.factory.atlas_frontier_events import SourceReleaseEvent, reconcile
from bilqis_mlx.factory.atlas_frontier_progress import FrontierStatus, plan_frontier_progress
from bilqis_mlx.factory.atlas_frontier_progress_audit import (
    rehydrate_frontier_progress,
)
from bilqis_mlx.factory.atlas_frontier_progress_metrics import (
    frontier_verification_measurement,
)
from bilqis_mlx.factory.atlas_frontier_selection import select_frontier_delta
from bilqis_mlx.factory.skos_curriculum import IMPLEMENTATION_UNCOVERED
from bilqis_mlx.factory.tests.curriculum.frontier.atlas_frontier_closure_fixtures import rehash
from bilqis_mlx.factory.tests.curriculum.frontier.test_atlas_frontier_progress import (
    ProjectionAuthorityFixture,
    _ready,
    _selected_projection,
    _stage,
    _staged_ready,
)
from bilqis_mlx.factory.tests.curriculum.frontier.progress.test_atlas_frontier_progress_dispositions import (
    _admit, _single_ready,
)
from bilqis_mlx.factory.tests.curriculum.frontier.test_atlas_frontier_selection import (
    _candidate, _options,
    _closure,
)
from bilqis_mlx.factory.tests.curriculum.frontier.test_candidate_staging import (
    CandidateStagingFixture,
)


class AtlasFrontierProgressRegressionTests(ProjectionAuthorityFixture, unittest.TestCase):
    def test_selection_schema_fork_fails_closed(self):
        release, snapshot, closure, lawful = _ready()
        projection = _selected_projection(release, snapshot, closure, lawful)
        forged = replace(
            lawful, schema="fixture/frontier-selection-fork", selection_sha256="0" * 64)
        forged = replace(forged, selection_sha256=forged.expected_digest())

        with self.assertRaises(BilqisError):
            plan_frontier_progress(
                snapshot, closure, forged,
                current_release=release, selected_projection=projection)

    def test_staged_receipt_rejects_self_rehashed_alternate_ready_semantic(self):
        release, snapshot, closure, lawful, receipt = _staged_ready()
        alternate_id = next(
            identity for identity in closure.constituent_order
            if identity != lawful.selected_semantic_id)
        alternate_rows = tuple(
            row for row in closure.candidates if row.semantic_id == alternate_id)
        forged = replace(
            lawful,
            selected_semantic_id=alternate_id,
            selected_obligations=alternate_rows,
            selection_sha256="0" * 64,
        )
        forged = replace(forged, selection_sha256=forged.expected_digest())
        forged_receipt = _stage(
            forged, receipt.projection, release, receipt.staged_successor, snapshot)

        with self.assertRaises(BilqisError):
            plan_frontier_progress(
                snapshot, closure, forged,
                current_release=release,
                selected_projection=receipt.projection,
                staged_receipt=forged_receipt)

    def test_historical_receipt_cannot_supply_its_own_comparator_snapshot(self):
        fixture = CandidateStagingFixture()
        fixture.setUp()
        staged = fixture.stage()
        release = fixture.current
        _, snapshot, closure, selection, receipt = _staged_ready()
        prior = plan_frontier_progress(
            snapshot, closure, selection,
            current_release=release,
            selected_projection=receipt.projection,
            staged_receipt=receipt,
        )
        advanced = _admit(prior, snapshot, closure, receipt)

        forged_snapshot = rehash(snapshot, cursor=1)
        forged_closure = _closure(forged_snapshot, tuple(
            _candidate(forged_snapshot, identity)
            for identity in forged_snapshot.source_eligible_concept_ids))
        capabilities = {
            identity: staged.successor.transition.added_capabilities
            for identity in forged_snapshot.source_eligible_concept_ids
        }
        identities = {identity: () for identity in forged_snapshot.source_eligible_concept_ids}
        projections = _options(
            forged_snapshot, release, forged_closure,
            capabilities=capabilities, identities=identities)
        forged_selection = select_frontier_delta(
            forged_snapshot, forged_closure, release, projections)
        forged_projection = next(
            item for item in projections
            if item.semantic_id == forged_selection.selected_semantic_id)
        forged_receipt = _stage(
            forged_selection, forged_projection, release, staged.successor,
            forged_snapshot)
        with self.assertRaises(BilqisError):
            rehydrate_frontier_progress(
                replace(advanced),
                tuple(dict.fromkeys((
                    snapshot,
                    advanced.input_snapshot,
                    advanced.planning_snapshot,
                ))),
                (forged_receipt,),
            )

    def test_admission_reconciliation_reports_only_direct_implementation_debt(self):
        release, staged_snapshot, _, selection, receipt = _staged_ready()
        prior = plan_frontier_progress(
            staged_snapshot,
            _closure(staged_snapshot, tuple(
                _candidate(staged_snapshot, identity)
                for identity in staged_snapshot.source_eligible_concept_ids)),
            selection,
            current_release=release,
            selected_projection=receipt.projection,
            staged_receipt=receipt,
        )
        admitted = rehash(
            staged_snapshot,
            admitted_factory_release_sha256=receipt.staged_successor_sha256,
            admission_receipt_sha256="a" * 64,
            coverage_rows=tuple(
                replace(row, implementation_status=IMPLEMENTATION_UNCOVERED)
                if row.semantic_id == "z.op.0" else row
                for row in staged_snapshot.coverage_rows),
            prerequisite_edges=(
                PrerequisiteEdge("z.op.1", "z.op.0", "a" * 64),
                PrerequisiteEdge("z.op.2", "z.op.0", "b" * 64),
            ),
            predecessor_sha256=staged_snapshot.snapshot_sha256,
            event_generation=staged_snapshot.event_generation + 1,
        )
        direct = ClosureReason(
            "FAMILY_IMPLEMENTATION_UNCOVERED", "family:positive_identity")
        inherited = ClosureReason(
            "PREREQUISITE_IMPLEMENTATION_UNCOVERED", "factory:prerequisite", "z.op.0")
        closure = _closure(admitted, (
            _candidate(
                admitted, "z.op.0", status=ClosureStatus.IMPLEMENTATION_UNCOVERED,
                reasons=(direct,)),
            _candidate(
                admitted, "z.op.1", status=ClosureStatus.IMPLEMENTATION_UNCOVERED,
                reasons=(inherited,)),
            _candidate(
                admitted, "z.op.2", status=ClosureStatus.IMPLEMENTATION_UNCOVERED,
                reasons=(inherited,)),
        ))

        reconciled = plan_frontier_progress(admitted, closure, prior=prior)

        self.assertEqual(reconciled.status, FrontierStatus.IMPLEMENTATION_UNCOVERED)
        self.assertEqual(reconciled.implementation_uncovered_count, 1)

    def test_admission_reconciliation_requires_replan_for_remaining_ready_work(self):
        release, snapshot, closure, selection, receipt = _staged_ready()
        prior = plan_frontier_progress(
            snapshot, closure, selection,
            current_release=release, selected_projection=receipt.projection,
            staged_receipt=receipt)
        admitted = rehash(
            snapshot,
            admitted_factory_release_sha256=receipt.staged_successor_sha256,
            admission_receipt_sha256="a" * 64,
            predecessor_sha256=snapshot.snapshot_sha256,
            event_generation=snapshot.event_generation + 1,
        )
        admitted_closure = _closure(admitted, tuple(
            _candidate(admitted, identity)
            for identity in admitted.source_eligible_concept_ids))

        reconciled = plan_frontier_progress(admitted, admitted_closure, prior=prior)

        self.assertEqual(reconciled.status, FrontierStatus.REPLAN_REQUIRED)

    def test_single_semantic_admission_mints_zero_to_zero_cursor_successor(self):
        snapshot, closure, selection, receipt = _single_ready()
        prior = plan_frontier_progress(
            snapshot, closure, selection,
            current_release=receipt.predecessor_release,
            selected_projection=receipt.projection,
            staged_receipt=receipt)
        admitted = rehash(
            snapshot,
            admitted_factory_release_sha256=receipt.staged_successor_sha256,
            admission_receipt_sha256="a" * 64,
            predecessor_sha256=snapshot.snapshot_sha256,
            event_generation=snapshot.event_generation + 1,
        )
        admitted_closure = _closure(
            admitted, (_candidate(admitted, "z.op.0"),))

        advanced = plan_frontier_progress(admitted, admitted_closure, prior=prior)

        self.assertEqual(advanced.cursor, 0)
        self.assertNotEqual(
            advanced.planning_snapshot.snapshot_sha256, admitted.snapshot_sha256)
        self.assertEqual(
            advanced.planning_snapshot.predecessor_sha256, admitted.snapshot_sha256)
        self.assertEqual(
            advanced,
            plan_frontier_progress(admitted, admitted_closure, prior=prior),
        )

    def test_pending_stage_reopens_when_source_evidence_changes(self):
        release, snapshot, closure, selection, receipt = _staged_ready()
        prior = plan_frontier_progress(
            snapshot, closure, selection,
            current_release=release, selected_projection=receipt.projection,
            staged_receipt=receipt)
        source_rows = tuple(sorted((
            replace(
                row,
                source_evidence_sha256=(
                    "c" * 64 if row.semantic_id == selection.selected_semantic_id
                    else row.source_evidence_sha256),
                implementation_status=IMPLEMENTATION_UNCOVERED,
            )
            for row in snapshot.coverage_rows
        ), key=lambda row: (row.semantic_id, row.family_id)))
        source = rehash(
            snapshot,
            source_coverage_sha256="f" * 64,
            coverage_rows=source_rows,
        )
        event = SourceReleaseEvent(
            snapshot.snapshot_sha256,
            snapshot.event_generation + 1,
            source.source_coverage_sha256,
            source,
            True,
            "0" * 64,
        )
        event = replace(event, event_sha256=event.expected_digest())
        changed = reconcile(snapshot, event)
        changed_closure = _closure(changed, tuple(
            _candidate(changed, identity)
            for identity in changed.source_eligible_concept_ids))

        reopened = plan_frontier_progress(changed, changed_closure, prior=prior)

        self.assertEqual(reopened.status, FrontierStatus.REPLAN_REQUIRED)
        self.assertIsNone(reopened.pending_staged_receipt_sha256)

    def test_pending_stage_survives_metadata_only_epoch_change(self):
        release, snapshot, closure, selection, receipt = _staged_ready()
        prior = plan_frontier_progress(
            snapshot, closure, selection,
            current_release=release, selected_projection=receipt.projection,
            staged_receipt=receipt)
        metadata = rehash(
            snapshot,
            correction_generation=snapshot.correction_generation + 1,
            predecessor_sha256=snapshot.snapshot_sha256,
            event_generation=snapshot.event_generation + 1,
        )
        metadata_closure = _closure(metadata, tuple(
            _candidate(metadata, identity)
            for identity in metadata.source_eligible_concept_ids))

        resumed = plan_frontier_progress(metadata, metadata_closure, prior=prior)

        self.assertEqual(resumed.status, FrontierStatus.LEASE_REQUIRED)
        self.assertEqual(
            resumed.pending_staged_receipt_sha256,
            prior.pending_staged_receipt_sha256,
        )
        self.assertFalse(hasattr(resumed, "pending_receipt"))
        self.assertEqual(
            resumed.pending_staged_successor_sha256,
            receipt.staged_successor_sha256,
        )
        self.assertEqual(resumed.pending_semantic_id, selection.selected_semantic_id)
        observed = []
        with frontier_verification_measurement(observed.append):
            resumed.verify()
        self.assertEqual(observed[0].historical_bytes_serialized, 0)

    def test_predecessor_scope_allows_never_requested_concept_to_leave_frontier(self):
        release, snapshot, closure, selection, receipt = _staged_ready()
        prior = plan_frontier_progress(
            snapshot, closure, selection,
            current_release=release, selected_projection=receipt.projection,
            staged_receipt=receipt)
        retained = {"z.op.0", "z.op.1"}
        contracted = rehash(
            snapshot,
            source_eligible_concept_ids=tuple(sorted(retained)),
            coverage_rows=tuple(
                row for row in snapshot.coverage_rows
                if row.semantic_id in retained),
            prerequisite_edges=tuple(
                edge for edge in snapshot.prerequisite_edges
                if edge.semantic_id in retained
                and edge.prerequisite_semantic_id in retained),
            correction_generation=snapshot.correction_generation + 1,
            event_generation=snapshot.event_generation + 1,
            predecessor_sha256=snapshot.snapshot_sha256,
        )
        contracted_closure = _closure(contracted, tuple(
            _candidate(contracted, identity)
            for identity in contracted.source_eligible_concept_ids))

        resumed = plan_frontier_progress(
            contracted, contracted_closure, prior=prior)

        self.assertEqual(resumed.status, FrontierStatus.LEASE_REQUIRED)
        self.assertEqual(
            resumed.pending_staged_receipt_sha256,
            prior.pending_staged_receipt_sha256)

    def test_predecessor_scope_rejects_requested_concept_leaving_frontier(self):
        release, snapshot, closure, selection, receipt = _staged_ready()
        prior = plan_frontier_progress(
            snapshot, closure, selection,
            current_release=release, selected_projection=receipt.projection,
            staged_receipt=receipt)
        retained = {"z.op.1", "z.op.2"}
        contracted = rehash(
            snapshot,
            source_eligible_concept_ids=tuple(sorted(retained)),
            coverage_rows=tuple(
                row for row in snapshot.coverage_rows
                if row.semantic_id in retained),
            prerequisite_edges=(),
            correction_generation=snapshot.correction_generation + 1,
            event_generation=snapshot.event_generation + 1,
            predecessor_sha256=snapshot.snapshot_sha256,
        )
        contracted_closure = _closure(contracted, tuple(
            _candidate(contracted, identity, prerequisites=())
            for identity in contracted.source_eligible_concept_ids))

        with self.assertRaises(BilqisError) as caught:
            plan_frontier_progress(contracted, contracted_closure, prior=prior)
        self.assertEqual(
            caught.exception.context["reason"],
            "BAMF_PLANNER_PROGRESS_PREDECESSOR_SCOPE_DRIFT")


if __name__ == "__main__":
    unittest.main()
