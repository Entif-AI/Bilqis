import unittest,tempfile,json
from pathlib import Path
from bilqis_ref.sealing import prepare,verify_opening
from bilqis_ref.statistics import paired,restricted_exposure
class SealTests(unittest.TestCase):
    def test_commitment_tamper(self):
        with tempfile.TemporaryDirectory() as d:
            p=Path(d)/"seal";m=prepare(p,191,4,"SEALED",["cycle"]);self.assertEqual(m["case_count"],20);self.assertTrue(verify_opening(p))
            self.assertNotIn('"label"',(p/"evaluator-input/cases.jsonl").read_text())
            with (p/"custodian-private/gold.jsonl").open("a") as f:f.write(" ")
            with self.assertRaises(ValueError):verify_opening(p)
    def test_seed_unit_not_case_unit(self):
        r=paired([.2,.3,.4,.5],[.1,.2,.3,.4]);self.assertEqual(r["paired_seeds"],4);self.assertAlmostEqual(r["mean_difference"],.1);self.assertEqual(r["exact_two_sided_signflip_p"],.125)
    def test_failure_cost_not_dropped(self):
        r=restricted_exposure([20,None],100);self.assertEqual(r["restricted_mean_exposures"],60);self.assertEqual(r["censored_fraction"],.5)
