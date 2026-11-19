"""Focused curriculum-factory contract tests."""
from pathlib import Path as _Path

_TEST_ROOT = _Path(__file__).resolve().parent
__path__.extend(
    str(_TEST_ROOT / compartment)
    for compartment in ("curriculum", "lifecycle", "sources")
)
del _TEST_ROOT, _Path

from pathlib import Path

# Keep the executable-release fixture import used by other test suites.
__path__.append(str(Path(__file__).parent / "executable_release"))
