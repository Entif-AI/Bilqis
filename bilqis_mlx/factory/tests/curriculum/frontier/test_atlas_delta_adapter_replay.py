from dataclasses import replace
from unittest.mock import patch

from bilqis_mlx.factory.atlas_delta_adapter import _credited_requested_keys
from bilqis_mlx.factory.atlas_frontier_progress import FrontierStatus, plan_frontier_progress
from bilqis_mlx.factory.atlas_frontier_closure import ClosureReason, ClosureStatus
from bilqis_mlx.factory.atlas_frontier_selection import select_frontier_delta
from bilqis_mlx.factory.candidate_realizations import project_authoritative_target
from bilqis_mlx.factory.skos_curriculum import IMPLEMENTATION_UNCOVERED
from bilqis_mlx.factory.tests.curriculum.frontier.atlas_delta_adapter_fixtures import (
    AtlasDeltaAdapterFixture,
)
from bilqis_mlx.factory.tests.curriculum.frontier.atlas_frontier_closure_fixtures import rehash
from bilqis_mlx.factory.tests.curriculum.frontier.test_atlas_frontier_progress import _stage
from bilqis_mlx.factory.tests.curriculum.frontier.test_atlas_frontier_selection import (
    _candidate, _closure,
)


class AtlasDeltaAdapterReplayTests(AtlasDeltaAdapterFixture):
    def test_staged_restart_holds_same_successor_for_existing_admission_owner(self):
        with patch(
            "bilqis_mlx.factory.candidate_realizations.project_realized_target",
            side_effect=self._authority,
        ), patch(
            "bilqis_mlx.factory.atlas_frontier_progress_validation.project_realized_target",
            side_effect=self._authority,
        ), patch(
            "bilqis_mlx.factory.candidate_realizations.realized_source_sense_id",
            return_value=self.staged.source_sense_id,
        ):
            projections = tuple(
                project_authoritative_target(
                    identity, self.current,
                    tuple(row for row in self.closure.candidates
                          if row.semantic_id == identity))
                for identity in self.closure.constituent_order)
            selection = select_frontier_delta(
                self.snapshot, self.closure, self.current, projections)
            projection = next(
                item for item in projections
                if item.semantic_id == selection.selected_semantic_id)
            receipt = _stage(
                selection, projection, self.current, self.staged.successor, self.snapshot)
            prior = plan_frontier_progress(
                self.snapshot, self.closure, selection,
                current_release=self.current, selected_projection=projection,
                staged_receipt=receipt)
            result = self._call_with_prior(prior)
        self.assertIs(result, FrontierStatus.LEASE_REQUIRED)
        self.assertEqual(
            prior.pending_staged_successor_sha256, self.staged.successor.release_sha256)

    def _call_with_prior(self, prior):
        from bilqis_mlx.factory.atlas_frontier import next_atlas_delta
        return next_atlas_delta(self._epoch(prior=prior), self.learner, self.plan)

    def test_invalidated_historical_receipt_does_not_suppress_replanning(self):
        with patch(
            "bilqis_mlx.factory.candidate_realizations.project_realized_target",
            side_effect=self._authority,
        ), patch(
            "bilqis_mlx.factory.atlas_frontier_progress_validation.project_realized_target",
            side_effect=self._authority,
        ):
            projections = tuple(
                project_authoritative_target(
                    identity, self.current,
                    tuple(row for row in self.closure.candidates
                          if row.semantic_id == identity))
                for identity in self.closure.constituent_order)
            selection = select_frontier_delta(
                self.snapshot, self.closure, self.current, projections)
            projection = next(
                item for item in projections
                if item.semantic_id == selection.selected_semantic_id)
            receipt = _stage(
                selection, projection, self.current, self.staged.successor, self.snapshot)
            prior = plan_frontier_progress(
                self.snapshot, self.closure, selection,
                current_release=self.current, selected_projection=projection,
                staged_receipt=receipt)
        corrected_rows = tuple(
            replace(row, implementation_status=IMPLEMENTATION_UNCOVERED)
            if row.semantic_id == selection.selected_semantic_id else row
            for row in self.snapshot.coverage_rows)
        corrected = rehash(
            self.snapshot, coverage_rows=corrected_rows,
            event_generation=self.snapshot.event_generation + 1,
            predecessor_sha256=self.snapshot.snapshot_sha256)
        invalidated_reason = ClosureReason(
            "FAMILY_IMPLEMENTATION_UNCOVERED", "family:positive_identity")
        dependent_reason = ClosureReason(
            "PREREQUISITE_IMPLEMENTATION_UNCOVERED", "factory:prerequisite",
            selection.selected_semantic_id)
        corrected_closure = _closure(corrected, tuple(
            _candidate(
                corrected, identity,
                status=(ClosureStatus.IMPLEMENTATION_UNCOVERED
                        if identity in {selection.selected_semantic_id, "z.op.1"}
                        else ClosureStatus.READY),
                reasons=((invalidated_reason,)
                         if identity == selection.selected_semantic_id
                         else ((dependent_reason,) if identity == "z.op.1" else ())),
            ) for identity in corrected.source_eligible_concept_ids))
        with patch(
            "bilqis_mlx.factory.atlas_frontier_progress_validation.project_realized_target",
            side_effect=self._authority,
        ):
            invalidated = plan_frontier_progress(
                corrected, corrected_closure, prior=prior)
            self.assertIs(invalidated.status, FrontierStatus.REPLAN_REQUIRED)
            self.assertIsNone(invalidated.pending_staged_receipt_sha256)
            self.assertEqual(
                invalidated.history_head.receipt_index_sha256,
                prior.history_head.receipt_index_sha256,
            )
            self.assertEqual(
                invalidated.history_head.receipt_count,
                prior.history_head.receipt_count,
            )
            epoch = self._epoch(
                snapshot=corrected, closure=corrected_closure, prior=invalidated)
            self.assertEqual(_credited_requested_keys(epoch), ())
