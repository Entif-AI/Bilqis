"""Source-backed B11 forward, loss, gradient, and update ownership."""
from dataclasses import replace
from types import SimpleNamespace
from unittest import TestCase, skipUnless
from unittest.mock import patch

import mlx.core as mx

from bilqis_mlx.errors import BilqisError
from bilqis_mlx.learning.atlas_acceptance import candidate_identity_digest
from bilqis_mlx.learning.atlas_candidate import (
    CandidateCustodyIdentity, CandidateState, begin_candidate,
)
from bilqis_mlx.learning.atlas_engram import MotifManifest
from bilqis_mlx.learning.atlas_engram_transaction import MotifAllocationSnapshot
from bilqis_mlx.learning.atlas_plasticity import (
    IdentityRowAge, PlasticityPolicy, group_eligibility,
)
from bilqis_mlx.learning.atlas_readout import (
    AnswerPlan, ControlAction, DecisionKind, DecisionOutput, DecisionSpec,
    ExecutionMode, compile_frame_output,
)
from bilqis_mlx.learning.source_atoms.tests.backbone_test_support import (
    SourceBackboneTestBase,
)
from bilqis_mlx.runtime.atlas_candidate_step import production_candidate_step
from bilqis_mlx.runtime.atlas_execution_binder import bind_execution_provenance
from bilqis_mlx.runtime.atlas_model import (
    BamfCompiledBatch, BamfGradientExecution, BamfLossExecution,
    bamf_value_and_grad, forward_bamf,
)
from bilqis_mlx.runtime._atlas_owner_ingress import apply_compiled_batch_correction
from bilqis_mlx.runtime.tests.test_atlas_revalidation import AUTHORITY, _event
from bilqis_mlx.runtime.tests.model.execution.active_semantic_rows_support import active_semantic_rows
from bilqis_mlx.runtime.atlas_optimizer import AdamWHyperparameters, AdamWStateTree
from bilqis_mlx.runtime.backbone_identity import execution_generation_digest
import bilqis_mlx.runtime.atlas_model_forward as forward_impl
from bilqis_mlx.runtime.bamf_bundle.execution_cache import (
    _new_execution_cache,
)
from bilqis_mlx.runtime.model_topology_v2 import (
    Initializer, ModelTopologySpecV2, expected_bamf_shapes,
)
from bilqis_mlx.runtime.topology_v2.ledger import bamf_parameter_census
from bilqis_mlx.semantics.frame_codec import SchemaTagMap
from bilqis_mlx.semantics.frame_schema import FrameSchema, RoleSpec, SourceSpan
from bilqis_mlx.semantics.released_frame_schemas import (
    load_released_frame_schemas, seal_released_frame_schemas,
)
from bilqis_mlx.source_adapters.tests.atoms.helpers import REAL_BUNDLE


@skipUnless(REAL_BUNDLE, "real pinned A01 artifact not mounted")
class AtlasModelSourceForwardTests(SourceBackboneTestBase):
    def _answer_plan(self, *, compiled=None, parameters=None):
        compiled = self.compiled if compiled is None else compiled
        parameters = self.parameters if parameters is None else parameters
        role_id = next(
            role for role, _row in compiled.features.role_map
            if role not in ("UNKNOWN", "NONE")
        )
        schema = FrameSchema(
            "frame:test-b11-forward", 1, "test:b11-forward",
            (RoleSpec(role_id, ("Entity",), 0, 1),),
            "ORDERED", "test",
        )
        manifest = seal_released_frame_schemas(
            (schema,),
            SchemaTagMap.from_schemas(self.snapshot.release_sha256, (schema,)),
            self.snapshot,
        )
        released = load_released_frame_schemas(
            manifest.canonical_bytes(),
            expected_sha256=manifest.digest,
            snapshot=self.snapshot,
        )
        domain = compile_frame_output(schema, released, compiled.features)
        generation = execution_generation_digest(
            parameters,
            spec=ModelTopologySpecV2(),
            extents=compiled.extents,
        )
        row = compiled.compiled.rows[0]
        return AnswerPlan(
            domain.modality_id,
            len(row.positions),
            (DecisionSpec(
                "finish", None, 0, DecisionKind.CONTROL,
                (ControlAction.END_FRAME,),
            ),),
            domain,
            self.snapshot,
            SourceSpan(0, 0),
            generation,
        )

    def test_forward_bamf_owns_source_backbone_and_typed_readout(self):
        batch = BamfCompiledBatch(
            self.compiled, (self.source,), self.schema,
            active_semantic_rows(self.compiled, self.active_indices))
        output = forward_bamf(
            self.parameters, batch, self._answer_plan(),
            ExecutionMode.INFERENCE, None)
        self.assertIs(output.execution_mode, ExecutionMode.INFERENCE)
        self.assertEqual(
            tuple(item.decision_id for item in output.decisions),
            ("finish",),
        )
        self.assertEqual(output.committed[0].value, ControlAction.END_FRAME)

    def test_forward_bamf_does_not_reload_atlas_or_feature_manifest(self):
        batch = BamfCompiledBatch(
            self.compiled, (self.source,), self.schema,
            active_semantic_rows(self.compiled, self.active_indices))
        plan = self._answer_plan()
        with patch(
                "bilqis_mlx.learning.source_atoms.embedding.load_pinned_atlas_snapshot",
                side_effect=AssertionError("B11 reloaded Atlas snapshot")), patch(
                    "bilqis_mlx.learning.source_atoms.embedding.build_feature_manifest",
                    side_effect=AssertionError("B11 rebuilt feature manifest")), patch(
                        "bilqis_mlx.source_adapters.atom_binding.load_pinned_atlas_snapshot",
                        side_effect=AssertionError("B11 atom binding reloaded Atlas snapshot")):
            output = forward_bamf(
                self.parameters, batch, plan, ExecutionMode.INFERENCE, None)
        self.assertEqual(output.committed[0].value, ControlAction.END_FRAME)

    def test_forward_preserves_atlas_feature_correction_hold_until_real_source_read(self):
        batch = BamfCompiledBatch(
            self.compiled, (self.source,), self.schema,
            active_semantic_rows(self.compiled, self.active_indices))
        event = _event(batch.atlas_feature_artifact_owner.source_dependency)
        self.assertIn(
            "ATLAS_FEATURE",
            apply_compiled_batch_correction(batch, event, AUTHORITY),
        )
        retained_owner = batch.atlas_feature_artifact_owner
        with self.assertRaises(BilqisError) as caught:
            forward_bamf(
                self.parameters, batch, self._answer_plan(),
                ExecutionMode.INFERENCE, None)
        self.assertIs(batch.atlas_feature_artifact_owner, retained_owner)
        self.assertEqual(
            caught.exception.context["reason"], "BAMF_C09_ARTIFACT_HELD")
