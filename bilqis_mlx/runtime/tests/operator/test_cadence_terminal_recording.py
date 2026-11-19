"""#1333 terminal attempts consume cadence only after durable terminal custody."""
from contextlib import nullcontext
from types import SimpleNamespace

from bilqis_mlx.runtime.bamf_operator._session_visit import visit


def _prepared(*, accepted):
    cadence = {
        "schema": "bilqis.bamf.active-grade-cadence-authorization/v1",
        "phase": "MAIN",
        "phase_round": 0,
        "phase_sha256": "1" * 64,
        "cadence_sha256": "2" * 64,
        "active_grade_activation_sha256": "3" * 64,
        "active_grade_definition_sha256": "4" * 64,
        "member_census_sha256": "5" * 64,
        "deficit_evidence_sha256": "6" * 64,
        "policy_epoch": 1,
        "authorized_capability_ids": ["cap"],
        "disposition": "TEACHING",
    }
    identity = SimpleNamespace(
        visit_id="visit", policy_key="policy", to_record=lambda: {"visit_id": "visit"})
    selection = SimpleNamespace(
        option_id="cap", metadata={"cadence": cadence},
        visit=SimpleNamespace(identity=identity))
    step = SimpleNamespace(transaction=SimpleNamespace(
        parent=SimpleNamespace(optimizer_step=0), update_steps=1,
        training_authorities=("authority",)))
    decision = SimpleNamespace(
        accepted=accepted, reason="retention",
        to_record=lambda: {"accepted": accepted})
    successor = SimpleNamespace(extents=SimpleNamespace(factor_map_digest="f" * 64))
    return SimpleNamespace(
        status="READY", parent=SimpleNamespace(retained_state=SimpleNamespace(optimizer_step=0)),
        selection=selection, step=step, decision=decision, retained=object(),
        successor=successor, rejection_attempt_ordinal=1, rejection_journal_ordinal=1,
        capability="cap", resource={}, candidate_evidence={}, how_outcome=None,
        structural_weaknesses=())


def _run(prepared, order):
    return visit(
        "/run", 0.0, steps_per_visit=1, progress=None,
        source_prefetch_workers=0, source_prefetch_executor=None,
        source_prefetch_metrics=None, observer=None, run_authority_binding=None,
        prepare_visit=lambda *_args, **_kwargs: prepared,
        record_rejection=lambda *_args, **_kwargs: order.append("rejection"),
        accept_publish=lambda *_args, **_kwargs: order.append("publication"),
        load_generation=lambda *_args, **_kwargs: None,
        measure_phase=lambda *_args, **_kwargs: nullcontext(),
        emit_progress=lambda *_args, **_kwargs: None,
        record_cadence_attempt=lambda *_args, **_kwargs: order.append("cadence"),
    )


def test_rejected_attempt_records_cadence_after_rejection_custody():
    order = []
    assert _run(_prepared(accepted=False), order) == "REJECTED"
    assert order == ["rejection", "cadence"]


def test_accepted_attempt_records_cadence_after_successor_publication():
    order = []
    assert _run(_prepared(accepted=True), order) == "ACCEPTED"
    assert order == ["publication", "cadence"]
