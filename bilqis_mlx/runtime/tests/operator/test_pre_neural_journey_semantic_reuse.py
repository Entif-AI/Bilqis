"""Semantic-context reuse guards for the neural-inert production journey."""
from dataclasses import replace
import unittest
from unittest.mock import patch

from bilqis_mlx.errors import BilqisError
from bilqis_mlx.factory.adapters import SourceAdapterRegistry
from bilqis_mlx.factory.generation import runtime_adapter_for_release
from bilqis_mlx.factory.teaching import describe_delivered_teaching
from bilqis_mlx.factory.schedule import schedule_program_from_executable_release
from bilqis_mlx.runtime.accepted_priority_visit import (
    accepted_priority_school, execute_accepted_priority_candidate,
)
from bilqis_mlx.runtime.atlas_model_microbatch import microbatch_compatible
from bilqis_mlx.runtime.backbone_identity import execution_generation_digest
from bilqis_mlx.runtime.b11_source_execution_authority import (
    b11_source_authority_launch_epoch,
    bind_b11_source_execution_authority,
)
import bilqis_mlx.runtime.b11_source_execution_authority as b11_authority_impl
from bilqis_mlx.runtime.bamf_operator.session import _Capture, _execution_context, _step_seed
from bilqis_mlx.runtime.factory_candidate_training import FactoryDeliveryObservation
from bilqis_mlx.runtime.factory_task_authority import factory_task_authority
from bilqis_mlx.runtime.factory_training_bridge import prepare_factory_training_batch
from bilqis_mlx.runtime.foundation_teacher_owner import select_foundation_priority_visit
from bilqis_mlx.runtime.tests.batch.training.visit_provenance_support import visit_provenance

from .pre_neural_journey_support import (
    PreNeuralJourneySupport, historical_school_release, journey_source,
    portable_atlas_snapshot, wide_shape_patch,
)


class PreNeuralJourneySemanticReuseTests(PreNeuralJourneySupport, unittest.TestCase):
    def test_historical_b_and_binds_b11_to_emitted_source_owner(self):
        self.current, self.parent_graph = historical_school_release()
        snapshot = portable_atlas_snapshot()
        schema, features, atlas_selection = journey_source(snapshot)
        with wide_shape_patch(len(snapshot.abi_entries)):
            self.publish_matching_genesis(snapshot, schema, features)
            with self.journey_mounts(snapshot, schema, features, atlas_selection):
                parent, context, atlas_path, feature_path = _execution_context(self.run)
                rows = tuple(context.draw_rows(
                    seed=12345, capability="B.AND", each=4))
                execution = context.release.execution_plan.capability_map["B.AND"]
                delivery = describe_delivered_teaching(
                    context.release, "B.AND", execution.teaching_option_ids[0], rows)
                generation = execution_generation_digest(
                    parent.retained_state.optimizer.parameters,
                    spec=parent.topology, extents=parent.extents)
                prepared = prepare_factory_training_batch(
                    context, parent, atlas_path, feature_path, rows, generation,
                    capability="B.AND", delivery=delivery, requested_count=4,
                    source_seed=12345, source_each=4, optimizer_step_seed=7,
                    visit_provenance=visit_provenance("B.AND"),
                    teacher_strategy={"policy": "b11-source-owner-regression"})

        self.assertEqual(len(prepared.compiled_rows), 4)
        self.assertEqual(
            execution.provider_id,
            "source.micro.boolean-identification/v1")
        for compiled in prepared.compiled_rows:
            authority = compiled.source_execution_authority
            self.assertEqual(
                authority.source_adapter.descriptor.adapter_id,
                "source.micro.boolean-connectives/v1")
            self.assertEqual(
                authority.source_handoff.source_adapter_id,
                authority.source_adapter.descriptor.adapter_id)

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

    def test_priority_planning_uses_authenticated_snapshot_without_loader_backed_compile(self):
        from bilqis_mlx.factory import skos_curriculum

        self.current, self.parent_graph = historical_school_release()
        snapshot = portable_atlas_snapshot()
        schema, features, atlas_selection = journey_source(snapshot)
        snapshot_compile = skos_curriculum._compile_semantic_curriculum_snapshot
        with wide_shape_patch(len(snapshot.abi_entries)):
            self.publish_matching_genesis(snapshot, schema, features)
            with self.journey_mounts(snapshot, schema, features, atlas_selection):
                parent, context, atlas_path, _feature_path = _execution_context(self.run)
                program = schedule_program_from_executable_release(context.release)
                school = accepted_priority_school(parent, program)
                with patch.object(
                        skos_curriculum, "compile_semantic_curriculum",
                        side_effect=AssertionError("planning reopened accepted Atlas")), patch.object(
                            skos_curriculum, "_compile_semantic_curriculum_snapshot",
                            wraps=snapshot_compile) as direct:
                    selected = select_foundation_priority_visit(
                        self.run, context, atlas_path, program=program, school=school)

        self.assertEqual(selected.status, "TEACHER_SELECTED")
        self.assertGreaterEqual(direct.call_count, 1)

    def test_priority_requalification_reuses_planning_generation_authority(self):
        from bilqis_mlx.runtime import priority_qualification

        with patch.object(
                priority_qualification, "_accepted_correction_registry",
                side_effect=AssertionError("requalification rebound correction authority")):
            (_pointer, _before, _after, _context, selected, _rows,
             _pointer_bytes, _event_bytes) = self.exercise_journey()
        self.assertEqual(selected.status, "TEACHER_SELECTED")


