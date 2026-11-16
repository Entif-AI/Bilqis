"""#542 BAMF resume validation and neural-inert routing contract."""
from __future__ import annotations

from contextlib import contextmanager, redirect_stderr, redirect_stdout
import io
import json
from pathlib import Path
import shutil
from types import SimpleNamespace
from unittest.mock import patch

from bilqis_mlx.cli import main
from bilqis_mlx.runtime.model_topology_v2 import ModelTopologySpecV2
from bilqis_mlx.runtime.atlas_flywheel import AdmissionFlywheelStatus
from bilqis_mlx.runtime.tests.bamf_first_student._bamf_first_student_support import BamfFirstStudentCase
from bilqis_mlx.runtime.tests.custody.bamf_bundle.genesis_authority_fixtures import (
    source_features,
)
from bilqis_mlx.runtime.tests.custody.bamf_bundle.helpers import shape_patch
from bilqis_mlx.semantics.atlas.snapshot import AtlasArtifactIdentity


ROOT = Path(__file__).resolve().parents[5]
TOPOLOGY = ROOT / "configs/models/bamf-0.2.json"


def _tree_snapshot(root: Path):
    return tuple(
        (str(path.relative_to(root)), path.is_dir(), path.stat().st_mtime_ns,
         None if path.is_dir() else path.read_bytes())
        for path in (root, *sorted(root.rglob("*")))
    )


