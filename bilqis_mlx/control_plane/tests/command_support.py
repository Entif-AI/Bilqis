"""Shared CP05 test fixtures with no production-side shortcuts."""
from __future__ import annotations

from pathlib import Path

from bilqis_mlx.mission_control.model import (
    AuthorityClass, CoverageState, RecordMeta,
)
from bilqis_mlx.mission_control.operator import (
    ActionParameter, OperatorActionRequestV2,
)

from bilqis_mlx.control_plane.command.model import (
    CommandAction, CommandMode, CommandPlan, ResolvedCommandTarget,
    intent_sha256, request_sha256,
)


DIGESTS = tuple(char * 64 for char in "1234567")


def meta(name: str, materialized_at: int = 100) -> RecordMeta:
    return RecordMeta(
        record_id=name,
        run=None,
        materialized_at=materialized_at,
        observed_at=materialized_at,
        as_of=materialized_at,
        coverage=CoverageState.COMPLETE,
        authority=AuthorityClass.DERIVED,
    )


def request(
    *, request_id: str = "request-1", idempotency_key: str = "idem-1",
    action: str = "create", dry_run: bool = True,
    human_authorized: bool = False,
    parameters: tuple[ActionParameter, ...] = (),
    requested_at: int = 100,
) -> OperatorActionRequestV2:
    return OperatorActionRequestV2(
        meta(f"request:{request_id}", requested_at),
        request_id,
        idempotency_key,
        action,
        parameters,
        dry_run,
        human_authorized,
        requested_at,
    )


def target(run_dir: Path) -> ResolvedCommandTarget:
    return ResolvedCommandTarget(
        run_dir=str(run_dir.resolve()),
        run_id="fixture-run",
        run_seed=7,
        run_identity_sha256=DIGESTS[0],
        generation=0,
        generation_manifest_sha256=DIGESTS[1],
        optimizer_step=0,
        candidate_identity_sha256=DIGESTS[2],
        factory_release_sha256=DIGESTS[3],
        semantic_release_sha256=DIGESTS[4],
        topology_sha256=DIGESTS[5],
        acceptance_sha256=DIGESTS[6],
        source_identity="source:fixture",
    )


class FakeExecutor:
    def __init__(self, run_dir: Path, mode: CommandMode):
        self.run_dir = run_dir
        self.mode = mode
        self.preflight_calls = 0
        self.execute_calls = 0
        self.verify_calls = 0
        self.reconcile_value = None
        self.preflight_error = None
        self.verify_error = None
        self.execute_result = (0, None)

    def preflight(self, action_request, operation_id):
        self.preflight_calls += 1
        if self.preflight_error is not None:
            raise self.preflight_error
        plan = CommandPlan(
            operation_id=operation_id,
            request_sha256=request_sha256(action_request),
            intent_sha256=intent_sha256(action_request),
            action=CommandAction(action_request.action),
            mode=self.mode,
            target=target(self.run_dir),
            argv=(
                ("train", "--human-run")
                if self.mode is CommandMode.MUTATING
                else ()
            ),
            postcondition_kind="fixture-postcondition",
        )
        return plan, {
            "kind": "fixture-preflight",
            "target": plan.target.to_record(),
        }

    def preview(self, action_request, operation_id):
        return self.preflight(action_request, operation_id)

    def inert_postcondition(self, plan, preflight):
        return {"kind": "fixture-inert", "target": plan.target.to_record()}

    def verify_target_before_execute(self, plan):
        self.verify_calls += 1
        if self.verify_error is not None:
            raise self.verify_error

    def execute(self, plan, *, stdout_path, stderr_path):
        self.execute_calls += 1
        stdout_path.write_text("fixture stdout\n")
        stderr_path.write_text("fixture stderr\n")
        return self.execute_result

    def postcondition_after_success(self, plan):
        return {"kind": "fixture-completed", "target": plan.target.to_record()}

    def reconcile(self, plan):
        return self.reconcile_value


class Launcher:
    def __init__(self, *, pid: int = 99_999_999, error: Exception | None = None):
        self.pid = pid
        self.error = error
        self.calls = []

    def __call__(self, operation_id):
        self.calls.append(operation_id)
        if self.error is not None:
            raise self.error
        return self.pid
