"""Learner-relative authority stays split between A09 semantic credit and evidence."""
from bilqis_mlx.factory.atlas_frontier import AtlasCoverageEpoch
from bilqis_mlx.factory.atlas_delta_adapter import _issue_accepted_obligation_credit
from bilqis_mlx.factory.atlas_frontier_progress_validation import current_obligations
from bilqis_mlx.factory.generated_grade.inputs import _a09_baselines
from bilqis_mlx.factory.tests.curriculum.frontier.atlas_delta_adapter_fixtures import (
    AtlasDeltaAdapterFixture,
)


class GeneratedGradeLearnerAuthorityTests(AtlasDeltaAdapterFixture):
    def test_semantic_baseline_comes_only_from_authenticated_a09_credit(self):
        current = current_obligations(self.closure)
        semantic_id = sorted(current)[0]
        credit = _issue_accepted_obligation_credit(
            self.current.release_sha256,
            "f" * 64,
            ((semantic_id, current[semantic_id]),),
        )
        epoch = AtlasCoverageEpoch(
            self.snapshot, self.closure, self.frontier, self.current,
            (self.staged,), accepted_credit=credit)

        self.assertEqual(_a09_baselines(epoch), (semantic_id,))
        self.assertEqual(_a09_baselines(self._epoch()), ())
