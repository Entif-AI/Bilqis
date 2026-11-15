"""C16.3 persistent BAMF operator routing contracts."""
from __future__ import annotations

from pathlib import Path
from tempfile import TemporaryDirectory
from types import SimpleNamespace
import unittest
from unittest.mock import patch

from bilqis_mlx.errors import BilqisError
from bilqis_mlx.runtime.bamf_operator.session import (
    _execution_context, _visit, operate_bamf, prepare_bamf_visit,
)


class BamfOperatorRoutingTests(unittest.TestCase):
    def test_prepare_visit_accumulates_horizon_before_one_retention_decision(self):
        parent = SimpleNamespace(
            retained_state=SimpleNamespace(optimizer_step=11),
            optimizer_hyperparameters="hparams",
        )
        context = SimpleNamespace(release=object())
        identity = SimpleNamespace(visit_id="visit:horizon", policy_key="policy:horizon")
        selection = SimpleNamespace(
            status="TEACHER_SELECTED",
            visit=SimpleNamespace(identity=identity),
            offer=SimpleNamespace(
                capability_id="capability:horizon", source_seed=17,
                rows=lambda: ({"id": "row:horizon"},),
            ),
        )
        transactions = []

        def execute(*_args, candidate=None, **_kwargs):
            ordinal = len(transactions) + 1
            if ordinal == 1:
                self.assertIsNone(candidate)
            else:
                self.assertIs(candidate, transactions[-1])
            transaction = SimpleNamespace(
                parent=SimpleNamespace(optimizer_step=11),
                update_steps=ordinal,
                training_authorities=tuple(f"authority-{step}" for step in range(ordinal)),
            )
            transactions.append(transaction)
            return SimpleNamespace(
                transaction=transaction,
                realized_cost={
                    "wall_seconds": float(ordinal),
                    "optimizer_steps": 1,
                    "candidate_optimizer_steps": ordinal,
                    "c08_memory_budget_bytes": 64 * 1024 ** 3,
                },
            )

        decision = SimpleNamespace(accepted=True)
        retained = SimpleNamespace(optimizer_step=15)
        successor = object()
        with patch(
                "bilqis_mlx.runtime.bamf_operator.session._execution_context",
                return_value=(parent, context, "atlas", "feature")), patch(
                "bilqis_mlx.runtime.bamf_operator.session.schedule_program_from_executable_release",
                return_value="program"), patch(
                "bilqis_mlx.runtime.bamf_operator.session.accepted_priority_school",
                return_value="school"), patch(
                "bilqis_mlx.runtime.bamf_operator.session.select_foundation_priority_visit",
                return_value=selection), patch(
                "bilqis_mlx.runtime.bamf_operator.session.bind_accepted_execution_cache",
                return_value="cache"), patch(
                "bilqis_mlx.runtime.bamf_operator.session.candidate_step_horizon",
                return_value=4) as horizon, patch(
                "bilqis_mlx.runtime.bamf_operator.session._Capture",
                return_value="capture"), patch(
                "bilqis_mlx.runtime.bamf_operator.session.FactoryDeliveryObservation",
                return_value="observation"), patch(
                "bilqis_mlx.runtime.bamf_operator.session.execute_accepted_priority_candidate",
                side_effect=execute) as execute_candidate, patch(
                "bilqis_mlx.runtime.bamf_operator.session.evaluate_factory_retention_candidate",
                return_value="evaluation") as evaluate, patch(
                "bilqis_mlx.runtime.bamf_operator.session.issue_factory_retention_decision",
                return_value=decision) as decide, patch(
                "bilqis_mlx.runtime.bamf_operator.session.resolve_candidate",
                return_value=retained), patch(
                "bilqis_mlx.runtime.bamf_operator.session.derive_accepted_teacher_successor",
                return_value=successor) as derive, patch(
                "bilqis_mlx.runtime.bamf_operator.session_support.shutil.disk_usage",
                return_value=SimpleNamespace(used=123)):
            prepared = prepare_bamf_visit(Path("/run"), steps_per_visit=16)

        self.assertEqual(prepared.status, "ACCEPTED")
        self.assertEqual(len(prepared.steps), 4)
        self.assertEqual(prepared.step.transaction.update_steps, 4)
        self.assertEqual(execute_candidate.call_count, 4)
        horizon.assert_called_once_with(
            Path("/run"), parent, "cache", "capability:horizon", 16)
        evaluate.assert_called_once_with(
            context, transactions[-1], "atlas", "capability:horizon", run_dir=Path("/run"))
        decide.assert_called_once_with("evaluation")
        event = derive.call_args.kwargs["delivery_events"][0]
        self.assertEqual(event["resource"]["optimizer_steps"], 4)
        self.assertEqual(event["resource"]["wall_seconds"], 10.0)

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
            parent = SimpleNamespace(
                retained_state=SimpleNamespace(optimizer_step=11),
                optimizer_hyperparameters="hparams",
            )
            context = SimpleNamespace(release=object())
            identity = SimpleNamespace(visit_id="visit:resource", policy_key="policy:resource")
            selection = SimpleNamespace(
                status="TEACHER_SELECTED",
                visit=SimpleNamespace(identity=identity),
                offer=SimpleNamespace(
                    capability_id="capability:resource", source_seed=17,
                    rows=lambda: ({"id": "row:resource"},),
                ),
            )
            transaction = SimpleNamespace(
                parent=SimpleNamespace(optimizer_step=11), update_steps=1,
                training_authorities=("authority",),
            )
            step = SimpleNamespace(
                transaction=transaction,
                realized_cost={
                    "wall_seconds": 30.0,
                    "optimizer_steps": 1,
                    "c08_memory_budget_bytes": 64 * 1024 ** 3,
                },
            )
            decision = SimpleNamespace(accepted=True)
            retained = SimpleNamespace(optimizer_step=12)
            successor = object()
            with patch(
                    "bilqis_mlx.runtime.bamf_operator.session._execution_context",
                    return_value=(parent, context, "atlas", "feature")), patch(
                    "bilqis_mlx.runtime.bamf_operator.session.schedule_program_from_executable_release",
                    return_value="program"), patch(
                    "bilqis_mlx.runtime.bamf_operator.session.accepted_priority_school",
                    return_value="school"), patch(
                    "bilqis_mlx.runtime.bamf_operator.session.select_foundation_priority_visit",
                    return_value=selection), patch(
                    "bilqis_mlx.runtime.bamf_operator.session.bind_accepted_execution_cache",
                    return_value="cache"), patch(
                    "bilqis_mlx.runtime.bamf_operator.session.candidate_step_horizon",
                    return_value=1), patch(
                    "bilqis_mlx.runtime.bamf_operator.session._Capture",
                    return_value="capture"), patch(
                    "bilqis_mlx.runtime.bamf_operator.session.FactoryDeliveryObservation",
                    return_value="observation"), patch(
                    "bilqis_mlx.runtime.bamf_operator.session.execute_accepted_priority_candidate",
                    return_value=step), patch(
                    "bilqis_mlx.runtime.bamf_operator.session.evaluate_factory_retention_candidate",
                    return_value="evaluation"), patch(
                    "bilqis_mlx.runtime.bamf_operator.session.issue_factory_retention_decision",
                    return_value=decision), patch(
                    "bilqis_mlx.runtime.bamf_operator.session.resolve_candidate",
                    return_value=retained), patch(
                    "bilqis_mlx.runtime.bamf_operator.session.derive_accepted_teacher_successor",
                    return_value=successor) as derive:
                prepared = prepare_bamf_visit(Path(temporary), steps_per_visit=16)
        self.assertIs(prepared.successor, successor)
        event = derive.call_args.kwargs["delivery_events"][0]
        self.assertEqual(event["event"], "BAMF_C16_3_ACCEPTED")
        resource = event["resource"]
        self.assertEqual(resource["schema"], "bilqis.bamf.c16.3-resource-observation/v1")
        self.assertEqual(resource["memory_budget_bytes"], 64 * 1024 ** 3)
        self.assertGreater(resource["disk_used_bytes"], 0)
        self.assertEqual(resource["optimizer_steps"], 1)
        self.assertEqual(resource["wall_seconds"], 30.0)

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



if __name__ == "__main__":
    unittest.main()
