"""End-user behavior: autonomous school advances ONE trained student."""
from __future__ import annotations

import json
from pathlib import Path
import random
import tempfile
import unittest

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

    def test_human_progress_line_and_patience_gate_are_readable(self):
        progress={
            "elapsed_minutes":12.5,"pass":3,"grade":"G06","step":16984,
            "accuracy_before":.625,"accuracy_after":.708333333,
            "immediate_delta":.083333333,"repeat_delta":.041666667,
            "rolling_repeat_delta":.015625,"progress_window":8,
            "old_delta":0.0,"reward":.1667,"teacher_strategies":20,
            "teacher_mutations":16,"minutes_since_measurable_progress":22.0,
            "patience_minutes":60.0,
        }
        line=engine._progress_line(progress)
        self.assertIn("G06 step 16984",line)
        self.assertIn("62.5%->70.8%",line)
        self.assertIn("vs prior +4.2pp",line)
        self.assertIn("rolling8 +1.6pp",line)
        self.assertIn("no-gain 22.0/60.0m",line)
        self.assertFalse(engine._stagnation_stop(
            elapsed_seconds=4000,seconds_since_progress=4000,
            repeat_comparisons=7,progress_window=8,patience_minutes=60))
        self.assertTrue(engine._stagnation_stop(
            elapsed_seconds=4000,seconds_since_progress=4000,
            repeat_comparisons=8,progress_window=8,patience_minutes=60))

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
            self.assertTrue((out/engine._read(out/engine.STATE)["checkpoint"]).exists())


if __name__=="__main__":
    unittest.main()
