import hashlib
import json
import os
import sqlite3
import subprocess
import sys
import zlib
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

from .base import DataPlaneCase
from bilqis_mlx.data_plane import close_data_planes, data_plane
from bilqis_mlx._data_plane.cli import _maintenance
from bilqis_mlx._data_plane.maintenance import (
    file_gc_report, gc_report, migrate_legacy_payloads, pin,
)


def _sha(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()


def _canonical(value) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":")).encode()


class DataPlaneMaintenanceTests(DataPlaneCase):
    def test_maintenance_lock_blocks_before_schema_upgrade(self):
        close_data_planes()
        path = self.root / "plane.sqlite3"
        db = sqlite3.connect(path)
        db.execute("CREATE TABLE meta(key TEXT PRIMARY KEY,value TEXT NOT NULL) WITHOUT ROWID")
        db.execute("INSERT INTO meta(key,value) VALUES('schema_version','1')")
        db.commit()
        db.close()
        run = self.root / "run"
        run.mkdir()
        (run / "bamf-state.json").write_text("{}")
        lock = run / ".bamf-operator.lock"
        holder = subprocess.Popen(
            [sys.executable, "-c", (
                "import fcntl,sys; f=open(sys.argv[1],'a+b'); "
                "fcntl.flock(f,fcntl.LOCK_EX); print('READY',flush=True); sys.stdin.read()"
            ), str(lock)],
            stdin=subprocess.PIPE, stdout=subprocess.PIPE, text=True,
        )
        try:
            self.assertEqual(holder.stdout.readline().strip(), "READY")
            args = SimpleNamespace(
                scan_root=[run], apply=True, scope="migrate",
                max_records=0, vacuum=False,
            )
            with self.assertRaisesRegex(ValueError, "HUMAN_TRAINING_ACTIVE"):
                _maintenance(args)
        finally:
            if holder.stdin:
                holder.stdin.close()
            holder.wait(timeout=5)
            if holder.stdout:
                holder.stdout.close()
        db = sqlite3.connect(path)
        try:
            self.assertEqual(
                db.execute("SELECT value FROM meta WHERE key='schema_version'").fetchone(),
                ("1",),
            )
            self.assertIsNone(db.execute(
                "SELECT 1 FROM sqlite_master WHERE type='table' AND name='archived_objects'"
            ).fetchone())
        finally:
            db.close()

    def test_cli_module_entrypoint_emits_status(self):
        env = dict(os.environ)
        env["BILQIS_DATA_PLANE"] = str(self.root / "plane.sqlite3")
        completed = subprocess.run(
            [sys.executable, "-m", "bilqis_mlx._data_plane.cli", "status"],
            cwd=Path(__file__).resolve().parents[5],
            env=env,
            check=True,
            capture_output=True,
            text=True,
        )
        payload = json.loads(completed.stdout)
        self.assertEqual(payload["path"], str((self.root / "plane.sqlite3").resolve()))

    def test_v1_database_upgrades_in_place_without_losing_legacy_readability(self):
        close_data_planes()
        path = self.root / "plane.sqlite3"
        db = sqlite3.connect(path)
        db.execute("CREATE TABLE meta(key TEXT PRIMARY KEY,value TEXT NOT NULL) WITHOUT ROWID")
        db.execute("INSERT INTO meta(key,value) VALUES('schema_version','1')")
        db.commit()
        db.close()

        plane = data_plane()

        self.assertEqual(
            plane._db.execute("SELECT value FROM meta WHERE key='schema_version'").fetchone(),
            ("2",),
        )
        self.assertEqual(plane.stats()["objects"], 0)

    def test_new_object_and_node_payloads_stay_out_of_sqlite(self):
        plane = data_plane()
        object_raw = b'{"payload":"' + b"x" * 200_000 + b'"}'
        object_sha = _sha(object_raw)
        node_raw = _canonical({"schema": "fixture", "generation": 1})
        node_sha = _sha(node_raw)

        plane.put_object(object_sha, object_raw)
        plane.put_node(node_sha, node_raw, 1, None)

        self.assertEqual(plane._db.execute("SELECT COUNT(*) FROM objects").fetchone()[0], 0)
        self.assertEqual(plane._db.execute("SELECT COUNT(*) FROM nodes").fetchone()[0], 0)
        self.assertEqual(plane.get_object(object_sha), object_raw)
        self.assertEqual(plane.get_node(node_sha), node_raw)
        self.assertEqual(plane.stats()["archived_objects"], 1)
        self.assertEqual(plane.stats()["archived_nodes"], 1)

    def test_independent_writers_converge_on_one_archive_record(self):
        data_plane()
        close_data_planes()
        raw = b'{"racing":"' + b"x" * 20_000 + b'"}'
        digest = _sha(raw)
        script = (
            "import hashlib,sys; from bilqis_mlx.data_plane import data_plane; "
            "raw=bytes.fromhex(sys.argv[1]); digest=hashlib.sha256(raw).hexdigest(); "
            "data_plane().put_object(digest,raw)"
        )
        env = dict(os.environ)
        children = [
            subprocess.Popen(
                [sys.executable, "-c", script, raw.hex()], env=env,
                cwd=Path(__file__).resolve().parents[5],
            )
            for _ in range(2)
        ]
        for child in children:
            self.assertEqual(child.wait(timeout=15), 0)
        plane = data_plane()
        self.assertEqual(plane._db.execute(
            "SELECT COUNT(*) FROM archived_objects WHERE sha256=?", (digest,)
        ).fetchone()[0], 1)
        pack = next((plane.path.with_name(plane.path.name + ".archive") / "objects").glob("*.pack"))
        self.assertEqual(pack.stat().st_size, 53 + len(zlib.compress(raw, level=6)))

    def test_legacy_payload_migration_is_verified_and_idempotent(self):
        plane = data_plane()
        object_raw = b'{"legacy":true}'
        object_sha = _sha(object_raw)
        node_raw = _canonical({"schema": "fixture", "generation": 2})
        node_sha = _sha(node_raw)
        plane._db.execute(
            "INSERT INTO objects(sha256,payload,raw_bytes) VALUES(?,?,?)",
            (object_sha, zlib.compress(object_raw), len(object_raw)))
        plane._db.execute(
            "INSERT INTO nodes(sha256,payload,generation,parent_sha256) VALUES(?,?,?,?)",
            (node_sha, node_raw, 2, None))

        first = migrate_legacy_payloads(plane)
        second = migrate_legacy_payloads(plane)

        self.assertEqual(first, {"migrated_objects": 1, "migrated_nodes": 1})
        self.assertEqual(second, {"migrated_objects": 0, "migrated_nodes": 0})
        self.assertEqual(plane.get_object(object_sha), object_raw)
        self.assertEqual(plane.get_node(node_sha), node_raw)
        self.assertEqual(plane.stats()["legacy_objects"], 0)
        self.assertEqual(plane.stats()["legacy_nodes"], 0)

    def test_bamf_pointer_ancestry_and_nested_object_references_survive_gc(self):
        plane = data_plane()
        nested_raw = _canonical({"evidence": "live"})
        nested_sha = _sha(nested_raw)
        plane.put_object(nested_sha, nested_raw)
        dead_object = b'{"dead":true}'
        dead_object_sha = _sha(dead_object)
        plane.put_object(dead_object_sha, dead_object)

        parent_raw = _canonical({
            "schema": "bundle", "generation": 0,
            "sidecars": {"nested": {"object_sha256": nested_sha}},
            "tensors": {},
        })
        parent_sha = _sha(parent_raw)
        plane.put_node(parent_sha, parent_raw, 0, None)
        current_raw = _canonical({
            "schema": "bundle", "generation": 1,
            "sidecars": {}, "tensors": {},
        })
        current_sha = _sha(current_raw)
        plane.put_node(current_sha, current_raw, 1, parent_sha)
        dead_node_raw = _canonical({"schema": "dead", "generation": 99})
        dead_node_sha = _sha(dead_node_raw)
        plane.put_node(dead_node_sha, dead_node_raw, 99, None)
        (self.root / "bamf-state.json").write_text(json.dumps({
            "schema": "bilqis.mlx.bamf-generation-pointer/v2",
            "manifest_sha256": current_sha,
        }))

        dry = gc_report(plane, (self.root,))
        self.assertEqual(dry["reachable_nodes"], 2)
        self.assertEqual(dry["unreachable_nodes"], 1)
        self.assertEqual(dry["unreachable_objects"], 1)

        applied = gc_report(plane, (self.root,), apply=True)
        self.assertTrue(applied["applied"])
        self.assertEqual(plane.get_object(nested_sha), nested_raw)
        self.assertEqual(plane.get_node(parent_sha), parent_raw)
        with self.assertRaises(ValueError):
            plane.get_object(dead_object_sha)
        with self.assertRaises(ValueError):
            plane.get_node(dead_node_sha)

    def test_operator_pin_is_an_explicit_retention_tier(self):
        plane = data_plane()
        raw = b'{"operator":"witness"}'
        digest = _sha(raw)
        plane.put_object(digest, raw)
        pin(plane, "object", digest, "operator", "fixture witness")

        report = gc_report(plane, (self.root,), apply=True)

        self.assertEqual(report["unreachable_objects"], 0)
        self.assertEqual(plane.get_object(digest), raw)

    def test_file_only_gc_never_deletes_sqlite_objects_or_nodes(self):
        plane = data_plane()
        raw = b'{"ordinary":"still here"}'
        digest = _sha(raw)
        plane.put_object(digest, raw)
        dead_file = b"obsolete tensor"
        dead_file_sha = _sha(dead_file)
        dead_path = plane.file_object_destination(dead_file_sha)
        dead_path.parent.mkdir(parents=True)
        dead_path.write_bytes(dead_file)

        report = file_gc_report(plane, (self.root,), apply=True)

        self.assertEqual(report["unreachable_file_objects"], 1)
        self.assertFalse(dead_path.exists())
        self.assertEqual(plane.get_object(digest), raw)

    def test_file_only_gc_follows_filesystem_bamf_manifest_ancestry(self):
        plane = data_plane()
        live_file = b"accepted tensor"
        live_sha = _sha(live_file)
        live_path = plane.file_object_destination(live_sha)
        live_path.parent.mkdir(parents=True)
        live_path.write_bytes(live_file)
        dead_file = b"rejected tensor"
        dead_sha = _sha(dead_file)
        dead_path = plane.file_object_destination(dead_sha)
        dead_path.parent.mkdir(parents=True, exist_ok=True)
        dead_path.write_bytes(dead_file)

        bundle = self.root / "bamf-bundles" / "fixture"
        bundle.mkdir(parents=True)
        manifest = _canonical({
            "schema": "bilqis.mlx.bamf-bundle/v6",
            "parent_manifest_sha256": None,
            "tensors": {"object_sha256": live_sha},
            "sidecars": {},
        })
        manifest_sha = _sha(manifest)
        canonical_bundle = self.root / "bamf-bundles" / manifest_sha
        bundle.rename(canonical_bundle)
        (canonical_bundle / "manifest.json").write_bytes(manifest)
        (self.root / "bamf-state.json").write_text(json.dumps({
            "schema": "bilqis.mlx.bamf-generation-pointer/v2",
            "manifest_sha256": manifest_sha,
            "bundle": f"bamf-bundles/{manifest_sha}",
        }))

        report = file_gc_report(plane, (self.root,), apply=True)

        self.assertEqual(report["reachable_file_objects"], 1)
        self.assertEqual(report["unreachable_file_objects"], 1)
        self.assertTrue(live_path.exists())
        self.assertFalse(dead_path.exists())

    def test_file_only_gc_preserves_named_evidence_reference(self):
        plane = data_plane()
        raw = b"evidence checkpoint"
        digest = _sha(raw)
        path = plane.file_object_destination(digest)
        path.parent.mkdir(parents=True)
        path.write_bytes(raw)
        plane.put_object_reference(
            "evidence-witness", _canonical({"checkpoint_sha256": digest}))

        report = file_gc_report(plane, (self.root,), apply=True)

        self.assertEqual(report["reachable_file_objects"], 1)
        self.assertEqual(report["unreachable_file_objects"], 0)
        self.assertTrue(path.exists())

    def test_archive_compaction_discards_bytes_from_collected_records(self):
        plane = data_plane()
        keep = b'{"keep":"' + b"a" * 50_000 + b'"}'
        dead = b'{"dead":"' + b"b" * 50_000 + b'"}'
        keep_sha, dead_sha = _sha(keep), _sha(dead)
        plane.put_object(keep_sha, keep)
        plane.put_object(dead_sha, dead)
        plane.put_object_reference("keep", keep)
        pack = next((plane.path.with_name(plane.path.name + ".archive") / "objects").glob("*.pack"))
        before = pack.stat().st_size

        gc_report(plane, (self.root,), apply=True)
        result = plane.compact_archive("objects")

        self.assertLess(result["pack_bytes"], before)
        self.assertEqual(plane.get_object(keep_sha), keep)
        with self.assertRaises(ValueError):
            plane.get_object(dead_sha)

    def test_interrupted_pack_append_retries_and_compacts_orphan_bytes(self):
        plane = data_plane()
        raw = b'{"retry":"' + b"z" * 50_000 + b'"}'
        digest = _sha(raw)
        original = plane._archive_append

        def interrupted(*args, **kwargs):
            result = original(*args, **kwargs)
            raise RuntimeError("simulated crash before metadata publication")

        with patch.object(plane, "_archive_append", side_effect=interrupted):
            with self.assertRaises(RuntimeError):
                plane.put_object(digest, raw)
        self.assertEqual(plane._db.execute(
            "SELECT COUNT(*) FROM archived_objects").fetchone()[0], 0)

        plane.put_object(digest, raw)
        pack = next((plane.path.with_name(plane.path.name + ".archive") / "objects").glob("*.pack"))
        before = pack.stat().st_size
        result = plane.compact_archive("objects")

        self.assertLess(result["pack_bytes"], before)
        self.assertEqual(plane.get_object(digest), raw)


if __name__ == "__main__":
    import unittest
    unittest.main()
