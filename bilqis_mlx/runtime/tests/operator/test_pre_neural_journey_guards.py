"""Fail-closed planning and custody guards for the neural-inert production journey."""
import json
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
            "teacher: binding accepted planning generation",
            "planner: resolving accepted atlas selection",
            "planner: compiling semantic curriculum",
            "planner: rebuilding source candidate frontier",
            "planner: staging source-valid candidate realizations",
            "planner: reconciling accepted planning state",
            "planner: building bounded executable snapshot",
            "planner: resolving frontier closure",
            "planner: ranking next bounded target",
            "planner: candidate frontier ready",
            "teacher: preparing source-backed offers for 14 lawful capabilities",
            "teacher: ranking priority options",
            "teacher: selecting current priority visit",
            "teacher: priority selection complete (TEACHER_SELECTED)",
        ])


    def test_priority_planning_reuses_authenticated_atlas_snapshot(self):
        from bilqis_mlx.factory.skos_curriculum import common as curriculum_common

        self.current, self.parent_graph = historical_school_release()
        snapshot = portable_atlas_snapshot()
        schema, features, atlas_selection = journey_source(snapshot)
        with wide_shape_patch(len(snapshot.abi_entries)):
            self.publish_matching_genesis(snapshot, schema, features)
            with self.journey_mounts(snapshot, schema, features, atlas_selection):
                parent, context, atlas_path, _feature_path = _execution_context(self.run)
                program = schedule_program_from_executable_release(context.release)
                school = accepted_priority_school(parent, program)
                with patch.object(
                        curriculum_common, "_load_pinned",
                        side_effect=AssertionError("authenticated atlas was reloaded")):
                    selected = select_foundation_priority_visit(
                        self.run, context, atlas_path, program=program, school=school)

        self.assertEqual(selected.status, "TEACHER_SELECTED")

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
                cache = selected.offer._planning_generation._cache
                observation = FactoryDeliveryObservation(
                    _Capture(
                        self.run, selected, generation=cache.generation,
                        accepted_manifest_sha256=cache.accepted_manifest_sha256,
                        candidate_attempt_ordinal=1,
                        parent_optimizer_step=parent.retained_state.optimizer_step),
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
                            "B13_CURRENTNESS_POINTER_DRIFT",
                        )
                    neural.assert_not_called()
                finally:
                    state_path.write_bytes(original)



if __name__ == "__main__":
    unittest.main()
