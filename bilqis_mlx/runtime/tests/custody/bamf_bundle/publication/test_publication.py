"""B13.1 crash, retry, pointer-lineage and outbox witnesses."""
from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
import unittest
from dataclasses import replace
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import patch

import bilqis_mlx.runtime.bamf_bundle.publication as publication
import bilqis_mlx.runtime.bamf_bundle.publication.storage as publication_storage
import bilqis_mlx.runtime.mlx_checkpoint as mlx_checkpoint
from bilqis_mlx.data_plane import data_plane
from bilqis_mlx.errors import BilqisError
from bilqis_mlx.runtime.bamf_bundle import (
    inspect_accepted_generation, load_bamf_generation, publish_bamf_generation,
    record_bamf_rejection,
)

from bilqis_mlx.runtime.tests.custody.bamf_bundle.helpers import (
    publish_candidate,
    accepted_state, candidate, parent_state, rejected_state, shape_patch,
)


class BamfPublicationTests(unittest.TestCase):
    def setUp(self):
        self.temporary = TemporaryDirectory()
        self.root = Path(self.temporary.name)
        self.run = self.root / "run"
        self.environment = patch.dict(
            os.environ, {"BILQIS_DATA_PLANE": str(self.root / "plane.sqlite3")})
        self.environment.start()

    def tearDown(self):
        self.environment.stop()
        self.temporary.cleanup()

    def publish(self, source):
        with shape_patch(), patch.object(mlx_checkpoint, "assert_headroom"):
            return publish_candidate(self.run, source)

    def test_accepted_generation_advances_once_and_parent_bundle_remains(self):
        initial_state = parent_state()
        first = self.publish(candidate(initial_state))
        retained = accepted_state(initial_state)
        second_source = candidate(retained, 1, first["manifest_sha256"])
        second = self.publish(second_source)
        with shape_patch():
            loaded = load_bamf_generation(self.run / "bamf-state.json")
        self.assertEqual(loaded.generation, 1)
        self.assertEqual(loaded.retained_state.optimizer_step, 12)
        self.assertEqual(loaded.parent_manifest_sha256, first["manifest_sha256"])
        self.assertTrue((self.run / first["bundle"]).is_dir())
        self.assertNotEqual(first["manifest_sha256"], second["manifest_sha256"])

    def test_lightweight_inspection_exposes_current_command_target_identity(self):
        published = self.publish(candidate(parent_state()))
        inspection = inspect_accepted_generation(self.run / "bamf-state.json")
        acceptance = json.loads((
            self.run / "bamf-acceptance"
            / f"{published['manifest_sha256']}.json"
        ).read_text())
        manifest = json.loads((
            self.run / published["bundle"] / "manifest.json"
        ).read_text())
        identity_binding = manifest["sidecars"]["run_identity"]
        identity = json.loads((
            self.run / published["bundle"] / identity_binding["filename"]
        ).read_text())

        self.assertEqual(
            inspection.candidate_identity_sha256,
            acceptance["candidate_identity_sha256"],
        )
        self.assertEqual(
            inspection.semantic_release_sha256,
            manifest["provenance"]["release_digest"],
        )
        self.assertEqual(
            inspection.factory_release_sha256,
            acceptance.get(
                "factory_release_sha256",
                identity["factory_release_sha256"],
            ),
        )

    def test_retry_converges_after_renamed_bundle_before_pointer(self):
        source = candidate(parent_state())
        with shape_patch(), patch.object(mlx_checkpoint, "assert_headroom"), \
                patch.object(publication, "_atomic_pointer", side_effect=RuntimeError("crash")):
            with self.assertRaisesRegex(RuntimeError, "crash"):
                publish_candidate(self.run, source)
        self.assertFalse((self.run / "bamf-state.json").exists())
        published = self.publish(source)
        self.assertTrue((self.run / published["bundle"]).is_dir())
        self.assertEqual(json.loads((self.run / "bamf-state.json").read_text()), published)

    def test_stale_old_style_stage_does_not_block_retry(self):
        stale = self.run / ".bamf-staging" / "0000000"
        stale.mkdir(parents=True)
        (stale / "partial").write_text("interrupted")
        published = self.publish(candidate(parent_state()))
        self.assertTrue((self.run / published["bundle"]).is_dir())
        self.assertEqual((stale / "partial").read_text(), "interrupted")

    def test_unsafe_run_root_rejects_before_publication_or_lock_writes(self):
        for kind in ("symlink", "file"):
            with self.subTest(kind=kind):
                run = self.root / kind
                outside = self.root / (kind + "-outside")
                if kind == "symlink":
                    outside.mkdir()
                    run.symlink_to(outside, target_is_directory=True)
                else:
                    run.write_text("not-a-directory")
                self.run = run

                with self.assertRaises(BilqisError):
                    self.publish(candidate(parent_state()))
                if kind == "symlink":
                    self.assertEqual(tuple(outside.iterdir()), ())
                else:
                    self.assertEqual(run.read_text(), "not-a-directory")

                with self.assertRaises(BilqisError):
                    load_bamf_generation(run / "bamf-state.json")
                if kind == "symlink":
                    self.assertEqual(tuple(outside.iterdir()), ())

    def test_reader_lock_never_mints_missing_b13_custody(self):
        self.assertFalse(self.run.exists())
        with self.assertRaises(BilqisError):
            load_bamf_generation(self.run / "bamf-state.json")
        self.assertFalse(self.run.exists())

        self.run.mkdir()
        with self.assertRaises(BilqisError):
            load_bamf_generation(self.run / "bamf-state.json")
        self.assertFalse((self.run / ".bamf-pointer.lock").exists())

    def test_initial_pointer_lock_repairs_failed_durability_before_yield(self):
        self.run.mkdir()
        real_fsync = publication_storage.os.fsync
        calls = 0

        def fail_once(fd):
            nonlocal calls
            calls += 1
            if calls == 1:
                raise OSError("durability failure")
            return real_fsync(fd)

        entered = []
        with patch.object(publication_storage.os, "fsync", side_effect=fail_once), \
                self.assertRaises(OSError):
            with publication_storage._initial_generation_pointer_lock(self.run):
                entered.append("first")
        self.assertEqual(entered, [])
        self.assertTrue((self.run / ".bamf-pointer.lock").is_file())

        with publication_storage._initial_generation_pointer_lock(self.run):
            entered.append("retry")
        self.assertEqual(entered, ["retry"])

    def test_pointer_lock_durability_error_survives_unlock_failure(self):
        self.run.mkdir()
        durability = OSError("durability failure")
        real_flock = publication_storage.fcntl.flock

        def fail_unlock(fd, operation):
            if operation == publication_storage.fcntl.LOCK_UN:
                raise OSError("unlock failure")
            return real_flock(fd, operation)

        with patch.object(publication_storage.os, "fsync", side_effect=durability), \
                patch.object(publication_storage.fcntl, "flock", side_effect=fail_unlock), \
                self.assertRaises(OSError) as failure:
            with publication_storage._initial_generation_pointer_lock(self.run):
                self.fail("durability failure must precede owner body")
        self.assertIs(failure.exception, durability)
        self.assertIn(
            "BAMF_POINTER_LOCK_RELEASE_FAILED:OSError",
            getattr(durability, "__notes__", ()))

    def test_pointer_lock_reopen_repeats_file_and_directory_fsync(self):
        self.run.mkdir()
        directory_syncs = []
        real_directory_sync = publication_storage._fsync_directory
        with publication_storage._initial_generation_pointer_lock(self.run):
            pass
        with patch.object(
                publication_storage, "_fsync_directory",
                side_effect=lambda path: directory_syncs.append(Path(path))):
            with publication_storage._pointer_lock(self.run):
                pass
        self.assertEqual(directory_syncs, [self.run])
        real_directory_sync(self.run)

    def test_stage_root_publish_and_child_cleanup_are_durable(self):
        self.run.mkdir()
        syncs = []
        with patch.object(
                publication_storage, "_fsync_directory",
                side_effect=lambda path: syncs.append(Path(path))):
            stage = publication_storage._stage(self.run)
            self.assertEqual(syncs, [self.run / ".bamf-staging", self.run])
            stage.mkdir()
            (stage / "partial").write_text("x")
            publication_storage._remove_stage(stage)
        self.assertEqual(syncs[-1], self.run / ".bamf-staging")
        self.assertFalse(stage.exists())

    def test_symlinked_bundle_root_rejects_before_external_bundle_write(self):
        self.run.mkdir()
        outside = self.root / "outside-bundles"
        outside.mkdir()
        (self.run / "bamf-bundles").symlink_to(outside, target_is_directory=True)

        with self.assertRaises(BilqisError):
            self.publish(candidate(parent_state()))

        self.assertEqual(tuple(outside.iterdir()), ())
        self.assertFalse((self.run / "bamf-state.json").exists())

    def test_nested_bundle_alias_cannot_redirect_cold_load(self):
        published = self.publish(candidate(parent_state()))
        source = self.run / published["bundle"]
        outside = self.root / "outside"
        outside.mkdir()
        shutil.copytree(source, outside / published["manifest_sha256"])
        shutil.rmtree(source)
        (self.run / "bamf-bundles" / "alias").symlink_to(
            outside, target_is_directory=True)
        pointer_path = self.run / "bamf-state.json"
        pointer = json.loads(pointer_path.read_text())
        pointer["bundle"] = "bamf-bundles/alias/" + published["manifest_sha256"]
        pointer_path.write_text(json.dumps(pointer))

        with self.assertRaises(BilqisError):
            load_bamf_generation(pointer_path)

    def test_pointer_requires_exact_canonical_bundle_spelling(self):
        published = self.publish(candidate(parent_state()))
        pointer_path = self.run / "bamf-state.json"
        pointer = json.loads(pointer_path.read_text())
        digest = published["manifest_sha256"]
        for spelling in (
                f"bamf-bundles//{digest}",
                f"bamf-bundles/./{digest}",
                f"bamf-bundles/{digest}/"):
            with self.subTest(spelling=spelling):
                pointer["bundle"] = spelling
                pointer_path.write_text(json.dumps(pointer))
                with self.assertRaises(BilqisError):
                    load_bamf_generation(pointer_path)

    def test_pointer_written_before_outbox_crash_replays_exactly_once(self):
        source = candidate(parent_state())
        with shape_patch(), patch.object(mlx_checkpoint, "assert_headroom"), \
                patch.object(publication, "reconcile_bamf_outbox", side_effect=RuntimeError("crash")):
            with self.assertRaisesRegex(RuntimeError, "crash"):
                publish_candidate(self.run, source)
        self.assertTrue((self.run / "bamf-state.json").is_file())
        with shape_patch():
            first = load_bamf_generation(self.run / "bamf-state.json")
            second = load_bamf_generation(self.run / "bamf-state.json")
        self.assertEqual(first.retained_state.optimizer_step, 0)
        self.assertEqual(second.retained_state.optimizer_step, 0)
        events = [json.loads(line) for line in (self.run / "events.jsonl").read_text().splitlines()]
        self.assertEqual(len(events), 1)
        self.assertEqual(events[0]["event"], "FIXTURE_GENESIS")

    def test_competing_same_generation_cannot_overwrite_pointer(self):
        first = self.publish(candidate(parent_state()))
        from bilqis_mlx.runtime.bamf_bundle import publish_initial_generation
        from bilqis_mlx.runtime.tests.custody.bamf_bundle.helpers import (
            genesis_preparation,
        )
        with shape_patch(), patch.object(mlx_checkpoint, "assert_headroom"):
            different = genesis_preparation(run_seed=18)
            with self.assertRaises(BilqisError):
                publish_initial_generation(self.run, different, reserve_gib=0.)
        self.assertEqual(
            json.loads((self.run / "bamf-state.json").read_text())["manifest_sha256"],
            first["manifest_sha256"])

    def test_second_process_holding_writer_lock_fails_before_pointer_change(self):
        script = (
            "import fcntl,os,sys,pathlib; "
            "root=pathlib.Path(sys.argv[1]); root.mkdir(parents=True,exist_ok=True); "
            "fd=os.open(root/'.bamf-pointer.lock',os.O_RDWR|os.O_CREAT,0o600); "
            "fcntl.flock(fd,fcntl.LOCK_EX); print('locked',flush=True); "
            "sys.stdin.readline(); fcntl.flock(fd,fcntl.LOCK_UN); os.close(fd)"
        )
        process = subprocess.Popen(
            [sys.executable, "-c", script, str(self.run)], stdin=subprocess.PIPE,
            stdout=subprocess.PIPE, text=True)
        try:
            self.assertEqual(process.stdout.readline().strip(), "locked")
            with self.assertRaises(BilqisError):
                self.publish(candidate(parent_state()))
            self.assertFalse((self.run / "bamf-state.json").exists())
        finally:
            process.stdin.write("\n")
            process.stdin.flush()
            process.wait(timeout=5)

    def test_successor_rejects_pointer_manifest_lineage_mismatch(self):
        first = self.publish(candidate(parent_state()))
        pointer_path = self.run / "bamf-state.json"
        pointer = json.loads(pointer_path.read_text())
        pointer["run_id"] = "fixture-run-forged"
        pointer_path.write_text(json.dumps(pointer))
        successor = replace(
            candidate(
                accepted_state(parent_state()), 1, first["manifest_sha256"]),
            run_id="fixture-run-forged")

        with self.assertRaises(BilqisError):
            self.publish(successor)


if __name__ == "__main__":
    unittest.main()
