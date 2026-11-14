"""C16.3 persistent BAMF operator routing contracts."""
from __future__ import annotations

from pathlib import Path
from tempfile import TemporaryDirectory
from types import SimpleNamespace
import unittest
from unittest.mock import patch

from bilqis_mlx.runtime.bamf_operator.session import (
    _execution_context, _visit, operate_bamf, prepare_bamf_visit,
)


class BamfOperatorRoutingTests(unittest.TestCase):
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
                prepared = prepare_bamf_visit(Path(temporary))
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
        context = object()
        host = SimpleNamespace(source_context=lambda **_kwargs: context)
        receipt = SimpleNamespace(
            source_atlas_bundle_id="atlas",
            source_release_sha256="release",
            source_source_bundle_id="source",
        )
        accepted = SimpleNamespace(receipt=receipt, construction_predecessor="predecessor")
        selection = SimpleNamespace(path="/atlas")
        authenticated = SimpleNamespace(features="features")
        feature = SimpleNamespace(path="/feature")
        with patch(
                "bilqis_mlx.runtime.bamf_operator.session.load_accepted_generation",
                return_value=parent), patch(
                "bilqis_mlx.runtime.bamf_operator.session.AcceptedRuntimeHost",
                return_value=host), patch(
                "bilqis_mlx.runtime.bamf_operator.session.read_accepted_generation_feature_context",
                return_value=accepted), patch(
                "bilqis_mlx.runtime.bamf_operator.session.AtlasArtifactIdentity",
                return_value="identity"), patch(
                "bilqis_mlx.runtime.bamf_operator.session._atlas_snapshot.resolve_atlas_artifact_selection",
                return_value=selection), patch(
                "bilqis_mlx.runtime.bamf_operator.session.authenticate_bamf_execution_feature_context",
                return_value=authenticated), patch(
                "bilqis_mlx.runtime.bamf_operator.session.persist_feature_manifest",
                return_value=feature):
            self.assertEqual(
                _execution_context(Path("/run")),
                (parent, context, "/atlas", "/feature"))

    def test_priority_hold_never_counts_as_a_neural_visit(self):
        with TemporaryDirectory() as temporary:
            current = SimpleNamespace(
                generation=4, retained_state=SimpleNamespace(optimizer_step=11))
            progress = []
            with patch(
                    "bilqis_mlx.runtime.bamf_operator.session._visit",
                    return_value="HELD") as visit, patch(
                    "bilqis_mlx.runtime.bamf_operator.session.load_accepted_generation",
                    return_value=current):
                result = operate_bamf(
                    temporary, minutes=1, max_visits=3, reserve_gib=0.0,
                    progress=progress.append)
        self.assertEqual(result.status, "PRIORITY_HOLD")
        self.assertEqual(result.visits, 0)
        self.assertEqual(result.accepted, 0)
        self.assertEqual(result.rejected, 0)
        visit.assert_called_once_with(Path(temporary).resolve(), 0.0, progress=progress.append)
        self.assertEqual(progress, ["starting visit 1", "visit 1 outcome: HELD"])

    def test_no_admissible_priority_selection_never_executes_candidate(self):
        parent = SimpleNamespace()
        context = SimpleNamespace(release=object())
        held = SimpleNamespace(status="NO_ADMISSIBLE_TEACHING")
        with patch(
                "bilqis_mlx.runtime.bamf_operator.session._execution_context",
                return_value=(parent, context, "atlas", "feature")), patch(
                "bilqis_mlx.runtime.bamf_operator.session.schedule_program_from_executable_release",
                return_value="program"), patch(
                "bilqis_mlx.runtime.bamf_operator.session.accepted_priority_school",
                return_value="school"), patch(
                "bilqis_mlx.runtime.bamf_operator.session.select_foundation_priority_visit",
                return_value=held), patch(
                "bilqis_mlx.runtime.bamf_operator.session.execute_accepted_priority_candidate",
                side_effect=AssertionError("optimizer candidate must not run")):
            self.assertEqual(_visit("/run", 0.0), "HELD")

    def test_rejection_records_priority_replay_fields_without_advancing_parent(self):
        parent = SimpleNamespace(
            retained_state=SimpleNamespace(optimizer_step=11),
            optimizer_hyperparameters="hparams",
        )
        context = SimpleNamespace(release=object())
        identity = SimpleNamespace(
            visit_id="visit:beta", policy_key="policy:beta",
            to_record=lambda: {"visit_id": "visit:beta"})
        selection = SimpleNamespace(
            status="TEACHER_SELECTED",
            option_id="capability:beta",
            visit=SimpleNamespace(
                identity=identity,
                projection=SimpleNamespace(teacher_state={
                    "last_visit_receipt": {"schema": "fixture-receipt"}})),
            offer=SimpleNamespace(
                capability_id="capability:beta", source_seed=17,
                rows=lambda: ({"id": "row:1"},),
            ),
        )
        transaction = SimpleNamespace(
            parent=SimpleNamespace(optimizer_step=11),
            update_steps=1,
            training_authorities=("authority",),
        )
        step = SimpleNamespace(transaction=transaction)
        decision = SimpleNamespace(
            accepted=False,
            reason="retention_gate",
            to_record=lambda: {"decision": "REJECTED"},
        )
        with patch(
                "bilqis_mlx.runtime.bamf_operator.session._execution_context",
                return_value=(parent, context, "atlas", "feature")), patch(
                "bilqis_mlx.runtime.bamf_operator.session.schedule_program_from_executable_release",
                return_value="program"), patch(
                "bilqis_mlx.runtime.bamf_operator.session.accepted_priority_school",
                return_value="school"), patch(
                "bilqis_mlx.runtime.bamf_operator.session.select_foundation_priority_visit",
                return_value=selection), patch(
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
                return_value=parent.retained_state), patch(
                "bilqis_mlx.runtime.bamf_operator.session.record_bamf_rejection") as rejection:
            self.assertEqual(_visit("/run", 0.0), "REJECTED")

        evidence = rejection.call_args.args[2]
        self.assertEqual(evidence["schema"], "bilqis.bamf.c16.3-rejection/v2")
        self.assertEqual(evidence["visit_id"], "visit:beta")
        self.assertEqual(evidence["selected_option_id"], "capability:beta")
        self.assertEqual(evidence["selected_policy_key"], "policy:beta")
        self.assertEqual(evidence["candidate_optimizer_step"], 12)
        self.assertEqual(evidence["retained_optimizer_step"], 11)
        self.assertEqual(evidence["retention_reason"], "retention_gate")
        self.assertEqual(parent.retained_state.optimizer_step, 11)

    def test_operator_executes_c03_selection_without_reading_factory_release_order(self):
        class OrderTrap:
            @property
            def capabilities(self):
                raise AssertionError("bamf_operator must not inspect Factory capability order")

        parent = SimpleNamespace(
            retained_state=SimpleNamespace(optimizer_step=11),
            optimizer_hyperparameters="hparams",
        )
        context = SimpleNamespace(release=SimpleNamespace(execution_plan=OrderTrap()))
        identity = SimpleNamespace(
            visit_id="visit:beta", policy_key="policy:beta",
            to_record=lambda: {"visit_id": "visit:beta"})
        selection = SimpleNamespace(
            status="TEACHER_SELECTED", option_id="capability:beta",
            visit=SimpleNamespace(
                identity=identity,
                projection=SimpleNamespace(teacher_state={
                    "last_visit_receipt": {"schema": "fixture-receipt"}})),
            offer=SimpleNamespace(
                capability_id="capability:beta", source_seed=17,
                rows=lambda: ({"id": "row:beta"},),
            ),
        )
        transaction = SimpleNamespace(
            parent=SimpleNamespace(optimizer_step=11), update_steps=1,
            training_authorities=("authority",),
        )
        step = SimpleNamespace(transaction=transaction)
        decision = SimpleNamespace(
            accepted=False, reason="retention_gate",
            to_record=lambda: {"decision": "REJECTED"},
        )

        def execute(selected, *_args, **_kwargs):
            self.assertIs(selected, selection)
            self.assertEqual(selected.offer.capability_id, "capability:beta")
            return step

        with patch(
                "bilqis_mlx.runtime.bamf_operator.session._execution_context",
                return_value=(parent, context, "atlas", "feature")), patch(
                "bilqis_mlx.runtime.bamf_operator.session.schedule_program_from_executable_release",
                return_value="program"), patch(
                "bilqis_mlx.runtime.bamf_operator.session.accepted_priority_school",
                return_value="school"), patch(
                "bilqis_mlx.runtime.bamf_operator.session.select_foundation_priority_visit",
                return_value=selection), patch(
                "bilqis_mlx.runtime.bamf_operator.session._Capture",
                return_value="capture"), patch(
                "bilqis_mlx.runtime.bamf_operator.session.FactoryDeliveryObservation",
                return_value="observation"), patch(
                "bilqis_mlx.runtime.bamf_operator.session.execute_accepted_priority_candidate",
                side_effect=execute), patch(
                "bilqis_mlx.runtime.bamf_operator.session.evaluate_factory_retention_candidate",
                return_value="evaluation"), patch(
                "bilqis_mlx.runtime.bamf_operator.session.issue_factory_retention_decision",
                return_value=decision), patch(
                "bilqis_mlx.runtime.bamf_operator.session.resolve_candidate",
                return_value=parent.retained_state), patch(
                "bilqis_mlx.runtime.bamf_operator.session.record_bamf_rejection"):
            self.assertEqual(_visit("/run", 0.0), "REJECTED")


if __name__ == "__main__":
    unittest.main()
