"""Cold-resume binding for generation-zero foundation Factory authority."""
from pathlib import Path
from tempfile import TemporaryDirectory
from types import SimpleNamespace
from unittest import TestCase
from unittest.mock import Mock, patch

from bilqis_mlx.errors import BilqisError
from bilqis_mlx.runtime.bamf_bundle import accepted_runtime as _accepted_runtime  # noqa: F401
from bilqis_mlx.runtime.bamf_bundle.accepted_execution_cache import (
    _require_initial_foundation_authority,
)
from bilqis_mlx.runtime.bamf_bundle.publication.factory_release import (
    _require_release_root_shape, require_initial_factory_release,
)


class FoundationColdResumeTests(TestCase):
    def test_lineage_with_run_identity_verifies_pinned_release_and_foundation(self):
        student = SimpleNamespace(run_identity=SimpleNamespace(
            factory_release_sha256="1" * 64))
        run_dir = Path("fixture-run")
        with patch(
                "bilqis_mlx.runtime.bamf_bundle.publication.factory_release."
                "require_initial_factory_release") as require_release:
            _require_initial_foundation_authority(run_dir, student)
        require_release.assert_called_once_with(run_dir, student)

    def test_historical_bundle_without_run_identity_remains_readable_only(self):
        student = SimpleNamespace(run_identity=None)
        with patch(
                "bilqis_mlx.runtime.bamf_bundle.publication.factory_release."
                "require_initial_factory_release") as require_release:
            _require_initial_foundation_authority(Path("fixture-run"), student)
        require_release.assert_not_called()

    def test_cold_resume_allows_successor_release_artifacts_but_genesis_stays_strict(self):
        initial = "1" * 64
        successor = "2" * 64
        with TemporaryDirectory() as temporary:
            run_dir = Path(temporary)
            root = run_dir / "factory-releases"
            root.mkdir()
            (root / f"{initial}.json").write_text("{}")
            (root / f"{successor}.json").write_text("{}")
            _require_release_root_shape(
                run_dir, initial, allow_other_releases=True)
            with self.assertRaises(BilqisError):
                _require_release_root_shape(run_dir, initial)

    def test_historical_v2_release_uses_its_sealed_execution_plan_as_foundation(self):
        expected = "1" * 64
        foundation = ("A.ONE", "A.TWO")
        release = SimpleNamespace(
            release_sha256=expected,
            _foundation_capability_wire=False,
            foundation_capability_ids=None,
            execution_plan=SimpleNamespace(active_capability_inventory=foundation),
            verify=Mock(),
            require_foundation_capability_ids=Mock(side_effect=ValueError(
                "FACTORY_EXECUTABLE_RELEASE_FOUNDATION_CAPABILITY_IDS_REQUIRED")),
        )
        student = SimpleNamespace(run_identity=SimpleNamespace(
            factory_release_sha256=expected))

        with TemporaryDirectory() as temporary:
            run_dir = Path(temporary)
            root = run_dir / "factory-releases"
            root.mkdir()
            (root / f"{expected}.json").write_text("{}")
            with patch(
                    "bilqis_mlx.runtime.admission."
                    "_read_executable_factory_release_artifact",
                    return_value=release):
                restored = require_initial_factory_release(run_dir, student)

        self.assertIs(restored, release)
        release.verify.assert_called_once_with()
        release.require_foundation_capability_ids.assert_not_called()

    def test_historical_v2_release_rejects_ambiguous_foundation_inventory(self):
        expected = "1" * 64
        release = SimpleNamespace(
            release_sha256=expected,
            _foundation_capability_wire=False,
            foundation_capability_ids=None,
            execution_plan=SimpleNamespace(
                active_capability_inventory=("A.ONE", "A.ONE")),
            verify=Mock(),
        )
        student = SimpleNamespace(run_identity=SimpleNamespace(
            factory_release_sha256=expected))

        with TemporaryDirectory() as temporary:
            run_dir = Path(temporary)
            root = run_dir / "factory-releases"
            root.mkdir()
            (root / f"{expected}.json").write_text("{}")
            with patch(
                    "bilqis_mlx.runtime.admission."
                    "_read_executable_factory_release_artifact",
                    return_value=release), self.assertRaises(BilqisError):
                require_initial_factory_release(run_dir, student)
