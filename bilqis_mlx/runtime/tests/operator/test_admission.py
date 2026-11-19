"""A declarative unknown grade uses the same durable runtime admission gate."""
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


def _executable_fixture(seed=17):
    course = _synthetic_course(6)
    registry = _synthetic_registry()
    curriculum, bindings = from_legacy_course(course)
    graph = {
        "tokens": [
            "fixture.padding",
            "cogal.value.false",
            "cogal.value.true",
        ],
    }
    answers = AnswerModalityRegistry((
        RegisteredAnswerModality(
            AnswerModality("binary", "answer.binary/v1", "a" * 64),
            fixed_domain(("FALSE", "TRUE")),
            lambda value: {
                "FALSE": "cogal.value.false",
                "TRUE": "cogal.value.true",
            }[value]),
    ))
    release = compile_executable_factory_release(
        curriculum, bindings, CurriculumProfile.full(),
        registry, answers, source_root=None, graph=graph,
        verification_seed=seed)
    return release, graph


class ExecutableMigrationTests(unittest.TestCase):
    def test_live_reader_rejects_historical_release_without_foundation_identity(self):
        from bilqis_mlx.factory.executable_release import (
            ExecutableFactoryRelease, _digest,
        )
        from bilqis_mlx.runtime.admission import _read_executable_factory_release

        release, _graph = _executable_fixture()
        manifest = json.loads(json.dumps(release.manifest()))
        manifest.pop("foundation_capability_ids")
        historical_sha = _digest(manifest)
        historical = ExecutableFactoryRelease.from_manifest(manifest, historical_sha)
        self.assertIsNone(historical.foundation_capability_ids)

        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            release_root = root / "factory-releases"
            release_root.mkdir()
            path = release_root / f"{historical_sha}.json"
            path.write_text(json.dumps({
                "factory_release_sha256": historical_sha,
                **manifest,
            }, sort_keys=True))
            receipt = {
                "factory_release_sha256": historical_sha,
                "factory_release_file": f"factory-releases/{historical_sha}.json",
            }
            with self.assertRaisesRegex(
                    ValueError,
                    "FACTORY_EXECUTABLE_RELEASE_FOUNDATION_CAPABILITY_IDS_REQUIRED"):
                _read_executable_factory_release(root, receipt, _graph)

    def test_legacy_live_rubric_rebinds_without_changing_parent_evidence(self):
        from bilqis_mlx.runtime.release_adoption import _migrate_executable_release
        from bilqis_mlx.runtime.state import _fingerprint
        from bilqis_mlx.curriculum.scheduler import start_new
        from bilqis_mlx.factory.schedule import schedule_program_from_executable_release
        release, graph = _executable_fixture()
        program = schedule_program_from_executable_release(release)
        course = _synthetic_course(6)
        student = Checkpoint("c" * 64, "bundles/parent", 23, True)
        school = start_new(course, student)
        receipt = dict(school=asdict(school), semantic_graph_sha256=_fingerprint(graph),
                       live_rubric_sha256="d" * 64, last_exam={"historical": "unchanged"})
        original = deepcopy(receipt)
        with tempfile.TemporaryDirectory() as temporary, patch('bilqis_mlx.compatibility.executable_projection.compile_projected_executable_release',
                return_value=(release, program, None)):
            migrated, _, _, rebound = _migrate_executable_release(
                Path(temporary), receipt, course, course, None, graph)
        self.assertEqual(migrated["live_rubric_sha256"], program.grades[0].assessment_sha256)
        self.assertEqual(rebound.current_student, student)
        self.assertEqual(migrated["last_exam"], receipt["last_exam"])
        self.assertEqual(receipt, original)

        from bilqis_mlx.runtime.session import _resume_admitted_student
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            release_file = _persist_executable_factory_release(root, release)
            saved = {**migrated, "factory_release_file": release_file, "generation": 1}
            with patch("bilqis_mlx.runtime.session._state_dag.read_current", return_value=saved), \
                    patch("bilqis_mlx.runtime.session._resume",
                          return_value=("params", "optimizer", graph, saved)) as resume, \
                    patch("bilqis_mlx.compatibility.executable_projection.legacy_course_for_profile",
                          side_effect=AssertionError("v2 re-entered legacy projection")), \
                    patch("bilqis_mlx.compatibility.executable_projection.resolve_legacy_resume_course",
                          side_effect=AssertionError("v2 re-entered legacy decoding")):
                for _ in range(2):
                    result = _resume_admitted_student(root, {}, course, course, None, "d" * 64)
                    self.assertEqual(result[-1], program)
                    self.assertEqual(resume.call_args.args[2], program)
                    self.assertIsNone(resume.call_args.kwargs["admitted_courses"])
                self.assertEqual(resume.call_count, 2)


