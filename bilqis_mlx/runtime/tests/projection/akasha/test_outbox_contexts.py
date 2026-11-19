"""Context-native C09 requalification projection into the C10 outbox."""
from pathlib import Path
import sqlite3
from tempfile import TemporaryDirectory
from types import MappingProxyType, SimpleNamespace
import unittest
from unittest.mock import patch

from bilqis_mlx.errors import BilqisError
from bilqis_mlx.runtime.akasha_outbox import (
    AkashaEventKind,
    append_context_requalification,
    pending_events,
    read_outbox,
)
from bilqis_mlx.runtime.atlas_requalification import (
    CapabilitySupport,
    RequalificationLedger,
    RequalificationStatus,
    TargetedSourceTask,
)
from bilqis_mlx.runtime.accepted_correction_runtime import (
    AcceptedCorrectionRuntime,
)
from bilqis_mlx.runtime.accepted_corrections import (
    AcceptedRuntimeHost, ContextRevalidationFrontier, _reset_accepted_correction_runtime_for_tests,
)
from bilqis_mlx.runtime.accepted_correction_ledger import (
    CONTEXT_INVALIDATION_EVENT, read_records,
)
from bilqis_mlx.runtime.accepted_stale_replay_runtime import (
    _flush_context_requalifications,
)
from bilqis_mlx.runtime.bamf_bundle import admission
from bilqis_mlx.runtime.bamf_bundle.accepted_runtime import _reset_execution_cache_owner_for_tests
from bilqis_mlx.runtime.tests.correction.capability_support_owner_support import (
    CapabilitySupportOwnerFixture, IMMEDIATE_DEPENDENCIES,
)
from bilqis_mlx.runtime.tests.correction import (
    capability_support_owner_support as support_fixture,
)
from bilqis_mlx.runtime.tests.custody.bamf_bundle.authority.correction_runtime.temporal_support import (
    source_owned_temporal_case,
)
from bilqis_mlx.runtime.tests.custody.bamf_bundle.authority.accepted_context_revalidation_support import (
    AUTHORITY, signed_context_result,
)
from bilqis_mlx.runtime.tests.custody.bamf_bundle.helpers import shape_patch
from bilqis_mlx.semantics.cognitive_dependencies import DependencyKind, DependencyRef


CONTEXT_EVENT_ID = "b" * 64
CONTEXT_RECEIPT_ID = "c" * 64
GENERATION = "d" * 64
TEMPORAL_IDENTITY = MappingProxyType({
    "source_time": 10,
    "effective_time": 20,
    "observed_at": 15,
    "recorded_at": 16,
    "authority_registry_sha256": "e" * 64,
    "schema_version": "bilqis.source-context-temporal-identity/v1",
})


def _ledger(
    status=RequalificationStatus.REQUALIFICATION_REQUIRED, *, pending=True,
):
    support = CapabilitySupport(
        capability_id="capability:context",
        support_artifact_ids=("capability:context",),
        source_anchor_ids=("source:context",),
        retained_generation_sha256=GENERATION,
        observation_ids=("observation:context",),
        status=status,
    )
    task = TargetedSourceTask.from_context(support, CONTEXT_EVENT_ID)
    return RequalificationLedger(
        (support,), pending_source_tasks=(task,) if pending else ()), task


def _pending_ledger():
    return _ledger()


def _context_record(context_event_id=CONTEXT_EVENT_ID):
    return {
        "event": "BAMF_C09_CONTEXT_INVALIDATION",
        "event_id": CONTEXT_RECEIPT_ID,
        "context_invalidation": {"context_event_id": context_event_id},
        "source_temporal_identity": dict(TEMPORAL_IDENTITY),
    }


