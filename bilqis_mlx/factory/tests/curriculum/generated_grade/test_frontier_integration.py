"""End-to-end #1320 proposal proof over the existing A09 successor machinery."""
from unittest.mock import patch

from bilqis_mlx.factory.generated_grade import synthesize_generated_grade
from bilqis_mlx.factory.generated_grade.inputs import (
    _compile_generated_grade_inputs,
)
from bilqis_mlx.factory.tests.curriculum.frontier.atlas_delta_adapter_fixtures import (
    AtlasDeltaAdapterFixture,
)


class GeneratedGradeFrontierIntegrationTests(AtlasDeltaAdapterFixture):
    def _inputs(self):
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
            return _compile_generated_grade_inputs(
                self._epoch(), self.learner, self.plan)

    def test_new_z_semantic_is_proposed_through_existing_a09_receipts(self):
        inputs = self._inputs()
        proposal = synthesize_generated_grade(
            self.snapshot, self.closure, self.current, inputs)

        self.assertIn("z.op.0", proposal.member_semantic_ids)
        self.assertEqual(proposal.a09_handoff_sha256, inputs.a09_handoff_sha256)
        self.assertEqual(proposal.a09_progress_sha256, inputs.a09_progress_sha256)
        self.assertEqual(proposal.a09_proposal_sha256, inputs.a09_proposal_sha256)
        decision = next(item for item in proposal.decisions
                        if item.semantic_id == "z.op.0")
        self.assertEqual(decision.compiled_capability_ids, ("Z.C6",))
        self.assertEqual(decision.source_anchor_ids, (self.staged.source_anchor,))
        self.assertNotIn("Z", proposal.member_semantic_ids)

    def test_reloading_same_a09_epoch_recomputes_identical_proposal(self):
        first_inputs = self._inputs()
        first = synthesize_generated_grade(
            self.snapshot, self.closure, self.current, first_inputs)
        second_inputs = self._inputs()
        second = synthesize_generated_grade(
            self.snapshot, self.closure, self.current, second_inputs)

        self.assertEqual(first_inputs.input_sha256, second_inputs.input_sha256)
        self.assertEqual(first.proposal_sha256, second.proposal_sha256)
