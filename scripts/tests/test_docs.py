import importlib.util
from pathlib import Path
import tempfile
import unittest


def _checker_module():
    path = Path(__file__).parents[1] / "quality" / "check_docs.py"
    spec = importlib.util.spec_from_file_location("bilqis_check_docs", path)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


class DocumentationChecksTests(unittest.TestCase):
    def _write(self, root: Path, relative: str, content: str = "# document\n") -> None:
        path = root / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content, encoding="utf-8")

    def test_reports_broken_markdown_links(self):
        checker = _checker_module()
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            self._write(root, "README.md", "[missing](docs/missing.md)\n")
            self._write(root, "docs/README.md")

            issues = checker.inspect_docs(root)

        self.assertEqual(issues, ("README.md:1 BROKEN_MARKDOWN_LINK docs/missing.md",))

    def test_reports_misplaced_docs_root_files_and_directories(self):
        checker = _checker_module()
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            self._write(root, "docs/README.md")
            self._write(root, "docs/old-note.md")
            self._write(root, "docs/scratch/note.md")

            issues = checker.inspect_docs(root)

        self.assertEqual(
            issues,
            (
                "docs/old-note.md DOCS_ROOT_FILE",
                "docs/scratch DOCS_TOP_LEVEL_DIRECTORY",
            ),
        )

    def test_ignores_hidden_os_metadata_and_empty_legacy_directories(self):
        checker = _checker_module()
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            self._write(root, "docs/README.md")
            self._write(root, "docs/.DS_Store", "metadata")
            (root / "docs" / "development").mkdir()

            issues = checker.inspect_docs(root)

        self.assertEqual(issues, ())

    def test_accepts_anchors_external_urls_and_escaped_local_paths(self):
        checker = _checker_module()
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            self._write(
                root,
                "README.md",
                "\n".join(
                    (
                        "[anchor](#details)",
                        "[external](https://example.invalid/reference)",
                        "[local](docs/evidence/a%20file.md#heading)",
                        "[reference]: docs/evidence/a%20file.md#heading",
                    )
                ),
            )
            self._write(root, "docs/README.md")
            self._write(root, "docs/evidence/a file.md")

            issues = checker.inspect_docs(root)

        self.assertEqual(issues, ())

    def test_accepts_repository_relative_links_from_nested_documents(self):
        checker = _checker_module()
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            self._write(root, "README.md")
            self._write(root, "docs/README.md")
            self._write(root, "docs/history/record.md", "[evidence](docs/evidence/receipt.md)\n")
            self._write(root, "docs/evidence/receipt.md")

            issues = checker.inspect_docs(root)

        self.assertEqual(issues, ())

    def test_ignores_vendored_run_and_installed_dependency_markdown(self):
        checker = _checker_module()
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            self._write(root, "README.md")
            self._write(root, "docs/README.md")
            self._write(root, "vendor/source.md", "[broken](missing.md)\n")
            self._write(root, "runs/receipt.md", "[broken](missing.md)\n")
            self._write(root, "node_modules/ajv/README.md", "[broken](SECURITY.md)\n")

            issues = checker.inspect_docs(root)

        self.assertEqual(issues, ())


if __name__ == "__main__":
    unittest.main()
