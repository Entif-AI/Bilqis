"""Correction transitions bind accepted evidence to one exact #1314 successor."""
from pathlib import Path
from tempfile import TemporaryDirectory
from types import SimpleNamespace
import unittest
from unittest.mock import patch

from bilqis_mlx.errors import BilqisError
from bilqis_mlx.factory.generated_grade.definition import _seal_generated_grade
from bilqis_mlx.factory.tests.curriculum.generated_grade.test_definition import (
    _single_member_fixture,
)
from bilqis_mlx.runtime.active_generated_grade_correction import (
    _issue_correction_transition_authority,
    require_correction_transition_authority,
)
from bilqis_mlx.runtime.active_generated_grade_contracts import (
    issue_active_generated_grade,
)


def _fixtures():
    release = __import__(
        "bilqis_mlx.factory.tests.curriculum.frontier.test_atlas_frontier_selection",
        fromlist=["_release"],
    )._release()
    capabilities = tuple(release.curriculum.capability_map)
    first_release, first_proposal = _single_member_fixture(
        "semantic:first", capabilities[0])
    second_release, second_proposal = _single_member_fixture(
        "semantic:second", capabilities[1])
    first_definition = _seal_generated_grade(
        first_proposal, first_release, release_lineage=(first_release,))
    second_definition = _seal_generated_grade(
        second_proposal, second_release, release_lineage=(second_release,))
    predecessor = issue_active_generated_grade(
        run_id="fixture-run", activation_generation=1,
        activation_manifest_sha256="a" * 64,
        activation_acceptance_sha256="b" * 64,
        generated_grade_id=first_definition.definition_sha256,
        proposal_sha256=first_proposal.proposal_sha256,
        definition=first_definition,
        a09_snapshot_sha256=first_proposal.snapshot_sha256,
        a09_closure_sha256=first_proposal.closure_sha256,
        a09_proposal_sha256=first_proposal.a09_proposal_sha256,
        predecessor_activation_sha256=None,
        predecessor_definition_sha256=None,
        transition_kind="INITIAL",
        transition_receipt_sha256=None,
        transition_reason=None,
    )
    return predecessor, second_proposal, second_definition


def _correction(dependency_key: str):
    return SimpleNamespace(
        event_id="correction:grade-membership",
        source_receipt_sha256="b" * 64,
        old_evidence_sha256="c" * 64,
        new_evidence_sha256="d" * 64,
        dependency=SimpleNamespace(
            kind=SimpleNamespace(value="SOURCE"),
            key=dependency_key,
        ),
        reason_code="SOURCE_CORRECTED",
    )


