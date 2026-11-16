"""Source-fixture complete-solver titles and diagnostic mastery debt."""
from dataclasses import replace
from copy import deepcopy
import unittest

from bilqis_mlx.errors import BilqisError
from bilqis_mlx.learning.capability_championship import (
    ReplayBinding, assessment_exam, assessment_path_attribution, assessment_progress, fresh_title_match,
)
from bilqis_mlx.learning.champions import Checkpoint
from bilqis_mlx.learning.championship_witnesses import earning_witness, refresh_battery, verified_battery
from bilqis_mlx.learning.epoch_championships import advance_epoch
from bilqis_mlx.runtime.capability_retention import (
    AssessmentPair, CompleteSolver, EvaluationCohort, EvidenceKind, case_census_digest, configuration_outcome,
    evaluate_capabilities,
)
from bilqis_mlx.runtime.cognitive_solver import QualifiedComposition, SolveBudget, SolveContext
from bilqis_mlx.semantics.domains import contract_digest
from bilqis_mlx.runtime.tests.test_bamf_capability_retention import _cases, _solver
from bilqis_mlx.semantics.cognitive_dag import DAGBudget

PARENT, CANDIDATE = "a" * 64, "b" * 64


def _cohort(count=3):
    cases, contexts = _cases("misleading.prefix", "opaque-title-group", count, "title")
    cohort = EvaluationCohort(
        EvidenceKind.FIXED_SCHOOL, cases, (("misleading.prefix", "opaque-title-group"),),
        "d" * 64, "e" * 64, "f" * 64, "0" * 64, (), (), case_census_digest(cases))
    return cohort, contexts


def _replay(solver, cohort, generation, weight, step):
    assessment = evaluate_capabilities(solver, cohort, generation)
    checkpoint = Checkpoint(weight * 64, "bundles/fixture-" + weight, step, True)
    binding = ReplayBinding(
        solver, generation, checkpoint, "opaque-title-group",
        tuple(sorted(set(assessment.solver_contracts))),
        lambda offered_generation, offered_checkpoint: (
            offered_generation == generation and offered_checkpoint == checkpoint))
    return binding, assessment


