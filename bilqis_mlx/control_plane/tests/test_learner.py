"""CP01 integration with real disposable BAMF generation custody."""
import json
from pathlib import Path
from threading import Event, Thread
from unittest.mock import patch

from bilqis_mlx.control_plane import ControlPlaneClient, ControlPlaneService
from bilqis_mlx.presentation.operator_cli.tests.bamf_lifecycle.create_resume_support import (
    BamfCreateResumeCase, TOPOLOGY,
)
from bilqis_mlx.runtime.bamf_operator.locking import bamf_operator_lock

from .support import start_service


class ControlPlaneLearnerIntegrationTests(BamfCreateResumeCase):
    def _create_disposable_generation_zero(self) -> Path:
        target = self.root / "created-bamf"
        manifest = self.root / "manifest.json"
        manifest.write_text("{}", encoding="utf-8")
        with self.foundation_create_context():
            code, _output, errors = self.invoke([
                "--human-run", "--model-topology", str(TOPOLOGY),
                "--atlas-release-manifest", str(manifest),
                "--run-dir", str(target), *self.FOUNDATION_ARGS,
            ])
        self.assertEqual((code, errors), (0, ""))
        return target

    def test_restart_rediscovers_same_generation_without_mutating_learner(self):
        target = self._create_disposable_generation_zero()
        pointer = target / "bamf-state.json"
        before = pointer.read_bytes()
        socket_path = self.root / "cp.sock"
        first = ControlPlaneService(target, socket_path)
        first_thread = start_service(first)
        with ControlPlaneClient(socket_path, client_id="electron-fixture") as client:
            first_health = client.request("health")
        first_service_id = first_health["service"]["service_id"]
        first_learner = first_health["learner"]
        first.shutdown()
        first_thread.join(2)

        second = ControlPlaneService(target, socket_path)
        second_thread = start_service(second)
        with ControlPlaneClient(socket_path, client_id="electron-fixture") as client:
            second_health = client.request("health")
        second.shutdown()
        second_thread.join(2)

        self.assertNotEqual(
            first_service_id, second_health["service"]["service_id"])
        self.assertEqual(first_learner, second_health["learner"])
        self.assertEqual(first_learner["run_id"], "operator-first-student")
        self.assertEqual(first_learner["generation"], 0)
        self.assertEqual(pointer.read_bytes(), before)

    def test_client_disconnect_leaves_disposable_operator_owner_running(self):
        target = self._create_disposable_generation_zero()
        pointer = target / "bamf-state.json"
        before = pointer.read_bytes()
        socket_path = self.root / "cp.sock"
        locked, release = Event(), Event()

        def learner_owner():
            with bamf_operator_lock(target):
                locked.set()
                release.wait(3)

        owner = Thread(target=learner_owner, daemon=True)
        owner.start()
        self.assertTrue(locked.wait(1))
        service = ControlPlaneService(target, socket_path)
        service_thread = start_service(service)
        client = ControlPlaneClient(socket_path, client_id="crash-fixture")
        attached = client.connect()
        self.assertTrue(attached["learner"]["operator_active"])
        self.assertTrue(client.request("health")["learner_active"])
        client.close()
        self.assertTrue(owner.is_alive())
        self.assertEqual(pointer.read_bytes(), before)
        service.shutdown()
        service_thread.join(2)
        release.set()
        owner.join(2)
        self.assertFalse(owner.is_alive())

    def test_health_never_hydrates_bamf_numerical_state(self):
        target = self._create_disposable_generation_zero()
        socket_path = self.root / "cp.sock"
        service = ControlPlaneService(target, socket_path)
        service_thread = start_service(service)
        try:
            with patch(
                    "bilqis_mlx.runtime.mlx_checkpoint.load_bamf_state_payload",
                    side_effect=AssertionError("CP01 must not hydrate numerical state")):
                with ControlPlaneClient(socket_path) as client:
                    health = client.request("health")
                    self.assertEqual(health["learner"]["generation"], 0)
                    self.assertTrue(health["learner_ready"])
        finally:
            service.shutdown()
            service_thread.join(2)

    def test_health_degrades_on_tampered_acceptance_metadata(self):
        target = self._create_disposable_generation_zero()
        pointer = json.loads((target / "bamf-state.json").read_text())
        acceptance_path = (
            target / "bamf-acceptance"
            / f"{pointer['manifest_sha256']}.json")
        acceptance = json.loads(acceptance_path.read_text())
        acceptance["run_id"] = "tampered-run"
        acceptance_path.write_text(json.dumps(acceptance), encoding="utf-8")
        socket_path = self.root / "cp.sock"
        service = ControlPlaneService(target, socket_path)
        service_thread = start_service(service)
        try:
            with ControlPlaneClient(socket_path) as client:
                health = client.request("health")
            self.assertEqual(health["learner"]["state"], "degraded")
            self.assertFalse(health["learner_ready"])
        finally:
            service.shutdown()
            service_thread.join(2)
