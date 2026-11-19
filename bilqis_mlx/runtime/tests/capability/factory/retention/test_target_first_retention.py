"""#1329 target-first C05 evidence resolves before broader protection work."""
from dataclasses import replace
from types import SimpleNamespace as N
from unittest.mock import ANY, Mock, patch

import bilqis_mlx.runtime.retention.local_screen as local_screen
from bilqis_mlx.runtime.capability_retention import (
    AssessmentPair,
    EvidenceStage,
    case_census_digest,
    evaluate_capabilities,
)
from bilqis_mlx.runtime.capability_retention_foundation import FoundationRetentionPolicy
from bilqis_mlx.runtime.baseline.currentness import BaselineCoverage
from bilqis_mlx.runtime.retention.local_evaluation import (
    evaluate_target_gate,
    finalize_target_first_local_candidate,
)
from bilqis_mlx.runtime.tests.capability.capability_retention_helpers import (
    CANDIDATE,
    PARENT,
    _screen_inputs,
)


def _target_pair(*, measured: bool, gain: bool, group: str = "Z"):
    parent_solver, candidate_solver, target, base_policy, cohorts = _screen_inputs(
        protected_loss=0, labels=(group, "other"))
    source = cohorts[0]
    coverage = BaselineCoverage(
        (target,) if measured else (),
        () if measured else (target,),
        ((group, int(measured), 1),),
        int(measured), 1, "e" * 64)
    policy = FoundationRetentionPolicy(
        ((target, group),), (group,), (), base_policy.probe_each,
        source.expected_case_digest, coverage)
    cohort = replace(
        source,
        capability_groups=((target, group),),
        evidence_stage=EvidenceStage.FOUNDATION_ACQUISITION,
        policy_sha256=policy.digest(),
    )
    candidate = candidate_solver if gain else parent_solver
    return target, policy, AssessmentPair(
        evaluate_capabilities(parent_solver, cohort, PARENT),
        evaluate_capabilities(candidate, cohort, CANDIDATE))


def test_comparable_zero_delta_target_rejects_before_broader_scope():
    target, policy, pair = _target_pair(measured=True, gain=False)

    decision = evaluate_target_gate(
        target, policy, pair,
        retention_protection_plan_sha256="1" * 64)

    assert decision is not None
    assert decision.reason == "NO_MEASURABLE_TARGET_GAIN"
    assert decision.evaluated_capability_ids == (target,)
    assert decision.outcome_scores == ((target, 0, 0, 3),)


def test_unmeasured_zero_delta_target_continues_and_grade_identity_is_opaque():
    target, policy, pair = _target_pair(measured=False, gain=False, group="future-grade-z")

    decision = evaluate_target_gate(
        target, policy, pair,
        retention_protection_plan_sha256="2" * 64)

    assert decision is None


def test_comparable_positive_target_continues():
    target, policy, pair = _target_pair(measured=True, gain=True)

    decision = evaluate_target_gate(
        target, policy, pair,
        retention_protection_plan_sha256="3" * 64)

    assert decision is None


def test_local_coverage_combines_exact_target_state_with_compiled_protection():
    target_plan = N(
        target_capability_id="future.target",
        protected_capability_ids=("established.prerequisite",),
        evaluated_capability_groups=(
            ("future.target", "future-grade-z"),
            ("established.prerequisite", "prior-grade"),
        ),
    )
    target_coverage = BaselineCoverage(
        (), ("future.target",), (("future-grade-z", 0, 1),),
        0, 1, "a" * 64)

    coverage = local_screen._local_coverage(
        target_coverage, target_plan, "b" * 64)

    assert coverage.measured_capabilities == ("established.prerequisite",)
    assert coverage.unmeasured_capabilities == ("future.target",)
    assert coverage.group_denominators == (
        ("future-grade-z", 0, 1), ("prior-grade", 1, 1))


def test_unmeasured_target_still_allows_established_protected_veto():
    parent_solver, candidate_solver, target, base_policy, cohorts = _screen_inputs(
        protected_loss=12, labels=("future-grade-z", "prior-grade"))
    protected = "protected"
    target_cases = cohorts[0].cases
    protected_cases = tuple(
        case for case in cohorts[2].cases if case.capability_id == protected)
    groups = ((target, "future-grade-z"), (protected, "future-grade-z"))
    coverage = BaselineCoverage(
        (protected,), (target,), (("future-grade-z", 1, 2),),
        1, 2, "e" * 64)
    final_policy = FoundationRetentionPolicy(
        groups, ("future-grade-z",), ((protected, 1),),
        base_policy.probe_each, case_census_digest(target_cases + protected_cases),
        coverage)
    fixed = replace(
        cohorts[2],
        cases=target_cases + protected_cases,
        capability_groups=groups,
        expected_case_digest=case_census_digest(target_cases + protected_cases),
        evidence_stage=EvidenceStage.FOUNDATION_ACQUISITION,
        policy_sha256=final_policy.digest(),
    )
    target_pair = AssessmentPair(
        evaluate_capabilities(parent_solver, cohorts[0], PARENT),
        evaluate_capabilities(parent_solver, cohorts[0], CANDIDATE))
    protected_cohort = replace(
        fixed,
        cases=protected_cases,
        capability_groups=((protected, "future-grade-z"),),
        expected_case_digest=case_census_digest(protected_cases),
    )
    protected_pair = AssessmentPair(
        evaluate_capabilities(parent_solver, protected_cohort, PARENT),
        evaluate_capabilities(candidate_solver, protected_cohort, CANDIDATE))

    decision = finalize_target_first_local_candidate(
        target, final_policy, fixed, target_pair, protected_pair,
        retention_protection_plan_sha256="4" * 64,
        evaluated_capability_ids=(target, protected))

    assert decision.reason == "PROTECTED_CAPABILITY_REGRESSION"
    assert decision.blocking_capability == protected
    assert decision.outcome_scores[0] == (target, 0, 0, 3)


