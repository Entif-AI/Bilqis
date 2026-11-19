"""Verify executable admission and CLI readback against durable release evidence."""
from dataclasses import asdict, replace
from copy import deepcopy
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from bilqis_mlx.learning.champions import Checkpoint
from bilqis_mlx.factory.answers import (
    AnswerModality, AnswerModalityRegistry, RegisteredAnswerModality,
    fixed_domain,
)
from bilqis_mlx.factory.curriculum_definition import from_legacy_course
from bilqis_mlx.factory.executable_release import compile_executable_factory_release
from bilqis_mlx.factory.execution import CurriculumProfile
from bilqis_mlx.factory.tests.test_execution_plan import (
    _synthetic_course, _synthetic_registry,
)
from bilqis_mlx.factory.tests.support import synthetic_release_inputs
from bilqis_mlx.runtime.state import _fingerprint
from bilqis_mlx.runtime.admission import (
    _executable_factory_admission, _factory_admission,
    _persist_executable_factory_release, _read_executable_factory_release,
    _require_executable_factory_admission, _require_factory_admission,
)

from .test_admission import AdmissionFixture, _executable_fixture


class AdmissionColdReadbackTests(AdmissionFixture, unittest.TestCase):
    def test_cli_preflight_and_artifact_readback_preserve_all_run_bytes(self):
        import io
        from contextlib import redirect_stdout
        from bilqis_mlx.presentation.operator_cli import preflight as cli
        from bilqis_mlx.runtime.admission import _read_executable_factory_release_artifact

        release, graph = _executable_fixture()
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            release_file = _persist_executable_factory_release(root, release)
            receipt = dict(factory_release_sha256=release.release_sha256,
                           factory_release_file=release_file, factory_admission_v2={},
                           school={"current_student": asdict(self.student)})
            original = deepcopy(receipt)
            (root / "state.json").write_text(json.dumps(receipt))
            (root / "model-and-own-adamw.safetensors").write_bytes(b"preserved-disposable-bytes")
            (root / "events.jsonl").write_text('{"historical":true}\n')
            snapshot = {"factory": {"active_grades": ["Z"], "canonical_grades": [],
                "profile_id": "fixture", "active_capabilities": ["Z.C0"]}}
            before = {str(path.relative_to(root)): path.read_bytes()
                      for path in root.rglob("*") if path.is_file()}
            with patch.object(cli, "_inspect", return_value=snapshot), \
                    patch.object(cli, "read_current", return_value=receipt), \
                    patch.object(cli, "_boolean_revision_preflight", return_value={}), \
                    patch.object(cli, "assert_headroom", return_value={}), \
                    patch("bilqis_mlx.grade_a_manifest.verify_manifest", return_value={
                        "verified_items": 72, "exam_rubric_sha256": "a" * 64}), \
                    redirect_stdout(io.StringIO()):
                self.assertEqual(cli.preflight(root, resume=True, verify_source=True), 0)
                self.assertEqual(_read_executable_factory_release_artifact(root, receipt), release)
            self.assertEqual(receipt, original)
            self.assertEqual({str(path.relative_to(root)): path.read_bytes()
                              for path in root.rglob("*") if path.is_file()}, before)

    def test_historical_qualification_preserves_receipt_and_run_bytes(self):
        from types import SimpleNamespace
        from bilqis_mlx.compatibility.executable_projection import preflight_sealed_v1_migration
        from bilqis_mlx.curriculum.scheduler import start_new
        from bilqis_mlx.factory.schedule import schedule_program_from_executable_release

        release, graph = _executable_fixture()
        course = _synthetic_course(6)
        receipt = dict(school=asdict(start_new(course, self.student)),
                       semantic_graph_sha256=_fingerprint(graph))
        original = deepcopy(receipt)
        program = schedule_program_from_executable_release(release)
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            (root / "state.json").write_text(json.dumps(receipt))
            before = (root / "state.json").read_bytes()
            with patch("bilqis_mlx.runtime.admission._verified_legacy_upgrade_release",
                       return_value=SimpleNamespace(course=course)), \
                    patch("bilqis_mlx.runtime.assessment._verify_saved_cohort"), \
                    patch("bilqis_mlx.grade_a_probe.read_sources", return_value=(None, None, graph, None, None)), \
                    patch("bilqis_mlx.compatibility.executable_projection.verify_legacy_resume_binding"), \
                    patch("bilqis_mlx.grade_a_release.accepted_grade_a", return_value=course), \
                    patch("bilqis_mlx.compatibility.live_releases.initial_course", return_value=course), \
                    patch("bilqis_mlx.compatibility.executable_projection.compile_projected_executable_release",
                          return_value=(release, program, None)):
                result = preflight_sealed_v1_migration(root, receipt, {}, None)
            self.assertEqual(result["neural_updates"], 0)
            self.assertEqual(result["saved_course_sha256"], course.digest())
            self.assertEqual(result["source_qualified_successor_sha256"], release.release_sha256)
            self.assertEqual(receipt, original)
            self.assertEqual((root / "state.json").read_bytes(), before)
            self.assertEqual(tuple(path.name for path in root.iterdir()), ("state.json",))

    def test_v2_readback_rejects_schema_and_loaded_catalog_drift(self):
        release, graph = _executable_fixture(seed=19)
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            release_file = _persist_executable_factory_release(root, release)
            receipt = {
                "factory_release_sha256": release.release_sha256,
                "factory_release_file": release_file,
            }
            changed_graph = {
                "tokens": [
                    "fixture.padding",
                    "cogal.value.true",
                    "cogal.value.false",
                ],
            }
            with self.assertRaisesRegex(
                    ValueError, "FACTORY_EXECUTABLE_RELEASE_CATALOG_DRIFT"):
                _read_executable_factory_release(
                    root, receipt, changed_graph)

            path = root / release_file
            payload = json.loads(path.read_text())
            payload["schema"] = "unrelated.schema/v999"
            path.write_text(json.dumps(payload))
            with self.assertRaisesRegex(
                    ValueError, "FACTORY_EXECUTABLE_RELEASE_DURABLE_SCHEMA_INVALID"):
                _read_executable_factory_release(root, receipt, graph)

    def test_v2_graph_substitution_and_false_admission_digest_fail_closed(self):
        release, graph = _executable_fixture(seed=37)
        changed = {**graph, "nodes": [{"meaning": "substituted"}]}
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            with self.assertRaisesRegex(ValueError, "SEMANTIC_GRAPH_DRIFT"):
                _executable_factory_admission(
                    root, release, self.student, _fingerprint(changed), changed)
            with self.assertRaisesRegex(ValueError, "SEMANTIC_GRAPH_DRIFT"):
                _executable_factory_admission(
                    root, release, self.student, "b" * 64, graph)
            self.assertFalse((root / "factory-releases").exists())
            _, release_file, admission = _executable_factory_admission(
                root, release, self.student, _fingerprint(graph), graph)
            receipt = dict(factory_release_sha256=release.release_sha256,
                           factory_release_file=release_file,
                           factory_admission_v2={**asdict(admission),
                                                 "semantic_graph_sha256": _fingerprint(changed)},
                           semantic_graph_sha256=_fingerprint(changed),
                           school={"current_student": asdict(self.student)})
            with self.assertRaisesRegex(ValueError, "SEMANTIC_GRAPH_DRIFT"):
                _require_executable_factory_admission(root, receipt, graph)

    def test_v2_admission_binds_release_plan_catalog_graph_and_student(self):
        release, graph = _executable_fixture(seed=23)
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            _, release_file, admission = _executable_factory_admission(
                root, release, self.student, _fingerprint(graph), graph)
            receipt = {
                "factory_release_sha256": release.release_sha256,
                "factory_release_file": release_file,
                "factory_admission_v2": asdict(admission),
                "semantic_graph_sha256": _fingerprint(graph),
                "school": {"current_student": asdict(self.student)},
            }
            restored = _require_executable_factory_admission(
                root, json.loads(json.dumps(receipt)), graph)
            self.assertEqual(restored, release)
            self.assertEqual(
                admission.execution_plan_sha256,
                release.execution_plan.digest())
            self.assertEqual(
                admission.semantic_catalog_sha256,
                release.semantic_catalog_sha256)

    def test_v2_admission_rejects_same_step_student_substitution(self):
        release, graph = _executable_fixture(seed=29)
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            _, release_file, admission = _executable_factory_admission(
                root, release, self.student, _fingerprint(graph), graph)
            receipt = {
                "factory_release_sha256": release.release_sha256,
                "factory_release_file": release_file,
                "factory_admission_v2": {
                    **asdict(admission),
                    "student_sha256": "c" * 64,
                },
                "semantic_graph_sha256": _fingerprint(graph),
                "school": {"current_student": asdict(self.student)},
            }
            with self.assertRaisesRegex(
                    ValueError, "FACTORY_EXECUTABLE_ADMISSION_BASELINE_DRIFT"):
                _require_executable_factory_admission(root, receipt, graph)
