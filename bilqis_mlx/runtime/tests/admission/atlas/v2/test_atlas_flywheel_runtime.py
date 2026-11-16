"""C07.4 production composition over accepted B13 custody."""
from contextlib import ExitStack, redirect_stderr, redirect_stdout
import io
import hashlib
import json
from pathlib import Path
from types import SimpleNamespace
import unittest
from unittest.mock import ANY, patch

from bilqis_mlx.cli import main
from bilqis_mlx.factory.autonomy import (
    EvidenceReceipt,
    obligations_for_capability,
    record_evidence,
)
from bilqis_mlx.factory.atlas_frontier import next_atlas_delta
from bilqis_mlx.factory.atlas_frontier_progress import FrontierStatus
from bilqis_mlx.factory.tests.curriculum.frontier.test_atlas_frontier import _rights
from bilqis_mlx.runtime.atlas_admission import read_accepted_atlas_factory_release
from bilqis_mlx.runtime.atlas_admission_policy import AdmissionStatus
from bilqis_mlx.runtime.atlas_flywheel_runtime import AcceptedAtlasFlywheelSupervisor
from bilqis_mlx.runtime.autonomy_state import persist_autonomy_state
from bilqis_mlx.runtime.bamf_bundle import load_bamf_generation_authority
from bilqis_mlx.runtime.bamf_bundle.feature.acceptance import (
    accepted_binding_for_manifest,
    accepted_generation,
)
from bilqis_mlx.learning.champions import Checkpoint
from bilqis_mlx.runtime.tests.admission.atlas.v2.mixed_witness_support import (
    MixedWitnessSupport,
)
from bilqis_mlx.runtime.tests.admission.atlas.v2.test_c07_lease_closure_v2 import (
    _COMPACT_DECLARED,
)
from bilqis_mlx.runtime.tests.custody.bamf_bundle.helpers import shape_patch
from bilqis_mlx.semantics.atlas.snapshot import AtlasArtifactSelection
from bilqis_mlx.source_adapters import event_frames


