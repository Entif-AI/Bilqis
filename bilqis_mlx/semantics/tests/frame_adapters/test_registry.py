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
from bilqis_mlx.semantics.frame_adapters import (
    BOOLEAN_COMPOSITE_ADAPTER,
    BOOLEAN_CONNECTIVE_ADAPTER,
    BOOLEAN_IDENTIFICATION_ADAPTER,
    C13_EPISODE_ADAPTER,
    FINITE_NUMERIC_ADAPTER,
    MICRO_PREDICATE_ADAPTER,
    bind_registered_source_row,
    released_frame_adapter_ids,
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
        }
        actual = {
            adapter.descriptor.adapter_id
            for adapter in self.registry._by_generator.values()
            if adapter.descriptor.adapter_id in expected
        }
        self.assertEqual(set(released_frame_adapter_ids()), expected)
        self.assertEqual(actual, expected)


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
