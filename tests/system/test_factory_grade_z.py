"""Disposable end-to-end proof that a new grade needs no generic runtime edits.

This test declares Grade Z, its source adapter, and its binary answer modality
entirely inside the test. Production code must treat it as ordinary factory
data through release compilation, admission, scheduling, assessment,
championship, telemetry, recovery, teacher evidence, stagnation, and stop logic.
No optimizer or MLX runtime is invoked.
"""
from __future__ import annotations

from dataclasses import asdict, replace
import json
from pathlib import Path
import tempfile
import unittest

from bilqis_mlx.curriculum import BINARY
from bilqis_mlx.factory.adapters import RegisteredSourceAdapter, SourceAdapterRegistry
from bilqis_mlx.factory.answers import (
    AnswerModality, AnswerModalityRegistry, RegisteredAnswerModality, fixed_domain,
)
from bilqis_mlx.factory.executable_release import compile_executable_factory_release
from bilqis_mlx.factory.execution import CurriculumProfile, GradeProfile
from bilqis_mlx.factory.model import SourceAdapter
from bilqis_mlx.factory.schedule import schedule_program_from_executable_release
from bilqis_mlx.learning.champions import Checkpoint
from bilqis_mlx.runtime.admission import _require_executable_factory_admission
from bilqis_mlx.runtime.state import _state_from_json

from tests.system.factory_grade_z.championship import (
    assert_championship, assert_telemetry_and_operator,
)
from tests.system.factory_grade_z.fixture import CAPABILITIES, fixture
from tests.system.factory_grade_z.lifecycle import (
    admit_and_schedule, assert_cohort_lifecycle,
    assert_compiler_and_generation, assert_mastery_debt_and_teacher,
)


