"""#1172 real-Factory C08 vectorized microbatch execution witnesses."""
from __future__ import annotations

import unittest
from unittest.mock import patch

import bilqis_mlx.runtime.atlas_model_microbatch as microbatch_impl
import bilqis_mlx.learning._engram.atlas_engram_source_context as motif_context_impl
import bilqis_mlx.learning.atlas_engram_reads.source_owner as motif_read_impl
import bilqis_mlx.learning.source_atoms.embedding as source_embedding_impl
from bilqis_mlx.runtime.factory_candidate_microbatch import (
    execute_factory_logical_batch,
)
from bilqis_mlx.runtime.factory_candidate_training import _resource_plan

from .factory_training_bridge_support import FactoryTrainingBridgeFixture


class FactoryTrainingMicrobatchTests(FactoryTrainingBridgeFixture):
    def test_four_distinct_factory_rows_use_one_vectorized_gradient_launch(self):
        rows, prepared = self.prepare("A.IDENTITY", 37172, 4)
        resource_plan, _ = _resource_plan(prepared, self.candidate, None)
        with patch.object(
                motif_context_impl, "load_pinned_atlas_snapshot",
                side_effect=AssertionError("B11 reopened Atlas")) as atlas_reload, \
                patch.object(
                    motif_context_impl, "public_formal_context",
                    side_effect=AssertionError("B11 redrew motif source")) as motif_redraw, \
                patch.object(
                    motif_read_impl, "lookup_source_pinned_frame_schema",
                    side_effect=AssertionError("B11 reopened released frame schemas")) as schema_reload, \
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
                prepared, self.context, self.feature_context.snapshot,
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
        self.assertEqual(atom_redraw.call_count, 0)
        self.assertEqual(atom_recheck.call_count, 0)
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
