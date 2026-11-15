#!/usr/bin/env python3
"""Validate the predecessor-to-BAMF invariant transfer ledger."""
from __future__ import annotations

import ast
import json
import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MANIFEST = ROOT / "docs/tasks/bamf-0.2/invariant-transfer-v1.json"
SCHEMA = "bilqis.bamf.invariant-transfer/v1"
STATUSES = {"TRANSFERRED", "SUPERSEDED", "MISSING"}
EVIDENCE_KINDS = {"independent_authority", "self_consistency", "superseding_authority"}
SHA = re.compile(r"^[0-9a-f]{40}$")


def _git(*args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ["git", *args], cwd=ROOT, capture_output=True, text=True,
    )


def _test_names(source: str) -> set[str]:
    try:
        tree = ast.parse(source)
    except SyntaxError:
        return set()
    return {
        node.name for node in ast.walk(tree)
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
        and node.name.startswith("test_")
    }


def _current_test(proof: dict, problems: list[str], invariant_id: str) -> None:
    path = ROOT / str(proof.get("path", ""))
    test = proof.get("test")
    if not path.is_file():
        problems.append(f"SUCCESSOR_PROOF_MISSING {invariant_id} {proof.get('path')}")
        return
    if test not in _test_names(path.read_text(encoding="utf-8")):
        problems.append(f"SUCCESSOR_TEST_MISSING {invariant_id} {proof.get('path')}::{test}")


def _superseding_authority(proof: dict, problems: list[str], invariant_id: str) -> None:
    path = ROOT / str(proof.get("path", ""))
    anchor = str(proof.get("anchor", ""))
    if not path.is_file():
        problems.append(f"SUPERSEDING_AUTHORITY_MISSING {invariant_id} {proof.get('path')}")
        return
    if not anchor or anchor not in path.read_text(encoding="utf-8"):
        problems.append(
            f"SUPERSEDING_AUTHORITY_ANCHOR_MISSING {invariant_id} "
            f"{proof.get('path')}::{anchor}"
        )


def _predecessor_test(commit: str, proof: dict, problems: list[str], invariant_id: str) -> None:
    path, test = proof.get("path"), proof.get("test")
    result = _git("show", f"{commit}:{path}")
    if result.returncode:
        problems.append(f"PREDECESSOR_PROOF_MISSING {invariant_id} {path}")
        return
    if test not in _test_names(result.stdout):
        problems.append(f"PREDECESSOR_TEST_MISSING {invariant_id} {path}::{test}")


def validate(manifest: dict) -> list[str]:
    problems: list[str] = []
    if manifest.get("schema") != SCHEMA:
        problems.append(f"SCHEMA_INVALID {manifest.get('schema')}")
    authority = manifest.get("predecessor_authority", {})
    commit = str(authority.get("commit", ""))
    if not SHA.fullmatch(commit) or _git("cat-file", "-e", f"{commit}^{{commit}}").returncode:
        problems.append(f"PREDECESSOR_AUTHORITY_INVALID {commit}")
    live = authority.get("live_check", {})
    if (live.get("command") != "python3 -B scripts/check_legacy_trainer_authority.py --live"
            or live.get("status") != "RECENT_DURABLE_RECEIPT"
            or live.get("verified_head") != commit
            or not live.get("receipt")):
        problems.append("PREDECESSOR_LIVE_RECEIPT_INVALID")

    seen: set[str] = set()
    invariants = manifest.get("invariants")
    if not isinstance(invariants, list) or not invariants:
        return problems + ["INVARIANTS_EMPTY"]
    for row in invariants:
        invariant_id = str(row.get("id", ""))
        if not invariant_id or invariant_id in seen:
            problems.append(f"INVARIANT_ID_INVALID {invariant_id}")
        seen.add(invariant_id)
        status = row.get("status")
        if status not in STATUSES:
            problems.append(f"STATUS_INVALID {invariant_id} {status}")
        if status == "MISSING":
            problems.append(f"INVARIANT_MISSING {invariant_id}")
        if not row.get("observable_invariant"):
            problems.append(f"OBSERVABLE_INVARIANT_EMPTY {invariant_id}")
        owner = ROOT / str(row.get("bamf_owner", {}).get("path", ""))
        if not owner.is_file():
            problems.append(f"BAMF_OWNER_MISSING {invariant_id} {row.get('bamf_owner', {}).get('path')}")
        predecessor = row.get("predecessor_proofs", [])
        if not predecessor:
            problems.append(f"PREDECESSOR_PROOFS_EMPTY {invariant_id}")
        elif SHA.fullmatch(commit):
            for proof in predecessor:
                _predecessor_test(commit, proof, problems, invariant_id)
        evidence = row.get("successor_evidence", [])
        for proof in evidence:
            kind = proof.get("kind")
            if kind not in EVIDENCE_KINDS:
                problems.append(f"EVIDENCE_KIND_INVALID {invariant_id} {kind}")
                continue
            if kind == "superseding_authority":
                _superseding_authority(proof, problems, invariant_id)
            else:
                _current_test(proof, problems, invariant_id)
        if status == "TRANSFERRED" and not any(
                proof.get("kind") == "independent_authority" for proof in evidence):
            problems.append(f"INDEPENDENT_AUTHORITY_REQUIRED {invariant_id}")
        if status == "SUPERSEDED" and not any(
                proof.get("kind") == "superseding_authority" for proof in evidence):
            problems.append(f"SUPERSEDING_AUTHORITY_REQUIRED {invariant_id}")
    return problems


def main() -> int:
    try:
        manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        print(f"BAMF_INVARIANT_TRANSFER_FAIL: {exc}", file=sys.stderr)
        return 1
    problems = validate(manifest)
    for problem in problems:
        print(problem)
    if problems:
        print(f"BAMF_INVARIANT_TRANSFER_FAILED violations={len(problems)}")
        return 1
    print(
        "BAMF_INVARIANT_TRANSFER_OK "
        f"entries={len(manifest['invariants'])} "
        f"authority={manifest['predecessor_authority']['commit']}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
