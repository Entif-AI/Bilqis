"""Factory-owned C05 cases and real B11/B10/C04 complete solvers."""
from __future__ import annotations

from dataclasses import dataclass

from bilqis_mlx.runtime.backbone_identity import issue_execution_generation_binding
from bilqis_mlx.runtime.bamf_bundle import (
    BamfBundleCandidate, authenticate_bamf_execution_feature_context,
)
from bilqis_mlx.runtime.capability_retention import CompleteSolver, EvaluationCase
from bilqis_mlx.runtime.cognitive_solver import NeuralRequest, SolveBudget, SolveContext
from bilqis_mlx.runtime.source_execution import SourceExecutionContext
from bilqis_mlx.semantics.cognitive_dag import DAGBudget
from bilqis_mlx.semantics.cognitive_operators import TypedValue
from bilqis_mlx.semantics.domains import contract_digest

from .capability_evaluation import _invalid
from .factory_evaluation_batching import (
    PreparedFactoryEvaluation, batched_factory_outputs,
)
from .factory_evaluation_compiler import (
    CompiledFactoryEvaluationCase, bind_factory_evaluation_case,
    compile_factory_evaluation_case, compiled_case_matches_contract,
)
from .factory_compiled_cohort import (
    compiled_cohort_candidates, compiled_cohort_record,
    load_compiled_cohort_cases, seal_compiled_case, seal_compiled_cohort,
)
from .task_goal_readout import (
    b11_task_goal_proposer, proposal_from_task_goal_output, task_goal_route_plan,
)


@dataclass(frozen=True)
class FactoryEvaluationInstrument:
    case: EvaluationCase
    compiled_case: CompiledFactoryEvaluationCase
    source_row: dict
    source_seed: int
    source_each: int

    def __post_init__(self):
        if (type(self.case) is not EvaluationCase
                or type(self.compiled_case) is not CompiledFactoryEvaluationCase
                or self.compiled_case.task_template.source_row_id != self.case.case_id
                or not isinstance(self.source_row, dict)
                or self.source_row.get("id") != self.case.case_id
                or type(self.source_seed) is not int or self.source_seed < 0
                or type(self.source_each) is not int or self.source_each < 1):
            _invalid("BAMF_C05_FACTORY_INSTRUMENT_INVALID")


def _execution_binding(candidate: BamfBundleCandidate):
    if not isinstance(candidate, BamfBundleCandidate):
        _invalid("BAMF_C05_CANDIDATE_REQUIRED")
    return issue_execution_generation_binding(candidate.retained_state.optimizer.parameters,
        spec=candidate.topology, extents=candidate.extents)


def _factory_gold(source_context, row, goal):
    execution = source_context.release.execution_plan.capability_map.get(
        row.get("capability"))
    if execution is None:
        _invalid("BAMF_C05_GOLD_CAPABILITY_MISSING")
    raw = row.get("gold")
    if type(raw) not in (int, str):
        _invalid("BAMF_C05_GOLD_MODALITY_UNSUPPORTED")
    text = str(raw)
    matches = []
    for family in execution.answer_families:
        modality = source_context.answer_registry.require(family.kind)
        active = modality.canonicalize(tuple(family.values))
        if text in active:
            matches.append(family.kind)
    if len(matches) != 1:
        _invalid("BAMF_C05_GOLD_MODALITY_AMBIGUOUS")
    family = matches[0]
    if goal.output_signature == "Number" and family == "numeric_active":
        return TypedValue("Number", int(text), goal.semantic_release)
    if goal.output_signature == "Boolean" and family == "binary":
        if text not in {"FALSE", "TRUE"}:
            _invalid("BAMF_C05_GOLD_MODALITY_UNSUPPORTED")
        return TypedValue("Boolean", text == "TRUE", goal.semantic_release)
    if goal.output_signature == "OperatorId" and family == "boolean_operator":
        return TypedValue("OperatorId", text, goal.semantic_release)
    _invalid("BAMF_C05_GOLD_MODALITY_UNSUPPORTED")


def _factory_evaluation_instrument(
    source_context: SourceExecutionContext,
    candidate: BamfBundleCandidate,
    artifact_path: str,
    row: dict,
    *,
    source_seed: int,
    source_each: int,
    authenticated=None,
) -> FactoryEvaluationInstrument:
    """Freeze one independent Factory row into a C05 case without solver choice."""
    compiled_case = compile_factory_evaluation_case(
        source_context, candidate, artifact_path, row,
        source_seed=source_seed, source_each=source_each,
        authenticated=authenticated)
    return _instrument_from_compiled(
        source_context, row, compiled_case,
        source_seed=source_seed, source_each=source_each)


