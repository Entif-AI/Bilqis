"""#1314 successor-transition and non-churn authority tests."""
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


def _fixture(semantic_id="skos:fixture", capability_id="F.FIXTURE"):
    release = __import__(
        "bilqis_mlx.factory.tests.curriculum.frontier.test_atlas_frontier_selection",
        fromlist=["_release"],
    )._release()
    if semantic_id == "skos:fixture":
        semantic_id = release.semantic_catalog[0]
        capability_id = next(iter(release.curriculum.capability_map)).strip()
    exact_release, proposal = _single_member_fixture(semantic_id, capability_id)
    definition = _seal_generated_grade(
        proposal, exact_release, release_lineage=(exact_release,))
    return proposal, definition


def _successor_definition(definition, proposal):
    draft = replace(
        definition,
        proposal_sha256=proposal.proposal_sha256,
        learner_foot_sha256=proposal.learner_foot_sha256,
        definition_sha256="0" * 64,
    )
    return replace(draft, definition_sha256=draft.expected_digest())


class ActiveGeneratedGradeTransitionTests(unittest.TestCase):
    def _identity(self, generation=11):
        return (
            "fixture-run", generation,
            f"{generation:064x}", f"{generation + 1:064x}")

    def _patches(self, proposal, definition, *, second=None, second_definition=None):
        issued = {proposal.proposal_sha256: proposal}
        if second is not None:
            issued[second.proposal_sha256] = second
        definitions = [definition]
        if second_definition is not None:
            definitions.append(second_definition)
        return (
            patch(
                "bilqis_mlx.runtime.active_generated_grade."
                "_accepted_generation_identity",
                return_value=self._identity()),
            patch(
                "bilqis_mlx.runtime.active_generated_grade."
                "_activation_is_accepted_ancestor",
                return_value=True),
            patch(
                "bilqis_mlx.runtime.active_generated_grade."
                "_require_identity_still_current",
                return_value=None),
            patch(
                "bilqis_mlx.runtime.active_generated_grade_custody."
                "_read_issued_proposal",
                side_effect=lambda _root, digest: issued[digest]),
            patch(
                "bilqis_mlx.runtime.active_generated_grade."
                "_read_issued_proposal",
                side_effect=lambda _root, digest: issued[digest]),
            patch(
                "bilqis_mlx.runtime.active_generated_grade."
                "seal_accepted_generated_grade",
                side_effect=lambda _root, issued_proposal, **_kwargs: (
                    definition if issued_proposal.proposal_sha256
                    == proposal.proposal_sha256 else second_definition)),
            patch(
                "bilqis_mlx.runtime.active_generated_grade."
                "_reconcile_accepted_generated_grade",
                side_effect=lambda _root, _proposal, stored: stored),
        )

    def test_c07_adoption_alone_cannot_replace_frozen_active_grade(self):
        from bilqis_mlx.runtime.active_generated_grade import (
            ensure_active_generated_grade,
        )

        proposal, definition = _fixture()
        with TemporaryDirectory() as directory:
            root = Path(directory)
            patches = self._patches(proposal, definition)
            with patches[0], patches[1], patches[2], patches[3], patches[4], patches[5], patches[6], patch(
                "bilqis_mlx.runtime.active_generated_grade_custody."
                "_accepted_bound_generated_grade_proposal",
                return_value=proposal,
            ):
                first = ensure_active_generated_grade(root)
                with patch(
                    "bilqis_mlx.runtime.active_generated_grade_custody."
                    "_accepted_bound_generated_grade_proposal",
                    side_effect=AssertionError("active grade must not be resynthesized"),
                ):
                    again = ensure_active_generated_grade(root)
        self.assertEqual(again, first)

    def test_missing_pointer_with_activation_history_fails_closed(self):
        from bilqis_mlx.runtime.active_generated_grade import (
            activate_accepted_generated_grade,
            ensure_active_generated_grade,
        )

        proposal, definition = _fixture()
        with TemporaryDirectory() as directory:
            root = Path(directory)
            patches = self._patches(proposal, definition)
            with patches[0], patches[1], patches[2], patches[3], patches[4], patches[5], patches[6], patch(
                "bilqis_mlx.runtime.active_generated_grade_custody."
                "_accepted_bound_generated_grade_proposal",
                return_value=proposal,
            ):
                activate_accepted_generated_grade(root, proposal)
                (root / "generated-grades" / "current.json").unlink()
                with self.assertRaises(BilqisError) as raised:
                    ensure_active_generated_grade(root)

        self.assertEqual(
            raised.exception.context.get("reason"),
            "BAMF_ACTIVE_GENERATED_GRADE_POINTER_MISSING",
        )

    def test_first_publication_recovers_exact_orphan_after_pointer_write_crash(self):
        from bilqis_mlx.runtime.active_generated_grade import (
            activate_accepted_generated_grade,
        )
        from bilqis_mlx.runtime import active_generated_grade_custody as custody

        proposal, definition = _fixture()
        with TemporaryDirectory() as directory:
            root = Path(directory)
            patches = self._patches(proposal, definition)
            original = custody._durable_json

            def crash_before_pointer(path, payload, **kwargs):
                if Path(path).name == "current.json":
                    raise RuntimeError("simulated pointer-write crash")
                return original(path, payload, **kwargs)

            with patches[0], patches[1], patches[2], patches[3], patches[4], patches[5], patches[6]:
                with patch.object(custody, "_durable_json", side_effect=crash_before_pointer):
                    with self.assertRaisesRegex(RuntimeError, "pointer-write crash"):
                        activate_accepted_generated_grade(root, proposal)

                recovered = activate_accepted_generated_grade(root, proposal)

        self.assertEqual(recovered.definition, definition)
        self.assertEqual(recovered.transition_kind, "INITIAL")

    def test_pointer_durable_commit_receipt_missing_is_healed_after_validation(self):
        from bilqis_mlx.runtime.active_generated_grade import (
            activate_accepted_generated_grade,
            read_active_generated_grade,
        )
        from bilqis_mlx.runtime import active_generated_grade_custody as custody

        proposal, definition = _fixture()
        with TemporaryDirectory() as directory:
            root = Path(directory)
            patches = self._patches(proposal, definition)
            with patches[0], patches[1], patches[2], patches[3], patches[4], patches[5], patches[6]:
                with patch.object(
                    custody, "_persist_commit",
                    side_effect=RuntimeError("simulated commit-receipt crash"),
                ):
                    with self.assertRaisesRegex(RuntimeError, "commit-receipt crash"):
                        activate_accepted_generated_grade(root, proposal)

                self.assertTrue((root / "generated-grades" / "current.json").is_file())
                commits = root / "generated-grades" / "commits"
                self.assertFalse(commits.exists() and any(commits.iterdir()))
                cold = read_active_generated_grade(root)

            self.assertEqual(cold.definition, definition)
            self.assertTrue(
                (commits / f"{cold.activation_sha256}.json").is_file())

    def test_certification_transition_has_no_local_self_minting_path(self):
        import bilqis_mlx.runtime.active_generated_grade as active_grade_module
        from bilqis_mlx.runtime.active_generated_grade import (
            activate_accepted_generated_grade,
            activate_certified_generated_grade,
        )

        proposal, definition = _fixture()
        _release, successor_proposal = _single_member_fixture(
            "skos:future-z", "Z.FUTURE")
        successor_definition = _successor_definition(
            definition, successor_proposal)
        with TemporaryDirectory() as directory:
            root = Path(directory)
            patches = self._patches(
                proposal, definition, second=successor_proposal,
                second_definition=successor_definition)
            with patches[0], patches[1], patches[2], patches[3], patches[4], patches[5], patches[6]:
                activate_accepted_generated_grade(root, proposal)
                with self.assertRaises(BilqisError) as forged:
                    activate_certified_generated_grade(
                        root, successor_proposal, transition_authority=object())

        self.assertEqual(
            forged.exception.context.get("reason"),
            "BAMF_ACTIVE_GENERATED_GRADE_CERTIFICATION_AUTHORITY_REQUIRED")
        self.assertFalse(hasattr(
            active_grade_module,
            "_issue_certified_grade_transition_authority",
        ))


if __name__ == "__main__":
    unittest.main()
