"""Issue #1168 cold-reuse parity and throughput regressions."""
from pathlib import Path
import tempfile
import unittest
from types import SimpleNamespace
from unittest.mock import patch

from bilqis_mlx.runtime.capability_retention import (
    CompleteSolver, EvidenceKind, EvidenceStage, EvaluationCase, EvaluationCohort,
    case_census_digest,
)
from bilqis_mlx.runtime.capability_retention_foundation import (
    FoundationRetentionPolicy, evaluate_foundation_fixed_school_candidate,
)
from bilqis_mlx.runtime.cognitive_solver import (
    GenerationBinding, SolveBudget, SolveContext, solve_task,
)
from bilqis_mlx.runtime.factory_compiled_cohort import (
    load_compiled_case, seal_compiled_case,
)
from bilqis_mlx.runtime.factory_complete_solver import FactoryEvaluationInstrument
from bilqis_mlx.semantics.cognitive_dag import DAGBudget
from bilqis_mlx.semantics.cognitive_operators import TypedValue
from bilqis_mlx.semantics.domains import contract_digest
from bilqis_mlx.semantics.tests.test_frame_compiler import RELEASE
import bilqis_mlx.runtime.factory_complete_solver as complete_solver

from .compiled_evaluation_fixtures import compiled_case


def _cold_case(compiled):
    directory = tempfile.TemporaryDirectory()
    root = Path(directory.name)
    artifact = seal_compiled_case(root, compiled)
    return directory, load_compiled_case(root, artifact, compiled.identity_sha256)


