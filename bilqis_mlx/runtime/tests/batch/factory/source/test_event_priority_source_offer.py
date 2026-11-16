"""#1319 D.EVENT proof through the selected priority-source owner seam."""
from contextlib import ExitStack
from pathlib import Path
from dataclasses import replace
from types import SimpleNamespace
import hashlib
import unittest
from unittest.mock import patch

from bilqis_mlx.factory.autonomy import EvidenceReceipt, obligations_for_capability, record_evidence
from bilqis_mlx.runtime.atlas_flywheel_runtime import (
    AcceptedAtlasFlywheelSupervisor,
    run_accepted_atlas_flywheel,
)
from bilqis_mlx.runtime.autonomy_state import persist_autonomy_state
from bilqis_mlx.runtime.bamf_operator.session_support import _execution_context
from bilqis_mlx.runtime.priority_source_offer import prepare_priority_source_offer
from bilqis_mlx.runtime.tests.admission.atlas.v2.mixed_witness_support import MixedWitnessSupport
from bilqis_mlx.runtime.tests.admission.atlas.v2.test_c07_lease_closure_v2 import _COMPACT_DECLARED
from bilqis_mlx.runtime.tests.custody.bamf_bundle.helpers import shape_patch
from bilqis_mlx.semantics.atlas.snapshot import AtlasArtifactSelection
from bilqis_mlx.semantics.atlas_features import build_feature_manifest
from bilqis_mlx.semantics.frame_schema import AtomicFrame
from bilqis_mlx.source_adapters import event_frames
from bilqis_mlx.factory.tests.curriculum.frontier.test_atlas_frontier import _rights


