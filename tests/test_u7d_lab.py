"""Focused U7D admission and action-level behavior tests."""
from collections import Counter
import unittest
from pathlib import Path

from bilqis_u7d import laboratory_v2 as lab
from bilqis_u7d import run_v2 as runner


class U7DLaboratoryTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.manifest, cls.episodes = runner.verify()

    def test_worlds_and_source_oracles_frozen_before_kev(self):
        self.assertTrue(lab.validate_episodes(self.episodes))
        self.assertEqual(Counter(e["kind"] for e in self.episodes),
                         {"nested-evidence":8,"lineage":8,"current-vs-history":8})
        self.assertEqual(len({e["semantic_fingerprint"] for e in self.episodes}),24)
        self.assertEqual(len({e["target"] for e in self.episodes}),8)
        self.assertTrue(all(len(e["dossiers"])==8 for e in self.episodes))
        if (runner.RUN/"qualification.json").exists():
            self.assertEqual(runner.read(runner.RUN/"qualification.json")["student_optimizer_updates"],0)

    def test_wrong_report_is_legal_and_fails_without_oracle_hint(self):
        e=self.episodes[0]
        wrong=next(x for x in lab.DOSSIERS if x!=e["target"])
        s=lab.start(e)
        self.assertIn("Inspect "+wrong,[o["candidate_id"] for o in lab.legal(e,s)])
        s,_=lab.apply(e,s,"Inspect "+wrong)
        self.assertIn("Report "+wrong,[o["candidate_id"] for o in lab.legal(e,s)])
        s,_=lab.apply(e,s,"Report "+wrong)
        self.assertFalse(s["success"])
        self.assertTrue(s["done"])

    def test_one_factor_intervention_mutates_world_and_preserves_counts(self):
        for e in self.episodes:
            s=lab.start(e)
            target=e["target"]
            s,_=lab.apply(e,s,"Inspect "+target)
            before_version=s["world_versions"][target]
            before=lab.oracle(e["dossiers"][target])[0]
            s,feedback=lab.apply(e,s,"Test "+target)
            self.assertEqual(before_version,"original")
            self.assertEqual(s["world_versions"][target],"intervened")
            self.assertEqual(lab.oracle(e["dossiers"][target],True)[0],e["dossiers"][target]["intervened"])
            self.assertNotEqual(before,e["dossiers"][target]["intervened"])
            self.assertIn("Independent oracles agree",feedback)
            s,_=lab.apply(e,s,"Report "+target)
            self.assertTrue(s["success"])

    def test_native_visible_options_are_english_and_under_bounded_menu(self):
        for e in self.episodes:
            s=lab.start(e)
            for _ in range(8):
                visible=lab.prose(e,s)
                self.assertNotIn('"kind"',visible)
                self.assertNotIn('"gold"',visible)
                opts=lab.legal(e,s)
                self.assertLessEqual(len(opts),16)
                self.assertTrue(all(c["candidate_id"].startswith(("Inspect ","Test ","Report ","End "))
                                    for c in opts))
                available=[c for c in opts if c["candidate_id"].startswith("Inspect ")]
                if not available:break
                s,_=lab.apply(e,s,available[0]["candidate_id"])

    def test_controls_match_budget_and_cannot_access_gold(self):
        controls=runner.read(runner.RUN/"matched-controls.json")
        self.assertEqual(set(controls),{"random","heuristic"})
        for actor,data in controls.items():
            self.assertEqual(len(data["episodes"]),24)
            self.assertTrue(all(0<=r["actions_used"]<=lab.MAX_STEPS for r in data["episodes"]))
            self.assertEqual(sum(x["success"] for x in data["episodes"]),data["successes"])

    def test_novel_finals_never_enter_adaptive_dev(self):
        final=runner.read(runner.RUN/"sealed-final.json.gz")
        self.assertEqual(len(final),8)
        self.assertFalse({x["semantic_fingerprint"] for x in self.episodes}&
                         {x["semantic_fingerprint"] for x in final})


if __name__=="__main__":unittest.main()