class CapabilityChampionshipTests(unittest.TestCase):
    def test_thresholds_use_unweighted_means_and_do_not_clear_unseen_scope_debt(self):
        cases, contexts = _cases("capability", "group", 100, "threshold")
        cohort = EvaluationCohort(
            EvidenceKind.FIXED_SCHOOL, cases, (("capability", "group"),),
            "d" * 64, "e" * 64, "f" * 64, "0" * 64, (), (), case_census_digest(cases))
        for count, entry, continuation in ((92, True, True), (87, False, True),
                                            (86, False, False), (100, True, True)):
            with self.subTest(correct=count):
                assessment = evaluate_capabilities(
                    _solver(contexts, {case.case_id for case in cases[:count]}), cohort, PARENT)
                progress = assessment_progress(
                    assessment, active_group="group", cumulative_capabilities=("capability",),
                    capability_groups=(("capability", "group"),), carried_debt=())
                self.assertEqual((progress.entry_threshold_met, progress.continuation_threshold_met),
                                 (entry, continuation))
                self.assertEqual(progress.perfect_cumulative_mastery, count == 100)
                self.assertEqual(progress.mastery_debt, (("capability", 100 - count),))
                if count == 100:
                    prior_scope = assessment_progress(
                        assessment, active_group="group", cumulative_capabilities=("capability",),
                        capability_groups=(("capability", "group"),), carried_debt=(("capability", 7),), carried_debt_scope_sha256="1" * 64)
                    self.assertEqual(prior_scope.historical_debt, (("capability", 7),))
                    self.assertFalse(prior_scope.perfect_cumulative_mastery)
        small, small_context = _cases("small", "group", 1, "small")
        all_cases = cases + small
        all_contexts = {**contexts, **small_context}
        uneven = replace(cohort, cases=all_cases,
                         capability_groups=(("capability", "group"), ("small", "group")),
                         expected_case_digest=case_census_digest(all_cases))
        measured = evaluate_capabilities(_solver(all_contexts, {case.case_id for case in cases}),
                                          uneven, PARENT)
        progress = assessment_progress(measured, active_group="group",
                                      cumulative_capabilities=("capability", "small"),
                                      capability_groups=(("capability", "group"), ("small", "group")), carried_debt=())
        self.assertEqual((progress.mean_numerator, progress.mean_denominator), (1, 2))
        self.assertFalse(progress.entry_threshold_met)
        before = measured.digest()
        self.assertEqual(len(assessment_path_attribution(measured)), 101)
        self.assertEqual(measured.digest(), before)

    def test_ambiguous_group_and_unverified_generation_fail_closed(self):
        cohort, contexts = _cohort()
        replay, assessment = _replay(
            _solver(contexts, {case.case_id for case in cohort.cases}), cohort, PARENT, "1", 1)
        with self.assertRaises(ValueError):
            advance_epoch({"introduced_grade": "opaque-title-group"},
                          capability_groups={"opaque-title-group": ("misleading.prefix",),
                                  "other": ("misleading.prefix",)},
                          challenger_exam=assessment_exam(assessment, replay,
                                                           challenge_group="opaque-title-group"),
                          incumbent_exams={})
        with self.assertRaises(BilqisError):
            replace(replay, verify_generation=lambda generation, checkpoint: False).measure(cohort)
        with self.assertRaises(BilqisError):
            replace(replay, solver_contracts=("9" * 64,)).measure(cohort)

    def test_partial_active_group_is_unmeasured_while_missing_foreign_stays_debt(self):
        cohort, contexts = _cohort()
        assessment = evaluate_capabilities(
            _solver(contexts, {case.case_id for case in cohort.cases}), cohort, PARENT)
        for missing_group, measured in (("opaque-title-group", False), ("foreign", True)):
            progress = assessment_progress(
                assessment, active_group="opaque-title-group",
                cumulative_capabilities=("misleading.prefix", "missing"),
                capability_groups=(("misleading.prefix", "opaque-title-group"),
                                   ("missing", missing_group)),
                carried_debt=(("missing", 4),), carried_debt_scope_sha256=cohort.scope_sha256)
            self.assertEqual(progress.active_group_coverage_complete, measured)
            self.assertIs(progress.entry_threshold_met, True if measured else None)
            self.assertIs(progress.continuation_threshold_met, True if measured else None)
            self.assertIn(("missing", 4), progress.mastery_debt)
            self.assertFalse(progress.perfect_cumulative_mastery)

    def test_historical_pointer_provenance_and_battery_drift_are_rejected(self):
        cohort, contexts = _cohort()
        full = _solver(contexts, {case.case_id for case in cohort.cases})
        incumbent, initial = _replay(full, cohort, PARENT, "1", 1)
        challenger, _ = _replay(full, cohort, CANDIDATE, "2", 2)
        exam = assessment_exam(initial, incumbent, challenge_group="opaque-title-group")
        epoch, _, _ = advance_epoch({"introduced_grade": "opaque-title-group"},
                                    capability_groups={"opaque-title-group": ("misleading.prefix",)},
                                    challenger_exam=exam, incumbent_exams={})
        role = epoch["active_roles"]["misleading.prefix"]
        def match(offered_role=role, offered_incumbent=incumbent, resolver=lambda key: cohort):
            return fresh_title_match(
                offered_role, offered_incumbent, challenger, cohort,
                resolve_cohort=resolver, settled_matchups={}, challenge_group="opaque-title-group")
        for key, wrong in (("optimizer_step", 10), ("model_and_native_adamw", False),
                            ("filename", "bundles/foreign")):
            forged = deepcopy(role)
            forged["checkpoint"][key] = wrong
            with self.subTest(key=key), self.assertRaises((BilqisError, ValueError)):
                match(forged)
        missing = deepcopy(role)
        del missing["complete_solver_provenance"]
        with self.assertRaises(BilqisError):
            match(missing)
        with self.assertRaises(BilqisError):
            match(offered_incumbent=replace(incumbent, generation_digest="9" * 64))
        for field in ("source_sha256", "rubric_sha256", "scope_sha256"):
            with self.subTest(field=field), self.assertRaises(BilqisError):
                match(resolver=lambda key: replace(cohort, **{field: "9" * 64}))
        wrong_cases = (replace(cohort.cases[0], episode_id="different-episode"), *cohort.cases[1:])
        with self.assertRaises(BilqisError):
            match(resolver=lambda key: replace(cohort, cases=wrong_cases,
                                               expected_case_digest=case_census_digest(wrong_cases)))
        same_weight = replace(challenger, checkpoint=incumbent.checkpoint)
        with self.assertRaises(BilqisError):
            fresh_title_match(role, incumbent, same_weight, cohort,
                              resolve_cohort=lambda key: cohort, settled_matchups={},
                              challenge_group="opaque-title-group")

    def test_legacy_witness_bytes_and_original_battery_provenance_survive(self):
        cohort, contexts = _cohort()
        replay, assessment = _replay(
            _solver(contexts, {case.case_id for case in cohort.cases}), cohort, PARENT, "1", 1)
        exam = assessment_exam(assessment, replay, challenge_group="opaque-title-group")
        legacy = deepcopy(exam)
        del legacy["complete_solver_provenance"]
        witness = earning_witness(legacy, ("misleading.prefix",))
        # Literal receipt generated with the ae8c86a historical reader.
        self.assertEqual(witness["sha256"],
                         "267cd174426265bdd03b2e19d1ab61d88fc328742f793c905a250e93aa2fd089")
        epoch, _, _ = advance_epoch({"introduced_grade": "opaque-title-group"},
                                    capability_groups={"opaque-title-group": ("misleading.prefix",)},
                                    challenger_exam=exam, incumbent_exams={})
        role = epoch["active_roles"]["misleading.prefix"]
        history = deepcopy(role["qualification_witnesses"])
        segment = verified_battery(role)[0]
        empty = deepcopy(exam)
        empty["correct_questions"] = {"misleading.prefix": []}
        empty["scores"] = {"misleading.prefix": {"correct": 0, "total": 3}}
        survived = refresh_battery(role, gate_exam=empty, fresh_exam=empty,
                                   qualification_scope=("misleading.prefix",),
                                   battery_correct={segment["sha256"]: ["title:0"]})
        self.assertEqual([question["id"] for question in survived[0]["questions"]], ["title:0"])
        self.assertEqual(survived[0]["complete_solver_provenance"], replay.provenance())
        duplicate = refresh_battery(role, gate_exam=exam, fresh_exam=exam,
                                   qualification_scope=("misleading.prefix",),
                                   battery_correct={segment["sha256"]: ["title:0", "title:1", "title:2"]})
        self.assertEqual(duplicate, verified_battery(role))
        self.assertEqual(role["qualification_witnesses"], history)

    def test_fresh_battery_changes_winner_despite_challenger_current_maximum(self):
        old_cohort, old_contexts = _cohort()
        current_cases, current_contexts = _cases("misleading.prefix", "opaque-title-group", 3, "current")
        current = replace(old_cohort, cases=current_cases,
                          expected_case_digest=case_census_digest(current_cases))
        contexts = {**old_contexts, **current_contexts}
        old_ids = {case.case_id for case in old_cohort.cases}
        current_ids = {case.case_id for case in current.cases}
        incumbent, initial = _replay(_solver(contexts, old_ids), old_cohort, PARENT, "1", 1)
        challenger, candidate = _replay(_solver(contexts, current_ids), current, CANDIDATE, "2", 2)
        groups = {"opaque-title-group": ("misleading.prefix",)}
        initial_exam = assessment_exam(initial, incumbent, challenge_group="opaque-title-group")
        epoch, _, _ = advance_epoch({"introduced_grade": "opaque-title-group"}, capability_groups=groups,
                                    challenger_exam=initial_exam, incumbent_exams={})
        role = epoch["active_roles"]["misleading.prefix"]
        match = fresh_title_match(role, incumbent, challenger, current,
                                  resolve_cohort=lambda key: old_cohort, settled_matchups={},
                                  challenge_group="opaque-title-group")
        self.assertEqual(match["incumbent_current_exam"]["scores"]["misleading.prefix"]["correct"], 0)
        self.assertEqual(match["challenger_current_exam"]["scores"]["misleading.prefix"]["correct"], 3)
        incumbent_current = match["incumbent_current_exam"]
        candidate_exam = assessment_exam(candidate, challenger, challenge_group="opaque-title-group")
        defended, _, decisions = advance_epoch(
            epoch, capability_groups=groups, challenger_exam=candidate_exam,
            incumbent_exams={incumbent.checkpoint.sha256: incumbent_current},
            title_matches={"misleading.prefix": match})
        self.assertEqual(decisions[0]["decision"], "TITLE_DEFENDED")
        self.assertEqual(decisions[0]["incumbent_battery_correct"], 3)
        self.assertEqual(decisions[0]["challenger_battery_correct"], 0)
        better, improved = _replay(_solver(contexts, old_ids | current_ids), current, "c" * 64, "3", 3)
        match = fresh_title_match(defended["active_roles"]["misleading.prefix"], incumbent, better,
                                  current, resolve_cohort=lambda key: old_cohort,
                                  settled_matchups=defended["settled_matchups"],
                                  challenge_group="opaque-title-group")
        won, _, decisions = advance_epoch(
            defended, capability_groups=groups,
            challenger_exam=assessment_exam(improved, better, challenge_group="opaque-title-group"),
            incumbent_exams={incumbent.checkpoint.sha256: match["incumbent_current_exam"]},
            title_matches={"misleading.prefix": match})
        self.assertEqual(decisions[0]["decision"], "TITLE_WON")
        self.assertEqual(won["active_roles"]["misleading.prefix"]["checkpoint"]["sha256"], "3" * 64)

    def test_cache_gain_with_same_weights_has_own_zero_step_outcome(self):
        cohort, contexts = _cohort()
        def cached(goal, generation):
            binding = contexts[goal.goal_id]
            node = goal.expression_or_holes.nodes[0]
            filled = replace(goal, expression_or_holes=replace(
                goal.expression_or_holes, nodes=(replace(node, operator_id="ADD", candidate_operator_ids=()),)))
            composition = QualifiedComposition(
                filled, contract_digest(binding), generation,
                binding.frontier.rights_epoch,
                binding.frontier.correction_generation, "9" * 64)
            return SolveContext(binding, qualified_compositions=(composition,),
                                qualification_verifier=lambda item: True)
        parent = CompleteSolver(lambda goal, generation: SolveContext(contexts[goal.goal_id]),
                                SolveBudget(DAGBudget()))
        candidate = CompleteSolver(cached, SolveBudget(DAGBudget()))
        before, left = _replay(parent, cohort, PARENT, "1", 1)
        after, right = _replay(candidate, cohort, CANDIDATE, "1", 1)
        self.assertEqual(before.checkpoint, after.checkpoint)
        receipt = configuration_outcome(AssessmentPair(left, right))
        self.assertEqual((left.score("misleading.prefix"), right.score("misleading.prefix")),
                         ((0, 3), (3, 3)))
        self.assertEqual((receipt.net_correct_delta, receipt.optimizer_steps), (3, 0))
        self.assertTrue(all(result.route.value == "CACHED_COMPOSITION" for result in right.results))

    def test_explicit_source_group_overrides_misleading_capability_prefix(self):
        cohort, contexts = _cohort()
        replay, assessment = _replay(
            _solver(contexts, {case.case_id for case in cohort.cases}), cohort, PARENT, "1", 1)
        exam = assessment_exam(assessment, replay, challenge_group="opaque-title-group")
        epoch, changes, _ = advance_epoch(
            {"introduced_grade": "opaque-title-group"},
            capability_groups={"opaque-title-group": ("misleading.prefix",)},
            challenger_exam=exam, incumbent_exams={})
        self.assertEqual(changes, ("misleading.prefix",))
        self.assertEqual(epoch["active_roles"]["misleading.prefix"]["capability_group"],
                         "opaque-title-group")
        self.assertEqual(epoch["active_roles"]["misleading.prefix"]
                         ["complete_solver_provenance"]["generation_digest"], PARENT)

    def test_fresh_current_and_battery_title_tie_transfers_once(self):
        cohort, contexts = _cohort()
        full = _solver(contexts, {case.case_id for case in cohort.cases})
        incumbent, initial = _replay(full, cohort, PARENT, "1", 1)
        challenger, candidate = _replay(full, cohort, CANDIDATE, "2", 2)
        groups = {"opaque-title-group": ("misleading.prefix",)}
        initial_exam = assessment_exam(initial, incumbent, challenge_group="opaque-title-group")
        epoch, _, _ = advance_epoch({"introduced_grade": "opaque-title-group"},
                                    capability_groups=groups, challenger_exam=initial_exam, incumbent_exams={})
        role = epoch["active_roles"]["misleading.prefix"]
        before = repr(role)
        match = fresh_title_match(
            role, incumbent, challenger, cohort,
            resolve_cohort=lambda key: cohort, settled_matchups=epoch["settled_matchups"],
            challenge_group="opaque-title-group")
        candidate_exam = assessment_exam(candidate, challenger, challenge_group="opaque-title-group")
        updated, changes, decisions = advance_epoch(
            epoch, capability_groups=groups, challenger_exam=candidate_exam,
            incumbent_exams={incumbent.checkpoint.sha256: initial_exam},
            title_matches={"misleading.prefix": match})
        self.assertEqual(changes, ("misleading.prefix",))
        self.assertEqual(decisions[0]["decision"], "TITLE_WON")
        self.assertEqual(updated["active_roles"]["misleading.prefix"]["checkpoint"]["sha256"],
                         "2" * 64)
        self.assertEqual(repr(role), before)
        with self.assertRaises(BilqisError):
            fresh_title_match(
                updated["active_roles"]["misleading.prefix"], challenger, incumbent, cohort,
                resolve_cohort=lambda key: cohort, settled_matchups=updated["settled_matchups"],
                challenge_group="opaque-title-group")

    def test_progress_threshold_is_not_perfect_mastery_and_missing_debt_stays(self):
        cohort, contexts = _cohort()
        assessment = evaluate_capabilities(
            _solver(contexts, {case.case_id for case in cohort.cases[:2]}), cohort, PARENT)
        progress = assessment_progress(
            assessment, active_group="opaque-title-group",
            cumulative_capabilities=("misleading.prefix", "unmeasured.capability"),
            capability_groups=(("misleading.prefix", "opaque-title-group"),
                               ("unmeasured.capability", "foreign")), carried_debt=(("unmeasured.capability", 4),),
            carried_debt_scope_sha256=cohort.scope_sha256)
        self.assertFalse(progress.perfect_cumulative_mastery)
        self.assertEqual(progress.unmeasured_capabilities, ("unmeasured.capability",))
        self.assertIn(("unmeasured.capability", 4), progress.mastery_debt)
        self.assertFalse(hasattr(progress, "promoted"))
