from dataclasses import replace
import unittest

from bilqis_mlx.curriculum.scheduler import start_new, verify_state
from bilqis_mlx.curriculum.tests.test_school import cp, three_grade_course
from bilqis_mlx.errors import BilqisError, ErrorBus, SCHOOL


class ErrorControlPlaneTests(unittest.TestCase):
    def test_school_course_drift_preserves_exact_invariant_and_context(self):
        course = three_grade_course()
        state = start_new(course, cp("student"))
        drifted = replace(state, course_digest="0" * 64)

        with self.assertRaises(BilqisError) as caught:
            verify_state(course, drifted)

        error = caught.exception
        self.assertIs(error.spec, SCHOOL.STATE.COURSE_DIGEST_MISMATCH)
        self.assertEqual(error.context["saved_course_digest"], "0" * 64)
        self.assertEqual(error.context["runtime_course_digest"], course.digest())

        report = ErrorBus.report(error)
        self.assertEqual(report.code, "SCHOOL.STATE.COURSE_DIGEST_MISMATCH")
        self.assertEqual(report.owner, "curriculum.scheduler")
        self.assertTrue(report.preserve_state)
        self.assertIn("immutable", report.next_action.lower())

    def test_typed_error_can_preserve_one_declared_legacy_wire_code(self):
        spec = SCHOOL.STATE.COURSE_DIGEST_MISMATCH
        with self.assertRaises(BilqisError) as caught:
            ErrorBus.raise_legacy(spec, saved_course_digest="old", runtime_course_digest="new")
        self.assertEqual(str(caught.exception), spec.legacy_codes[0])
        self.assertEqual(caught.exception.code, spec.code)
        report = ErrorBus.report(caught.exception)
        self.assertFalse(report.legacy_untyped)
        self.assertEqual(report.code, spec.code)
        self.assertTrue(report.preserve_state)

    def test_extracted_owner_failures_are_registered_and_keep_wire_aliases(self):
        from bilqis_mlx.errors.catalog import CATALOG
        for spec in (SCHOOL.STATE.INVALID_CAPABILITY_SCORE,
                     SCHOOL.LEARNING.MISSING_SOURCE_ROWS):
            with self.subTest(code=spec.code):
                self.assertIn(spec, CATALOG)
                error = ErrorBus.legacy_error(spec)
                self.assertEqual(str(error), spec.legacy_codes[0])
                self.assertEqual(ErrorBus.explain(spec.code)[0].code, spec.code)
                self.assertFalse(ErrorBus.explain(spec.code)[0].legacy_untyped)

    def test_legacy_string_error_is_still_routed_through_one_bus(self):
        report = ErrorBus.report(
            ValueError("FACTORY_RELEASE_RUNTIME_SOURCE_ADAPTER_DRIFT"))
        self.assertEqual(
            report.code, "FACTORY_RELEASE_RUNTIME_SOURCE_ADAPTER_DRIFT")
        self.assertEqual(report.disposition, "PRESERVE_AND_REPAIR")
        self.assertTrue(report.legacy_untyped)


if __name__ == "__main__":
    unittest.main()
