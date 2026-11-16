"""CP07 independent non-Electron attach/recovery over accepted BAMF custody."""
from contextlib import contextmanager
from dataclasses import replace
from pathlib import Path
import signal
import socket as sockets
import subprocess
import sys
import time

from bilqis_mlx.control_plane import ControlPlaneClient, PROTOCOL_VERSION
from bilqis_mlx.control_plane.discovery import discover_learner
from bilqis_mlx.mission_control.model import CoverageState, RunRef
from bilqis_mlx.mission_control.projection import MissionControlProjection
from bilqis_mlx.mission_control.query_contracts import QueryFamily, QueryMode, QueryRequest
from bilqis_mlx.mission_control.tests.samples import SAMPLES
from bilqis_mlx.presentation.operator_cli.tests.bamf_lifecycle.create_resume_support import (
    BamfCreateResumeCase, TOPOLOGY,
)
from bilqis_mlx.runtime.bamf_bundle import inspect_accepted_generation


@contextmanager
def standalone(run_dir: Path, socket: Path, projection: Path):
    """A genuine independent CP01 process; kill only this disposable child."""
    child = subprocess.Popen([
        sys.executable, "-m", "bilqis_mlx.control_plane",
        "--run-dir", str(run_dir), "--socket", str(socket),
        "--projection-db", str(projection),
    ], stdout=subprocess.DEVNULL, stderr=subprocess.PIPE, text=True)
    try:
        deadline = time.monotonic() + 4
        ready = False
        while child.poll() is None and time.monotonic() < deadline:
            with sockets.socket(sockets.AF_UNIX) as probe:
                try:
                    probe.connect(str(socket))
                    ready = True
                    break
                except (FileNotFoundError, ConnectionRefusedError):
                    time.sleep(0.01)
        assert ready, f"CP07_SERVICE_START_FAILED:{child.poll()}"
        yield child
    finally:
        if child.poll() is None:
            child.send_signal(signal.SIGINT)
        try:
            child.wait(timeout=3)
        except subprocess.TimeoutExpired:
            child.kill()
            child.wait(timeout=3)
        if child.stderr is not None:
            child.stderr.close()