class EventPrioritySourceOfferTests(MixedWitnessSupport, unittest.TestCase):
    def _fixture(self):
        staged_seed = self.zero_id_stage()
        seed_handoff, _seed_plan, _seed_learner = self.capability_handoff(staged_seed)
        snapshot, event_candidate, schema, features = self.common_atlas()
        registry_path = (
            Path(__file__).resolve().parents[6]
            / "bilqis_mlx/semantics/copular_registry_v1.json")
        snapshot = replace(
            snapshot,
            prior_abi_sha256=hashlib.sha256(registry_path.read_bytes()).hexdigest())
        features = build_feature_manifest(snapshot, schema)
        selection = AtlasArtifactSelection(
            "/artifact", snapshot.bundle_id, snapshot.release_sha256,
            snapshot.source_bundle_id)
        source_frontier, policy = _rights()
        source_authority = SimpleNamespace(frontier=source_frontier, policy=policy)
        combined = self.combined_source_registry()
        self.publish_matching_genesis(snapshot, schema, features)
        self.issue_mixed_lease(
            seed_handoff, event_candidate, snapshot,
            event_capabilities=("D.EVENT_OCCURRENCE",))
        semantic_id = event_frames.atlas_semantic_id("D.EVENT_OCCURRENCE")
        source_nt = (
            f'<{semantic_id}> <http://www.w3.org/2004/02/skos/core#definition> '
            '"event occurrence semantic role"@en .\n').encode("utf-8")
        return SimpleNamespace(
            snapshot=snapshot, event_candidate=event_candidate, schema=schema,
            features=features, selection=selection, source_authority=source_authority,
            combined=combined, source_nt=source_nt)

    def _context(self, fixture):
        stack = ExitStack()
        stack.enter_context(self.source_replay(
            fixture.snapshot, fixture.schema, fixture.features))
        for target, value in (
                ("bilqis_mlx.runtime.atlas_flywheel_runtime.resolve_atlas_artifact_selection",
                 fixture.selection),
                ("bilqis_mlx.runtime.atlas_flywheel_runtime.compile_semantic_curriculum",
                 fixture.event_candidate),
                ("bilqis_mlx.runtime.atlas_flywheel_runtime.issue_source_context_transition_authority",
                 fixture.source_authority),
                ("bilqis_mlx.runtime.atlas_flywheel_runtime._candidate_frontier", self.frontier),
                ("bilqis_mlx.runtime.atlas_flywheel_runtime.live_source_registry", fixture.combined),
                ("bilqis_mlx.runtime.atlas_flywheel_runtime.live_answer_registry", self.answer_registry),
                ("bilqis_mlx.source_adapters.school.live_source_registry", fixture.combined),
                ("bilqis_mlx.factory.live_answers.live_answer_registry", self.answer_registry),
                ("bilqis_mlx.runtime.bamf_bundle.vocabulary.admission.resolve_atlas_source_bundle",
                 Path("/source"))):
            stack.enter_context(patch(target, return_value=value))
        for target in (
                "bilqis_mlx.runtime.bamf_bundle.feature_authority.load_pinned_atlas_snapshot",
                "bilqis_mlx.runtime.bamf_bundle.vocabulary.admission.load_pinned_atlas_snapshot",
                "bilqis_mlx.semantics.atlas.vocabulary_planning.load_pinned_atlas_snapshot",
                "bilqis_mlx.semantics.atlas.vocabulary_resources.load_pinned_atlas_snapshot",
                "bilqis_mlx.source_adapters.atoms.admission.load_pinned_atlas_snapshot"):
            stack.enter_context(patch(target, return_value=fixture.snapshot))
        stack.enter_context(patch(
            "bilqis_mlx.semantics.atlas.vocabulary_resources._verify_bundle",
            return_value=(fixture.snapshot.source_bundle_id,
                          {"canonical.nt": fixture.source_nt})))
        stack.enter_context(patch(
            "bilqis_mlx.runtime.bamf_bundle.vocabulary.admission.shutil.disk_usage",
            return_value=SimpleNamespace(free=1 << 50)))
        stack.enter_context(patch(
            "bilqis_mlx.runtime.bamf_bundle.currentness_transaction."
            "bind_source_authority_currentness",
            return_value=object()))
        stack.enter_context(patch("bilqis_mlx.runtime.mlx_checkpoint.assert_headroom"))
        return stack

    def _credit_identity_prerequisites(self, supervisor):
        state = supervisor.load_state()
        ledger = state.learner_evidence.ledger
        for index, obligation in enumerate(obligations_for_capability(
                state.epoch.current_release, "A.IDENTITY", plan=state.plan), 1):
            ledger = record_evidence(
                state.epoch.current_release, ledger,
                EvidenceReceipt(
                    obligation.obligation_id, f"event-source-prerequisite-{index}",
                    state.learner_evidence.checkpoint_sha256,
                    state.learner_evidence.optimizer_step,
                    hashlib.sha256(
                        f"event-source-prerequisite:{index}".encode()).hexdigest(),
                    obligation.minimum_specimens, True),
                plan=state.plan,
                current_checkpoint_sha256=state.learner_evidence.checkpoint_sha256,
                current_optimizer_step=state.learner_evidence.optimizer_step)
        persist_autonomy_state(
            self.run, state.epoch.current_release, plan=state.plan, ledger=ledger)

    def test_event_offer_require_current_materializes_generic_atomic_source(self):
        with patch(
                "bilqis_mlx.runtime.tests.custody.bamf_bundle.helpers.DECLARED",
                _COMPACT_DECLARED), patch(
                    "bilqis_mlx.runtime.topology_v2.serialization.expected_bamf_shapes",
                    return_value=_COMPACT_DECLARED), shape_patch():
            fixture = self._fixture()
            supervisor = AcceptedAtlasFlywheelSupervisor(
                self.run, self.parent_graph, reserve_gib=0.)
            with self._context(fixture):
                self._credit_identity_prerequisites(supervisor)
                admission = run_accepted_atlas_flywheel(
                    self.run, self.parent_graph, reserve_gib=0., max_advances=1)
                self.assertEqual(admission.advances, 1)

                parent, source_context, atlas_path, _feature_path = _execution_context(
                    self.run)
                offer = prepare_priority_source_offer(
                    source_context, parent, atlas_path,
                    capability="D.EVENT_OCCURRENCE", source_seed=1319, source_each=1)
                materialized = offer.require_current(source_context, parent)

        self.assertEqual(offer.source_authority.provider_id, event_frames.ADAPTER_ID)
        self.assertEqual(offer.source_family_id, offer.source_authority.source_family_id)
        self.assertIsNone(materialized.manifest)
        self.assertEqual(materialized.adapter.descriptor.adapter_id, event_frames.ADAPTER_ID)
        self.assertEqual(len(materialized.source_rows), 1)
        self.assertIsInstance(materialized.source_rows[0].frames[0].root, AtomicFrame)
        self.assertEqual(materialized.source_rows[0].config.schemas, ())
        self.assertEqual(materialized.source_rows[0].config.schema_map.entries, ())
        event_abi = fixture.snapshot.abi_for_semantic(
            event_frames.atlas_semantic_id("D.EVENT_OCCURRENCE"))
        event_graph_index = materialized.source_rows[0].source_graph["tokens"].index(
            event_frames.SYMBOLS["D.EVENT_OCCURRENCE"])
        self.assertEqual(event_abi.index, 2)
        self.assertNotEqual(event_graph_index, event_abi.index)
        self.assertIn(
            event_frames.SYMBOLS["D.EVENT_OCCURRENCE"],
            materialized.source_rows[0].source_graph["tokens"])
        self.assertEqual(len(materialized.model_sources), 1)
        self.assertEqual(
            materialized.model_sources[0].prefix.semantic_release,
            fixture.snapshot.release_sha256)


if __name__ == "__main__":
    unittest.main()
