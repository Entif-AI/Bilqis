"""Active CP01 discovery prefers a human operator over passive inspection."""
import os
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest
from unittest.mock import patch

from bilqis_mlx.control_plane.active_endpoint import (
    advertise_active_endpoint, discover_active_endpoint,
)


class ActiveEndpointTests(unittest.TestCase):
    def test_operator_endpoint_outranks_existing_service_endpoint(self):
        with TemporaryDirectory(dir="/tmp") as directory:
            root = Path(directory)
            registry = root / "registry"
            inspection = root / "inspection"
            operator = root / "aspirant"
            with patch.dict(os.environ, {
                    "BILQIS_ACTIVE_CONTROL_PLANE_DIR": str(registry),
            }), advertise_active_endpoint(
                    inspection, socket_path=root / "inspection.sock", role="service"), \
                    advertise_active_endpoint(
                        operator, socket_path=root / "aspirant.sock", role="operator"):
                selected = discover_active_endpoint()

            self.assertIsNotNone(selected)
            self.assertEqual(selected.role, "operator")
            self.assertEqual(selected.run_dir, operator.resolve())


if __name__ == "__main__":
    unittest.main()