class PreNeuralB11OwnerAuthorityTests(PreNeuralJourneySupport, unittest.TestCase):
    def _prepared(self):
        self.current, self.parent_graph = historical_school_release()
        snapshot = portable_atlas_snapshot()
        schema, features, atlas_selection = journey_source(snapshot)
        prepared = {}
        with wide_shape_patch(len(snapshot.abi_entries)):
            self.publish_matching_genesis(snapshot, schema, features)
            with self.journey_mounts(snapshot, schema, features, atlas_selection):
                parent, context, atlas_path, feature_path = _execution_context(self.run)
                generation = execution_generation_digest(
                    parent.retained_state.optimizer.parameters,
                    spec=parent.topology, extents=parent.extents)
                for capability, seed in (("B.AND", 12345), ("B.COMPOSITE", 12346)):
                    rows = tuple(context.draw_rows(
                        seed=seed, capability=capability, each=4))
                    execution = context.release.execution_plan.capability_map[capability]
                    delivery = describe_delivered_teaching(
                        context.release, capability,
                        execution.teaching_option_ids[0], rows)
                    prepared[capability] = prepare_factory_training_batch(
                        context, parent, atlas_path, feature_path, rows, generation,
                        capability=capability, delivery=delivery, requested_count=4,
                        source_seed=seed, source_each=4, optimizer_step_seed=7,
                        visit_provenance=visit_provenance(capability),
                        teacher_strategy={"policy": "b11-owner-authority-regression"})
        return snapshot, context, prepared, parent, generation

    def test_broader_dispatch_provider_cannot_substitute_for_emitted_row_owner(self):
        snapshot, context, prepared, _parent, _generation = self._prepared()
        compiled = prepared["B.AND"].compiled_rows[0]
        execution = context.release.execution_plan.capability_map["B.AND"]
        broader = runtime_adapter_for_release(
            context.source_root, context.graph, context.release,
            context.source_registry, execution)

        with self.assertRaises(BilqisError) as caught:
            bind_b11_source_execution_authority(
                compiled.compiled.compiled.rows[0],
                compiled.compiled.compiler_configs[0], compiled.sources[0],
                broader, snapshot, compiled.compiled.features)
        self.assertEqual(caught.exception.code, "SCHOOL.BAMF_TRAINING_ADAPTER.INVALID")
        self.assertEqual(
            caught.exception.context["reason"],
            "B11_SOURCE_EXECUTION_OWNER_MISMATCH")

    def test_compatible_sibling_generator_cannot_substitute_for_row_owner(self):
        snapshot, context, prepared, _parent, _generation = self._prepared()
        compiled = prepared["B.AND"].compiled_rows[0]
        sibling = context.source_registry.resolve_owner(
            "bilqis.mlx.grade-b-composite-constructor/v1",
            compiled.sources[0].source_row["oracle"])

        with self.assertRaises(BilqisError) as caught:
            bind_b11_source_execution_authority(
                compiled.compiled.compiled.rows[0],
                compiled.compiled.compiler_configs[0], compiled.sources[0],
                sibling, snapshot, compiled.compiled.features)
        self.assertEqual(caught.exception.code, "SCHOOL.BAMF_TRAINING_ADAPTER.INVALID")
        self.assertEqual(
            caught.exception.context["reason"],
            "B11_SOURCE_EXECUTION_OWNER_MISMATCH")

    def test_replacement_execution_context_rejects_row_owner_registry_drift(self):
        _snapshot, context, prepared, _parent, _generation = self._prepared()
        compiled = prepared["B.AND"].compiled_rows[0]
        owner = compiled.source_execution_authority.source_adapter
        key = owner.descriptor.generator_id
        adapters = tuple(
            replace(item, descriptor=replace(
                item.descriptor, implementation_sha256="f" * 64))
            if item.descriptor.generator_id == key else item
            for item in context.source_registry._by_generator.values())
        replacement_context = replace(
            context, source_registry=SourceAdapterRegistry(adapters))

        with self.assertRaises(BilqisError) as caught:
            factory_task_authority(replacement_context, compiled)
        self.assertEqual(caught.exception.code, "SCHOOL.BAMF_TRAINING_ADAPTER.INVALID")
        self.assertEqual(
            caught.exception.context["reason"],
            "B11_SOURCE_EXECUTION_OWNER_DRIFT")

    def test_microbatch_rejects_rows_with_inconsistent_bound_owners(self):
        _snapshot, _context, prepared, _parent, _generation = self._prepared()
        self.assertFalse(microbatch_compatible((
            prepared["B.AND"].compiled_rows[0],
            prepared["B.COMPOSITE"].compiled_rows[0],
        )))

    def test_same_owner_b_and_rows_remain_vectorization_compatible(self):
        _snapshot, _context, prepared, _parent, _generation = self._prepared()
        self.assertTrue(microbatch_compatible((
            prepared["B.AND"].compiled_rows[0],
            prepared["B.AND"].compiled_rows[1],
        )))

    def test_pre_neural_owner_check_is_once_and_launch_trust_skips_inner_rechecks(self):
        _snapshot, context, prepared, _parent, _generation = self._prepared()
        compiled = prepared["B.AND"].compiled_rows[0]
        original_digest = b11_authority_impl._source_digest
        original_resolve = context.source_registry.resolve_owner

        with patch.object(
                b11_authority_impl, "_source_digest",
                wraps=original_digest) as source_digest, patch.object(
                    context.source_registry, "resolve_owner",
                    wraps=original_resolve) as resolve_owner:
            factory_task_authority(context, compiled)
            owner_checks = resolve_owner.call_count
            with b11_source_authority_launch_epoch((compiled,)):
                compiled.__post_init__()
                compiled.__post_init__()
        self.assertGreaterEqual(source_digest.call_count, 1)
        self.assertEqual(owner_checks, 1)
        self.assertEqual(resolve_owner.call_count, owner_checks)

if __name__ == "__main__":
    unittest.main()
