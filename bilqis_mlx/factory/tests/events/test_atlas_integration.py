import hashlib
from dataclasses import replace
import unittest

from bilqis_mlx.errors import BilqisError
from bilqis_mlx.factory import candidate_realizations
from bilqis_mlx.factory.atlas_frontier import (
    AtlasCoverageEpoch,
    bind_realized_snapshot,
    next_atlas_delta,
    staged_selection_receipt,
)
from bilqis_mlx.factory.atlas_frontier_closure import resolve_frontier_closure
from bilqis_mlx.factory.atlas_frontier_events import FactoryAdmissionEvent, reconcile
from bilqis_mlx.factory.atlas_frontier_progress import plan_frontier_progress
from bilqis_mlx.factory.atlas_frontier_progress_contracts import FrontierStatus
from bilqis_mlx.factory.atlas_frontier_progress_validation import (
    credited_obligation_keys, current_obligations,
)
from bilqis_mlx.factory.atlas_delta_adapter import _issue_accepted_obligation_credit
from bilqis_mlx.factory.atlas_delta_scope import AtlasDeltaScopeHandoff
from bilqis_mlx.factory.atlas_frontier_selection import select_frontier_delta_for_projection
from bilqis_mlx.factory.atlas_frontier_selection import _candidate_signature
from bilqis_mlx.factory.atlas_frontier_selection_validation import obligation_signature
from bilqis_mlx.factory.autonomy import (
    EvidenceReceipt,
    compile_autonomy_plan,
    initial_evidence_ledger,
    obligations_for_capability,
    record_evidence,
)
from bilqis_mlx.factory.jit_curriculum import CurriculumDeltaProposal
from bilqis_mlx.factory.tests.events.support import (
    EventCandidateRealizationFixture,
    LEGACY,
)
from bilqis_mlx.source_adapters import event_frames


