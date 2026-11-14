"""Three-lane source preparation must stay deterministic and neural-inert."""
from pathlib import Path
import json
import signal
from types import SimpleNamespace
import unittest
from unittest.mock import patch

from bilqis_mlx.cli import parse_args
from bilqis_mlx.factory.curriculum_definition import from_legacy_course
from bilqis_mlx.factory.executable_release import compile_executable_factory_release
from bilqis_mlx.factory.execution import CurriculumProfile
from bilqis_mlx.factory.tests.test_executable_release import _answers
from bilqis_mlx.factory.tests.test_execution_plan import (
    _synthetic_course, _synthetic_registry,
)
from bilqis_mlx.runtime import source_prefetch
from bilqis_mlx.runtime.source_prefetch import prepare_step_sources


ROOT = Path(__file__).resolve().parents[4]
SOURCE_ROOT = ROOT / "vendor" / "legacy-v16"
MANIFEST = ROOT / "docs/provenance/GRADE_A_CANDIDATE_MANIFEST_V2.json"


class SourcePrefetchTests(unittest.TestCase):
    def test_live_v2_assessment_and_worker_lanes_reject_seed_specific_future_root(self):
        from bilqis_mlx.factory.tests.test_teaching import closed_source_fixture
        from bilqis_mlx.runtime.assessment import _draw_live_rows
        from bilqis_mlx.runtime.source_execution import SourceExecutionContext
        course, graph, sources, answers, release = closed_source_fixture()
        context = SourceExecutionContext(release, graph, None, sources, answers)
        with self.assertRaisesRegex(ValueError, "CLOSURE:Z.C0:future.root"):
            _draw_live_rows(None, graph, seed=999, capability="Z.C0", source_context=context)
        with patch("bilqis_mlx.source_adapters.school.live_source_registry", return_value=sources):
            with self.assertRaisesRegex(ValueError, "CLOSURE:Z.C0:future.root"):
                _draw_live_rows(None, graph, seed=999, capability="Z.C0", executable_release=release)
        request = {
            "identity": "e" * 64, "source_root": "/source", "graph": graph,
            "course": course, "executable_release": release,
            "capability": "Z.C0", "batch_size": 4, "fresh_seed": 17,
            "prior_capability": None, "prior_seed": None,
            "fragile_fixed_rows": (), "fragile_requested": (), "fragile_seeds": {},
            "fragile_rotation": 0, "retention_support_capability": None,
            "retention_support_seed": 17, "retention_support_rotation": 0,
            "teaching_seed": 17, "teaching_enrichment_enabled": False,
        }
        variants = {
            "fresh": {"fresh_seed": 999},
            "prior": {"prior_capability": "Z.C1", "prior_seed": 999},
            "support": {"retention_support_capability": "Z.C1", "retention_support_seed": 999},
            "enrichment": {"teaching_enrichment_enabled": True, "teaching_seed": 999},
            "preservation_draw": {"fragile_fixed_rows": ({"id": "fixed", "capability": "Z.C1"},),
                "fragile_requested": ("Z.C1",), "fragile_seeds": {"Z.C1": (999, 1001, 1002)}},
        }
        with (patch("bilqis_mlx.runtime.source_prefetch.live_source_registry", return_value=sources),
              patch("bilqis_mlx.runtime.source_prefetch.live_answer_registry", return_value=answers)):
            self.assertEqual(len(prepare_step_sources(request)["fresh"]), 32)
            for lane, fields in variants.items():
                with self.subTest(lane=lane), self.assertRaisesRegex(ValueError, "CLOSURE:Z.C[01]:future.root"):
                    prepare_step_sources({**request, **fields})

    def test_historical_assessment_dispatch_keeps_its_existing_generation_path(self):
        from bilqis_mlx.runtime.assessment import _draw_live_rows
        course = SimpleNamespace()
        rows = [{"id": "legacy", "capability": "A.IDENTITY", "gold": "TRUE"}]
        with (patch("bilqis_mlx.runtime.assessment.draw_course_rows", return_value=rows),
              patch("bilqis_mlx.factory.generation.validate_instructional_constituents",
                    side_effect=AssertionError("v1 acquired v2 closure"))):
            self.assertEqual(_draw_live_rows(None, {}, seed=17, capability="A.IDENTITY", course=course), rows)

    def test_human_cli_defaults_to_two_prep_workers_with_serial_escape_hatch(self):
        self.assertEqual(parse_args(["train"]).source_prefetch_workers, 2)
        self.assertEqual(
            parse_args(["train", "--source-prefetch-workers", "0"]).source_prefetch_workers,
            0,
        )

    def test_spawned_prefetch_workers_ignore_terminal_sigint(self):
        with source_prefetch.source_prefetch_pool(1) as pool:
            # Child importability must not depend on the dynamic module name
            # that scripts/run_tests.py assigns to collected test files.
            self.assertEqual(
                pool.submit(signal.getsignal, signal.SIGINT).result(timeout=10),
                signal.SIG_IGN)

    def test_step_packet_is_deterministic_and_rejects_neural_or_write_authority(self):
        course = SimpleNamespace(grades=(SimpleNamespace(id="B"),))
        request = {
            "identity": "a" * 64,
            "source_root": "/source",
            "graph": {"tokens": []},
            "course": course,
            "capability": "B.XOR",
            "batch_size": 4,
            "fresh_seed": 11,
            "prior_capability": None,
            "prior_seed": None,
            "fragile_fixed_rows": (),
            "fragile_requested": (),
            "fragile_seeds": {},
            "fragile_rotation": 0,
            "retention_support_capability": None,
            "retention_support_seed": 12,
            "retention_support_rotation": 0,
            "teaching_seed": 13,
            "teaching_enrichment_enabled": False,
        }
        rows = [
            {"id": f"r{i}", "source_id": f"r{i}", "capability": "B.XOR",
             "gold": "TRUE" if i % 2 else "FALSE", "tokens": [1, i + 2]}
            for i in range(8)
        ]
        with patch("bilqis_mlx.runtime.source_prefetch.draw_course_rows", return_value=rows):
            first = prepare_step_sources(request)
            second = prepare_step_sources(request)
        self.assertEqual(first, second)
        self.assertEqual(first["identity"], request["identity"])
        self.assertEqual(len(first["fresh"]), 8)
        self.assertEqual(first["prior"], [])
        self.assertNotIn("parameters", first)
        self.assertNotIn("optimizer", first)
        self.assertNotIn("run_dir", first)

        for forbidden in ("parameters", "optimizer", "run_dir", "checkpoint"):
            with self.subTest(forbidden=forbidden):
                with self.assertRaisesRegex(ValueError, "SOURCE_PREFETCH_FORBIDDEN_AUTHORITY"):
                    prepare_step_sources({**request, forbidden: object()})

    def test_active_v2_packet_uses_executable_release_instead_of_legacy_course(self):
        course = _synthetic_course(6)
        curriculum, bindings = from_legacy_course(course)
        graph = {
            "tokens": [
                "fixture.padding",
                "cogal.value.false",
                "cogal.value.true",
            ],
        }
        sources = _synthetic_registry()
        answers = _answers()
        release = compile_executable_factory_release(
            curriculum, bindings, CurriculumProfile.full(), sources, answers,
            source_root=None, graph=graph, verification_seed=17)
        request = {
            "identity": "b" * 64, "source_root": "/source",
            "graph": graph, "course": course,
            "executable_release": release,
            "capability": "Z.C0", "batch_size": 4,
            "fresh_seed": 15, "prior_capability": None,
            "prior_seed": None, "fragile_fixed_rows": (),
            "fragile_requested": (), "fragile_seeds": {},
            "fragile_rotation": 0,
            "retention_support_capability": None,
            "retention_support_seed": 17,
            "retention_support_rotation": 0, "teaching_seed": 16,
            "teaching_enrichment_enabled": False,
        }
        expected = [{"id": "v2", "capability": "Z.C0", "gold": "TRUE"}]
        with (patch("bilqis_mlx.runtime.source_prefetch.draw_course_rows",
                    side_effect=AssertionError("Legacy v1 generation forbidden")),
              patch("bilqis_mlx.runtime.source_prefetch.live_source_registry",
                    return_value=sources),
              patch("bilqis_mlx.runtime.source_prefetch.live_answer_registry",
                    return_value=answers),
              patch("bilqis_mlx.factory.generation.draw_executable_release_rows",
                    return_value=expected) as executable):
            result = prepare_step_sources(request)
        self.assertEqual(result["fresh"], expected)
        self.assertEqual(executable.call_args.kwargs, {
            "seed": request["fresh_seed"], "capability": request["capability"],
            "each": 32,
        })
        self.assertEqual(executable.call_args.args[2], release)

    def test_v2_packet_rejects_untyped_release(self):
        request = {
            "identity": "c" * 64, "source_root": "/source",
            "graph": {"tokens": []}, "course": SimpleNamespace(),
            "executable_release": SimpleNamespace(release_sha256="d" * 64),
            "capability": "B.AND", "batch_size": 4,
            "fresh_seed": 15, "prior_capability": None,
            "prior_seed": None, "fragile_fixed_rows": (),
            "fragile_requested": (), "fragile_seeds": {},
            "fragile_rotation": 0,
            "retention_support_capability": None,
            "retention_support_seed": 17,
            "retention_support_rotation": 0, "teaching_seed": 16,
            "teaching_enrichment_enabled": False,
        }
        with self.assertRaisesRegex(TypeError, "Expected an ExecutableFactoryRelease"):
            prepare_step_sources(request)

    def test_fragile_worker_forwards_frozen_policy_without_boolean_assumption(self):
        request = {
            "fragile_fixed_rows": ({"id": "fixed", "capability": "C.ADD"},),
            "fragile_requested": ("C.ADD",),
            "fragile_seeds": {"C.ADD": (3, 5, 7)},
            "fragile_rotation": 11,
            "batch_size": 8,
        }
        from bilqis_mlx.profiles.retention import FragilePreservationPolicy
        policy = FragilePreservationPolicy(("C.ADD",), 4, "fixture/source/v1")
        with (patch("bilqis_mlx.runtime.source_prefetch.fragile_preservation_policy",
                    return_value=policy),
              patch("bilqis_mlx.runtime.source_prefetch.fresh_preservation_rows",
                    return_value=()) as select):
            result = source_prefetch._fragile_rows(request)

        self.assertEqual(result, ())
        self.assertEqual(select.call_args.kwargs["capabilities"], ("C.ADD",))
        self.assertEqual(select.call_args.kwargs["rotation"], 11)
        self.assertIs(select.call_args.kwargs["retention_policy"], policy)

    def test_step_packet_prepares_fresh_retention_support_family(self):
        request = {
            "identity": "d" * 64,
            "source_root": "/source",
            "graph": {"tokens": []},
            "course": SimpleNamespace(grades=(SimpleNamespace(id="B"),)),
            "capability": "B.XOR",
            "batch_size": 8,
            "fresh_seed": 21,
            "prior_capability": None,
            "prior_seed": None,
            "fragile_fixed_rows": (),
            "fragile_requested": (),
            "fragile_seeds": {},
            "fragile_rotation": 0,
            "retention_support_capability": "C.COUNT",
            "retention_support_seed": 22,
            "retention_support_rotation": 0,
            "teaching_seed": 23,
            "teaching_enrichment_enabled": False,
        }
        current = [
            {"id": f"b{i}", "source_id": f"b{i}", "capability": "B.XOR",
             "gold": "TRUE" if i % 2 else "FALSE", "tokens": [1, i + 2]}
            for i in range(8)
        ]
        support = [
            {"id": "c:n", "source_id": "count-two", "capability": "C.COUNT",
             "answer_kind": "numeric_active", "gold": "2", "tokens": [1, 2]},
            {"id": "c:t", "source_id": "count-two", "capability": "C.COUNT",
             "answer_kind": "binary", "gold": "TRUE", "tokens": [1, 3]},
            {"id": "c:f", "source_id": "count-two", "capability": "C.COUNT",
             "answer_kind": "binary", "gold": "FALSE", "tokens": [1, 4]},
        ]

        def draw(_root, _graph, _course, *, capability, **_kwargs):
            return support if capability == "C.COUNT" else current

        with patch("bilqis_mlx.runtime.source_prefetch.draw_course_rows",
                   side_effect=draw):
            result = prepare_step_sources(request)

        self.assertEqual({row["id"] for row in result["retention_support"]},
                         {"c:n", "c:t", "c:f"})
        self.assertEqual({row["capability"] for row in result["fresh"]},
                         {"B.XOR"})

    def test_real_source_packet_survives_spawned_process_boundary(self):
        from bilqis_mlx.grade_a_probe import read_sources
        from bilqis_mlx.grade_a_release import accepted_grade_a
        from bilqis_mlx.live_grade_a import live_course as a_live_course
        from bilqis_mlx.live_grade_b import live_course as b_live_course

        manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))
        course = b_live_course(
            a_live_course(accepted_grade_a(manifest)), SOURCE_ROOT)
        graph = read_sources(SOURCE_ROOT)[2]
        request = {
            "identity": "b" * 64,
            "source_root": str(SOURCE_ROOT),
            "graph": graph,
            "course": course,
            "capability": "B.XOR",
            "batch_size": 4,
            "fresh_seed": 119,
            "prior_capability": None,
            "prior_seed": None,
            "fragile_fixed_rows": (),
            "fragile_requested": (),
            "fragile_seeds": {},
            "fragile_rotation": 0,
            "retention_support_capability": None,
            "retention_support_seed": 121,
            "retention_support_rotation": 0,
            "teaching_seed": 120,
            "teaching_enrichment_enabled": False,
        }
        with source_prefetch.source_prefetch_pool(1) as pool:
            prepared = pool.submit(prepare_step_sources, request).result(timeout=30)
        direct = prepare_step_sources(request)
        self.assertEqual(prepared, direct)
        self.assertEqual(prepared["identity"], request["identity"])
        self.assertEqual(len(prepared["fresh"]), 32)
        self.assertEqual({row["capability"] for row in prepared["fresh"]}, {"B.XOR"})
