"""Complete-solver adapters for native title defense and diagnostic mastery debt."""
from __future__ import annotations

from dataclasses import asdict, dataclass
from fractions import Fraction
from typing import Callable

from ..curriculum.promotion import PROMOTION_SWEEP_ENTRY_FLOOR, PROMOTION_SWEEP_FAILURE_FLOOR
from ..runtime.capability_retention import (
    Assessment, AssessmentPair, CompleteSolver, EvaluationCohort,
    _answer_identity, _invalid, _names, _sha, evaluate_capabilities,
)
from ..semantics.domains import contract_digest
from .champions import Checkpoint
from .championship_policy import CONTEXT_KEYS
from .championship_witnesses import verified_battery
from .epoch_championships import _pair_key
from .mentor_epoch import _pointer


@dataclass(frozen=True)
class ReplayBinding:
    solver: CompleteSolver
    generation_digest: str
    checkpoint: Checkpoint
    checkpoint_origin_group: str
    solver_contracts: tuple[str, ...]
    verify_generation: Callable[[str, Checkpoint], bool]

    def __post_init__(self):
        if (not isinstance(self.solver, CompleteSolver) or not _sha(self.generation_digest)
                or not isinstance(self.checkpoint, Checkpoint)
                or not isinstance(self.checkpoint_origin_group, str)
                or not self.checkpoint_origin_group
                or not _names(self.solver_contracts) or not self.solver_contracts
                or any(not _sha(value) for value in self.solver_contracts)
                or not callable(self.verify_generation)):
            _invalid("BAMF_CHAMPIONSHIP_REPLAY_BINDING_INVALID")

        _pointer(asdict(self.checkpoint))

    def measure(self, cohort):
        if self.verify_generation(self.generation_digest, self.checkpoint) is not True:
            _invalid("BAMF_CHAMPIONSHIP_GENERATION_CHECKPOINT_UNVERIFIED")
        result = evaluate_capabilities(self.solver, cohort, self.generation_digest)
        if not set(result.solver_contracts) <= set(self.solver_contracts):
            _invalid("BAMF_CHAMPIONSHIP_SOLVER_CONFIGURATION_DRIFT")
        return result

    def provenance(self):
        return {"schema_version": "bilqis.c05.complete-solver-provenance/v1",
                "generation_digest": self.generation_digest,
                "weight_sha256": self.checkpoint.sha256,
                "solver_contracts": sorted(self.solver_contracts)}


def _source_context(cohort):
    return {
        "cohort_sha256": cohort.expected_case_digest,
        "rubric_sha256": cohort.rubric_sha256,
        "cohort_rubric_sha256": cohort.rubric_sha256,
        "assessment_scope_sha256": cohort.scope_sha256,
        "source_graph_sha256": cohort.source_sha256,
        "source_oracle_sha256": contract_digest(tuple(
            (case.case_id, _answer_identity(case.gold)) for case in cohort.cases)),
    }


def assessment_exam(assessment, binding, *, challenge_group):
    """Convert current evaluator evidence to the existing native title contract."""
    if (not isinstance(assessment, Assessment) or not isinstance(binding, ReplayBinding)
            or assessment.generation_digest != binding.generation_digest
            or binding.verify_generation(binding.generation_digest, binding.checkpoint) is not True
            or not set(assessment.solver_contracts) <= set(binding.solver_contracts)
            or challenge_group not in dict(assessment.cohort.capability_groups).values()):
        _invalid("BAMF_CHAMPIONSHIP_ASSESSMENT_BINDING_INVALID")
    questions, correct = {}, {}
    for case, result in zip(assessment.cohort.cases, assessment.results):
        question = {"id": case.case_id, "capability": case.capability_id,
                    "gold": contract_digest(_answer_identity(case.gold))}
        questions.setdefault(case.capability_id, []).append(question)
        correct.setdefault(case.capability_id, [])
        if _answer_identity(result.answer) == _answer_identity(case.gold):
            correct[case.capability_id].append(question)
    return {
        **_source_context(assessment.cohort),
        "checkpoint": asdict(binding.checkpoint),
        "checkpoint_origin_group": binding.checkpoint_origin_group,
        "challenge_group": challenge_group,
        "complete_solver_provenance": binding.provenance(),
        "scores": {capability: dict(zip(("correct", "total"), assessment.score(capability)))
                   for capability, _ in assessment.cohort.capability_groups},
        "questions": questions, "correct_questions": correct,
    }


