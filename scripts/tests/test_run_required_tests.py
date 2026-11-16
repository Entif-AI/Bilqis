import io
from pathlib import Path
import tempfile
import unittest

from scripts import run_required_tests


class RequiredTestRunnerTests(unittest.TestCase):
    def _test_file(self, root: Path, package: str, body: str) -> Path:
        target = root / package / "tests" / "test_required.py"
        target.parent.mkdir(parents=True)
        for package in (target.parents[1], target.parent):
            (package / "__init__.py").write_text("")
        target.write_text("import unittest\n" + body)
        return target

    def test_required_target_passes_when_every_test_executes(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            target = self._test_file(
                root,
                "required_pass_fixture",
                "class Required(unittest.TestCase):\n"
                "    def test_ok(self): self.assertEqual(2 + 2, 4)\n",
            )
            output = io.StringIO()
            result = run_required_tests.main(
                [str(target)], root=root, stream=output)
        self.assertEqual(result, 0)
        self.assertIn("skipped=0", output.getvalue())

    def test_required_target_fails_when_unittest_skips(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            target = self._test_file(
                root,
                "required_skip_fixture",
                "class Required(unittest.TestCase):\n"
                "    @unittest.skip('optional binary missing')\n"
                "    def test_missing(self): pass\n",
            )
            output = io.StringIO()
            result = run_required_tests.main(
                [str(target)], root=root, stream=output)
        self.assertEqual(result, 1)
        self.assertIn("REQUIRED_TEST_SKIP_BLOCKED", output.getvalue())


if __name__ == "__main__":
    unittest.main()
