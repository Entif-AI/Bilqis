from __future__ import annotations

from dataclasses import replace
from copy import deepcopy
import json
from pathlib import Path
import unittest

from bilqis_mlx.boolean_composite import (
    CAPABILITY as BOOLEAN_COMPOSITE_CAPABILITY,
    GENERATOR as BOOLEAN_COMPOSITE_GENERATOR,
    ORACLE as BOOLEAN_COMPOSITE_ORACLE,
)
from bilqis_mlx.boolean_identification import (
    CAPABILITY as BOOLEAN_IDENTIFICATION_CAPABILITY,
    GENERATOR as BOOLEAN_IDENTIFICATION_GENERATOR,
    ORACLE as BOOLEAN_IDENTIFICATION_ORACLE,
)
from bilqis_mlx.errors import BilqisError
from bilqis_mlx.generated_assessment import digest
from bilqis_mlx.grade_a_probe import read_sources
from bilqis_mlx.live_grade_c import PLANS, draw as draw_numeric_rows, registry_graph
from bilqis_mlx.numeric_curriculum import draw_numeric as draw_numeric_constructions
from bilqis_mlx.semantics.atlas_projection import AbiEntry, AtlasCounts, FrozenAtlasSnapshot
from bilqis_mlx.semantics.atlas_features.formal import source_family_for_adapter
from bilqis_mlx.semantics.frame_adapters import (
    BOOLEAN_COMPOSITE_ADAPTER,
    BOOLEAN_CONNECTIVE_ADAPTER,
    BOOLEAN_IDENTIFICATION_ADAPTER,
    C13_EPISODE_ADAPTER,
    FINITE_NUMERIC_ADAPTER,
    MICRO_PREDICATE_ADAPTER,
    bind_registered_source_row,
    released_frame_adapter_ids,
    source_frame_strategy,
    source_graph_for_adapter,
)
from bilqis_mlx.semantics.frame_schema import (
    AtomicFrame,
    FrameInstance,
    FrameTree,
    SourceSpan,
    validate_frame_tree,
)
from bilqis_mlx.source_adapters.school import (
    A_ORACLE,
    B_ORACLE,
    C_ORACLE,
    live_source_registry,
)
from bilqis_mlx.source_adapters import event_frames


from .helpers import FrameAdapterTestCase, ROOT, SOURCE_ROOT, RELEASE, REGISTRY_PATH, _snapshot, _walk


