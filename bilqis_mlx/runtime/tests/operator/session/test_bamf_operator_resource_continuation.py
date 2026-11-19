"""Native visit coordination after a provisional candidate resource failure."""
from contextlib import nullcontext
from functools import partial
from types import SimpleNamespace
from unittest.mock import Mock

import pytest

from bilqis_mlx.runtime.atlas_memory_retry import RESOURCE_REJECTION_SCHEMA
from bilqis_mlx.runtime.bamf_operator._session_execution import _run_visits
from bilqis_mlx.runtime.bamf_operator._session_visit import visit
from bilqis_mlx.runtime.bamf_operator.session_parts.stop_receipt import _resume_state
from bilqis_mlx.runtime.bamf_operator.session_support import BamfPreparedVisit


@pytest.mark.parametrize("has_peer", (True, False))
def test_resource_rejection_returns_to_scheduler_without_learner_feedback(tmp_path, has_peer):
    parent = object()
    identity = SimpleNamespace(
        visit_id="visit:failed", policy_key="policy",
        to_record=lambda: {"visit_id": "visit:failed"})
    failed = BamfPreparedVisit(
        "RESOURCE_REJECTED", parent,
        selection=SimpleNamespace(visit=SimpleNamespace(identity=identity)),
        capability="failed",
        resource={"schema": RESOURCE_REJECTION_SCHEMA, "status": "EXHAUSTED"})
    peer = BamfPreparedVisit(
        "READY", parent, selection=SimpleNamespace(metadata={}),
        decision=SimpleNamespace(accepted=True), successor=SimpleNamespace(
            extents=SimpleNamespace(factor_map_digest="feature")),
        step=SimpleNamespace(transaction=SimpleNamespace(training_authorities=())))
    prepare = Mock(side_effect=(
        failed, peer if has_peer else BamfPreparedVisit("RESOURCE_HOLD", parent)))
    journal, publish, cadence = Mock(), Mock(), Mock()
    authority = SimpleNamespace(assert_current=Mock())
    disk = Mock(return_value={"sufficient": True})
    observer = SimpleNamespace(finish=Mock(), update=Mock())
    outcome = _run_visits(
        tmp_path, deadline=100, max_visits=1, steps_per_visit=1, reserve_gib=100,
        source_prefetch_workers=0, progress=None, source_prefetch_executor=None,
        metrics=None, run_authority_binding=authority, resource_snapshot=disk,
        monotonic=lambda: 0, observer_type=lambda *_: nullcontext(observer),
        emit_progress=lambda *_: None,
        visit_fn=partial(
            visit, prepare_visit=prepare, record_rejection=journal, accept_publish=publish,
            load_generation=None, measure_phase=lambda *_: nullcontext(),
            emit_progress=lambda *_: None, record_cadence_attempt=cadence))

    assert prepare.call_count == 2
    assert prepare.call_args.kwargs["resource_holds"] == frozenset({"failed"})
    assert disk.call_count == 2
    journal.assert_called_once_with(tmp_path, parent, {
        "schema": RESOURCE_REJECTION_SCHEMA,
        "status": "EXHAUSTED",
        "capability": "failed",
        "visit_id": "visit:failed",
        "teacher_visit": {"visit_id": "visit:failed"},
        "selected_policy_key": "policy",
    })
    cadence.assert_not_called()
    if has_peer:
        assert outcome[:4] == ("VISIT_LIMIT", 1, 1, 0)
        publish.assert_called_once()
    else:
        assert outcome[:4] == ("RESOURCE_HOLD", 0, 0, 0)
        publish.assert_not_called()
        assert _resume_state("RESOURCE_HOLD") == (True, "RESUME_AFTER_RESOURCE_RECOVERY")