class AdmissionFixture:
    def setUp(self):
        course, self.registry = synthetic_release_inputs()
        grade = course.grades[0]
        caps = tuple(replace(cap, id=cap.id.replace("A.", "Z.")) for cap in grade.capabilities)
        self.course = replace(course, grades=(replace(
            grade, id="Z", capabilities=caps,
            exam_item_counts=tuple((cap.id, 4) for cap in caps)),))
        self.student = Checkpoint("a" * 64, "bundles/fixture", 7, True)

    def admission(self, root):
        release, path, admission = _factory_admission(
            root, self.course, self.student, "b" * 64, registry=self.registry)
        receipt = {"factory_release_sha256": release.release_sha256,
                   "factory_release_file": path, "factory_admission": asdict(admission),
                   "semantic_graph_sha256": "b" * 64,
                   "school": {"current_student": asdict(self.student)}}
        return release, receipt


class RuntimeAdmissionTests(AdmissionFixture, unittest.TestCase):
    def test_synthetic_grade_admits_and_reads_back_without_a_live_grade_provider(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            release, receipt = self.admission(root)
            restored = _require_factory_admission(
                root, json.loads(json.dumps(receipt)), self.course, registry=self.registry)
            self.assertEqual(restored, release)
            self.assertEqual(restored.grades[0].grade_id, "Z")

    def test_schema_tamper_and_same_step_student_substitution_are_rejected(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            _, receipt = self.admission(root)
            receipt["factory_admission"]["student_sha256"] = "c" * 64
            with self.assertRaisesRegex(ValueError, "FACTORY_ADMISSION_BASELINE_DRIFT"):
                _require_factory_admission(root, receipt, self.course, registry=self.registry)
            receipt["factory_admission"]["student_sha256"] = self.student.sha256
            path = root / receipt["factory_release_file"]
            payload = json.loads(path.read_text())
            payload["schema"] = "unrelated.schema/v999"
            path.write_text(json.dumps(payload))
            with self.assertRaisesRegex(ValueError, "FACTORY_RELEASE_DURABLE_SCHEMA_INVALID"):
                _require_factory_admission(root, receipt, self.course, registry=self.registry)

    def test_optional_teaching_gate_reads_v2_and_checks_the_released_options(self):
        from bilqis_mlx.runtime.admission import admitted_release_supports_teaching_option
        from types import SimpleNamespace

        source = SimpleNamespace(teaching_option_ids=("source.single-event/v1",))
        release = SimpleNamespace(source_adapters=(source,))
        with patch('bilqis_mlx.runtime.admission._read_executable_factory_release_artifact',
                   return_value=release), patch('bilqis_mlx.runtime.admission._read_factory_release',
                   side_effect=AssertionError('v2 must not enter the legacy decoder')):
            receipt = {"factory_admission_v2": {}}
            self.assertTrue(admitted_release_supports_teaching_option(Path('/unused'), receipt))
            self.assertTrue(admitted_release_supports_teaching_option(
                Path('/unused'), receipt, "source.single-event/v1"))
            self.assertFalse(admitted_release_supports_teaching_option(
                Path('/unused'), receipt, "unreleased"))
        from bilqis_mlx.cli import parse_args
        args = parse_args(['train', '--human-run', '--source-teaching-enrichment'])
        self.assertTrue(args.boolean_association_bridge)

    def test_v2_executable_release_persists_and_cold_reads_without_course_rebuild(self):
        release, graph = _executable_fixture()
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            release_file = _persist_executable_factory_release(root, release)
            receipt = {
                "factory_release_sha256": release.release_sha256,
                "factory_release_file": release_file,
            }
            restored = _read_executable_factory_release(
                root, receipt, graph)
            self.assertEqual(restored, release)
            self.assertEqual(
                restored.execution_plan.curriculum_sha256,
                release.curriculum.digest())
