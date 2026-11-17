"""#542 persists Atlas-release policy only through accepted B13/C09 custody."""
from __future__ import annotations

from contextlib import contextmanager, redirect_stderr, redirect_stdout
from dataclasses import asdict, replace
import io
import json
from pathlib import Path
from unittest.mock import patch

from bilqis_mlx.cli import main
from bilqis_mlx.learning.tests.test_atlas_salience import _signed
import bilqis_mlx.runtime.mlx_checkpoint as mlx_checkpoint
from bilqis_mlx.runtime.accepted_corrections import AcceptedRuntimeHost
from bilqis_mlx.runtime.atlas_admission import (
    AtlasAdmissionEnrollmentRequestV2,
    read_accepted_atlas_lease_v2,
)
from bilqis_mlx.runtime.bamf_bundle import load_bamf_generation_authority
from bilqis_mlx.runtime.jit_adoption import _accepted_lease_run_identity
from bilqis_mlx.runtime.tests.bamf_first_student._bamf_first_student_support import BamfFirstStudentCase
from bilqis_mlx.runtime.tests.admission.atlas.test_atlas_admission import _REGISTRY
from bilqis_mlx.runtime.tests.admission.atlas.lease.test_v2 import _lease_v2
from bilqis_mlx.runtime.tests.custody.bamf_bundle.genesis_authority_fixtures import (
    accepted_feature_source_patch, genesis_feature_source_patch,
)
from bilqis_mlx.runtime.tests.custody.bamf_bundle.helpers import shape_patch


ROOT = Path(__file__).resolve().parents[5]
TOPOLOGY = ROOT / "configs/models/bamf-0.2.json"
HOST_READER = (
    "bilqis_mlx.runtime.bamf_bundle.source_authority_custody."
    "read_host_system_source_authority_registry"
)


