"""Visit-currentness guards for the neural-inert production journey."""
from types import MappingProxyType, SimpleNamespace
import unittest
from unittest.mock import patch

from bilqis_mlx.factory.schedule import schedule_program_from_executable_release
from bilqis_mlx.runtime.accepted_priority_visit import accepted_priority_school
from bilqis_mlx.runtime.bamf_operator.session import _execution_context
from bilqis_mlx.runtime.foundation_teacher_owner import select_foundation_priority_visit

from .pre_neural_journey_support import (
    PreNeuralJourneySupport, historical_school_release, journey_source,
    portable_atlas_snapshot, wide_shape_patch,
)


class PreNeuralJourneyCurrentnessTests(PreNeuralJourneySupport, unittest.TestCase):
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

    def test_21_capability_16_step_currentness_cost_is_bounded(self):
        from bilqis_mlx.runtime.bamf_bundle.currentness_transaction import (
            VisitCurrentnessMetrics, currentness_metrics,
            refresh_accepted_currentness,
        )

        self.current, self.parent_graph = historical_school_release()
        snapshot = portable_atlas_snapshot()
        schema, features, atlas_selection = journey_source(snapshot)
        metrics = VisitCurrentnessMetrics()
        with wide_shape_patch(len(snapshot.abi_entries)):
            self.publish_matching_genesis(snapshot, schema, features)
            with self.journey_mounts(snapshot, schema, features, atlas_selection):
                parent, context, atlas_path, _feature_path = _execution_context(
                    self.run, currentness_metrics=metrics)
                program = schedule_program_from_executable_release(context.release)
                cache = context._accepted_runtime_host._accepted_cache
                school = accepted_priority_school(
                    parent, program,
                    candidate_identity_sha256=cache._candidate_identity_sha256)
                selected = select_foundation_priority_visit(
                    self.run, context, atlas_path, program=program, school=school)
                transaction = selected.offer._planning_generation._accepted_currentness
                for _ in range(16):
                    refresh_accepted_currentness(transaction, transaction._parent)

        self.assertEqual(len(context.release.execution_plan.capabilities), 21)
        self.assertEqual(selected.status, "TEACHER_SELECTED")
        self.assertEqual(currentness_metrics(transaction), {
            "deep_authentication_count": 1,
            "accepted_cache_currentness_count": 16,
            "full_candidate_identity_hashes": 1,
            "bundle_tree_scans": 2,
        })

    def test_step_currentness_witness_skips_full_checkpoint_rehash_in_bound_frontier(self):
        from bilqis_mlx.runtime.bamf_bundle.currentness_transaction import (
            refresh_accepted_currentness,
        )
        from bilqis_mlx.runtime.lawful_teaching_frontier import (
            require_bound_lawful_teaching_frontier,
        )

        (_pointer, _before, _after, context, selected, _rows,
         _pointer_bytes, _event_bytes) = self.exercise_journey()
        planning = selected.offer._planning_generation
        parent = planning._parent
        transaction = planning._accepted_currentness
        from bilqis_mlx.runtime.bamf_bundle.source_authority_custody import currentness
        with patch.object(
                currentness, "_trust_root_snapshot",
                return_value=transaction._source_currentness._trust_root):
            step_currentness = refresh_accepted_currentness(transaction, parent)
        frontier = selected._lawful_frontier
        active_grade = SimpleNamespace(
            activation_sha256=frontier.active_grade_activation_sha256,
            definition=SimpleNamespace(
                definition_sha256=frontier.active_grade_definition_sha256,
                members=tuple(SimpleNamespace(capability_id=capability_id,
                                              semantic_id=semantic_id)
                              for capability_id, semantic_id
                              in frontier.active_grade_members),
            ),
        )

        with patch.object(
                currentness, "_trust_root_snapshot",
                return_value=transaction._source_currentness._trust_root), patch(
                "bilqis_mlx.runtime.active_generated_grade.read_active_generated_grade",
                return_value=active_grade), patch(
                "bilqis_mlx.runtime.active_generated_grade."
                "_read_bound_active_generated_grade",
                return_value=active_grade), patch(
                "bilqis_mlx.runtime.atlas_flywheel_runtime._accepted_checkpoint",
                side_effect=AssertionError("accepted checkpoint rehashed in hot step")):
            current = require_bound_lawful_teaching_frontier(
                frontier, context, parent,
                currentness_step=step_currentness)
        self.assertIs(current, frontier)

    def test_step_currentness_witness_is_revoked_by_next_refresh(self):
        from bilqis_mlx.runtime.bamf_bundle.currentness_transaction import (
            refresh_accepted_currentness,
            require_accepted_currentness_step,
        )

        (_pointer, _before, _after, _context, selected, _rows,
         _pointer_bytes, _event_bytes) = self.exercise_journey()
        planning = selected.offer._planning_generation
        parent = planning._parent
        transaction = planning._accepted_currentness
        from bilqis_mlx.runtime.bamf_bundle.source_authority_custody import currentness
        with patch.object(
                currentness, "_trust_root_snapshot",
                return_value=transaction._source_currentness._trust_root):
            first = refresh_accepted_currentness(transaction, parent)
            second = refresh_accepted_currentness(transaction, parent)

        with patch.object(
                currentness, "_trust_root_snapshot",
                return_value=transaction._source_currentness._trust_root):
            with self.assertRaises(ValueError):
                require_accepted_currentness_step(first, transaction, parent)
            self.assertIs(
                require_accepted_currentness_step(second, transaction, parent),
                second,
            )

    def test_step_currentness_live_fence_rechecks_mutable_authority_edges(self):
        from bilqis_mlx.runtime.bamf_bundle import bundle_currentness
        from bilqis_mlx.runtime.bamf_bundle import currentness_transaction
        from bilqis_mlx.runtime.bamf_bundle.currentness_transaction import (
            refresh_accepted_currentness,
            require_live_accepted_currentness_step,
        )
        from bilqis_mlx.runtime.bamf_bundle.source_authority_custody import currentness

        (_pointer, _before, _after, _context, selected, _rows,
         _pointer_bytes, _event_bytes) = self.exercise_journey()
        planning = selected.offer._planning_generation
        parent = planning._parent
        transaction = planning._accepted_currentness
        stable_trust_root = transaction._source_currentness._trust_root
        with patch.object(
                currentness, "_trust_root_snapshot",
                return_value=stable_trust_root):
            step = refresh_accepted_currentness(transaction, parent)

        with patch.object(
                currentness_transaction, "_pointer_snapshot",
                return_value=("9" * 64, transaction._acceptance_sha256,
                              transaction._acceptance_identity)), patch.object(
                    currentness, "_trust_root_snapshot",
                    return_value=stable_trust_root):
            with self.assertRaises(ValueError):
                require_live_accepted_currentness_step(step, transaction, parent)

        with patch.object(
                bundle_currentness, "_stat_identity",
                return_value=(9, 9, 9, 9, 9)), patch.object(
                    currentness, "_trust_root_snapshot",
                    return_value=stable_trust_root):
            with self.assertRaises(ValueError):
                require_live_accepted_currentness_step(step, transaction, parent)

        with patch.object(
                currentness, "_trust_root_snapshot",
                return_value=("HOST_SYSTEM_V1", 9, 9, 9, 9, 9)):
            with self.assertRaises(ValueError):
                require_live_accepted_currentness_step(step, transaction, parent)

        with patch.object(
                currentness_transaction, "contract_digest",
                return_value="9" * 64), patch.object(
                    currentness, "_trust_root_snapshot",
                    return_value=stable_trust_root):
            with self.assertRaises(ValueError):
                require_live_accepted_currentness_step(step, transaction, parent)

    def test_priority_planning_reuses_generation_binding_after_context_authentication(self):
        from bilqis_mlx.runtime import backbone_identity
        from bilqis_mlx.runtime.bamf_bundle import accepted_execution_runtime

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
                            accepted_execution_runtime, "execution_generation_digest",
                            side_effect=counted):
                    selected = select_foundation_priority_visit(
                        self.run, context, atlas_path, program=program, school=school)

        self.assertEqual(len(context.release.execution_plan.capabilities), 21)
        self.assertEqual(selected.status, "TEACHER_SELECTED")
        # #1173 owns one execution-generation proof per immutable state. Once the
        # accepted execution context has bound it, C03 planning must not hash the
        # parameter tree again during the 21-capability fan-out.
        self.assertEqual(calls, 0)

    def test_priority_planning_deep_custody_binds_once_then_uses_currentness(self):
        from bilqis_mlx.runtime import bamf_bundle
        from bilqis_mlx.runtime.bamf_operator import session_support
        from bilqis_mlx.runtime.bamf_bundle import currentness_transaction
        from bilqis_mlx.runtime.bamf_bundle.source_authority_custody import currentness
        from bilqis_mlx.runtime.priority_source_offer import _require_planning_generation

        b13_original = currentness_transaction.bind_bamf_bundle_currentness
        c09_original = currentness_transaction.bind_source_authority_currentness
        context_features_original = session_support.authenticate_bamf_execution_feature_context
        planning_features_original = bamf_bundle.authenticate_bamf_execution_feature_context
        counts = {"b13": 0, "c09": 0, "context_features": 0, "planning_features": 0}

        def b13_counted(*args, **kwargs):
            counts["b13"] += 1
            return b13_original(*args, **kwargs)

        def c09_counted(*args, **kwargs):
            counts["c09"] += 1
            return c09_original(*args, **kwargs)

        def context_features_counted(*args, **kwargs):
            counts["context_features"] += 1
            return context_features_original(*args, **kwargs)

        def planning_features_counted(*args, **kwargs):
            counts["planning_features"] += 1
            return planning_features_original(*args, **kwargs)

        with patch.object(currentness_transaction, "bind_bamf_bundle_currentness",
                          side_effect=b13_counted), patch.object(
                              currentness_transaction, "bind_source_authority_currentness",
                              side_effect=c09_counted), patch.object(
                                  session_support, "authenticate_bamf_execution_feature_context",
                                  side_effect=context_features_counted), patch.object(
                                  bamf_bundle, "authenticate_bamf_execution_feature_context",
                                  side_effect=planning_features_counted):
            (_pointer, _before, _after, context, selected, _rows,
             _pointer_bytes, _event_bytes) = self.exercise_journey()

        binding = selected.offer._planning_generation
        parent = binding._parent
        self.assertEqual(counts, {
            "b13": 1, "c09": 1, "context_features": 1, "planning_features": 0})
        stable_trust_root = binding._accepted_currentness._source_currentness._trust_root

        with patch.object(
                currentness_transaction, "bind_bamf_bundle_currentness",
                side_effect=AssertionError("deep B13 validation repeated")), patch.object(
                    currentness, "resolve_source_authority_registry",
                    side_effect=AssertionError("deep C09 resolution repeated")), patch.object(
                        currentness, "_trust_root_snapshot",
                        return_value=stable_trust_root), patch.object(
                            session_support, "authenticate_bamf_execution_feature_context",
                            side_effect=AssertionError(
                                "execution context reauthenticated features")), patch.object(
                            bamf_bundle, "authenticate_bamf_execution_feature_context",
                            side_effect=AssertionError(
                                "feature context reauthenticated")):
            for _ in range(3):
                cache, authenticated = _require_planning_generation(
                    binding, context, parent)
                self.assertIs(cache, binding._cache)
                self.assertIs(authenticated, binding._authenticated_features)

    def test_priority_planning_currentness_rejects_b13_and_c09_drift(self):
        from bilqis_mlx.runtime.bamf_bundle import bundle_currentness
        from bilqis_mlx.runtime.bamf_bundle import currentness_transaction
        from bilqis_mlx.runtime.bamf_bundle.currentness_transaction import (
            refresh_accepted_currentness,
        )
        from bilqis_mlx.runtime.bamf_bundle.source_authority_custody import currentness

        (_pointer, _before, _after, context, selected, _rows,
         _pointer_bytes, _event_bytes) = self.exercise_journey()
        binding = selected.offer._planning_generation
        parent = binding._parent
        transaction = binding._accepted_currentness

        with patch.object(
                bundle_currentness, "_stat_identity",
                return_value=(9, 9, 9, 9, 9)):
            with self.assertRaises(ValueError):
                refresh_accepted_currentness(transaction, parent)

        with patch.object(
                currentness, "_trust_root_snapshot",
                return_value=("HOST_SYSTEM_V1", 9, 9, 9, 9, 9)):
            with self.assertRaises(ValueError):
                refresh_accepted_currentness(transaction, parent)

        with patch.object(
                currentness_transaction, "contract_digest", return_value="9" * 64):
            with self.assertRaises(ValueError):
                refresh_accepted_currentness(transaction, parent)

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
