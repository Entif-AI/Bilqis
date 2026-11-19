"""Snapshot-local, fail-fast integration qualification for issue #1391."""
import os
import signal
from pathlib import Path
import subprocess
import sys
import time

root = Path.cwd()
bootstrap = root / "docs/evidence/bamf/1391-native-memory/resource_bootstrap"
environment = dict(os.environ)
test_paths = (str(bootstrap), str(root))
if dependency_path := environment.get("BILQIS_1391_TEST_DEPS"):
    test_paths += (dependency_path,)
environment.update({
    "BILQIS_TEST_WORKERS": "1",
    "BILQIS_TEST_BASE_REF": "92299b7ccddb1a1b4155723b4eb4eee1057864cb",
    "BILQIS_QUALITY_BASE_REF": "92299b7ccddb1a1b4155723b4eb4eee1057864cb",
    "PYTHONPATH": os.pathsep.join(test_paths),
    "PATH": str(Path(sys.executable).parent) + os.pathsep + "/opt/homebrew/bin:" + os.environ["PATH"],
})
print("STAGE Node test dependencies", flush=True)
subprocess.run(["npm", "ci", "--ignore-scripts", "--omit=dev"],
               env=environment, timeout=180, check=True)
started = time.monotonic()
# Prior leaf: 18 minutes including static Git-history checks. Aggregate discovery
# contains 1,186 files / approximately 5,500 unittest methods. Expected complete
# pipeline: 45–90 minutes; terminal failure boundary below the two-hour ceiling.
deadline = started + 115 * 60
# Use the aggregate runner's source shim, SKOS policy and import context.
# Stop after loading so import errors surface before any test executes.
preflight = """
from scripts import run_tests

load = run_tests.load_test_files

def check_imports(paths, root):
    suite = load(paths, root)
    failures = [case for case in suite if isinstance(case, run_tests._LoadFailure)]
    for case in failures:
        print(f"{case}: {type(case._error).__name__}: {case._error}", flush=True)
    count = suite.countTestCases()
    print(f"AGGREGATE_PREFLIGHT cases={count} load_errors={len(failures)}", flush=True)
    raise SystemExit(1 if failures or not count else 0)

run_tests.load_test_files = check_imports
run_tests.main([])
"""
stages = (
    ("static integration quality", ["npm", "run", "quality:check"]),
    ("aggregate import/collection preflight", [sys.executable, "-B", "-c", preflight]),
    ("affected owner tests", ["npm", "run", "test:changed"]),
    ("Node behavior", ["npm", "run", "bamf:test"]),
    ("security boundary", ["npm", "run", "bamf:security:test"]),
    ("premerge aggregate", ["npm", "run", "test:premerge"]),
)
for label, command in stages:
    print(f"STAGE {label} START", flush=True)
    remaining = deadline - time.monotonic()
    if remaining <= 0:
        raise TimeoutError("integration qualification exceeded its wall-clock bound")
    process = subprocess.Popen(command, env=environment, start_new_session=True)
    try:
        process.wait(timeout=remaining)
    except subprocess.TimeoutExpired:
        os.killpg(process.pid, signal.SIGTERM)
        try:
            process.wait(timeout=10)
        except subprocess.TimeoutExpired:
            os.killpg(process.pid, signal.SIGKILL)
            process.wait()
        raise
    print(f"STAGE {label} exit={process.returncode} "
          f"elapsed_seconds={time.monotonic() - started:.3f}", flush=True)
    if process.returncode:
        raise SystemExit(process.returncode)
print("INTEGRATION_QUALIFICATION_PASS", flush=True)
