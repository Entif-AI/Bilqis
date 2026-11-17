"""The published explain command must resolve in the canonical checkout.

This catches a package.json script that advertises a command missing from the
argparse entrypoint, even when a separate worktree has a working implementation.
"""
from contextlib import redirect_stdout
from io import StringIO
import unittest

from bilqis_mlx.cli import _main, parse_args


class ExplainCliTests(unittest.TestCase):
    def test_legacy_school_state_error_explains_all_five_predicates(self):
        args = parse_args(["explain", "INVALID_OR_DRIFTED_SCHOOL_STATE"])
        output = StringIO()
        with redirect_stdout(output):
            result = _main(args)
        self.assertEqual(result, 0)
        text = output.getvalue()
        self.assertIn("LEGACY ERROR AMBIGUITY", text)
        for field in (
            "SCHOOL.STATE.SCHEMA_MISMATCH",
            "SCHOOL.STATE.COURSE_DIGEST_MISMATCH",
            "SCHOOL.STATE.STAGE_INVALID",
            "SCHOOL.STATE.ACTIVE_GRADES_EMPTY",
            "SCHOOL.STATE.GRADE_INDEX_OUT_OF_RANGE",
        ):
            self.assertIn(field, text)

    def test_abstract_stop_reason_and_candidate_gate_have_real_explanations(self):
        for code, expected in (
            ("AUTONOMY_SOURCE_DEVELOPMENT_REQUIRED", "source-development mode"),
            ("STAGED_SUCCESSOR_BINDING_REQUIRED", "precompiled executable successor"),
        ):
            with self.subTest(code=code):
                # npm's script inserts -- before the positional code.
                args = parse_args(["explain", "--", code])
                output = StringIO()
                with redirect_stdout(output):
                    self.assertEqual(_main(args), 0)
                self.assertIn(expected, output.getvalue())
                self.assertIn("NEXT ACTION", output.getvalue())

    def test_error_alias_uses_the_same_registry(self):
        args = parse_args(["explain-error", "SCHOOL.STATE.COURSE_DIGEST_MISMATCH"])
        output = StringIO()
        with redirect_stdout(output):
            self.assertEqual(_main(args), 0)
        self.assertIn("runtime schedule", output.getvalue())


if __name__ == "__main__":
    unittest.main()
