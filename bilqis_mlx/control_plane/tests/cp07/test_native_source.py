"""Authenticated BAMF history is the CP07 production-source acceptance witness."""
import json
import unittest
from unittest.mock import patch

from bilqis_mlx.errors import BilqisError
from bilqis_mlx.control_plane import ControlPlaneClient, ControlPlaneService, EventFamily
from bilqis_mlx.control_plane.native_contracts import materialized_at, run_ref
from bilqis_mlx.control_plane.native_source import (
    authenticated_history, materialize_native_projection, native_query_catalog,
    native_query_source, refresh_native_events,
)
from bilqis_mlx.mission_control import (
    CandidateDecision, CapabilitySnapshot, LearningEpisode, OperatorView, ResourceSample,
    TeacherSnapshot,
)
from bilqis_mlx.mission_control.projection import MissionControlProjection
from bilqis_mlx.mission_control.query_contracts import QueryFamily, QueryMode, QueryRequest
from bilqis_mlx.runtime.tests.custody.bamf_bundle.helpers import (
    retention_decision,
)
from bilqis_mlx.runtime.bamf_bundle import record_bamf_rejection

from ..support import start_service
from ..observed import test_source as observed_support
from .native_source_support import NativeSourceFixture


class NativeBamfProjectionTests(NativeSourceFixture, unittest.TestCase):

    def test_authenticated_history_materializes_native_cp02_and_rebuilds_cp06(self):
        self.parent()
        source, pointer = self.publish_successor()
        before = (self.run / "bamf-state.json").read_bytes()

        history = authenticated_history(self.run)
        self.assertEqual([item.manifest["generation"] for item in history], [0, 1])
        self.assertEqual(history[-1].manifest_sha256, pointer["manifest_sha256"])

        material = materialize_native_projection(self.run)
        episodes = [record for record in material.records if isinstance(record, LearningEpisode)]
        candidates = [record for record in material.records if isinstance(record, CandidateDecision)]
        capabilities = [record for record in material.records if isinstance(record, CapabilitySnapshot)]
        resources = [record for record in material.records if isinstance(record, ResourceSample)]
        teachers = [record for record in material.records if isinstance(record, TeacherSnapshot)]
        operator_views = [record for record in material.records if isinstance(record, OperatorView)]
        self.assertEqual(len(operator_views), 2)
        self.assertEqual(operator_views[-1].learner_state, "READY")
        self.assertEqual(operator_views[-1].meta.run.generation, 1)
        self.assertEqual(len(episodes), 1)
        self.assertEqual(episodes[0].capability_id, "A.NATIVE")
        self.assertEqual(episodes[0].meta.coverage.value, "PARTIAL")
        self.assertEqual(len(candidates), 1)
        self.assertEqual(candidates[0].outcome.value, "ACCEPTED")
        self.assertEqual(len(capabilities), 1)
        self.assertEqual(capabilities[0].grade_id, "UNKNOWN")
        self.assertEqual(capabilities[0].score_correct.state.value, "MISSING")
        self.assertEqual(capabilities[0].score_total.state.value, "MISSING")
        self.assertEqual(capabilities[0].debt.state.value, "MISSING")
        self.assertEqual(len(resources), 1)
        self.assertEqual(resources[0].memory_used_bytes.state.value, "UNKNOWN")
        self.assertEqual(resources[0].memory_budget_bytes.value, 64 * 1024 ** 3)
        self.assertGreater(resources[0].disk_used_bytes.value, 0)
        self.assertEqual(resources[0].step_rate_per_minute.value, 2.0)
        self.assertEqual(len(teachers), 1)
        self.assertEqual(teachers[0].teacher_identity, history[-1].teacher_state["teacher_identity"])
        self.assertEqual(teachers[0].teacher_epoch, history[-1].teacher_state["teacher_epoch"])
        self.assertEqual(
            teachers[0].strategy_id,
            history[-1].teacher_state["last_visit"]["policy_key"],
        )
        self.assertEqual(teachers[0].attempts.state.value, "MISSING")
        self.assertEqual(teachers[0].accepted.state.value, "MISSING")
        self.assertEqual(teachers[0].rejected.state.value, "MISSING")

        index = self.root / "native-projection.sqlite3"
        projection = MissionControlProjection.rebuild_from_bamf(index, self.run)
        current = projection.catalog().query(QueryRequest(
            QueryFamily.CAPABILITY, run_id=source.run_id,
        ))
        historical = projection.catalog().query(QueryRequest(
            QueryFamily.EPISODE, mode=QueryMode.HISTORICAL,
            run_id=source.run_id, generation=1,
        ))
        self.assertEqual(current.records[0].capability_id, "A.NATIVE")
        generation_gap = projection.catalog().query(QueryRequest(
            QueryFamily.GENERATION, mode=QueryMode.HISTORICAL,
            run_id=source.run_id, generation=1,
        ))
        resource_page = projection.catalog().query(QueryRequest(
            QueryFamily.RESOURCE, mode=QueryMode.HISTORICAL,
            run_id=source.run_id, generation=1,
        ))
        current_resource_page = projection.catalog().query(QueryRequest(
            QueryFamily.RESOURCE, run_id=source.run_id,
        ))
        self.assertEqual(generation_gap.state.value, "UNKNOWN")
        self.assertEqual(resource_page.state.value, "PARTIAL")
        self.assertIsInstance(resource_page.records[0], ResourceSample)
        self.assertEqual(current_resource_page.state.value, "PARTIAL")
        self.assertEqual(current_resource_page.markers, ())
        self.assertIsInstance(current_resource_page.records[0], ResourceSample)
        projected_episode = next(
            record for record in historical.records if isinstance(record, LearningEpisode))
        self.assertEqual(projected_episode.episode_id, episodes[0].episode_id)

        index.unlink()
        rebuilt = MissionControlProjection.rebuild_from_bamf(index, self.run)
        self.assertEqual(rebuilt.catalog().query(QueryRequest(
            QueryFamily.CAPABILITY, run_id=source.run_id,
        )), current)
        self.assertEqual((self.run / "bamf-state.json").read_bytes(), before)


    def test_generation_coordinate_is_never_reinterpreted_as_unix_materialization_time(self):
        self.assertEqual(materialized_at({}, 7), 0)
        self.assertEqual(materialized_at({"recorded_at": 1_800_000_000}, 7), 1_800_000_000)

    def test_event_refresh_skips_full_projection_when_mutable_sources_are_unchanged(self):
        self.parent()
        class FakeService:
            pass

        service = FakeService()
        service.run_dir = self.run
        service._cp07_native_event_ids = set()
        service._cp07_native_run_refs = tuple(
            run_ref(item) for item in authenticated_history(self.run))
        with patch(
                "bilqis_mlx.control_plane.native_source.publish_native_events",
                return_value=(None, ())) as publish:
            self.assertEqual(refresh_native_events(service), ())
            self.assertEqual(publish.call_count, 1)
            self.assertEqual(refresh_native_events(service), ())
            self.assertEqual(publish.call_count, 1)
            (self.run / "trainer-observed.json").write_text("{}")
            self.assertEqual(refresh_native_events(service), ())
            self.assertEqual(publish.call_count, 1)

    def test_query_source_reuses_catalog_until_mutable_source_changes(self):
        self.parent()
        self.publish_successor()
        with patch(
                "bilqis_mlx.control_plane.native_source.materialize_native_projection",
                wraps=materialize_native_projection) as materialize:
            source = native_query_source(self.run)
            first = source()
            self.assertIs(source(), first)
            self.assertEqual(materialize.call_count, 1)
            (self.run / "bamf-state.json").touch()
            second = source()
            self.assertIsNot(second, first)
            self.assertEqual(materialize.call_count, 2)

    def test_query_source_observation_change_does_not_reauthenticate_accepted_history(self):
        self.parent()
        self.publish_successor()
        with patch(
                "bilqis_mlx.control_plane.native_source.authenticated_history",
                wraps=authenticated_history) as authenticate:
            source = native_query_source(self.run)
            source()
            first = authenticate.call_count
            self.assertGreater(first, 0)
            (self.run / "trainer-observed.json").write_text("{}")
            source()
            self.assertEqual(authenticate.call_count, first)

    def test_query_source_observation_refresh_does_not_cold_load_accepted_student(self):
        self.parent()
        source_generation, _pointer = self.publish_successor()
        query_source = native_query_source(self.run)
        query_source()
        row = observed_support.visit(
            run_id=source_generation.run_id,
            parent_manifest_sha256=(self.run / "bamf-state.json").read_text(),
            outcome="COMPLETED",
        )
        pointer = json.loads((self.run / "bamf-state.json").read_text())
        row["parent_manifest_sha256"] = pointer["manifest_sha256"]
        (self.run / "trainer-observed.json").write_text(json.dumps({
            "schema": "bilqis.bamf.trainer-observed/v1",
            "visits": [row],
        }))
        with patch(
                "bilqis_mlx.runtime.bamf_bundle.admission.load_accepted_generation",
                side_effect=AssertionError("observation refresh cold-loaded accepted student")):
            page = query_source().query(QueryRequest(
                QueryFamily.RUN, run_id=source_generation.run_id))
        self.assertIn(page.state.value, {"PRESENT", "PARTIAL"})

    def test_native_query_catalog_exposes_current_operator_view_without_cp06_database(self):
        self.parent()
        source, _pointer = self.publish_successor()
        page = native_query_catalog(self.run).query(QueryRequest(
            QueryFamily.RUN, run_id=source.run_id))
        view = next(record for record in page.records if isinstance(record, OperatorView))
        self.assertEqual(page.state.value, "PRESENT")
        self.assertEqual(view.meta.run.generation, 1)
        self.assertEqual(view.learner_state, "READY")

    def test_native_family_hydration_matrix_distinguishes_present_absent_and_contract_gap(self):
        self.parent()
        source, _pointer = self.publish_successor()
        catalog = native_query_catalog(self.run)

        for family in (QueryFamily.CAPABILITY, QueryFamily.RESOURCE, QueryFamily.TEACHER):
            page = catalog.query(QueryRequest(family, run_id=source.run_id))
            self.assertEqual(page.state.value, "PARTIAL", family.value)
            self.assertGreater(len(page.records), 0, family.value)
            self.assertEqual(page.markers, (), family.value)

        for family in (
                QueryFamily.SCHOOL, QueryFamily.SEMANTIC, QueryFamily.FRAME,
                QueryFamily.NEURAL, QueryFamily.MEMORY, QueryFamily.SALIENCE,
                QueryFamily.CORRECTION):
            page = catalog.query(QueryRequest(family, run_id=source.run_id))
            self.assertEqual(page.state.value, "EMPTY", family.value)
            self.assertEqual(page.coverage.value, "COMPLETE", family.value)
            self.assertEqual(page.records, (), family.value)
            self.assertEqual(page.markers, (), family.value)

        generation = catalog.query(QueryRequest(
            QueryFamily.GENERATION, run_id=source.run_id))
        self.assertEqual(generation.state.value, "UNKNOWN")
        self.assertEqual(generation.coverage.value, "UNKNOWN")
        self.assertEqual(generation.records, ())
        self.assertEqual(len(generation.markers), 1)

    def test_historical_acceptance_tamper_fails_closed(self):
        self.parent()
        source, _pointer = self.publish_successor()
        index = self.root / "tampered.sqlite3"
        projection = MissionControlProjection.rebuild_from_bamf(index, self.run)
        before = projection.catalog().query(QueryRequest(
            QueryFamily.CAPABILITY, run_id=source.run_id))
        history = authenticated_history(self.run)
        parent = history[0]
        acceptance = self.run / "bamf-acceptance" / f"{parent.manifest_sha256}.json"
        raw = acceptance.read_text(encoding="utf-8")
        acceptance.write_text(raw.replace('"generation":0', '"generation":9'), encoding="utf-8")
        with self.assertRaises(BilqisError) as caught:
            MissionControlProjection.rebuild_from_bamf(index, self.run)
        self.assertEqual(
            caught.exception.context.get("reason"),
            "CONTROL_PLANE_NATIVE_HISTORY_ACCEPTANCE_DRIFT",
        )
        self.assertEqual(
            MissionControlProjection(index).catalog().query(QueryRequest(
                QueryFamily.CAPABILITY, run_id=source.run_id)),
            before,
        )

    def test_cp06_rebuild_uses_only_portable_authenticated_run_artifacts(self):
        self.parent()
        source, _pointer = self.publish_successor()
        index = self.root / "artifact-only.sqlite3"
        with patch(
                "bilqis_mlx.data_plane.data_plane",
                side_effect=AssertionError("CP06 reconstruction accessed shared data plane")):
            projection = MissionControlProjection.rebuild_from_bamf(index, self.run)
        current = projection.catalog().query(QueryRequest(
            QueryFamily.CAPABILITY, run_id=source.run_id,
        ))
        self.assertEqual(current.records[0].capability_id, "A.NATIVE")

    def test_subscription_automatically_publishes_new_authenticated_native_events(self):
        self.parent()
        socket = self.root / "native.sock"
        service = ControlPlaneService(
            self.run, socket, event_heartbeat_seconds=0.01,
            event_retention_limit=16, event_queue_limit=16,
        )
        thread = start_service(service)
        try:
            with ControlPlaneClient(socket) as client:
                subscription = client.subscribe_events()
                self.publish_successor()
                observed = []
                while len(observed) < 5:
                    event = next(subscription)
                    if event.schema_version.endswith("event-envelope/v1"):
                        observed.append(event)
                families = {event.event_family for event in observed}
                self.assertTrue({
                    EventFamily.RUN_STATE_CHANGED.value,
                    EventFamily.LESSON_VISIT_COMPLETED.value,
                    EventFamily.CANDIDATE_RETAINED.value,
                    EventFamily.CAPABILITY_CHANGED.value,
                    EventFamily.RESOURCE_HEALTH_SAMPLE.value,
                } <= families)
                ids = [event.event_id for event in observed]
                self.assertEqual(len(ids), len(set(ids)))
                self.assertEqual(refresh_native_events(service), ())
        finally:
            service.shutdown()
            thread.join(2)

    def test_authenticated_rejection_is_projected_without_advancing_learner(self):
        parent = self.parent()
        before = (self.run / "bamf-state.json").read_bytes()
        visit = self.native_visit(parent)
        decision = retention_decision(
            accepted=False, parent=parent.retained_state, retained=parent.retained_state)
        receipt = record_bamf_rejection(self.run, parent, {
            "schema": "bilqis.bamf.c16.3-rejection/v2",
            "visit_id": visit.visit_id,
            "teacher_visit": visit.to_record(),
            "selected_option_id": "option:native",
            "selected_policy_key": visit.policy_key,
            "candidate_optimizer_step": parent.retained_state.optimizer_step + 1,
            "retained_optimizer_step": parent.retained_state.optimizer_step,
            "retention_reason": decision.reason,
            "capability": "A.REJECT",
            "decision": decision.to_record(),
        })
        material = materialize_native_projection(
            self.run, include_live_rejections=True)
        rejected = [
            record for record in material.records
            if isinstance(record, CandidateDecision) and record.outcome.value == "REJECTED"
        ]
        self.assertEqual(len(rejected), 1)
        self.assertEqual(rejected[0].capability_id, "A.REJECT")
        self.assertEqual(rejected[0].reason_code, decision.reason)
        self.assertEqual(rejected[0].candidate_id, decision.candidate_generation)
        self.assertIn(f"bamf-rejection:{receipt}", rejected[0].meta.receipt_refs)
        self.assertEqual((self.run / "bamf-state.json").read_bytes(), before)

        with patch(
                "bilqis_mlx.data_plane.data_plane",
                side_effect=AssertionError("CP06 reconstruction accessed shared data plane")):
            portable = materialize_native_projection(self.run)
        self.assertFalse(any(
            isinstance(record, CandidateDecision) and record.outcome.value == "REJECTED"
            for record in portable.records))

if __name__ == "__main__":
    unittest.main()
