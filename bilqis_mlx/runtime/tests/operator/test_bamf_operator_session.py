"""C16.3 persistent BAMF operator routing contracts."""
from __future__ import annotations

import os
from contextlib import ExitStack
from pathlib import Path
from tempfile import TemporaryDirectory
from types import SimpleNamespace
import unittest
from unittest.mock import patch

from bilqis_mlx.errors import BilqisError
from bilqis_mlx.runtime.bamf_operator.session import (
    _adopt_and_activate_certified_successor, _execution_context, _visit,
    operate_bamf, prepare_bamf_visit,
)


def _evidence_receipt(bytes_written, evidence_objects, seconds):
    return {
        "schema": "bilqis.bamf.c16.3-candidate-evidence-reference/v1",
        "persistence": {
            "bytes_written": bytes_written, "file_fsyncs": 1,
            "directory_fsyncs": 1, "evidence_objects": evidence_objects,
            "persistence_seconds": seconds,
        },
    }


def _prepare_native_resource_visit(temporary):
    parent = SimpleNamespace(
        retained_state=SimpleNamespace(optimizer_step=11),
        optimizer_hyperparameters="hparams")
    context = SimpleNamespace(release=object())
    identity = SimpleNamespace(visit_id="visit:resource", policy_key="policy:resource")
    selection = SimpleNamespace(
        status="TEACHER_SELECTED", option_id="option:resource",
        visit=SimpleNamespace(identity=identity),
        offer=SimpleNamespace(
            capability_id="capability:resource", source_seed=17,
            rows=lambda: ({"id": "row:resource"},)))
    cache = SimpleNamespace(generation=1, accepted_manifest_sha256="a" * 64)
    transaction = SimpleNamespace(
        parent=SimpleNamespace(optimizer_step=11), update_steps=1,
        training_authorities=("authority",))
    step = SimpleNamespace(
        transaction=transaction,
        realized_cost={
            "wall_seconds": 30.0, "optimizer_steps": 1,
            "c08_memory_budget_bytes": 64 * 1024 ** 3})
    decision = SimpleNamespace(
        accepted=True, to_record=lambda: {"decision": "ACCEPTED"})
    retained = SimpleNamespace(optimizer_step=12)
    successor = object()
    evidence = _evidence_receipt(300, 4, 0.005)
    capture = SimpleNamespace(finalize=lambda **_kwargs: evidence)
    patches = (
        ("_execution_context", {"return_value": (parent, context, "atlas", "feature")}),
        ("schedule_program_from_executable_release", {"return_value": "program"}),
        ("accepted_priority_school", {"return_value": "school"}),
        ("select_foundation_priority_visit", {"return_value": selection}),
        ("bind_accepted_execution_cache", {"return_value": cache}),
        ("candidate_step_horizon", {"return_value": 1}),
        ("rejection_attempt_ordinals", {"return_value": (1, 1)}),
        ("_Capture", {"return_value": capture}),
        ("FactoryDeliveryObservation", {"return_value": "observation"}),
        ("execute_accepted_priority_candidate", {"return_value": step}),
        ("evaluate_factory_retention_candidate", {"return_value": SimpleNamespace(
            candidate_state=retained, parent_state=parent.retained_state)}),
        ("issue_factory_retention_decision", {"return_value": decision}),
        ("derive_accepted_teacher_successor", {"return_value": successor}),
        ("bind_factory_baseline_successor", {"return_value": successor}),
    )
    session_names = {
        "_execution_context", "schedule_program_from_executable_release",
        "accepted_priority_school", "select_foundation_priority_visit",
    }
    with ExitStack() as stack:
        handles = {}
        for name, kwargs in patches:
            owner = (
                "bilqis_mlx.runtime.bamf_operator.session."
                if name in session_names else
                "bilqis_mlx.runtime.bamf_operator.session_parts.native_session."
            )
            handles[name] = stack.enter_context(patch(owner + name, **kwargs))
        stack.enter_context(patch(
            "bilqis_mlx.runtime.bamf_operator.championship."
            "bind_accepted_championship_successor", return_value=successor))
        prepared = prepare_bamf_visit(Path(temporary), steps_per_visit=16)
    return prepared, successor, handles["derive_accepted_teacher_successor"], evidence


def _candidate_executor(transactions, case):
    def execute(*_args, candidate=None, **_kwargs):
        ordinal = len(transactions) + 1
        case.assertIsNone(candidate) if ordinal == 1 else case.assertIs(
            candidate, transactions[-1])
        transaction = SimpleNamespace(
            parent=SimpleNamespace(optimizer_step=11), update_steps=ordinal,
            training_authorities=tuple(
                f"authority-{step}" for step in range(ordinal)))
        transactions.append(transaction)
        return SimpleNamespace(
            transaction=transaction,
            realized_cost={
                "wall_seconds": float(ordinal), "optimizer_steps": 1,
                "candidate_optimizer_steps": ordinal,
                "c08_memory_budget_bytes": 64 * 1024 ** 3,
            })
    return execute


