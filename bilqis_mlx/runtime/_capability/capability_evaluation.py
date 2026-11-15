"""Evaluator-side complete-solver measurements and advisory paired eligibility."""
from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
import re
from typing import Callable

from ..errors import ErrorBus, SCHOOL
from ..learning.retention_policy import retention_reason, scaled_loss_allowance
from ..semantics.cognitive_dag import TaskGoal
from ..semantics.cognitive_operators import TypedValue, ValueState
from ..semantics.domains import contract_digest
from .cognitive_solver import (
    CapabilityResult, GenerationBinding, SolveBudget, SolveContext, solve_task,
)

CAPABILITY_GROUP_ARITY = 2


def _invalid(reason):
    ErrorBus.raise_(SCHOOL.BAMF_CAPABILITY_EVIDENCE.INVALID, reason=reason)


def _sha(value):
    return isinstance(value, str) and re.fullmatch(r"[0-9a-f]{64}", value) is not None


def _names(values):
    return (isinstance(values, tuple)
            and all(isinstance(value, str) and value for value in values)
            and len(set(values)) == len(values))


class EvidenceKind(str, Enum):
    FRESH_TARGET = "FRESH_TARGET"
    FRESH_LESSON = "FRESH_LESSON"
    FIXED_SCHOOL = "FIXED_SCHOOL"


class EvidenceStage(str, Enum):
    FOUNDATION_ACQUISITION = "FOUNDATION_ACQUISITION"
    STRICT_GENERALIZATION = "STRICT_GENERALIZATION"


@dataclass(frozen=True)
class EvaluationCase:
    case_id: str
    capability_id: str
    group_id: str
    source_family_id: str
    episode_id: str
    goal: TaskGoal
    gold: TypedValue

    def __post_init__(self):
        if (not all(isinstance(value, str) and value for value in (
                self.case_id, self.capability_id, self.group_id,
                self.source_family_id, self.episode_id))
                or not isinstance(self.goal, TaskGoal)
                or not isinstance(self.gold, TypedValue)
                or self.gold.semantic_release != self.goal.semantic_release
                or self.gold.type_name != self.goal.output_signature
                or self.gold.state is ValueState.UNRESOLVED):
            _invalid("BAMF_EVALUATION_CASE_INVALID")


def case_census_digest(cases: tuple[EvaluationCase, ...]) -> str:
    """Bind the independent source draw, including exact rows and evaluator gold."""
    return contract_digest(cases)


@dataclass(frozen=True)
class EvaluationCohort:
    kind: EvidenceKind
    cases: tuple[EvaluationCase, ...]
    capability_groups: tuple[tuple[str, str], ...]
    rubric_sha256: str
    scope_sha256: str
    source_sha256: str
    policy_sha256: str
    training_family_ids: tuple[str, ...]
    training_episode_ids: tuple[str, ...]
    expected_case_digest: str
    evidence_stage: EvidenceStage = EvidenceStage.FOUNDATION_ACQUISITION
    schema_version: str = "bilqis.c05.evaluation-cohort/v1"

    def __post_init__(self):
        if (not isinstance(self.kind, EvidenceKind)
                or not isinstance(self.cases, tuple) or not self.cases
                or any(not isinstance(case, EvaluationCase) for case in self.cases)
                or not isinstance(self.capability_groups, tuple)
                or any(not isinstance(pair, tuple) or len(pair) != CAPABILITY_GROUP_ARITY
                       or not all(isinstance(item, str) and item for item in pair)
                       for pair in self.capability_groups)
                or len(dict(self.capability_groups)) != len(self.capability_groups)
                or not all(_sha(value) for value in (
                    self.rubric_sha256, self.scope_sha256, self.source_sha256,
                    self.policy_sha256, self.expected_case_digest))
                or not _names(self.training_family_ids)
                or not _names(self.training_episode_ids)
                or not isinstance(self.evidence_stage, EvidenceStage)
                or self.schema_version != "bilqis.c05.evaluation-cohort/v1"):
            _invalid("BAMF_EVALUATION_COHORT_INVALID")
        if (case_census_digest(self.cases) != self.expected_case_digest
                or len({case.case_id for case in self.cases}) != len(self.cases)
                or len({case.episode_id for case in self.cases}) != len(self.cases)
                or {(case.capability_id, case.group_id) for case in self.cases}
                != set(self.capability_groups)):
            _invalid("BAMF_EVALUATION_CENSUS_DRIFT")
        if (self.evidence_stage is EvidenceStage.STRICT_GENERALIZATION
                and self.kind is not EvidenceKind.FIXED_SCHOOL and (
                {case.source_family_id for case in self.cases}
                & set(self.training_family_ids)
                or {case.episode_id for case in self.cases}
                & set(self.training_episode_ids))):
            _invalid("BAMF_EVALUATION_TRAINING_PROVENANCE_OVERLAP")


