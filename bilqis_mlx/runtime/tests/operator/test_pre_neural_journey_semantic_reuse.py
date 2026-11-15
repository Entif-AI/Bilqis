"""Semantic-context reuse guards for the neural-inert production journey."""
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


class PreNeuralJourneySemanticReuseTests(PreNeuralJourneySupport, unittest.TestCase):
    def test_candidate_preflight_reuses_planning_feature_context_without_reauthentication(self):
        self.current, self.parent_graph = historical_school_release()
        snapshot = portable_atlas_snapshot()
        schema, features, atlas_selection = journey_source(snapshot)
        marker = object()
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
                expected = selected.offer._planning_generation._authenticated_features
                with patch(
                        "bilqis_mlx.runtime.factory_training_bridge."
                        "authenticate_bamf_execution_feature_context",
                        side_effect=AssertionError("training bridge reauthenticated features")), patch(
                            "bilqis_mlx.runtime.factory_candidate_training."
                            "_execute_prepared_candidate", return_value=marker) as boundary:
                    result = execute_accepted_priority_candidate(
                        selected, context, atlas_path, feature_path,
                        teacher_hparams=parent.optimizer_hyperparameters,
                        observation=observation,
                        optimizer_step_seed=_step_seed(selected.visit.identity.visit_id),
                        max_norm=1.0,
                    )
        self.assertIs(result, marker)
        self.assertIs(boundary.call_args.kwargs["semantic_context"], expected)

    def test_priority_target_registration_reuses_authenticated_c09_runtime(self):
        """Offer target replay must not reopen deep C09 accepted-registry custody."""
        from bilqis_mlx.runtime.bamf_bundle import accepted_runtime

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
                        accepted_runtime, "_accepted_correction_registry",
                        side_effect=AssertionError(
                            "target registration rebound deep C09 authority")):
                    selected = select_foundation_priority_visit(
                        self.run, context, atlas_path, program=program, school=school)

        self.assertEqual(len(context.release.execution_plan.capabilities), 21)
        self.assertEqual(selected.status, "TEACHER_SELECTED")

    def test_priority_requalification_reuses_planning_generation_authority(self):
        from bilqis_mlx.runtime import priority_qualification

        with patch.object(
                priority_qualification, "_accepted_correction_registry",
                side_effect=AssertionError("requalification rebound correction authority")):
            (_pointer, _before, _after, _context, selected, _rows,
             _pointer_bytes, _event_bytes) = self.exercise_journey()
        self.assertEqual(selected.status, "TEACHER_SELECTED")



if __name__ == "__main__":
    unittest.main()
