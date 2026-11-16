"""Learner-relative evidence updates change policy output without semantic mutation."""
from dataclasses import replace
import unittest

from bilqis_mlx.factory.generated_grade import (
    AcquisitionCostEvidence,
    CostEvidenceKind,
    GeneratedGradePolicy,
    synthesize_generated_grade,
)
from bilqis_mlx.factory.tests.curriculum.generated_grade.test_synthesis import _fixture, _inputs


class GeneratedGradePolicyUpdateTests(unittest.TestCase):
    def test_cost_evidence_can_change_membership_with_same_canonical_snapshot(self):
        snapshot, closure, release, evidence, _, learner = _fixture()
        policy = GeneratedGradePolicy("learner-relative-grade/v1", 1, 0)
        before = synthesize_generated_grade(
            snapshot, closure, release, _inputs(learner, evidence, policy))
        changed = tuple(
            replace(
                item,
                acquisition_cost=AcquisitionCostEvidence(
                    CostEvidenceKind.MEASURED,
                    "optimizer-steps-to-criterion",
                    0,
                ),
            ) if item.semantic_id == "skos:distinct" else item
            for item in evidence
        )
        after = synthesize_generated_grade(
            snapshot, closure, release, _inputs(learner, changed, policy))

        self.assertEqual(before.snapshot_sha256, after.snapshot_sha256)
        self.assertEqual(before.learner_foot_sha256, after.learner_foot_sha256)
        self.assertNotEqual(before.member_semantic_ids, after.member_semantic_ids)
        self.assertEqual(after.member_semantic_ids, ("skos:distinct",))

    def test_negative_transfer_is_explicit_interference_and_raises_cost(self):
        snapshot, closure, release, evidence, policy, learner = _fixture()
        learner = replace(
            learner,
            baselined_semantic_ids=("skos:bridge",),
        )
        changed = tuple(
            replace(
                item,
                acquisition_cost=AcquisitionCostEvidence(
                    CostEvidenceKind.MEASURED,
                    "optimizer-steps-to-criterion",
                    9,
                    (("skos:bridge", -3),),
                ),
            ) if item.semantic_id == "skos:descendant" else item
            for item in evidence
        )
        result = synthesize_generated_grade(
            snapshot, closure, release, _inputs(learner, changed, policy))
        descendant = next(
            item for item in result.decisions if item.semantic_id == "skos:descendant")

        self.assertEqual(descendant.applied_transfer_savings, -3)
        self.assertEqual(descendant.effective_acquisition_units, 12)
        self.assertEqual(descendant.closure_acquisition_units, 12)
