from dataclasses import replace
import os
from tempfile import TemporaryDirectory
import unittest
from unittest.mock import patch

import bilqis_mlx.runtime.mlx_checkpoint as mlx_checkpoint
from bilqis_mlx.errors import BilqisError
from bilqis_mlx.factory.adapters import SourceAdapterRegistry
from bilqis_mlx.factory.answers import AnswerModalityRegistry
from bilqis_mlx.factory.curriculum_definition import from_legacy_course
from bilqis_mlx.factory.executable_release import compile_executable_factory_release
from bilqis_mlx.factory.execution import CurriculumProfile
from bilqis_mlx.factory.tests.test_executable_release import _answers
from bilqis_mlx.factory.tests.test_execution_plan import _synthetic_course, _synthetic_registry
from bilqis_mlx.runtime.accepted_corrections import AcceptedRuntimeHost
from bilqis_mlx.runtime.source_execution import SourceExecutionContext
from bilqis_mlx.runtime.tests.custody.bamf_bundle.helpers import (
    candidate, next_accepted_step, parent_state, provision_source_authority_registry,
    publish_candidate, shape_patch, with_source_authority_registry,
)
from bilqis_mlx.runtime.tests.test_atlas_revalidation import AUTHORITY, _event, _ref
from bilqis_mlx.semantics.cognitive_dependencies import DependencyKind