class AkashaOutboxContextTests(unittest.TestCase):
    @patch(
        "bilqis_mlx.runtime.akasha_outbox.contexts._accepted_context_invalidation",
        return_value=(
            _context_record(),
            SimpleNamespace(source_time=10, effective_time=20,
                            observed_at=15, recorded_at=16),
        ),
    )
    def test_context_task_enqueues_exactly_once_with_source_owned_time(
        self, _accepted,
    ):
        ledger, task = _ledger()
        with TemporaryDirectory() as folder:
            path = Path(folder) / "outbox.sqlite3"
            run_dir = Path(folder)
            self.assertEqual(
                append_context_requalification(
                    path, run_dir, GENERATION, task, ledger),
                1,
            )
            self.assertEqual(
                append_context_requalification(
                    path, run_dir, GENERATION, task, ledger),
                0,
            )
            event = pending_events(path)[0]
            self.assertIs(event.kind, AkashaEventKind.REQUALIFICATION)
            self.assertEqual(event.subject_id, task.capability_id)
            self.assertEqual(event.source_receipt_sha256, CONTEXT_RECEIPT_ID)
            self.assertEqual(
                (event.source_time, event.effective_time,
                 event.observed_at, event.recorded_at),
                (10, 20, 15, 16),
            )
            self.assertIn(CONTEXT_EVENT_ID, event.payload_json)
            self.assertIn(task.task_id, event.payload_json)
            self.assertEqual(len(read_outbox(path)), 1)

    @patch(
        "bilqis_mlx.runtime.akasha_outbox.contexts._accepted_context_invalidation",
        side_effect=lambda _run, _manifest, event_id: (
            _context_record(event_id),
            SimpleNamespace(source_time=10, effective_time=20,
                            observed_at=15, recorded_at=16),
        ),
    )
    def test_context_task_rejects_support_drift(self, _accepted):
        ledger, task = _ledger()
        with TemporaryDirectory() as folder:
            path = Path(folder) / "outbox.sqlite3"
            qualified, _ = _ledger(RequalificationStatus.QUALIFIED)
            with self.assertRaises(BilqisError):
                append_context_requalification(
                    path, Path(folder), GENERATION, task, qualified)

    @patch(
        "bilqis_mlx.runtime.akasha_outbox.contexts._accepted_context_invalidation",
        return_value=(
            _context_record(),
            SimpleNamespace(source_time=10, effective_time=20,
                            observed_at=15, recorded_at=16),
        ),
    )
    def test_context_task_must_be_pending_in_c09_ledger(self, _accepted):
        ledger, task = _ledger(pending=False)
        with TemporaryDirectory() as folder, self.assertRaises(BilqisError) as caught:
            append_context_requalification(
                Path(folder) / "outbox.sqlite3", Path(folder),
                GENERATION, task, ledger)
        self.assertEqual(
            caught.exception.context["reason"],
            "BAMF_C10_CONTEXT_REQUALIFICATION_ARGUMENT_INVALID",
        )

    @patch(
        "bilqis_mlx.runtime.accepted_correction_ledger.read_records",
        return_value=(_context_record(), _context_record()),
    )
    def test_duplicate_durable_context_receipt_fails_closed(self, _records):
        ledger, task = _ledger()
        with TemporaryDirectory() as folder, self.assertRaises(BilqisError) as caught:
            append_context_requalification(
                Path(folder) / "outbox.sqlite3", Path(folder),
                GENERATION, task, ledger)
        self.assertEqual(
            caught.exception.context["reason"],
            "BAMF_C10_CONTEXT_RECEIPT_REQUIRED",
        )

    @patch("bilqis_mlx.runtime.akasha_outbox.append_context_requalification")
    def test_cold_flush_projects_v2_but_never_fabricates_v1_time(self, append):
        ledger, task = _pending_ledger()
        retained = type("Retained", (), {
            "run_dir": Path("/tmp/bamf-911-context"),
            "manifest_sha256": GENERATION,
        })()
        v2 = _context_record()
        v2["context_invalidation"]["schema_version"] = (
            "bilqis.c09-context-invalidation/v2")
        _flush_context_requalifications(retained, ledger, (v2,))
        append.assert_called_once_with(
            retained.run_dir / "akasha-outbox.sqlite3",
            retained.run_dir,
            GENERATION,
            task,
            ledger,
        )

        append.reset_mock()
        v1 = _context_record()
        v1["context_invalidation"]["schema_version"] = (
            "bilqis.c09-context-invalidation/v1")
        _flush_context_requalifications(retained, ledger, (v1,))
        append.assert_not_called()
        with self.assertRaises(BilqisError):
            _flush_context_requalifications(retained, ledger, ())


