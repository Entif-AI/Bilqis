"""Execution-owned B11 producer receipt and B05 adversaries."""
from copy import copy
from dataclasses import replace
from types import SimpleNamespace
from unittest import TestCase, skipUnless
from unittest.mock import patch

import mlx.core as mx
import numpy as np

from bilqis_mlx.errors import BilqisError
import bilqis_mlx.learning.source_atoms.backbone_receipt_runtime as receipt_runtime
import bilqis_mlx.learning.source_atoms.backbone_receipts as receipt_authority
from bilqis_mlx.learning.source_atoms.backbone import (
    complete_source_backbone_producer,
    start_source_backbone_producer,
)
from bilqis_mlx.learning.source_atoms.backbone_receipts import (
    ProducedBackboneBoundary, receipt_projection as _receipt_projection,
)
from bilqis_mlx.runtime.block_attnres import (
    DepthSummary, _numerical_depth_select, _rms_norm, depth_parameter_view,
    depth_select,
)
from bilqis_mlx.runtime.backbone_group_numerical import _content_digest
from bilqis_mlx.runtime.backbone_identity import execution_generation_digest
from bilqis_mlx.runtime.model_topology_v2 import ModelTopologySpecV2
from bilqis_mlx.semantics.domains import contract_digest
from bilqis_mlx.source_adapters.tests.atoms.helpers import REAL_BUNDLE
from bilqis_mlx.learning.source_atoms.tests.backbone_test_support import SourceBackboneTestBase


class SourceBackboneReceiptBoundaryTests(TestCase):
    def test_post_g1_receipt_reuses_bound_source_execution_authorities(self):
        authority = object()
        hidden = mx.zeros((1, 1, 768), dtype=mx.float32)
        expected = SimpleNamespace(
            hidden=hidden,
            execution_digest="e" * 64,
            layer_end=4,
            full_parameter_tree_digest="p" * 64,
            scope_content_digest="s" * 64,
            input_content_digest="i" * 64,
            cache_chain_digest="c" * 64,
        )
        motif = SimpleNamespace(
            hidden=hidden,
            participating_slots=(),
            dispositions=(("QUALIFIED_MISS",),),
            context_digests=("d" * 64,),
        )
        producer = SimpleNamespace(
            _compiled=SimpleNamespace(extents=object()),
            _parameters={},
            _sources=(object(),),
            _source_execution_authorities=(authority,),
            _motif_manifest=object(),
            _motif_seal=object(),
            _motif_read=None,
            _receipts=(SimpleNamespace(receipt_digest="r" * 64),),
        )

        def retained_read(*args, source_execution_authorities, **kwargs):
            self.assertIs(
                source_execution_authorities,
                producer._source_execution_authorities)
            return motif

        with patch.object(
                receipt_runtime, "_replay_to_result",
                return_value=(1, expected)), \
                patch.object(
                    receipt_runtime, "_read_retained_compiled_motifs",
                    side_effect=retained_read):
            values = receipt_runtime._group_receipt_values(
                producer,
                object(),
                "a" * 64,
                SimpleNamespace(digest="t" * 64),
                "g" * 64,
                "x" * 64,
                object(),
            )

        self.assertEqual(values["source_id"], "g1")
        self.assertIs(producer._motif_read, motif)