class BamfAtlasReleaseCreateTests(BamfFirstStudentCase):
    FOUNDATION_ARGS = (
        "--run-id", "operator-first-student",
        "--run-seed", "543",
        "--learning-rate", "0.0007",
        "--adam-beta1", "0.88",
        "--adam-beta2", "0.97",
        "--adam-eps", "1e-7",
        "--weight-decay", "0.03",
    )

    def invoke(self, argv):
        output, errors = io.StringIO(), io.StringIO()
        with redirect_stdout(output), redirect_stderr(errors):
            code = main(["train", *argv])
        return code, output.getvalue(), errors.getvalue()

    def output_records(self, output):
        decoder = json.JSONDecoder()
        records = []
        offset = 0
        while offset < len(output):
            while offset < len(output) and output[offset].isspace():
                offset += 1
            if offset == len(output):
                break
            record, offset = decoder.raw_decode(output, offset)
            records.append(record)
        return tuple(records)

    @contextmanager
    def c07_create_context(self):
        with patch(
                "bilqis_mlx.presentation.operator_cli.bamf_lifecycle.source_foundation",
                return_value=(self.source, self.release, self.graph)), patch(
                "bilqis_mlx.presentation.operator_cli.bamf_lifecycle_inputs.active_run_dir",
                return_value=self.source), patch(
                "bilqis_mlx.presentation.operator_cli.bamf_lifecycle.atlas_manifest_identity",
                return_value=self.identity), shape_patch(), genesis_feature_source_patch(), patch(
                "bilqis_mlx.semantics.atlas.snapshot.resolve_atlas_artifact_selection",
                return_value=self.selection), patch(
                "bilqis_mlx.runtime.bamf_first_student.resolve_atlas_artifact_selection",
                return_value=self.selection), accepted_feature_source_patch(), patch.object(
                mlx_checkpoint, "assert_headroom"), patch(
                "bilqis_mlx.runtime.bamf_bundle.codec.assert_headroom"), patch(
                HOST_READER, return_value=_REGISTRY):
            yield

    @contextmanager
    def c07_read_context(self):
        with shape_patch(), accepted_feature_source_patch(), patch(
                HOST_READER, return_value=_REGISTRY):
            yield

    def manifest(self):
        path = self.root / "atlas-manifest.json"
        path.write_text("{}", encoding="utf-8")
        return path

    def matching_request(self):
        """Build a non-authoritative request from equivalent staged gen0 identity."""
        witness = self.root / "lease-identity-witness"
        manifest = self.manifest()
        with self.c07_create_context():
            code, _output, errors = self.invoke([
                "--human-run", "--model-topology", str(TOPOLOGY),
                "--atlas-release-manifest", str(manifest),
                "--run-dir", str(witness), *self.FOUNDATION_ARGS,
            ])
        self.assertEqual((code, errors), (0, ""))
        with self.c07_read_context():
            student, _manifest_sha = load_bamf_generation_authority(
                witness / "bamf-state.json")
        base = _lease_v2()
        approval = _signed(replace(
            base.source_approval,
            atlas_release_sha256=self.identity.release_sha256,
        ))
        return AtlasAdmissionEnrollmentRequestV2(
            base.lease_id,
            student.run_identity.run_id,
            student.run_identity.run_seed,
            student.topology.digest,
            approval,
            base.resource_ceiling,
            base.requested_at,
            base.human_command_sha256,
        )

    def scope_file(self, request, name="scope.json"):
        path = self.root / name
        path.write_text(json.dumps(asdict(request)), encoding="utf-8")
        return path

    def test_fresh_atlas_release_persists_exact_accepted_lease_and_resumes(self):
        target = self.root / "atlas-release-bamf"
        manifest = self.manifest()
        request = self.matching_request()
        scope = self.scope_file(request)

        with self.c07_create_context():
            code, output, errors = self.invoke([
                "--human-run", "--model-topology", str(TOPOLOGY),
                "--admission-policy", "atlas-release",
                "--atlas-release-manifest", str(manifest),
                "--atlas-admission-scope", str(scope),
                "--run-dir", str(target), *self.FOUNDATION_ARGS,
            ])

        self.assertEqual((code, errors), (0, ""))
        records = self.output_records(output)
        self.assertEqual(records[-1]["admission_policy"], "atlas-release")
        self.assertTrue((target / "bamf-state.json").is_file())
        self.assertTrue((target / "autonomy/atlas-admission/v2/current.json").is_file())
        with self.c07_read_context():
            host = AcceptedRuntimeHost(target)
            saved = read_accepted_atlas_lease_v2(
                target, source_authority=host.source_authority())
            student, _manifest_sha = load_bamf_generation_authority(
                target / "bamf-state.json")
        self.assertEqual(saved.lease_id, request.lease_id)
        self.assertEqual(saved.source_approval, request.source_approval)
        self.assertEqual(saved.resource_ceiling, request.resource_ceiling)
        self.assertEqual(saved.run_identity, _accepted_lease_run_identity(student.run_identity))
        self.assertEqual(student.retained_state.optimizer_step, 0)
        self.assertFalse(records[-1]["ready_for_training"])

        with self.c07_read_context():
            code, output, errors = self.invoke([
                "--dry-run", "--resume", "--run-dir", str(target),
                "--admission-policy", "atlas-release",
            ])
        self.assertEqual((code, errors), (0, ""))
        self.assertEqual(self.output_records(output)[-1]["admission_policy"], "atlas-release")

    def test_atlas_release_dry_run_is_read_only_and_reports_requested_policy(self):
        target = self.root / "dry-atlas-release"
        manifest = self.manifest()
        scope = self.scope_file(self.matching_request())

        with self.c07_create_context():
            code, output, errors = self.invoke([
                "--dry-run", "--model-topology", str(TOPOLOGY),
                "--admission-policy", "atlas-release",
                "--atlas-release-manifest", str(manifest),
                "--atlas-admission-scope", str(scope),
                "--run-dir", str(target), *self.FOUNDATION_ARGS,
            ])

        self.assertEqual((code, errors), (0, ""))
        report = json.loads(output)
        self.assertEqual(report["result"], "READY_TO_CREATE")
        self.assertEqual(report["admission_policy"], "atlas-release")
        self.assertEqual(report["neural_updates"], 0)
        self.assertFalse(target.exists())

    def test_staged_run_can_receive_first_post_genesis_v2_enrollment(self):
        target = self.root / "staged-then-enrolled"
        manifest = self.manifest()
        request = self.matching_request()
        scope = self.scope_file(request)
        with self.c07_create_context():
            code, _output, errors = self.invoke([
                "--human-run", "--model-topology", str(TOPOLOGY),
                "--atlas-release-manifest", str(manifest),
                "--run-dir", str(target), *self.FOUNDATION_ARGS,
            ])
        self.assertEqual((code, errors), (0, ""))
        self.assertFalse((target / "autonomy/atlas-admission/v2/current.json").exists())

        with self.c07_read_context(), patch(
                "bilqis_mlx.presentation.operator_cli.command._invoke_learner",
                side_effect=AssertionError("C16.2 owns neural execution")):
            code, output, errors = self.invoke([
                "--human-run", "--resume", "--run-dir", str(target),
                "--admission-policy", "atlas-release",
                "--atlas-admission-scope", str(scope),
            ])
        self.assertEqual((code, errors), (0, ""))
        report = self.output_records(output)[-1]
        self.assertEqual(report["result"], "ENROLLED")
        self.assertEqual(report["admission_policy"], "atlas-release")
        self.assertFalse(report["ready_for_training"])
        self.assertTrue((target / "autonomy/atlas-admission/v2/current.json").is_file())

    def test_first_enrollment_does_not_silently_renew_existing_v2_authority(self):
        target = self.root / "no-silent-renewal"
        manifest = self.manifest()
        request = self.matching_request()
        scope = self.scope_file(request)
        with self.c07_create_context():
            code, _output, errors = self.invoke([
                "--human-run", "--model-topology", str(TOPOLOGY),
                "--atlas-release-manifest", str(manifest),
                "--run-dir", str(target), *self.FOUNDATION_ARGS,
            ])
        self.assertEqual((code, errors), (0, ""))
        with self.c07_read_context():
            code, _output, errors = self.invoke([
                "--human-run", "--resume", "--run-dir", str(target),
                "--admission-policy", "atlas-release",
                "--atlas-admission-scope", str(scope),
            ])
        self.assertEqual((code, errors), (0, ""))
        current = target / "autonomy/atlas-admission/v2/current.json"
        before = current.read_bytes()
        changed = replace(
            request,
            lease_id=request.lease_id + "-replacement",
            human_command_sha256="8" * 64,
        )
        changed_scope = self.scope_file(changed, "changed-scope.json")
        with self.c07_read_context():
            code, output, errors = self.invoke([
                "--human-run", "--resume", "--run-dir", str(target),
                "--admission-policy", "atlas-release",
                "--atlas-admission-scope", str(changed_scope),
            ])
        self.assertEqual((code, output), (2, ""))
        self.assertIn("BAMF_ATLAS_LEASE_V2_EXPLICIT_RENEWAL_REQUIRED", errors)
        self.assertEqual(current.read_bytes(), before)

    def test_dual_v1_v2_authority_epoch_fails_closed_on_resume(self):
        target = self.root / "epoch-conflict"
        manifest = self.manifest()
        request = self.matching_request()
        scope = self.scope_file(request)
        with self.c07_create_context():
            code, _output, errors = self.invoke([
                "--human-run", "--model-topology", str(TOPOLOGY),
                "--admission-policy", "atlas-release",
                "--atlas-release-manifest", str(manifest),
                "--atlas-admission-scope", str(scope),
                "--run-dir", str(target), *self.FOUNDATION_ARGS,
            ])
        self.assertEqual((code, errors), (0, ""))
        legacy = target / "autonomy/atlas-admission/current.json"
        legacy.parent.mkdir(parents=True, exist_ok=True)
        legacy.write_text("{}\n", encoding="utf-8")
        before = legacy.read_bytes()
        with self.c07_read_context():
            code, output, errors = self.invoke([
                "--dry-run", "--resume", "--run-dir", str(target),
            ])
        self.assertEqual((code, output), (2, ""))
        self.assertIn("BAMF_ATLAS_AUTHORITY_EPOCH_CONFLICT", errors)
        self.assertEqual(legacy.read_bytes(), before)

    def test_scope_manifest_conflict_rejects_before_generation_zero(self):
        target = self.root / "wrong-release-bamf"
        manifest = self.manifest()
        request = self.matching_request()
        approval = _signed(replace(
            request.source_approval, atlas_release_sha256="9" * 64))
        scope = self.scope_file(replace(request, source_approval=approval))

        with self.c07_create_context():
            code, output, errors = self.invoke([
                "--human-run", "--model-topology", str(TOPOLOGY),
                "--admission-policy", "atlas-release",
                "--atlas-release-manifest", str(manifest),
                "--atlas-admission-scope", str(scope),
                "--run-dir", str(target), *self.FOUNDATION_ARGS,
            ])

        self.assertEqual((code, output), (2, ""))
        self.assertIn("BAMF_OPERATOR_ATLAS_REQUEST_MANIFEST_CONFLICT", errors)
        self.assertFalse(target.exists())

    def test_post_genesis_signature_failure_leaves_only_staged_custody(self):
        target = self.root / "invalid-signature-bamf"
        manifest = self.manifest()
        request = self.matching_request()
        approval = replace(request.source_approval, signature_hex="0" * 128)
        scope = self.scope_file(replace(request, source_approval=approval))

        with self.c07_create_context():
            code, output, errors = self.invoke([
                "--human-run", "--model-topology", str(TOPOLOGY),
                "--admission-policy", "atlas-release",
                "--atlas-release-manifest", str(manifest),
                "--atlas-admission-scope", str(scope),
                "--run-dir", str(target), *self.FOUNDATION_ARGS,
            ])

        self.assertEqual(code, 2)
        self.assertIn("BAMF_C09_SOURCE_SIGNATURE_INVALID", errors)
        self.assertEqual(
            tuple(record.get("event") for record in self.output_records(output)),
            ("BAMF_GENERATION_ACCEPTED",),
        )
        self.assertTrue((target / "bamf-state.json").is_file())
        self.assertFalse((target / "autonomy/atlas-admission/v2/current.json").exists())
        with self.c07_read_context():
            code, output, errors = self.invoke([
                "--dry-run", "--resume", "--run-dir", str(target),
            ])
        self.assertEqual((code, errors), (0, ""))
        self.assertEqual(self.output_records(output)[-1]["admission_policy"], "staged")


if __name__ == "__main__":
    import unittest
    unittest.main()
