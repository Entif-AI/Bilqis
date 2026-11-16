"""Cold-resume integrity for #1314 active generated grades."""
import json
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest
from unittest.mock import patch

from bilqis_mlx.errors import BilqisError
from bilqis_mlx.factory.generated_grade.definition import _seal_generated_grade
from bilqis_mlx.factory.tests.curriculum.generated_grade.test_definition import (
    _single_member_fixture,
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
    return proposal, definition


def _identity():
    return "fixture-run", 7, f"{7:064x}", f"{8:064x}"


class ActiveGeneratedGradeColdResumeTests(unittest.TestCase):
    def test_cold_resume_reseals_definition_against_accepted_1320_ancestry(self):
        from bilqis_mlx.runtime.active_generated_grade import (
            activate_accepted_generated_grade,
            read_active_generated_grade,
        )

        proposal, definition = _fixture()
        with TemporaryDirectory() as directory:
            root = Path(directory)
            with patch(
                "bilqis_mlx.runtime.active_generated_grade."
                "seal_accepted_generated_grade", return_value=definition,
            ) as seal, patch(
                "bilqis_mlx.runtime.active_generated_grade."
                "_accepted_generation_identity", return_value=_identity(),
            ), patch(
                "bilqis_mlx.runtime.active_generated_grade."
                "_activation_is_accepted_ancestor", return_value=True,
            ), patch(
                "bilqis_mlx.runtime.active_generated_grade."
                "_require_identity_still_current", return_value=None,
            ), patch(
                "bilqis_mlx.runtime.active_generated_grade_custody."
                "_read_issued_proposal", return_value=proposal,
            ), patch(
                "bilqis_mlx.runtime.active_generated_grade."
                "_read_issued_proposal", return_value=proposal,
            ), patch(
                "bilqis_mlx.runtime.active_generated_grade."
                "_reconcile_accepted_generated_grade", return_value=definition,
            ) as reconcile:
                activate_accepted_generated_grade(root, proposal)
                seal.reset_mock()
                reconcile.reset_mock()
                read_active_generated_grade(root)

        self.assertEqual(reconcile.call_count, 1)
        called_root, called_active, called_proposal = reconcile.call_args.args
        self.assertEqual(called_root, root)
        self.assertEqual(called_active.definition, definition)
        self.assertEqual(called_proposal, proposal)

    def test_cold_resume_rejects_noncanonical_activation_digest_field(self):
        from bilqis_mlx.runtime.active_generated_grade import (
            activate_accepted_generated_grade,
            read_active_generated_grade,
        )

        proposal, definition = _fixture()
        with TemporaryDirectory() as directory:
            root = Path(directory)
            with patch(
                "bilqis_mlx.runtime.active_generated_grade."
                "seal_accepted_generated_grade", return_value=definition,
            ), patch(
                "bilqis_mlx.runtime.active_generated_grade."
                "_accepted_generation_identity", return_value=_identity(),
            ), patch(
                "bilqis_mlx.runtime.active_generated_grade."
                "_activation_is_accepted_ancestor", return_value=True,
            ), patch(
                "bilqis_mlx.runtime.active_generated_grade."
                "_require_identity_still_current", return_value=None,
            ), patch(
                "bilqis_mlx.runtime.active_generated_grade_custody."
                "_read_issued_proposal", return_value=proposal,
            ), patch(
                "bilqis_mlx.runtime.active_generated_grade."
                "_read_issued_proposal", return_value=proposal,
            ), patch(
                "bilqis_mlx.runtime.active_generated_grade."
                "_reconcile_accepted_generated_grade",
                side_effect=lambda *_args, **_kwargs: None,
            ):
                active = activate_accepted_generated_grade(root, proposal)
                path = root / "generated-grades" / "activations" / (
                    active.activation_sha256 + ".json")
                record = json.loads(path.read_text(encoding="utf-8"))
                record["activation_sha256"] = "f" * 64
                path.write_text(json.dumps(record), encoding="utf-8")
                with self.assertRaises(BilqisError) as raised:
                    read_active_generated_grade(root)

        self.assertEqual(
            raised.exception.context.get("reason"),
            "BAMF_ACTIVE_GENERATED_GRADE_RECORD_INVALID",
        )

    def test_cold_resume_rejects_noncanonical_persisted_json_bytes(self):
        from bilqis_mlx.runtime.active_generated_grade import (
            activate_accepted_generated_grade,
            read_active_generated_grade,
        )

        proposal, definition = _fixture()
        with TemporaryDirectory() as directory:
            root = Path(directory)
            with patch(
                "bilqis_mlx.runtime.active_generated_grade."
                "seal_accepted_generated_grade", return_value=definition,
            ), patch(
                "bilqis_mlx.runtime.active_generated_grade."
                "_accepted_generation_identity", return_value=_identity(),
            ), patch(
                "bilqis_mlx.runtime.active_generated_grade."
                "_activation_is_accepted_ancestor", return_value=True,
            ), patch(
                "bilqis_mlx.runtime.active_generated_grade."
                "_require_identity_still_current", return_value=None,
            ), patch(
                "bilqis_mlx.runtime.active_generated_grade_custody."
                "_read_issued_proposal", return_value=proposal,
            ), patch(
                "bilqis_mlx.runtime.active_generated_grade."
                "_read_issued_proposal", return_value=proposal,
            ), patch(
                "bilqis_mlx.runtime.active_generated_grade."
                "_reconcile_accepted_generated_grade",
                side_effect=lambda *_args, **_kwargs: None,
            ):
                activate_accepted_generated_grade(root, proposal)
                pointer = root / "generated-grades" / "current.json"
                record = json.loads(pointer.read_text(encoding="utf-8"))
                pointer.write_text(json.dumps(record), encoding="utf-8")
                with self.assertRaises(BilqisError) as raised:
                    read_active_generated_grade(root)

        self.assertEqual(
            raised.exception.context.get("reason"),
            "BAMF_ACTIVE_GENERATED_GRADE_POINTER_INVALID",
        )


if __name__ == "__main__":
    unittest.main()