class DisposableGradeZSystemProof(unittest.TestCase):
    def test_current_operate_and_admitted_resume_do_not_reconstruct_courses(self):
        import ast
        import inspect
        from bilqis_mlx.runtime.operating_loop import operate
        from bilqis_mlx.runtime.session import _resume_admitted_student

        for entrypoint in (operate, _resume_admitted_student):
            with self.subTest(entrypoint=entrypoint.__name__):
                tree = ast.parse(inspect.getsource(entrypoint))
                calls = [node for node in ast.walk(tree) if isinstance(node, ast.Call)]
                self.assertFalse(any(isinstance(node.func, ast.Attribute) and
                    node.func.attr == "legacy_course_for_profile" for node in calls))

    def test_assessment_context_draws_twelve_v2_capabilities_without_course(self):
        from unittest.mock import patch
        from bilqis_mlx.runtime.assessment import _draw_live_rows
        from bilqis_mlx.runtime.source_execution import SourceExecutionContext

        registry, graph, template = fixture()
        names = CAPABILITIES
        curriculum = template.curriculum
        bindings = template.source_bindings
        answers = AnswerModalityRegistry((RegisteredAnswerModality(
            AnswerModality("binary", "answer.binary/z-fixture", "e" * 64),
            fixed_domain(BINARY), lambda value: "cogal.value." + value.lower()),))
        release = compile_executable_factory_release(
            curriculum, bindings, CurriculumProfile.full(), registry, answers,
            source_root=None, graph=graph, verification_seed=19)
        context = SourceExecutionContext(release, graph, None, registry, answers)
        with patch("bilqis_mlx.runtime.assessment.draw_course_rows",
                   side_effect=AssertionError("historical generation used")):
            rows = _draw_live_rows(None, graph, seed=31, source_context=context)
            selected = _draw_live_rows(
                None, graph, seed=31, capability=names[-1], each=2,
                source_context=context)
            with self.assertRaisesRegex(ValueError, "UNKNOWN_CAPABILITY"):
                _draw_live_rows(None, graph, seed=31, capability="Z.UNKNOWN",
                                source_context=context)
        self.assertEqual(tuple(row["capability"] for row in rows),
                         tuple(name for name in names for _ in range(4)))
        self.assertEqual(selected, [row for row in rows
                                   if row["capability"] == names[-1]][:2])

    def test_runtime_uses_only_the_admitted_source_and_answer_footprint(self):
        from unittest.mock import Mock, patch
        from bilqis_mlx.runtime.assessment import _draw_live_rows
        from bilqis_mlx.runtime.source_execution import SourceExecutionContext
        from bilqis_mlx.runtime.source_prefetch import prepare_step_sources

        registry, graph, template = fixture()
        unused_answer = Mock(side_effect=AssertionError("undeclared modality invoked"))
        answers = AnswerModalityRegistry((
            RegisteredAnswerModality(template.answer_modalities[0], fixed_domain(BINARY),
                                    lambda value: "cogal.value." + value.lower()),
            RegisteredAnswerModality(
                AnswerModality("unused", "answer.unused/z-fixture", "f" * 64),
                unused_answer, unused_answer),
        ))
        release = compile_executable_factory_release(
            template.curriculum, template.source_bindings,
            CurriculumProfile("fixture/one-capability", (
                GradeProfile("Z", enabled_capabilities=(CAPABILITIES[0],)),)),
            registry, answers, source_root=None, graph=graph, verification_seed=29)
        provider = registry.require("fixture.z-generator/v1", "fixture.z-oracle/v1")
        draw = Mock(wraps=provider.draw)
        unused = Mock(side_effect=AssertionError("undeclared provider invoked"))
        sources = SourceAdapterRegistry((replace(provider, draw=draw),
            RegisteredSourceAdapter(SourceAdapter(
                "fixture.unused-adapter/v1", "fixture.unused-generator/v1",
                ("fixture.unused-oracle/v1",), "f" * 64), unused, unused)))
        context = SourceExecutionContext(release, graph, None, sources, answers)
        with self.assertRaisesRegex(ValueError, "UNKNOWN_CAPABILITY"):
            _draw_live_rows(None, graph, seed=3, capability=CAPABILITIES[-1],
                            source_context=context)
        draw.assert_not_called()
        request = dict(
            identity="a" * 64, source_root=".", graph=graph, course=None,
            executable_release=release, capability=CAPABILITIES[0], batch_size=2,
            fresh_seed=3, prior_capability=None, prior_seed=4,
            fragile_fixed_rows=(), fragile_requested=(), fragile_seeds={},
            fragile_rotation=0, retention_support_capability=None,
            retention_support_seed=5, retention_support_rotation=0,
            teaching_seed=6, teaching_enrichment_enabled=False)
        with patch("bilqis_mlx.runtime.source_prefetch.live_source_registry", return_value=sources),                 patch("bilqis_mlx.runtime.source_prefetch.live_answer_registry", return_value=answers),                 patch("bilqis_mlx.runtime.source_prefetch.draw_course_rows",
                      side_effect=AssertionError("historical source bypass")):
            prepared = prepare_step_sources(request)
            self.assertEqual({row["capability"] for row in prepared["fresh"]},
                             {CAPABILITIES[0]})
            draw.reset_mock()
            with self.assertRaisesRegex(ValueError, "UNKNOWN_CAPABILITY"):
                prepare_step_sources({**request, "capability": CAPABILITIES[-1]})
            draw.assert_not_called()
            with self.assertRaisesRegex(ValueError, "UNKNOWN_CAPABILITY"):
                prepare_step_sources({**request, "prior_capability": CAPABILITIES[-1]})
            self.assertTrue(all(call.kwargs["capability"] == CAPABILITIES[0]
                                for call in draw.call_args_list))
        unused.assert_not_called()
        unused_answer.assert_not_called()

    def test_grade_z_runs_through_the_generic_factory_control_plane(self):
        registry, graph, release = fixture()
        student = Checkpoint("1" * 64, "bundles/z-student", 7, True)
        manifest = {"manifest_sha256": "2" * 64}
        assert_compiler_and_generation(self, registry, graph, release)

        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            receipt, program, school, graph_sha = admit_and_schedule(
                self, root, graph, release, student, manifest)
            routine, pointer, promotion, generalization = assert_cohort_lifecycle(
                self, root, receipt, manifest, registry, graph, release)
            mastered = assert_mastery_debt_and_teacher(
                self, program, school, student, routine, pointer,
                promotion, generalization)
            receipt.update(school=asdict(mastered))
            state_file = root / "grade-z-state.json"
            state_file.write_text(json.dumps(receipt), encoding="utf-8")
            cold_receipt = json.loads(state_file.read_text(encoding="utf-8"))
            cold_release = _require_executable_factory_admission(
                root, cold_receipt, graph)
            cold_program = schedule_program_from_executable_release(cold_release)
            cold_school = _state_from_json(cold_receipt["school"], cold_program)
            self.assertEqual(cold_school, mastered)
            self.assertEqual(cold_school.stage, "WHOLE_SCHOOL_MASTERED")
            self.assertEqual(cold_release.release_sha256, release.release_sha256)
            scores, scope_sha, changed = assert_championship(
                self, root, routine, pointer, student, graph_sha, manifest)
            assert_telemetry_and_operator(
                self, routine, pointer, student, mastered, scores, scope_sha, changed)


if __name__ == "__main__":
    unittest.main()
