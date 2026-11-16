"""Regression coverage for detached-run source isolation."""
from __future__ import annotations

import json
from pathlib import Path
from types import SimpleNamespace
import subprocess
import sys
import tempfile
import unittest

from scripts.bamf.detached_long_run import (
    SOURCE_MUTATED_EXIT, _snapshot_workdir, _worker,
)


class DetachedLongRunTests(unittest.TestCase):
    def test_snapshot_preserves_internal_broken_symlink_but_rejects_escape(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            source = root / "source"
            source.mkdir()
            (source / "internal.py").symlink_to("missing.py")

            snapshot = root / "snapshot"
            _snapshot_workdir(source, snapshot)
            self.assertTrue((snapshot / "internal.py").is_symlink())
            self.assertEqual((snapshot / "internal.py").readlink(), Path("missing.py"))

        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            source = root / "source"
            source.mkdir()
            (source / "escape.py").symlink_to("../outside.py")
            with self.assertRaisesRegex(RuntimeError, "escapes workdir"):
                _snapshot_workdir(source, root / "snapshot")

    def test_snapshot_child_cannot_see_later_worktree_edits(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            source = root / "source"
            snapshot = root / "snapshot"
            source.mkdir()
            (source / "subject.py").write_text("VALUE = 'before'\n", encoding="utf-8")
            (source / "probe.py").write_text(
                "from subject import VALUE\nprint(VALUE)\n", encoding="utf-8")

            receipt = _snapshot_workdir(source, snapshot)
            (source / "subject.py").write_text("VALUE = 'after'\n", encoding="utf-8")

            completed = subprocess.run(
                [sys.executable, "-B", "probe.py"],
                cwd=snapshot,
                check=False,
                capture_output=True,
                text=True,
            )

            self.assertEqual(completed.returncode, 0, completed.stderr)
            self.assertEqual(completed.stdout.strip(), "before")
            self.assertEqual(receipt["source_sha256"], receipt["snapshot_sha256"])

    def test_git_snapshot_is_a_real_worktree_and_preserves_dirty_surface(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            source = root / "source"
            snapshot = root / "snapshot"
            source.mkdir()
            subprocess.run(["git", "init", "-q"], cwd=source, check=True)
            subprocess.run(["git", "config", "user.email", "tests@example.invalid"],
                           cwd=source, check=True)
            subprocess.run(["git", "config", "user.name", "Detached Tests"],
                           cwd=source, check=True)
            (source / "subject.py").write_text("VALUE = 'committed'\n", encoding="utf-8")
            (source / ".gitignore").write_text("vendor/example/runs/\n", encoding="utf-8")
            (source / "vendor" / "example").mkdir(parents=True)
            (source / "vendor" / "example" / "tracked.txt").write_text(
                "tracked\n", encoding="utf-8")
            subprocess.run(["git", "add", "subject.py"], cwd=source, check=True)
            subprocess.run(
                ["git", "add", ".gitignore", "vendor/example/tracked.txt"],
                cwd=source, check=True)
            subprocess.run(["git", "commit", "-qm", "seed"], cwd=source, check=True)
            (source / "subject.py").write_text("VALUE = 'dirty'\n", encoding="utf-8")
            (source / "untracked.txt").write_text("present\n", encoding="utf-8")
            runs = source / "vendor" / "example" / "runs"
            runs.mkdir()
            (runs / "checkpoint.bin").write_bytes(b"historical evidence")
            venv = source / ".venv"
            (venv / "bin").mkdir(parents=True)
            (venv / "bin" / "python").write_text("#!/bin/sh\n", encoding="utf-8")

            receipt = _snapshot_workdir(source, snapshot)

            self.assertTrue((snapshot / ".git").is_file())
            self.assertEqual(
                subprocess.check_output(
                    ["git", "rev-parse", "--show-toplevel"], cwd=snapshot, text=True
                ).strip(),
                str(snapshot.resolve()),
            )
            self.assertEqual((snapshot / "subject.py").read_text(), "VALUE = 'dirty'\n")
            self.assertEqual((snapshot / "untracked.txt").read_text(), "present\n")
            self.assertEqual(
                (snapshot / "vendor" / "example" / "tracked.txt").read_text(),
                "tracked\n")
            self.assertEqual(
                (snapshot / "vendor" / "example" / "runs" / "checkpoint.bin").read_bytes(),
                b"historical evidence")
            self.assertTrue((snapshot / ".venv").is_symlink())
            self.assertEqual(receipt["source_sha256"], receipt["snapshot_sha256"])

    def test_worker_allows_private_generated_outputs(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            source = root / "source"
            snapshot = root / "snapshot"
            (source / "lib" / "ithkuil").mkdir(parents=True)
            (source / "subject.py").write_text("VALUE = 'before'\n", encoding="utf-8")
            snapshot_receipt = _snapshot_workdir(source, snapshot)
            receipt = root / "receipt.json"
            args = SimpleNamespace(
                label="private-output-test",
                workdir=snapshot,
                source_workdir=source,
                source_sha256=snapshot_receipt["source_sha256"],
                snapshot_sha256=snapshot_receipt["snapshot_sha256"],
                log=root / "run.log",
                receipt=receipt,
                pid_file=root / "pid",
                no_notify=True,
                command=[
                    sys.executable, "-B", "-c",
                    "from pathlib import Path; "
                    "p=Path('lib/ithkuil/_private/curriculum_frontier'); "
                    "p.mkdir(parents=True); (p/'plan.json').write_text('{}\\n')",
                ],
            )

            self.assertEqual(_worker(args), 0)
            result = json.loads(receipt.read_text(encoding="utf-8"))
            self.assertEqual(result["status"], "PASS")
            self.assertFalse(result["source_mutated"])
            self.assertNotEqual(
                result["snapshot_sha256"], result["final_snapshot_sha256"])

    def test_worker_allows_generated_run_state_without_hiding_source_mutation(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            source = root / "source"
            snapshot = root / "snapshot"
            (source / "vendor" / "legacy-v16" / "runs" / "seed").mkdir(parents=True)
            (source / "vendor" / "legacy-v16" / "runs" / "seed" / "state.json").write_text(
                "{}\n", encoding="utf-8")
            (source / "subject.py").write_text("VALUE = 'before'\n", encoding="utf-8")
            snapshot_receipt = _snapshot_workdir(source, snapshot)
            receipt = root / "receipt.json"
            args = SimpleNamespace(
                label="run-output-test",
                workdir=snapshot,
                source_workdir=source,
                source_sha256=snapshot_receipt["source_sha256"],
                snapshot_sha256=snapshot_receipt["snapshot_sha256"],
                log=root / "run.log",
                receipt=receipt,
                pid_file=root / "pid",
                no_notify=True,
                command=[
                    sys.executable, "-B", "-c",
                    "from pathlib import Path; "
                    "p=Path('runs/disposable'); p.mkdir(parents=True); "
                    "(p/'state.json').write_text('{}\\n'); "
                    "q=Path('vendor/legacy-v16/runs/generated'); q.mkdir(parents=True); "
                    "(q/'state.json').write_text('{}\\n')",
                ],
            )

            self.assertEqual(_worker(args), 0)
            result = json.loads(receipt.read_text(encoding="utf-8"))
            self.assertEqual(result["status"], "PASS")
            self.assertFalse(result["source_mutated"])
            self.assertNotEqual(
                result["snapshot_sha256"], result["final_snapshot_sha256"])
            self.assertEqual((source / "subject.py").read_text(), "VALUE = 'before'\n")

    def test_worker_allows_testmon_runtime_database(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            source = root / "source"
            snapshot = root / "snapshot"
            source.mkdir()
            (source / "subject.py").write_text("VALUE = 'before'\n", encoding="utf-8")
            snapshot_receipt = _snapshot_workdir(source, snapshot)
            receipt = root / "receipt.json"
            args = SimpleNamespace(
                label="testmon-output-test",
                workdir=snapshot,
                source_workdir=source,
                source_sha256=snapshot_receipt["source_sha256"],
                snapshot_sha256=snapshot_receipt["snapshot_sha256"],
                log=root / "run.log",
                receipt=receipt,
                pid_file=root / "pid",
                no_notify=True,
                command=[
                    sys.executable, "-B", "-c",
                    "from pathlib import Path; Path('.testmondata').write_bytes(b'cache')",
                ],
            )

            self.assertEqual(_worker(args), 0)
            result = json.loads(receipt.read_text(encoding="utf-8"))
            self.assertEqual(result["status"], "PASS")
            self.assertFalse(result["source_mutated"])
            self.assertNotEqual(
                result["snapshot_sha256"], result["final_snapshot_sha256"])

    def test_worker_fails_if_command_mutates_snapshot_source(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            source = root / "source"
            snapshot = root / "snapshot"
            source.mkdir()
            (source / "subject.py").write_text("VALUE = 'before'\n", encoding="utf-8")
            snapshot_receipt = _snapshot_workdir(source, snapshot)
            receipt = root / "receipt.json"
            args = SimpleNamespace(
                label="mutation-test",
                workdir=snapshot,
                source_workdir=source,
                source_sha256=snapshot_receipt["source_sha256"],
                snapshot_sha256=snapshot_receipt["snapshot_sha256"],
                log=root / "run.log",
                receipt=receipt,
                pid_file=root / "pid",
                no_notify=True,
                command=[
                    sys.executable, "-B", "-c",
                    "from pathlib import Path; Path('subject.py').write_text('changed\\n')",
                ],
            )

            self.assertEqual(_worker(args), SOURCE_MUTATED_EXIT)
            result = json.loads(receipt.read_text(encoding="utf-8"))
            self.assertEqual(result["status"], "FAIL")
            self.assertTrue(result["source_mutated"])
            self.assertEqual(result["command_returncode"], 0)


if __name__ == "__main__":
    unittest.main()
