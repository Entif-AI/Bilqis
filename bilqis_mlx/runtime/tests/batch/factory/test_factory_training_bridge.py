"""Factory compilation and live B11 routing over current A/B/C sources."""
from __future__ import annotations

import unittest
from dataclasses import replace
from types import SimpleNamespace
from unittest.mock import patch

import mlx.core as mx

from bilqis_mlx.errors import BilqisError
from bilqis_mlx.semantics.cognitive_dependencies import (
    DependencyKind, DependencyRef,
)
from bilqis_mlx.learning.atlas_readout import DecisionKind, ExecutionMode
import bilqis_mlx.learning.atlas_engram_reads.source_owner as motif_read_impl
import bilqis_mlx.semantics.atlas_features.formal as formal_features_impl
from bilqis_mlx.runtime.atlas_model import bind_compiled_training_batch, forward_bamf
from bilqis_mlx.runtime.atlas_training_authority import (
    bind_logical_batch_training_authority,
)
from bilqis_mlx.runtime.b11_source_execution_authority import (
    b11_source_authority_launch_epoch,
    b11_source_authority_launch_trusted,
    require_b11_source_execution_authority,
)
import bilqis_mlx.runtime.b11_source_execution_authority as b11_authority_impl
import bilqis_mlx.learning.frame_encoder.compiled as frame_encoder_compiled_impl
from bilqis_mlx.runtime.cognitive_solver import (
    GenerationBinding, RouteKind, SolveBudget, SolveContext, solve_task,
)
from bilqis_mlx.runtime.factory_complete_solver import factory_evaluation_instrument
from bilqis_mlx.runtime.factory_task_authority import (
    factory_task_authority, factory_task_training_goal,
)
from bilqis_mlx.runtime.refinement_request import refinement_request_disposition
from bilqis_mlx.runtime.task_goal_readout import (
    b11_task_goal_proposer, task_goal_route_decisions, task_goal_route_plan,
    task_goal_training_targets,
)
from bilqis_mlx.semantics.frame_compiler import (
    PositionKind, prefix_inventory_evidence_digest, prefix_inventory_handle,
)

from .factory_training_bridge_support import FactoryTrainingBridgeFixture


