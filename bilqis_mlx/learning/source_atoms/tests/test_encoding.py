"""Source-owned raw atoms remain differentiable through the real B03 entrypoint."""
from dataclasses import replace
from pathlib import Path
from types import SimpleNamespace
from unittest import TestCase, skipUnless
from unittest.mock import patch

import mlx.core as mx
import numpy as np

from bilqis_mlx.errors import BilqisError
from bilqis_mlx.learning.frame_encoder import CompiledEncoderInput
from bilqis_mlx.learning.frame_embeddings import semantic_bank_views
from bilqis_mlx.learning.source_atoms import SourceAtomRow, encode_source_compiled
from bilqis_mlx.learning.source_atoms.embedding import source_atom_vectors
from bilqis_mlx.runtime.atlas_artifact_owner import AtlasFeatureArtifactOwner
from bilqis_mlx.runtime.tests.test_atlas_revalidation import (
    AUTHORITY, _event, _result,
)
from bilqis_mlx.runtime.model_topology_v2 import (
    GenerationExtents, ModelTopologySpecV2, expected_bamf_shapes,
)
from bilqis_mlx.semantics.atlas_features import FeatureSchema, build_feature_manifest
from bilqis_mlx.semantics.atlas.snapshot import load_pinned_atlas_snapshot
from bilqis_mlx.semantics.context_eligibility import (
    PUBLIC_FORMAL, ContextEligibility, ContextMember, SourceFrontier, SourceGrant,
    frame_evidence_digest, member_evidence_digest, project_context,
)
from bilqis_mlx.semantics.frame_compiler import (
    StreamingAST, compile_prefix_rows, validate_partial_visible_forest,
)
from bilqis_mlx.semantics.frame_schema import FrameTree, SourceSpan, atomic_fallback
from bilqis_mlx.source_adapters.tests.atoms.helpers import REAL_BUNDLE, source_case


class SourceEmbeddingBoundaryTests(TestCase):
    def test_generation_drift_precedes_owner_and_source_handoff_work(self):
        release = "a" * 64
        selection = SimpleNamespace(
            release_sha256=release,
            bundle_id="bundle",
            source_bundle_id="source-bundle")
        source = SourceAtomRow(
            selection, {}, {}, Path("."), 0, 1)
        snapshot = SimpleNamespace(
            release_sha256=release,
            bundle_id="bundle",
            source_bundle_id="source-bundle")
        features = SimpleNamespace(
            semantic_release=release,
            atlas_bundle_id="bundle",
            source_bundle_id="source-bundle",
            digest="d" * 64)
        extents = SimpleNamespace(factor_map_digest=features.digest)
        owner = object.__new__(AtlasFeatureArtifactOwner)
        with patch.object(
                AtlasFeatureArtifactOwner, "require",
                side_effect=AssertionError("artifact owner reached")), \
                patch(
                    "bilqis_mlx.learning.source_atoms.embedding."
                    "_build_source_atom_handoff_from_snapshot",
                    side_effect=AssertionError("source handoff reached")):
            with self.assertRaises(BilqisError) as caught:
                source_atom_vectors(
                    None, None, None, source, features, None, extents, (),
                    owner, snapshot=snapshot)
        self.assertEqual(
            caught.exception.context["reason"],
            "BAMF_SOURCE_ATOM_GENERATION_DRIFT")


