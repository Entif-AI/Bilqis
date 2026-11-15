"""Factory-owned C05 cases and real B11/B10/C04 complete solvers."""
from __future__ import annotations

from dataclasses import dataclass

from bilqis_mlx.runtime.backbone_identity import execution_generation_digest
from bilqis_mlx.runtime.bamf_bundle import (
    BamfBundleCandidate, authenticate_bamf_execution_feature_context,
)
from bilqis_mlx.runtime.capability_retention import CompleteSolver, EvaluationCase
from bilqis_mlx.runtime.cognitive_solver import SolveBudget, SolveContext
from bilqis_mlx.runtime.source_execution import SourceExecutionContext
from bilqis_mlx.semantics.cognitive_dag import DAGBudget
from bilqis_mlx.semantics.cognitive_operators import TypedValue
from bilqis_mlx.semantics.domains import contract_digest

from .capability_evaluation import _invalid
from .factory_evaluation_compiler import (
    CompiledFactoryEvaluationCase, bind_factory_evaluation_case,
    compile_factory_evaluation_case, compiled_case_matches_contract,
)
from .factory_compiled_cohort import (
    compiled_cohort_candidates, compiled_cohort_record,
    load_compiled_cohort_cases, seal_compiled_case, seal_compiled_cohort,
)
from .task_goal_readout import b11_task_goal_proposer, task_goal_route_plan


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


def _generation(candidate: BamfBundleCandidate) -> str:
    if not isinstance(candidate, BamfBundleCandidate):
        _invalid("BAMF_C05_CANDIDATE_REQUIRED")
    return execution_generation_digest(
        candidate.retained_state.optimizer.parameters,
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
    generation = _generation(candidate)
    by_goal = {item.case.goal.goal_id: item for item in instruments}
    if len(by_goal) != len(instruments):
        _invalid("BAMF_C05_FACTORY_INSTRUMENT_GOAL_CONFLICT")
    contexts = {}
    parameters = candidate.retained_state.optimizer.parameters
    feature_context = authenticate_bamf_execution_feature_context(
        candidate, artifact_path, source_context.run_dir)

    def context_for(goal, requested_generation):
        instrument = by_goal.get(goal.goal_id)
        if requested_generation != generation or instrument is None:
            _invalid("BAMF_C05_FACTORY_SOLVER_GENERATION_OR_TASK_DRIFT")
        if goal != instrument.case.goal:
            _invalid("BAMF_C05_FACTORY_SOLVER_SOURCE_DRIFT")
        cached = contexts.get(goal.goal_id)
        if cached is not None:
            return cached
        batch, authority = bind_factory_evaluation_case(
            source_context, candidate, artifact_path, instrument.compiled_case,
            instrument.source_row, generation=generation,
            source_seed=instrument.source_seed, source_each=instrument.source_each,
            authenticated=feature_context)
        if (authority.goal != instrument.case.goal
                or authority.source_family_id != instrument.case.source_family_id
                or authority.episode_id != instrument.case.episode_id):
            _invalid("BAMF_C05_FACTORY_INSTRUMENT_DRIFT")
        plan = task_goal_route_plan(
            authority.goal, batch, feature_context.snapshot, generation)
        proposer = b11_task_goal_proposer(
            parameters, batch, plan, authority)
        context = SolveContext(
            authority.binding, neural_proposer=proposer)
        source_context.register_solve_context(context)
        contexts[goal.goal_id] = context
        return context

    budget = SolveBudget(DAGBudget(), max_neural_calls=1)
    return CompleteSolver(context_for, budget), generation


__all__ = (
    "FactoryEvaluationInstrument", "factory_complete_solver",
    "factory_evaluation_instrument", "factory_evaluation_instruments",
)