@skipUnless(REAL_BUNDLE, "real pinned A01 artifact not mounted")
class SourceBackboneReceiptTests(SourceBackboneTestBase):
    def test_receipt_minter_is_not_a_public_surface(self):
        self.assertFalse(hasattr(receipt_authority, "make_receipt"))
        self.assertFalse(hasattr(receipt_authority, "_issue_receipt"))
        self.assertFalse(hasattr(receipt_authority, "_PRODUCER_SEAL"))
        self.assertFalse(hasattr(receipt_authority, "_ISSUED_RECEIPTS"))
        self.assertFalse(hasattr(receipt_authority, "require_produced_backbone_boundary"))
        with self.assertRaises(BilqisError):
            receipt_authority._issue_from_producer(object())

    def test_receipts_are_evidence_not_a_standalone_selector_authority(self):
        producer = self.producer()
        producer.advance()
        features, view = self.depth_inputs(self.parameters)
        with self.assertRaises(BilqisError):
            depth_select(producer.receipts, features, view)

    def test_fabricated_exact_producer_shell_cannot_issue_arbitrary_group_bytes(self):
        producer = self.producer()
        producer.advance()
        result = producer._session.results[-1]
        foreign = result.hidden.at[0, 0, 0].add(.25)
        forged = replace(result, hidden=foreign)
        fake = object.__new__(type(producer))
        fake.__dict__.update(producer.__dict__)
        fake._session = SimpleNamespace(results=(forged,))
        fake._receipts = producer.receipts[:1]
        with self.assertRaises(BilqisError):
            receipt_authority._issue_from_producer(fake, forged)

    def test_producer_requires_selected_state_before_next_group(self):
        producer = self.producer()
        producer.advance()
        with self.assertRaises(BilqisError):
            producer.advance()

    def test_caller_cannot_supply_motif_context(self):
        with self.assertRaises(TypeError):
            start_source_backbone_producer(
                self.compiled, self.parameters, (self.source,), self.schema,
                self.banks(),
                self.artifact_owner,
                group1_motif=object())

    def test_producer_owns_h0_and_ordered_group_receipts(self):
        producer = self.producer()
        self.assertEqual(tuple(item.source_id for item in producer.receipts), ("h0",))
        receipts = [producer.receipts[0]]
        for index, expected in enumerate(("g1", "g2", "g3")):
            if index:
                features, view = self.depth_inputs(self.parameters, boundary=index)
                receipt = producer.advance(features, view)
            else:
                receipt = producer.advance()
            self.assertIs(type(receipt), ProducedBackboneBoundary)
            self.assertEqual(receipt.source_id, expected)
            self.assertEqual(receipt.predecessor_receipt_digest,
                             receipts[-1].receipt_digest)
            receipts.append(receipt)
        self.assertEqual(tuple(item.completed_layer for item in receipts), (0, 4, 8, 12))
        self.assertEqual(receipts[1].motif_disposition, "NO_HIT_QUARANTINED")
        self.assertEqual(receipts[1].motif_read_position,
                         "AFTER_LAYER_4_BEFORE_CAPTURE")
        self.assertNotEqual(receipts[1].motif_read_digest, contract_digest(()))
        self.assertEqual(tuple(item.motif_disposition for item in receipts[2:]),
                         ("NOT_APPLICABLE", "NOT_APPLICABLE"))

    def test_completion_owner_runs_all_three_groups_without_caller_depth_facts(self):
        producer = self.producer()
        completed = complete_source_backbone_producer(producer)
        self.assertIs(completed, producer)
        self.assertEqual(
            tuple(item.source_id for item in completed.receipts),
            ("h0", "g1", "g2", "g3"),
        )
        self.assertEqual(
            tuple(item.completed_layer for item in completed.receipts),
            (0, 4, 8, 12),
        )

    def test_g2_cannot_be_relabelled_as_g1_or_mixed_into_public_selector(self):
        producer = self.producer()
        first = producer.advance()
        features, view = self.depth_inputs(self.parameters)
        second = producer.advance(features, view)
        with self.assertRaises((TypeError, BilqisError)):
            replace(second, source_id="g1", completed_layer=4)
        original = producer._receipts
        producer._receipts = (original[0], second)
        try:
            with self.assertRaises(BilqisError):
                depth_select(producer, features, view)
        finally:
            producer._receipts = original

    def test_same_extents_different_parameter_tree_cannot_reuse_receipts(self):
        first = self.producer()
        changed = dict(self.parameters)
        changed["blocks.0.ffn_in"] = changed["blocks.0.ffn_in"].at[0, 0].add(.25)
        second = self.producer(changed)
        first_g1, second_g1 = first.advance(), second.advance()
        self.assertNotEqual(first_g1.parameter_tree_digest,
                            second_g1.parameter_tree_digest)
        self.assertNotEqual(first_g1.receipt_digest, second_g1.receipt_digest)
        features, view = self.depth_inputs(self.parameters)
        original = first._receipts
        first._receipts = (original[0], second_g1)
        try:
            with self.assertRaises(BilqisError):
                depth_select(first, features, view)
        finally:
            first._receipts = original

    def test_generation_prefix_and_cache_tampering_reject_before_b05(self):
        producer = self.producer()
        group = producer.advance()
        features, view = self.depth_inputs(self.parameters)
        for field in ("generation_digest", "prefix_digest", "cache_chain_digest"):
            forged = copy(group)
            object.__setattr__(forged, field, "f" * 64)
            with self.subTest(field=field), self.assertRaises(BilqisError):
                original = producer._receipts
                producer._receipts = (original[0], forged)
                try:
                    depth_select(producer, features, view)
                finally:
                    producer._receipts = original

    def test_recomputed_receipt_forgery_and_foreign_current_reject(self):
        producer = self.producer()
        group = producer.advance()
        features, view = self.depth_inputs(self.parameters)
        forged = copy(group)
        object.__setattr__(forged, "cache_chain_digest", "f" * 64)
        object.__setattr__(forged, "receipt_digest",
                           contract_digest(_receipt_projection(forged.__dict__)))
        with self.assertRaises(BilqisError):
            original = producer._receipts
            producer._receipts = (original[0], forged)
            try:
                depth_select(producer, features, view)
            finally:
                producer._receipts = original
        foreign = group.hidden.at[0, 0, 0].add(.125)
        with self.assertRaises(TypeError):
            depth_select(foreign, producer.receipts, features, view)

    def test_same_value_detached_receipt_hidden_does_not_own_b05_graph(self):
        parameters = dict(self.parameters)
        parameters["blocks.0.ffn_norm"] = mx.ones((768,), dtype=mx.float32)
        parameters["blocks.0.ffn_in"] = parameters["blocks.0.ffn_in"].at[0, 0].add(.1)
        parameters["blocks.0.ffn_out"] = parameters["blocks.0.ffn_out"].at[2, 0].add(.2)

        def objective(parameters):
            producer = self.producer(parameters)
            group = producer.advance()
            detached = copy(group)
            object.__setattr__(detached, "hidden", mx.stop_gradient(group.hidden))
            producer._receipts = (producer.receipts[0], detached)
            features, view = self.depth_inputs(parameters)
            return mx.sum(depth_select(producer, features, view)[..., 2])

        gradients = mx.grad(objective)(parameters)
        self.assertGreater(float(mx.abs(gradients["blocks.0.ffn_out"]).sum()), 0)

    def test_identity_tree_and_generation_extents_are_bound(self):
        changed = dict(self.parameters)
        changed["identity.bank.0"] = changed["identity.bank.0"].at[0, 0].add(.125)
        first, second = self.producer(), self.producer(changed)
        first_group, second_group = first.advance(), second.advance()
        self.assertNotEqual(first_group.parameter_tree_digest,
                            second_group.parameter_tree_digest)
        features, foreign_view = self.depth_inputs(changed)
        with self.assertRaises(BilqisError):
            depth_select(first, features, foreign_view)
        extents = replace(self.compiled.extents, active_semantic_digest="9" * 64)
        self.assertNotEqual(
            execution_generation_digest(
                self.parameters, spec=ModelTopologySpecV2(), extents=self.compiled.extents),
            execution_generation_digest(
                self.parameters, spec=ModelTopologySpecV2(), extents=extents))
        foreign_extents_view = depth_parameter_view(
            self.parameters, spec=ModelTopologySpecV2(), extents=extents,
            boundary_group=1)
        with self.assertRaises(BilqisError):
            depth_select(first, features, foreign_extents_view)

    def test_public_b05_matches_normalized_group_capture(self):
        parameters = dict(self.parameters)
        parameters["depth.norm"] = mx.ones((768,), dtype=mx.float32)
        producer = self.producer(parameters)
        group = producer.advance()
        features, view = self.depth_inputs(parameters)
        summaries = (
            DepthSummary("h0", 0, producer.receipts[0].hidden),
            DepthSummary("g1", 4, _rms_norm(group.hidden, view["norm"])),
        )
        expected = _numerical_depth_select(group.hidden, summaries, features, view)
        actual = depth_select(producer, features, view)
        np.testing.assert_allclose(np.asarray(actual), np.asarray(expected), atol=2e-6)

    def test_selected_g1_is_the_actual_g2_input(self):
        parameters = dict(self.parameters)
        parameters["depth.norm"] = mx.ones((768,), dtype=mx.float32)
        parameters["depth.value"] = parameters["depth.value"].at[0, 0].add(1)
        parameters["depth.output"] = parameters["depth.output"].at[0, 0].add(1)
        producer = self.producer(parameters)
        group = producer.advance()
        features, view = self.depth_inputs(parameters)
        selected = depth_select(producer, features, view)
        self.assertNotEqual(_content_digest(selected), group.output_digest)
        g2 = producer.advance(features, view)
        self.assertEqual(g2.input_digest, _content_digest(selected))
        self.assertNotEqual(g2.input_digest, group.output_digest)
        features2, view2 = self.depth_inputs(parameters, boundary=2)
        selected2 = depth_select(producer, features2, view2)
        self.assertNotEqual(_content_digest(selected2), g2.output_digest)
        g3 = producer.advance(features2, view2)
        self.assertEqual(g3.input_digest, _content_digest(selected2))
        self.assertNotEqual(g3.input_digest, g2.output_digest)

    def test_advance_rejects_stale_selected_boundary_before_next_group(self):
        parameters = dict(self.parameters)
        parameters["depth.norm"] = mx.ones((768,), dtype=mx.float32)
        producer = self.producer(parameters)
        producer.advance()
        features1, view1 = self.depth_inputs(parameters, boundary=1)
        producer.advance(features1, view1)
        with self.assertRaises(BilqisError):
            producer.advance(features1, view1)
        self.assertEqual(len(producer.receipts), 3)
        features2, view2 = self.depth_inputs(parameters, boundary=2)
        g3 = producer.advance(features2, view2)
        self.assertEqual(g3.source_id, "g3")

    def test_public_b05_selection_keeps_gradient_to_executed_backbone(self):
        parameters = dict(self.parameters)
        parameters["blocks.0.ffn_norm"] = mx.ones((768,), dtype=mx.float32)
        parameters["blocks.0.ffn_in"] = parameters["blocks.0.ffn_in"].at[0, 0].add(.1)
        parameters["blocks.0.ffn_out"] = parameters["blocks.0.ffn_out"].at[2, 0].add(.2)

        def objective(parameters):
            producer = self.producer(parameters)
            producer.advance()
            features, view = self.depth_inputs(parameters)
            selected = depth_select(producer, features, view)
            return mx.sum(selected[..., 2])

        gradients = mx.grad(objective)(parameters)
        self.assertGreater(float(mx.abs(gradients["blocks.0.ffn_out"]).sum()), 0)
        indices = mx.array(self.source.source_row["tokens"][:2])
        self.assertTrue(bool(mx.all(mx.abs(
            gradients["identity.bank.0"][indices, 2]) > 0)))
