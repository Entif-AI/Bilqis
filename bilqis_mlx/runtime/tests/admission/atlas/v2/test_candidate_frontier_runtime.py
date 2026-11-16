from dataclasses import replace
from pathlib import Path
import sqlite3
from tempfile import TemporaryDirectory
import unittest
from unittest.mock import patch

from bilqis_mlx.data_plane import DataPlane
from bilqis_mlx.runtime import atlas_flywheel_runtime
from bilqis_mlx.runtime.atlas_flywheel_runtime import _candidate_frontier
from bilqis_mlx.runtime import planner_frontier_trust


_FACTORY_RELEASE_A = "a" * 64
_FACTORY_RELEASE_B = "b" * 64


class CandidateFrontierRuntimeTests(unittest.TestCase):
    def setUp(self):
        self.temporary = TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        root = Path(self.temporary.name)
        self.run_dir = root / "run"
        self.run_dir.mkdir()
        self.plane = DataPlane(root / "data-plane.sqlite3")
        self.addCleanup(self.plane.close)
        self.plane_patch = patch.object(
            planner_frontier_trust, "data_plane", return_value=self.plane)
        self.plane_patch.start()
        self.addCleanup(self.plane_patch.stop)

    def _count_builder(self):
        original = atlas_flywheel_runtime.subprocess.run
        calls = []

        def counted(*args, **kwargs):
            calls.append(args[0])
            return original(*args, **kwargs)

        return calls, patch.object(
            atlas_flywheel_runtime.subprocess, "run", side_effect=counted)

    def test_unchanged_frontier_reuses_trusted_release_without_builder(self):
        calls, builder = self._count_builder()
        progress = []
        with builder:
            first = _candidate_frontier(
                self.run_dir, _FACTORY_RELEASE_A, progress=progress.append)
            second = _candidate_frontier(
                self.run_dir, _FACTORY_RELEASE_A, progress=progress.append)

        self.assertEqual(first, second)
        self.assertEqual(first.release_sha256, second.release_sha256)
        self.assertEqual(len(calls), 1)
        self.assertEqual(progress, [
            "planner: rebuilding source candidate frontier",
            "planner: reusing source candidate frontier",
        ])
        self.assertEqual(len(first.candidates), 240)
        self.assertGreater(len(first.senses), 0)

    def test_factory_release_change_forces_new_trust_key_and_rebuild(self):
        calls, builder = self._count_builder()
        with builder:
            first = _candidate_frontier(self.run_dir, _FACTORY_RELEASE_A)
            second = _candidate_frontier(self.run_dir, _FACTORY_RELEASE_B)

        self.assertEqual(first, second)
        self.assertEqual(len(calls), 2)
        self.assertIsNotNone(planner_frontier_trust.load_planner_frontier_trust(
            first.builder_sha256, first.input_digest, _FACTORY_RELEASE_A))
        self.assertIsNotNone(planner_frontier_trust.load_planner_frontier_trust(
            second.builder_sha256, second.input_digest, _FACTORY_RELEASE_B))

    def test_builder_or_source_input_identity_change_forces_rebuild(self):
        baseline = _candidate_frontier(self.run_dir, _FACTORY_RELEASE_A)
        identities = (
            ("d" * 64, baseline.input_digest),
            (baseline.builder_sha256, "e" * 64),
        )
        for builder_sha256, input_digest in identities:
            with self.subTest(builder=builder_sha256, input=input_digest):
                changed = replace(
                    baseline,
                    builder_sha256=builder_sha256,
                    input_digest=input_digest,
                    release_sha256="f" * 64,
                )
                changed = replace(changed, release_sha256=changed.expected_digest())
                changed.verify()
                calls = []
                with patch.object(
                        atlas_flywheel_runtime,
                        "candidate_frontier_source_identity",
                        return_value=(builder_sha256, input_digest)), patch.object(
                            atlas_flywheel_runtime, "load_candidate_frontier",
                            return_value=changed), patch.object(
                                atlas_flywheel_runtime.subprocess, "run",
                                side_effect=lambda *args, **kwargs: calls.append(args[0])):
                    result = _candidate_frontier(
                        self.run_dir, _FACTORY_RELEASE_A)
                self.assertEqual(result, changed)
                self.assertEqual(len(calls), 1)

    def test_local_cache_tamper_rebuilds_then_matches_immutable_trust(self):
        calls, builder = self._count_builder()
        with builder:
            first = _candidate_frontier(self.run_dir, _FACTORY_RELEASE_A)
            candidate_pool = self.run_dir / "candidate-frontier" / "candidate_pool.csv"
            candidate_pool.write_text(
                candidate_pool.read_text(encoding="utf-8") + "\n",
                encoding="utf-8")
            second = _candidate_frontier(self.run_dir, _FACTORY_RELEASE_A)

        self.assertEqual(first, second)
        self.assertEqual(len(calls), 2)

    def test_missing_local_cache_rebuilds_against_existing_external_trust(self):
        calls, builder = self._count_builder()
        with builder:
            first = _candidate_frontier(self.run_dir, _FACTORY_RELEASE_A)
            for path in sorted(
                    (self.run_dir / "candidate-frontier").iterdir(), reverse=True):
                path.unlink()
            (self.run_dir / "candidate-frontier").rmdir()
            second = _candidate_frontier(self.run_dir, _FACTORY_RELEASE_A)

        self.assertEqual(first, second)
        self.assertEqual(len(calls), 2)

    def test_trust_publication_is_idempotent_and_conflicts_fail_closed(self):
        release = _candidate_frontier(self.run_dir, _FACTORY_RELEASE_A)
        first = planner_frontier_trust.publish_planner_frontier_trust(
            release, _FACTORY_RELEASE_A)
        second = planner_frontier_trust.publish_planner_frontier_trust(
            release, _FACTORY_RELEASE_A)
        self.assertEqual(first, second)

        changed = replace(release, output_digest="c" * 64, release_sha256="d" * 64)
        changed = replace(changed, release_sha256=changed.expected_digest())
        changed.verify()
        with self.assertRaises(ValueError):
            planner_frontier_trust.publish_planner_frontier_trust(
                changed, _FACTORY_RELEASE_A)

        with self.assertRaises(sqlite3.IntegrityError):
            self.plane._db.execute(
                "UPDATE bamf_planner_frontier_trust SET output_digest=? "
                "WHERE trust_key_sha256=?",
                ("d" * 64, first.trust_key_sha256),
            )


if __name__ == "__main__":
    unittest.main()
