"""CP06 revision, frontier-baseline, corruption, and path safety tests."""
from dataclasses import replace
from pathlib import Path
import sqlite3
from tempfile import TemporaryDirectory
import unittest

from bilqis_mlx.errors import BilqisError
from bilqis_mlx.mission_control.observability import GenerationManifest
from bilqis_mlx.mission_control.operator import OperatorActionReceipt
from bilqis_mlx.mission_control.projection import (
    MissionControlProjection, ProjectionFrontierState,
)
from bilqis_mlx.mission_control.query_contracts import (
    QueryFamily, QueryMode, QueryRequest,
)
from bilqis_mlx.mission_control.tests.samples import SAMPLES


class MissionControlProjectionHistoryTests(unittest.TestCase):
    def test_changed_generation_and_receipt_create_revisioned_state(self):
        with TemporaryDirectory() as temporary:
            projection = MissionControlProjection.create_empty(
                Path(temporary) / "projection.sqlite3")
            old = SAMPLES[14]
            self.assertIs(type(old), GenerationManifest)
            new_run = replace(
                old.meta.run,
                generation=8,
                generation_manifest_sha256="5" * 64,
            )
            new = replace(
                old,
                meta=replace(
                    old.meta,
                    record_id="generation:8",
                    run=new_run,
                    materialized_at=121,
                    observed_at=119,
                    as_of=119,
                    receipt_refs=("receipt:generation:8",),
                ),
                checkpoint_sha256="6" * 64,
                student_sha256="7" * 64,
                optimizer_state_sha256="8" * 64,
                parent_manifest_sha256=old.meta.run.generation_manifest_sha256,
            )
            projection.ingest_records((old, new))
            catalog = projection.catalog()
            old_page = catalog.query(QueryRequest(
                QueryFamily.GENERATION, mode=QueryMode.HISTORICAL,
                generation=7,
            ))
            new_page = catalog.query(QueryRequest(
                QueryFamily.GENERATION, mode=QueryMode.HISTORICAL,
                generation=8,
            ))
            self.assertEqual(
                [item.meta.record_id for item in old_page.records], ["generation"])
            self.assertEqual(
                [item.meta.record_id for item in new_page.records], ["generation:8"])

            receipt = next(
                item for item in SAMPLES if type(item) is OperatorActionReceipt
            )
            pending = replace(
                receipt,
                meta=replace(
                    receipt.meta,
                    materialized_at=119,
                    observed_at=118,
                    as_of=118,
                    receipt_refs=(),
                ),
                state=type(receipt.state).PENDING,
                acknowledged_at=119,
                postcondition_ref=None,
            )
            projection.ingest_records((pending, receipt))
            revisions = projection.revisions(receipt.meta.record_id)
            self.assertEqual(
                [item.state.value for item in revisions], ["PENDING", "COMPLETED"])
            self.assertEqual(projection.stats().revisions, 4)

            ambiguous = replace(
                receipt,
                postcondition_ref="receipt:ambiguous-same-time",
            )
            with self.assertRaises(BilqisError) as identity_conflict:
                projection.ingest_records((ambiguous,))
            self.assertEqual(
                identity_conflict.exception.context["reason"],
                "PROJECTION_RECORD_IDENTITY_CONFLICT",
            )

    def test_frontier_lag_and_divergence_are_explicit(self):
        with TemporaryDirectory() as temporary:
            projection = MissionControlProjection.create_empty(
                Path(temporary) / "projection.sqlite3")
            empty = projection.frontier_status(
                "mission-control", "epoch-a", 2, "a" * 64)
            self.assertEqual(empty.state, ProjectionFrontierState.EMPTY)
            projection.record_frontier(
                "mission-control", "epoch-a", 2, "a" * 64)
            current = projection.frontier_status(
                "mission-control", "epoch-a", 2, "a" * 64)
            stale = projection.frontier_status(
                "mission-control", "epoch-a", 3, "b" * 64)
            diverged = projection.frontier_status(
                "mission-control", "epoch-a", 2, "c" * 64)
            restarted = projection.frontier_status(
                "mission-control", "epoch-b", 1, "d" * 64)
            self.assertEqual(current.state, ProjectionFrontierState.CURRENT)
            self.assertEqual(stale.state, ProjectionFrontierState.STALE)
            self.assertEqual(diverged.state, ProjectionFrontierState.DIVERGED)
            self.assertEqual(restarted.state, ProjectionFrontierState.STALE)
            with self.assertRaises(BilqisError) as baseline_jump:
                projection.record_frontier(
                    "mission-control", "epoch-a", 3, "b" * 64)
            self.assertEqual(
                baseline_jump.exception.context["reason"],
                "PROJECTION_FRONTIER_BASELINE_CONFLICT",
            )
            with self.assertRaises(BilqisError) as epoch_change:
                projection.record_frontier(
                    "mission-control", "epoch-b", 1, "d" * 64)
            self.assertEqual(
                epoch_change.exception.context["reason"],
                "PROJECTION_FRONTIER_BASELINE_CONFLICT",
            )

    def test_incompatible_or_corrupt_index_fails_closed_with_rebuild_guidance(self):
        with TemporaryDirectory() as temporary:
            path = Path(temporary) / "projection.sqlite3"
            MissionControlProjection.create_empty(path)
            with sqlite3.connect(path) as db:
                db.execute(
                    "UPDATE projection_meta SET value = '999' WHERE key = 'schema_version'")
                db.commit()
            with self.assertRaises(BilqisError) as incompatible:
                MissionControlProjection(path)
            self.assertEqual(
                incompatible.exception.context["reason"],
                "PROJECTION_SCHEMA_INCOMPATIBLE_REBUILD_REQUIRED",
            )
            recovered = MissionControlProjection.rebuild(path, SAMPLES[:2])
            self.assertEqual(recovered.stats().active_records, 2)

            path.write_bytes(b"not-a-sqlite-database")
            with self.assertRaises(BilqisError) as corrupt:
                MissionControlProjection(path)
            self.assertEqual(
                corrupt.exception.context["reason"],
                "PROJECTION_CORRUPT_REBUILD_REQUIRED",
            )

    def test_missing_index_and_row_tamper_fail_closed(self):
        with TemporaryDirectory() as temporary:
            path = Path(temporary) / "projection.sqlite3"
            with self.assertRaises(BilqisError) as missing:
                MissionControlProjection(path)
            self.assertEqual(
                missing.exception.context["reason"],
                "PROJECTION_MISSING_REBUILD_REQUIRED",
            )
            projection = MissionControlProjection.rebuild(path, SAMPLES[:2])
            with sqlite3.connect(path) as db:
                db.execute(
                    """UPDATE record_revisions SET payload_json =
                    replace(payload_json, 'READY', 'BROKEN')
                    WHERE record_id = 'run-context'"""
                )
                db.commit()
            with self.assertRaises(BilqisError) as tampered:
                projection.catalog()
            self.assertEqual(
                tampered.exception.context["reason"],
                "PROJECTION_ROW_DIGEST_MISMATCH_REBUILD_REQUIRED",
            )

    def test_symlink_projection_path_is_rejected(self):
        with TemporaryDirectory() as temporary:
            root = Path(temporary)
            target = root / "target.sqlite3"
            MissionControlProjection.create_empty(target)
            link = root / "projection.sqlite3"
            link.symlink_to(target)
            with self.assertRaises(BilqisError) as unsafe:
                MissionControlProjection(link)
            self.assertEqual(
                unsafe.exception.context["reason"], "PROJECTION_PATH_UNSAFE")


if __name__ == "__main__":
    unittest.main()
