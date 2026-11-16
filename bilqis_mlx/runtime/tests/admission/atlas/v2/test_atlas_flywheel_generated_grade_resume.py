"""Human-resume production-parameter coverage for the accepted Atlas flywheel."""
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
    AutonomyActionKind, EvidenceReceipt, obligations_for_capability, record_evidence,
)
from bilqis_mlx.runtime.atlas_admission import read_accepted_atlas_factory_release
from bilqis_mlx.runtime.atlas_flywheel_runtime import AcceptedAtlasFlywheelSupervisor
from bilqis_mlx.runtime.atlas_flywheel_runtime import run_accepted_atlas_flywheel
from bilqis_mlx.runtime.generated_grade import propose_accepted_generated_grade
from bilqis_mlx.runtime.autonomy_live import LiveAutonomySession
from bilqis_mlx.runtime.bamf_operator.session import operate_bamf
from bilqis_mlx.runtime.autonomy_state import persist_autonomy_state
from bilqis_mlx.runtime.bamf_bundle import load_bamf_generation_authority
from bilqis_mlx.runtime.bamf_bundle.feature.acceptance import accepted_binding_for_manifest, accepted_generation
from bilqis_mlx.runtime.tests.admission.atlas.v2.mixed_witness_support import MixedWitnessSupport
from bilqis_mlx.runtime.tests.admission.atlas.v2.test_c07_lease_closure_v2 import _COMPACT_DECLARED
from bilqis_mlx.runtime.tests.custody.bamf_bundle.helpers import shape_patch
from bilqis_mlx.semantics.atlas.snapshot import AtlasArtifactSelection
from bilqis_mlx.source_adapters import event_frames
from bilqis_mlx.factory.tests.curriculum.frontier.test_atlas_frontier import _rights


from bilqis_mlx.runtime.tests.admission.atlas.v2.atlas_flywheel_human_resume_support import AcceptedAtlasFlywheelHumanResumeSupport

class AcceptedAtlasFlywheelGeneratedGradeResumeTests(AcceptedAtlasFlywheelHumanResumeSupport):
    def test_durable_a09_evidence_cold_reenters_c07_without_fabricated_mastery(self):
        """Neural-free A09/C07 composition witness; not the #1299 learner proof."""
        from bilqis_mlx.factory.atlas_frontier import next_atlas_delta
        from bilqis_mlx.factory.atlas_frontier_progress import FrontierStatus

        with patch(
                "bilqis_mlx.runtime.tests.custody.bamf_bundle.helpers.DECLARED",
                _COMPACT_DECLARED), patch(
                    "bilqis_mlx.runtime.topology_v2.serialization.expected_bamf_shapes",
                    return_value=_COMPACT_DECLARED), shape_patch():
            fixture = self._production_parameter_fixture()
            supervisor = AcceptedAtlasFlywheelSupervisor(
                self.run, self.parent_graph, reserve_gib=0.)
            with self._production_parameter_context(fixture):
                self._credit_identity_prerequisites(supervisor)
                parent, _manifest = load_bamf_generation_authority(
                    self.run / "bamf-state.json")
                parent_step = parent.retained_state.optimizer_step
                first = run_accepted_atlas_flywheel(
                    self.run, self.parent_graph, reserve_gib=0., max_advances=1)
                self.assertEqual(first.advances, 1)
                accepted_event, _manifest = load_bamf_generation_authority(
                    self.run / "bamf-state.json")
                self.assertEqual(
                    accepted_event.retained_state.optimizer_step, parent_step)
                self.assertEqual(
                    accepted_event.baseline_evidence, parent.baseline_evidence)
                self._close_event_evidence_without_neural_update()

                cold_supervisor = AcceptedAtlasFlywheelSupervisor(
                    self.run, self.parent_graph, reserve_gib=0.)
                cold = cold_supervisor.load_state()
                handoff = next_atlas_delta(
                    cold.epoch, cold.learner_evidence, cold.plan)
                self.assertNotIsInstance(handoff, FrontierStatus, handoff)
                self.assertEqual(
                    handoff.staged_candidate.target_capability_id,
                    "D.COMMENCEMENT",
                )
                cold_again_supervisor = AcceptedAtlasFlywheelSupervisor(
                    self.run, self.parent_graph, reserve_gib=0.)
                cold_again = cold_again_supervisor.load_state()
                handoff_again = next_atlas_delta(
                    cold_again.epoch, cold_again.learner_evidence, cold_again.plan)
                self.assertNotIsInstance(handoff_again, FrontierStatus, handoff_again)
                self.assertEqual(
                    handoff_again.handoff_sha256,
                    handoff.handoff_sha256,
                )
                self.assertEqual(
                    cold_again.learner_evidence.ledger,
                    cold.learner_evidence.ledger,
                )
                first_grade = propose_accepted_generated_grade(cold_supervisor)
                second_grade = propose_accepted_generated_grade(cold_again_supervisor)
                self.assertEqual(first_grade.proposal_sha256, second_grade.proposal_sha256)
                self.assertEqual(first_grade.input_sha256, second_grade.input_sha256)
                self.assertEqual(first_grade.decisions, second_grade.decisions)

                second = run_accepted_atlas_flywheel(
                    self.run, self.parent_graph, reserve_gib=0., max_advances=1)
                self.assertEqual(second.advances, 1)
                accepted_commencement, _manifest = load_bamf_generation_authority(
                    self.run / "bamf-state.json")
                self.assertEqual(
                    accepted_commencement.retained_state.optimizer_step, parent_step)
                self.assertEqual(
                    accepted_commencement.baseline_evidence,
                    accepted_event.baseline_evidence,
                )