class CorrectionGradeTransitionAuthorityTests(unittest.TestCase):
    def test_latest_accepted_related_correction_binds_exact_successor(self):
        predecessor, proposal, definition = _fixtures()
        correction_id = "e" * 64
        correction = _correction(proposal.member_semantic_ids[0])
        with TemporaryDirectory() as directory, patch(
            "bilqis_mlx.runtime.accepted_corrections.accepted_corrections",
            return_value=((correction_id, correction),),
        ):
            authority = _issue_correction_transition_authority(
                Path(directory),
                accepted_manifest_sha256="f" * 64,
                correction_record_sha256=correction_id,
                predecessor=predecessor,
                proposal=proposal,
                definition=definition,
            )

        self.assertEqual(authority.correction_record_sha256, correction_id)
        self.assertEqual(
            authority.predecessor_activation_sha256,
            predecessor.activation_sha256,
        )
        self.assertEqual(authority.successor_proposal_sha256, proposal.proposal_sha256)
        self.assertEqual(
            authority.successor_definition_sha256,
            definition.definition_sha256,
        )
        self.assertEqual(authority.relation_kind, "DEPENDENCY")

    def test_unrelated_correction_cannot_authorize_successor(self):
        predecessor, proposal, definition = _fixtures()
        correction_id = "e" * 64
        correction = _correction("source:unrelated")
        with TemporaryDirectory() as directory, patch(
            "bilqis_mlx.runtime.accepted_corrections.accepted_corrections",
            return_value=((correction_id, correction),),
        ), self.assertRaises(BilqisError) as raised:
            _issue_correction_transition_authority(
                Path(directory),
                accepted_manifest_sha256="f" * 64,
                correction_record_sha256=correction_id,
                predecessor=predecessor,
                proposal=proposal,
                definition=definition,
            )

        self.assertEqual(
            raised.exception.context.get("reason"),
            "BAMF_ACTIVE_GENERATED_GRADE_CORRECTION_NOT_SUCCESSOR_BOUND",
        )

    def test_only_latest_accepted_correction_can_issue_transition(self):
        predecessor, proposal, definition = _fixtures()
        correction_id = "e" * 64
        correction = _correction(proposal.member_semantic_ids[0])
        later_id = "1" * 64
        later = _correction("source:later")
        with TemporaryDirectory() as directory, patch(
            "bilqis_mlx.runtime.accepted_corrections.accepted_corrections",
            return_value=((correction_id, correction), (later_id, later)),
        ), self.assertRaises(BilqisError) as raised:
            _issue_correction_transition_authority(
                Path(directory),
                accepted_manifest_sha256="f" * 64,
                correction_record_sha256=correction_id,
                predecessor=predecessor,
                proposal=proposal,
                definition=definition,
            )

        self.assertEqual(
            raised.exception.context.get("reason"),
            "BAMF_ACTIVE_GENERATED_GRADE_CORRECTION_AUTHORITY_REQUIRED",
        )

    def test_cold_authority_reproves_exact_accepted_correction_record(self):
        predecessor, proposal, definition = _fixtures()
        correction_id = "e" * 64
        correction = _correction(proposal.member_semantic_ids[0])
        manifest = "f" * 64
        with TemporaryDirectory() as directory, patch(
            "bilqis_mlx.runtime.accepted_corrections.accepted_corrections",
            return_value=((correction_id, correction),),
        ), patch(
            "bilqis_mlx.runtime.active_generated_grade_correction."
            "_historical_accepted_corrections",
            return_value=((correction_id, correction),),
        ), patch(
            "bilqis_mlx.runtime.active_generated_grade_correction."
            "_read_issued_proposal",
            create=True,
        ):
            root = Path(directory)
            from bilqis_mlx.runtime import active_generated_grade_custody as custody
            custody._persist_activation(root, predecessor)
            authority = _issue_correction_transition_authority(
                root,
                accepted_manifest_sha256=manifest,
                correction_record_sha256=correction_id,
                predecessor=predecessor,
                proposal=proposal,
                definition=definition,
            )
            active = issue_active_generated_grade(
                run_id="fixture-run", activation_generation=2,
                activation_manifest_sha256=manifest,
                activation_acceptance_sha256="1" * 64,
                generated_grade_id=definition.definition_sha256,
                proposal_sha256=proposal.proposal_sha256,
                definition=definition,
                a09_snapshot_sha256=proposal.snapshot_sha256,
                a09_closure_sha256=proposal.closure_sha256,
                a09_proposal_sha256=proposal.a09_proposal_sha256,
                predecessor_activation_sha256=predecessor.activation_sha256,
                predecessor_definition_sha256=(
                    predecessor.definition.definition_sha256),
                transition_kind="CORRECTION",
                transition_receipt_sha256=authority.authority_sha256,
                transition_reason=authority.reason_code,
            )
            with patch(
                "bilqis_mlx.runtime.active_generated_grade_correction."
                "_read_issued_proposal",
                return_value=proposal,
            ), patch(
                "bilqis_mlx.runtime.active_generated_grade_correction."
                "active_from_record",
                return_value=predecessor,
            ), patch(
                "bilqis_mlx.runtime.active_generated_grade_correction."
                "definition_from_record",
                return_value=predecessor.definition,
            ), patch(
                "bilqis_mlx.runtime.active_generated_grade_correction."
                "_historical_accepted_corrections",
                return_value=((correction_id, correction),),
            ):
                require_correction_transition_authority(root, active)

            changed = _correction(proposal.member_semantic_ids[0])
            changed.source_receipt_sha256 = "2" * 64
            with patch(
                "bilqis_mlx.runtime.active_generated_grade_correction."
                "_historical_accepted_corrections",
                return_value=((correction_id, changed),),
            ), patch(
                "bilqis_mlx.runtime.active_generated_grade_correction."
                "_read_issued_proposal",
                return_value=proposal,
            ), self.assertRaises(BilqisError) as raised:
                require_correction_transition_authority(root, active)

        self.assertEqual(
            raised.exception.context.get("reason"),
            "BAMF_ACTIVE_GENERATED_GRADE_CORRECTION_ANCESTRY_DRIFT",
        )


if __name__ == "__main__":
    unittest.main()