def _instrument_from_compiled(
    source_context: SourceExecutionContext,
    row: dict,
    compiled_case: CompiledFactoryEvaluationCase,
    *,
    source_seed: int,
    source_each: int,
) -> FactoryEvaluationInstrument:
    authority = compiled_case.task_template
    execution = source_context.release.execution_plan.capability_map[
        authority.capability_id]
    case = EvaluationCase(
        authority.source_row_id, authority.capability_id, execution.grade_id,
        authority.source_family_id, authority.episode_id, authority.goal,
        _factory_gold(source_context, row, authority.goal))
    return FactoryEvaluationInstrument(
        case, compiled_case, row, source_seed, source_each)


def factory_evaluation_instrument(
    source_context: SourceExecutionContext,
    candidate: BamfBundleCandidate,
    artifact_path: str,
    row: dict,
    *,
    source_seed: int,
    source_each: int,
) -> FactoryEvaluationInstrument:
    return _factory_evaluation_instrument(
        source_context, candidate, artifact_path, row,
        source_seed=source_seed, source_each=source_each)


def factory_evaluation_instruments(
    source_context: SourceExecutionContext,
    candidate: BamfBundleCandidate,
    artifact_path: str,
    rows,
    *,
    seed: int,
    each: int | None = None,
    source_cohort_sha256: str | None = None,
) -> tuple[FactoryEvaluationInstrument, ...]:
    """Compile one immutable cohort with one shared feature authentication."""
    rows = tuple(rows)
    if not rows:
        _invalid("BAMF_C05_FACTORY_INSTRUMENTS_REQUIRED")
    authenticated = authenticate_bamf_execution_feature_context(
        candidate, artifact_path, source_context.run_dir)
    counts = {}
    if each is None:
        for row in rows:
            capability = row.get("capability")
            counts[capability] = counts.get(capability, 0) + 1
    each_values = tuple(
        each if each is not None else counts[row.get("capability")] for row in rows)
    if source_cohort_sha256 is not None:
        candidates = compiled_cohort_candidates(
            source_context.run_dir,
            source_cohort_sha256=source_cohort_sha256,
            factory_release_sha256=source_context.release.release_sha256,
            semantic_catalog_sha256=source_context.release.semantic_catalog_sha256,
            source_seed=seed)
        for record in candidates:
            artifacts = record.get("compiled_case_artifact_sha256")
            if not isinstance(artifacts, list) or not artifacts:
                continue
            cached = load_compiled_cohort_cases(source_context.run_dir, record)
            if (len(cached) == len(rows)
                    and all(compiled_case_matches_contract(
                        source_context, candidate, artifact_path, compiled_case, row,
                        source_seed=seed, source_each=row_each,
                        authenticated=authenticated)
                        for compiled_case, row, row_each in zip(
                            cached, rows, each_values))):
                return tuple(_instrument_from_compiled(
                    source_context, row, compiled_case,
                    source_seed=seed, source_each=row_each)
                    for compiled_case, row, row_each in zip(
                        cached, rows, each_values))
    instruments = tuple(_factory_evaluation_instrument(
        source_context, candidate, artifact_path, row,
        source_seed=seed,
        source_each=row_each,
        authenticated=authenticated,
    ) for row, row_each in zip(rows, each_values))
    if source_cohort_sha256 is not None:
        artifacts = tuple(seal_compiled_case(
            source_context.run_dir, item.compiled_case) for item in instruments)
        record = compiled_cohort_record(
            factory_release_sha256=source_context.release.release_sha256,
            semantic_catalog_sha256=source_context.release.semantic_catalog_sha256,
            source_cohort_sha256=source_cohort_sha256,
            source_seed=seed,
            case_records=tuple(
                item.compiled_case.identity_record for item in instruments),
            case_artifacts=artifacts)
        seal_compiled_cohort(source_context.run_dir, record)
    return instruments


