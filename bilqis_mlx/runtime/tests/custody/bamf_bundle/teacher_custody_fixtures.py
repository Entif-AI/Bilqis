"""Shared deterministic C03 teacher fixtures for custody integration tests."""
from bilqis_mlx.learning.teacher_lineage import adaptation_authority_ref
from bilqis_mlx.learning.tests.teacher_strategy.support import teacher_fixture


def adaptation():
    record = {
        "schema": "bilqis.bamf.legacy-trainer-authority/v1",
        "version": "1.0.0",
        "effective_date": "2026-11-07",
        "purpose": "latest legacy trainer adaptation and compatibility oracle",
        "source_branch": "codex/337-replay-349-20261026",
        "source_worktree": "/preserved/replay",
        "source_run": "/preserved/replay/run",
        "source_state": "/preserved/replay/run/state.json",
        "operator_preflight": "python3 -B scripts/check_legacy_trainer_authority.py --live",
        "historical_non_authoritative_runs": [],
    }
    return adaptation_authority_ref(record, observed_source_head="d" * 40)


def selection_teacher():
    teacher, _strong, _weak = teacher_fixture()
    teacher["events"] = 100
    teacher["global_stats"] = {
        key: {"trials": 10, "reward_sum": index, "reward_ema": index}
        for index, key in enumerate(teacher["strategies"])
    }
    teacher["grade_stats"] = {}
    return teacher
