"""Canonical neural-inert BAMF production-journey conformance."""
from __future__ import annotations

import hashlib
import json
import unittest
from dataclasses import replace
from types import MappingProxyType
from unittest.mock import patch

from bilqis_mlx.factory.adapters import SourceAdapterRegistry
from bilqis_mlx.factory.candidate_frontier import load_candidate_frontier
from bilqis_mlx.factory.candidate_staging import StagedCandidate
from bilqis_mlx.factory.live_answers import live_answer_registry
from bilqis_mlx.factory.schedule import schedule_program_from_executable_release
from bilqis_mlx.runtime.accepted_priority_visit import accepted_priority_school
from bilqis_mlx.runtime.bamf_bundle.admission import load_accepted_generation
from bilqis_mlx.runtime.bamf_operator.session import _execution_context
from bilqis_mlx.runtime.foundation_teacher_owner import select_foundation_priority_visit
from bilqis_mlx.runtime.jit_adoption import verify_current_implementations
from bilqis_mlx.source_adapters.school import live_source_registry

from .pre_neural_journey_support import (
    ROOT, PreNeuralJourneySupport, historical_school_release, journey_source,
    portable_atlas_snapshot, wide_shape_patch,
)


class PreNeuralProductionJourneyTests(PreNeuralJourneySupport, unittest.TestCase):
    def _staged_bytes(self):
        root = self.run / "autonomy" / "staged-candidates"
        if not root.exists():
            return {}
        return {
            str(path.relative_to(root)): path.read_bytes()
            for path in root.rglob("*") if path.is_file()
        }

    def _exercise_journey(self):
        self.current, self.parent_graph = historical_school_release()
        snapshot = portable_atlas_snapshot()
        schema, features, atlas_selection = journey_source(snapshot)
        with wide_shape_patch(len(snapshot.abi_entries)):
            pointer = self.publish_matching_genesis(snapshot, schema, features)
            before = load_accepted_generation(self.run)
            pointer_bytes = (self.run / "bamf-state.json").read_bytes()
            event_bytes = (self.run / "events.jsonl").read_bytes()

            with self.journey_mounts(
                    snapshot, schema, features, atlas_selection):
                parent, context, atlas_path, _feature_path = _execution_context(self.run)
                program = schedule_program_from_executable_release(context.release)
                school = accepted_priority_school(parent, program)
                selected = select_foundation_priority_visit(
                    self.run, context, atlas_path, program=program, school=school)
                rows = selected.offer.rows()
            after = load_accepted_generation(self.run)
        return pointer, before, after, context, selected, rows, pointer_bytes, event_bytes

    def _assert_source_corruption_fails_closed(
            self, selected, pointer_bytes, event_bytes):
        source_wire = selected.offer._rows_json
        staged_before = self._staged_bytes()
        object.__setattr__(selected.offer, "_rows_json", source_wire + " ")
        try:
            with self.assertRaises(ValueError):
                selected.offer.rows()
        finally:
            object.__setattr__(selected.offer, "_rows_json", source_wire)
        self.assertEqual((self.run / "bamf-state.json").read_bytes(), pointer_bytes)
        self.assertEqual((self.run / "events.jsonl").read_bytes(), event_bytes)
        self.assertEqual(self._staged_bytes(), staged_before)

    def _load_verified_staged_candidate(self, context):
        staged_paths = tuple(
            (self.run / "autonomy/staged-candidates").glob("*.json"))
        self.assertEqual(len(staged_paths), 1)
        staged_payload = json.loads(staged_paths[0].read_text())
        staged = StagedCandidate.from_manifest(staged_payload, staged_paths[0].stem)
        builder = ROOT / "lib/ithkuil/src/build_curriculum_frontier.py"
        frontier = load_candidate_frontier(
            self.run / "candidate-frontier", ROOT / "lib/ithkuil/_data/csv",
            expected_builder_sha256=hashlib.sha256(builder.read_bytes()).hexdigest())
        staged.verify(frontier, context.release)
        verify_current_implementations(
            staged.successor, live_source_registry(), live_answer_registry())
        return staged, frontier

    def _assert_staged_identity(self, staged, context):
        self.assertEqual(staged.candidate_id, "D-01")
        self.assertEqual(
            staged.successor.transition.added_capabilities,
            ("D.COPULAR_IDENTITY",))
        self.assertEqual(staged.successor.transition.changed_capabilities, ())
        predecessor = {item.adapter_id: item for item in context.release.source_adapters}
        successor = {item.adapter_id: item for item in staged.successor.source_adapters}
        self.assertEqual({key: successor[key] for key in predecessor}, predecessor)
        self.assertIn("source.ithkuil-reference-identity/v1", successor)

    def _assert_provider_and_frontier_corruption_fail(self, staged, frontier, context):
        corrupted_frontier = replace(frontier, release_sha256="f" * 64)
        with self.assertRaisesRegex(ValueError, "CANDIDATE_FRONTIER_RELEASE_DIGEST_MISMATCH"):
            staged.verify(corrupted_frontier, context.release)
        current_registry = live_source_registry()
        current_adapters, seen_generators = [], set()
        for descriptor in staged.successor.source_adapters:
            registered = current_registry.resolve_owner(descriptor.generator_id)
            generator_id = registered.descriptor.generator_id
            if generator_id in seen_generators:
                continue
            seen_generators.add(generator_id)
            if registered.descriptor.adapter_id == "source.ithkuil-reference-identity/v1":
                registered = replace(registered, descriptor=replace(
                    registered.descriptor, implementation_sha256="f" * 64))
            current_adapters.append(registered)
        with self.assertRaisesRegex(
                ValueError, "JIT_ADOPTION_SOURCE_IMPLEMENTATION_DRIFT"):
            verify_current_implementations(
                staged.successor, SourceAdapterRegistry(tuple(current_adapters)),
                live_answer_registry())

    def _assert_custody_corruption_fails_closed(self, pointer_bytes, event_bytes):
        staged_before = self._staged_bytes()
        state_path = self.run / "bamf-state.json"
        pointer_record = json.loads(pointer_bytes)
        pointer_record["generation"] += 1
        state_path.write_text(json.dumps(
            pointer_record, sort_keys=True, separators=(",", ":")))
        tampered_pointer = state_path.read_bytes()
        try:
            with self.assertRaises(ValueError):
                _execution_context(self.run)
            self.assertEqual(state_path.read_bytes(), tampered_pointer)
            self.assertEqual((self.run / "events.jsonl").read_bytes(), event_bytes)
            self.assertEqual(self._staged_bytes(), staged_before)
        finally:
            state_path.write_bytes(pointer_bytes)

    def test_historical_accepted_run_reaches_real_teacher_offer_without_neural_mutation(self):
        (pointer, before, after, context, selected, rows,
         pointer_bytes, event_bytes) = self._exercise_journey()
        self.assertEqual(pointer["generation"], 0)
        self.assertEqual(len(context.release.execution_plan.capabilities), 21)
        self.assertEqual(selected.status, "TEACHER_SELECTED")
        self.assertEqual(selected.offer.source_each, 4)
        self.assertEqual(len(rows), 4)
        self.assertEqual(before.retained_state.optimizer_step, 0)
        self.assertEqual(after.retained_state.optimizer_step, 0)
        self.assertEqual(after.teacher_state, before.teacher_state)
        self.assertEqual((self.run / "bamf-state.json").read_bytes(), pointer_bytes)
        self.assertEqual((self.run / "events.jsonl").read_bytes(), event_bytes)
        self._assert_source_corruption_fails_closed(selected, pointer_bytes, event_bytes)
        staged, frontier = self._load_verified_staged_candidate(context)
        self._assert_staged_identity(staged, context)
        self._assert_provider_and_frontier_corruption_fail(staged, frontier, context)
        self._assert_custody_corruption_fails_closed(pointer_bytes, event_bytes)

    def test_priority_planning_authenticates_generation_once_for_all_capabilities(self):
        from bilqis_mlx.runtime import priority_source_offer

        original = priority_source_offer._current_cache
        calls = 0

        def counted(*args, **kwargs):
            nonlocal calls
            calls += 1
            return original(*args, **kwargs)

        with patch.object(priority_source_offer, "_current_cache", side_effect=counted):
            _pointer, _before, _after, context, selected, _rows, _pointer_bytes, _event_bytes = (
                self._exercise_journey())

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
                with patch.object(backbone_identity, "execution_generation_digest", side_effect=counted), \
                        patch.object(accepted_runtime, "execution_generation_digest", side_effect=counted):
                    selected = select_foundation_priority_visit(
                        self.run, context, atlas_path, program=program, school=school)

        self.assertEqual(len(context.release.execution_plan.capabilities), 21)
        self.assertEqual(selected.status, "TEACHER_SELECTED")
        self.assertEqual(calls, 1)

    def test_planning_generation_rejects_in_memory_parent_mutation(self):
        from bilqis_mlx.runtime.priority_source_offer import _require_planning_generation

        (_pointer, _before, _after, context, selected, _rows,
         _pointer_bytes, _event_bytes) = self._exercise_journey()
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
