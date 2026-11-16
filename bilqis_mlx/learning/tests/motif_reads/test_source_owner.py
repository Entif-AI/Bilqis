"""Positive B08 read ownership across real source, A05 positions and retained state."""
from __future__ import annotations

from dataclasses import replace
import os
from types import SimpleNamespace
import unittest
from unittest.mock import patch

import mlx.core as mx

from bilqis_mlx.errors import BilqisError
from bilqis_mlx.learning._engram.tests.test_atlas_engram_source import (
    SourceQualifiedMotifTests,
)
from bilqis_mlx.learning.atlas_engram import MotifBudget
from bilqis_mlx.learning.atlas_engram_source import prepare_source_qualified_motifs
from bilqis_mlx.learning.atlas_engram_reads.source_owner import (
    _B13_EXECUTION_SEAL, _pad_motif_read_row, _read_retained_compiled_motifs,
)
from bilqis_mlx.learning.frame_encoder import CompiledEncoderInput
from bilqis_mlx.learning.source_atoms import SourceAtomRow
from bilqis_mlx.runtime.model_topology_v2 import (
    GenerationExtents, ModelTopologySpecV2, expected_bamf_shapes,
)
from bilqis_mlx.runtime.b11_source_execution_authority import (
    bind_b11_source_execution_authority, b11_source_authority_launch_epoch,
)
import bilqis_mlx.learning.atlas_engram_reads.numerical as numerical_impl
from bilqis_mlx.semantics.atlas_features import FeatureSchema, build_feature_manifest
from bilqis_mlx.semantics.atlas.snapshot import load_pinned_atlas_snapshot
from bilqis_mlx.semantics.context_eligibility import SourceFrontier
from bilqis_mlx.semantics.frame_adapters import bind_registered_source_row
from bilqis_mlx.semantics.frame_adapters.public_formal import public_formal_context
from bilqis_mlx.semantics.frame_codec import SchemaTagMap
from bilqis_mlx.semantics.frame_compiler import (
    FrameCompilerConfig, StreamingAST, compile_prefix_rows,
)
from bilqis_mlx.semantics.frame_schema import FrameInstance, SourceSpan
from bilqis_mlx.semantics.released_frame_schemas import (
    lookup_source_pinned_frame_schema,
)
from bilqis_mlx.source_adapters.atoms.admission import public_formal_atom_context


class SourceOwnedMotifReadBoundaryTests(unittest.TestCase):
    def test_mixed_width_row_padding_adds_only_none_positions_and_zero_features(self):
        short_positions, short_features = _pad_motif_read_row(
            (None, None), mx.ones((2, 128), dtype=mx.float32), 3)
        long_positions, long_features = _pad_motif_read_row(
            (None, None, None), mx.ones((3, 128), dtype=mx.float32), 3)
        stacked = mx.stack((short_features, long_features))
        self.assertEqual(short_positions, (None, None, None))
        self.assertEqual(long_positions, (None, None, None))
        self.assertEqual(stacked.shape, (2, 3, 128))
        self.assertTrue(bool(mx.all(stacked[0, :2] == 1)))
        self.assertTrue(bool(mx.all(stacked[0, 2] == 0)))
        self.assertTrue(bool(mx.all(stacked[1] == 1)))

    def test_wrong_private_seal_rejects_before_read_inputs_can_authorize(self):
        with self.assertRaises(BilqisError):
            _read_retained_compiled_motifs(
                None, None, (), None, spec=None, extents=None,
                site_index=1, hidden=None, seal=object())


