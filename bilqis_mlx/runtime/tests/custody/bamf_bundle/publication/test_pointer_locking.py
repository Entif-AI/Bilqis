"""B13.1 pointer-lock durability and concurrency witnesses."""
from __future__ import annotations

import json
import os
import subprocess
import sys
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import patch

import bilqis_mlx.runtime.bamf_bundle.currentness_transaction as currentness_transaction
import bilqis_mlx.runtime.bamf_bundle.publication.storage as publication_storage
import bilqis_mlx.runtime.mlx_checkpoint as mlx_checkpoint
from bilqis_mlx.errors import BilqisError
from bilqis_mlx.runtime.bamf_bundle import load_bamf_generation
from bilqis_mlx.runtime.tests.custody.bamf_bundle.helpers import (
    candidate,
    parent_state,
    publish_candidate,
    shape_patch,
)


class BamfPointerLockTests(unittest.TestCase):
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

    def test_concurrent_readers_do_not_block_accepted_state_currentness(self):
        published = self.publish(candidate(parent_state()))
        pointer = json.loads((self.run / "bamf-state.json").read_text())
        script = (
            "import fcntl,os,sys,pathlib; "
            "root=pathlib.Path(sys.argv[1]); "
            "fd=os.open(root/'.bamf-pointer.lock',os.O_RDWR); "
            "fcntl.flock(fd,fcntl.LOCK_SH); print('locked',flush=True); "
            "sys.stdin.readline(); fcntl.flock(fd,fcntl.LOCK_UN); os.close(fd)"
        )
        process = subprocess.Popen(
            [sys.executable, "-c", script, str(self.run)], stdin=subprocess.PIPE,
            stdout=subprocess.PIPE, text=True)
        try:
            self.assertEqual(process.stdout.readline().strip(), "locked")
            from bilqis_mlx.runtime.bamf_bundle.accepted_runtime import (
                load_accepted_generation,
            )
            with shape_patch():
                loaded = load_accepted_generation(self.run)
            self.assertEqual(loaded.generation, 0)
            snapshot = currentness_transaction._pointer_snapshot(
                self.run,
                published["manifest_sha256"],
                expected_run_id=pointer["run_id"],
                expected_generation=pointer["generation"],
            )
            self.assertEqual(snapshot[1], pointer["acceptance_sha256"])
        finally:
            process.stdin.write("\n")
            process.stdin.flush()
            process.wait(timeout=5)

    def test_currentness_reader_still_rejects_active_pointer_writer(self):
        published = self.publish(candidate(parent_state()))
        pointer = json.loads((self.run / "bamf-state.json").read_text())
        script = (
            "import fcntl,os,sys,pathlib; "
            "root=pathlib.Path(sys.argv[1]); "
            "fd=os.open(root/'.bamf-pointer.lock',os.O_RDWR); "
            "fcntl.flock(fd,fcntl.LOCK_EX); print('locked',flush=True); "
            "sys.stdin.readline(); fcntl.flock(fd,fcntl.LOCK_UN); os.close(fd)"
        )
        process = subprocess.Popen(
            [sys.executable, "-c", script, str(self.run)], stdin=subprocess.PIPE,
            stdout=subprocess.PIPE, text=True)
        try:
            self.assertEqual(process.stdout.readline().strip(), "locked")
            with self.assertRaises(BilqisError) as caught:
                currentness_transaction._pointer_snapshot(
                    self.run,
                    published["manifest_sha256"],
                    expected_run_id=pointer["run_id"],
                    expected_generation=pointer["generation"],
                )
            self.assertEqual(
                caught.exception.context["reason"], "BAMF_POINTER_WRITER_ACTIVE")
        finally:
            process.stdin.write("\n")
            process.stdin.flush()
            process.wait(timeout=5)


if __name__ == "__main__":
    unittest.main()
