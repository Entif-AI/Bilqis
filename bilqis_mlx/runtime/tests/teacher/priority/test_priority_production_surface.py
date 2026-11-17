"""#1315 production C03 selection cannot bypass the lawful priority path."""
from pathlib import Path

import bilqis_mlx.runtime.accepted_teacher_custody as custody
import bilqis_mlx.runtime.foundation_teacher_owner as foundation


def test_direct_foundation_selector_is_retired():
    assert not hasattr(foundation, "select_foundation_teacher_visit")
    assert "select_accepted_teacher_visit" not in custody.__all__


def test_production_package_does_not_call_lower_level_custody_selector():
    package_root = Path(__file__).resolve().parents[4]
    violations = []
    for path in package_root.rglob("*.py"):
        if "tests" in path.parts or path.name == "accepted_teacher_custody.py":
            continue
        if "select_accepted_teacher_visit" in path.read_text(encoding="utf-8"):
            violations.append(path.relative_to(package_root).as_posix())
    assert violations == []
