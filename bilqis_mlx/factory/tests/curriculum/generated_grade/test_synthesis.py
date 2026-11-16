"""Issue #1320 learner-relative generated-grade acceptance fixtures."""
from dataclasses import replace
import hashlib
import unittest
from bilqis_mlx.factory.atlas_frontier_closure import (
    CandidateClosure,
    ClosureReason,
    ClosureStatus,
    FrontierClosure,
    SourceHold,
)
from bilqis_mlx.factory.atlas_frontier_contracts import PlannerBudget, PrerequisiteEdge
from bilqis_mlx.factory.generated_grade import (
    AcceptedLearnerFoot,
    AcquisitionCostEvidence,
    CandidateDevelopmentEvidence,
    CostEvidenceKind,
    GeneratedGradePolicy,
    synthesize_generated_grade,
)
from bilqis_mlx.factory.generated_grade.contracts import _issue_inputs
from bilqis_mlx.factory.atlas_frontier_contracts import _bytes
from bilqis_mlx.factory.tests.curriculum.frontier.atlas_frontier_closure_fixtures import (
    rehash,
    row,
    three_node_snapshot,
)
from bilqis_mlx.factory.tests.curriculum.frontier.test_atlas_frontier_selection import (
    _release,
)
from bilqis_mlx.semantics.atlas_projection import CorpusCoverageRow
def _sha(label: str) -> str:
    return hashlib.sha256(label.encode()).hexdigest()


def _inputs(learner, evidence, policy, *, status="PROPOSAL"):
    values = dict(
        learner=learner,
        candidate_evidence=evidence,
        policy=policy,
        a09_progress_sha256=_sha("a09-progress"),
        a09_status=status,
        a09_handoff_sha256=_sha("a09-handoff"),
        a09_proposal_sha256=_sha("a09-proposal"),
        schema="bilqis.generated-grade-inputs/v1",
    )
    digest = hashlib.sha256(_bytes(values)).hexdigest()
    return _issue_inputs(**values, input_sha256=digest)

