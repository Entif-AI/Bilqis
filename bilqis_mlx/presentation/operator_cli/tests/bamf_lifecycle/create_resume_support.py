"""Shared fixture for the C16.1a create/resume lifecycle witnesses."""
from contextlib import contextmanager, redirect_stderr, redirect_stdout
import io
import json
from pathlib import Path
from unittest.mock import patch

from bilqis_mlx.cli import main
import bilqis_mlx.runtime.mlx_checkpoint as mlx_checkpoint
from bilqis_mlx.runtime.tests.bamf_first_student._bamf_first_student_support import BamfFirstStudentCase
from bilqis_mlx.runtime.tests.custody.bamf_bundle.genesis_authority_fixtures import (
    accepted_feature_source_patch, genesis_feature_source_patch,
)
from bilqis_mlx.runtime.tests.custody.bamf_bundle.helpers import shape_patch


ROOT = Path(__file__).resolve().parents[5]
TOPOLOGY = ROOT / "configs/models/bamf-0.2.json"


class BamfCreateResumeCase(BamfFirstStudentCase):
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

    @staticmethod
    def output_records(output: str):
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
    def accepted_read_context(self):
        with shape_patch(), accepted_feature_source_patch():
            yield

    @contextmanager
    def foundation_create_context(self):
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
                return_value=self.selection), patch.object(
                mlx_checkpoint, "assert_headroom"), patch(
                "bilqis_mlx.runtime.bamf_bundle.codec.assert_headroom"):
            yield
