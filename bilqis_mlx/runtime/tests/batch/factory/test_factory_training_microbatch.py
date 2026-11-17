"""#1172 real-Factory C08 vectorized microbatch execution witnesses."""
from __future__ import annotations

import unittest
from types import SimpleNamespace
from unittest.mock import patch

import bilqis_mlx.runtime.atlas_model_microbatch as microbatch_impl
import bilqis_mlx.runtime.b11_source_execution_authority as b11_authority_impl
import bilqis_mlx.learning._engram.atlas_engram_source_context as motif_context_impl
import bilqis_mlx.learning.atlas_engram_reads.source_owner as motif_read_impl
import bilqis_mlx.learning.source_atoms.embedding as source_embedding_impl
import bilqis_mlx.semantics.atlas_features.formal as formal_features_impl
from bilqis_mlx.errors import BilqisError
from bilqis_mlx.learning._championship.adviser_supervision import (
    MentorRowInfluence, issue_mentor_supervision, mentor_policy_binding,
)
from bilqis_mlx.runtime.source_execution import source_content_digest
from bilqis_mlx.runtime.factory_candidate_microbatch import (
    execute_factory_logical_batch,
)
from bilqis_mlx.runtime.factory_candidate_training import _resource_plan

from .factory_training_bridge_support import FactoryTrainingBridgeFixture


class MentorDispatchContractTests(unittest.TestCase):
    def test_mentor_supervision_preserves_targets_and_forces_weighted_scalar_oracle(self):
        import bilqis_mlx.runtime.factory_candidate_microbatch as candidate_microbatch
        source_rows = (
            {"id": "row:one", "capability": "future:cap"},
            {"id": "row:two", "capability": "future:cap"},
        )
        compiled = tuple(SimpleNamespace(
            sources=(SimpleNamespace(source_row=row),)) for row in source_rows)
        prepared = SimpleNamespace(compiled_rows=compiled)
        supervision = issue_mentor_supervision(
            "d" * 64, "a" * 64, "test-policy", "b" * 64, 17,
            tuple(MentorRowInfluence(
                row["id"], row["capability"], source_content_digest((row,)),
                influence, 1, 0.0, ({"accepted": True},), ())
                for row, influence in zip(source_rows, (0.02, 0.08), strict=True)),
            physical_inference_launches=1, logical_direct_votes=1,
            logical_soup_votes=0.0)
        targets = ("target:one", "target:two")

        def row_inputs(_context, item, _snapshot, _generation):
            index = compiled.index(item)
            return f"bound:{index}", f"authority:{index}", targets[index], \
                f"mask:{index}", f"plan:{index}"

        def accumulate(plan, execute_row, *, execute_group):
            self.assertIsNone(execute_group((0, 1)))
            self.assertEqual(execute_row(0), "gradient:0")
            self.assertEqual(execute_row(1), "gradient:1")
            return "logical-gradient"

        with patch.object(candidate_microbatch, "_row_execution_inputs",
                          side_effect=row_inputs), patch.object(
                candidate_microbatch, "bamf_value_and_grad",
                side_effect=("gradient:0", "gradient:1")) as scalar, patch.object(
                candidate_microbatch, "bamf_microbatch_value_and_grad") as vectorized, patch.object(
                candidate_microbatch, "accumulate_logical_batch_gradients",
                side_effect=accumulate):
            result, authorities, returned_targets = execute_factory_logical_batch(
                {}, prepared, object(), object(), "generation", None, object(),
                mentor_supervision=supervision)

        self.assertEqual(result, "logical-gradient")
        self.assertEqual(authorities, ("authority:0", "authority:1"))
        self.assertEqual(returned_targets, targets)
        self.assertEqual(vectorized.call_count, 0)
        self.assertEqual(scalar.call_count, 2)
        for call, expected, multiplier in zip(
                scalar.call_args_list, targets, (1.02, 1.08), strict=True):
            self.assertIn(expected, call.args)
            self.assertEqual(call.kwargs["source_loss_multiplier"], multiplier)

    def test_mentor_supervision_rejects_stale_epoch_or_effective_policy(self):
        strategy = {"distill": 0.5, "lr": 0.01}
        binding = mentor_policy_binding("test-policy", strategy)
        row = {"id": "row:bound", "capability": "future:cap"}
        supervision = issue_mentor_supervision(
            "d" * 64, "a" * 64, "test-policy", binding, 17,
            (MentorRowInfluence(
                row["id"], row["capability"], source_content_digest((row,)),
                0.04, 1, 0.0, ({"accepted": True},), ()),),
            physical_inference_launches=1, logical_direct_votes=1,
            logical_soup_votes=0.0)
        supervision.require_current(
            "d" * 64, "a" * 64, "test-policy", binding, 17)
        with self.assertRaises(BilqisError) as caught:
            supervision.require_current(
                "d" * 64, "c" * 64, "test-policy", binding, 17)
        self.assertEqual(
            caught.exception.context["reason"],
            "MENTOR_SUPERVISION_CURRENTNESS_DRIFT")
        with self.assertRaises(BilqisError) as caught:
            supervision.require_current(
                "d" * 64, "a" * 64, "test-policy",
                mentor_policy_binding("test-policy", {**strategy, "distill": 0.75}),
                17)
        self.assertEqual(
            caught.exception.context["reason"],
            "MENTOR_SUPERVISION_CURRENTNESS_DRIFT")
        with self.assertRaises(BilqisError) as caught:
            supervision.require_current(
                "e" * 64, "a" * 64, "test-policy", binding, 17)
        self.assertEqual(
            caught.exception.context["reason"],
            "MENTOR_SUPERVISION_CURRENTNESS_DRIFT")
        with self.assertRaises(BilqisError) as caught:
            supervision.require_current(
                "d" * 64, "a" * 64, "test-policy", binding, 18)
        self.assertEqual(
            caught.exception.context["reason"],
            "MENTOR_SUPERVISION_CURRENTNESS_DRIFT")
        self.assertEqual(
            supervision.guidance_record(),
            {"schema": "bilqis.mlx.championship-guidance/v1",
             "rows": [{"row_id": "row:bound", "influence": 0.04}]})