class EventCandidateAtlasIntegrationTests(EventCandidateRealizationFixture, unittest.TestCase):
    def _stage_capability(self, candidate, source_frontier, policy, state, capability):
        current, graph, mastered, prior, admitted_snapshot = state
        semantic_id = event_frames.atlas_semantic_id(capability)
        staged = candidate_realizations.prepare_realized_candidate(
            self.frontier, current, graph, semantic_id,
            source_root=LEGACY, source_registry=self.source_registry,
            answer_registry=self.answer_registry,
        )
        snapshot = (
            self.build_snapshot(candidate, source_frontier, policy, current, staged)
            if admitted_snapshot is None else admitted_snapshot
        )
        snapshot = bind_realized_snapshot(
            snapshot, candidate, self.frontier, current, (staged,))
        translated = {
            (edge.semantic_id, edge.prerequisite_semantic_id, edge.status)
            for edge in snapshot.prerequisite_edges
        }
        expected_previous = {
            "D.COMMENCEMENT": "D.EVENT_OCCURRENCE",
            "D.TERMINATION": "D.COMMENCEMENT",
        }.get(capability)
        if expected_previous is not None:
            self.assertIn((
                semantic_id,
                event_frames.atlas_semantic_id(expected_previous),
                "FRONTIER_HYPOTHESIS_UNVERIFIED",
            ), translated)
        plan, checkpoint, step, ledger, learner = self.learner_evidence(
            current, mastered, capability)
        closure = resolve_frontier_closure(
            snapshot, candidate.census, current_release=current,
            evidence_ledger=ledger, autonomy_plan=plan,
            checkpoint_sha256=checkpoint, optimizer_step=step,
        )
        if prior is not None:
            prior = plan_frontier_progress(snapshot, closure, prior=prior)
            self.assertIs(prior.status, FrontierStatus.REPLAN_REQUIRED)
            snapshot = prior.planning_snapshot
            closure = resolve_frontier_closure(
                snapshot, candidate.census, current_release=current,
                evidence_ledger=ledger, autonomy_plan=plan,
                checkpoint_sha256=checkpoint, optimizer_step=step,
            )
        pending = self._assert_delta(
            candidate, current, semantic_id, staged, snapshot, closure,
            prior, learner, plan,
        )
        admitted_snapshot = self._admit(snapshot, staged, capability)
        graph = candidate_realizations.admitted_candidate_graph(staged, graph)
        return staged.successor, graph, mastered | {capability}, pending, admitted_snapshot

    def _assert_delta(self, candidate, current, semantic_id, staged, snapshot,
                      closure, prior, learner, plan):
        epoch = AtlasCoverageEpoch(
            snapshot=snapshot, closure=closure, candidate_frontier=self.frontier,
            current_release=current, staged_candidates=(staged,), prior=prior,
        )
        handoff = next_atlas_delta(epoch, learner, plan)
        self.assertIsInstance(handoff, AtlasDeltaScopeHandoff)
        handoff.verify()
        proposal = handoff.proposal
        self.assertIsInstance(proposal, CurriculumDeltaProposal)
        self.assertEqual(proposal.selected_candidate_ids, (staged.candidate_id,))
        self.assertEqual(
            proposal.selected_successor_sha256, staged.successor.release_sha256)
        self.assertEqual(handoff.staged_candidate.staged_sha256, staged.staged_sha256)
        self.assertEqual(
            tuple(scope.capability_id for scope in handoff.operator_scopes),
            handoff.receipt.selection.introduced_capability_ids,
        )
        for scope in handoff.operator_scopes:
            self.assertEqual(
                scope.operator_id, event_frames.SYMBOLS[scope.capability_id])
        self.assertEqual(
            handoff.operator_ids,
            tuple(sorted(event_frames.SYMBOLS[capability]
                         for capability in handoff.receipt.selection.introduced_capability_ids)),
        )
        rows = tuple(item for item in closure.candidates if item.semantic_id == semantic_id)
        requested = (() if prior is None else tuple(sorted(
            credited_obligation_keys(
                snapshot, closure, prior, current_obligations(closure)))))
        projection = candidate_realizations.project_authoritative_target(
            semantic_id, current, rows)
        selection = select_frontier_delta_for_projection(
            snapshot, closure, current, projection, requested)
        receipt = staged_selection_receipt(epoch, selection, projection, staged)
        self._last_staged_selection_receipt = receipt
        pending = plan_frontier_progress(
            snapshot, closure, selection, current_release=current,
            selected_projection=projection, prior=prior, staged_receipt=receipt,
        )
        self.assertIs(pending.status, FrontierStatus.LEASE_REQUIRED)
        return pending

    def _admit(self, snapshot, staged, capability):
        admission = FactoryAdmissionEvent(
            predecessor_sha256=snapshot.snapshot_sha256,
            generation=snapshot.event_generation + 1,
            source_provenance_sha256=snapshot.source_coverage_sha256,
            factory_release_sha256=staged.successor.release_sha256,
            admission_receipt_sha256=hashlib.sha256(
                f"test-admission:{capability}".encode()).hexdigest(),
            accepted=True, event_sha256="0" * 64,
        )
        admission = replace(admission, event_sha256=admission.expected_digest())
        return reconcile(snapshot, admission)

    def _assert_final_frontier(
        self,
        candidate,
        state,
        *,
        expected_status=FrontierStatus.IMPLEMENTATION_UNCOVERED,
        expected_uncovered=6,
    ):
        current, _, mastered, prior, admitted_snapshot = state
        final_snapshot = bind_realized_snapshot(
            admitted_snapshot, candidate, self.frontier, current, ())
        final_plan = compile_autonomy_plan(current)
        final_checkpoint = "e" * 64
        final_ledger = initial_evidence_ledger(current, plan=final_plan)
        final_index = 0
        for prerequisite in sorted(mastered):
            for obligation in obligations_for_capability(current, prerequisite, plan=final_plan):
                final_index += 1
                final_ledger = record_evidence(
                    current,
                    final_ledger,
                    EvidenceReceipt(
                        obligation.obligation_id,
                        f"final-event-prerequisite-{final_index}",
                        final_checkpoint,
                        0,
                        hashlib.sha256(f"final:{final_index}".encode()).hexdigest(),
                        obligation.minimum_specimens,
                        True,
                    ),
                    plan=final_plan,
                    current_checkpoint_sha256=final_checkpoint,
                    current_optimizer_step=0,
                )
        final_closure = resolve_frontier_closure(
            final_snapshot, candidate.census,
            current_release=current,
            evidence_ledger=final_ledger,
            autonomy_plan=final_plan,
            checkpoint_sha256=final_checkpoint,
            optimizer_step=0,
        )
        final_progress = plan_frontier_progress(final_snapshot, final_closure, prior=prior)
        event_ids = {
            event_frames.atlas_semantic_id(capability)
            for capability in event_frames.SOURCE_SPECS
        }
        self.assertTrue(all(
            row.implementation_status == "FACTORY_PROGRAM_BOUND_UNADMITTED"
            for row in final_snapshot.coverage_rows if row.semantic_id in event_ids
        ))
        self.assertEqual(final_progress.requested_semantic_ids, tuple(sorted(event_ids)))
        self.assertIs(final_progress.status, expected_status)
        self.assertEqual(
            final_progress.implementation_uncovered_count,
            expected_uncovered,
        )

    def test_atlas_adapter_proposes_three_real_source_qualified_successors(self):
        candidate, source_frontier, policy = self.atlas_fixture()
        state = (self.current, self.parent_graph, {"A.IDENTITY"}, None, None)
        observed = []
        for capability in event_frames.SOURCE_SPECS:
            state = self._stage_capability(
                candidate, source_frontier, policy, state, capability)
            observed.append(capability)
        self.assertEqual(tuple(observed), tuple(event_frames.SOURCE_SPECS))
        self._assert_final_frontier(candidate, state)

    def test_cold_rebuild_skips_realized_semantic_already_in_accepted_release(self):
        candidate, source_frontier, policy = self.atlas_fixture()
        state = (self.current, self.parent_graph, {"A.IDENTITY"}, None, None)
        current, graph, mastered, prior, _admitted_snapshot = self._stage_capability(
            candidate, source_frontier, policy, state, "D.EVENT_OCCURRENCE")
        accepted_credit = _issue_accepted_obligation_credit(
            current.release_sha256,
            "a" * 64,
            prior.all_requested_obligation_keys(),
        )

        semantic_id = event_frames.atlas_semantic_id("D.COMMENCEMENT")
        staged = candidate_realizations.prepare_realized_candidate(
            self.frontier, current, graph, semantic_id,
            source_root=LEGACY, source_registry=self.source_registry,
            answer_registry=self.answer_registry)
        snapshot = self.build_snapshot(
            candidate, source_frontier, policy, current, staged)
        snapshot = bind_realized_snapshot(
            snapshot, candidate, self.frontier, current, (staged,))
        plan, checkpoint, step, ledger, learner = self.learner_evidence(
            current, mastered, "D.COMMENCEMENT")
        closure = resolve_frontier_closure(
            snapshot, candidate.census, current_release=current,
            evidence_ledger=ledger, autonomy_plan=plan,
            checkpoint_sha256=checkpoint, optimizer_step=step)

        handoff = next_atlas_delta(
            AtlasCoverageEpoch(
                snapshot, closure, self.frontier, current, (staged,), None,
                accepted_credit),
            learner, plan)

        self.assertIsInstance(handoff, AtlasDeltaScopeHandoff)
        handoff.verify()
        self.assertEqual(handoff.receipt.selected_semantic_id, semantic_id)

    def test_cold_rebuild_reopens_accepted_semantic_when_obligation_changes(self):
        candidate, source_frontier, policy = self.atlas_fixture()
        state = (self.current, self.parent_graph, {"A.IDENTITY"}, None, None)
        current, graph, mastered, prior, _admitted_snapshot = self._stage_capability(
            candidate, source_frontier, policy, state, "D.EVENT_OCCURRENCE")
        accepted_credit = _issue_accepted_obligation_credit(
            current.release_sha256,
            "a" * 64,
            prior.all_requested_obligation_keys(),
        )

        semantic_id = event_frames.atlas_semantic_id("D.COMMENCEMENT")
        staged = candidate_realizations.prepare_realized_candidate(
            self.frontier, current, graph, semantic_id,
            source_root=LEGACY, source_registry=self.source_registry,
            answer_registry=self.answer_registry)
        snapshot = self.build_snapshot(
            candidate, source_frontier, policy, current, staged)
        snapshot = bind_realized_snapshot(
            snapshot, candidate, self.frontier, current, (staged,))
        occurrence_id = event_frames.atlas_semantic_id("D.EVENT_OCCURRENCE")
        rows = tuple(
            replace(row, source_evidence_sha256="c" * 64)
            if row.semantic_id == occurrence_id else row
            for row in snapshot.coverage_rows)
        changed = replace(
            snapshot, coverage_rows=rows,
            correction_generation=snapshot.correction_generation + 1,
            snapshot_sha256="0" * 64)
        snapshot = replace(changed, snapshot_sha256=changed.expected_digest())
        plan, checkpoint, step, ledger, learner = self.learner_evidence(
            current, mastered, "D.COMMENCEMENT")
        closure = resolve_frontier_closure(
            snapshot, candidate.census, current_release=current,
            evidence_ledger=ledger, autonomy_plan=plan,
            checkpoint_sha256=checkpoint, optimizer_step=step)

        result = next_atlas_delta(
            AtlasCoverageEpoch(
                snapshot, closure, self.frontier, current, (staged,), None,
                accepted_credit),
            learner, plan)

        self.assertIs(result, FrontierStatus.IMPLEMENTATION_UNCOVERED)

    def test_staged_receipt_rejects_rehashed_obligation_substitution(self):
        candidate, source_frontier, policy = self.atlas_fixture()
        state = (self.current, self.parent_graph, {"A.IDENTITY"}, None, None)
        _current, _graph, _mastered, prior, _snapshot = self._stage_capability(
            candidate, source_frontier, policy, state, "D.EVENT_OCCURRENCE")
        receipt = self._last_staged_selection_receipt
        selected = receipt.selection.selected_obligations
        forged_rows = (
            replace(selected[0], source_evidence_sha256="c" * 64),
            *selected[1:],
        )
        forged_projection = replace(
            receipt.projection,
            obligation_signature=obligation_signature(forged_rows),
            projection_sha256="0" * 64,
        )
        forged_projection = replace(
            forged_projection,
            projection_sha256=forged_projection.expected_digest(),
        )
        forged_selection = replace(
            receipt.selection,
            selected_obligations=forged_rows,
            candidate_signature=_candidate_signature(
                receipt.selected_semantic_id,
                forged_rows,
                receipt.selection.introduced_capability_ids,
                receipt.selection.introduced_semantic_ids,
            ),
            selection_sha256="0" * 64,
        )
        forged_selection = replace(
            forged_selection,
            selection_sha256=forged_selection.expected_digest(),
        )
        forged = replace(
            receipt,
            selection=forged_selection,
            projection=forged_projection,
            receipt_sha256="0" * 64,
        )
        forged = replace(forged, receipt_sha256=forged.expected_digest())

        with self.assertRaises(BilqisError) as caught:
            forged.verify()
        self.assertEqual(
            caught.exception.context["reason"],
            "BAMF_PLANNER_STAGED_SELECTION_INVALID",
        )


if __name__ == "__main__":
    unittest.main()