def _assert_horizon_result(
        case, prepared, execute_candidate, bind_plan, bind_rows,
        capture_factory, horizon, evaluate, decide, derive, context,
        parent, cache, selection, transactions, evidence):
    case.assertEqual(prepared.status, "ACCEPTED")
    case.assertEqual(len(prepared.steps), 4)
    case.assertEqual(prepared.step.transaction.update_steps, 4)
    case.assertEqual(execute_candidate.call_count, 4)
    bind_plan.assert_called_once_with(context, parent, cache)
    bind_rows.assert_called_once_with(context, cache, "capability:horizon")
    capture_factory.assert_called_once_with(
        Path("/run"), selection, generation=1,
        accepted_manifest_sha256="a" * 64,
        candidate_attempt_ordinal=1, parent_optimizer_step=11)
    horizon.assert_called_once_with(
        Path("/run"), parent, cache, "capability:horizon", 16)
    evaluate.assert_called_once_with(
        context, transactions[-1], "atlas", "capability:horizon",
        run_dir=Path("/run"))
    decide.assert_called_once_with(evaluate.return_value)
    event = derive.call_args.kwargs["delivery_events"][0]
    case.assertIs(prepared.resource, event["resource"])
    case.assertEqual(event["resource"]["optimizer_steps"], 4)
    case.assertEqual(event["resource"]["wall_seconds"], 10.0)
    case.assertEqual(event["visit_id"], "visit:horizon")
    case.assertEqual(event["selected_policy_key"], "policy:horizon")
    case.assertEqual(event["selected_option_id"], "option:horizon")
    case.assertEqual(event["parent_generation"], 1)
    case.assertEqual(event["accepted_manifest_sha256"], "a" * 64)
    case.assertEqual(event["candidate_attempt_ordinal"], 1)
    case.assertEqual(event["candidate_evidence"], evidence)
    case.assertEqual(event["resource"]["evidence_file_fsyncs"], 1)


class BamfOperatorRoutingTests(unittest.TestCase):
    def test_certified_successor_adopts_through_c07_before_1314_activation(self):
        context = SimpleNamespace(graph={"accepted": "graph"})
        with patch(
            "bilqis_mlx.runtime.atlas_flywheel_runtime.run_accepted_atlas_flywheel",
            return_value=SimpleNamespace(advances=1),
        ) as adopt, patch(
            "bilqis_mlx.runtime.active_generated_grade."
            "activate_certified_generated_grade",
        ) as activate:
            advanced = _adopt_and_activate_certified_successor(
                Path("/run"), context,
                certification_receipt_sha256="c" * 64,
                reserve_gib=32.0,
            )
        self.assertTrue(advanced)
        adopt.assert_called_once_with(
            Path("/run"), context.graph, reserve_gib=32.0, max_advances=1)
        activate.assert_called_once_with(
            Path("/run"), certification_receipt_sha256="c" * 64)

    def test_certified_successor_does_not_activate_without_c07_advance(self):
        context = SimpleNamespace(graph={})
        with patch(
            "bilqis_mlx.runtime.atlas_flywheel_runtime.run_accepted_atlas_flywheel",
            return_value=SimpleNamespace(advances=0),
        ), patch(
            "bilqis_mlx.runtime.active_generated_grade."
            "activate_certified_generated_grade",
        ) as activate:
            advanced = _adopt_and_activate_certified_successor(
                Path("/run"), context,
                certification_receipt_sha256="c" * 64,
                reserve_gib=32.0,
            )
        self.assertFalse(advanced)
        activate.assert_not_called()

    def test_candidate_horizon_buffers_step_evidence_until_one_boundary_write(self):
        from bilqis_mlx.factory.teaching import content_digest
        from bilqis_mlx.runtime.bamf_operator.evidence import (
            CandidateEvidenceCapture as _Capture, prepare_candidate_evidence_root,
        )

        identity = SimpleNamespace(
            visit_id="visit:evidence", policy_key="policy:evidence",
            to_record=lambda: {
                "visit_id": "visit:evidence", "policy_key": "policy:evidence"})
        selection = SimpleNamespace(
            option_id="option:evidence",
            visit=SimpleNamespace(identity=identity),
            offer=SimpleNamespace(
                capability_id="capability:evidence", source_seed=17,
                release_sha256="b" * 64),
        )
        execution = SimpleNamespace(
            provider_id="provider:evidence", provider_implementation_sha256="f" * 64,
            variation_axes=("seed",), teaching_option_ids=("option:evidence",))
        release = SimpleNamespace(
            release_sha256="b" * 64,
            execution_plan=SimpleNamespace(
                capability_map={"capability:evidence": execution}))
        row = {
            "id": "row:one", "capability": "capability:evidence",
            "tokens": [1, 2, 3],
        }
        rows = (row,)
        with TemporaryDirectory() as temporary:
            root = Path(temporary)
            prepare_candidate_evidence_root(root)
            capture = _Capture(
                root, selection, generation=3,
                accepted_manifest_sha256="a" * 64,
                candidate_attempt_ordinal=1, parent_optimizer_step=10)
            with patch(
                    "bilqis_mlx.runtime.state.os.fsync",
                    wraps=os.fsync) as fsync:
                for ordinal in range(1, 17):
                    capture.delivery(
                        release, "capability:evidence", 10 + ordinal, rows,
                        option_rows=rows, seed=ordinal,
                        controls={
                            "realized_cost": {"wall_seconds": 0.01},
                            "delivered_content_sha256": content_digest(rows),
                        },
                    )
                self.assertEqual(fsync.call_count, 0)
