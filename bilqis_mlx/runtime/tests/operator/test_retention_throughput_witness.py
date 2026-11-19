"""Disposable #1165 witness: fixed optimizer work, fewer C05 certifications."""
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

from bilqis_mlx.runtime.bamf_operator.session import prepare_bamf_visit


def _selection():
    identity = SimpleNamespace(visit_id="visit:throughput", policy_key="policy:throughput")
    return SimpleNamespace(
        status="TEACHER_SELECTED",
        visit=SimpleNamespace(identity=identity),
        offer=SimpleNamespace(
            capability_id="capability:throughput", source_seed=17,
            rows=lambda: ({"id": "row:throughput"},),
        ),
    )


def _fixture():
    parent = SimpleNamespace(
        retained_state=SimpleNamespace(optimizer_step=0),
        optimizer_hyperparameters="hparams",
    )
    context = SimpleNamespace(release=object())
    evaluation = SimpleNamespace(
        candidate_state=object(), parent_state=parent.retained_state)
    decision = SimpleNamespace(
        accepted=False, to_record=lambda: {"decision": "REJECTED"})
    cache = SimpleNamespace(generation=1, accepted_manifest_sha256="a" * 64)
    capture = SimpleNamespace(finalize=lambda **_kwargs: {
        "schema": "bilqis.bamf.c16.3-candidate-evidence-reference/v1",
        "persistence": {
            "bytes_written": 1, "file_fsyncs": 1,
            "directory_fsyncs": 1, "evidence_objects": 1,
            "persistence_seconds": 0.0,
        },
    })
    return parent, context, evaluation, decision, cache, capture


def _run_fixed_optimizer_steps(horizon: int, *, total_steps: int = 16):
    assert total_steps % horizon == 0
    parent, context, evaluation, decision, cache, capture = _fixture()
    selection = _selection()
    decisions = 0
    optimizer_steps = 0

    for _ in range(total_steps // horizon):
        transactions = []

        def execute(*_args, candidate=None, **_kwargs):
            ordinal = len(transactions) + 1
            if ordinal == 1:
                assert candidate is None
            else:
                assert candidate is transactions[-1]
            transaction = SimpleNamespace(
                parent=SimpleNamespace(optimizer_step=0),
                update_steps=ordinal,
                training_authorities=tuple(range(ordinal)),
                motif_transition=None,
            )
            transactions.append(transaction)
            return SimpleNamespace(
                transaction=transaction,
                realized_cost={
                    "wall_seconds": 1.0,
                    "optimizer_steps": 1,
                    "candidate_optimizer_steps": ordinal,
                    "c08_memory_budget_bytes": 1,
                },
            )

        with patch(
                "bilqis_mlx.runtime.championship_advisers.prepare_championship_adviser_pool",
                return_value=None), patch(
                "bilqis_mlx.runtime.bamf_operator.session._execution_context",
                return_value=(parent, context, "atlas", "feature")), patch(
                "bilqis_mlx.runtime.bamf_operator.session.schedule_program_from_executable_release",
                return_value="program"), patch(
                "bilqis_mlx.runtime.bamf_operator.session.accepted_priority_school",
                return_value="school"), patch(
                "bilqis_mlx.runtime.bamf_operator.session.select_foundation_priority_visit",
                return_value=selection), patch(
                "bilqis_mlx.runtime.bamf_operator.session_parts.native_session.bind_accepted_execution_cache",
                return_value=cache), patch(
                "bilqis_mlx.runtime.bamf_operator.session_parts.native_session.candidate_step_horizon",
                return_value=horizon), patch(
                "bilqis_mlx.runtime.bamf_operator.session_parts.native_session.rejection_attempt_ordinals",
                return_value=(1, 1)), patch(
                "bilqis_mlx.runtime.bamf_operator.session_parts.native_session.prepare_candidate_evidence_root"), patch(
                "bilqis_mlx.runtime.bamf_operator.session_parts.native_session._Capture",
                return_value=capture), patch(
                "bilqis_mlx.runtime.bamf_operator.session_parts.native_session.FactoryDeliveryObservation",
                return_value="observation"), patch(
                "bilqis_mlx.runtime.bamf_operator.session_parts.native_session.execute_accepted_priority_candidate",
                side_effect=execute), patch(
                "bilqis_mlx.runtime.bamf_operator.session_parts.native_session.evaluate_factory_retention_candidate",
                return_value=evaluation) as evaluate, patch(
                "bilqis_mlx.runtime.bamf_operator.session_parts.native_session.issue_factory_retention_decision",
                return_value=decision) as certify, patch(
                    "bilqis_mlx.runtime.outcomes.issuance.build_outcome",
                    return_value={}):
            prepared = prepare_bamf_visit(Path("/tmp"), steps_per_visit=horizon)
        assert prepared.status == "REJECTED"
        assert prepared.step.transaction.update_steps == horizon
        assert evaluate.call_count == 1
        assert certify.call_count == 1
        optimizer_steps += prepared.step.transaction.update_steps
        decisions += certify.call_count
    return optimizer_steps, decisions


def test_fixed_sixteen_step_witness_reduces_c05_decisions_without_changing_gate_owner():
    one_step = _run_fixed_optimizer_steps(1)
    four_step = _run_fixed_optimizer_steps(4)
    assert one_step == (16, 16)
    assert four_step == (16, 4)
    assert four_step[1] * 4 == one_step[1]
