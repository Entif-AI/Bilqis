"""#1320 sealing is subordinate to accepted C07/B13 custody."""
from dataclasses import replace
from pathlib import Path
import unittest
from unittest.mock import patch

from bilqis_mlx.errors import BilqisError
from bilqis_mlx.factory.tests.curriculum.generated_grade.test_definition import (
    _single_member_fixture,
)
from bilqis_mlx.runtime.generated_grade import seal_accepted_generated_grade


class AcceptedGeneratedGradeDefinitionTests(unittest.TestCase):
    def test_seal_resolves_release_from_accepted_runtime_authority(self):
        release = __import__(
            "bilqis_mlx.factory.tests.curriculum.frontier.test_atlas_frontier_selection",
            fromlist=["_release"],
        )._release()
        capability = next(iter(release.curriculum.capability_map.values()))
        semantic_id = release.semantic_catalog[0]
        exact_release, proposal = _single_member_fixture(
            semantic_id, capability.capability_id)

        with patch(
            "bilqis_mlx.runtime.generated_grade."
            "propose_accepted_generated_grade",
            return_value=proposal,
        ) as accepted_proposal, patch(
            "bilqis_mlx.runtime.generated_grade."
            "read_accepted_atlas_factory_release",
            return_value=exact_release,
        ) as accepted_reader:
            definition = seal_accepted_generated_grade(Path("/accepted-run"), proposal)

        accepted_proposal.assert_called_once()
        accepted_reader.assert_called_once_with(Path("/accepted-run"))
        self.assertEqual(definition.adopted_release_sha256, exact_release.release_sha256)
        self.assertEqual(definition.member_semantic_ids, (semantic_id,))

    def test_seal_rejects_digest_valid_proposal_not_recomputed_from_accepted_state(self):
        release = __import__(
            "bilqis_mlx.factory.tests.curriculum.frontier.test_atlas_frontier_selection",
            fromlist=["_release"],
        )._release()
        capability = next(iter(release.curriculum.capability_map.values()))
        semantic_id = release.semantic_catalog[0]
        exact_release, accepted = _single_member_fixture(
            semantic_id, capability.capability_id)
        forged_draft = replace(
            accepted, a09_status="CALLER_FORGED", proposal_sha256="0" * 64)
        forged = replace(
            forged_draft, proposal_sha256=forged_draft.expected_digest())

        with patch(
            "bilqis_mlx.runtime.generated_grade."
            "propose_accepted_generated_grade",
            return_value=accepted,
        ), self.assertRaises(BilqisError) as raised:
            seal_accepted_generated_grade(Path("/accepted-run"), forged)

        self.assertEqual(
            raised.exception.context.get("reason"),
            "BAMF_GENERATED_GRADE_ACCEPTED_PROPOSAL_MISMATCH",
        )

    def test_public_seal_has_no_staged_release_argument(self):
        import inspect
        self.assertEqual(
            tuple(inspect.signature(seal_accepted_generated_grade).parameters),
            ("run_dir", "proposal"),
        )