class CompiledEvaluationReuseTests(unittest.TestCase):
    def test_cold_task_contract_has_scalar_result_parity_and_separate_generation_identity(self):
        compiled = compiled_case()
        directory, cold = _cold_case(compiled)
        self.addCleanup(directory.cleanup)
        original_context = SolveContext(compiled.task_template.binding)
        cold_context = SolveContext(cold.task_template.binding)
        budget = SolveBudget(DAGBudget(), max_neural_calls=0)
        parent_generation, candidate_generation = "8" * 64, "9" * 64
        original = solve_task(
            compiled.task_template.goal, original_context,
            GenerationBinding(
                parent_generation, compiled.task_template.goal.semantic_release,
                contract_digest(compiled.task_template.binding)), budget)
        reused = solve_task(
            cold.task_template.goal, cold_context,
            GenerationBinding(
                parent_generation, cold.task_template.goal.semantic_release,
                contract_digest(cold.task_template.binding)), budget)
        candidate = solve_task(
            cold.task_template.goal, cold_context,
            GenerationBinding(
                candidate_generation, cold.task_template.goal.semantic_release,
                contract_digest(cold.task_template.binding)), budget)
        self.assertEqual(original, reused)
        self.assertEqual(reused.answer, candidate.answer)
        self.assertEqual(reused.task_sha256, candidate.task_sha256)
        self.assertNotEqual(reused.generation_digest, candidate.generation_digest)

    def test_cold_reuse_preserves_foundation_c05_decision(self):
        compiled = compiled_case()
        directory, cold = _cold_case(compiled)
        self.addCleanup(directory.cleanup)
        goal = compiled.task_template.goal
        cases = tuple(EvaluationCase(
            f"case-{index}", "A.IDENTITY", "A", f"family-{index}",
            f"episode-{index}", goal, TypedValue("Boolean", True, RELEASE))
            for index in range(2))
        census = case_census_digest(cases)
        policy = FoundationRetentionPolicy(
            (("A.IDENTITY", "A"),), ("A",), (), 2, census)
        fixed = EvaluationCohort(
            EvidenceKind.FIXED_SCHOOL, cases, (("A.IDENTITY", "A"),),
            "1" * 64, "2" * 64, "3" * 64, policy.digest(), (), (), census,
            evidence_stage=EvidenceStage.FOUNDATION_ACQUISITION)
        budget = SolveBudget(DAGBudget(), max_neural_calls=0)
        original_context = SolveContext(compiled.task_template.binding)
        cold_context = SolveContext(cold.task_template.binding)
        original_solver = CompleteSolver(lambda _goal, _generation: original_context, budget)
        cold_solver = CompleteSolver(lambda _goal, _generation: cold_context, budget)
        generations = ("8" * 64, "9" * 64)
        reference = evaluate_foundation_fixed_school_candidate(
            original_solver, original_solver, "A.IDENTITY", policy, fixed, *generations)
        reused = evaluate_foundation_fixed_school_candidate(
            cold_solver, cold_solver, "A.IDENTITY", policy, fixed, *generations)
        self.assertEqual(reused, reference)

    def test_cold_cohort_hit_bypasses_compilation_and_lowering_path(self):
        compiled = compiled_case()
        cohort = {"compiled_case_artifact_sha256": ["7" * 64]}
        source_context = SimpleNamespace(
            run_dir=Path("."), release=SimpleNamespace(
                release_sha256="a" * 64, semantic_catalog_sha256="b" * 64))

        class Authenticated:
            def __post_init__(self):
                return None

        with (
            patch.object(complete_solver, "authenticate_bamf_execution_feature_context",
                         return_value=Authenticated()) as authenticate,
            patch.object(complete_solver, "compiled_cohort_candidates",
                         return_value=(cohort,)),
            patch.object(complete_solver, "load_compiled_cohort_cases",
                         return_value=(compiled,)) as load,
            patch.object(complete_solver, "compiled_case_matches_contract",
                         return_value=True) as matches,
            patch.object(complete_solver, "_instrument_from_compiled",
                         return_value="cold-instrument") as from_cache,
            patch.object(complete_solver, "_factory_evaluation_instrument",
                         side_effect=AssertionError("cold hit recompiled")) as compile_case,
        ):
            actual = complete_solver.factory_evaluation_instruments(
                source_context, object(), "artifact", ({
                    "id": "row-1", "capability": "A.IDENTITY",
                    "tokens": [1], "gold": "TRUE",
                },), seed=17, each=1, source_cohort_sha256="c" * 64)
        self.assertEqual(actual, ("cold-instrument",))
        self.assertEqual((authenticate.call_count, load.call_count,
                          matches.call_count, from_cache.call_count,
                          compile_case.call_count), (1, 1, 1, 1, 0))

    def test_cohort_compile_authenticates_once_and_compiles_each_row_once(self):
        rows = tuple({
            "id": f"row-{index}", "capability": "A.IDENTITY",
            "tokens": [1], "gold": "TRUE",
        } for index in range(4))
        source_context = SimpleNamespace(run_dir=Path("."))

        class Authenticated:
            def __post_init__(self):
                return None

        with (
            patch.object(complete_solver, "authenticate_bamf_execution_feature_context",
                         return_value=Authenticated()) as authenticate,
            patch.object(complete_solver, "_factory_evaluation_instrument",
                         side_effect=lambda *args, **kwargs: args[3]["id"]) as compile_case,
        ):
            actual = complete_solver.factory_evaluation_instruments(
                source_context, object(), "artifact", rows, seed=19, each=1)
        self.assertEqual(actual, tuple(row["id"] for row in rows))
        self.assertEqual(authenticate.call_count, 1)
        self.assertEqual(compile_case.call_count, len(rows))

    def test_parent_candidate_solvers_add_two_generation_authentications_only(self):
        compiled = compiled_case()
        goal = compiled.task_template.goal
        case = EvaluationCase(
            "row-1", "A.IDENTITY", "A", "family-1", "episode-1", goal,
            TypedValue("Boolean", True, RELEASE))
        instrument = FactoryEvaluationInstrument(
            case, compiled, {"id": "row-1", "capability": "A.IDENTITY",
                             "tokens": [1], "gold": "TRUE"}, 17, 1)

        class SourceContext:
            run_dir = Path(".")

            def register_solve_context(self, _context):
                return None

        class Authenticated:
            snapshot = object()

            def __post_init__(self):
                return None

        candidate = SimpleNamespace(
            retained_state=SimpleNamespace(optimizer=SimpleNamespace(parameters={})))
        with (
            patch.object(
                complete_solver, "_execution_binding",
                side_effect=(
                    SimpleNamespace(generation_digest="8" * 64),
                    SimpleNamespace(generation_digest="9" * 64),
                ),
            ),
            patch.object(complete_solver, "authenticate_bamf_execution_feature_context",
                         return_value=Authenticated()) as authenticate,
            patch.object(complete_solver, "bind_factory_evaluation_case",
                         return_value=(object(), compiled.task_template)) as bind,
            patch.object(complete_solver, "task_goal_route_plan", return_value=object()),
            patch.object(complete_solver, "b11_task_goal_proposer",
                         return_value=lambda _request: None),
        ):
            parent_solver, parent_generation = complete_solver.factory_complete_solver(
                SourceContext(), candidate, "artifact", (instrument,))
            candidate_solver, candidate_generation = complete_solver.factory_complete_solver(
                SourceContext(), candidate, "artifact", (instrument,))
            parent_solver.context_for(goal, parent_generation)
            candidate_solver.context_for(goal, candidate_generation)
        self.assertNotEqual(parent_generation, candidate_generation)
        self.assertEqual(authenticate.call_count, 2)
        self.assertEqual(bind.call_count, 2)

    def test_complete_solver_source_does_not_recompile_evaluation_rows(self):
        source = Path(
            "bilqis_mlx/runtime/_capability/factory/factory_complete_solver.py"
        ).read_text()
        solver = source[source.index("def factory_complete_solver("):]
        self.assertNotIn("compile_factory_evaluation_batch(", solver)
        self.assertNotIn("factory_task_authority(", solver)


if __name__ == "__main__":
    unittest.main()
