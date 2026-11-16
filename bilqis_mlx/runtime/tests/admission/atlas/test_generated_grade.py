"""#1320 sealing is subordinate to accepted C07/B13 custody."""
from dataclasses import replace
from pathlib import Path
from tempfile import TemporaryDirectory
from types import SimpleNamespace
import unittest
from unittest.mock import patch

from bilqis_mlx.errors import BilqisError
from bilqis_mlx.factory.tests.curriculum.generated_grade.test_definition import (
    _single_member_fixture,
)
from bilqis_mlx.runtime.generated_grade import (
    _issue_generated_grade_admission_authority,
    _persist_issued_proposal,
    _read_issued_proposal,
    seal_accepted_generated_grade,
)


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
            "bilqis_mlx.runtime.generated_grade._read_issued_proposal",
            return_value=proposal,
        ) as issued_reader, patch(
            "bilqis_mlx.runtime.generated_grade."
            "read_accepted_atlas_factory_release",
            return_value=exact_release,
        ) as accepted_reader, patch(
            "bilqis_mlx.runtime.generated_grade._recompute_current_accepted_proposal",
            return_value=proposal,
        ):
            definition = seal_accepted_generated_grade(Path("/accepted-run"), proposal)

        issued_reader.assert_called_once_with(
            Path("/accepted-run"), proposal.proposal_sha256)
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
            "bilqis_mlx.runtime.generated_grade._read_issued_proposal",
            return_value=accepted,
        ), self.assertRaises(BilqisError) as raised:
            seal_accepted_generated_grade(Path("/accepted-run"), forged)

        self.assertEqual(
            raised.exception.context.get("reason"),
            "BAMF_GENERATED_GRADE_ACCEPTED_PROPOSAL_MISMATCH",
        )

    def test_self_digested_forged_sidecar_is_not_accepted_authority(self):
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
            "bilqis_mlx.runtime.generated_grade._read_issued_proposal",
            return_value=forged,
        ), patch(
            "bilqis_mlx.runtime.generated_grade._accepted_release_lineage",
            return_value=(exact_release,),
        ), patch(
            "bilqis_mlx.runtime.generated_grade._recompute_current_accepted_proposal",
            return_value=accepted,
        ), self.assertRaises(BilqisError):
            seal_accepted_generated_grade(Path("/accepted-run"), forged)

    def test_issued_proposal_survives_successor_adoption_before_seal(self):
        release = __import__(
            "bilqis_mlx.factory.tests.curriculum.frontier.test_atlas_frontier_selection",
            fromlist=["_release"],
        )._release()
        capability = next(iter(release.curriculum.capability_map.values()))
        proposal_release, proposal = _single_member_fixture(
            release.semantic_catalog[0], capability.capability_id)
        successor = object()
        sentinel = object()
        with patch(
            "bilqis_mlx.runtime.generated_grade._read_issued_proposal",
            return_value=proposal,
        ), patch(
            "bilqis_mlx.runtime.generated_grade._accepted_release_lineage",
            return_value=(proposal_release, successor),
        ), patch(
            "bilqis_mlx.runtime.generated_grade._proposal_bound_in_accepted_ancestry",
            return_value=True,
        ), patch(
            "bilqis_mlx.runtime.generated_grade._seal_generated_grade",
            return_value=sentinel,
        ) as seal:
            result = seal_accepted_generated_grade(Path("/accepted-run"), proposal)
        self.assertIs(result, sentinel)
        seal.assert_called_once_with(
            proposal, successor, release_lineage=(proposal_release, successor))

    def test_issued_proposal_receipt_round_trips_from_run_custody(self):
        release = __import__(
            "bilqis_mlx.factory.tests.curriculum.frontier.test_atlas_frontier_selection",
            fromlist=["_release"],
        )._release()
        capability = next(iter(release.curriculum.capability_map.values()))
        _exact_release, proposal = _single_member_fixture(
            release.semantic_catalog[0], capability.capability_id)
        with TemporaryDirectory() as directory:
            run_dir = Path(directory)
            _persist_issued_proposal(run_dir, proposal)
            self.assertEqual(
                _read_issued_proposal(run_dir, proposal.proposal_sha256), proposal)

    def test_admission_authority_persists_phase_one_proposal_before_binding(self):
        release = __import__(
            "bilqis_mlx.factory.tests.curriculum.frontier.test_atlas_frontier_selection",
            fromlist=["_release"],
        )._release()
        capability = next(iter(release.curriculum.capability_map.values()))
        _exact_release, proposal = _single_member_fixture(
            release.semantic_catalog[0], capability.capability_id)
        handoff = SimpleNamespace(
            receipt=SimpleNamespace(
                predecessor_release=SimpleNamespace(
                    release_sha256=proposal.current_release_sha256)),
            proposal=SimpleNamespace(
                proposal_sha256=proposal.a09_proposal_sha256),
        )
        with TemporaryDirectory() as directory:
            run_dir = Path(directory)
            supervisor = SimpleNamespace(run_dir=run_dir)
            with patch(
                "bilqis_mlx.runtime.generated_grade._recompute_accepted_generated_grade",
                return_value=proposal,
            ):
                _issue_generated_grade_admission_authority(supervisor, handoff)

            self.assertEqual(
                _read_issued_proposal(run_dir, proposal.proposal_sha256),
                proposal,
            )

    def test_public_seal_has_no_staged_release_argument(self):
        import inspect
        self.assertEqual(
            tuple(inspect.signature(seal_accepted_generated_grade).parameters),
            ("run_dir", "proposal"),
        )
