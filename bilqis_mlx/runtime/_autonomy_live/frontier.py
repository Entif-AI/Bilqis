"""Source-frontier proposal helpers for a live autonomy session."""
from __future__ import annotations

from dataclasses import asdict
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys

from ..state import _durable_json


def propose_source_frontier_work(session, checkpoint, graph, source_registry):
    from ...factory.candidate_frontier import load_candidate_frontier
    from ...factory.executable_release import ExecutableFactoryRelease
    from ...factory.jit_curriculum import propose_curriculum_delta

    if not isinstance(session.release, ExecutableFactoryRelease):
        return None
    repo_root = Path(__file__).resolve().parents[3]
    builder = repo_root / "lib/ithkuil/src/build_curriculum_frontier.py"
    artifact_dir = Path(session.run_dir) / "candidate-frontier"
    source_dir = repo_root / "lib/ithkuil/_data/csv"
    if not builder.is_file():
        raise ValueError("AUTONOMY_FRONTIER_BUILDER_MISSING")
    builder_sha256 = hashlib.sha256(builder.read_bytes()).hexdigest()
    subprocess.run(
        [sys.executable, str(builder)], check=True, capture_output=True, text=True,
        env={**os.environ, "BILQIS_CURRICULUM_FRONTIER_OUT": str(artifact_dir)},
    )
    frontier = load_candidate_frontier(
        artifact_dir, source_dir, expected_builder_sha256=builder_sha256)
    from ..candidate_staging import load_staged_candidates, persist_staged_candidate

    staged = load_staged_candidates(
        session.run_dir, frontier, session.release, source_registry=source_registry)
    if graph is not None:
        from ...compatibility.source_adapter_resume import predecessor_compatible_source_registry
        from ...factory.candidate_realizations import prepare_realized_candidates
        from ...factory.live_answers import live_answer_registry
        known = {item.candidate_id for item in staged}
        staging_source_registry = predecessor_compatible_source_registry(
            session.release, source_registry)
        for item in prepare_realized_candidates(
                frontier, session.release, graph, source_root=session.source_root,
                source_registry=staging_source_registry,
                answer_registry=live_answer_registry()):
            if item.candidate_id not in known:
                persist_staged_candidate(
                    session.run_dir, item, frontier, session.release)
        staged = load_staged_candidates(
            session.run_dir, frontier, session.release,
            source_registry=source_registry)
    proposal = propose_curriculum_delta(
        frontier, session.release, session.ledger, session.plan,
        checkpoint.sha256, checkpoint.optimizer_step,
        candidate_bindings=tuple(item.binding for item in staged))
    proposal_dir = session.run_dir / "autonomy" / "jit-proposals"
    if proposal_dir.is_symlink():
        raise ValueError("AUTONOMY_JIT_PROPOSAL_DIRECTORY_UNSAFE")
    relative = Path("autonomy") / "jit-proposals" / (
        proposal.proposal_sha256 + ".json")
    path = session.run_dir / relative
    if path.is_symlink():
        raise ValueError("AUTONOMY_JIT_PROPOSAL_PATH_UNSAFE")
    payload = json.loads(json.dumps(
        asdict(proposal), sort_keys=True, ensure_ascii=False, allow_nan=False))
    if path.exists():
        if (not path.is_file() or
                json.loads(path.read_text(encoding="utf-8")) != payload):
            raise ValueError("AUTONOMY_JIT_PROPOSAL_IMMUTABLE_DRIFT")
    else:
        _durable_json(path, payload)
    if json.loads(path.read_text(encoding="utf-8")) != payload:
        raise ValueError("AUTONOMY_JIT_PROPOSAL_READBACK_DRIFT")
    if proposal.disposition.value == "SOURCE_DEVELOPMENT":
        from ..source_development import prepare_source_frontier, persist_source_development
        result = prepare_source_frontier(repo_root)
        persist_source_development(
            session.run_dir, result, proposal=proposal, checkpoint=checkpoint)
    return proposal, relative.as_posix()


def resolve_ready_proposal(session, checkpoint, proposal, source_registry):
    from ...factory.candidate_frontier import load_candidate_frontier
    from ..candidate_staging import load_staged_candidates
    from ..jit_adoption import resolve_ready_candidate

    root = Path(__file__).resolve().parents[3]
    builder = root / "lib/ithkuil/src/build_curriculum_frontier.py"
    artifact_dir = Path(session.run_dir) / "candidate-frontier"
    subprocess.run(
        [sys.executable, str(builder)], check=True, capture_output=True, text=True,
        env={**os.environ, "BILQIS_CURRICULUM_FRONTIER_OUT": str(artifact_dir)},
    )
    frontier = load_candidate_frontier(
        artifact_dir,
        root / "lib/ithkuil/_data/csv",
        expected_builder_sha256=hashlib.sha256(builder.read_bytes()).hexdigest())
    return resolve_ready_candidate(
        frontier, session.release, session.ledger, session.plan,
        checkpoint, proposal,
        load_staged_candidates(
            session.run_dir, frontier, session.release,
            source_registry=source_registry))