@unittest.skipUnless(
    os.environ.get("BILQIS_ATLAS_REAL_ARTIFACT"),
    "real repo-pinned A01 artifact supplied at source turn-in",
)
class SourceOwnedMotifReadTests(unittest.TestCase):
    def _fixture(self):
        case = SourceQualifiedMotifTests()._case("A")
        selection, root, graph, adapter, row, task, policy, seed, each, profile = case
        task = replace(task, causal_prefix_end=len(row["tokens"]))
        snapshot = load_pinned_atlas_snapshot(selection)
        atom_ast, atom_config = public_formal_atom_context(
            selection, row, graph, source_root=root, source_seed=seed,
            source_each=each, task=task, frontier=SourceFrontier(1, 1, ()),
            policy=policy, source_profile_parameters=profile)
        projection, frontier = public_formal_context(
            adapter, row, snapshot, source_root=root, graph=graph,
            task_scope=task, source_frontier=atom_config.frontier, policy=policy,
            source_seed=seed, source_each=each,
            source_profile_parameters=profile)
        tree = bind_registered_source_row(
            adapter, row, snapshot, source_root=root, graph=graph,
            source_span=SourceSpan(0, len(row["tokens"])),
            causal_prefix_end=len(row["tokens"]))
        schema, _ = lookup_source_pinned_frame_schema(
            tree.root.frame_schema_id, tree.root.frame_schema_revision,
            source_family="micro", atlas_selection=selection)
        config = FrameCompilerConfig(
            (schema,), SchemaTagMap.from_schemas(selection.release_sha256, (schema,)),
            projection, task, frontier, policy)
        ast = StreamingAST(atom_ast.source_instance_id, atom_ast.atoms, (tree,))
        rows = compile_prefix_rows(
            ((ast, len(row["tokens"]), config),), selection.release_sha256)
        framed = tuple(item for item in projection.envelopes
                       if isinstance(item.frame, FrameInstance))
        roles = tuple(sorted({binding.role_id for item in framed
                              for binding in item.frame.bindings}))
        schemas = tuple(sorted({item.frame.frame_schema_id for item in framed}))
        feature_schema = FeatureSchema(
            roles, schemas, source_bindings=tuple(
                (schema_id, adapter.descriptor.adapter_id) for schema_id in schemas))
        features = build_feature_manifest(snapshot, feature_schema)
        approved, _ = prepare_source_qualified_motifs(
            adapter, row, selection, source_root=root, graph=graph,
            task_scope=task, source_frontier=SourceFrontier(1, 1, ()), policy=policy,
            source_seed=seed, source_each=each, source_profile_parameters=profile,
            budget=MotifBudget(64))
        manifest = approved.candidate.proposed.manifest
        extents = GenerationExtents(
            1, 1, snapshot.active_set_sha256, manifest.digest, features.digest)
        compiled = CompiledEncoderInput(rows, (config,), features, extents)
        spec = ModelTopologySpecV2()
        parameters = {
            item.name: mx.zeros(item.shape, dtype=mx.float32)
            for item in expected_bamf_shapes(spec, extents)}
        slot_id = next(slot.slot_id for slot in manifest.slots if slot.key.kind == "EXACT")
        parameters["motif.page.0"] = parameters["motif.page.0"].at[
            slot_id, 0].add(2.0)
        for site_index in (0, 1):
            parameters[f"motif.site.{site_index}.norm"] = mx.ones(
                (768,), dtype=mx.float32)
            projection = f"motif.site.{site_index}.projection"
            parameters[projection] = parameters[projection].at[0, 0].add(1.0)
        source = SourceAtomRow(selection, row, graph, root, seed, each, None, profile)
        self.adapter = adapter
        self.snapshot = snapshot
        self.features = features
        self.config = config
        hidden = mx.zeros(
            (1, len(rows.rows[0].positions), 768), dtype=mx.float32)
        return (
            compiled, parameters, source, feature_schema, manifest, spec, extents,
            hidden, slot_id)

    def test_bound_launch_reuses_exact_b08_context_without_requalification(self):
        (compiled, parameters, source, _feature_schema, manifest, spec, extents,
         hidden, _) = self._fixture()
        cold = _read_retained_compiled_motifs(
            compiled, parameters, (source,), manifest, spec=spec, extents=extents,
            site_index=1, hidden=hidden, seal=_B13_EXECUTION_SEAL)
        authority = bind_b11_source_execution_authority(
            compiled.compiled.rows[0], self.config, source, self.adapter,
            self.snapshot, self.features)
        batch = SimpleNamespace(
            source_execution_authority=authority,
            compiled=compiled,
            sources=(source,),
        )
        with patch.object(
                numerical_impl, "project_context",
                wraps=numerical_impl.project_context) as project_call:
            with patch.object(
                    numerical_impl, "_schema_grant_live",
                    wraps=numerical_impl._schema_grant_live) as live_call:
                with b11_source_authority_launch_epoch((batch,)):
                    bound = _read_retained_compiled_motifs(
                        compiled, parameters, (source,), manifest,
                        spec=spec, extents=extents, site_index=1,
                        hidden=hidden, seal=_B13_EXECUTION_SEAL,
                        source_execution_authorities=(authority,))
                project_call.assert_not_called()
                live_call.assert_not_called()
        mx.eval(cold.hidden, bound.hidden)
        self.assertTrue(bool(mx.allclose(cold.hidden, bound.hidden)))
        self.assertEqual(bound.dispositions, cold.dispositions)
        self.assertEqual(bound.context_digests, cold.context_digests)
        self.assertEqual(bound.participating_slots, cold.participating_slots)
        self.assertEqual(bound.row_participating_slots, cold.row_participating_slots)

    def test_retained_exact_slot_changes_only_the_a05_closure(self):
        (compiled, parameters, source, _feature_schema, manifest, spec, extents,
         hidden, slot_id) = self._fixture()
        result = _read_retained_compiled_motifs(
            compiled, parameters, (source,), manifest, spec=spec, extents=extents,
            site_index=1, hidden=hidden, seal=_B13_EXECUTION_SEAL)
        mx.eval(result.hidden)
        self.assertEqual(result.participating_slots, (slot_id,))
        self.assertEqual(result.dispositions[0][-1], "EXACT")
        self.assertEqual(set(result.dispositions[0][:-1]), {"MISS"})
        self.assertEqual(float(mx.abs(result.hidden[:, :-1] - hidden[:, :-1]).sum()), 0.0)
        self.assertEqual(float(result.hidden[0, -1, 0]), 1.0)

    def test_wrong_b13_seal_or_source_row_cannot_authorize_the_read(self):
        (compiled, parameters, source, _feature_schema, manifest, spec, extents,
         hidden, _) = self._fixture()
        with self.assertRaises(BilqisError):
            _read_retained_compiled_motifs(
                compiled, parameters, (source,), manifest, spec=spec, extents=extents,
                site_index=1, hidden=hidden, seal=object())
        forged = replace(source, source_row={**source.source_row, "gold": "forged"})
        with self.assertRaises(BilqisError):
            _read_retained_compiled_motifs(
                compiled, parameters, (forged,), manifest, spec=spec, extents=extents,
                site_index=1, hidden=hidden, seal=_B13_EXECUTION_SEAL)