class SourceExecutionContextTests(unittest.TestCase):
    def setUp(self):
        self.course = _synthetic_course(6)
        curriculum, bindings = from_legacy_course(self.course)
        self.graph = {"tokens": ["fixture.padding", "cogal.value.false", "cogal.value.true"]}
        self.sources = _synthetic_registry()
        self.answers = _answers()
        self.release = compile_executable_factory_release(
            curriculum, bindings, CurriculumProfile.full(), self.sources, self.answers,
            source_root=None, graph=self.graph, verification_seed=17)
        self.arguments = dict(release=self.release, graph=self.graph, source_root=None,
                              source_registry=self.sources, answer_registry=self.answers)

    def test_context_holds_the_existing_release_and_runtime_inputs(self):
        context = SourceExecutionContext(**self.arguments)
        self.assertIs(context.release, self.release)
        self.assertIs(context.graph, self.graph)
        self.assertIs(context.source_registry, self.sources)
        self.assertIs(context.answer_registry, self.answers)
        self.assertIsNone(context.source_root)

    def test_bound_source_batch_draws_provider_once_and_revalidates_without_redraw(self):
        from bilqis_mlx.factory import generation

        context = SourceExecutionContext(**self.arguments)
        original = generation.draw_executable_release_rows
        with patch.object(
                generation, "draw_executable_release_rows",
                wraps=original) as draw:
            rows, authority = context.draw_bound_rows(
                seed=17, capability="Z.C0", each=1)
            self.assertEqual(draw.call_count, 1)
            self.assertIs(context.require_bound_rows(rows, authority), authority)
            self.assertEqual(draw.call_count, 1)
        self.assertEqual(context._source_preparation_metrics.provider_draws, 1)

    def test_unbound_source_context_cannot_claim_accepted_runtime_custody(self):
        from pathlib import Path
        context = SourceExecutionContext(**self.arguments)
        with self.assertRaises(ValueError):
            context.require_accepted_runtime(Path("fixture-run"))

    def test_structurally_forged_context_cannot_claim_host_custody(self):
        from pathlib import Path
        run_dir = Path("fixture-run")
        context = SourceExecutionContext(**self.arguments, run_dir=run_dir)
        with self.assertRaises(BilqisError) as caught:
            context.require_accepted_runtime(run_dir)
        self.assertEqual(
            caught.exception.context["reason"],
            "FACTORY_SOURCE_CORRECTION_RUNTIME_REQUIRED",
        )

    def test_accepted_runtime_host_mints_context_that_clears_custody_gate(self):
        from pathlib import Path
        with TemporaryDirectory() as temporary, patch.dict(
                os.environ, {"BILQIS_DATA_PLANE": str(Path(temporary) / "plane.sqlite3")}):
            run_dir = Path(temporary) / "run"
            provision_source_authority_registry(run_dir, AUTHORITY)
            source = with_source_authority_registry(
                candidate(parent_state()), AUTHORITY)
            with shape_patch(AUTHORITY), patch.object(mlx_checkpoint, "assert_headroom"):
                publish_candidate(run_dir, source)
            with patch(
                "bilqis_mlx.runtime.admission._read_executable_factory_release_artifact",
                return_value=self.release,
            ), patch(
                "bilqis_mlx.source_adapters.school.live_source_registry",
                return_value=self.sources,
            ), patch(
                "bilqis_mlx.factory.live_answers.live_answer_registry",
                return_value=self.answers,
            ):
                with shape_patch(AUTHORITY):
                    context = AcceptedRuntimeHost(run_dir).source_context(
                        graph=self.graph, source_root=None)
            with shape_patch(AUTHORITY):
                context.require_accepted_runtime(run_dir)
                self.assertIs(
                    context.source_authority(),
                    AcceptedRuntimeHost(run_dir).source_authority())

    def test_stale_source_context_cannot_roll_forward_correction_into_successor(self):
        from pathlib import Path
        with TemporaryDirectory() as temporary, patch.dict(
                os.environ, {"BILQIS_DATA_PLANE": str(Path(temporary) / "plane.sqlite3")}):
            run_dir = Path(temporary) / "run"
            provision_source_authority_registry(run_dir, AUTHORITY)
            source = with_source_authority_registry(
                candidate(parent_state()), AUTHORITY)
            with shape_patch(AUTHORITY), patch.object(mlx_checkpoint, "assert_headroom"):
                pointer = publish_candidate(run_dir, source)
            with patch(
                "bilqis_mlx.runtime.admission._read_executable_factory_release_artifact",
                return_value=self.release,
            ), patch(
                "bilqis_mlx.source_adapters.school.live_source_registry",
                return_value=self.sources,
            ), patch(
                "bilqis_mlx.factory.live_answers.live_answer_registry",
                return_value=self.answers,
            ), shape_patch(AUTHORITY):
                context = AcceptedRuntimeHost(run_dir).source_context(
                    graph=self.graph, source_root=None)
            successor = candidate(
                next_accepted_step(parent_state()), generation=1,
                parent=pointer["manifest_sha256"],
            )
            successor = with_source_authority_registry(successor, AUTHORITY)
            with shape_patch(AUTHORITY), patch.object(mlx_checkpoint, "assert_headroom"):
                publish_candidate(run_dir, successor)
            correction = _event(_ref(DependencyKind.RIGHTS, "rights:stale-context"))
            with shape_patch(AUTHORITY), self.assertRaises(BilqisError):
                context.record_correction(correction)

    def test_forged_accepted_runtime_host_subclass_cannot_mint_live_context(self):
        from pathlib import Path

        class ForgedHost(AcceptedRuntimeHost):
            def __post_init__(self):
                pass

            @property
            def registry(self):
                return AUTHORITY

            def source_authority(self):
                return object()

        run_dir = Path("fixture-run")
        forged = ForgedHost(run_dir)
        receipt = {"factory_release_sha256": self.release.release_sha256}
        with patch(
            "bilqis_mlx.runtime.admission._read_executable_factory_release_artifact",
            return_value=self.release,
        ):
            with self.assertRaises(BilqisError):
                SourceExecutionContext.from_admitted_release(
                    run_dir, receipt, graph=self.graph, source_root=None,
                    source_registry=self.sources, answer_registry=self.answers,
                    accepted_runtime_host=forged,
                )

    def test_admitted_context_uses_the_cold_read_authority(self):
        from pathlib import Path
        from bilqis_mlx.factory.execution import GradeProfile
        thin = compile_executable_factory_release(
            self.release.curriculum, self.release.source_bindings,
            CurriculumProfile("thin", grades=(GradeProfile("Z", enabled_capabilities=("Z.C5",)),)),
            self.sources, self.answers, source_root=None, graph=self.graph, verification_seed=19)
        receipt = {"factory_release_sha256": thin.release_sha256}
        arguments = {key: value for key, value in self.arguments.items() if key != "release"}
        with patch("bilqis_mlx.runtime.admission._read_executable_factory_release_artifact",
                   return_value=thin) as read:
            context = SourceExecutionContext.from_admitted_release(Path("fixture-run"), receipt,
                                                                   **arguments)
        read.assert_called_once_with(Path("fixture-run"), receipt)
        self.assertIs(context.release, thin)
        self.assertEqual(tuple(context.release.execution_plan.capability_map), ("Z.C5",))
        self.assertEqual(len(context.release.curriculum.capability_map), 6)

    def test_admitted_context_propagates_failed_cold_read(self):
        arguments = {key: value for key, value in self.arguments.items() if key != "release"}
        with patch("bilqis_mlx.runtime.admission._read_executable_factory_release_artifact",
                   side_effect=ValueError("invalid saved artifact")):
            with self.assertRaisesRegex(ValueError, "invalid saved artifact"):
                SourceExecutionContext.from_admitted_release(None, {}, **arguments)

    def test_context_rejects_legacy_course_and_untyped_registries(self):
        for field, value in (("release", self.course), ("source_registry", object()),
                             ("answer_registry", object())):
            with self.subTest(field=field), self.assertRaises(TypeError):
                SourceExecutionContext(**{**self.arguments, field: value})

    def test_context_rejects_unverified_release_or_mismatched_graph(self):
        mutations = (
            {"release": replace(self.release, release_sha256="f" * 64)},
            {"graph": {"tokens": list(reversed(self.graph["tokens"]))}},
            {"source_registry": SourceAdapterRegistry()},
            {"answer_registry": AnswerModalityRegistry()},
        )
        for mutation in mutations:
            with self.subTest(field=tuple(mutation)), self.assertRaises(ValueError):
                SourceExecutionContext(**{**self.arguments, **mutation})


if __name__ == "__main__":
    unittest.main()
