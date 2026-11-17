"""Focused tests for extracted native BAMF session bindings."""
from pathlib import Path
from tempfile import TemporaryDirectory
from types import SimpleNamespace
import unittest
from unittest.mock import patch

from bilqis_mlx.runtime.bamf_operator.session import (
    _execution_context, prepare_bamf_visit,
)
from bilqis_mlx.runtime.tests.operator.test_bamf_operator_session import (
    _assert_horizon_result, _candidate_executor, _evidence_receipt,
    _prepare_native_resource_visit,
)


class BamfOperatorNativeSessionTests(unittest.TestCase):
    def setUp(self):
        for name, behavior in (
                ('build_outcome', {'return_value': {'schema': 'routing-fixture'}}),
                ('credited_visit', {'side_effect': lambda visit, outcome: visit}),
                ('carry_credit_to_successor', {
                    'side_effect': lambda visit, successor, parent: successor})):
            patched = patch('bilqis_mlx.runtime.outcomes.issuance.' + name, **behavior)
            patched.start()
            self.addCleanup(patched.stop)

    def test_prepare_visit_accumulates_horizon_before_one_retention_decision(self):
        parent = SimpleNamespace(
            retained_state=SimpleNamespace(optimizer_step=11),
            optimizer_hyperparameters="hparams",
        )
        cache = SimpleNamespace(generation=1, accepted_manifest_sha256="a" * 64)
        context = SimpleNamespace(
            release=object(),
            _accepted_runtime_host=SimpleNamespace(_accepted_cache=cache),
        )
        identity = SimpleNamespace(visit_id="visit:horizon", policy_key="policy:horizon")
        selection = SimpleNamespace(
            status="TEACHER_SELECTED",
            option_id="option:horizon",
            visit=SimpleNamespace(identity=identity),
            offer=SimpleNamespace(
                capability_id="capability:horizon", source_seed=17,
                rows=lambda: ({"id": "row:horizon"},),
            ),
        )
        transactions = []
        execute = _candidate_executor(transactions, self)
        decision = SimpleNamespace(
            accepted=True, to_record=lambda: {"decision": "ACCEPTED"})
        retained = SimpleNamespace(optimizer_step=15)
        successor = object()
        evidence = _evidence_receipt(900, 6, 0.01)
        capture = SimpleNamespace(finalize=lambda **_kwargs: evidence)
        with patch(
                "bilqis_mlx.runtime.bamf_operator.session._execution_context",
                return_value=(parent, context, "atlas", "feature")), patch(
                "bilqis_mlx.runtime.bamf_operator.session.schedule_program_from_executable_release",
                return_value="program"), patch(
                "bilqis_mlx.runtime.bamf_operator.session.accepted_priority_school",
                return_value="school"), patch(
                "bilqis_mlx.runtime.bamf_operator.session.select_foundation_priority_visit",
                return_value=selection), patch(
                "bilqis_mlx.runtime.bamf_operator.session_parts.native_session.bind_accepted_execution_cache",
                return_value=cache), patch(
                "bilqis_mlx.runtime.bamf_operator.session.bind_current_retention_protection_plan",
                return_value="plan") as bind_plan, patch(
                "bilqis_mlx.runtime.bamf_operator.session_parts.native_session.bind_current_retention_source_rows",
                return_value="rows") as bind_rows, patch(
                "bilqis_mlx.runtime.bamf_operator.session_parts.native_session.candidate_step_horizon",
                return_value=4) as horizon, patch(
                "bilqis_mlx.runtime.bamf_operator.session_parts.native_session.rejection_attempt_ordinals",
                return_value=(1, 1)), patch(
                "bilqis_mlx.runtime.bamf_operator.session_parts.native_session.prepare_candidate_evidence_root"), patch(
                "bilqis_mlx.runtime.bamf_operator.session_parts.native_session._Capture",
                return_value=capture) as capture_factory, patch(
                "bilqis_mlx.runtime.bamf_operator.session_parts.native_session.FactoryDeliveryObservation",
                return_value="observation"), patch(
                "bilqis_mlx.runtime.bamf_operator.session_parts.native_session.execute_accepted_priority_candidate",
                side_effect=execute) as execute_candidate, patch(
                "bilqis_mlx.runtime.bamf_operator.session_parts.native_session.evaluate_factory_retention_candidate",
                return_value=SimpleNamespace(
                    candidate_state=retained, parent_state=parent.retained_state)) as evaluate, patch(
                "bilqis_mlx.runtime.bamf_operator.session_parts.native_session.issue_factory_retention_decision",
                return_value=decision) as decide, patch(
                "bilqis_mlx.runtime.bamf_operator.session_parts.native_session.derive_accepted_teacher_successor",
                return_value=successor) as derive, patch(
                "bilqis_mlx.runtime.bamf_operator.session_parts.native_session.bind_factory_baseline_successor",
                return_value=successor), patch(
                "bilqis_mlx.runtime.bamf_operator.championship."
                "bind_accepted_championship_successor",
                return_value=successor), patch(
                "bilqis_mlx.runtime.bamf_operator.session_support.shutil.disk_usage",
                return_value=SimpleNamespace(used=123)):
            prepared = prepare_bamf_visit(Path("/run"), steps_per_visit=16)

        _assert_horizon_result(
            self, prepared, execute_candidate, bind_plan, bind_rows,
            capture_factory, horizon, evaluate, decide, derive, context,
            parent, cache, selection, transactions, evidence)

    def test_resource_observation_reports_semantic_materialization_counts(self):
        from bilqis_mlx.runtime.bamf_operator.session_support import _resource_observation

        cost = {
            "wall_seconds": 1.0,
            "optimizer_steps": 1,
            "candidate_optimizer_steps": 1,
            "c08_memory_budget_bytes": 64 * 1024 ** 3,
            "atlas_reload_count": 0,
            "feature_manifest_rebuild_count": 0,
            "visit_atlas_reload_count": 1,
            "visit_feature_manifest_rebuild_count": 1,
        }
        step = SimpleNamespace(
            transaction=SimpleNamespace(update_steps=1), realized_cost=cost)
        with patch(
                "bilqis_mlx.runtime.bamf_operator.session_support.shutil.disk_usage",
                return_value=SimpleNamespace(used=123)):
            resource = _resource_observation(Path("/run"), step)
        self.assertEqual(resource["atlas_reload_count"], 0)
        self.assertEqual(resource["feature_manifest_rebuild_count"], 0)
        self.assertEqual(resource["visit_atlas_reload_count"], 1)
        self.assertEqual(resource["visit_feature_manifest_rebuild_count"], 1)

    def test_accepted_visit_persists_native_resource_observation(self):
        with TemporaryDirectory() as temporary:
            prepared, successor, derive, evidence = _prepare_native_resource_visit(temporary)
        self.assertIs(prepared.successor, successor)
        event = derive.call_args.kwargs["delivery_events"][0]
        self.assertEqual(event["event"], "BAMF_C16_3_ACCEPTED")
        resource = event["resource"]
        self.assertEqual(resource["schema"], "bilqis.bamf.c16.3-resource-observation/v2")
        self.assertEqual(resource["candidate_identity_full_computations"], 0)
        self.assertEqual(resource["candidate_identity_numerical_bytes_hashed"], 0)
        self.assertEqual(resource["memory_budget_bytes"], 64 * 1024 ** 3)
        self.assertGreater(resource["disk_used_bytes"], 0)
        self.assertEqual(resource["optimizer_steps"], 1)
        self.assertEqual(resource["wall_seconds"], 30.0)
        self.assertEqual(resource["evidence_bytes_written"], 300)
        self.assertEqual(resource["evidence_file_fsyncs"], 1)
        self.assertEqual(resource["evidence_directory_fsyncs"], 1)
        self.assertEqual(resource["evidence_objects"], 4)
        self.assertEqual(resource["evidence_persistence_seconds"], 0.005)
        self.assertEqual(event["candidate_evidence"], evidence)

    def test_execution_context_uses_accepted_release_without_requiring_c07_lease(self):
        parent = object()
        context = SimpleNamespace()
        host = SimpleNamespace(source_context=lambda **_kwargs: context)
        authenticated = SimpleNamespace(
            features="features", construction_predecessor="predecessor",
            selection=SimpleNamespace(path="/atlas"))
        feature = SimpleNamespace(path="/feature")
        with patch(
                "bilqis_mlx.runtime.bamf_operator.session_support.load_accepted_generation",
                return_value=parent), patch(
                "bilqis_mlx.runtime.bamf_operator.session_support.AcceptedRuntimeHost",
                return_value=host), patch(
                "bilqis_mlx.runtime.bamf_operator.session_support.authenticate_bamf_execution_feature_context",
                return_value=authenticated), patch(
                "bilqis_mlx.runtime.bamf_operator.session_support.persist_feature_manifest",
                return_value=feature):
            self.assertEqual(
                _execution_context(Path("/run")),
                (parent, context, "/atlas", "/feature"))
        self.assertIs(context._accepted_feature_context, authenticated)
