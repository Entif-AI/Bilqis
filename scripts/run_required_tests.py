#!/usr/bin/env python3
"""Run launch-critical unittest targets and fail closed on every skip."""

from __future__ import annotations

import argparse
from pathlib import Path
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts import run_tests


def main(argv=None, *, root: Path | None = None, stream=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("targets", nargs="+", help="required test paths or dotted names")
    arguments = parser.parse_args(argv)
    root = (root or ROOT).resolve()
    stream = stream or sys.stdout
    shimmed = run_tests._install_source_only_legacy_geometry_shim()
    try:
        suite = run_tests._load_targets(tuple(arguments.targets), root)
        if suite.countTestCases() == 0:
            print("REQUIRED_TESTS_EMPTY", file=stream)
            return 2
        result = unittest.TextTestRunner(stream=stream, verbosity=2).run(suite)
        run_tests._print_totals(result, stream)
        if result.skipped:
            print(
                "REQUIRED_TEST_SKIP_BLOCKED "
                + ",".join(test.id() for test, _reason in result.skipped),
                file=stream,
            )
            return 1
        return 0 if result.wasSuccessful() else 1
    finally:
        if shimmed:
            sys.modules.pop("bilqis_logic.geometry", None)


if __name__ == "__main__":
    raise SystemExit(main())
