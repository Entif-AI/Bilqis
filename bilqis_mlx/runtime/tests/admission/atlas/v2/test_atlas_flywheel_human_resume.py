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
from bilqis_mlx.factory.autonomy import EvidenceReceipt, obligations_for_capability, record_evidence
from bilqis_mlx.runtime.atlas_admission import read_accepted_atlas_factory_release
from bilqis_mlx.runtime.atlas_flywheel_runtime import AcceptedAtlasFlywheelSupervisor
from bilqis_mlx.runtime.autonomy_state import persist_autonomy_state
from bilqis_mlx.runtime.bamf_bundle import load_bamf_generation_authority
from bilqis_mlx.runtime.bamf_bundle.feature.acceptance import accepted_binding_for_manifest, accepted_generation
from bilqis_mlx.runtime.tests.admission.atlas.v2.mixed_witness_support import MixedWitnessSupport
from bilqis_mlx.runtime.tests.admission.atlas.v2.test_c07_lease_closure_v2 import _COMPACT_DECLARED
from bilqis_mlx.runtime.tests.custody.bamf_bundle.helpers import shape_patch
from bilqis_mlx.semantics.atlas.snapshot import AtlasArtifactSelection
from bilqis_mlx.source_adapters import event_frames
from bilqis_mlx.factory.tests.curriculum.frontier.test_atlas_frontier import _rights


class AcceptedAtlasFlywheelHumanResumeTests(MixedWitnessSupport, unittest.TestCase):
    def _production_parameter_fixture(self):
        staged_seed = self.zero_id_stage()
        seed_handoff, _seed_plan, _seed_learner = self.capability_handoff(staged_seed)
        snapshot, event_candidate, schema, features = self.common_atlas()
        selection = AtlasArtifactSelection(
            "/artifact", snapshot.bundle_id, snapshot.release_sha256,
            snapshot.source_bundle_id)
        source_frontier, policy = _rights()
        source_authority = SimpleNamespace(frontier=source_frontier, policy=policy)
        combined = self.combined_source_registry()
        self.publish_matching_genesis(snapshot, schema, features)
        _approval, lease, _source_authority = self.issue_mixed_lease(
            seed_handoff, event_candidate, snapshot,
            event_capabilities=("D.EVENT_OCCURRENCE", "D.COMMENCEMENT"))
        source_ids = tuple(
            event_frames.atlas_semantic_id(capability)
            for capability in ("D.EVENT_OCCURRENCE", "D.COMMENCEMENT"))
        source_nt = b"".join(
            f'<{semantic_id}> <http://www.w3.org/2004/02/skos/core#definition> '
            f'"c07 proof semantic role"@en .\n'.encode("utf-8")
            for semantic_id in source_ids)
        return SimpleNamespace(
            snapshot=snapshot, event_candidate=event_candidate, schema=schema,
            features=features, selection=selection, source_authority=source_authority,
            combined=combined, lease=lease, source_nt=source_nt)

    def _production_parameter_context(self, fixture):
        stack = ExitStack()
        stack.enter_context(self.source_replay(
            fixture.snapshot, fixture.schema, fixture.features))
        patches = (
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
             Path("/source")),
        )
        for target, value in patches:
            stack.enter_context(patch(target, return_value=value))
        for target in (
            "bilqis_mlx.runtime.bamf_bundle.feature_authority.load_pinned_atlas_snapshot",
            "bilqis_mlx.runtime.bamf_bundle.vocabulary.admission.load_pinned_atlas_snapshot",
            "bilqis_mlx.semantics.atlas.vocabulary_planning.load_pinned_atlas_snapshot",
            "bilqis_mlx.semantics.atlas.vocabulary_resources.load_pinned_atlas_snapshot",
        ):
            stack.enter_context(patch(target, return_value=fixture.snapshot))
        stack.enter_context(patch(
            "bilqis_mlx.semantics.atlas.vocabulary_resources._verify_bundle",
            return_value=(fixture.snapshot.source_bundle_id,
                          {"canonical.nt": fixture.source_nt})))
        stack.enter_context(patch(
            "bilqis_mlx.runtime.bamf_bundle.vocabulary.admission.shutil.disk_usage",
            return_value=SimpleNamespace(free=1 << 50)))
        stack.enter_context(patch("bilqis_mlx.runtime.mlx_checkpoint.assert_headroom"))
        return stack

    def _credit_identity_prerequisites(self, supervisor):
        state = supervisor.load_state()
        ledger = state.learner_evidence.ledger
        obligations = obligations_for_capability(
            state.epoch.current_release, "A.IDENTITY", plan=state.plan)
        for index, obligation in enumerate(obligations, 1):
            ledger = record_evidence(
                state.epoch.current_release, ledger,
                EvidenceReceipt(
                    obligation.obligation_id, f"c07-production-prerequisite-{index}",
                    state.learner_evidence.checkpoint_sha256,
                    state.learner_evidence.optimizer_step,
                    hashlib.sha256(
                        f"c07-production-prerequisite:{index}".encode()).hexdigest(),
                    obligation.minimum_specimens, True),
                plan=state.plan,
                current_checkpoint_sha256=state.learner_evidence.checkpoint_sha256,
                current_optimizer_step=state.learner_evidence.optimizer_step)
        persist_autonomy_state(
            self.run, state.epoch.current_release, plan=state.plan, ledger=ledger)

    @staticmethod
    def _json_records(rendered):
        decoder, records, offset = json.JSONDecoder(), [], 0
        while offset < len(rendered):
            while offset < len(rendered) and rendered[offset].isspace():
                offset += 1
            if offset == len(rendered):
                break
            record, offset = decoder.raw_decode(rendered, offset)
            records.append(record)
        return tuple(records)

    def _invoke_real_human_resume(self):
        output, errors = io.StringIO(), io.StringIO()

        def cold_operator_probe(
                run_dir, *, minutes, max_visits, steps_per_visit, reserve_gib,
                source_prefetch_workers, progress=None):
            from bilqis_mlx.runtime.bamf_operator import BamfOperatorResult
            from bilqis_mlx.runtime.bamf_operator.session import _execution_context

            parent, context, _atlas_path, _feature_path = _execution_context(
                Path(run_dir).resolve())
            accepted_release = read_accepted_atlas_factory_release(Path(run_dir).resolve())
            self.assertEqual(context.release.release_sha256, accepted_release.release_sha256)
            return BamfOperatorResult(
                "VISIT_LIMIT", 0, 0, 0,
                parent.generation, parent.retained_state.optimizer_step)

        with patch(
                "bilqis_mlx.presentation.operator_cli.bamf_lifecycle.source_foundation",
                return_value=(None, None, self.parent_graph)), patch(
                    "bilqis_mlx.presentation.operator_cli.command._invoke_learner",
                    side_effect=AssertionError(
                        "accepted flywheel must not reuse a live learner")), patch(
                    "bilqis_mlx.runtime.bamf_operator.operate_bamf",
                    side_effect=cold_operator_probe) as operate, \
                redirect_stdout(output), redirect_stderr(errors):
            code = main([
                "train", "--human-run", "--resume", "--run-dir", str(self.run),
                "--max-visits", "1"])
        self.assertEqual((code, errors.getvalue()), (0, ""))
        operate.assert_called_once_with(
            self.run, minutes=90, max_visits=1, steps_per_visit=16, reserve_gib=100.0,
            source_prefetch_workers=2, progress=ANY)
        return self._json_records(output.getvalue())[-1]

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