def fresh_title_match(role, incumbent, challenger, current_cohort, *, resolve_cohort,
                      settled_matchups, challenge_group, allow_legacy_role=False,
                      comparison_context_sha256=None):
    """Produce fresh current/battery evidence; native engine alone settles titles."""
    if (not isinstance(role, dict) or not isinstance(incumbent, ReplayBinding)
            or not isinstance(challenger, ReplayBinding)
            or not isinstance(current_cohort, EvaluationCohort)
            or not callable(resolve_cohort) or not isinstance(settled_matchups, dict)
            or type(allow_legacy_role) is not bool
            or role.get("checkpoint", {}).get("sha256") != incumbent.checkpoint.sha256):
        _invalid("BAMF_CHAMPIONSHIP_MATCH_INPUT_INVALID")
    stored_pointer = _pointer(role["checkpoint"])
    if any(stored_pointer.get(key) != value for key, value in asdict(incumbent.checkpoint).items()):
        _invalid("BAMF_CHAMPIONSHIP_INCUMBENT_CHECKPOINT_DRIFT")
    provenance = role.get("complete_solver_provenance")
    if ((provenance is None and not allow_legacy_role)
            or (provenance is not None and provenance != incumbent.provenance())):
        _invalid("BAMF_CHAMPIONSHIP_INCUMBENT_GENERATION_DRIFT")
    if (incumbent.checkpoint.sha256 == challenger.checkpoint.sha256
            or _pair_key(role["capability"], incumbent.checkpoint.sha256,
                         challenger.checkpoint.sha256,
                         comparison_context_sha256) in settled_matchups):
        _invalid("BAMF_CHAMPIONSHIP_WEIGHT_PAIR_ALREADY_SETTLED")
    parent = incumbent.measure(current_cohort)
    candidate = challenger.measure(current_cohort)
    AssessmentPair(parent, candidate)
    results = {incumbent.checkpoint.sha256: {}, challenger.checkpoint.sha256: {}}
    for segment in verified_battery(role):
        key = tuple((name, segment[name]) for name in (*CONTEXT_KEYS, "cohort_rubric_sha256")
                    if name in segment)
        cohort = resolve_cohort(key)
        if (not isinstance(cohort, EvaluationCohort)
                or any(_source_context(cohort).get(name) != value for name, value in key)):
            _invalid("BAMF_CHAMPIONSHIP_BATTERY_SOURCE_DRIFT")
        offered = {case.case_id: case for case in cohort.cases}
        for question in segment["questions"]:
            case = offered.get(question["id"])
            if (case is None or case.capability_id != question["capability"]
                    or contract_digest(_answer_identity(case.gold)) != question["gold"]):
                _invalid("BAMF_CHAMPIONSHIP_BATTERY_QUESTION_DRIFT")
        measured = (incumbent.measure(cohort), challenger.measure(cohort))
        AssessmentPair(*measured)
        for binding, assessment in zip((incumbent, challenger), measured):
            correct = {case.case_id for case, result in zip(cohort.cases, assessment.results)
                       if _answer_identity(result.answer) == _answer_identity(case.gold)}
            results[binding.checkpoint.sha256][segment["sha256"]] = [
                question["id"] for question in segment["questions"]
                if question["id"] in correct]
    return {
        "incumbent_checkpoint_sha256": incumbent.checkpoint.sha256,
        "challenger_checkpoint_sha256": challenger.checkpoint.sha256,
        "incumbent_current_exam": assessment_exam(parent, incumbent, challenge_group=challenge_group),
        "challenger_current_exam": assessment_exam(candidate, challenger, challenge_group=challenge_group),
        "battery_results": results,
    }