def test_live_screen_short_circuits_before_protected_compilation():
    target, protected = "future.target", "future.protected"
    target_plan = N(
        target_capability_id=target,
        target_grade_id="opaque-grade",
        protected_capability_ids=(protected,),
        evaluated_capability_ids=(target, protected),
        evaluated_capability_groups=((target, "opaque-grade"),
                                     (protected, "prior-grade")),
        evaluation_scope_sha256="1" * 64,
        comparison_scope_sha256="2" * 64,
    )
    plan = N(digest="3" * 64, rubric_sha256="4" * 64,
             source_sha256="5" * 64)
    release = N(release_sha256="6" * 64)
    parent = N(baseline_evidence=None)
    cache, target_instrument = N(), N(case=N(capability_id=target))
    rejection = object()
    protected_compile = Mock(side_effect=AssertionError(
        "protected compilation ran before target rejection"))
    fresh_rows = Mock(return_value=N(
        seed=13, rows=({"id": "fresh", "capability": target},)))
    target_cohort = object()
    assessments = Mock(side_effect=(object(), object()))
    observed = []

    with patch.multiple(
            local_screen,
            _split_cached_rows=Mock(return_value=(
                (7, ({"id": "reference", "capability": target},)),
                ((protected, 8, ({"id": "protected", "capability": protected},)),))),
            _comparison_epoch=Mock(return_value=N(identity=lambda capability: capability)),
            BaselineLedger=N(from_optional_record=Mock(return_value=object())),
            baseline_coverage=Mock(return_value=N()),
            candidate_identity_for_canonical_consumer=Mock(return_value="7" * 64),
            _owner_seed=Mock(return_value=11),
            _fresh_rows=fresh_rows,
            _instruments=Mock(return_value=(target_instrument,)),
            _policy=Mock(return_value=object()),
            _cohort=Mock(return_value=target_cohort),
            factory_complete_solver=Mock(side_effect=(
                (object(), "a" * 64), (object(), "b" * 64))),
            evaluate_capabilities=assessments,
            AssessmentPair=Mock(return_value=object()),
            evaluate_target_gate=Mock(return_value=rejection),
            _cached_instruments=protected_compile):
        result = local_screen.foundation_local_retention_screen(
            object(), parent, object(), object(), "artifact", release, plan,
            target_plan, (("trained-family",), ("trained-episode",)),
            ((target, 7, ({"id": "reference", "capability": target},)),
             (protected, 8, ({"id": "protected", "capability": protected},))),
            cache, observer=observed.append)

    assert result[0] is rejection
    protected_compile.assert_not_called()
    fresh_rows.assert_called_once_with(
        ANY,
        (target,), seed=11 + local_screen.C05_FRESH_TARGET_SEED_OFFSET,
        training=(("trained-family",), ("trained-episode",)),
        require_independent=False)
    assert assessments.call_args_list[0].args[1] is target_cohort
    assert assessments.call_args_list[1].args[1] is target_cohort
    profile = {}
    for event in observed:
        profile.update(event)
    assert profile["retention_target_case_count"] == 1
    assert profile["retention_target_shared_backbone_launches"] == 0
    assert profile["retention_target_scalar_neural_launches"] == 0
    progress = [event for event in observed if "retention_completed" in event]
    assert [(event["retention_completed"], event["retention_total"],
             event["retention_subject"], event["retention_role"])
            for event in progress] == [
                (0, 4, target, "parent"),
                (1, 4, target, "parent"),
                (1, 4, target, "candidate"),
                (2, 4, target, "candidate"),
            ]
    for field in (
            "retention_target_prepare_wall_seconds",
            "retention_target_solver_wall_seconds",
            "retention_target_parent_wall_seconds",
            "retention_target_candidate_wall_seconds"):
        assert isinstance(profile[field], float)
        assert profile[field] >= 0.0
    assert "retention_protected_prepare_wall_seconds" not in profile
