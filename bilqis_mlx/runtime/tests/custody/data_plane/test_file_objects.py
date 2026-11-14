"""Immutable file ownership, racing adoption and directory durability."""
import hashlib
import multiprocessing
import os
from unittest.mock import patch

from bilqis_mlx._data_plane import file_objects
from bilqis_mlx.data_plane import close_data_planes, data_plane
from bilqis_mlx.runtime.tests.custody.data_plane.base import DataPlaneCase, historical_module


def _racing_adopter(source, digest, barrier, results):
    plane = data_plane()
    try:
        barrier.wait(timeout=15)
        results.put(str(plane.adopt_file_object(source, digest)))
    except Exception as error:
        results.put(repr(error))


class FileObjectTests(DataPlaneCase):
    def source(self):
        source = self.root / "source.safetensors"
        source.write_bytes(b"immutable tensor bytes")
        return source, hashlib.sha256(source.read_bytes()).hexdigest()

    def test_adoption_owns_bytes_independently_of_source_aliases(self):
        source, digest = self.source()
        alias = self.root / "alias"
        os.link(source, alias)
        target = data_plane().adopt_file_object(source, digest)
        alias.write_bytes(b"caller changed source")
        self.assertEqual(data_plane().require_file_object(digest), target)
        self.assertEqual(target.read_bytes(), b"immutable tensor bytes")

    def test_require_file_object_reuses_stat_bound_digest_proof(self):
        source, digest = self.source()
        plane = data_plane()
        target = plane.adopt_file_object(source, digest)
        with patch.object(file_objects, "_digest", wraps=file_objects._digest) as digest_file:
            self.assertEqual(plane.require_file_object(digest), target)
            self.assertEqual(plane.require_file_object(digest), target)
        digest_file.assert_not_called()

    def test_competing_install_verifies_and_reuses_winner(self):
        source, digest = self.source()
        plane = data_plane()
        target = plane.file_object_destination(digest)
        link = os.link

        def competing_link(origin, destination):
            link(origin, destination)
            raise FileExistsError(destination)

        with patch.object(file_objects.os, "link", side_effect=competing_link):
            self.assertEqual(plane.adopt_file_object(source, digest), target)
        self.assertEqual(plane.require_file_object(digest), target)

    def test_legacy_competing_installer_cannot_ratify_caller_link(self):
        source, digest = self.source()
        plane = data_plane()
        link = os.link

        def legacy_winner(origin, destination):
            link(source, destination)
            raise FileExistsError(destination)

        with patch.object(file_objects.os, "link", side_effect=legacy_winner):
            target = plane.adopt_file_object(source, digest)
        source.write_bytes(b"legacy writer retains this alias")
        self.assertEqual(plane.require_file_object(digest), target)

    def test_pinned_legacy_loser_fails_safely_and_upgraded_retry_converges(self):
        legacy = historical_module(
            self.root, "deaa8b9dbd277993f884abeea7413f9cb799d945",
            "bilqis_mlx/_data_plane/file_objects.py", "bilqis_mlx._data_plane.legacy_fixture",
            "bd0ac8d7c8488af69e92a837530c129f9d8df7ee9a525de4627f865c8cb218b1")
        source, digest = self.source()
        plane = data_plane()
        link = os.link

        def upgraded_winner(origin, destination):
            with patch.object(file_objects.os, "link", link):
                plane.adopt_file_object(source, digest)
            return link(origin, destination)

        with patch.object(file_objects.os, "link", side_effect=upgraded_winner):
            with self.assertRaises(FileExistsError):
                legacy.DataPlaneFileObjectMixin.adopt_file_object(plane, source, digest)
        target = plane.require_file_object(digest)
        inode = target.stat().st_ino
        self.assertTrue(plane.owns_file_object(digest))
        self.assertEqual(plane.adopt_file_object(source, digest), target)
        self.assertEqual(target.stat().st_ino, inode)
        source.write_bytes(b"failed old writer retains this alias")
        self.assertEqual(plane.require_file_object(digest), target)

    def test_existing_unowned_inode_isolated_from_open_caller_descriptor(self):
        source, digest = self.source()
        plane = data_plane()
        target = plane.file_object_destination(digest)
        target.parent.mkdir(parents=True)
        os.link(source, target)
        replacement_source = self.root / "same-bytes"
        replacement_source.write_bytes(source.read_bytes())
        with source.open("r+b") as caller:
            source.unlink()
            old_inode = target.stat().st_ino
            plane.adopt_file_object(replacement_source, digest)
            self.assertNotEqual(target.stat().st_ino, old_inode)
            caller.write(b"corrupted caller bytes")
            caller.flush()
            self.assertEqual(plane.require_file_object(digest), target)
        owned_inode = target.stat().st_ino
        close_data_planes()
        data_plane().adopt_file_object(replacement_source, digest)
        self.assertEqual(target.stat().st_ino, owned_inode)

    def test_owned_receipt_with_extra_hard_link_is_reisolated_before_reuse(self):
        source, digest = self.source()
        plane = data_plane()
        target = plane.adopt_file_object(source, digest)
        owned_inode = target.stat().st_ino
        alias = self.root / "owned-object-alias"
        os.link(target, alias)

        # Hard-link creation changes ctime on this platform. Refresh the
        # adversarial ownership receipt to match the now-aliased inode so the
        # rejection below is isolated to the single-link ownership predicate.
        linked_state = target.stat()
        with plane.transaction():
            plane._db.execute(
                "INSERT OR REPLACE INTO meta(key,value) VALUES(?,?)",
                (file_objects._OWNER_KEY_PREFIX + digest,
                 file_objects._inode_identity(linked_state)))
        with plane._lock:
            owner = plane._db.execute(
                "SELECT value FROM meta WHERE key=?",
                (file_objects._OWNER_KEY_PREFIX + digest,),
            ).fetchone()

        self.assertEqual(owner, (file_objects._inode_identity(linked_state),))
        self.assertEqual(linked_state.st_nlink, 2)
        self.assertFalse(plane.owns_file_object(digest))

        replacement = plane.adopt_file_object(source, digest)
        self.assertEqual(replacement, target)
        self.assertNotEqual(target.stat().st_ino, owned_inode)
        self.assertEqual(target.stat().st_nlink, 1)
        self.assertTrue(plane.owns_file_object(digest))

        alias.write_bytes(b"caller retained old owned inode")
        self.assertEqual(plane.require_file_object(digest), target)
        self.assertEqual(target.read_bytes(), b"immutable tensor bytes")

    def test_reuse_fsyncs_current_object_inode_independently(self):
        source, digest = self.source()
        plane = data_plane()
        target = plane.adopt_file_object(source, digest)
        synced = []
        fsync = os.fsync

        def sync(fd):
            synced.append(os.fstat(fd).st_ino)
            fsync(fd)

        with patch.object(file_objects.os, "fsync", side_effect=sync):
            plane.adopt_file_object(source, digest)
        self.assertIn(target.stat().st_ino, synced)

    def test_interrupted_ownership_publication_retries_without_trusting_inode(self):
        source, digest = self.source()
        plane = data_plane()
        with patch.object(file_objects, "_fsync_file", side_effect=RuntimeError("crash")):
            with self.assertRaisesRegex(RuntimeError, "crash"):
                plane.adopt_file_object(source, digest)
        self.assertFalse(plane.owns_file_object(digest))
        target = plane.adopt_file_object(source, digest)
        self.assertTrue(plane.owns_file_object(digest))
        self.assertEqual(plane.require_file_object(digest), target)
        self.assertEqual(list(target.parent.iterdir()), [target])

    def test_adoption_syncs_directory_ancestry_including_reuse(self):
        source, digest = self.source()
        plane = data_plane()
        target = plane.file_object_destination(digest)
        for unused in range(2):
            with patch.object(file_objects, "_fsync_directory") as sync:
                plane.adopt_file_object(source, digest)
            synced = [call.args[0] for call in sync.call_args_list]
            for directory in (target.parent, target.parent.parent, self.root.resolve()):
                self.assertIn(directory, synced)

    def test_independent_process_writers_converge_on_one_object(self):
        from bilqis_mlx.runtime.tests.custody.data_plane.test_file_objects import (
            _racing_adopter as process_target,
        )
        source, digest = self.source()
        plane = data_plane()
        context = multiprocessing.get_context("spawn")
        barrier, results = context.Barrier(2), context.Queue()
        workers = [context.Process(target=process_target,
                                   args=(source, digest, barrier, results))
                   for unused in range(2)]
        try:
            for worker in workers:
                worker.start()
            target = plane.file_object_destination(digest)
            self.assertEqual([results.get(timeout=25) for unused in workers],
                             [str(target), str(target)])
            for worker in workers:
                worker.join(timeout=5)
                self.assertEqual(worker.exitcode, 0)
            self.assertEqual(plane.require_file_object(digest), target)
            self.assertEqual(list(target.parent.iterdir()), [target])
        finally:
            for worker in workers:
                if worker.is_alive():
                    worker.terminate()
                    worker.join()
            results.close()
