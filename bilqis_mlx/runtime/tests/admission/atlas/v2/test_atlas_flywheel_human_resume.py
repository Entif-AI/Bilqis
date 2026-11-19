"""Human-resume production-parameter coverage for the accepted Atlas flywheel."""
from contextlib import ExitStack, nullcontext, redirect_stderr, redirect_stdout
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

@patch("bilqis_mlx.runtime.bamf_operator.session._training_memory_context", nullcontext)
class AcceptedAtlasFlywheelHumanResumeTests(AcceptedAtlasFlywheelHumanResumeSupport):
    def test_human_resume_runs_real_parameter_flywheel_from_accepted_custody(self):
        with patch(
                "bilqis_mlx.runtime.tests.custody.bamf_bundle.helpers.DECLARED",
                _COMPACT_DECLARED), patch(
                    "bilqis_mlx.runtime.topology_v2.serialization.expected_bamf_shapes",
                    return_value=_COMPACT_DECLARED), shape_patch():
            fixture = self._production_parameter_fixture()
            supervisor = AcceptedAtlasFlywheelSupervisor(
                self.run, self.parent_graph, reserve_gib=100.)
            with self._production_parameter_context(fixture):
                self._credit_identity_prerequisites(supervisor)
                parent, _manifest = load_bamf_generation_authority(
                    self.run / "bamf-state.json")
                parent_release = read_accepted_atlas_factory_release(self.run).release_sha256
                report = self._invoke_real_human_resume()
                accepted, _accepted_manifest = load_bamf_generation_authority(
                    self.run / "bamf-state.json")
                pointer, accepted_student = accepted_generation(
                    self.run / "bamf-state.json")
                binding = accepted_binding_for_manifest(
                    self.run, pointer["manifest_sha256"], accepted_student,
                    expected_acceptance_sha256=pointer["acceptance_sha256"])
            self.assertEqual(report["status"], "VISIT_LIMIT")
            self.assertEqual(report["visits"], 0)
            self.assertEqual(report["accepted"], 0)
            self.assertEqual(report["rejected"], 0)
            self.assertIn("admission_status", report)
            self.assertEqual(accepted.generation, parent.generation + 1)
            self.assertEqual(
                accepted.retained_state.optimizer_step,
                parent.retained_state.optimizer_step)
            self.assertNotEqual(
                read_accepted_atlas_factory_release(self.run).release_sha256,
                parent_release)
            self.assertEqual(binding.lease_sha256, fixture.lease.digest())

    def test_persistent_operator_keeps_fixed_release_after_accepted_visit(self):
        with patch(
                "bilqis_mlx.runtime.tests.custody.bamf_bundle.helpers.DECLARED",
                _COMPACT_DECLARED), patch(
                    "bilqis_mlx.runtime.topology_v2.serialization.expected_bamf_shapes",
                    return_value=_COMPACT_DECLARED), shape_patch():
            fixture = self._production_parameter_fixture()
            with self._production_parameter_context(fixture):
                parent, _manifest = load_bamf_generation_authority(
                    self.run / "bamf-state.json")
                parent_release = read_accepted_atlas_factory_release(
                    self.run).release_sha256
                seen_releases = []

                def fake_visit(run_dir, _reserve_gib, **_kwargs):
                    from bilqis_mlx.runtime.bamf_operator.session import _execution_context
                    _student, context, _atlas, _features = _execution_context(run_dir)
                    seen_releases.append(context.release.release_sha256)
                    if len(seen_releases) == 1:
                        return "ACCEPTED"
                    return "HELD"

                with patch(
                        "bilqis_mlx.runtime.bamf_operator.session._visit",
                        side_effect=fake_visit):
                    result = operate_bamf(
                        self.run, minutes=1, max_visits=0, reserve_gib=100.,
                        source_prefetch_workers=0, parent_graph=self.parent_graph)

                accepted, _accepted_manifest = load_bamf_generation_authority(
                    self.run / "bamf-state.json")
                successor_release = read_accepted_atlas_factory_release(
                    self.run).release_sha256

            self.assertEqual(result.status, "PRIORITY_HOLD")
            self.assertEqual((result.visits, result.accepted, result.rejected), (1, 1, 0))
            self.assertEqual(result.admission_advances, 0)
            self.assertIsNone(result.admission_status)
            self.assertEqual(seen_releases[0], parent_release)
            self.assertEqual(seen_releases[1], parent_release)
            self.assertEqual(successor_release, parent_release)
            self.assertEqual(
                accepted.retained_state.optimizer_step,
                parent.retained_state.optimizer_step)