class AcceptedAtlasFlywheelRuntimeTests(MixedWitnessSupport, unittest.TestCase):
    def _accepted_runtime_fixture(self):
        staged_seed = self.zero_id_stage()
        seed_handoff, seed_plan, seed_learner = self.capability_handoff(staged_seed)
        snapshot, event_candidate, schema, features = self.common_atlas()
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
        return (
            seed_handoff, seed_plan, seed_learner,
            snapshot, event_candidate, schema, features,
            selection, source_authority, combined,
        )

    def test_cold_supervisor_builds_a09_handoff_from_durable_b13_evidence(self):
        with shape_patch():
            (_seed_handoff, _seed_plan, _seed_learner,
             snapshot, event_candidate, schema, features,
             selection, source_authority, combined) = self._accepted_runtime_fixture()
            supervisor = AcceptedAtlasFlywheelSupervisor(
                self.run, self.parent_graph, reserve_gib=0.)
            with self.source_replay(snapshot, schema, features), patch(
                    "bilqis_mlx.runtime.atlas_flywheel_runtime."
                    "resolve_atlas_artifact_selection",
                    return_value=selection), patch(
                        "bilqis_mlx.runtime.atlas_flywheel_runtime."
                        "compile_semantic_curriculum",
                        return_value=event_candidate), patch(
                            "bilqis_mlx.runtime.atlas_flywheel_runtime."
                            "issue_source_context_transition_authority",
                            return_value=source_authority), patch(
                                "bilqis_mlx.runtime.atlas_flywheel_runtime."
                                "_candidate_frontier",
                                return_value=self.frontier), patch(
                                    "bilqis_mlx.runtime.atlas_flywheel_runtime."
                                    "live_source_registry",
                                    return_value=combined), patch(
                                        "bilqis_mlx.runtime.atlas_flywheel_runtime."
                                        "live_answer_registry",
                                        return_value=self.answer_registry), patch(
                                            "bilqis_mlx.source_adapters.school."
                                            "live_source_registry",
                                            return_value=combined), patch(
                                                "bilqis_mlx.factory.live_answers."
                                                "live_answer_registry",
                                                return_value=self.answer_registry):
                state = supervisor.load_state()
                self.assertTrue(state.epoch.staged_candidates)
                self.assertIs(
                    next_atlas_delta(state.epoch, state.learner_evidence, state.plan),
                    FrontierStatus.WAITING_FOR_EVIDENCE)
                ledger = state.learner_evidence.ledger
                for index, obligation in enumerate(obligations_for_capability(
                        state.epoch.current_release, "A.IDENTITY", plan=state.plan), 1):
                    ledger = record_evidence(
                        state.epoch.current_release,
                        ledger,
                        EvidenceReceipt(
                            obligation.obligation_id,
                            f"c07-runtime-prerequisite-{index}",
                            state.learner_evidence.checkpoint_sha256,
                            state.learner_evidence.optimizer_step,
                            hashlib.sha256(
                                f"c07-runtime-prerequisite:{index}".encode()
                            ).hexdigest(),
                            obligation.minimum_specimens,
                            True,
                        ),
                        plan=state.plan,
                        current_checkpoint_sha256=(
                            state.learner_evidence.checkpoint_sha256),
                        current_optimizer_step=state.learner_evidence.optimizer_step,
                    )
                persist_autonomy_state(
                    self.run, state.epoch.current_release,
                    plan=state.plan, ledger=ledger)
                state = supervisor.load_state()
                handoff = next_atlas_delta(
                    state.epoch, state.learner_evidence, state.plan)
                self.assertNotIsInstance(handoff, FrontierStatus, handoff)
                self.assertEqual(
                    handoff.staged_candidate.target_capability_id,
                    "D.EVENT_OCCURRENCE")

    def test_cold_runtime_type_publishes_real_capability_only_owner_without_neural_step(self):
        from bilqis_mlx.runtime.generated_grade import (
            _mint_generated_grade_authority,
        )
        with shape_patch():
            (handoff, plan, learner, snapshot, _event_candidate,
             schema, features, _selection, _source_authority,
             combined) = self._accepted_runtime_fixture()
            supervisor = AcceptedAtlasFlywheelSupervisor(
                self.run, self.parent_graph, reserve_gib=0.)
            checkpoint = Checkpoint(
                learner.checkpoint_sha256, "bundles/c07-runtime",
                learner.optimizer_step, True)
            parent, _manifest = load_bamf_generation_authority(
                self.run / "bamf-state.json")
            parent_step = parent.retained_state.optimizer_step
            generated_grade_authority = _mint_generated_grade_authority(type(
                "Proposal", (), {
                    "proposal_sha256": "a" * 64,
                    "current_release_sha256":
                        handoff.receipt.predecessor_release.release_sha256,
                    "a09_proposal_sha256": handoff.proposal.proposal_sha256,
                })())
            with self.source_replay(snapshot, schema, features), patch(
                "bilqis_mlx.runtime.atlas_flywheel_runtime.build_live_autonomy_plan",
                return_value=plan), patch(
                    "bilqis_mlx.runtime.generated_grade."
                    "_issue_generated_grade_admission_authority",
                    return_value=generated_grade_authority), patch(
                    "bilqis_mlx.runtime.atlas_flywheel_runtime."
                    "reconcile_live_autonomy_state",
                    return_value=learner.ledger), patch(
                        "bilqis_mlx.runtime.atlas_flywheel_runtime._accepted_checkpoint",
                        return_value=checkpoint), patch(
                            "bilqis_mlx.runtime.atlas_flywheel_runtime."
                            "_candidate_frontier",
                            return_value=handoff.candidate_frontier), patch(
                                "bilqis_mlx.runtime.atlas_flywheel_runtime."
                                "live_source_registry",
                                return_value=combined), patch(
                                    "bilqis_mlx.runtime.atlas_flywheel_runtime."
                                    "live_answer_registry",
                                    return_value=self.answer_registry), patch(
                                        "bilqis_mlx.source_adapters.school."
                                        "live_source_registry",
                                        return_value=combined), patch(
                                            "bilqis_mlx.factory.live_answers."
                                            "live_answer_registry",
                                            return_value=self.answer_registry), self.z_operator_authority(
                                                handoff.staged_candidate):
                result = supervisor.admit(handoff)
            self.assertIs(result.status, AdmissionStatus.ADOPTED)
            self.assertTrue(result.requires_cold_resume)
            accepted, _manifest = load_bamf_generation_authority(
                self.run / "bamf-state.json")
            self.assertEqual(accepted.retained_state.optimizer_step, parent_step)
            self.assertEqual(
                read_accepted_atlas_factory_release(self.run).release_sha256,
                handoff.staged_candidate.successor.release_sha256)
            accepted_manifest = _manifest
            with self.assertRaisesRegex(
                    ValueError,
                    "BAMF_ATLAS_FLYWHEEL_ACCEPTED_PREDECESSOR_DRIFT"):
                supervisor.admit(handoff)
            replayed, replayed_manifest = load_bamf_generation_authority(
                self.run / "bamf-state.json")
            self.assertEqual(replayed_manifest, accepted_manifest)
            self.assertEqual(
                replayed.retained_state.optimizer_step,
                accepted.retained_state.optimizer_step)
            self.assertEqual(
                read_accepted_atlas_factory_release(self.run).release_sha256,
                handoff.staged_candidate.successor.release_sha256)


if __name__ == "__main__":
    unittest.main()
