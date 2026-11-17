"""Runtime consumes Factory provider-dimension policy without grade dispatch."""
from types import SimpleNamespace
import unittest
from unittest.mock import Mock, patch

from bilqis_mlx.runtime._release_adoption.dimensions import advance_provider_dimensions


class ProviderDimensionRuntimeTests(unittest.TestCase):
    @patch("bilqis_mlx.runtime._release_adoption.dimensions._source_adapters_school")
    @patch("bilqis_mlx.runtime._release_adoption.dimensions._factory_live_answers")
    @patch("bilqis_mlx.runtime._release_adoption.dimensions._factory_provider_dimensions")
    @patch("bilqis_mlx.runtime._release_adoption.dimensions._runtime_state")
    @patch("bilqis_mlx.runtime._release_adoption.dimensions._factory_schedule")
    @patch("bilqis_mlx.runtime._release_adoption.dimensions._runtime_admission")
    def test_future_provider_uses_generic_compiled_successor(
            self, admission, schedule, runtime_state, dimensions, answers, sources):
        current = object()
        program = object()
        admission._require_executable_factory_admission.return_value = current
        schedule.schedule_program_from_executable_release.return_value = program
        runtime_state._state_from_json.return_value = SimpleNamespace(
            stage="AWAITING_NEXT_GRADE")
        dimensions.next_automatic_provider_dimension.return_value = SimpleNamespace(
            dimension_id="lesson-intensity")
        compiled = SimpleNamespace(profile=object(), release=object())
        dimensions.compile_provider_dimension_successor.return_value = compiled
        sources.live_source_registry.return_value = "source-registry"
        answers.live_answer_registry.return_value = "answer-registry"
        expected = ("receipt-2", "course-2", "release-2", "program-2")
        adopt = Mock(return_value=expected)
        receipt = {"school": {}, "qualification": None}

        actual = advance_provider_dimensions(
            "run", receipt, "grade-a", "source-root", {"tokens": ["x"]},
            "course", "release", "program", adopt_executable_profile=adopt)

        self.assertEqual(actual, expected)
        dimensions.compile_provider_dimension_successor.assert_called_once_with(
            current, "lesson-intensity", "source-registry", "answer-registry",
            source_root="source-root", graph={"tokens": ["x"]},
            verification_seed=2026111701)
        adopt.assert_called_once_with(
            "run", receipt, "grade-a", "source-root", {"tokens": ["x"]},
            compiled.profile, compiled_successor=compiled.release)

    @patch("bilqis_mlx.runtime._release_adoption.dimensions._factory_provider_dimensions")
    @patch("bilqis_mlx.runtime._release_adoption.dimensions._runtime_state")
    @patch("bilqis_mlx.runtime._release_adoption.dimensions._factory_schedule")
    @patch("bilqis_mlx.runtime._release_adoption.dimensions._runtime_admission")
    def test_runtime_does_not_progress_before_developmental_boundary(
            self, admission, schedule, runtime_state, dimensions):
        admission._require_executable_factory_admission.return_value = object()
        schedule.schedule_program_from_executable_release.return_value = object()
        runtime_state._state_from_json.return_value = SimpleNamespace(stage="TEACHING")
        receipt = {"school": {}, "qualification": None}
        original = (receipt, "course", "release", "program")

        actual = advance_provider_dimensions(
            "run", receipt, "grade-a", "source-root", {}, *original[1:],
            adopt_executable_profile=Mock())

        self.assertEqual(actual, original)
        dimensions.next_automatic_provider_dimension.assert_not_called()


if __name__ == "__main__":
    unittest.main()
