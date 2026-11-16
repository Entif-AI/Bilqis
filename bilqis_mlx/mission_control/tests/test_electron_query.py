"""GUI05 consumes real CP03 pages without exposing private transport identities."""
import os
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest
from unittest.mock import Mock, patch

from bilqis_mlx.errors import BilqisError
from bilqis_mlx.control_plane import ControlPlaneService
from bilqis_mlx.control_plane.tests.support import start_service
from bilqis_mlx.mission_control import MissionControlQueryCatalog, QueryFamily, QueryMode, QueryRequest
from bilqis_mlx.mission_control.electron_bridge import ElectronBridge
from bilqis_mlx.mission_control.tests.dossier_fixture import records, SCHEMA, RUN_ID


class ElectronQueryTests(unittest.TestCase):
    def test_real_service_dossier_reference_and_historical_isolation(self):
        catalog = MissionControlQueryCatalog(records())
        with TemporaryDirectory() as tmp:
            socket = Path(tmp) / "cp.sock"
            service = ControlPlaneService(Path(tmp) / "absent", socket, query_source=lambda: catalog)
            thread = start_service(service)
            bridge = ElectronBridge()
            try:
                with patch.dict(os.environ, {"BILQIS_CONTROL_PLANE_SOCKET": str(socket)}):
                    bridge.connect()
                pages = [bridge.query(QueryRequest(QueryFamily.CAPABILITY, QueryMode.HISTORICAL,
                    run_id=RUN_ID, generation=g, schema_version=SCHEMA).to_record()) for g in (1, 3)]
                self.assertEqual([p["records"][0]["now"]["value"] for p in pages], [9, 10])
                ref = "evidence:B.AND:fresh:3"
                linked = bridge.query(QueryRequest(QueryFamily.REFERENCE, QueryMode.HISTORICAL,
                    run_id=RUN_ID, generation=3, reference=ref).to_record())
                self.assertEqual(linked["links"][0]["target_record_id"], ref)
                score = bridge.query(QueryRequest(QueryFamily.CAPABILITY, QueryMode.HISTORICAL,
                    run_id=RUN_ID, generation=3, record_id=ref).to_record())
                self.assertEqual(score["records"][0]["score_correct"]["value"], 10)
                wrong = bridge.query(QueryRequest(QueryFamily.EPISODE, QueryMode.HISTORICAL,
                    run_id=RUN_ID, generation=3, record_id=ref).to_record())
                self.assertEqual(wrong["state"], "MISSING")
                self.assertNotIn("session", pages[0])
                self.assertNotIn("service", pages[0])
                self.assertFalse((Path(tmp) / "absent").exists())
            finally:
                bridge.disconnect()
                service.shutdown()
                thread.join(2)

    def test_mismatched_query_response_is_rejected(self):
        request = QueryRequest(QueryFamily.CAPABILITY, run_id=RUN_ID, generation=3)
        bridge = ElectronBridge()
        response = MissionControlQueryCatalog(records()).encode_page(
            MissionControlQueryCatalog(records()).query(request))
        bridge.client = Mock()
        response.update(accepted=True, query_id="0" * 64)
        bridge.client.query.return_value = response
        with self.assertRaises(BilqisError) as caught:
            bridge.query(request.to_record())
        self.assertEqual(caught.exception.code, "SCHOOL.BAMF_CONTROL_PLANE.INVALID")
