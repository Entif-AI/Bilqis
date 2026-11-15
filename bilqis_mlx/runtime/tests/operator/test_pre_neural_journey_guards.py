"""Fail-closed planning and custody guards for the neural-inert production journey."""
import json
from types import MappingProxyType
import unittest
from unittest.mock import patch

from bilqis_mlx.factory.schedule import schedule_program_from_executable_release
from bilqis_mlx.runtime.accepted_priority_visit import (
    accepted_priority_school, execute_accepted_priority_candidate,
)
from bilqis_mlx.runtime.bamf_operator.session import _Capture, _execution_context, _step_seed
from bilqis_mlx.runtime.factory_candidate_training import FactoryDeliveryObservation
from bilqis_mlx.runtime.foundation_teacher_owner import select_foundation_priority_visit

from .pre_neural_journey_support import (
    PreNeuralJourneySupport, historical_school_release, journey_source,
    portable_atlas_snapshot, wide_shape_patch,
)


class PreNeuralJourneyGuardTests(PreNeuralJourneySupport, unittest.TestCase):
    def test_priority_planning_reports_operator_visible_substages(self):
        self.current, self.parent_graph = historical_school_release()
        snapshot = portable_atlas_snapshot()
        schema, features, atlas_selection = journey_source(snapshot)
        messages = []

        with wide_shape_patch(len(snapshot.abi_entries)):
            self.publish_matching_genesis(snapshot, schema, features)
            with self.journey_mounts(snapshot, schema, features, atlas_selection):
                parent, context, atlas_path, _feature_path = _execution_context(self.run)
                program = schedule_program_from_executable_release(context.release)
                school = accepted_priority_school(parent, program)
                selected = select_foundation_priority_visit(
                    self.run, context, atlas_path, program=program, school=school,
                    progress=messages.append)

        self.assertEqual(selected.status, "TEACHER_SELECTED")
        self.assertEqual(messages, [
            "planner: resolving accepted atlas selection",
            "planner: rebuilding source candidate frontier",
            "planner: staging source-valid candidate realizations",
            "planner: reconciling accepted planning state",
            "planner: building bounded executable snapshot",
            "planner: resolving frontier closure",
            "planner: ranking next bounded target",
            "planner: candidate frontier ready",
            "teacher: binding accepted planning generation",
            "teacher: preparing source-backed offers for 21 capabilities",
            "teacher: ranking priority options",
            "teacher: selecting current priority visit",
            "teacher: priority selection complete (TEACHER_SELECTED)",
        ])

    def test_candidate_preflight_rejects_pointer_drift_before_neural_boundary(self):
        self.current, self.parent_graph = historical_school_release()
        snapshot = portable_atlas_snapshot()
        schema, features, atlas_selection = journey_source(snapshot)
        with wide_shape_patch(len(snapshot.abi_entries)):
            self.publish_matching_genesis(snapshot, schema, features)
            with self.journey_mounts(snapshot, schema, features, atlas_selection):
                parent, context, atlas_path, feature_path = _execution_context(self.run)
                program = schedule_program_from_executable_release(context.release)
                school = accepted_priority_school(parent, program)
                selected = select_foundation_priority_visit(
                    self.run, context, atlas_path, program=program, school=school)
                rows = selected.offer.rows()
                observation = FactoryDeliveryObservation(
                    _Capture(self.run, selected),
                    parent.retained_state.optimizer_step + 1,
                    rows,
                    selected.offer.source_seed,
                )
                state_path = self.run / "bamf-state.json"
                original = state_path.read_bytes()
                changed = json.loads(original)
                changed["generation"] += 1
                state_path.write_text(json.dumps(
                    changed, sort_keys=True, separators=(",", ":")))
                try:
                    with patch(
                            "bilqis_mlx.runtime.factory_candidate_training."
                            "_execute_prepared_candidate") as neural:
                        with self.assertRaises(ValueError) as error:
                            execute_accepted_priority_candidate(
                                selected, context, atlas_path, feature_path,
                                teacher_hparams=parent.optimizer_hyperparameters,
                                observation=observation,
                                optimizer_step_seed=_step_seed(
                                    selected.visit.identity.visit_id),
                                max_norm=1.0,
                            )
                        self.assertEqual(
                            error.exception.context["reason"],
                            "BAMF_PRIORITY_PLANNING_GENERATION_DRIFT",
                        )
                    neural.assert_not_called()
                finally:
                    state_path.write_bytes(original)

    def test_priority_planning_authenticates_generation_once_for_all_capabilities(self):
        from bilqis_mlx.runtime import priority_planning_generation

        original = priority_planning_generation._current_cache
        calls = 0

        def counted(*args, **kwargs):
            nonlocal calls
            calls += 1
            return original(*args, **kwargs)

        with patch.object(priority_planning_generation, "_current_cache", side_effect=counted):
            (_pointer, _before, _after, context, selected, _rows,
             _pointer_bytes, _event_bytes) = self.exercise_journey()

        self.assertEqual(len(context.release.execution_plan.capabilities), 21)
        self.assertEqual(selected.status, "TEACHER_SELECTED")
        self.assertEqual(calls, 1)

    def test_priority_planning_hashes_parameter_tree_once_after_context_authentication(self):
        from bilqis_mlx.runtime import backbone_identity
        from bilqis_mlx.runtime.bamf_bundle import accepted_runtime

        self.current, self.parent_graph = historical_school_release()
        snapshot = portable_atlas_snapshot()
        schema, features, atlas_selection = journey_source(snapshot)
        original = backbone_identity.execution_generation_digest
        calls = 0

        def counted(*args, **kwargs):
            nonlocal calls
            calls += 1
            return original(*args, **kwargs)

        with wide_shape_patch(len(snapshot.abi_entries)):
            self.publish_matching_genesis(snapshot, schema, features)
            with self.journey_mounts(snapshot, schema, features, atlas_selection):
                parent, context, atlas_path, _feature_path = _execution_context(self.run)
                program = schedule_program_from_executable_release(context.release)
                school = accepted_priority_school(parent, program)
                with patch.object(
                        backbone_identity, "execution_generation_digest",
                        side_effect=counted), patch.object(
                            accepted_runtime, "execution_generation_digest",
                            side_effect=counted):
                    selected = select_foundation_priority_visit(
                        self.run, context, atlas_path, program=program, school=school)

        self.assertEqual(len(context.release.execution_plan.capabilities), 21)
        self.assertEqual(selected.status, "TEACHER_SELECTED")
        self.assertEqual(calls, 1)

    def test_planning_generation_rejects_in_memory_parent_mutation(self):
        from bilqis_mlx.runtime.priority_source_offer import _require_planning_generation

        (_pointer, _before, _after, context, selected, _rows,
         _pointer_bytes, _event_bytes) = self.exercise_journey()
        binding = selected.offer._planning_generation
        parent = binding._parent
        optimizer = parent.retained_state.optimizer
        parameters = optimizer.parameters
        name = next(iter(parameters))
        original_parameter = parameters[name]
        original_identity = parent.run_identity

        changed_parameters = dict(parameters)
        changed_parameters[name] = original_parameter + 1
        object.__setattr__(optimizer, "parameters", MappingProxyType(changed_parameters))
        try:
            with self.assertRaises(ValueError):
                _require_planning_generation(binding, context, parent)
        finally:
            object.__setattr__(optimizer, "parameters", parameters)

        object.__setattr__(parent, "run_identity", None)
        try:
            with self.assertRaises(ValueError):
                _require_planning_generation(binding, context, parent)
        finally:
            object.__setattr__(parent, "run_identity", original_identity)


if __name__ == "__main__":
    unittest.main()