class FactoryTrainingBridgeTests(FactoryTrainingBridgeFixture):
    def route_context(self, compiled):
        authority = factory_task_authority(self.context, compiled)
        plan = task_goal_route_plan(
            authority.goal, compiled, self.b11_snapshot(compiled),
            self.generation)
        return authority, plan

    def test_current_a_b_c_draws_bind_exact_c02_rows_into_b11(self):
        cases = (
            ("A.IDENTITY", 37101, 2),
            ("B.IDBOOLOPS", 37102, 1),
            ("C.NUMBER", 37103, 3),
        )
        for capability, seed, each in cases:
            with self.subTest(capability=capability):
                rows, prepared = self.prepare(capability, seed, each)
                self.assertEqual(len(prepared.training_batch.rows), each)
                self.assertEqual(len(prepared.compiled_rows), each)
                self.assertTrue(all(
                    batch.compiled.compiled.rows[0].positions
                    for batch in prepared.compiled_rows))
                if capability == "B.IDBOOLOPS":
                    self.assertTrue(all(
                        position.kind is PositionKind.ATOM
                        for batch in prepared.compiled_rows
                        for position in batch.compiled.compiled.rows[0].positions))
                for index, (source_row, training_row, compiled) in enumerate(zip(
                        rows, prepared.training_batch.rows,
                        prepared.compiled_rows)):
                    self.assertEqual(
                        compiled.compiled.compiled.rows[0],
                        training_row.model_input.prefix)
                    self.assertEqual(
                        compiled.training_authority.training_batch_sha256,
                        prepared.training_batch.authority_digest)
                    self.assertEqual(
                        compiled.training_authority.source_row_id, source_row["id"])
                    self.assertEqual(
                        compiled.training_authority.episode_id,
                        training_row.provenance.episode_id)
                    self.assertEqual(
                        compiled.training_authority.source_row_sha256,
                        training_row.provenance.source_row_content_sha256)
                    self.assertEqual(
                        compiled.training_authority.immediate_dependencies,
                        training_row.provenance.immediate_dependencies)
                    self.assertEqual(training_row.provenance.requested_count, each + 2)
                    self.assertEqual(training_row.provenance.delivered_count, each)
                    self.assertEqual(training_row.provenance.visit.capability_id, capability)
                    self.assertEqual(training_row.provenance.visit.run_seed, 17)
                    self.assertEqual(
                        training_row.provenance.teacher_strategy,
                        (("policy", "c02-parent-integration"),))
                    self.assertFalse(hasattr(compiled, "target"))
                    self.assertFalse(hasattr(compiled.compiled, "target"))
                    self.assertEqual(index, rows.index(source_row))

    def test_four_bound_rows_reuse_source_authority_at_both_motif_sites(self):
        _rows, prepared = self.prepare("A.IDENTITY", 37124, 4)
        parameters = self.candidate.retained_state.optimizer.parameters
        manifest = self.candidate.retained_state.allocations.manifest
        with patch.object(
                motif_read_impl, "source_qualified_motif_context",
                side_effect=AssertionError("B08 redrew motif source")), \
                patch.object(
                    motif_read_impl, "lookup_source_pinned_frame_schema",
                    side_effect=AssertionError("B08 reopened frame schemas")), \
                patch.object(
                    formal_features_impl, "load_pinned_atlas_snapshot",
                    side_effect=AssertionError("B08 reopened formal Atlas")), \
                patch.object(
                    formal_features_impl, "lookup_source_pinned_frame_schema",
                    side_effect=AssertionError("B08 reopened formal schema")), \
                patch.object(
                    formal_features_impl, "source_graph_for_adapter",
                    side_effect=AssertionError("B08 reopened formal source graph")):
            for site_index in (0, 1):
                for compiled in prepared.compiled_rows:
                    row = compiled.compiled.compiled.rows[0]
                    hidden = mx.zeros(
                        (1, len(row.positions), self.candidate.topology.width),
                        dtype=mx.float32)
                    result = motif_read_impl._read_retained_compiled_motifs(
                        compiled.compiled, parameters, compiled.sources, manifest,
                        spec=self.candidate.topology,
                        extents=self.candidate.extents,
                        site_index=site_index, hidden=hidden,
                        seal=motif_read_impl._B13_EXECUTION_SEAL,
                        source_execution_authorities=(
                            compiled.source_execution_authority,))
                    self.assertEqual(result.hidden.shape, hidden.shape)

    def test_training_bridge_registers_every_compiled_row_with_source_custody(self):
        with patch.object(
                type(self.context), "register_compiled_batch",
                autospec=True) as register:
            _rows, prepared = self.prepare("A.IDENTITY", 37116, 2)
        self.assertEqual(register.call_count, len(prepared.compiled_rows))
        self.assertEqual(
            tuple(call.args[1] for call in register.call_args_list),
            prepared.compiled_rows)

    def test_b11_row_preserves_refinement_owner_inputs(self):
        _rows, prepared = self.prepare("B.IDBOOLOPS", 37119, 1)
        training_row = prepared.training_batch.rows[0]
        compiled = prepared.compiled_rows[0]
        self.assertIs(compiled.visit_provenance, training_row.provenance.visit)

        prefix = compiled.compiled.compiled.rows[0]
        config = compiled.compiled.compiler_configs[0]
        handle = prefix_inventory_handle(prefix.source_instance_id, prefix.visible_end)
        grant = next(
            (item for item in config.frontier.grants
             if item.source_handle == handle),
            None,
        )
        self.assertIsNotNone(grant)
        self.assertEqual(grant.evidence_digest, prefix_inventory_evidence_digest(prefix))

        authority, plan = self.route_context(compiled)
        self.assertEqual(
            plan.refinement_request, refinement_request_disposition(authority.goal))

    def test_revalidated_frame_context_cannot_reuse_stale_training_authority(self):
        _rows, prepared = self.prepare("A.IDENTITY", 37101, 2)
        compiled = prepared.compiled_rows[0]
        owner = compiled.compiled.packed_frame_artifact_owner
        row = compiled.compiled.compiled.rows[0]
        nodes = owner.require_row(row)
        node = next(
            item for item in nodes
            if any(ref.kind is DependencyKind.TIME
                   and ref.key.startswith("time:asof:context:")
                   for ref in item.immediate_dependencies)
        )
        old_time = next(
            ref for ref in node.immediate_dependencies
            if ref.kind is DependencyKind.TIME
            and ref.key.startswith("time:asof:context:"))
        new_time = DependencyRef(
            DependencyKind.TIME, "time:asof:context:" + "f" * 64)
        new_dependencies = tuple(sorted(
            new_time if ref == old_time else ref
            for ref in node.immediate_dependencies))
        updated = replace(node, immediate_dependencies=new_dependencies)
        owner._install_context_revalidation(
            owner.index.replace_node(updated),
            SimpleNamespace(
                artifact_id=node.artifact_id,
                previous_content_digest=node.content_digest,
                new_content_digest=node.content_digest,
                new_dependencies=new_dependencies,
            ),
        )

        with self.assertRaises(BilqisError) as caught:
            compiled.__post_init__()
        self.assertEqual(
            caught.exception.context["reason"],
            "B11_TRAINING_AUTHORITY_CONTEXT_DRIFT")

    def test_bound_b11_source_authority_rejects_source_substitution(self):
        _rows, prepared = self.prepare("A.IDENTITY", 37122, 2)
        compiled = prepared.compiled_rows[0]
        source = compiled.sources[0]
        forged = replace(
            source, source_row={**source.source_row, "gold": "forged"})
        with self.assertRaises(BilqisError):
            require_b11_source_execution_authority(
                compiled.source_execution_authority,
                compiled.compiled.compiled.rows[0],
                compiled.compiled.compiler_configs[0],
                forged)

    def test_bound_b11_source_authority_rejects_in_place_row_drift(self):
        _rows, prepared = self.prepare("A.IDENTITY", 37123, 2)
        compiled = prepared.compiled_rows[0]
        source = compiled.sources[0]
        row = source.source_row
        marker = object()
        previous = row.get("_authority_drift_test", marker)
        row["_authority_drift_test"] = True
        try:
            with self.assertRaises(BilqisError):
                require_b11_source_execution_authority(
                    compiled.source_execution_authority,
                    compiled.compiled.compiled.rows[0],
                    compiled.compiled.compiler_configs[0],
                    source)
        finally:
            if previous is marker:
                row.pop("_authority_drift_test", None)
            else:
                row["_authority_drift_test"] = previous

    def test_launch_epoch_validates_source_once_and_trusts_inner_batch_checks(self):
        _rows, prepared = self.prepare("A.IDENTITY", 37124, 2)
        compiled = prepared.compiled_rows[0]
        authority = compiled.source_execution_authority
        row = compiled.compiled.compiled.rows[0]
        config = compiled.compiled.compiler_configs[0]
        source = compiled.sources[0]

        original_digest = b11_authority_impl._source_digest
        with patch.object(
                b11_authority_impl, "_source_digest", wraps=original_digest) as digest_call:
            with patch.object(
                    frame_encoder_compiled_impl, "project_context",
                    wraps=frame_encoder_compiled_impl.project_context) as project_call:
                with b11_source_authority_launch_epoch((compiled,)):
                    self.assertTrue(b11_source_authority_launch_trusted(
                        authority, row, config, source))
                    compiled.__post_init__()
                    compiled.compiled.__post_init__()
                self.assertFalse(b11_source_authority_launch_trusted(
                    authority, row, config, source))
                self.assertEqual(digest_call.call_count, 1)
                project_call.assert_not_called()

    def test_launch_epoch_rejects_in_place_row_drift_before_trust(self):
        _rows, prepared = self.prepare("A.IDENTITY", 37127, 2)
        compiled = prepared.compiled_rows[0]
        source_row = compiled.sources[0].source_row
        marker = object()
        previous = source_row.get("_launch_drift_test", marker)
        source_row["_launch_drift_test"] = True
        try:
            with self.assertRaises(BilqisError):
                with b11_source_authority_launch_epoch((compiled,)):
                    self.fail("drifted source row entered launch trust")
        finally:
            if previous is marker:
                source_row.pop("_launch_drift_test", None)
            else:
                source_row["_launch_drift_test"] = previous

    def test_b11_row_binding_rejects_sibling_row_substitution(self):
        rows, prepared = self.prepare("A.IDENTITY", 37104, 2)
        first = prepared.compiled_rows[0]
        with self.assertRaises(BilqisError):
            bind_compiled_training_batch(
                prepared.training_batch, first.compiled,
                first.sources, first.feature_schema,
                active_semantic_rows=first.active_semantic_rows, row_index=1)
        self.assertNotEqual(rows[0]["id"], rows[1]["id"])

    def test_c08_logical_batch_authority_rejects_partial_duplicate_and_foreign_rows(self):
        _rows, prepared = self.prepare("A.IDENTITY", 37120, 2)
        authorities = tuple(
            compiled.training_authority for compiled in prepared.compiled_rows)

        with self.assertRaises(BilqisError) as partial:
            bind_logical_batch_training_authority(
                prepared.training_batch, authorities[:1])
        self.assertEqual(
            partial.exception.context["reason"],
            "C08_LOGICAL_BATCH_AUTHORITY_INPUT_INVALID",
        )

        with self.assertRaises(BilqisError) as duplicate:
            bind_logical_batch_training_authority(
                prepared.training_batch, (authorities[0], authorities[0]))
        self.assertEqual(
            duplicate.exception.context["reason"],
            "C08_LOGICAL_BATCH_AUTHORITY_DRIFT",
        )

        _foreign_rows, foreign = self.prepare("A.IDENTITY", 37121, 2)
        with self.assertRaises(BilqisError) as stale:
            bind_logical_batch_training_authority(
                prepared.training_batch,
                (authorities[0], foreign.compiled_rows[1].training_authority),
            )
        self.assertEqual(
            stale.exception.context["reason"],
            "C08_LOGICAL_BATCH_AUTHORITY_DRIFT",
        )

    def test_current_a_b_c_score_through_one_b11_backend(self):
        parameters = self.candidate.retained_state.optimizer.parameters
        for capability, seed, each in (
                ("A.IDENTITY", 37101, 2),
                ("B.IDBOOLOPS", 37112, 1),
                ("C.NUMBER", 37103, 3)):
            with self.subTest(capability=capability):
                _, prepared = self.prepare(capability, seed, each)
                compiled = prepared.compiled_rows[0]
                _, plan = self.route_context(compiled)
                output = forward_bamf(
                    parameters, compiled, plan, ExecutionMode.INFERENCE, None)
                self.assertTrue(output.decisions)
                for decision in output.decisions:
                    self.assertTrue(bool(mx.all(mx.isfinite(decision.logits))))

    def test_live_b11_proposer_routes_source_binding_into_pure_operator(self):
        rows, prepared = self.prepare("A.IDENTITY", 37118, 2)
        compiled = prepared.compiled_rows[0]
        authority, plan = self.route_context(compiled)
        proposer = b11_task_goal_proposer(
            self.candidate.retained_state.optimizer.parameters,
            compiled, plan, authority)
        result = solve_task(
            authority.goal,
            SolveContext(authority.binding, neural_proposer=proposer),
            GenerationBinding(
                self.generation, authority.goal.semantic_release,
                authority.source_binding_sha256),
            SolveBudget(authority.goal.budget))
        receipt = result.dag_receipts[-1]
        node = authority.goal.expression_or_holes.nodes[0]
        legal = {ref.identity for ref in node.candidate_operand_refs[0]}
        self.assertIs(result.route, RouteKind.NEURAL_COMPOSITION)
        self.assertEqual(result.neural_calls, 1)
        self.assertEqual(result.local_refinement_calls, 0)
        self.assertEqual(sum(item.operation_count for item in result.dag_receipts), 1)
        self.assertEqual(receipt.executed_nodes, ("choice:root",))
        self.assertEqual(receipt.selected_bindings[0][1], "SELECT_BOOLEAN")
        self.assertIn(receipt.selected_bindings[0][2][0], legal)
        self.assertIn(result.answer.value, (False, True))
        self.assertEqual(rows[0]["capability"], "A.IDENTITY")

    def test_source_owner_mints_b10_operator_training_target(self):
        rows, prepared = self.prepare("C.ADD", 37115, 3)
        compiled = prepared.compiled_rows[0]
        authority = factory_task_authority(self.context, compiled)
        resolved = factory_task_training_goal(self.context, compiled, authority)
        targets, mask = task_goal_training_targets(authority.goal, resolved)
        route = task_goal_route_decisions(authority.goal)
        self.assertEqual(len(route), 1)
        self.assertIs(route[0].kind, DecisionKind.OPERATOR)
        self.assertEqual(targets[0].decision_id, route[0].decision_id)
        self.assertEqual(targets[0].value, "ADD")
        self.assertEqual(mask, {route[0].decision_id: True})
        self.assertEqual(rows[0]["capability"], "C.ADD")


if __name__ == "__main__":
    unittest.main()
