"""#1314 frozen active generated-grade custody."""
from dataclasses import replace
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import patch
import unittest

from bilqis_mlx.errors import BilqisError
from bilqis_mlx.factory.generated_grade.definition import _seal_generated_grade
from bilqis_mlx.factory.tests.curriculum.generated_grade.test_definition import (
    _single_member_fixture,
)
from bilqis_mlx.runtime.active_generated_grade_contracts import ActiveGeneratedGrade


class ActiveGeneratedGradeTests(unittest.TestCase):
    def _fixture(self):
        release = __import__(
            "bilqis_mlx.factory.tests.curriculum.frontier.test_atlas_frontier_selection",
            fromlist=["_release"],
        )._release()
        capability = next(iter(release.curriculum.capability_map.values()))
        exact_release, proposal = _single_member_fixture(
            release.semantic_catalog[0], capability.capability_id)
        definition = _seal_generated_grade(
            proposal, exact_release, release_lineage=(exact_release,))
        return proposal, definition

    def _identity(self, generation=7):
        return (
            "fixture-run",
            generation,
            f"{generation:064x}",
            f"{generation + 1:064x}",
        )

    def _successor_definition(self, definition, proposal):
        draft = replace(
            definition,
            proposal_sha256=proposal.proposal_sha256,
            definition_sha256="0" * 64,
        )
        return replace(draft, definition_sha256=draft.expected_digest())

    def test_initial_activation_round_trips_exact_definition_from_durable_custody(self):
        from bilqis_mlx.runtime.active_generated_grade import (
            activate_accepted_generated_grade,
            read_active_generated_grade,
        )

        proposal, definition = self._fixture()
        with TemporaryDirectory() as directory:
            root = Path(directory)
            with patch(
                "bilqis_mlx.runtime.active_generated_grade."
                "seal_accepted_generated_grade",
                return_value=definition,
            ), patch(
                "bilqis_mlx.runtime.active_generated_grade."
                "_accepted_generation_identity",
                return_value=self._identity(),
            ), patch(
                "bilqis_mlx.runtime.active_generated_grade."
                "_activation_is_accepted_ancestor",
                return_value=True,
            ), patch(
                "bilqis_mlx.runtime.active_generated_grade."
                "_require_identity_still_current",
                return_value=None,
            ), patch(
                "bilqis_mlx.runtime.active_generated_grade_custody."
                "_read_issued_proposal",
                return_value=proposal,
            ):
                activated = activate_accepted_generated_grade(root, proposal)
                cold = read_active_generated_grade(root)
                self.assertIsInstance(cold, ActiveGeneratedGrade)

        self.assertEqual(cold, activated)
        self.assertEqual(cold.definition, definition)
        self.assertEqual(cold.transition_kind, "INITIAL")
        self.assertIsNone(cold.predecessor_activation_sha256)
        self.assertIsNone(cold.transition_receipt_sha256)

    def test_distinct_definition_cannot_replace_active_grade_without_transition_authority(self):
        from bilqis_mlx.runtime.active_generated_grade import (
            activate_accepted_generated_grade,
        )

        proposal, definition = self._fixture()
        _other_release, other_proposal = _single_member_fixture(
            "skos:future-z", "Z.FUTURE")
        other_definition = self._successor_definition(
            definition, other_proposal)
        with TemporaryDirectory() as directory:
            root = Path(directory)
            with patch(
                "bilqis_mlx.runtime.active_generated_grade."
                "_accepted_generation_identity",
                return_value=self._identity(),
            ), patch(
                "bilqis_mlx.runtime.active_generated_grade."
                "_activation_is_accepted_ancestor",
                return_value=True,
            ), patch(
                "bilqis_mlx.runtime.active_generated_grade."
                "_require_identity_still_current",
                return_value=None,
            ), patch(
                "bilqis_mlx.runtime.active_generated_grade_custody."
                "_read_issued_proposal",
                side_effect=lambda _root, digest: (
                    proposal if digest == proposal.proposal_sha256
                    else other_proposal),
            ), patch(
                "bilqis_mlx.runtime.active_generated_grade."
                "seal_accepted_generated_grade",
                side_effect=(definition, other_definition),
            ):
                activate_accepted_generated_grade(root, proposal)
                with self.assertRaises(BilqisError) as raised:
                    activate_accepted_generated_grade(root, other_proposal)

        self.assertEqual(
            raised.exception.context.get("reason"),
            "BAMF_ACTIVE_GENERATED_GRADE_TRANSITION_AUTHORITY_REQUIRED",
        )

    def test_accepted_correction_creates_successor_activation_without_mutating_predecessor(self):
        from bilqis_mlx.runtime.active_generated_grade import (
            activate_accepted_generated_grade,
            activate_corrected_generated_grade,
            read_active_generated_grade,
        )

        proposal, definition = self._fixture()
        _other_release, other_proposal = _single_member_fixture(
            "skos:future-z", "Z.FUTURE")
        other_definition = self._successor_definition(
            definition, other_proposal)
        correction_id = "c" * 64
        correction = unittest.mock.MagicMock(reason_code="SOURCE_CORRECTED")
        with TemporaryDirectory() as directory:
            root = Path(directory)
            with patch(
                "bilqis_mlx.runtime.active_generated_grade."
                "_accepted_generation_identity",
                return_value=self._identity(),
            ), patch(
                "bilqis_mlx.runtime.active_generated_grade."
                "_activation_is_accepted_ancestor",
                return_value=True,
            ), patch(
                "bilqis_mlx.runtime.active_generated_grade."
                "_require_identity_still_current",
                return_value=None,
            ), patch(
                "bilqis_mlx.runtime.active_generated_grade_custody."
                "_read_issued_proposal",
                side_effect=lambda _root, digest: (
                    proposal if digest == proposal.proposal_sha256
                    else other_proposal),
            ), patch(
                "bilqis_mlx.runtime.active_generated_grade."
                "seal_accepted_generated_grade",
                side_effect=(definition, other_definition),
            ), patch(
                "bilqis_mlx.runtime.active_generated_grade."
                "_accepted_correction_by_id",
                return_value=correction,
            ):
                first = activate_accepted_generated_grade(root, proposal)
                successor = activate_corrected_generated_grade(
                    root, other_proposal, correction_event_id=correction_id)
                cold = read_active_generated_grade(root)

        self.assertEqual(cold, successor)
        self.assertEqual(
            successor.predecessor_activation_sha256, first.activation_sha256)
        self.assertEqual(
            successor.predecessor_definition_sha256,
            first.definition.definition_sha256)
        self.assertEqual(successor.transition_kind, "CORRECTION")
        self.assertEqual(successor.transition_receipt_sha256, correction_id)
        self.assertEqual(successor.transition_reason, "SOURCE_CORRECTED")


if __name__ == "__main__":
    unittest.main()
