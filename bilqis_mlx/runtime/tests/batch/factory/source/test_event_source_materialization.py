"""#1319 event source-frame materialization through the generic Factory seam."""
from types import SimpleNamespace
from dataclasses import replace
import hashlib
import unittest

from bilqis_mlx.runtime.factory_training_source import _prepare_source_row
from bilqis_mlx.runtime.factory_training_context import (
    _source_frame_inventory_materialized,
)
from bilqis_mlx.runtime.priority_source_materialization import _prepare_model_sources
from bilqis_mlx.semantics.atlas_features import AtlasFeatures
from bilqis_mlx.semantics.atlas_projection import AbiEntry
from bilqis_mlx.semantics.frame_adapters import source_graph_for_adapter
from bilqis_mlx.semantics.frame_schema import AtomicFrame
from bilqis_mlx.semantics.tests.frame_adapters.helpers import ROOT, _snapshot
from bilqis_mlx.source_adapters import event_frames
from bilqis_mlx.source_adapters.school import live_source_registry
from bilqis_mlx.live_grade_c import registry_graph


class EventSourceMaterializationTests(unittest.TestCase):
    def _case(self):
        source_root, graph = source_graph_for_adapter(
            event_frames.ADAPTER_ID,
            row={"capability": "D.EVENT_OCCURRENCE"},
        )
        registry = live_source_registry()
        adapter = registry.require(event_frames.GENERATOR, event_frames.ORACLE)
        row = adapter.draw(
            source_root=source_root,
            graph=graph,
            course=None,
            capability="D.EVENT_OCCURRENCE",
            seed=1319,
            each=2,
        )[0]
        snapshot = _snapshot()
        event_index = graph["tokens"].index(
            event_frames.SYMBOLS["D.EVENT_OCCURRENCE"])
        node = graph["nodes"][event_index]
        event_entry = AbiEntry(
            event_index, 0, event_index, node["semantic_id"], node["id"],
            "EVENT_TEST_EXTENSION", True, True, "EVENT_TEST_EXTENSION")
        snapshot = replace(
            snapshot,
            prior_abi_sha256=hashlib.sha256(
                (ROOT / "bilqis_mlx/semantics/copular_registry_v1.json").read_bytes()
            ).hexdigest(),
            abi_entries=(*snapshot.abi_entries, event_entry),
            semantic_lookup=tuple(sorted((
                *snapshot.semantic_lookup,
                (event_entry.semantic_id, event_entry.index),
            ))),
        )
        selection = SimpleNamespace(
            release_sha256=snapshot.release_sha256,
            bundle_id=snapshot.bundle_id,
            source_bundle_id=snapshot.source_bundle_id,
        )
        source_context = SimpleNamespace(
            source_registry=registry,
            source_root=source_root,
            release=SimpleNamespace(curriculum=None),
            graph=registry_graph(),
        )
        features = AtlasFeatures(
            snapshot.release_sha256,
            snapshot.bundle_id,
            snapshot.source_bundle_id,
            None,
            (), (), (), (), (),
        )
        return source_context, selection, snapshot, features, row

    def test_event_inventory_materializes_atomic_frame_without_a03_manifest(self):
        source_context, selection, snapshot, _features, row = self._case()

        source_id, frames = _source_frame_inventory_materialized(
            source_context, row, selection, snapshot, None)

        self.assertEqual(source_id, row["source_id"])
        self.assertEqual(len(frames), 1)
        self.assertIsInstance(frames[0].root, AtomicFrame)
        self.assertEqual(
            frames[0].root.ast_construct,
            "source-task:" + event_frames.DIALECT,
        )

    def test_event_prepare_source_row_uses_schema_free_atomic_strategy(self):
        source_context, selection, snapshot, features, row = self._case()
        authenticated = SimpleNamespace(
            selection=selection,
            snapshot=snapshot,
            features=features,
        )

        prepared = _prepare_source_row(
            source_context,
            authenticated,
            None,
            None,
            row,
            capability="D.EVENT_OCCURRENCE",
            source_seed=1319,
            source_each=2,
        )

        self.assertEqual(prepared.source_id, row["source_id"])
        self.assertEqual(len(prepared.frames), 1)
        self.assertIsInstance(prepared.frames[0].root, AtomicFrame)
        self.assertEqual(prepared.config.schemas, ())
        self.assertEqual(prepared.config.schema_map.entries, ())
        self.assertIn(
            event_frames.SYMBOLS["D.EVENT_OCCURRENCE"],
            prepared.source_graph["tokens"],
        )

        model_sources, configs = _prepare_model_sources(
            source_context, authenticated, None, (prepared,))
        self.assertEqual(len(model_sources), 1)
        self.assertEqual(len(configs), 1)
        self.assertEqual(configs[0].schemas, ())
        self.assertEqual(model_sources[0].prefix.semantic_release, snapshot.release_sha256)