class RegistryTests(FrameAdapterTestCase):
    def test_boolean_identification_release_binds_inherited_and_identification_rows(self):
        adapter = self.registry.require(
            BOOLEAN_IDENTIFICATION_GENERATOR, BOOLEAN_IDENTIFICATION_ORACLE)
        for capability in ("B.AND", BOOLEAN_COMPOSITE_CAPABILITY,
                           BOOLEAN_IDENTIFICATION_CAPABILITY):
            with self.subTest(capability=capability):
                row = adapter.draw(
                    source_root=SOURCE_ROOT,
                    graph=self.micro_graph,
                    course=None,
                    capability=capability,
                    seed=31,
                    each=4,
                )[0]
                tree = self._bind(adapter, row, self.micro_graph)
                self.assertIsInstance(tree, FrameTree)

    def test_released_adapter_ids_are_the_actual_current_source_registry_ids(self):
        expected = {
            MICRO_PREDICATE_ADAPTER,
            BOOLEAN_CONNECTIVE_ADAPTER,
            BOOLEAN_COMPOSITE_ADAPTER,
            BOOLEAN_IDENTIFICATION_ADAPTER,
            C13_EPISODE_ADAPTER,
            FINITE_NUMERIC_ADAPTER,
            event_frames.ADAPTER_ID,
        }
        actual = {
            adapter.descriptor.adapter_id
            for adapter in self.registry._by_generator.values()
            if adapter.descriptor.adapter_id in expected
        }
        self.assertEqual(set(released_frame_adapter_ids()), expected)
        self.assertEqual(actual, expected)

    def test_event_strategy_is_atomic_and_successor_specific(self):
        strategy = source_frame_strategy(event_frames.ADAPTER_ID)
        self.assertIsNone(strategy.source_family)
        expected = {
            "D.EVENT_OCCURRENCE": (
                event_frames.SYMBOLS["D.EVENT_OCCURRENCE"],),
            "D.COMMENCEMENT": (
                event_frames.SYMBOLS["D.EVENT_OCCURRENCE"],
                event_frames.SYMBOLS["D.COMMENCEMENT"],
            ),
            "D.TERMINATION": tuple(event_frames.SYMBOLS.values()),
        }
        for capability, included in expected.items():
            with self.subTest(capability=capability):
                root, graph = source_graph_for_adapter(
                    event_frames.ADAPTER_ID, row={"capability": capability})
                self.assertEqual(root, SOURCE_ROOT)
                present = tuple(
                    symbol for symbol in event_frames.SYMBOLS.values()
                    if symbol in graph["tokens"])
                self.assertEqual(present, included)

    def test_event_strategy_binds_provider_row_as_atomic_frame(self):
        adapter = self.registry.require(event_frames.GENERATOR, event_frames.ORACLE)
        _root, graph = source_graph_for_adapter(
            event_frames.ADAPTER_ID,
            row={"capability": "D.EVENT_OCCURRENCE"})
        row = adapter.draw(
            source_root=SOURCE_ROOT, graph=graph, course=None,
            capability="D.EVENT_OCCURRENCE", seed=1319, each=2)[0]
        tree = self._bind(adapter, row, graph, start=0, end=len(row["tokens"]))
        self.assertIsInstance(tree.root, AtomicFrame)
        self.assertEqual(
            tree.root.ast_construct,
            "source-task:" + event_frames.DIALECT)

    def test_released_family_mapping_is_strategy_owned_and_unknown_fails_closed(self):
        expected = {
            MICRO_PREDICATE_ADAPTER: "micro",
            BOOLEAN_CONNECTIVE_ADAPTER: "boolean",
            BOOLEAN_COMPOSITE_ADAPTER: "boolean",
            BOOLEAN_IDENTIFICATION_ADAPTER: "boolean",
            FINITE_NUMERIC_ADAPTER: "numeric",
            C13_EPISODE_ADAPTER: "numeric",
        }
        for adapter_id, family in expected.items():
            with self.subTest(adapter_id=adapter_id):
                self.assertEqual(source_family_for_adapter(adapter_id), family)
        for adapter_id in (event_frames.ADAPTER_ID, "source.unknown/v1"):
            with self.subTest(adapter_id=adapter_id):
                with self.assertRaises(BilqisError) as caught:
                    source_family_for_adapter(adapter_id)
                self.assertEqual(caught.exception.code, "SCHOOL.MODEL_TOPOLOGY.INVALID")


    def test_registered_adapter_error_carries_span_role_and_adapter_identity(self):
        adapter = self.registry.require(
            "bilqis_mlx.live_grade_b.draw_connectives", B_ORACLE)
        row = adapter.draw(
            source_root=SOURCE_ROOT,
            graph=self.micro_graph,
            course=None,
            capability="B.AND",
            seed=31,
            each=4,
        )[0]
        forged = {**row, "gold": "INVALID"}
        with self.assertRaises(BilqisError) as caught:
            self._bind(adapter, forged, self.micro_graph, start=44, end=61)
        self.assertEqual(
            caught.exception.code,
            "SEMANTIC_FRAME.ADAPTER.INVALID_SOURCE",
        )
        self.assertEqual(caught.exception.context["adapter_id"],
                         BOOLEAN_CONNECTIVE_ADAPTER)
        self.assertEqual(caught.exception.context["role_id"], "<source-row>")
        self.assertEqual(
            (caught.exception.context["span_start"], caught.exception.context["span_end"]),
            (44, 61),
        )


    def test_child_reference_must_match_actual_subtree_record(self):
        adapter = self.registry.require(
            "bilqis_mlx.live_grade_b.draw_connectives", B_ORACLE)
        row = adapter.draw(
            source_root=SOURCE_ROOT,
            graph=self.micro_graph,
            course=None,
            capability="B.AND",
            seed=31,
            each=4,
        )[0]
        tree = self._bind(adapter, row, self.micro_graph)
        self.assertTrue(tree.children)
        forged_tree = FrameTree(tree.root, tree.children[1:])
        with self.assertRaises(BilqisError) as caught:
            validate_frame_tree(forged_tree)
        self.assertEqual(caught.exception.code, "SEMANTIC_FRAME.BINDING.INVALID")
        self.assertEqual(caught.exception.context["role_id"], "<child-frame>")
