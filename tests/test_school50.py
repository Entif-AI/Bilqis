"""End-user behavior: autonomous school advances ONE trained student."""
from __future__ import annotations

import json
from pathlib import Path
import random
import signal
import tempfile
import unittest
from unittest.mock import patch
import torch

from bilqis_active import load_active
from bilqis_school import arithmetic, engine, grades, lessons
from bilqis_development.continuation import expand
from bilqis_development.registry import extended_catalog
from bilqis_micro.run import optimizer_receipt
from bilqis_ref.model import state_hash

HAS_LOCAL_STUDENT=(Path.home()/"Code"/"bilqis-learner-custody"/"active-u7f-13848.pt").is_file()


class SkillTree(unittest.TestCase):
    def test_fifty_grade_contract_and_spiral_concepts(self):
        tree=grades.skill_tree()
        self.assertEqual(len(tree),50)
        self.assertEqual([g.domain for g in tree].count("logic_math"),22)
        self.assertEqual([g.domain for g in tree].count("ithkuil_grammar"),13)
        self.assertEqual([g.domain for g in tree].count("ithkuil_lexicon"),15)
        self.assertEqual([g.id for g in tree],[f"G{i:02d}" for i in range(1,51)])
        self.assertEqual([g.id for g in tree if g.ready],
                         [f"G{i:02d}" for i in range(1,23)])
        self.assertEqual(tree[22].compiler,None)
        for g in tree:
            for ref in g.prerequisites+g.rehearsal:
                self.assertLess(int(ref[1:]),g.number)
            for ref in g.foreshadows:
                self.assertLessEqual(int(ref[1:]),g.number+2)

    def test_same_authoritative_manifest_is_checked_in(self):
        expected=grades.manifest()
        path=engine.ROOT/"docs/development/SKILL_TREE_50.json"
        self.assertEqual(json.loads(path.read_text()),expected)


class ArithmeticSemantics(unittest.TestCase):
    def test_math_generator_produces_true_and_false_with_two_oracles(self):
        for grade in range(19,23):
            for truth in (True,False):
                rng=random.Random(grade*100 + int(truth))
                for i in range(40):
                    record=arithmetic.lesson(grade,rng,correct=truth,depth=2)
                    self.assertEqual(record["gold"],"TRUE" if truth else "FALSE")
                    self.assertTrue(arithmetic.verify(record["input"]["expression"]))

    @unittest.skipUnless(HAS_LOCAL_STUDENT,
                         "Neural checkpoint integration needs real local custodied U7F weights, not a public-Git fake.")
    def test_full_math_abi_expands_trained_student_without_resetting_weights(self):
        model,optimizer,payload,_=load_active()
        parent_sha=state_hash(model)
        old=optimizer_receipt(optimizer)
        graph=arithmetic.extend_graph(payload["graph"])
        receipt=expand(model,optimizer,payload["graph"],graph)
        self.assertEqual((receipt["old_vocab"],receipt["new_vocab"]),(113,222))
        self.assertTrue(receipt["trained_weights_preserved"])
        self.assertTrue(receipt["old_moments_preserved"])
        self.assertTrue(receipt["new_moments_zero"])
        self.assertEqual(old["steps"],optimizer_receipt(optimizer)["steps"])
        self.assertNotEqual(parent_sha,state_hash(model)) # new rows; old still exact


