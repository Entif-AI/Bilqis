"""End-to-end #1320 proof over the existing A09 staged-successor fixture."""
from dataclasses import replace
import hashlib

from bilqis_mlx.factory.generated_grade import (
    AcceptedLearnerFoot,
    AcquisitionCostEvidence,
    CandidateDevelopmentEvidence,
    CostEvidenceKind,
    GeneratedGradePolicy,
    seal_generated_grade,
    synthesize_generated_grade,
)
from bilqis_mlx.factory.tests.curriculum.frontier.atlas_delta_adapter_fixtures import (
    AtlasDeltaAdapterFixture,
)
from bilqis_mlx.factory.tests.curriculum.frontier.atlas_frontier_closure_fixtures import (
    rehash,
)


def _sha(value: str) -> str:
    return hashlib.sha256(value.encode()).hexdigest()


class GeneratedGradeFrontierIntegrationTests(AtlasDeltaAdapterFixture):
    def test_new_z_semantic_is_proposed_then_sealed_by_existing_successor_lineage(self):
        snapshot = rehash(self.snapshot, grade_labels=("A", "B", "C", "Z"))
        closure = replace(
            self.closure,
            snapshot_sha256=snapshot.snapshot_sha256,
            closure_sha256="0" * 64,
        )
        closure = replace(closure, closure_sha256=closure.expected_digest())
        capability_id = self.staged.successor.transition.added_capabilities[0]
        source_anchor = self.staged.successor.source_bindings.by_capability[
            capability_id].source_anchor
        evidence = tuple(
            CandidateDevelopmentEvidence(
                semantic_id=item.semantic_id,
                compiled_capability_ids=(capability_id,),
                source_anchor_ids=(source_anchor,),
                neighborhood_id="z-frontier-" + item.semantic_id,
                coverage_factors=("source-qualified",),
                acquisition_cost=AcquisitionCostEvidence(
                    CostEvidenceKind.MEASURED,
                    "optimizer-steps-to-criterion",
                    1 if item.semantic_id == "z.op.0" else 3,
                ),
                grounding_quality=3,
                answer_modality_burden=0,
                ast_burden=0,
                entanglement=0,
                reusable_constituent_value=2,
                downstream_unlocks=2,
                minimal_contrast_value=2,
                transfer_breadth=1,
                learning_progress=1,
                fairness_age=1,
                planning_compute_units=1,
                evidence_sha256=_sha("development:" + item.semantic_id),
            )
            for item in sorted(closure.candidates, key=lambda row: row.semantic_id)
        )
        learner = AcceptedLearnerFoot(
            "e" * 64,
            0,
            self.current.release_sha256,
            snapshot.policy_epoch,
            snapshot.qualification_epoch,
            (),
            (),
            _sha("accepted-z-learner"),
        )
        policy = GeneratedGradePolicy("learner-relative-grade/v1", 1, 1)

        proposal = synthesize_generated_grade(
            snapshot, closure, self.current, learner, evidence, policy)
        definition = seal_generated_grade(
            proposal,
            self.staged.successor,
            (("z.op.0", capability_id),),
            release_lineage=(self.current, self.staged.successor),
        )

        self.assertEqual(proposal.member_semantic_ids, ("z.op.0",))
        self.assertEqual(definition.member_semantic_ids, ("z.op.0",))
        self.assertEqual(definition.members[0].capability_id, capability_id)
        self.assertEqual(
            definition.release_lineage_sha256s,
            (self.current.release_sha256, self.staged.successor.release_sha256),
        )
        self.assertNotIn("Z", proposal.member_semantic_ids)
