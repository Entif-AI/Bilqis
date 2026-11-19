"""#1314 frozen active generated-grade custody."""
import json
import unittest
from dataclasses import replace
from pathlib import Path
from tempfile import TemporaryDirectory
from types import SimpleNamespace
from unittest.mock import patch

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

    def _bootstrap_active_grade(self, proposal, definition):
        from bilqis_mlx.runtime.active_generated_grade_contracts import (
            issue_active_generated_grade,
        )
        return issue_active_generated_grade(
            run_id="fixture-run",
            activation_generation=0,
            activation_manifest_sha256="1" * 64,
            activation_acceptance_sha256="2" * 64,
            generated_grade_id=definition.definition_sha256,
            definition=definition,
            proposal_sha256=proposal.proposal_sha256,
            a09_snapshot_sha256="3" * 64,
            a09_closure_sha256="4" * 64,
            a09_proposal_sha256=None,
            predecessor_activation_sha256=None,
            predecessor_definition_sha256=None,
            transition_kind="BOOTSTRAP",
            transition_receipt_sha256=proposal.proposal_sha256,
            transition_reason="DATA_DEFINED_INITIAL_GRADE_BOOTSTRAP",
        )

    def test_initial_activation_round_trips_exact_definition_from_durable_custody(self):
        from bilqis_mlx.runtime.active_generated_grade import (
            _read_bound_active_generated_grade,
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
            ), patch(
                "bilqis_mlx.runtime.active_generated_grade."
                "_read_issued_proposal",
                return_value=proposal,
            ), patch(
                "bilqis_mlx.runtime.active_generated_grade."
                "_reconcile_accepted_generated_grade",
                side_effect=lambda *_args, **_kwargs: None,
            ):
                activated = activate_accepted_generated_grade(root, proposal)
                cold = read_active_generated_grade(root)
                self.assertIsInstance(cold, ActiveGeneratedGrade)
                with patch(
                    "bilqis_mlx.runtime.bamf_bundle.currentness_transaction."
                    "require_accepted_currentness_step",
                    return_value=object(),
                ), patch(
                    "bilqis_mlx.runtime.active_generated_grade."
                    "_activation_is_accepted_ancestor",
                    side_effect=AssertionError("hot active-grade read rescanned B13 ancestry"),
                ):
                    bound = _read_bound_active_generated_grade(
                        root,
                        expected_activation_sha256=activated.activation_sha256,
                        expected_definition_sha256=(
                            activated.definition.definition_sha256),
                        currentness_step=object(), currentness_transaction=object(),
                        parent=object(),
                    )

        self.assertEqual(cold, activated)
        self.assertEqual(bound, activated)
        self.assertEqual(cold.definition, definition)
        self.assertEqual(cold.transition_kind, "INITIAL")
        self.assertIsNone(cold.predecessor_activation_sha256)
        self.assertIsNone(cold.transition_receipt_sha256)

    def test_bootstrap_hot_currentness_reuses_frozen_grade_and_rejects_file_drift(self):
        from bilqis_mlx.runtime.active_generated_grade import (
            _bind_active_generated_grade_currentness,
            _read_bound_active_generated_grade,
        )
        proposal, definition = self._fixture()
        active = self._bootstrap_active_grade(proposal, definition)
        with TemporaryDirectory() as directory:
            root = Path(directory)
            paths = (
                root / "generated-grades/current.json",
                root / "generated-grades/definitions"
                    / f"{definition.definition_sha256}.json",
                root / "generated-grades/activations"
                    / f"{active.activation_sha256}.json",
                root / "generated-grade-proposals/initial-bootstrap"
                    / f"{proposal.proposal_sha256}.json",
                root / "factory-releases"
                    / f"{definition.adopted_release_sha256}.json",
            )
            for index, path in enumerate(paths):
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_text(f"fixture-{index}\n", encoding="utf-8")

            with patch(
                "bilqis_mlx.runtime.active_generated_grade."
                "read_active_generated_grade",
                return_value=active,
            ):
                witness = _bind_active_generated_grade_currentness(root, active)
            with patch(
                "bilqis_mlx.runtime.bamf_bundle.currentness_transaction."
                "require_accepted_currentness_step",
                return_value=object(),
            ), patch(
                "bilqis_mlx.runtime.active_generated_grade._custody._read_stored_active",
                side_effect=AssertionError("hot bootstrap reparsed active custody"),
            ), patch(
                "bilqis_mlx.runtime.active_generated_grade._require_active_transition_current",
                side_effect=AssertionError("hot bootstrap repeated deep transition proof"),
            ):
                current = _read_bound_active_generated_grade(
                    root,
                    expected_activation_sha256=active.activation_sha256,
                    expected_definition_sha256=definition.definition_sha256,
                    currentness_step=object(),
                    currentness_transaction=object(),
                    parent=object(),
                    active_currentness=witness,
                )
            self.assertIs(current, active)

            paths[3].write_text("tampered\n", encoding="utf-8")
            with patch(
                "bilqis_mlx.runtime.bamf_bundle.currentness_transaction."
                "require_accepted_currentness_step",
                return_value=object(),
            ), self.assertRaises(BilqisError) as raised:
                _read_bound_active_generated_grade(
                    root,
                    expected_activation_sha256=active.activation_sha256,
                    expected_definition_sha256=definition.definition_sha256,
                    currentness_step=object(),
                    currentness_transaction=object(),
                    parent=object(),
                    active_currentness=witness,
                )
            self.assertEqual(
                raised.exception.context.get("reason"),
                "BAMF_ACTIVE_GENERATED_GRADE_CURRENTNESS_DRIFT",
            )

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
                "_read_issued_proposal",
                side_effect=lambda _root, digest: (
                    proposal if digest == proposal.proposal_sha256
                    else other_proposal),
            ), patch(
                "bilqis_mlx.runtime.active_generated_grade."
                "seal_accepted_generated_grade",
                side_effect=lambda _root, issued_proposal, **_kwargs: (
                    definition if issued_proposal.proposal_sha256
                    == proposal.proposal_sha256 else other_definition),
            ), patch(
                "bilqis_mlx.runtime.active_generated_grade."
                "_reconcile_accepted_generated_grade",
                side_effect=lambda *_args, **_kwargs: None,
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
        authority_digest = "d" * 64
        correction_authority = SimpleNamespace(
            authority_sha256=authority_digest,
            correction_record_sha256=correction_id,
            reason_code="SOURCE_CORRECTED",
        )
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
                "_read_issued_proposal",
                side_effect=lambda _root, digest: (
                    proposal if digest == proposal.proposal_sha256
                    else other_proposal),
            ), patch(
                "bilqis_mlx.runtime.active_generated_grade."
                "seal_accepted_generated_grade",
                side_effect=lambda _root, issued_proposal, **_kwargs: (
                    definition if issued_proposal.proposal_sha256
                    == proposal.proposal_sha256 else other_definition),
            ), patch(
                "bilqis_mlx.runtime.active_generated_grade."
                "_reconcile_accepted_generated_grade",
                side_effect=lambda *_args, **_kwargs: None,
            ), patch(
                "bilqis_mlx.runtime.active_generated_grade."
                "_issue_correction_transition_authority",
                return_value=correction_authority,
            ), patch(
                "bilqis_mlx.runtime.active_generated_grade."
                "require_correction_transition_authority",
                return_value=correction_authority,
            ):
                first = activate_accepted_generated_grade(root, proposal)
                successor = activate_corrected_generated_grade(
                    root, other_proposal, correction_event_id=correction_id)
                retry = activate_corrected_generated_grade(
                    root, other_proposal, correction_event_id=correction_id)
                cold = read_active_generated_grade(root)

        self.assertEqual(cold, successor)
        self.assertEqual(retry, successor)
        self.assertEqual(
            successor.predecessor_activation_sha256, first.activation_sha256)
        self.assertEqual(
            successor.predecessor_definition_sha256,
            first.definition.definition_sha256)
        self.assertEqual(successor.transition_kind, "CORRECTION")
        self.assertEqual(successor.transition_receipt_sha256, authority_digest)
        self.assertEqual(successor.transition_reason, "SOURCE_CORRECTED")


if __name__ == "__main__":
    unittest.main()