class AkashaOutboxContextIntegrationTests(CapabilitySupportOwnerFixture):
    def _training_custody(self):
        files = {}
        for relative in ("bamf-bundles", "bamf-acceptance"):
            root = self.run / relative
            for path in sorted(root.rglob("*")):
                if path.is_file():
                    files[str(path.relative_to(self.run))] = path.read_bytes()
        files["bamf-state.json"] = (self.run / "bamf-state.json").read_bytes()
        with sqlite3.connect(self.root / "plane.sqlite3") as connection:
            nodes = tuple(connection.execute(
                "SELECT * FROM nodes ORDER BY sha256").fetchall())
        return files, nodes

    def test_missing_durable_context_receipt_fails_closed(self):
        published, _authority = self.publish_support()
        ledger, task = _ledger()
        with self.assertRaises(BilqisError) as caught:
            append_context_requalification(
                self.run / "akasha-outbox.sqlite3", self.run,
                published["manifest_sha256"], task, ledger)
        self.assertEqual(
            caught.exception.context["reason"],
            "BAMF_C10_CONTEXT_RECEIPT_REQUIRED",
        )

    def test_live_and_cold_v2_projection_is_exactly_once_and_neural_inert(self):
        case = source_owned_temporal_case()
        old_time = DependencyRef(
            DependencyKind.TIME, "time:asof:context:" + case.previous.digest)
        dependencies = tuple(sorted((
            *(ref for ref in IMMEDIATE_DEPENDENCIES
              if ref.kind is not DependencyKind.TIME),
            old_time,
        )))
        with patch.object(
            support_fixture, "immediate_dependencies", return_value=dependencies,
        ):
            published, _authority = self.publish_support(
                authority_registry=AUTHORITY)
        owner = self.load_support(AUTHORITY)
        before = self._training_custody()

        with shape_patch(AUTHORITY):
            host = AcceptedRuntimeHost(self.run)
            transition = host.record_context_transition(
                case.previous, case.contexts)
        invalidation = transition.invalidations[0]
        record = next(
            item for item in read_records(self.run, published["manifest_sha256"])
            if item["event"] == CONTEXT_INVALIDATION_EVENT)
        result = signed_context_result(
            owner.current_node,
            invalidation=invalidation,
            accepted_event_id=record["event_id"],
            dependencies=tuple(sorted(
                ref for ref in owner.current_node.immediate_dependencies
                if ref != old_time)),
            digest="d" * 64,
            eligible=False,
        )
        with shape_patch(AUTHORITY):
            host.record_context_revalidation(
                ContextRevalidationFrontier((result,)))

        outbox = self.run / "akasha-outbox.sqlite3"
        live = read_outbox(outbox)
        self.assertEqual(len(live), 1)
        event = live[0]
        authority = case.contexts.transition_authority
        self.assertEqual(event.kind, AkashaEventKind.REQUALIFICATION)
        self.assertEqual(event.source_receipt_sha256, record["event_id"])
        self.assertEqual(
            (event.source_time, event.effective_time,
             event.observed_at, event.recorded_at),
            (authority.source_time, authority.effective_time,
             authority.observed_at, authority.recorded_at),
        )

        for path in self.run.glob("akasha-outbox.sqlite3*"):
            path.unlink()
        self.assertEqual(read_outbox(outbox), ())
        _reset_execution_cache_owner_for_tests()
        _reset_accepted_correction_runtime_for_tests()
        cold_owner = self.load_support(AUTHORITY)
        self.assertEqual(read_outbox(outbox), (event,))
        self.assertEqual(
            cold_owner.ledger.pending_source_tasks[0].context_event_id,
            invalidation.event_id,
        )
        self.assertEqual(self._training_custody(), before)


if __name__ == "__main__":
    unittest.main()
