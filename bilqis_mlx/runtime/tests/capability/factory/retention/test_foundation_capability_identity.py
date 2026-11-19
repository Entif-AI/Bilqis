"""BMF v0.3.1 foundation identity consumption at the B09 transition seam."""
from pathlib import Path
from types import SimpleNamespace
from unittest import TestCase
from unittest.mock import patch

from bilqis_mlx.errors import BilqisError
from bilqis_mlx.runtime._plasticity_promotion.evidence import _foundation_capabilities


FOUNDATION = ("A.ONE", "A.TWO")
INITIAL_RELEASE = "1" * 64


class FoundationCapabilityIdentityTests(TestCase):
    def test_consumes_signed_release_authority_not_execution_plan_rederivation(self):
        release = SimpleNamespace(
            require_foundation_capability_ids=lambda: FOUNDATION,
            execution_plan=SimpleNamespace(capabilities=(
                SimpleNamespace(capability_id="SUCCESSOR.ONLY"),)),
        )
        run_dir = Path("fixture-run")
        with patch(
                "bilqis_mlx.runtime._plasticity_promotion.evidence._release_for_sha",
                return_value=release) as load:
            self.assertEqual(
                _foundation_capabilities(run_dir, INITIAL_RELEASE), FOUNDATION)
        load.assert_called_once_with(run_dir, INITIAL_RELEASE)

    def test_fails_closed_when_release_lacks_signed_foundation_authority(self):
        release = SimpleNamespace(
            execution_plan=SimpleNamespace(capabilities=(
                SimpleNamespace(capability_id="A.ONE"),
                SimpleNamespace(capability_id="A.TWO"),
            )))
        with patch(
                "bilqis_mlx.runtime._plasticity_promotion.evidence._release_for_sha",
                return_value=release), self.assertRaises(BilqisError):
            _foundation_capabilities(Path("fixture-run"), INITIAL_RELEASE)
