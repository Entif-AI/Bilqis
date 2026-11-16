"""Issue #1320 learner-relative generated-grade acceptance behavior."""
from dataclasses import replace
import unittest
from bilqis_mlx.factory.atlas_frontier_closure import ClosureStatus
from bilqis_mlx.factory.atlas_frontier_contracts import PlannerBudget
from bilqis_mlx.factory.generated_grade import CostEvidenceKind, GeneratedGradePolicy, synthesize_generated_grade
from bilqis_mlx.factory.tests.curriculum.frontier.atlas_frontier_closure_fixtures import rehash
from bilqis_mlx.factory.tests.curriculum.generated_grade.fixtures import (
    _closure_with_bridge_mastered, _fixture, _inputs, _sha,
)

class GeneratedGradeSynthesisTests(unittest.TestCase):
    def test_representative_cohort_is_deterministic_and_not_a_static_grade_roster(self):
        snapshot, closure, release, evidence, policy, learner = _fixture()
        issued = _inputs(learner, evidence, policy)
        first = synthesize_generated_grade(snapshot, closure, release, issued)
        replay = synthesize_generated_grade(snapshot, closure, release, issued)

        self.assertEqual(first, replay)
        self.assertEqual(first.proposal_sha256, replay.proposal_sha256)
        self.assertNotIn("skos:cluster-b", first.member_semantic_ids)
        self.assertIn("skos:distinct", first.member_semantic_ids)
        self.assertIn("skos:new-z", first.member_semantic_ids)
        self.assertGreaterEqual(len({
            next(item for item in evidence if item.semantic_id == member).neighborhood_id
            for member in first.member_semantic_ids
        }), 3)
        self.assertTrue(all(
            not member.startswith(("A.", "B.", "C."))
            for member in first.member_semantic_ids))
        self.assertEqual(first.snapshot_sha256, snapshot.snapshot_sha256)
        self.assertEqual(first.policy_epoch, snapshot.policy_epoch)
        unknown = next(item for item in first.decisions if item.semantic_id == "skos:unknown")
        self.assertIs(unknown.cost_status, CostEvidenceKind.UNKNOWN)
        self.assertIsNone(unknown.effective_acquisition_units)
        self.assertNotIn("skos:unknown", first.member_semantic_ids)

    def test_mastered_prerequisite_lowers_descendant_cost_and_changes_next_grade(self):
        snapshot, closure, release, evidence, _policy, learner = _fixture()
        policy = GeneratedGradePolicy("learner-relative-grade/v1", 2, 1, 17)
        before = synthesize_generated_grade(
            snapshot, closure, release, _inputs(learner, evidence, policy))
        after_closure = _closure_with_bridge_mastered(closure)
        after_learner = replace(learner, evidence_sha256=_sha("learner-after-bridge"))
        after_evidence = tuple(
            item for item in evidence if item.semantic_id != "skos:bridge")
        after = synthesize_generated_grade(
            snapshot, after_closure, release,
            _inputs(after_learner, after_evidence, policy))

        before_desc = next(
            item for item in before.decisions if item.semantic_id == "skos:descendant")
        after_desc = next(
            item for item in after.decisions if item.semantic_id == "skos:descendant")
        self.assertEqual((before_desc.effective_acquisition_units, before_desc.closure_acquisition_units), (9, 11))
        self.assertEqual((after_desc.effective_acquisition_units, after_desc.closure_acquisition_units), (2, 2))
        self.assertNotIn("skos:descendant", before.member_semantic_ids)
        self.assertIn("skos:descendant", after.member_semantic_ids)
        self.assertNotIn("skos:bridge", after.member_semantic_ids)
        self.assertNotIn("skos:bridge", tuple(
            item.semantic_id for item in after.decisions))
        self.assertEqual(before.snapshot_sha256, after.snapshot_sha256)
        self.assertNotEqual(before.proposal_sha256, after.proposal_sha256)

    def test_selected_composite_places_unmet_constituent_before_dependent(self):
        snapshot, closure, release, evidence, _, learner = _fixture()
        snapshot = rehash(snapshot, budget=PlannerBudget(8, 8, 24))
        closure = replace(
            closure,
            snapshot_sha256=snapshot.snapshot_sha256,
            closure_sha256="0" * 64,
        )
        closure = replace(closure, closure_sha256=closure.expected_digest())
        policy = GeneratedGradePolicy("learner-relative-grade/v1", 8, 1, 17)

        result = synthesize_generated_grade(
            snapshot, closure, release, _inputs(learner, evidence, policy))

        descendant = next(item for item in result.decisions
                          if item.semantic_id == "skos:descendant")
        self.assertEqual(descendant.disposition, "SELECTED_TARGET")
        self.assertLess(
            result.member_semantic_ids.index("skos:bridge"),
            result.member_semantic_ids.index("skos:descendant"),
        )

    def test_high_unlock_or_held_candidates_cannot_bypass_lawful_closure(self):
        snapshot, closure, release, evidence, policy, learner = _fixture()
        result = synthesize_generated_grade(
            snapshot, closure, release, _inputs(learner, evidence, policy))
        decisions = {item.semantic_id: item for item in result.decisions}

        self.assertNotIn("skos:steep", result.member_semantic_ids)
        self.assertEqual(decisions["skos:steep"].disposition, "DEFERRED_STEEP_CLOSURE")
        self.assertEqual(decisions["skos:steep"].downstream_unlocks, 99)
        self.assertIn("WAITING_FOR_EVIDENCE", decisions["skos:steep"].a09_statuses)
        self.assertTrue(any(
            receipt[2] == "PREREQUISITE_WAITING_FOR_EVIDENCE"
            for receipt in decisions["skos:steep"].a09_reason_receipts))
        self.assertEqual(
            result.source_holds,
            (("source/lexicon/held", "SOURCE_RIGHTS_HELD", "source:rights"),),
        )

    def test_manifest_round_trip_is_cold_resume_identical(self):
        snapshot, closure, release, evidence, policy, learner = _fixture()
        proposal = synthesize_generated_grade(
            snapshot, closure, release, _inputs(learner, evidence, policy))

        restored = type(proposal).from_manifest(proposal.manifest())

        self.assertEqual(restored, proposal)
        self.assertEqual(restored.proposal_sha256, proposal.proposal_sha256)
        unknown = next(item for item in restored.decisions
                       if item.semantic_id == "skos:unknown")
        self.assertIsNone(unknown.qualified_transfer_savings)