@skipUnless(REAL_BUNDLE, "real pinned A01 artifact not mounted")
class SourceEncodingTests(TestCase):
    def setUp(self):
        ast, self.config, _, _, selection, row, graph, args = source_case(visible_end=2)
        self.source = SourceAtomRow(selection, row, graph, **args)
        self.snapshot = load_pinned_atlas_snapshot(selection)
        self.active_indices = tuple(
            entry.index for entry in self.snapshot.abi_entries if entry.active)
        self.schema = FeatureSchema((), ())
        features = build_feature_manifest(self.snapshot, self.schema)
        extents = GenerationExtents(
            1 + max(entry.bank for entry in self.snapshot.abi_entries), 1,
            self.snapshot.active_set_sha256, "b" * 64, features.digest)
        rows = compile_prefix_rows(((ast, 2, self.config),), self.snapshot.release_sha256)
        self.compiled = CompiledEncoderInput(rows, (self.config,), features, extents)
        self.artifact_owner = AtlasFeatureArtifactOwner(features, self.schema)
        self.parameters = {
            item.name: mx.zeros(item.shape, dtype=mx.float32)
            for item in expected_bamf_shapes(ModelTopologySpecV2(), extents)}
        self.parameters["features.norm"] = mx.ones((768,), dtype=mx.float32)
        self.parameters["identity.bank.0"] = (
            self.parameters["identity.bank.0"].at[:228, 0].add(.2).at[:228, 1].add(.6))
        self.parameters["features.type"] = self.parameters["features.type"].at[1, 0].add(.1)
        self.parameters["features.project_type"] = (
            self.parameters["features.project_type"].at[2, 0].add(1))

    def encode(self, parameters=None, compiled=None, source=None):
        actual_parameters = self.parameters if parameters is None else parameters
        actual_compiled = self.compiled if compiled is None else compiled
        banks = semantic_bank_views(
            actual_parameters, actual_compiled.extents,
            actual_compiled.features.semantic_release, self.active_indices)
        return encode_source_compiled(
            actual_compiled,
            actual_parameters,
            (self.source if source is None else source,), self.schema,
            banks,
            self.artifact_owner)

    def atomic_case(self, span_end=1):
        ast, config, _, _, selection, row, graph, args = source_case(
            visible_end=span_end)
        atomic = atomic_fallback(
            {"kind": "source-atom", "token": ast.atoms[0].token},
            source_instance_id=ast.source_instance_id, structural_path=(0,),
            source_span=SourceSpan(0, span_end), parent_occurrence_id=None,
            causal_prefix_end=span_end)
        frame_handle = "source-atomic:test:frame"
        member = ContextMember(
            "<atomic>", 0, "source-atomic:test:member", span_end)
        envelope = ContextEligibility(
            frame_handle, atomic, "source-atomic:test:source", (member,),
            config.task.principal_id, config.task.tenant_id, config.task.purpose,
            PUBLIC_FORMAL, self.snapshot.release_sha256,
            config.task.jurisdiction, config.task.scope, PUBLIC_FORMAL,
            config.policy.policy_epoch, config.frontier.rights_epoch,
            config.frontier.correction_generation, 0, 0, None, span_end)
        grants = list(config.frontier.grants)
        for handle, digest in (
            (envelope.source_handle, frame_evidence_digest(atomic)),
            (member.source_handle, member_evidence_digest(atomic, member)),
        ):
            grants.append(SourceGrant(
                handle, config.task.principal_id, config.task.tenant_id,
                PUBLIC_FORMAL, self.snapshot.release_sha256, digest,
                (config.task.purpose,), (config.task.jurisdiction,),
                (config.task.scope,), config.frontier.rights_epoch,
                config.frontier.correction_generation, 0, 0))
        frontier = SourceFrontier(
            config.frontier.rights_epoch, config.frontier.correction_generation,
            tuple(sorted(grants, key=lambda item: item.source_handle)))
        projection = project_context(
            (envelope,), config.task, frontier, config.policy)
        config = replace(config, approved=projection, frontier=frontier)
        ast = StreamingAST(
            ast.source_instance_id, ast.atoms, (FrameTree(atomic),))
        rows = compile_prefix_rows(
            ((ast, span_end, config),), self.snapshot.release_sha256)
        receipt = validate_partial_visible_forest(rows.rows[0], ast, config)
        compiled = CompiledEncoderInput(
            rows, (config,), self.compiled.features, self.compiled.extents,
            source_asts=(ast,), partial_forest_receipts=(receipt,))
        return compiled, SourceAtomRow(selection, row, graph, **args)

    def test_real_b03_result_matches_literal_source_owned_identity_and_factor_equation(self):
        before = {key: id(value) for key, value in self.parameters.items()}
        result = self.encode()
        vector = np.zeros(768, dtype=np.float32)
        vector[:3] = [.2, .6, .05]
        expected = vector / np.sqrt(np.mean(vector * vector) + 1e-5)
        np.testing.assert_allclose(np.asarray(result.global_seeds),
                                   np.broadcast_to(expected, (1, 2, 768)),
                                   rtol=1e-6, atol=1e-6)
        self.assertIs(result.compiled, self.compiled.compiled)
        self.assertEqual({key: id(value) for key, value in self.parameters.items()}, before)

    def test_gradients_reach_actual_b01_identity_and_factor_coordinates(self):
        def loss(parameters):
            return self.encode(parameters).global_seeds[..., 2].sum()

        gradients = mx.grad(loss)(self.parameters)
        actual_indices = self.source.source_row["tokens"][:2]
        selected = gradients["identity.bank.0"][mx.array(actual_indices), 2]
        self.assertTrue(bool(mx.all(mx.isfinite(selected))))
        self.assertTrue(bool(mx.all(mx.abs(selected) > 0)))
        self.assertGreater(float(mx.abs(gradients["features.project_type"][2, 0])), 0)
        self.assertGreater(float(mx.abs(gradients["features.type"][1, 0])), 0)
        self.assertEqual(float(mx.abs(gradients["identity.bank.1"]).sum()), 0)

    def test_atomic_fallback_reuses_exact_source_atom_embedding_and_gradient(self):
        compiled, source = self.atomic_case()
        encoded = self.encode(compiled=compiled, source=source)
        np.testing.assert_array_equal(
            np.asarray(encoded.global_seeds[0, -1]),
            np.asarray(encoded.global_seeds[0, 0]))

        def loss(identity):
            parameters = {**self.parameters, "identity.bank.0": identity}
            return self.encode(
                parameters, compiled=compiled, source=source).global_seeds[0, -1, 2]

        gradient = mx.grad(loss)(self.parameters["identity.bank.0"])
        row = source.source_row["tokens"][0]
        self.assertGreater(float(mx.abs(gradient[row, 2])), 0)

    def test_multi_atom_atomic_fallback_remains_held_without_composition_law(self):
        compiled, source = self.atomic_case(span_end=2)
        with self.assertRaises(BilqisError) as caught:
            self.encode(compiled=compiled, source=source)
        self.assertEqual(
            caught.exception.context["reason"],
            "BAMF_SOURCE_ATOM_ATOMIC_FRAME_SPAN_UNAVAILABLE")

    def test_source_known_inactive_rows_do_not_force_unadmitted_bank_expansion(self):
        compiled = replace(self.compiled, extents=replace(
            self.compiled.extents, semantic_bank_count=1))
        parameters = {key: value for key, value in self.parameters.items()
                      if key != "identity.bank.1"}
        result = self.encode(parameters=parameters, compiled=compiled)
        np.testing.assert_array_equal(np.asarray(result.global_seeds),
                                      np.asarray(self.encode().global_seeds))

    def test_current_revocation_and_generation_drift_precede_vector_return(self):
        revoked = replace(self.config.frontier.grants[0], revoked=True)
        config = replace(self.config, frontier=replace(
            self.config.frontier, grants=(revoked, *self.config.frontier.grants[1:])))
        with self.assertRaises(BilqisError):
            changed = replace(self.compiled, compiler_configs=(config,))
            self.encode(compiled=changed)
        changed = replace(self.compiled, extents=replace(
            self.compiled.extents, active_semantic_digest="9" * 64))
        with self.assertRaises(BilqisError):
            self.encode(compiled=changed)

    def test_generation_drift_rejects_before_owner_or_source_handoff_work(self):
        banks = semantic_bank_views(
            self.parameters, self.compiled.extents,
            self.compiled.features.semantic_release, self.active_indices)
        drifted_extents = replace(
            self.compiled.extents, factor_map_digest="c" * 64)
        with patch.object(
                AtlasFeatureArtifactOwner, "require",
                side_effect=AssertionError("artifact owner reached")), \
                patch(
                    "bilqis_mlx.learning.source_atoms.embedding."
                    "_build_source_atom_handoff_from_snapshot",
                    side_effect=AssertionError("source handoff reached")):
            with self.assertRaises(BilqisError) as caught:
                source_atom_vectors(
                    self.parameters,
                    self.compiled.compiled.rows[0],
                    self.compiled.compiler_configs[0],
                    self.source,
                    self.compiled.features,
                    self.schema,
                    drifted_extents,
                    banks,
                    self.artifact_owner,
                    snapshot=self.snapshot)
        self.assertEqual(
            caught.exception.context["reason"],
            "BAMF_SOURCE_ATOM_GENERATION_DRIFT")

    def test_source_correction_holds_real_features_before_next_use(self):
        event = _event(self.artifact_owner.source_dependency)
        queue = self.artifact_owner.apply_correction(event, AUTHORITY)
        self.assertEqual(
            queue.held_artifact_ids,
            (self.artifact_owner.current_node.artifact_id,))
        with self.assertRaises(BilqisError) as caught:
            self.encode()
        self.assertEqual(caught.exception.context["reason"],
                         "BAMF_C09_ARTIFACT_HELD")

    def test_equal_revalidation_clears_hold_but_changed_output_rejects_old_features(self):
        event = _event(self.artifact_owner.source_dependency)
        self.artifact_owner.apply_correction(event, AUTHORITY)
        progress = self.artifact_owner.advance(
            _result(
                self.artifact_owner.current_node,
                digest=self.artifact_owner.current_node.content_digest,
                correction=event),
            AUTHORITY)
        self.assertEqual(progress.queue.pending, ())
        self.assertEqual(progress.queue.held_artifact_ids, ())
        self.encode()

        changed_owner = AtlasFeatureArtifactOwner(self.compiled.features, self.schema)
        changed_event = _event(changed_owner.source_dependency)
        changed_owner.apply_correction(changed_event, AUTHORITY)
        changed_owner.advance(_result(
            changed_owner.current_node, digest="c" * 64,
            correction=changed_event), AUTHORITY)
        with self.assertRaises(BilqisError) as caught:
            encode_source_compiled(
                self.compiled, self.parameters, (self.source,), self.schema,
                semantic_bank_views(
                    self.parameters, self.compiled.extents,
                    self.compiled.features.semantic_release, self.active_indices),
                changed_owner)
        self.assertEqual(caught.exception.context["reason"],
                         "BAMF_C09_ATLAS_FEATURE_CONTENT_DRIFT")

    def test_partial_parameter_tree_and_caller_atom_vectors_are_not_accepted(self):
        partial = {key: value for key, value in self.parameters.items()
                   if key != "blocks.11.ffn_in"}
        with self.assertRaises(BilqisError):
            self.encode(parameters=partial)
        with self.assertRaises(TypeError):
            encode_source_compiled(
                self.compiled, self.parameters, (self.source,), self.schema,
                semantic_bank_views(
                    self.parameters, self.compiled.extents,
                    self.compiled.features.semantic_release, self.active_indices),
                self.artifact_owner,
                atom_vectors=mx.zeros((1, 2, 768)))