class _FactoryCompleteSolverBuilder:
    """Own one candidate's exact Factory evaluation contexts and batching state."""

    def __init__(
        self,
        source_context: SourceExecutionContext,
        candidate: BamfBundleCandidate,
        artifact_path: str,
        instruments: tuple[FactoryEvaluationInstrument, ...],
    ) -> None:
        self.source_context = source_context
        self.candidate = candidate
        self.artifact_path = artifact_path
        self.execution_binding = _execution_binding(candidate)
        self.generation = self.execution_binding.generation_digest
        self.by_goal = {item.case.goal.goal_id: item for item in instruments}
        if len(self.by_goal) != len(instruments):
            _invalid("BAMF_C05_FACTORY_INSTRUMENT_GOAL_CONFLICT")
        self.contexts = {}
        self.parameters = candidate.retained_state.optimizer.parameters
        self.telemetry = {
        "shared_backbone_launches": 0,
        "shared_backbone_rows": 0,
        "scalar_neural_launches": 0,
        "largest_shared_rows": 0,
        "largest_shared_positions": 0,
        }
        self.feature_context = authenticate_bamf_execution_feature_context(
            candidate, artifact_path, source_context.run_dir)

    def prepare(self, goal, requested_generation):
        instrument = self.by_goal.get(goal.goal_id)
        if requested_generation != self.generation or instrument is None:
            _invalid("BAMF_C05_FACTORY_SOLVER_GENERATION_OR_TASK_DRIFT")
        if goal != instrument.case.goal:
            _invalid("BAMF_C05_FACTORY_SOLVER_SOURCE_DRIFT")
        batch, authority = bind_factory_evaluation_case(
            self.source_context, self.candidate, self.artifact_path, instrument.compiled_case,
            instrument.source_row, generation=self.generation,
            source_seed=instrument.source_seed, source_each=instrument.source_each,
            authenticated=self.feature_context)
        if (authority.goal != instrument.case.goal
                or authority.source_family_id != instrument.case.source_family_id
                or authority.episode_id != instrument.case.episode_id):
            _invalid("BAMF_C05_FACTORY_INSTRUMENT_DRIFT")
        plan = task_goal_route_plan(
            authority.goal, batch, self.feature_context.snapshot, self.generation)
        return batch, plan, authority

    def register_context(self, authority, proposer):
        context = SolveContext(authority.binding, neural_proposer=proposer)
        self.source_context.register_solve_context(context)
        return context

    def scalar_context(self, batch, plan, authority):
        scalar = b11_task_goal_proposer(self.parameters, batch, plan, authority, execution_binding=self.execution_binding)

        def proposer(request):
            self.telemetry["scalar_neural_launches"] += 1
            return scalar(request)

        return self.register_context(authority, proposer)

    def context_from(self, prepared, output=None):
        authority = prepared.authority
        if output is None:
            return self.scalar_context(
                prepared.batch, prepared.plan, authority)
        def proposer(request):
            if (type(request) is not NeuralRequest
                    or request.goal_id != authority.goal.goal_id
                    or request.source_binding_digest != authority.source_binding_sha256
                    or request.generation_digest != authority.generation_binding
                    or request.allowed_operator_ids != authority.goal.allowed_operator_ids):
                _invalid("BAMF_C04_B11_TASK_REQUEST_MISMATCH")
            return proposal_from_task_goal_output(authority.goal, request, output)
        return self.register_context(authority, proposer)

    def context_for(self, goal, requested_generation):
        cached = self.contexts.get(goal.goal_id)
        if cached is not None:
            if (requested_generation != self.generation
                    or goal != self.by_goal[goal.goal_id].case.goal):
                _invalid("BAMF_C05_FACTORY_SOLVER_GENERATION_OR_TASK_DRIFT")
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
            _invalid("BAMF_C05_FACTORY_SOLVER_GENERATION_OR_TASK_DRIFT")
        for goal in goals:
            instrument = self.by_goal.get(goal.goal_id)
            if instrument is None:
                _invalid("BAMF_C05_FACTORY_SOLVER_GENERATION_OR_TASK_DRIFT")
            if goal != instrument.case.goal:
                _invalid("BAMF_C05_FACTORY_SOLVER_SOURCE_DRIFT")
        missing = tuple(goal for goal in goals if goal.goal_id not in self.contexts)
        if missing:
            bound = tuple(self.prepare(goal, requested_generation) for goal in missing)
            prepared = tuple(
                PreparedFactoryEvaluation(batch, plan, authority)
                for batch, plan, authority in bound)
            outputs = batched_factory_outputs(self.parameters, prepared, on_launch=self.on_launch,
                execution_binding=self.execution_binding)
            for goal, item, output in zip(missing, prepared, outputs, strict=True):
                self.contexts[goal.goal_id] = self.context_from(item, output)
        result = tuple(self.contexts.get(goal.goal_id) for goal in goals)
        if any(context is None for context in result):
            _invalid("BAMF_C05_FACTORY_BATCH_CONTEXT_MISSING")
        return result

    def telemetry_for(self):
        return dict(self.telemetry)

    def build(self) -> CompleteSolver:
        budget = SolveBudget(DAGBudget(), max_neural_calls=1)
        return CompleteSolver(
            self.context_for, budget,
            contexts_for=self.contexts_for, telemetry_for=self.telemetry_for)


def factory_complete_solver(
    source_context: SourceExecutionContext,
    candidate: BamfBundleCandidate,
    artifact_path: str,
    instruments: tuple[FactoryEvaluationInstrument, ...],
) -> tuple[CompleteSolver, str]:
    """Bind every case to the exact candidate parameters and real B11 proposer."""
    if (not instruments or any(type(item) is not FactoryEvaluationInstrument
                               for item in instruments)):
        _invalid("BAMF_C05_FACTORY_INSTRUMENTS_REQUIRED")
    builder = _FactoryCompleteSolverBuilder(
        source_context, candidate, artifact_path, instruments)
    return builder.build(), builder.generation


__all__ = (
    "FactoryEvaluationInstrument", "factory_complete_solver",
    "factory_evaluation_instrument", "factory_evaluation_instruments",
)