@dataclass(frozen=True)
class CapabilityProgress:
    generation_digest: str
    scope_sha256: str
    mean_numerator: int | None
    mean_denominator: int | None
    entry_threshold_met: bool | None
    continuation_threshold_met: bool | None
    active_group_coverage_complete: bool
    perfect_cumulative_mastery: bool
    mastery_debt: tuple[tuple[str, int | None], ...]
    unmeasured_capabilities: tuple[str, ...]
    historical_debt_scope_sha256: str | None
    historical_debt: tuple[tuple[str, int], ...]
    schema_version: str = "bilqis.c05.capability-progress/v1"


def assessment_path_attribution(assessment):
    if not isinstance(assessment, Assessment):
        _invalid("BAMF_PATH_ATTRIBUTION_ASSESSMENT_REQUIRED")
    return tuple((case.case_id, result.route.value, result.neural_calls,
                  sum(receipt.operation_count for receipt in result.dag_receipts))
                 for case, result in zip(assessment.cohort.cases, assessment.results))


def assessment_progress(assessment, *, active_group, cumulative_capabilities, capability_groups, carried_debt,
                        carried_debt_scope_sha256=None):
    if (not isinstance(assessment, Assessment) or not _names(cumulative_capabilities)
            or not cumulative_capabilities or not isinstance(carried_debt, tuple)
            or any(not isinstance(item, tuple) or len(item) != 2
                   or item[0] not in cumulative_capabilities
                   or type(item[1]) is not int or item[1] < 0 for item in carried_debt)
            or len(dict(carried_debt)) != len(carried_debt)
            or (carried_debt and not _sha(carried_debt_scope_sha256))):
        _invalid("BAMF_CAPABILITY_PROGRESS_INPUT_INVALID")
    if (not isinstance(capability_groups, tuple)
            or any(not isinstance(pair, tuple) or len(pair) != 2
                   or not all(isinstance(item, str) and item for item in pair)
                   for pair in capability_groups)
            or len(dict(capability_groups)) != len(capability_groups)
            or set(dict(capability_groups)) != set(cumulative_capabilities)):
        _invalid("BAMF_CAPABILITY_PROGRESS_GROUP_CENSUS_INVALID")
    expected = dict(capability_groups)
    known = dict(assessment.cohort.capability_groups)
    active = tuple(capability for capability, group in expected.items() if group == active_group)
    if not active or any(expected.get(capability) != group for capability, group in known.items()):
        _invalid("BAMF_CAPABILITY_PROGRESS_CENSUS_INVALID")
    complete = set(active) <= set(known)
    mean = (sum((Fraction(*assessment.score(capability)) for capability in active), Fraction()) / len(active)
            if complete else None)
    missing = tuple(capability for capability in cumulative_capabilities if capability not in known)
    comparable = carried_debt_scope_sha256 == assessment.cohort.scope_sha256
    prior = dict(carried_debt) if comparable else {}
    historical = carried_debt if carried_debt and not comparable else ()
    debt = tuple((capability, (assessment.score(capability)[1] - assessment.score(capability)[0]
                              if capability in known else prior.get(capability)))
                 for capability in cumulative_capabilities)
    return CapabilityProgress(
        assessment.generation_digest, assessment.cohort.scope_sha256,
        mean.numerator if mean is not None else None, mean.denominator if mean is not None else None,
        mean >= PROMOTION_SWEEP_ENTRY_FLOOR if mean is not None else None,
        mean >= PROMOTION_SWEEP_FAILURE_FLOOR if mean is not None else None, complete,
        not missing and not historical and all(amount == 0 for _, amount in debt),
        debt, missing, carried_debt_scope_sha256 if historical else None, historical)
