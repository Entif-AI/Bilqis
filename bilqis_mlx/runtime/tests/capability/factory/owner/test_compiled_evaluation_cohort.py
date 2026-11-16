"""Issue #1168 immutable C05 cohort identity and custody regressions."""
from pathlib import Path
import json
import tempfile
import unittest

from bilqis_mlx.errors import BilqisError
from bilqis_mlx.runtime.factory_compiled_cohort import (
    compiled_case_identity_digest, compiled_case_identity_record,
    compiled_cohort_candidates, compiled_cohort_record,
    compiled_source_cohort_digest, load_compiled_case,
    load_compiled_cohort_cases, seal_compiled_case, seal_compiled_cohort,
)

from .compiled_evaluation_fixtures import case_record, compiled_case


class CompiledEvaluationCohortContractTests(unittest.TestCase):
    def test_public_record_is_content_addressed_and_excludes_evaluator_gold(self):
        record = case_record()
        self.assertNotIn("gold", str(record).lower())
        self.assertNotIn("answer", str(record).lower())
        self.assertEqual(len(compiled_case_identity_digest(record)), 64)

    def test_every_bound_contract_field_invalidates_case_reuse(self):
        original = case_record()
        digest = compiled_case_identity_digest(original)
        for key in tuple(original):
            if key == "schema":
                continue
            with self.subTest(key=key):
                changed = dict(original)
                changed[key] = ("9" * 64 if key.endswith("sha256")
                                else changed[key] + ":drift")
                self.assertNotEqual(compiled_case_identity_digest(changed), digest)

    def test_generation_is_not_part_of_shared_compiled_case_identity(self):
        values = {key: value for key, value in case_record().items() if key != "schema"}
        values["generation"] = "7" * 64
        with self.assertRaises(BilqisError):
            compiled_case_identity_record(**values)

    def test_reusable_cohort_identity_is_gold_blind_but_source_sensitive(self):
        first = ({
            "id": "row-1", "capability": "A.IDENTITY", "tokens": [1],
            "gold": "TRUE", "native_output": {"token_id": 1},
        },)
        alternate_gold = ({**first[0], "gold": "FALSE",
                           "native_output": {"token_id": 0}},)
        changed_source = ({**first[0], "tokens": [2]},)
        kwargs = dict(
            generator_version="factory-v1", rubric_sha256="7" * 64, seed=17)
        self.assertEqual(
            compiled_source_cohort_digest(first, **kwargs),
            compiled_source_cohort_digest(alternate_gold, **kwargs))
        self.assertNotEqual(
            compiled_source_cohort_digest(first, **kwargs),
            compiled_source_cohort_digest(changed_source, **kwargs))

    def test_content_addressed_cohort_projection_is_cold_resume_stable_and_fail_closed(self):
        record = compiled_cohort_record(
            factory_release_sha256="a" * 64,
            semantic_catalog_sha256="b" * 64,
            source_cohort_sha256="c" * 64,
            source_seed=17,
            case_records=(case_record(),),
        )
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            first = seal_compiled_cohort(root, record)
            second = seal_compiled_cohort(root, record)
            self.assertEqual(first, second)
            projection = root / "c05-compiled-cohorts" / f"{first}.json"
            self.assertEqual(json.loads(projection.read_text()), record)
            self.assertNotIn("gold", projection.read_text().lower())
            projection.write_text("{}")
            with self.assertRaises(BilqisError):
                seal_compiled_cohort(root, record)

    def test_compiled_case_artifact_round_trips_without_private_evaluator_truth(self):
        compiled = compiled_case()
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            artifact = seal_compiled_case(root, compiled)
            path = root / "c05-compiled-cases" / f"{artifact}.json"
            raw = path.read_text()
            self.assertNotIn("PRIVATE_EVALUATOR_TRUTH_1168", raw)
            self.assertNotIn('"gold"', raw.lower())
            cold = load_compiled_case(root, artifact, compiled.identity_sha256)
            self.assertEqual(cold.identity_sha256, compiled.identity_sha256)
            self.assertEqual(cold.compiled_rows, compiled.compiled_rows)
            self.assertEqual(cold.task_template, compiled.task_template)
            path.write_text("{}")
            with self.assertRaises(BilqisError):
                load_compiled_case(root, artifact, compiled.identity_sha256)

    def test_content_addressed_cohort_cold_loads_exact_compiled_cases(self):
        compiled = compiled_case()
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            artifact = seal_compiled_case(root, compiled)
            record = compiled_cohort_record(
                factory_release_sha256="a" * 64,
                semantic_catalog_sha256="b" * 64,
                source_cohort_sha256="c" * 64,
                source_seed=17,
                case_records=(compiled.identity_record,),
                case_artifacts=(artifact,),
            )
            seal_compiled_cohort(root, record)
            candidates = compiled_cohort_candidates(
                root, source_cohort_sha256="c" * 64,
                factory_release_sha256="a" * 64,
                semantic_catalog_sha256="b" * 64, source_seed=17)
            self.assertEqual(candidates, (record,))
            cold = load_compiled_cohort_cases(root, candidates[0])
            self.assertEqual(tuple(item.identity_sha256 for item in cold),
                             (compiled.identity_sha256,))


if __name__ == "__main__":
    unittest.main()
