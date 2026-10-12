import copy
import unittest

from bilqis_alpha.data import known_cases
from bilqis_alpha.microscope import delta, validate_intervention, fixture_registry, replay


class MicroscopeTests(unittest.TestCase):
    def test_single_factor_interventions_preserve_every_other_field(self):
        fixture = fixture_registry()
        cases = {r["id"]: r for r in fixture["cases"]}
        interventions = [r for r in fixture["cases"] if "parent" in r]
        self.assertGreaterEqual(len(interventions), 2)
        self.assertTrue({"evidence", "role_assignment", "negation", "scope"}.issubset({r["factor"] for r in interventions}))
        for case in interventions:
            parent = cases[case["parent"]]
            validate_intervention(parent["semantic"], case["semantic"], case["factor"])
            self.assertTrue(delta(parent["semantic"], case["semantic"], case["factor"]))
            bad = copy.deepcopy(case["semantic"])
            bad["world"]["sources"].append("undeclared-source")
            with self.assertRaises(ValueError):
                validate_intervention(parent["semantic"], bad, case["factor"])

    def test_fixture_pins_real_checkpoint_and_demonstrates_hidden_wrong_relation(self):
        from bilqis_alpha.semantics import evaluate, normalize, digest
        fixture = fixture_registry()
        self.assertEqual(fixture["bindings"]["checkpoint_file_sha256"], "002cffcfbdf44eec2e509704d5a530bb134d655919ec129f46eeffda6b99a3eb")
        wrong = fixture["wrong_candidate_path"]
        self.assertEqual(evaluate(wrong["intended"]), evaluate(wrong["candidate"]))
        self.assertNotEqual(wrong["intended_relation"], wrong["candidate_relation"])
        self.assertEqual(wrong["provenance"], "independently evaluated candidate; no neural intermediate interface")
        self.assertTrue(any(r["selection_provenance"] == "first observed heldout miss by frozen corpus ID" for r in fixture["cases"]))

    def test_absent_or_unpinned_checkpoint_never_substitutes_an_answer(self):
        import tempfile
        from pathlib import Path
        with tempfile.TemporaryDirectory() as temp:
            with self.assertRaises((ValueError, FileNotFoundError)):
                replay(Path(temp))
            (Path(temp) / "model.pt").write_bytes(b"a substituted model")
            with self.assertRaisesRegex(ValueError, "unpinned"):
                replay(Path(temp))


if __name__ == "__main__":
    unittest.main()
