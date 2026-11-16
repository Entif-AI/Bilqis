"""Historical proposal-acceptance replay for #1314 frozen grades."""
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest
from unittest.mock import patch

from bilqis_mlx.errors import BilqisError
from bilqis_mlx.factory.generated_grade.definition import _seal_generated_grade
from bilqis_mlx.factory.tests.curriculum.generated_grade.test_definition import (
    _single_member_fixture,
)
from bilqis_mlx.runtime.active_generated_grade_acceptance import (
    _issue as _issue_acceptance,
    _persist_proposal_acceptance,
    _reconcile_accepted_generated_grade,
    _require_proposal_acceptance,
    _values as _acceptance_values,
)
from bilqis_mlx.runtime.active_generated_grade_contracts import (
    issue_active_generated_grade,
)


def _fixture():
    release = __import__(
        "bilqis_mlx.factory.tests.curriculum.frontier.test_atlas_frontier_selection",
        fromlist=["_release"],
    )._release()
    capability = next(iter(release.curriculum.capability_map.values()))
    exact_release, proposal = _single_member_fixture(
        release.semantic_catalog[0], capability.capability_id)
    definition = _seal_generated_grade(
        proposal, exact_release, release_lineage=(exact_release,))
    active = issue_active_generated_grade(
        run_id="fixture-run", activation_generation=7,
        activation_manifest_sha256="a" * 64,
        activation_acceptance_sha256="b" * 64,
        generated_grade_id=definition.definition_sha256,
        proposal_sha256=proposal.proposal_sha256,
        definition=definition,
        a09_snapshot_sha256=proposal.snapshot_sha256,
        a09_closure_sha256=proposal.closure_sha256,
        a09_proposal_sha256=proposal.a09_proposal_sha256,
        predecessor_activation_sha256=None,
        predecessor_definition_sha256=None,
        transition_kind="INITIAL",
        transition_receipt_sha256=None,
        transition_reason=None,
    )
    return exact_release, proposal, definition, active


class ProposalAcceptanceReceiptTests(unittest.TestCase):
    def test_acceptance_receipt_rejects_canonical_extra_fields(self):
        _release, proposal, _definition, active = _fixture()
        record = _acceptance_values(active, proposal)
        record["unexpected"] = "canonical-but-unauthorized"
        with self.assertRaises(BilqisError) as raised:
            _issue_acceptance(**record)
        self.assertEqual(
            raised.exception.context.get("reason"),
            "BAMF_ACTIVE_GENERATED_GRADE_PROPOSAL_ACCEPTANCE_INVALID",
        )

    def test_persisted_receipt_binds_exact_activation_and_proposal(self):
        _release, proposal, _definition, active = _fixture()
        with TemporaryDirectory() as directory, patch(
            "bilqis_mlx.runtime.active_generated_grade_custody."
            "_activation_is_accepted_ancestor",
            return_value=True,
        ):
            root = Path(directory)
            _persist_proposal_acceptance(root, active, proposal)
            receipt = _require_proposal_acceptance(root, active, proposal)

        self.assertEqual(receipt.proposal_sha256, proposal.proposal_sha256)
        self.assertEqual(
            receipt.definition_sha256,
            active.definition.definition_sha256,
        )
        self.assertEqual(receipt.manifest_sha256, active.activation_manifest_sha256)

    def test_historical_replay_does_not_resynthesize_from_current_learner(self):
        release, proposal, definition, active = _fixture()
        successor = type(release)(**{
            **release.__dict__,
            "release_sha256": "f" * 64,
            "predecessor_release_sha256": release.release_sha256,
        })
        with TemporaryDirectory() as directory:
            root = Path(directory)
            with patch(
                "bilqis_mlx.runtime.active_generated_grade_custody."
                "_activation_is_accepted_ancestor",
                return_value=True,
            ):
                _persist_proposal_acceptance(root, active, proposal)
            with patch(
                "bilqis_mlx.runtime.active_generated_grade_acceptance."
                "_read_issued_proposal", return_value=proposal,
            ), patch(
                "bilqis_mlx.runtime.active_generated_grade_acceptance."
                "_proposal_bound_at_or_before_accepted_generation", return_value=True,
            ) as historical_binding, patch(
                "bilqis_mlx.runtime.active_generated_grade_acceptance."
                "_accepted_release_lineage", return_value=(release, successor),
            ), patch(
                "bilqis_mlx.runtime.active_generated_grade_custody."
                "_activation_is_accepted_ancestor", return_value=True,
            ):
                _reconcile_accepted_generated_grade(root, active, proposal)

        self.assertEqual(active.definition, definition)
        historical_binding.assert_called_once_with(
            root,
            proposal,
            run_id=active.run_id,
            generation=active.activation_generation,
            manifest_sha256=active.activation_manifest_sha256,
            acceptance_sha256=active.activation_acceptance_sha256,
        )

    def test_historical_replay_rejects_proposal_not_bound_at_activation(self):
        release, proposal, _definition, active = _fixture()
        with TemporaryDirectory() as directory:
            root = Path(directory)
            with patch(
                "bilqis_mlx.runtime.active_generated_grade_custody."
                "_activation_is_accepted_ancestor", return_value=True,
            ):
                _persist_proposal_acceptance(root, active, proposal)
            with patch(
                "bilqis_mlx.runtime.active_generated_grade_acceptance."
                "_read_issued_proposal", return_value=proposal,
            ), patch(
                "bilqis_mlx.runtime.active_generated_grade_acceptance."
                "_proposal_bound_at_or_before_accepted_generation", return_value=False,
            ), patch(
                "bilqis_mlx.runtime.active_generated_grade_acceptance."
                "_seal_generated_grade",
            ) as seal, patch(
                "bilqis_mlx.runtime.active_generated_grade_acceptance."
                "_accepted_release_lineage", return_value=(release,),
            ), patch(
                "bilqis_mlx.runtime.active_generated_grade_custody."
                "_activation_is_accepted_ancestor", return_value=True,
            ), self.assertRaises(BilqisError) as raised:
                _reconcile_accepted_generated_grade(root, active, proposal)

        self.assertEqual(
            raised.exception.context.get("reason"),
            "BAMF_GENERATED_GRADE_ACCEPTED_PROPOSAL_MISMATCH",
        )
        seal.assert_not_called()

    def test_missing_acceptance_receipt_fails_closed(self):
        _release, proposal, _definition, active = _fixture()
        with TemporaryDirectory() as directory, patch(
            "bilqis_mlx.runtime.active_generated_grade_custody."
            "_activation_is_accepted_ancestor", return_value=True,
        ), self.assertRaises(BilqisError) as raised:
            _require_proposal_acceptance(Path(directory), active, proposal)

        self.assertEqual(
            raised.exception.context.get("reason"),
            "BAMF_ACTIVE_GENERATED_GRADE_PROPOSAL_ACCEPTANCE_INVALID",
        )


if __name__ == "__main__":
    unittest.main()
