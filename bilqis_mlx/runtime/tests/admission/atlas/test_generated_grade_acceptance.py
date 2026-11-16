"""#1320 issued-proposal custody and historical acceptance ancestry."""
from pathlib import Path
from tempfile import TemporaryDirectory
from types import SimpleNamespace
import unittest
from unittest.mock import patch

from bilqis_mlx.factory.tests.curriculum.generated_grade.test_definition import (
    _single_member_fixture,
)
from bilqis_mlx.runtime.generated_grade import _persist_issued_proposal
from bilqis_mlx.runtime.generated_grade_acceptance import (
    _binding_accepts_proposal,
    _proposal_bound_at_or_before_accepted_generation,
    _read_issued_proposal,
)


def _proposal():
    release = __import__(
        "bilqis_mlx.factory.tests.curriculum.frontier.test_atlas_frontier_selection",
        fromlist=["_release"],
    )._release()
    capability = next(iter(release.curriculum.capability_map.values()))
    _exact_release, proposal = _single_member_fixture(
        release.semantic_catalog[0], capability.capability_id)
    return proposal


class GeneratedGradeAcceptanceTests(unittest.TestCase):
    def test_issued_proposal_round_trips_from_run_custody(self):
        proposal = _proposal()
        with TemporaryDirectory() as directory:
            run_dir = Path(directory)
            _persist_issued_proposal(run_dir, proposal)
            self.assertEqual(
                _read_issued_proposal(run_dir, proposal.proposal_sha256), proposal)

    def test_issued_proposal_fsyncs_new_custody_directory_and_entry(self):
        proposal = _proposal()
        with TemporaryDirectory() as directory:
            run_dir = Path(directory)
            with patch(
                "bilqis_mlx.runtime.generated_grade._fsync_directory",
            ) as directory_sync:
                _persist_issued_proposal(run_dir, proposal)
            proposal_root = run_dir / "generated-grade-proposals"
            self.assertGreaterEqual(
                directory_sync.call_args_list.count(
                    unittest.mock.call(proposal_root)), 2)
            directory_sync.assert_any_call(run_dir)

    def test_non_c07_accepted_binding_is_not_proposal_authority(self):
        self.assertFalse(_binding_accepts_proposal(object(), _proposal()))

    def test_historical_binding_search_is_bounded_by_activation_ancestry(self):
        proposal = _proposal()
        activation = SimpleNamespace(
            run_id="fixture-run", generation=9,
            parent_manifest_sha256="parent-manifest")
        parent = SimpleNamespace(
            run_id="fixture-run", generation=8,
            parent_manifest_sha256="older-manifest")
        with patch(
            "bilqis_mlx.runtime.bamf_bundle.codec.load_bamf_bundle",
            side_effect=[activation, parent],
        ) as load, patch(
            "bilqis_mlx.runtime.bamf_bundle.feature.acceptance."
            "accepted_binding_for_manifest",
            side_effect=[object(), object()],
        ) as accepted_binding, patch(
            "bilqis_mlx.runtime.bamf_bundle.feature.acceptance."
            "parent_acceptance_anchor_from_manifest",
            return_value="parent-acceptance",
        ), patch(
            "bilqis_mlx.runtime.generated_grade_acceptance._binding_accepts_proposal",
            side_effect=[False, True],
        ):
            authorized = _proposal_bound_at_or_before_accepted_generation(
                Path("/accepted-run"), proposal,
                run_id="fixture-run", generation=9,
                manifest_sha256="activation-manifest",
                acceptance_sha256="activation-acceptance",
            )
        self.assertTrue(authorized)
        self.assertEqual(load.call_args_list[0].args[0], Path(
            "/accepted-run/bamf-bundles/activation-manifest"))
        self.assertEqual(load.call_args_list[1].args[0], Path(
            "/accepted-run/bamf-bundles/parent-manifest"))
        self.assertEqual(
            accepted_binding.call_args_list[0].args[1], "activation-manifest")
        self.assertEqual(
            accepted_binding.call_args_list[1].args[1], "parent-manifest")


if __name__ == "__main__":
    unittest.main()