class CP07StandaloneRecoveryTests(BamfCreateResumeCase):
    def create_accepted_run(self):
        target = self.root / "cp07-run"
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

    @staticmethod
    def fixture_projection_records(accepted, learner):
        """Actual G0 identity, with explicitly fixture-backed domain evidence."""
        run = RunRef(
            accepted.run_id, accepted.run_identity_sha256,
            accepted.generation, accepted.generation_manifest_sha256,
            accepted.candidate_identity_sha256, accepted.factory_release_sha256,
            accepted.semantic_release_sha256, accepted.topology_sha256,
        )
        context_id = f"run-context:{accepted.run_id}"
        view_id = f"operator-view:{accepted.run_id}"
        capability_id = "fixture:capability"
        episode_id = "fixture:episode"
        context = replace(SAMPLES[0],
            meta=replace(SAMPLES[0].meta, run=run, record_id=context_id,
                         coverage=CoverageState.PARTIAL),
            run_state=learner.state.value, optimizer_step=accepted.optimizer_step,
            stage="UNKNOWN")
        view = replace(SAMPLES[1],
            meta=replace(SAMPLES[1].meta, run=run, record_id=view_id,
                         coverage=CoverageState.PARTIAL),
            learner_state=learner.state.value, stage="UNKNOWN",
            related_record_ids=(capability_id,))
        capability = replace(SAMPLES[3],
            meta=replace(SAMPLES[3].meta, run=run, record_id=capability_id,
                         evidence_refs=(episode_id,)))
        episode = replace(SAMPLES[5],
            meta=replace(SAMPLES[5].meta, run=run, record_id=episode_id,
                         evidence_refs=("fixture:evidence:lesson",),
                         receipt_refs=("fixture:receipt:lesson",)))
        return (context, view, capability, episode)

    def _assert_queries_and_index_rebuild(self, socket, index, records, requests, learner):
        with ControlPlaneClient(socket, client_id="cp07-non-electron") as client:
            health = client.request("health")
            self.assertEqual(health["learner"], learner.to_record())
            first = tuple(client.query(request) for request in requests)
            self.assertTrue(all(page["accepted"] for page in first))
            self.assertEqual([page["state"] for page in first],
                             ["PARTIAL", "PRESENT", "PRESENT",
                              "PRESENT", "PRESENT", "PRESENT"])
            run_context = next(row for row in first[0]["records"]
                               if row["schema_version"].endswith("run-context/v1"))
            self.assertEqual(run_context["optimizer_step"], 0)
            self.assertEqual(run_context["stage"], "UNKNOWN")
            self.assertEqual(first[3]["records"][0]["meta"]["record_id"],
                             "fixture:capability")
            self.assertIn("fixture:episode", [
                link["target_record_id"] for link in first[4]["links"]])
            self.assertIn("fixture:receipt:lesson", [
                link["target_ref"] for link in first[5]["links"]])

            malformed = client._send({"type": "query", "query": {"schema": "old"}})
            self.assertEqual(malformed["reason"], "CONTROL_PLANE_QUERY_INVALID")
            index.unlink()
            unavailable = client.query(requests[0])
            self.assertFalse(unavailable["accepted"])
            self.assertEqual(unavailable["reason"],
                             "CONTROL_PLANE_QUERY_SOURCE_UNAVAILABLE")
            self.assertEqual(client.request("health")["learner"],
                             learner.to_record())
            MissionControlProjection.rebuild(index, records)
            rebuilt = tuple(client.query(request) for request in requests)
            for earlier, later in zip(first, rebuilt):
                self.assertEqual(earlier["records"], later["records"])
                self.assertEqual(earlier["links"], later["links"])
                self.assertEqual(earlier["state"], later["state"])

            index.write_bytes(b"cp07-corrupt-projection")
            corrupted = client.query(requests[0])
            self.assertFalse(corrupted["accepted"])
            MissionControlProjection.rebuild(index, records)
            self.assertEqual(client.query(requests[0])["records"], first[0]["records"])
        return first

    def test_independent_attach_recovery_and_projection_rebuild(self):
        run_dir = self.create_accepted_run()
        pointer = run_dir / "bamf-state.json"
        original_pointer = pointer.read_bytes()
        learner = discover_learner(run_dir)
        accepted = inspect_accepted_generation(pointer)
        records = self.fixture_projection_records(accepted, learner)
        index = self.root / "projection.sqlite3"
        socket = self.root / "cp.sock"
        MissionControlProjection.rebuild(index, records)

        requests = (
            QueryRequest(QueryFamily.RUN, run_id=accepted.run_id),
            QueryRequest(QueryFamily.CAPABILITY, run_id=accepted.run_id),
            QueryRequest(QueryFamily.EPISODE, run_id=accepted.run_id),
            QueryRequest(QueryFamily.CAPABILITY, mode=QueryMode.HISTORICAL,
                         run_id=accepted.run_id, generation=0, as_of=118),
            QueryRequest(QueryFamily.LINKS, record_id="fixture:capability"),
            QueryRequest(QueryFamily.LINKS, record_id="fixture:episode"),
        )
        with standalone(run_dir, socket, index) as first_process:
            first = self._assert_queries_and_index_rebuild(
                socket, index, records, requests, learner)

            # An abruptly lost external client cannot own the learner or CP01.
            crashed_client = subprocess.run([
                sys.executable, "-c",
                "import os,sys; from pathlib import Path; "
                "from bilqis_mlx.control_plane import ControlPlaneClient; "
                "c=ControlPlaneClient(Path(sys.argv[1])); c.connect(); os._exit(23)",
                str(socket),
            ], check=False, timeout=3)
            self.assertEqual(crashed_client.returncode, 23)
            with ControlPlaneClient(socket) as survivor:
                self.assertEqual(survivor.request("health")["learner"],
                                 learner.to_record())
            # Also inject a hard control-plane crash, not just graceful SIGINT.
            first_process.kill()
            first_process.wait(timeout=3)

        self.assertEqual(pointer.read_bytes(), original_pointer)
        self.assertEqual(discover_learner(run_dir), learner)
        with standalone(run_dir, socket, index):
            wrong = ControlPlaneClient(socket, protocol_version=PROTOCOL_VERSION + "-old")
            self.assertEqual(wrong.connect()["state"], "incompatible-version")
            wrong.close()
            with ControlPlaneClient(socket) as client:
                self.assertEqual(client.request("health")["learner"], learner.to_record())
                self.assertEqual(client.query(requests[3])["records"], first[3]["records"])
                gap = client.subscribe_events(after_cursor="e" * 64)
                self.assertEqual(gap.gap["state"], "fresh-snapshot-required")
        self.assertEqual(pointer.read_bytes(), original_pointer)