@dataclass(frozen=True)
class CompleteSolver:
    """Bind the actual solver to task-local source and one opaque generation ID."""
    context_for: Callable[[TaskGoal, str], SolveContext]
    budget: SolveBudget
    contexts_for: Callable[[tuple[TaskGoal, ...], str], tuple[SolveContext, ...]] | None = None
    telemetry_for: Callable[[], dict] | None = None

    def __post_init__(self):
        if (not callable(self.context_for) or not isinstance(self.budget, SolveBudget)
                or (self.contexts_for is not None and not callable(self.contexts_for))
                or (self.telemetry_for is not None and not callable(self.telemetry_for))):
            _invalid("BAMF_COMPLETE_SOLVER_INVALID")

    def _measure(self, goal: TaskGoal, generation: str, context: SolveContext):
        if not isinstance(context, SolveContext):
            _invalid("BAMF_SOLVER_SOURCE_CONTEXT_INVALID")
        binding = GenerationBinding(
            generation, goal.semantic_release, contract_digest(context.binding))
        result = solve_task(goal, context, binding, self.budget)
        tools = contract_digest({
            "budget": self.budget, "routes": context.route_registry,
            "operators": context.binding.registry})
        return result, tools

    def evaluate(self, goal: TaskGoal, generation: str):
        return self._measure(goal, generation, self.context_for(goal, generation))

    def evaluate_cases(self, goals: tuple[TaskGoal, ...], generation: str):
        if (not isinstance(goals, tuple) or not goals
                or any(not isinstance(goal, TaskGoal) for goal in goals)):
            _invalid("BAMF_SOLVER_CASES_INVALID")
        if self.contexts_for is None:
            return tuple(self.evaluate(goal, generation) for goal in goals)
        contexts = self.contexts_for(goals, generation)
        if (not isinstance(contexts, tuple) or len(contexts) != len(goals)
                or any(not isinstance(context, SolveContext) for context in contexts)):
            _invalid("BAMF_SOLVER_BATCH_CONTEXT_INVALID")
        return tuple(
            self._measure(goal, generation, context)
            for goal, context in zip(goals, contexts, strict=True))


def _answer_identity(answer):
    return (answer.type_name, answer.state, answer.semantic_release,
            contract_digest(answer.value))


@dataclass(frozen=True)
class Assessment:
    cohort: EvaluationCohort
    generation_digest: str
    results: tuple[CapabilityResult, ...]
    solver_contracts: tuple[str, ...]
    schema_version: str = "bilqis.c05.assessment/v1"

    def __post_init__(self):
        if (not isinstance(self.cohort, EvaluationCohort)
                or not _sha(self.generation_digest)
                or not isinstance(self.results, tuple)
                or len(self.results) != len(self.cohort.cases)
                or any(not isinstance(result, CapabilityResult) for result in self.results)
                or not isinstance(self.solver_contracts, tuple)
                or len(self.solver_contracts) != len(self.results)
                or any(not _sha(value) for value in self.solver_contracts)
                or self.schema_version != "bilqis.c05.assessment/v1"):
            _invalid("BAMF_ASSESSMENT_INVALID")
        if any(result.generation_digest != self.generation_digest
               or result.task_sha256 != contract_digest(case.goal)
               for case, result in zip(self.cohort.cases, self.results)):
            _invalid("BAMF_ASSESSMENT_GENERATION_OR_TASK_DRIFT")

    def score(self, capability: str):
        paired = tuple((case, result) for case, result in zip(self.cohort.cases, self.results)
                       if case.capability_id == capability)
        if not paired:
            _invalid("BAMF_ASSESSMENT_CAPABILITY_ABSENT")
        return (sum(_answer_identity(result.answer) == _answer_identity(case.gold)
                    for case, result in paired), len(paired))

    def digest(self):
        return contract_digest({
            "schema": self.schema_version, "cohort": self.cohort,
            "generation": self.generation_digest, "contracts": self.solver_contracts,
            "results": tuple(result.replay_record() for result in self.results)})


def evaluate_capabilities(solver, cohort, generation) -> Assessment:
    if (not isinstance(solver, CompleteSolver)
            or not isinstance(cohort, EvaluationCohort) or not _sha(generation)):
        _invalid("BAMF_ASSESSMENT_INPUT_INVALID")
    measurements = solver.evaluate_cases(
        tuple(case.goal for case in cohort.cases), generation)
    return Assessment(cohort, generation, tuple(item[0] for item in measurements),
                      tuple(item[1] for item in measurements))

EvidenceKind.__module__ = "bilqis_mlx.runtime.capability_retention"
EvidenceStage.__module__ = "bilqis_mlx.runtime.capability_retention"
EvaluationCase.__module__ = "bilqis_mlx.runtime.capability_retention"
EvaluationCohort.__module__ = "bilqis_mlx.runtime.capability_retention"
CompleteSolver.__module__ = "bilqis_mlx.runtime.capability_retention"
Assessment.__module__ = "bilqis_mlx.runtime.capability_retention"
