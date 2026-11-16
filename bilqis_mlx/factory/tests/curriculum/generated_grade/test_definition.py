"""Two-phase #1320 proposal -> executable definition boundary."""
from dataclasses import replace
import hashlib
import unittest

from bilqis_mlx.errors import BilqisError
from bilqis_mlx.factory.atlas_frontier_closure import CandidateClosure, ClosureStatus, FrontierClosure
from bilqis_mlx.factory.atlas_frontier_contracts import PlannerBudget
from bilqis_mlx.factory.generated_grade import (
    AcceptedLearnerFoot,
    AcquisitionCostEvidence,
    CandidateDevelopmentEvidence,
    CostEvidenceKind,
    GeneratedGradePolicy,
    seal_generated_grade,
    synthesize_generated_grade,
)
from bilqis_mlx.factory.tests.curriculum.frontier.atlas_frontier_closure_fixtures import (
    rehash,
    row,
    three_node_snapshot,
)
from bilqis_mlx.factory.tests.curriculum.frontier.test_atlas_frontier_selection import _release


def _sha(value: str) -> str:
    return hashlib.sha256(value.encode()).hexdigest()


def _single_member_fixture(semantic_id: str, capability_id: str):
    release = _release()
    snapshot = rehash(
        three_node_snapshot(),
        source_eligible_concept_ids=(semantic_id,),
        required_source_family_ids=("positive_identity",),
        coverage_rows=(row(semantic_id),),
        prerequisite_edges=(),
        source_held_rows=(),
        admitted_factory_release_sha256=release.release_sha256,
        admission_receipt_sha256="7" * 64,
        qualification_epoch=9,
        policy_epoch=4,
        budget=PlannerBudget(1, 1, 10),
    )
    candidate = CandidateClosure(
        semantic_id, "positive_identity", row(semantic_id).source_evidence_sha256,
        ClosureStatus.READY, (), ())
    provisional = FrontierClosure(
        snapshot.snapshot_sha256, _sha("prerequisites"),
        ("positive_identity",), (semantic_id,), (candidate,), (), "0" * 64)
    closure = replace(provisional, closure_sha256=provisional.expected_digest())
    learner = AcceptedLearnerFoot(
        "8" * 64, 10, release.release_sha256, 4, 9, (), (), _sha("learner"))
    source_binding = release.source_bindings.by_capability.get(capability_id)
    source_anchor = (source_binding.source_anchor if source_binding is not None
                     else "source:future")
    evidence = (CandidateDevelopmentEvidence(
        semantic_id=semantic_id,
        compiled_capability_ids=(capability_id,),
        source_anchor_ids=(source_anchor,),
        neighborhood_id="single",
        coverage_factors=("single-factor",),
        acquisition_cost=AcquisitionCostEvidence(
            CostEvidenceKind.MEASURED, "optimizer-steps-to-criterion", 1),
        grounding_quality=3, answer_modality_burden=0, ast_burden=0,
        entanglement=0, reusable_constituent_value=1, downstream_unlocks=1,
        minimal_contrast_value=1, transfer_breadth=1, learning_progress=1,
        fairness_age=1, planning_compute_units=1,
        evidence_sha256=_sha("development:" + semantic_id)),)
    policy = GeneratedGradePolicy("learner-relative-grade/v1", 1, 0)
    proposal = synthesize_generated_grade(
        snapshot, closure, release, learner, evidence, policy)
    return release, proposal


class GeneratedGradeDefinitionTests(unittest.TestCase):
    def test_definition_seals_only_when_member_is_executable_in_exact_release(self):
        release = _release()
        capability = next(iter(release.curriculum.capability_map.values()))
        semantic_id = release.semantic_catalog[0]
        exact_release, proposal = _single_member_fixture(
            semantic_id, capability.capability_id)

        definition = seal_generated_grade(
            proposal, exact_release, ((semantic_id, capability.capability_id),))

        self.assertEqual(definition.adopted_release_sha256, exact_release.release_sha256)
        self.assertEqual(definition.proposal_sha256, proposal.proposal_sha256)
        self.assertEqual(definition.member_semantic_ids, (semantic_id,))
        self.assertEqual(definition.members[0].capability_id, capability.capability_id)
        self.assertEqual(
            definition.members[0].source_anchor,
            exact_release.source_bindings.by_capability[capability.capability_id].source_anchor)

    def test_proposal_for_unadmitted_semantic_cannot_be_sealed_early(self):
        capability_id = "Z.FUTURE"
        release, proposal = _single_member_fixture("skos:future-z", capability_id)

        with self.assertRaises(BilqisError) as raised:
            seal_generated_grade(
                proposal, release, (("skos:future-z", capability_id),))

        self.assertEqual(
            raised.exception.context.get("reason"),
            "BAMF_GENERATED_GRADE_MEMBER_NOT_EXECUTABLE")