class FactoryTrainingMicrobatchTests(FactoryTrainingBridgeFixture):
    def test_mentor_influence_preserves_gold_loss_and_uses_scalar_row_oracle(self):
        rows, prepared = self.prepare("B.AND", 37129, 4)
        resource_plan, _ = _resource_plan(prepared, self.candidate, None)
        parameters = dict(self.candidate.retained_state.optimizer.parameters)
        baseline, _, _ = execute_factory_logical_batch(
            parameters, prepared, self.context, prepared.semantic_context.snapshot,
            self.generation, None, resource_plan)
        supervision = issue_mentor_supervision(
            "d" * 64, "a" * 64, "test-policy", "b" * 64, 17,
            tuple(MentorRowInfluence(
                row["id"], row["capability"], source_content_digest((row,)),
                0.08, 1, 0.0, ({"accepted": True},), ()) for row in rows),
            physical_inference_launches=1, logical_direct_votes=1,
            logical_soup_votes=0.0)
        advised, authorities, targets = execute_factory_logical_batch(
            parameters, prepared, self.context, prepared.semantic_context.snapshot,
            self.generation, None, resource_plan, mentor_supervision=supervision)

        self.assertEqual(advised.vectorized_microbatches, 0)
        self.assertEqual(advised.scalar_fallback_rows, 4)
        self.assertEqual(advised.gradient_launches, 4)
        self.assertEqual(len(authorities), 4)
        self.assertEqual(len(targets), 4)
        self.assertAlmostEqual(
            float(advised.weighted_mean_loss.item()),
            float(baseline.weighted_mean_loss.item()) * 1.08,
            places=4)

    def test_b_and_exact_row_owner_executes_as_one_vectorized_microbatch(self):
        rows, prepared = self.prepare("B.AND", 37129, 4)
        resource_plan, _ = _resource_plan(prepared, self.candidate, None)

        gradient, authorities, targets = execute_factory_logical_batch(
            dict(self.candidate.retained_state.optimizer.parameters),
            prepared, self.context, prepared.semantic_context.snapshot,
            self.generation, None, resource_plan)

        self.assertEqual(resource_plan.groups, ((0, 1, 2, 3),))
        self.assertEqual(gradient.gradient_launches, 1)
        self.assertEqual(gradient.vectorized_microbatches, 1)
        self.assertEqual(gradient.scalar_fallback_rows, 0)
        self.assertEqual(len(targets), 4)
        self.assertEqual(
            tuple(item.source_execution_authority.source_adapter.descriptor.adapter_id
                  for item in prepared.compiled_rows),
            ("source.micro.boolean-connectives/v1",) * 4)
        self.assertEqual(
            tuple(item.source_row_id for item in authorities),
            tuple(row["id"] for row in rows))

    def test_four_distinct_factory_rows_use_one_vectorized_gradient_launch(self):
        rows, prepared = self.prepare("A.IDENTITY", 37172, 4)
        resource_plan, _ = _resource_plan(prepared, self.candidate, None)
        self.assertIs(
            prepared.compiled_rows[0].source_execution_authority.snapshot,
            prepared.semantic_context.snapshot,
        )
        original_source_digest = b11_authority_impl._source_digest

        def source_digest_outside_launch(source):
            if b11_authority_impl._LAUNCH_TRUST.get():
                self.fail("B11 rehashed source inside trusted gradient launch")
            return original_source_digest(source)

        with patch.object(
                b11_authority_impl, "_source_digest",
                side_effect=source_digest_outside_launch) as source_digest, \
                patch.object(
                motif_context_impl, "load_pinned_atlas_snapshot",
                side_effect=AssertionError("B11 reopened Atlas")) as atlas_reload, \
                patch.object(
                    motif_context_impl, "public_formal_context",
                    side_effect=AssertionError("B11 redrew motif source")) as motif_redraw, \
                patch.object(
                    motif_read_impl, "lookup_source_pinned_frame_schema",
                    side_effect=AssertionError("B11 reopened released frame schemas")) as schema_reload, \
                patch.object(
                    formal_features_impl, "load_pinned_atlas_snapshot",
                    side_effect=AssertionError("B11 reopened formal Atlas")) as formal_atlas, \
                patch.object(
                    formal_features_impl, "lookup_source_pinned_frame_schema",
                    side_effect=AssertionError("B11 reopened formal schema")) as formal_schema, \
                patch.object(
                    formal_features_impl, "source_graph_for_adapter",
                    side_effect=AssertionError("B11 reopened formal source graph")) as formal_graph, \
                patch.object(
                    source_embedding_impl, "_build_source_atom_handoff_from_snapshot",
                    side_effect=AssertionError("B11 rebuilt source handoff")) as atom_redraw, \
                patch.object(
                    source_embedding_impl, "_require_embedding_ready_from_snapshot",
                    side_effect=AssertionError("B11 revalidated source handoff")) as atom_recheck, \
                patch.object(
                    microbatch_impl, "_decode_bamf_producer_row",
                    wraps=microbatch_impl._decode_bamf_producer_row) as row_decode, \
                patch.object(
                    microbatch_impl, "loss_bearing_bamf",
                    wraps=microbatch_impl.loss_bearing_bamf) as row_loss:
            gradient, authorities, targets = execute_factory_logical_batch(
                dict(self.candidate.retained_state.optimizer.parameters),
                prepared, self.context, prepared.semantic_context.snapshot,
                self.generation, None, resource_plan)
        row_ids = tuple(row["id"] for row in rows)

        self.assertEqual(resource_plan.groups, ((0, 1, 2, 3),))
        self.assertEqual(gradient.gradient_launches, 1)
        self.assertEqual(gradient.vectorized_microbatches, 1)
        self.assertEqual(gradient.materialization_barriers, 1)
        self.assertEqual(gradient.scalar_fallback_rows, 0)
        self.assertGreaterEqual(gradient.wall_seconds, 0.0)
        self.assertEqual(atlas_reload.call_count, 0)
        self.assertEqual(motif_redraw.call_count, 0)
        self.assertEqual(schema_reload.call_count, 0)
        self.assertEqual(formal_atlas.call_count, 0)
        self.assertEqual(formal_schema.call_count, 0)
        self.assertEqual(formal_graph.call_count, 0)
        self.assertEqual(atom_redraw.call_count, 0)
        self.assertEqual(atom_recheck.call_count, 0)
        self.assertGreaterEqual(source_digest.call_count, 4)
        self.assertEqual(row_decode.call_count, 0)
        self.assertEqual(row_loss.call_count, 0)
        self.assertEqual(len(gradient.loss_executions), 4)
        self.assertEqual(len(targets), 4)
        self.assertEqual(
            tuple(item.source_row_id for item in authorities), row_ids)
        self.assertEqual(
            tuple(item.training_authority.source_row_id
                  for item in gradient.loss_executions),
            row_ids)


if __name__ == "__main__":
    unittest.main()
