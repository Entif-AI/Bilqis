"""Accepted learner-foot derivation from current retained evidence."""
import hashlib
import unittest

from bilqis_mlx.factory.atlas_delta_adapter import AtlasLearnerEvidence
from bilqis_mlx.factory.autonomy import (
    EvidenceReceipt,
    compile_autonomy_plan,
    initial_evidence_ledger,
    obligations_for_capability,
    record_evidence,
)
from bilqis_mlx.factory.generated_grade import (
    AcquisitionCostEvidence,
    CandidateDevelopmentEvidence,
    CostEvidenceKind,
    accepted_learner_foot,
)
from bilqis_mlx.factory.tests.curriculum.frontier.test_atlas_frontier_selection import (
    _release,
    _snapshot,
)


def _sha(value: str) -> str:
    return hashlib.sha256(value.encode()).hexdigest()


class AcceptedLearnerFootTests(unittest.TestCase):
    def test_only_current_evidence_projects_mastery_into_generated_grade_foot(self):
        release = _release()
        snapshot = _snapshot(release)
        plan = compile_autonomy_plan(release)
        capability_id = next(iter(release.curriculum.capability_map))
        semantic_id = snapshot.source_eligible_concept_ids[0]
        evidence = (CandidateDevelopmentEvidence(
            semantic_id=semantic_id,
            compiled_capability_ids=(capability_id,),
            source_anchor_ids=(release.source_bindings.by_capability[
                capability_id].source_anchor,),
            neighborhood_id="fixture-neighborhood",
            coverage_factors=("fixture-factor",),
            acquisition_cost=AcquisitionCostEvidence(
                CostEvidenceKind.MEASURED, "optimizer-steps-to-criterion", 3),
            grounding_quality=3, answer_modality_burden=0, ast_burden=0,
            entanglement=0, reusable_constituent_value=1, downstream_unlocks=1,
            minimal_contrast_value=1, transfer_breadth=1, learning_progress=1,
            fairness_age=1, planning_compute_units=1,
            evidence_sha256=_sha("candidate-development")),)
        ledger = initial_evidence_ledger(release, plan=plan)
        for index, obligation in enumerate(
                obligations_for_capability(release, capability_id, plan=plan)):
            ledger = record_evidence(release, ledger, EvidenceReceipt(
                obligation.obligation_id,
                f"accepted-{index}",
                "e" * 64,
                7,
                _sha(f"cohort-{index}"),
                obligation.minimum_specimens,
                True,
            ), plan=plan)

        current = accepted_learner_foot(
            snapshot, release, AtlasLearnerEvidence(ledger, "e" * 64, 7),
            plan, evidence)
        stale = accepted_learner_foot(
            snapshot, release, AtlasLearnerEvidence(ledger, "f" * 64, 8),
            plan, evidence)

        self.assertEqual(current.mastered_capability_ids, (capability_id,))
        self.assertEqual(current.mastered_semantic_ids, (semantic_id,))
        self.assertEqual(stale.mastered_capability_ids, ())
        self.assertEqual(stale.mastered_semantic_ids, ())
        self.assertEqual(current.factory_release_sha256, release.release_sha256)
        self.assertEqual(current.policy_epoch, snapshot.policy_epoch)
