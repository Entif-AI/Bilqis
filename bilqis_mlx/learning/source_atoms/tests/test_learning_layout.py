"""Physical owner directories must preserve lazy canonical import identities."""
import importlib
import importlib.util
import json
from pathlib import Path
import subprocess
import sys
from unittest import TestCase


_APPROVED_ALIASES = frozenset({"source_selection.py", "teacher_observations.py"})


def _assert_root_symlink_inventory(test, root):
    observed = {path.name for path in root.iterdir() if path.is_symlink()}
    test.assertEqual(observed, _APPROVED_ALIASES)


def _assert_owner_alias(test, root, owner):
    alias = root / owner.name
    imported = Path(importlib.util.find_spec("bilqis_mlx.learning." + owner.stem).origin)
    if owner.name in _APPROVED_ALIASES:
        test.assertTrue(alias.is_symlink(), f"compatibility alias must be symlink: {alias}")
        test.assertEqual(alias.resolve(strict=True), owner.resolve(strict=True))
        test.assertEqual(imported, alias)
    else:
        test.assertFalse(alias.exists() or alias.is_symlink(),
                         f"unapproved duplicate/alias: {alias}")
        test.assertEqual(imported, owner)


class LearningLayoutTests(TestCase):
    def test_every_relocated_owner_resolves_once_under_its_existing_module_name(self):
        import bilqis_mlx.learning as learning

        root = Path(learning.__file__).parent
        _assert_root_symlink_inventory(self, root)
        observed = set()
        for directory in learning._SOURCE_DIRECTORIES:
            for path in sorted((root / directory).glob("*.py")):
                self.assertNotIn(path.stem, observed)
                observed.add(path.stem)
                name = "bilqis_mlx.learning." + path.stem
                _assert_owner_alias(self, root, path)
        self.assertEqual(len(observed), 52)

    def test_compatibility_alias_contract_rejects_regular_duplicates_and_other_links(self):
        from tempfile import TemporaryDirectory
        from unittest.mock import patch
        with TemporaryDirectory() as temporary:
            root = Path(temporary)
            teaching = root / "_teaching"
            teaching.mkdir()
            for filename in (*sorted(_APPROVED_ALIASES), "forbidden.py"):
                owner = teaching / filename
                owner.write_text("pass\n")
                alias = root / filename
                module = "bilqis_mlx.learning." + owner.stem
                with patch("importlib.util.find_spec", return_value=type(
                        "Spec", (), {"origin": str(alias)})()):
                    if filename in _APPROVED_ALIASES:
                        alias.symlink_to(owner.relative_to(root))
                        with self.subTest(filename=filename):
                            _assert_owner_alias(self, root, owner)
                        alias.unlink()
                        alias.write_text("pass\n")
                        with self.assertRaises(AssertionError):
                            _assert_owner_alias(self, root, owner)
                        alias.unlink()
                        wrong = root / "wrong.py"
                        wrong.write_text("pass\n")
                        alias.symlink_to(wrong.name)
                        with self.assertRaises(AssertionError):
                            _assert_owner_alias(self, root, owner)
                        alias.unlink()
                    else:
                        alias.symlink_to(owner.relative_to(root))
                        with self.assertRaises(AssertionError):
                            _assert_owner_alias(self, root, owner)
                        alias.unlink()
                        alias.write_text("pass\n")
                        with self.assertRaises(AssertionError):
                            _assert_owner_alias(self, root, owner)

    def test_root_inventory_rejects_rogue_compatibility_alias_name(self):
        from tempfile import TemporaryDirectory
        with TemporaryDirectory() as temporary:
            root = Path(temporary)
            teaching = root / "_teaching"
            teaching.mkdir()
            for filename in sorted(_APPROVED_ALIASES):
                owner = teaching / filename
                owner.write_text("pass\n")
                (root / filename).symlink_to(owner.relative_to(root))
            _assert_root_symlink_inventory(self, root)
            (root / "rogue.py").symlink_to("_teaching/source_selection.py")
            with self.assertRaises(AssertionError):
                _assert_root_symlink_inventory(self, root)

    def test_importing_learning_does_not_eagerly_load_neural_or_teacher_owners(self):
        command = (
            "import json,sys; import bilqis_mlx.learning; "
            "print(json.dumps(sorted(n for n in sys.modules "
            "if n == 'mlx' or n.startswith('bilqis_mlx.learning.'))))")
        result = subprocess.run([sys.executable, "-B", "-c", command],
                                check=True, capture_output=True, text=True)
        self.assertEqual(json.loads(result.stdout), [])

    def test_existing_helper_imports_still_resolve_to_their_owner_tests(self):
        module = importlib.import_module("bilqis_mlx.learning.tests.test_teacher_votes")
        self.assertEqual(Path(module.__file__).parent.name, "tests")
        self.assertEqual(Path(module.__file__).parent.parent.name, "_teaching")