class AdaptiveTeacher(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.library=lessons.TeacherLibrary()
        # Oracle-backed lesson/ABI tests can run in public CI without the
        # learned student's private checkpoint. Never fabricate a replacement
        # student's weights merely to satisfy a compiler test.
        cls.graph=arithmetic.extend_graph(extended_catalog())

    def test_all_twenty_two_early_grades_compile_actual_gold(self):
        policy={"old":12,"preview":2,"depth":2,"contrast":.5,"lr":.00013,"distill":.35}
        for grade in range(1,23):
            batch,counts=lessons.compose_batch(self.library,grade,policy,self.graph,
                                                random.Random(grade))
            self.assertEqual(len(batch),32)
            self.assertGreater(counts["current"],0)
            self.assertEqual(sum(counts.values()),32)
        self.assertFalse(self.library.ready(23))
        with self.assertRaises(ValueError):
            self.library.one(23,random.Random(1))

    def test_paired_lineage_current_not_silently_dropped(self):
        policy={"old":12,"preview":2,"depth":2,"contrast":1.,"lr":.00013,"distill":.15}
        batch,counts=lessons.compose_batch(self.library,17,policy,self.graph,
                                            random.Random(4))
        self.assertEqual(counts["current"] % 2,0)
        for i in range(0,counts["current"],2):
            self.assertTrue(lessons.validate_pair(*batch[i:i+2]))
        self.assertTrue(any(r["lesson_relation"]=="CURRENT_STATE"
                            for r in batch[:counts["current"]]) or
                        any(r["lesson_relation"]=="DEPENDENCY"
                            for r in batch[:counts["current"]]))

    def test_policy_mutations_have_one_changed_predefined_knob_and_memory(self):
        teacher=engine._teacher()
        old={k:dict(v) for k,v in teacher["strategies"].items()}
        key=next(iter(teacher["strategies"]))
        engine.observe(teacher,17,key,.33)
        result=engine.mutate(teacher,random.Random(123))
        self.assertIsNotNone(result)
        mutation=teacher["strategies"][result]
        difference=min(sum(mutation[k]!=original[k] for k in engine.KNOBS)
                       for original in old.values())
        self.assertEqual(difference,1)
        self.assertTrue(all(mutation[k] in engine.KNOBS[k] for k in mutation))
        self.assertEqual(teacher["global_stats"][key]["trials"],1)
        self.assertEqual(teacher["grade_stats"]["17"][key]["trials"],1)

    def test_strategy_budget_allows_long_running_teacher_search(self):
        self.assertGreaterEqual(engine.MAX_STRATEGIES,512)

    def test_graceful_interrupt_first_requests_second_aborts(self):
        state={"requested":False}
        handler=engine._graceful_interrupt_handler(state)
        handler(signal.SIGINT,None)
        self.assertTrue(state["requested"])
        with self.assertRaises(KeyboardInterrupt):
            handler(signal.SIGINT,None)

    def test_pass_report_tracks_previous_start_and_mastery_shape(self):
        baseline={grade:.50 for grade in engine.REPORT_GRADE_IDS}
        previous={grade:.60 for grade in engine.REPORT_GRADE_IDS}
        scores={grade:.75 for grade in engine.REPORT_GRADE_IDS}
        scores["G09"]=1.0
        scores["G11"]=.25
        report=engine._pass_report(4,scores,baseline,previous)
        self.assertAlmostEqual(report["mean_vs_previous"],3.05/22)
        self.assertAlmostEqual(report["median_vs_previous"],.15)
        self.assertAlmostEqual(report["median_vs_school_start"],.25)
        self.assertEqual(report["perfect_grades"],1)
        self.assertEqual(report["lowest_grade"],"G11")
        self.assertEqual(report["highest_grade"],"G09")
        self.assertIn("mean probe",engine._pass_summary_line(report))

    def test_call_grade_comparison_reports_start_end_and_delta_for_every_grade(self):
        start={grade:.50 for grade in engine.REPORT_GRADE_IDS}
        end=dict(start)
        end["G01"]=.75
        end["G02"]=.25
        comparison=engine._call_grade_comparison(start,end)
        self.assertEqual(set(comparison["grades"]),set(engine.REPORT_GRADE_IDS))
        self.assertEqual(
            comparison["grades"]["G01"],
            {"start_percent":50.0,"end_percent":75.0,"delta_pp":25.0})
        self.assertEqual(
            comparison["grades"]["G02"],
            {"start_percent":50.0,"end_percent":25.0,"delta_pp":-25.0})
        self.assertEqual(comparison["improved_grades"],1)
        self.assertEqual(comparison["regressed_grades"],1)
        self.assertEqual(comparison["unchanged_grades"],20)
        self.assertEqual(comparison["mean_start_percent"],50.0)
        self.assertEqual(comparison["mean_end_percent"],50.0)
        self.assertEqual(comparison["mean_delta_pp"],0.0)

    def test_pass_report_summary_preserves_human_report_metrics(self):
        baseline={grade:.50 for grade in engine.REPORT_GRADE_IDS}
        previous={grade:.60 for grade in engine.REPORT_GRADE_IDS}
        scores={grade:.75 for grade in engine.REPORT_GRADE_IDS}
        report=engine._pass_report(4,scores,baseline,previous,optimizer_step=123)
        report["disposition"]="ACCEPTED_NEW_CHAMPION"
        report["vs_champion_pass"]={
            "pass":3,"mean_delta":.025,"median_delta":.0,
            "regressed":False,"improved_grades":2,"regressed_grades":1,
            "unchanged_grades":19,
        }
        report["patience_reset"]=True
        report["patience_reset_reason"]="NEW_HOLISTIC_CHAMPION"
        summary=engine._pass_report_summary(report)
        self.assertEqual(summary["pass"],4)
        self.assertEqual(summary["optimizer_step"],123)
        self.assertEqual(summary["disposition"],"ACCEPTED_NEW_CHAMPION")
        self.assertEqual(summary["mean_probe_percent"],75.0)
        self.assertEqual(summary["median_probe_percent"],75.0)
        self.assertEqual(summary["mean_vs_previous_pp"],15.0)
        self.assertEqual(summary["median_vs_previous_pp"],15.0)
        self.assertEqual(summary["mean_vs_school_start_pp"],25.0)
        self.assertEqual(summary["grades_at_or_above_90"],0)
        self.assertEqual(summary["perfect_grades"],0)
        self.assertEqual(summary["vs_champion_pass"],3)
        self.assertEqual(summary["mean_vs_champion_pp"],2.5)
        self.assertTrue(summary["patience_reset"])
        self.assertEqual(
            summary["patience_reset_reason"],"NEW_HOLISTIC_CHAMPION")

    def test_pass_regression_guard_catches_mean_loss_even_with_flat_median(self):
        champion={grade:.75 for grade in engine.REPORT_GRADE_IDS}
        current=dict(champion)
        for grade in engine.REPORT_GRADE_IDS[:7]:
            current[grade]-=.05
        for grade in engine.REPORT_GRADE_IDS[7:11]:
            current[grade]+=.025
        result=engine._material_pass_regression(current,champion,.01)
        self.assertTrue(result["regressed"])
        self.assertEqual(result["median_delta"],0.0)
        self.assertEqual(result["regressed_grades"],7)
        tiny={grade:value-.005 for grade,value in champion.items()}
        result=engine._material_pass_regression(tiny,champion,.01)
        self.assertFalse(result["regressed"])

    def test_retry_pick_excludes_already_attempted_strategy(self):
        teacher=engine._teacher()
        rng=random.Random(77)
        first,_=engine.pick(teacher,1,rng)
        second,_=engine.pick(teacher,1,rng,exclude={first})
        self.assertNotEqual(first,second)

    def test_grade_champion_only_moves_on_true_personal_best(self):
        state={"grade_champions":{
            "G03":{
                "score":.75,"checkpoint":"old.pt",
                "checkpoint_sha256":"old","optimizer_step":10,
                "source_pass":2,"holistic_mean":.70,
            }
        }}
        tied=engine._maybe_promote_grade_champion(
            state,"G03",.75,checkpoint="tie.pt",
            checkpoint_sha256="tie",optimizer_step=20,source_pass=3,
            holistic_mean=.80)
        self.assertFalse(tied["new_champion"])
        self.assertEqual(state["grade_champions"]["G03"]["checkpoint"],"old.pt")
        better=engine._maybe_promote_grade_champion(
            state,"G03",.7916666667,checkpoint="new.pt",
            checkpoint_sha256="new",optimizer_step=30,source_pass=4,
            holistic_mean=.72)
        self.assertTrue(better["new_champion"])
        self.assertAlmostEqual(better["vs_prior_best"],.0416666667)
        self.assertEqual(state["grade_champions"]["G03"]["checkpoint"],"new.pt")

    def test_model_soup_weight_average_is_grade_weighted(self):
        first=torch.nn.Linear(2,1,bias=False)
        second=torch.nn.Linear(2,1,bias=False)
        with torch.no_grad():
            first.weight.fill_(1.0)
            second.weight.fill_(4.0)
        averaged=engine._average_model_state_dicts(
            [first,second],[2,1])
        self.assertTrue(torch.allclose(
            averaged["weight"],torch.full((1,2),2.0)))

    def test_consolidation_confirmation_requires_net_gain_and_limits_damage(self):
        baseline={grade:.75 for grade in engine.REPORT_GRADE_IDS}
        better=dict(baseline)
        better["G01"]+=1/24
        with patch.object(
                engine,"_probe_all_grades",
                side_effect=[baseline,better]):
            result=engine._consolidation_confirmation(
                None,None,None,None,device="cpu")
        self.assertEqual(result["decision"],"PROMOTE")
        self.assertEqual(result["reason"],"CONSOLIDATION_FULL_PROBE_GAIN")
        damaged=dict(baseline)
        damaged["G01"]+=3/24
        damaged["G18"]-=2/24
        with patch.object(
                engine,"_probe_all_grades",
                side_effect=[baseline,damaged]):
            result=engine._consolidation_confirmation(
                None,None,None,None,device="cpu")
        self.assertEqual(result["decision"],"REJECT")
        self.assertEqual(
            result["reason"],"CONSOLIDATION_FULL_PROBE_RETENTION_LOSS")

    def test_consolidation_requires_candidate_gate(self):
        with tempfile.TemporaryDirectory() as temp:
            with self.assertRaisesRegex(
                    ValueError,"INVALID_BOUNDED_TRAINING_REQUEST"):
                engine.run(
                    Path(temp)/"school",max_updates=1,max_minutes=1,
                    consolidate_grade_champions=True)

    def test_candidate_gate_uses_continuous_sentinel_for_uncertain_updates(self):
        self.assertEqual(
            engine._candidate_gate_decision(-.10)["reason"],
            "CLEAR_REWARD_LOSS")
        self.assertEqual(
            engine._candidate_gate_decision(.10)["decision"],
            "MEASURE")
        before={
            "accuracy":.75,
            "cross_entropy":.90,
            "correct_probability":.60,
            "margin":.40,
        }
        better={
            "accuracy":.75,
            "cross_entropy":.88,
            "correct_probability":.61,
            "margin":.42,
        }
        worse={
            "accuracy":.75,
            "cross_entropy":.93,
            "correct_probability":.58,
            "margin":.37,
        }
        ambiguous=engine._candidate_gate_decision(0.0,before,better)
        self.assertEqual(ambiguous["decision"],"PROMOTE")
        self.assertEqual(ambiguous["reason"],"SENTINEL_BETTER")
        veto=engine._candidate_gate_decision(.10,before,worse)
        self.assertEqual(veto["decision"],"REJECT")
        self.assertEqual(veto["reason"],"SENTINEL_VETOED_LOCAL_WIN")
        safe=engine._candidate_gate_decision(.10,before,before)
        self.assertEqual(safe["decision"],"PROMOTE")
        self.assertEqual(safe["reason"],"CLEAR_REWARD_WIN_SENTINEL_SAFE")
        self.assertEqual(
            engine._candidate_teacher_credit(
                .10,{"decision":"REJECT","reason":"SENTINEL_VETOED_LOCAL_WIN"}),
            -.05)
        self.assertEqual(
            engine._candidate_teacher_credit(
                0.0,{"decision":"REJECT","reason":"SENTINEL_NO_DEMONSTRATED_GAIN"}),
            0.0)
        self.assertEqual(
            engine._candidate_teacher_credit(
                0.0,{"decision":"PROMOTE","reason":"SENTINEL_BETTER"}),
            .025)

    def test_checkpoint_retention_keeps_runtime_and_recovery_anchors(self):
        with tempfile.TemporaryDirectory() as temp:
            out=Path(temp)
            names=(
                "student-100-start.pt",
                "student-120-grow-from.pt",
                "student-120-grow-to.pt",
                "student-200-pass.pt",
                "student-250-junk.pt",
                "student-300-pass.pt",
                "student-325-grade.pt",
                "student-350-junk.pt",
                "student-400-accepted.pt",
                "student-450-recent.pt",
                "student-500-live.pt",
            )
            for index,name in enumerate(names):
                (out/name).write_bytes(bytes([index])*128)
            state={
                "checkpoint":"student-500-live.pt",
                "school_start_checkpoint":"student-100-start.pt",
                "accepted_pass":{"checkpoint":"student-400-accepted.pt"},
                "champion_pass":{"checkpoint":"student-300-pass.pt"},
                "grade_champions":{
                    "G11":{"checkpoint":"student-325-grade.pt"},
                },
                "architecture_history":[{
                    "from":"student-120-grow-from.pt",
                    "to":"student-120-grow-to.pt",
                }],
                "grade_ledger":[
                    {"grade":"G22","optimizer_step":200},
                    {"grade":"G22","optimizer_step":300},
                    {"grade":"G22","optimizer_step":400},
                ],
                "optimizer_step":500,
            }
            plan=engine._checkpoint_retention_plan(
                out,state,keep_recent=2,keep_pass=1)
            kept={path.name for path in plan["keep"]}
            self.assertTrue({
                "student-100-start.pt",
                "student-120-grow-from.pt",
                "student-120-grow-to.pt",
                "student-300-pass.pt",
                "student-325-grade.pt",
                "student-400-accepted.pt",
                "student-450-recent.pt",
                "student-500-live.pt",
            }.issubset(kept))
            self.assertNotIn("student-250-junk.pt",kept)
            self.assertNotIn("student-350-junk.pt",kept)
            retention=engine._prune_checkpoints(
                out,state,keep_recent=2,keep_pass=1)
            self.assertEqual(retention["last_pruned_count"],3)
            self.assertEqual(retention["retained_count"],8)
            self.assertTrue((out/"student-500-live.pt").exists())
            self.assertTrue((out/"student-400-accepted.pt").exists())
            self.assertTrue((out/"student-300-pass.pt").exists())
            self.assertTrue((out/"student-325-grade.pt").exists())
            self.assertTrue((out/"student-100-start.pt").exists())

    def test_rejected_pass_metrics_are_not_counted_as_live_lineage(self):
        events=[
            {"pass":1,"grade":"G01","updates":64,
             "repeat_delta":.10,"immediate_delta":.05,"old_mean_delta":.01},
            {"pass":2,"grade":"G01","updates":64,
             "repeat_delta":-.20,"immediate_delta":-.10,"old_mean_delta":-.03},
            {"pass":3,"grade":"G01","updates":64,
             "repeat_delta":.05,"immediate_delta":.02,"old_mean_delta":0.0},
        ]
        lineage=engine._lineage_metric_events(events,{2})
        live=engine._metric_summary(lineage)
        attempted=engine._metric_summary(events)
        rejected=engine._metric_summary(
            [event for event in events if event["pass"]==2])
        self.assertEqual(live["grade_visits"],2)
        self.assertEqual(live["repeat_improved"],2)
        self.assertEqual(live["repeat_regressed"],0)
        self.assertAlmostEqual(live["mean_repeat_delta"],.075)
        self.assertEqual(attempted["repeat_regressed"],1)
        self.assertAlmostEqual(attempted["mean_repeat_delta"],-.05/3)
        self.assertEqual(rejected["grade_visits"],1)
        self.assertAlmostEqual(rejected["mean_repeat_delta"],-.20)

    def test_human_progress_line_and_patience_gate_are_readable(self):
        progress={
            "elapsed_minutes":12.5,"pass":3,"grade":"G06","step":16984,
            "accuracy_before":.625,"accuracy_after":.708333333,
            "immediate_delta":.083333333,"repeat_delta":.041666667,
            "rolling_repeat_delta":.015625,"progress_window":8,
            "old_mean_delta":-.0694444,"reward":.1667,"teacher_strategies":20,
            "teacher_mutations":16,"minutes_since_measurable_progress":22.0,
            "patience_minutes":60.0,
        }
        line=engine._progress_line(progress)
        self.assertIn("G06 step 16984",line)
        self.assertIn("62.5%->70.8%",line)
        self.assertIn("vs prior +4.2pp",line)
        self.assertIn("rolling8 +1.6pp",line)
        self.assertIn("old avg -6.9pp",line)
        self.assertIn(f"teacher 20/{engine.MAX_STRATEGIES} strategies/16 mutations",line)
        self.assertIn("no-gain 22.0/60.0m",line)
        self.assertFalse(engine._stagnation_stop(
            elapsed_seconds=4000,seconds_since_progress=4000,
            repeat_comparisons=7,progress_window=8,patience_minutes=60))
        self.assertTrue(engine._stagnation_stop(
            elapsed_seconds=4000,seconds_since_progress=4000,
            repeat_comparisons=8,progress_window=8,patience_minutes=60))

    def test_new_holistic_champion_can_reset_patience_clock(self):
        self.assertTrue(engine._qualifying_holistic_gain(.769,.756,.01))
        self.assertFalse(engine._qualifying_holistic_gain(.759,.756,.01))
        self.assertFalse(engine._qualifying_holistic_gain(.756,.756,.01))

    @unittest.skipUnless(HAS_LOCAL_STUDENT,
                         "End-to-end continuation needs real local custodied U7F checkpoint.")
    def test_resume_inherits_optimizer_even_when_score_declines(self):
        with tempfile.TemporaryDirectory() as temp:
            out=Path(temp)/"school"
            with self.assertRaisesRegex(ValueError,"FULL_50_NOT_COMPILED"):
                engine.run(out,strict_full50=True,max_updates=1,max_minutes=1)
            self.assertFalse(out.exists())
            first=engine.run(out,max_updates=2,max_minutes=2,block=2)
            self.assertEqual(first["live_optimizer_step"],13850)
            self.assertEqual(first["next_grade"],2)
            self.assertEqual(
                set(first["grade_start_end_this_call"]["grades"]),
                set(engine.REPORT_GRADE_IDS))
            self.assertEqual(first["pass_summaries_this_call"],[])
            initialized=engine._read(out/engine.STATE)
            self.assertEqual(initialized["accepted_pass"]["pass"],0)
            self.assertEqual(set(initialized["school_start_probe_scores"]),
                             set(engine.REPORT_GRADE_IDS))
            second=engine.run(out,max_updates=2,max_minutes=2,block=2)
            self.assertEqual(second["live_optimizer_step"],13852)
            self.assertEqual(second["next_grade"],3)
            self.assertEqual(second["completed_grades"],2)
            limited=engine.run(out,max_updates=20,max_minutes=2,block=2,
                               max_grade_visits=1)
            self.assertEqual(limited["status"],"PAUSED_AT_REQUESTED_GRADE_VISIT_LIMIT")
            self.assertEqual(limited["grade_visits_this_call"],1)
            self.assertEqual(limited["live_optimizer_step"],13854)
            self.assertEqual(engine._read(out/engine.STATE)["teacher"]["events"],3)
            checks=iter((False,False,True))
            interrupted=engine.run(
                out,max_updates=20,max_minutes=2,block=2,
                stop_requested=lambda: next(checks))
            self.assertEqual(interrupted["status"],"STOPPED_BY_GRACEFUL_INTERRUPT")
            self.assertEqual(interrupted["grade_visits_this_call"],1)
            self.assertEqual(interrupted["live_optimizer_step"],13856)
            self.assertEqual(engine._read(out/engine.STATE)["teacher"]["events"],4)
            state=engine._read(out/engine.STATE)
            teacher_events=state["teacher"]["events"]
            restored,restored_optimizer,_=engine._load_accepted_student(
                out,state,state["accepted_pass"],"cpu")
            self.assertEqual(optimizer_receipt(restored_optimizer)["steps"],[13848])
            self.assertEqual(state["teacher"]["events"],teacher_events)
            self.assertEqual(state_hash(restored),
                             state["model_sha256"])
            self.assertTrue((out/engine._read(out/engine.STATE)["checkpoint"]).exists())

    @unittest.skipUnless(HAS_LOCAL_STUDENT,
                         "Candidate promotion needs real local student/AdamW state.")
    def test_candidate_rejections_preserve_student_but_teacher_learns(self):
        with tempfile.TemporaryDirectory() as temp:
            out=Path(temp)/"school"
            with patch.object(
                    engine,"_candidate_gate_decision",
                    return_value={"decision":"REJECT","reason":"TEST_REJECT"}):
                result=engine.run(
                    out,max_updates=4,max_minutes=2,block=2,
                    max_grade_visits=1,candidate_grade_gate=True,
                    candidate_max_attempts=2)
            state=engine._read(out/engine.STATE)
            self.assertEqual(result["live_optimizer_step"],13848)
            self.assertEqual(result["completed_this_call"],0)
            self.assertEqual(result["training_updates_attempted_this_call"],4)
            self.assertEqual(result["candidate_rejections_this_call"],2)
            self.assertEqual(result["candidate_no_update_grades_this_call"],1)
            self.assertEqual(state["completed_updates"],0)
            self.assertEqual(state["attempted_updates"],4)
            self.assertEqual(state["teacher"]["events"],2)
            self.assertEqual(len(state["candidate_ledger"]),2)
            self.assertFalse(state["grade_ledger"][-1]["student_update_applied"])
            self.assertEqual(state["next_grade"],2)
            _,optimizer,_=engine._validate(out/state["checkpoint"],state)
            self.assertEqual(optimizer_receipt(optimizer)["steps"],[13848])

    @unittest.skipUnless(HAS_LOCAL_STUDENT,
                         "Candidate promotion needs real local student/AdamW state.")
    def test_candidate_promotion_advances_student_once(self):
        with tempfile.TemporaryDirectory() as temp:
            out=Path(temp)/"school"
            with patch.object(
                    engine,"_candidate_gate_decision",
                    return_value={"decision":"PROMOTE","reason":"TEST_PROMOTE"}):
                result=engine.run(
                    out,max_updates=2,max_minutes=2,block=2,
                    max_grade_visits=1,candidate_grade_gate=True,
                    candidate_max_attempts=2)
            state=engine._read(out/engine.STATE)
            self.assertEqual(result["live_optimizer_step"],13850)
            self.assertEqual(result["completed_this_call"],2)
            self.assertEqual(result["training_updates_attempted_this_call"],2)
            self.assertEqual(result["candidate_promotions_this_call"],1)
            self.assertEqual(result["candidate_rejections_this_call"],0)
            self.assertTrue(state["grade_ledger"][-1]["student_update_applied"])
            self.assertEqual(state["completed_updates"],2)
            self.assertEqual(state["attempted_updates"],2)

    @unittest.skipUnless(HAS_LOCAL_STUDENT,
                         "Soup consolidation needs real local student/AdamW state.")
    def test_soup_consolidation_distills_without_replacing_optimizer_lineage(self):
        with tempfile.TemporaryDirectory() as temp:
            out=Path(temp)/"school"
            confirmation={
                "decision":"PROMOTE",
                "reason":"CONSOLIDATION_FULL_PROBE_GAIN",
                "mean_delta":1/528,
                "median_delta":0.0,
                "improved_grades":1,
                "regressed_grades":0,
                "unchanged_grades":21,
                "worst_grade":"G01",
                "worst_grade_delta":0.0,
                "deltas":{grade:0.0 for grade in engine.REPORT_GRADE_IDS},
                "before_scores":{grade:.5 for grade in engine.REPORT_GRADE_IDS},
                "after_scores":{grade:.5 for grade in engine.REPORT_GRADE_IDS},
            }
            with (
                patch.object(
                    engine,"_candidate_gate_decision",
                    return_value={"decision":"PROMOTE","reason":"TEST_PROMOTE"}),
                patch.object(
                    engine,"_consolidation_confirmation",
                    return_value=confirmation),
            ):
                result=engine.run(
                    out,max_updates=2,max_minutes=3,block=2,
                    max_grade_visits=1,candidate_grade_gate=True,
                    candidate_max_attempts=1,
                    consolidate_grade_champions=True,
                    consolidation_weight=.15)
            state=engine._read(out/engine.STATE)
            attempt=state["candidate_ledger"][-1]
            self.assertTrue(result["consolidation_enabled"])
            self.assertIsNotNone(result["consolidation_teacher_digest"])
            self.assertEqual(result["live_optimizer_step"],13850)
            self.assertEqual(state["completed_updates"],2)
            self.assertEqual(state["attempted_updates"],2)
            self.assertEqual(len(state["consolidation_sessions"]),1)
            self.assertEqual(
                attempt["consolidation_teacher_digest"],
                result["consolidation_teacher_digest"])
            self.assertGreaterEqual(attempt["consensus_distill_mean"],0.0)
            self.assertGreaterEqual(attempt["consensus_coverage_mean"],0.0)
            self.assertLessEqual(attempt["consensus_coverage_mean"],1.0)
            _,optimizer,_=engine._validate(out/state["checkpoint"],state)
            self.assertEqual(optimizer_receipt(optimizer)["steps"],[13850])


if __name__=="__main__":
    unittest.main()
