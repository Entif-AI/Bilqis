"""Runtime builder for Factory complete solvers."""
from __future__ import annotations

from bilqis_mlx.runtime.capability_retention import CompleteSolver
from bilqis_mlx.runtime.cognitive_solver import NeuralRequest, SolveBudget, SolveContext
from bilqis_mlx.semantics.cognitive_dag import DAGBudget

from ..factory_evaluation_batching import PreparedFactoryEvaluation


class _FactoryCompleteSolverBuilder:
    def __init__(
        self, source_context, candidate, artifact_path, instruments, *,
        execution_binding, authenticate_context, bind_case, route_plan,
        scalar_proposer, proposal_from_output, batched_outputs, invalid,
    ) -> None:
        self.source_context = source_context
        self.candidate = candidate
        self.artifact_path = artifact_path
        self.execution_binding = execution_binding(candidate)
        self.generation = self.execution_binding.generation_digest
        self.by_goal = {item.case.goal.goal_id: item for item in instruments}
        if len(self.by_goal) != len(instruments):
            invalid("BAMF_C05_FACTORY_INSTRUMENT_GOAL_CONFLICT")
        self.contexts = {}
        self.parameters = candidate.retained_state.optimizer.parameters
        self.telemetry = {
            "shared_backbone_launches": 0,
            "shared_backbone_rows": 0,
            "scalar_neural_launches": 0,
            "largest_shared_rows": 0,
            "largest_shared_positions": 0,
        }
        self.feature_context = authenticate_context(
            candidate, artifact_path, source_context.run_dir)
        self.bind_case = bind_case
        self.route_plan = route_plan
        self.scalar_proposer = scalar_proposer
        self.proposal_from_output = proposal_from_output
        self.batched_outputs = batched_outputs
        self.invalid = invalid

    def prepare(self, goal, requested_generation):
        instrument = self.by_goal.get(goal.goal_id)
        if requested_generation != self.generation or instrument is None:
            self.invalid("BAMF_C05_FACTORY_SOLVER_GENERATION_OR_TASK_DRIFT")
        if goal != instrument.case.goal:
            self.invalid("BAMF_C05_FACTORY_SOLVER_SOURCE_DRIFT")
        batch, authority = self.bind_case(
            self.source_context, self.candidate, self.artifact_path,
            instrument.compiled_case, instrument.source_row,
            generation=self.generation, source_seed=instrument.source_seed,
            source_each=instrument.source_each, authenticated=self.feature_context,
            release_prevalidated=instrument.release_prevalidated)
        if (authority.goal != instrument.case.goal
                or authority.source_family_id != instrument.case.source_family_id
                or authority.episode_id != instrument.case.episode_id):
            self.invalid("BAMF_C05_FACTORY_INSTRUMENT_DRIFT")
        plan = self.route_plan(
            authority.goal, batch, self.feature_context.snapshot, self.generation)
        return batch, plan, authority

    def register_context(self, authority, proposer):
        context = SolveContext(authority.binding, neural_proposer=proposer)
        self.source_context.register_solve_context(context)
        return context

    def scalar_context(self, batch, plan, authority):
        scalar = self.scalar_proposer(
            self.parameters, batch, plan, authority,
            execution_binding=self.execution_binding)

        def proposer(request):
            self.telemetry["scalar_neural_launches"] += 1
            return scalar(request)

        return self.register_context(authority, proposer)

    def context_from(self, prepared, output=None):
        authority = prepared.authority
        if output is None:
            return self.scalar_context(prepared.batch, prepared.plan, authority)

        def proposer(request):
            if (type(request) is not NeuralRequest
                    or request.goal_id != authority.goal.goal_id
                    or request.source_binding_digest != authority.source_binding_sha256
                    or request.generation_digest != authority.generation_binding
                    or request.allowed_operator_ids != authority.goal.allowed_operator_ids):
                self.invalid("BAMF_C04_B11_TASK_REQUEST_MISMATCH")
            return self.proposal_from_output(authority.goal, request, output)

        return self.register_context(authority, proposer)

    def context_for(self, goal, requested_generation):
        cached = self.contexts.get(goal.goal_id)
        if cached is not None:
            if (requested_generation != self.generation
                    or goal != self.by_goal[goal.goal_id].case.goal):
                self.invalid("BAMF_C05_FACTORY_SOLVER_GENERATION_OR_TASK_DRIFT")
            return cached
        batch, plan, authority = self.prepare(goal, requested_generation)
        context = self.scalar_context(batch, plan, authority)
        self.contexts[goal.goal_id] = context
        return context

    def on_launch(self, rows, positions):
        self.telemetry["shared_backbone_launches"] += 1
        self.telemetry["shared_backbone_rows"] += rows
        self.telemetry["largest_shared_rows"] = max(
            self.telemetry["largest_shared_rows"], rows)
        self.telemetry["largest_shared_positions"] = max(
            self.telemetry["largest_shared_positions"], positions)

    def contexts_for(self, goals, requested_generation):
        if requested_generation != self.generation:
            self.invalid("BAMF_C05_FACTORY_SOLVER_GENERATION_OR_TASK_DRIFT")
        for goal in goals:
            instrument = self.by_goal.get(goal.goal_id)
            if instrument is None:
                self.invalid("BAMF_C05_FACTORY_SOLVER_GENERATION_OR_TASK_DRIFT")
            if goal != instrument.case.goal:
                self.invalid("BAMF_C05_FACTORY_SOLVER_SOURCE_DRIFT")
        missing = tuple(goal for goal in goals if goal.goal_id not in self.contexts)
        if missing:
            bound = tuple(self.prepare(goal, requested_generation) for goal in missing)
            prepared = tuple(
                PreparedFactoryEvaluation(batch, plan, authority)
                for batch, plan, authority in bound)
            outputs = self.batched_outputs(
                self.parameters, prepared, on_launch=self.on_launch,
                execution_binding=self.execution_binding)
            for goal, item, output in zip(missing, prepared, outputs, strict=True):
                self.contexts[goal.goal_id] = self.context_from(item, output)
        result = tuple(self.contexts.get(goal.goal_id) for goal in goals)
        if any(context is None for context in result):
            self.invalid("BAMF_C05_FACTORY_BATCH_CONTEXT_MISSING")
        return result

    def build(self) -> CompleteSolver:
        budget = SolveBudget(DAGBudget(), max_neural_calls=1)
        return CompleteSolver(
            self.context_for, budget,
            contexts_for=self.contexts_for, telemetry_for=lambda: dict(self.telemetry))


def build_factory_complete_solver(source_context, candidate, artifact_path, instruments, **deps):
    builder = _FactoryCompleteSolverBuilder(
        source_context, candidate, artifact_path, instruments, **deps)
    return builder.build(), builder.generation


__all__ = ("build_factory_complete_solver",)
