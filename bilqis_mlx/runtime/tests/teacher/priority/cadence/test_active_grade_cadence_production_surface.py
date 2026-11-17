"""#1333 native BAMF cadence cannot depend on the retired cross-grade scheduler."""
import ast
from pathlib import Path


def _top_level_imports(path):
    tree = ast.parse(path.read_text(encoding="utf-8"))
    return tuple(node for node in tree.body if isinstance(node, (ast.Import, ast.ImportFrom)))


def _called_names(path):
    tree = ast.parse(path.read_text(encoding="utf-8"))
    result = set()
    for node in ast.walk(tree):
        if not isinstance(node, ast.Call):
            continue
        if isinstance(node.func, ast.Name):
            result.add(node.func.id)
        elif isinstance(node.func, ast.Attribute):
            result.add(node.func.attr)
    return result


def test_priority_planning_import_path_is_scheduler_neutral():
    runtime = Path(__file__).resolve().parents[4]
    planning = runtime / "_autonomy_live/planning.py"
    rendered = ast.dump(ast.Module(body=list(_top_level_imports(planning)), type_ignores=[]))
    assert "curriculum.scheduler" not in rendered
    owner = (runtime / "_teacher/priority/priority_planning_owner.py").read_text(
        encoding="utf-8")
    assert "runtime.autonomy_live import" not in owner
    assert "runtime._autonomy_live.planning import" in owner


def test_native_bamf_teacher_and_operator_do_not_reference_cross_grade_scheduler_symbols():
    runtime = Path(__file__).resolve().parents[4]
    roots = (runtime / "_teacher", runtime / "bamf_operator")
    retired = (
        "_resume_ordinary_spiral", "_continue_main_sweep", "_main_queue",
        "DebtCadencePolicy", "weakest_three",
    )
    violations = []
    for root in roots:
        for path in root.rglob("*.py"):
            if "tests" in path.parts:
                continue
            text = path.read_text(encoding="utf-8")
            if any(symbol in text for symbol in retired):
                violations.append(path.relative_to(runtime).as_posix())
    assert violations == []


def test_operate_bamf_native_call_chain_reaches_active_grade_cadence_owner():
    runtime = Path(__file__).resolve().parents[4]
    assert "_visit_impl" in _called_names(runtime / "bamf_operator/session.py")
    assert "select_foundation_priority_visit" in _called_names(
        runtime / "bamf_operator/session.py")
    assert "issue_foundation_priority_authority" in _called_names(
        runtime / "_teacher/priority/foundation_teacher_owner.py")
    assert "issue_active_grade_cadence" in _called_names(
        runtime / "_teacher/priority/priority_authority.py")

