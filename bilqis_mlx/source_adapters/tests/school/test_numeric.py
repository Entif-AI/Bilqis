"""Complete Registry C source views, with no real neural updates."""
from collections import Counter
from dataclasses import replace
from pathlib import Path
import unittest

from bilqis_mlx.grade_a_release import accepted_grade_a
from bilqis_mlx.live_grade_a import live_course as a_course
from bilqis_mlx.live_grade_b import live_course as b_course
from bilqis_mlx.live_grade_c import PLANS, draw, live_course, proposed_graph, registry_graph
from bilqis_mlx.semantics.abi import load_historical_graph
from bilqis_mlx.source_adapters.numeric import decode
from bilqis_mlx.semantics.numeric import evaluate
from bilqis_mlx.verification.numeric import independent_value
import json
from copy import deepcopy

from bilqis_mlx.paths import REPO_ROOT as ROOT
SOURCE = ROOT / "vendor" / "legacy-v16"


class NumericProviderIdentityTests(unittest.TestCase):
    def test_implementation_revision_preserves_historical_semantic_admission(self):
        from unittest.mock import patch
        from bilqis_mlx import live_grade_c as numeric
        evidence = numeric.REGISTRY_PATH.read_bytes()
        graph = numeric.registry_graph()
        historical = numeric.constructor_digest()
        self.assertNotEqual(numeric.provider_implementation_digest(), historical)
        with patch.object(numeric, "provider_implementation_digest", return_value="f" * 64):
            self.assertEqual(numeric.constructor_digest(), historical)
            self.assertEqual(numeric.registry_graph(), graph)
        self.assertEqual(numeric.REGISTRY_PATH.read_bytes(), evidence)
        self.assertEqual({entry.admission_receipt for entry in numeric.admissions()},
                         set(json.loads(evidence)["admission_receipts"]))

    def test_changed_semantics_cannot_reuse_historical_release_attestation(self):
        from unittest.mock import patch
        from bilqis_mlx import live_grade_c as numeric
        revised = deepcopy(numeric.CONTRACT)
        revised["append_only_nodes"][0]["meaning"] = "A different semantic contract"
        for version in (numeric.CONTRACT["schema"], "bilqis.numeric-semantics/v2"):
            revised["schema"] = version
            with self.subTest(version=version), patch.object(numeric, "CONTRACT", revised):
                with self.assertRaisesRegex(ValueError, "GRADE_C_NATIVE_REGISTRY_ADMISSION_NOT_VERIFIED"):
                    numeric.registry_graph()

    def test_missing_semantic_attestation_fails_closed(self):
        from unittest.mock import patch
        from bilqis_mlx import live_grade_c as numeric
        evidence = json.loads((ROOT / "bilqis_mlx/compatibility/numeric_constructor_v1.json").read_text())
        for field in ("semantic_release", "semantic_release_sha256", "lesson_plan_sha256",
                      "source_files_sha256"):
            incomplete = {key: value for key, value in evidence.items() if key != field}
            with self.subTest(field=field), patch.object(
                    Path, "read_text", return_value=json.dumps(incomplete)):
                with self.assertRaisesRegex(ValueError, "GRADE_C_NATIVE_REGISTRY_ADMISSION_NOT_VERIFIED"):
                    numeric.constructor_digest()

    def test_numeric_source_owns_independent_check_and_semantic_footprint(self):
        from bilqis_mlx.source_adapters import numeric
        from bilqis_mlx.source_adapters.school import live_source_registry, C_ORACLE
        adapter = live_source_registry().require(
            "bilqis_mlx.numeric_curriculum.draw_numeric", C_ORACLE)
        self.assertIs(adapter.check, numeric.check_numeric)
        self.assertIs(adapter.semantic_footprint, numeric.semantic_footprint)
        row = {"record": {"task": numeric.DIALECT, "symbols": [
            "school.syntax.math", "school.op.EQ", "school.op.ADD",
            "school.number.1", "school.number.1", "school.number.2", "syntax.end"]}}
        self.assertEqual(numeric.semantic_footprint(row),
                         ("school.op.ADD", "school.number.1"))

    def test_matching_specimens_do_not_authorize_an_unattested_provider(self):
        from dataclasses import replace
        from types import SimpleNamespace
        from unittest.mock import patch
        from bilqis_mlx.factory.generation import runtime_adapter_for_release
        from bilqis_mlx.source_adapters.school import live_source_registry, C_ORACLE
        registry = live_source_registry()
        generator = "bilqis_mlx.numeric_curriculum.draw_numeric"
        adapter = registry.require(generator, C_ORACLE)
        release = SimpleNamespace(
            source_bindings=SimpleNamespace(by_capability={"C.ADD": SimpleNamespace(
                generator_id=generator, oracle_id=C_ORACLE)}),
            source_adapters=(replace(adapter.descriptor, implementation_sha256="f" * 64),))
        execution = SimpleNamespace(capability_id="C.ADD", provider_id=adapter.descriptor.adapter_id)
        with patch("bilqis_mlx.factory.generation._requalifies_sealed_capability",
                   return_value=True, create=True):
            with self.assertRaisesRegex(ValueError, "FACTORY_EXECUTABLE_GENERATION_ADAPTER_DRIFT"):
                runtime_adapter_for_release(None, {}, release, registry, execution)

    def test_adr106_staircase_receipt_reuses_unchanged_numeric_provider(self):
        from dataclasses import replace
        from types import SimpleNamespace
        from bilqis_mlx.factory.generation import runtime_adapter_for_release
        from bilqis_mlx.numeric_staircase import RELEASE as STAIRCASE_RELEASE
        from bilqis_mlx.source_adapters.school import live_source_registry, C_ORACLE
        registry = live_source_registry()
        generator = "bilqis_mlx.numeric_curriculum.draw_numeric"
        adapter = registry.require(generator, C_ORACLE)
        current = adapter.descriptor
        old_staircase_digest = (
            "ec3b5338fc1604a6250a847ee99eae09956b5a5bb269a63f3ac8372205133e74")
        admitted = replace(current, cohort_releases=tuple(
            (release, old_staircase_digest if release == STAIRCASE_RELEASE else digest)
            for release, digest in current.cohort_releases))
        release = SimpleNamespace(
            source_bindings=SimpleNamespace(by_capability={"C.COUNT": SimpleNamespace(
                generator_id=generator, oracle_id=C_ORACLE)}),
            source_adapters=(admitted,))
        execution = SimpleNamespace(
            capability_id="C.COUNT", provider_id=current.adapter_id)

        self.assertIs(
            runtime_adapter_for_release(None, {}, release, registry, execution),
            adapter)

        unknown = replace(admitted, cohort_releases=tuple(
            (name, "f" * 64 if name == STAIRCASE_RELEASE else digest)
            for name, digest in admitted.cohort_releases))
        drifted_release = SimpleNamespace(
            source_bindings=release.source_bindings,
            source_adapters=(unknown,))
        with self.assertRaisesRegex(
                ValueError, "FACTORY_EXECUTABLE_GENERATION_ADAPTER_DRIFT"):
            runtime_adapter_for_release(
                None, {}, drifted_release, registry, execution)


class GradeCSourceTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.parent = load_historical_graph()
        cls.graph = registry_graph()
        assert cls.graph == proposed_graph(cls.parent)
        manifest = json.loads((ROOT / "docs/provenance/GRADE_A_CANDIDATE_MANIFEST_V2.json").read_text())
        cls.previous = b_course(a_course(accepted_grade_a(manifest)), SOURCE)

    def test_provider_acceptance_and_footprints_preserve_numeric_source_rules(self):
        from unittest.mock import patch
        from bilqis_mlx.source_adapters.numeric import check_numeric, semantic_footprint
        rows = draw(self.graph, seed=19, maximum=3)
        with patch("bilqis_mlx.source_adapters._school.numeric.draw_numeric",
                   side_effect=AssertionError("checker invoked generator")):
            for row in rows:
                self.assertTrue(check_numeric(row, graph=self.graph))
                self.assertFalse(check_numeric({**row, "gold": "wrong"}, graph=self.graph))
                self.assertFalse(check_numeric({**row, "tokens": row["tokens"][:-1]}, graph=self.graph))
                footprint = semantic_footprint(row)
                self.assertTrue(footprint)
                self.assertTrue(all(root.startswith(("school.op.", "school.number."))
                                    for root in footprint))
                self.assertEqual(semantic_footprint({**row, "root": "forged.root"}), footprint)
        with self.assertRaises(ValueError):
            check_numeric({"record": {"symbols": ["invalid"]}}, graph=self.graph)
        with self.assertRaises(IndexError):
            check_numeric({**rows[0], "tokens": [len(self.graph["tokens"])]}, graph=self.graph)

    def test_c_growth_preserves_historical_registry_rows(self):
        from bilqis_mlx.token_atlas import rows_for_graph
        self.assertEqual(rows_for_graph(self.graph)[:len(self.parent['tokens'])],
                         rows_for_graph(self.parent))

    def test_full_staged_registry_sequence_preserves_a_b_and_old_token_contracts(self):
        course = live_course(self.previous, self.graph, maximum=10)
        self.assertTrue(course.executable)
        self.assertEqual(course.grades[:-1], self.previous.grades)
        self.assertEqual(tuple(p.lesson_id for p in PLANS),
                         ("LESSON-058", "LESSON-059", "LESSON-058", "LESSON-060",
                          "LESSON-060", "LESSON-061", "LESSON-062"))
        n = len(self.parent["tokens"])
        self.assertEqual(self.graph["tokens"][:n], self.parent["tokens"])
        self.assertEqual(self.graph["nodes"][:n], self.parent["nodes"])
        self.assertEqual(len(self.graph["tokens"])-n, 5)

    def test_all_generated_views_have_independent_gold_native_ids_and_concrete_inputs(self):
        rows = draw(self.graph, seed=19, maximum=10)
        self.assertEqual(Counter(r["capability"] for r in rows),
                         {p.capability: 33 for p in PLANS})
        by_count = [r for r in rows if r["capability"] == "C.COUNT" and r["answer_kind"] == "numeric_active"]
        self.assertEqual({r["gold"] for r in by_count}, {str(i) for i in range(11)})
        for row in rows:
            with self.subTest(capability=row["capability"], identity=row["id"]):
                expression = decode(row["record"]["symbols"])
                value = evaluate(expression)
                self.assertEqual(value, independent_value(expression))
                self.assertEqual(row["gold"], "TRUE" if value is True else "FALSE" if value is False else str(value))
                self.assertEqual(row["tokens"], [self.graph["tokens"].index(s) for s in row["record"]["symbols"]])
                if row["answer_kind"] == "numeric_active":
                    self.assertEqual(self.graph["tokens"][row["native_output"]["token_id"]],
                                     "school.number."+row["gold"])
                if row["capability"] in ("C.ADD", "C.SUB", "C.MUL", "C.DIV"):
                    self.assertIn("school.syntax.number_set", row["record"]["symbols"])

    def test_fresh_draws_have_no_instruction_exam_partition_and_new_scope_is_versioned(self):
        first = draw(self.graph, seed=10, maximum=3)
        self.assertEqual(first, draw(self.graph, seed=10, maximum=3))
        self.assertNotEqual(first, draw(self.graph, seed=11, maximum=3))
        self.assertTrue(all("partition" not in row for row in first))
        self.assertNotEqual(live_course(self.previous, self.graph, maximum=3).digest(),
                            live_course(self.previous, self.graph, maximum=10).digest())

    def test_unknown_token_or_missing_source_contract_fails_only_new_c(self):
        graph = {**self.graph, "tokens": self.parent["tokens"]}
        with self.assertRaises(ValueError):
            draw(graph, seed=19, maximum=3)
        self.assertTrue(self.previous.executable)

    def test_nontrivial_semantic_families_and_seed_changes_are_covered(self):
        first = draw(self.graph, seed=1, maximum=10)
        second = draw(self.graph, seed=2, maximum=10)
        direct = lambda rows, cap: [r for r in rows if r["capability"] == cap and
                                    r["answer_kind"] == "numeric_active"]
        self.assertTrue(any(int(r["gold"]) > 1 for r in direct(first, "C.MUL")))
        self.assertTrue(any(int(r["gold"]) > 1 for r in direct(first, "C.DIV")))
        for cap in ("C.ADD", "C.MUL", "C.DIV"):
            a, b = direct(first, cap), direct(second, cap)
            self.assertNotEqual([r["record"] for r in a], [r["record"] for r in b])
            self.assertTrue(any(len(r["witness"]["left_members"]) > 0 and
                                len(r["witness"]["right_members"]) > 0 for r in a))
        for cap in ("C.MUL", "C.DIV"):
            self.assertTrue(all("school.syntax.number_groups" in r["record"]["symbols"]
                                for r in direct(first, cap)))

    def test_swapped_or_reinterpreted_source_tokens_are_rejected(self):
        graph = deepcopy(self.graph)
        a, b = (graph["tokens"].index("school.op."+name) for name in ("ADD", "SUB"))
        graph["tokens"][a], graph["tokens"][b] = graph["tokens"][b], graph["tokens"][a]
        with self.assertRaises(ValueError):
            draw(graph, seed=19, maximum=3)