def _fixture():
    release = _release()
    ids = (
        "skos:bridge", "skos:cluster-a", "skos:cluster-b", "skos:descendant",
        "skos:distinct", "skos:new-z", "skos:steep", "skos:unknown",
    )
    edges = (
        PrerequisiteEdge("skos:descendant", "skos:bridge", "a" * 64),
        PrerequisiteEdge("skos:steep", "skos:bridge", "b" * 64),
        PrerequisiteEdge("skos:steep", "skos:distinct", "c" * 64),
    )
    base = three_node_snapshot()
    snapshot = rehash(
        base,
        source_eligible_concept_ids=ids,
        coverage_rows=tuple(row(identity) for identity in ids),
        prerequisite_edges=edges,
        admitted_factory_release_sha256=release.release_sha256,
        admission_receipt_sha256="7" * 64,
        budget=PlannerBudget(4, 4, 12),
        policy_epoch=17,
        qualification_epoch=23,
        source_held_rows=(CorpusCoverageRow(
            "source", "lexicon", "held", "skos:held", "SOURCE_HELD",
            "IMPLEMENTATION_UNCOVERED", False, "SOURCE_RIGHTS_HELD",
            "rights not admitted", "source:rights"),),
    )
    waiting = ClosureReason(
        "PREREQUISITE_WAITING_FOR_EVIDENCE", "factory:prerequisite", "skos:bridge")
    steep_waiting = (
        waiting,
        ClosureReason(
            "PREREQUISITE_WAITING_FOR_EVIDENCE", "factory:prerequisite", "skos:distinct"),
    )
    candidates = (
        CandidateClosure("skos:bridge", "positive_identity", row("skos:bridge").source_evidence_sha256,
                         ClosureStatus.READY, (), ()),
        CandidateClosure("skos:cluster-a", "positive_identity", row("skos:cluster-a").source_evidence_sha256,
                         ClosureStatus.READY, (), ()),
        CandidateClosure("skos:cluster-b", "positive_identity", row("skos:cluster-b").source_evidence_sha256,
                         ClosureStatus.READY, (), ()),
        CandidateClosure("skos:descendant", "positive_identity", row("skos:descendant").source_evidence_sha256,
                         ClosureStatus.WAITING_FOR_EVIDENCE, ("skos:bridge",), (waiting,)),
        CandidateClosure("skos:distinct", "positive_identity", row("skos:distinct").source_evidence_sha256,
                         ClosureStatus.READY, (), ()),
        CandidateClosure("skos:new-z", "positive_identity", row("skos:new-z").source_evidence_sha256,
                         ClosureStatus.READY, (), ()),
        CandidateClosure("skos:steep", "positive_identity", row("skos:steep").source_evidence_sha256,
                         ClosureStatus.WAITING_FOR_EVIDENCE,
                         ("skos:bridge", "skos:distinct"), steep_waiting),
        CandidateClosure("skos:unknown", "positive_identity", row("skos:unknown").source_evidence_sha256,
                         ClosureStatus.READY, (), ()),
    )
    provisional = FrontierClosure(
        snapshot.snapshot_sha256,
        _sha("prerequisite-evidence"),
        ("positive_identity",),
        ids,
        tuple(sorted(candidates)),
        (SourceHold("source/lexicon/held", "SOURCE_RIGHTS_HELD", "source:rights"),),
        "0" * 64,
    )
    closure = replace(provisional, closure_sha256=provisional.expected_digest())
    evidence = tuple(
        CandidateDevelopmentEvidence(
            semantic_id=identity,
            compiled_capability_ids=("factory:" + identity,),
            source_anchor_ids=("source:" + identity,),
            neighborhood_id=neighborhood,
            coverage_factors=(coverage,),
            acquisition_cost=AcquisitionCostEvidence(
                status=cost_kind,
                measure="optimizer-steps-to-criterion",
                units=cost,
                transfer_savings=transfer,
            ),
            grounding_quality=grounding,
            answer_modality_burden=modality,
            ast_burden=ast,
            entanglement=entanglement,
            reusable_constituent_value=reuse,
            downstream_unlocks=unlocks,
            minimal_contrast_value=contrast,
            transfer_breadth=breadth,
            learning_progress=progress,
            fairness_age=age,
            planning_compute_units=compute,
            evidence_sha256=_sha("dev:" + identity),
        )
        for identity, neighborhood, coverage, cost_kind, cost, transfer, grounding,
            modality, ast, entanglement, reuse, unlocks, contrast, breadth,
            progress, age, compute in (
            ("skos:bridge", "bridge", "relation", CostEvidenceKind.MEASURED, 2, (), 3, 0, 0, 0, 4, 4, 3, 2, 2, 6, 1),
            ("skos:cluster-a", "cluster", "identity", CostEvidenceKind.MEASURED, 1, (), 3, 0, 0, 0, 1, 1, 1, 1, 2, 8, 1),
            ("skos:cluster-b", "cluster", "identity", CostEvidenceKind.MEASURED, 1, (), 3, 0, 0, 0, 1, 1, 1, 1, 1, 7, 1),
            ("skos:descendant", "desc", "composition", CostEvidenceKind.MEASURED, 9,
             (("skos:bridge", 7),), 3, 0, 1, 0, 5, 5, 4, 3, 4, 5, 2),
            ("skos:distinct", "distinct", "quantity", CostEvidenceKind.BOOTSTRAPPED, 2, (), 3, 0, 0, 0, 3, 2, 5, 3, 3, 6, 1),
            ("skos:new-z", "new-z", "new-factor", CostEvidenceKind.MEASURED, 1, (), 3, 0, 0, 0, 4, 3, 6, 4, 4, 5, 1),
            ("skos:steep", "steep", "mega-unlock", CostEvidenceKind.MEASURED, 1, (), 3, 0, 3, 2, 9, 99, 9, 9, 5, 10, 4),
            ("skos:unknown", "cluster", "identity", CostEvidenceKind.UNKNOWN, None, (), 3, 0, 0, 0, 1, 1, 1, 1, 1, 4, 1),
        )
    )
    policy = GeneratedGradePolicy(
        policy_id="learner-relative-grade/v1",
        max_members=4,
        max_unmet_prerequisites=1,
    )
    learner = AcceptedLearnerFoot(
        checkpoint_sha256="8" * 64,
        optimizer_step=100,
        factory_release_sha256=release.release_sha256,
        policy_epoch=17,
        evidence_epoch=23,
        baselined_semantic_ids=(),
        mastered_capability_ids=(),
        evidence_sha256=_sha("learner-before"),
    )
    return snapshot, closure, release, evidence, policy, learner

class GeneratedGradeSynthesisTests(unittest.TestCase):
    def test_representative_cohort_is_deterministic_and_not_a_static_grade_roster(self):
        snapshot, closure, release, evidence, policy, learner = _fixture()
        issued = _inputs(learner, evidence, policy)
        first = synthesize_generated_grade(snapshot, closure, release, issued)
        replay = synthesize_generated_grade(snapshot, closure, release, issued)

        self.assertEqual(first, replay)
        self.assertEqual(first.proposal_sha256, replay.proposal_sha256)
        self.assertIn("skos:cluster-a", first.member_semantic_ids)
        self.assertNotIn("skos:cluster-b", first.member_semantic_ids)
        self.assertIn("skos:distinct", first.member_semantic_ids)
        self.assertIn("skos:new-z", first.member_semantic_ids)
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
        snapshot, closure, release, evidence, policy, learner = _fixture()
        before = synthesize_generated_grade(
            snapshot, closure, release, _inputs(learner, evidence, policy))
        after_learner = replace(
            learner,
            baselined_semantic_ids=("skos:bridge",),
            evidence_sha256=_sha("learner-after-bridge"),
        )
        after = synthesize_generated_grade(
            snapshot, closure, release, _inputs(after_learner, evidence, policy))

        before_desc = next(
            item for item in before.decisions if item.semantic_id == "skos:descendant")
        after_desc = next(
            item for item in after.decisions if item.semantic_id == "skos:descendant")
        self.assertEqual((before_desc.effective_acquisition_units, before_desc.closure_acquisition_units), (9, 11))
        self.assertEqual((after_desc.effective_acquisition_units, after_desc.closure_acquisition_units), (2, 2))
        self.assertNotIn("skos:descendant", before.member_semantic_ids)
        self.assertIn("skos:descendant", after.member_semantic_ids)
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
        policy = GeneratedGradePolicy("learner-relative-grade/v1", 8, 1)

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