class BamfResumeTests(BamfFirstStudentCase):
    def invoke(self, argv):
        output, errors = io.StringIO(), io.StringIO()
        with redirect_stdout(output), redirect_stderr(errors):
            code = main(["train", *argv])
        return code, output.getvalue(), errors.getvalue()

    @contextmanager
    def accepted_read_context(self):
        with shape_patch(), patch(
            "bilqis_mlx.runtime.bamf_bundle.feature_authority._authenticate_features",
            return_value=source_features(),
        ):
            yield

    def test_resume_without_overrides_reads_saved_b13_identity_without_writes(self):
        target = self.root / "accepted-bamf"
        receipt = self.preflight(target)
        before = _tree_snapshot(target)
        with self.accepted_read_context():
            code, output, errors = self.invoke([
                "--dry-run", "--resume", "--run-dir", str(target),
            ])
        self.assertEqual((code, errors), (0, ""))
        report = json.loads(output)
        self.assertEqual(report["result"], "READY_TO_RESUME")
        self.assertEqual(report["admission_policy"], "staged")
        self.assertEqual(report["run_seed"], receipt.run_identity.run_seed)
        self.assertEqual(
            report["model_topology"]["digest"],
            receipt.run_identity.initial_topology_digest,
        )
        self.assertEqual(
            report["atlas_release_manifest"]["sha256"],
            receipt.atlas_artifact.bundle_id,
        )
        self.assertEqual(_tree_snapshot(target), before)

    def test_resume_explicit_atlas_release_conflict_rejects_before_writes(self):
        target = self.root / "accepted-bamf"
        self.preflight(target)
        before = _tree_snapshot(target)
        for policy_args in (("--admission-policy", "atlas-release"),
                            ("--admission-policy=atlas-release",)):
            with self.subTest(policy_args=policy_args), self.accepted_read_context():
                code, output, errors = self.invoke([
                    "--dry-run", "--resume", "--run-dir", str(target), *policy_args,
                ])
            self.assertEqual((code, output), (2, ""))
            self.assertIn("BAMF_ATLAS_EXPLICIT_SCOPE_FILE_REQUIRED", errors)
            self.assertEqual(_tree_snapshot(target), before)

    def test_resume_rejects_atlas_scope_override_before_writes(self):
        target = self.root / "accepted-bamf"
        self.preflight(target)
        before = _tree_snapshot(target)
        scope = self.root / "scope.json"
        scope.write_text("{}", encoding="utf-8")
        with self.accepted_read_context():
            code, output, errors = self.invoke([
                "--dry-run", "--resume", "--run-dir", str(target),
                "--atlas-admission-scope", str(scope),
            ])
        self.assertEqual((code, output), (2, ""))
        self.assertIn("BAMF_ATLAS_SCOPE_REQUIRES_EXPLICIT_POLICY", errors)
        self.assertEqual(_tree_snapshot(target), before)

    def test_resume_scope_requires_human_authorization_before_request_parse(self):
        target = self.root / "accepted-bamf"
        self.preflight(target)
        before = _tree_snapshot(target)
        scope = self.root / "malformed-scope.json"
        scope.write_text("not-json", encoding="utf-8")
        with self.accepted_read_context():
            code, output, errors = self.invoke([
                "--dry-run", "--resume", "--run-dir", str(target),
                "--admission-policy", "atlas-release",
                "--atlas-admission-scope", str(scope),
            ])
        self.assertEqual((code, output), (2, ""))
        self.assertIn("BAMF_ATLAS_V2_EXPLICIT_HUMAN_REQUEST_REQUIRED", errors)
        self.assertNotIn("BAMF_ATLAS_ENROLLMENT_REQUEST_INVALID", errors)
        self.assertEqual(_tree_snapshot(target), before)

    def test_human_resume_dispatches_bamf_native_operator_after_validation(self):
        target = self.root / "accepted-bamf"
        self.preflight(target)
        before = _tree_snapshot(target)
        from bilqis_mlx.runtime.bamf_operator import BamfOperatorResult
        with self.accepted_read_context(), patch(
                "bilqis_mlx.presentation.operator_cli.command._invoke_learner",
                side_effect=AssertionError("legacy learner must remain untouched")), patch(
                "bilqis_mlx.runtime.bamf_operator.operate_bamf",
                return_value=BamfOperatorResult(
                    "VISIT_LIMIT", 1, 1, 0, 1, 1)) as operate:
            code, output, errors = self.invoke([
                "--human-run", "--resume", "--run-dir", str(target),
                "--max-visits", "1",
            ])
        self.assertEqual((code, errors), (0, ""))
        report = json.loads(output)
        self.assertEqual(report["status"], "VISIT_LIMIT")
        self.assertEqual(report["generation"], 1)
        call = operate.call_args
        self.assertEqual(call.args, (target,))
        self.assertEqual(call.kwargs["minutes"], 90)
        self.assertEqual(call.kwargs["max_visits"], 1)
        self.assertEqual(call.kwargs["reserve_gib"], 100.0)
        self.assertTrue(callable(call.kwargs["progress"]))
        self.assertEqual(_tree_snapshot(target), before)

    def test_human_resume_with_saved_atlas_lease_replans_then_continues_learning(self):
        target = self.root / "accepted-bamf"
        self.preflight(target)
        from bilqis_mlx.runtime.bamf_operator import BamfOperatorResult
        with self.accepted_read_context(), patch(
                "bilqis_mlx.presentation.operator_cli.bamf_lifecycle._saved_policy",
                return_value="atlas-release"), patch(
                "bilqis_mlx.presentation.operator_cli.bamf_lifecycle.source_foundation",
                return_value=(None, None, {"fixture": "accepted-source-graph"})), patch(
                "bilqis_mlx.runtime.atlas_flywheel_runtime.run_accepted_atlas_flywheel",
                return_value=SimpleNamespace(
                    status=AdmissionFlywheelStatus.WAITING_FOR_EVIDENCE,
                )) as flywheel, patch(
                "bilqis_mlx.presentation.operator_cli.command._invoke_learner",
                side_effect=AssertionError("BAMF v2 must not re-enter the legacy learner")), patch(
                "bilqis_mlx.runtime.bamf_operator.operate_bamf",
                return_value=BamfOperatorResult(
                    "VISIT_LIMIT", 1, 1, 0, 1, 1)) as operate:
            code, output, errors = self.invoke([
                "--human-run", "--resume", "--run-dir", str(target),
                "--max-visits", "1",
            ])
        self.assertEqual((code, errors), (0, ""))
        report = json.loads(output)
        self.assertEqual(report["status"], "VISIT_LIMIT")
        self.assertEqual(report["admission_status"], "WAITING_FOR_EVIDENCE")
        flywheel.assert_called_once()
        self.assertEqual(Path(flywheel.call_args.args[0]), target.resolve())
        call = operate.call_args
        self.assertEqual(call.args, (target,))
        self.assertEqual(call.kwargs["minutes"], 90)
        self.assertEqual(call.kwargs["max_visits"], 1)
        self.assertEqual(call.kwargs["reserve_gib"], 100.0)
        self.assertTrue(callable(call.kwargs["progress"]))

    def test_human_resume_with_ambiguous_flywheel_hold_does_not_start_learning(self):
        target = self.root / "accepted-bamf"
        self.preflight(target)
        with self.accepted_read_context(), patch(
                "bilqis_mlx.presentation.operator_cli.bamf_lifecycle._saved_policy",
                return_value="atlas-release"), patch(
                "bilqis_mlx.presentation.operator_cli.bamf_lifecycle.source_foundation",
                return_value=(None, None, {"fixture": "accepted-source-graph"})), patch(
                "bilqis_mlx.runtime.atlas_flywheel_runtime.run_accepted_atlas_flywheel",
                return_value=SimpleNamespace(
                    status=AdmissionFlywheelStatus.HELD,
                )), patch(
                "bilqis_mlx.runtime.bamf_operator.operate_bamf",
                side_effect=AssertionError("ambiguous admission hold must stop learning")):
            code, output, errors = self.invoke([
                "--human-run", "--resume", "--run-dir", str(target),
            ])
        self.assertEqual((code, errors), (0, ""))
        report = json.loads(output)
        self.assertEqual(report["result"], "HELD")
        self.assertEqual(report["admission_policy"], "atlas-release")
        self.assertEqual(report["neural_updates"], 0)

    def test_human_resume_run_id_conflict_never_reaches_learner(self):
        target = self.root / "accepted-bamf"
        self.preflight(target)
        before = _tree_snapshot(target)
        with self.accepted_read_context(), patch(
                "bilqis_mlx.presentation.operator_cli.command._invoke_learner",
                side_effect=AssertionError("C16.2 owns later neural execution")):
            code, output, errors = self.invoke([
                "--human-run", "--resume", "--run-dir", str(target),
                "--run-id", "wrong-run",
            ])
        self.assertEqual((code, output), (2, ""))
        self.assertIn("BAMF_OPERATOR_RESUME_RUN_ID_CONFLICT", errors)
        self.assertEqual(_tree_snapshot(target), before)

    def test_human_resume_optimizer_conflict_never_reaches_learner(self):
        target = self.root / "accepted-bamf"
        self.preflight(target)
        before = _tree_snapshot(target)
        with self.accepted_read_context(), patch(
                "bilqis_mlx.presentation.operator_cli.command._invoke_learner",
                side_effect=AssertionError("C16.2 owns later neural execution")):
            code, output, errors = self.invoke([
                "--human-run", "--resume", "--run-dir", str(target),
                "--learning-rate", "0.0008", "--adam-beta1", "0.88",
                "--adam-beta2", "0.97", "--adam-eps", "1e-7",
                "--weight-decay", "0.03",
            ])
        self.assertEqual((code, output), (2, ""))
        self.assertIn("BAMF_OPERATOR_RESUME_OPTIMIZER_CONFLICT", errors)
        self.assertEqual(_tree_snapshot(target), before)

    def test_no_pointer_bamf_v2_custody_resume_is_intercepted_before_learner(self):
        target = self.root / "interrupted-bamf"
        (target / "bamf-bundles").mkdir(parents=True)
        before = _tree_snapshot(target)
        with patch(
                "bilqis_mlx.presentation.operator_cli.command._invoke_learner",
                side_effect=AssertionError("legacy learner must not inspect BAMF v2 custody")):
            code, output, errors = self.invoke([
                "--human-run", "--resume", "--run-dir", str(target),
            ])
        self.assertEqual((code, output), (2, ""))
        self.assertIn("BAMF_OPERATOR_INTERRUPTED_GENESIS_REQUIRES_CREATE_RETRY", errors)
        self.assertEqual(_tree_snapshot(target), before)

    def test_trust_only_pointerless_resume_is_intercepted_before_learner(self):
        target = self.root / "trust-only-bamf"
        receipt = self.preflight(target)
        run_id = receipt.run_identity.run_id
        shutil.rmtree(target)
        with patch(
                "bilqis_mlx.presentation.operator_cli.command._invoke_learner",
                side_effect=AssertionError("legacy learner must not inspect BAMF v2 trust")):
            code, output, errors = self.invoke([
                "--human-run", "--resume", "--run-dir", str(target),
                "--run-id", run_id,
            ])
        self.assertEqual((code, output), (2, ""))
        self.assertIn("BAMF_OPERATOR_INTERRUPTED_GENESIS_REQUIRES_CREATE_RETRY", errors)
        self.assertFalse(target.exists())

    def test_resume_conflicting_seed_and_optimizer_reject_before_writes(self):
        target = self.root / "accepted-bamf"
        self.preflight(target)
        before = _tree_snapshot(target)
        cases = (
            (["--run-seed", "544"], "BAMF_OPERATOR_RESUME_RUN_SEED_CONFLICT"),
            (["--learning-rate", "0.0008", "--adam-beta1", "0.88",
              "--adam-beta2", "0.97", "--adam-eps", "1e-7",
              "--weight-decay", "0.03"], "BAMF_OPERATOR_RESUME_OPTIMIZER_CONFLICT"),
        )
        for override, reason in cases:
            with self.subTest(reason=reason), self.accepted_read_context():
                code, output, errors = self.invoke([
                    "--dry-run", "--resume", "--run-dir", str(target), *override,
                ])
            self.assertEqual((code, output), (2, ""))
            self.assertIn(reason, errors)
            self.assertEqual(_tree_snapshot(target), before)

    def test_resume_conflicting_atlas_manifest_rejects_before_writes(self):
        target = self.root / "accepted-bamf"
        self.preflight(target)
        before = _tree_snapshot(target)
        manifest = self.root / "other-manifest.json"
        manifest.write_text("{}", encoding="utf-8")
        other = AtlasArtifactIdentity("1" * 64, "2" * 64, "3" * 64)
        with self.accepted_read_context(), patch(
                "bilqis_mlx.presentation.operator_cli.bamf_lifecycle.atlas_manifest_identity",
                return_value=other):
            code, output, errors = self.invoke([
                "--dry-run", "--resume", "--run-dir", str(target),
                "--atlas-release-manifest", str(manifest),
            ])
        self.assertEqual((code, output), (2, ""))
        self.assertIn("BAMF_OPERATOR_RESUME_ATLAS_MANIFEST_CONFLICT", errors)
        self.assertEqual(_tree_snapshot(target), before)

    def test_resume_conflicting_topology_rejects_before_writes(self):
        target = self.root / "accepted-bamf"
        self.preflight(target)
        before = _tree_snapshot(target)
        forged = ModelTopologySpecV2()
        object.__setattr__(forged, "layers", forged.layers + 1)
        with self.accepted_read_context(), patch(
                "bilqis_mlx.runtime.topology_lifecycle.topology_from_file",
                return_value=forged):
            code, output, errors = self.invoke([
                "--dry-run", "--resume", "--run-dir", str(target),
                "--model-topology", str(TOPOLOGY),
            ])
        self.assertEqual((code, output), (2, ""))
        self.assertIn("BAMF_OPERATOR_RESUME_TOPOLOGY_CONFLICT", errors)
        self.assertEqual(_tree_snapshot(target), before)

    def test_resume_all_equality_assertions_wrong_still_reports_run_id_first(self):
        target = self.root / "accepted-all-wrong"
        self.preflight(target)
        before = _tree_snapshot(target)
        forged = ModelTopologySpecV2()
        object.__setattr__(forged, "layers", forged.layers + 1)
        manifest = self.root / "wrong-atlas.json"
        manifest.write_text("{}", encoding="utf-8")
        other = AtlasArtifactIdentity("1" * 64, "2" * 64, "3" * 64)
        with self.accepted_read_context(), patch(
                "bilqis_mlx.runtime.topology_lifecycle.topology_from_file",
                return_value=forged), patch(
                "bilqis_mlx.presentation.operator_cli.bamf_lifecycle.atlas_manifest_identity",
                return_value=other):
            code, output, errors = self.invoke([
                "--dry-run", "--resume", "--run-dir", str(target),
                "--run-id", "wrong-run", "--run-seed", "544",
                "--model-topology", str(TOPOLOGY),
                "--learning-rate", "0.8", "--adam-beta1", "0.8",
                "--adam-beta2", "0.8", "--adam-eps", "1e-5",
                "--weight-decay", "0.8",
                "--atlas-release-manifest", str(manifest),
            ])
        self.assertEqual((code, output), (2, ""))
        self.assertIn("BAMF_OPERATOR_RESUME_RUN_ID_CONFLICT", errors)
        self.assertEqual(_tree_snapshot(target), before)


if __name__ == "__main__":
    import unittest
    unittest.main()
