"""Additional C16.3 operator routing and rejection contracts."""
from pathlib import Path
from tempfile import TemporaryDirectory
from types import SimpleNamespace
import unittest
from unittest.mock import patch

from bilqis_mlx.errors import BilqisError
from bilqis_mlx.runtime.bamf_operator.session import _visit, operate_bamf


class BamfOperatorRoutingContinuationTests(unittest.TestCase):
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
        visit.assert_called_once_with(
            Path(temporary).resolve(), 0.0, steps_per_visit=16,
            progress=progress.append, source_prefetch_workers=2,
            source_prefetch_executor=visit.call_args.kwargs["source_prefetch_executor"],
            source_prefetch_metrics=visit.call_args.kwargs["source_prefetch_metrics"],
            observer=visit.call_args.kwargs["observer"])
        self.assertEqual(progress, ["starting visit 1", "visit 1 outcome: HELD"])

    def test_candidate_horizon_is_bounded_to_historical_sixteen_step_ceiling(self):
        with self.assertRaises(BilqisError):
            operate_bamf("/run", minutes=1, steps_per_visit=17)

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
                "bilqis_mlx.runtime.bamf_operator.session.bind_accepted_execution_cache",
                return_value="cache"), patch(
                "bilqis_mlx.runtime.bamf_operator.session.candidate_step_horizon",
                return_value=1), patch(
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
