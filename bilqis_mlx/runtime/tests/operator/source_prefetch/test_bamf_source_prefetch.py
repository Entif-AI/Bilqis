"""#1174 native operator source-prefetch contracts."""
from concurrent.futures import ThreadPoolExecutor
from contextlib import contextmanager
from pathlib import Path
from tempfile import TemporaryDirectory
from types import SimpleNamespace
import time
from unittest.mock import patch

import pytest

from bilqis_mlx.errors import BilqisError
from bilqis_mlx.runtime.bamf_operator.session import operate_bamf
from bilqis_mlx.runtime.bamf_operator.source_prefetch import (
    CandidateSourceLane,
    SourcePrefetchMetrics,
    prepare_priority_source_packet,
    priority_source_request,
)
from bilqis_mlx.runtime.source_execution import SourceExecutionContext
from bilqis_mlx.runtime.source_execution import source_content_digest
from bilqis_mlx.runtime.source_prefetch import (
    FORBIDDEN_AUTHORITY_KEYS,
    SCHEMA,
    freeze_source_packet,
    source_prefetch_pool,
    thaw_source_packet,
)
from bilqis_mlx.semantics.domains import contract_digest


def _fixture(capability="capability:prefetch", *, visit="visit:prefetch"):
    rows = ({"id": capability, "capability": capability, "gold": "TRUE"},)
    source_binding = {"capability": capability, "provider": "fixture"}
    offer = SimpleNamespace(
        accepted_manifest_sha256="a" * 64,
        generation_binding="b" * 64,
        release_sha256="c" * 64,
        capability_id=capability,
        source_seed=17,
        source_each=1,
        source_family_id="family:" + capability,
        source_binding_digest=contract_digest(source_binding),
        source_authority=SimpleNamespace(
            content_sha256=source_content_digest(rows)),
        rows=lambda: rows,
    )
    selection = SimpleNamespace(
        offer=offer, visit=SimpleNamespace(
            identity=SimpleNamespace(visit_id=visit)))
    context = SimpleNamespace(
        source_root=Path("/source"), graph={"tokens": []},
        release=SimpleNamespace(
            release_sha256="c" * 64,
            source_bindings=SimpleNamespace(by_capability={capability: source_binding})))
    parent = SimpleNamespace(retained_state=SimpleNamespace(optimizer_step=41))
    return selection, context, parent


def _packet(request, enrichment=()):
    return freeze_source_packet({
        "schema": SCHEMA,
        "identity": request["identity"],
        "fresh": list(request["source_rows"]),
        "prior": [],
        "preservation": [],
        "retention_support": [],
        "teaching_enrichment_rows": list(enrichment),
    })


def test_candidate_identity_binds_visit_step_and_source_authority_without_mutable_owners():
    selection, context, parent = _fixture()
    first = priority_source_request(selection, context, parent, 1)
    second = priority_source_request(selection, context, parent, 2)
    other_selection, _, _ = _fixture("capability:other")
    other = priority_source_request(other_selection, context, parent, 1)

    assert first["identity"] != second["identity"]
    assert first["identity"] != other["identity"]
    assert first["content_identity"] == second["content_identity"]
    assert first["source_content_sha256"] == second["source_content_sha256"]
    assert FORBIDDEN_AUTHORITY_KEYS.isdisjoint(first)
    assert "teacher" not in first
    assert "scheduler" not in first
    assert first["parent_optimizer_step"] == 41
    contaminated = {**first, "model_state": "forbidden"}
    with pytest.raises(BilqisError) as failure:
        prepare_priority_source_packet(contaminated)
    assert failure.value.context["reason"] == "BAMF_SOURCE_PREFETCH_REQUEST_INVALID"


def test_native_packet_carries_issued_factory_teaching_enrichment():
    selection, context, parent = _fixture("Z.C0")
    enrichment = ({"id": "z-enrichment", "capability": "Z.C0", "gold": "TRUE"},)
    request = priority_source_request(
        selection, context, parent, 1, enrichment_rows=enrichment)
    payload = thaw_source_packet(prepare_priority_source_packet(request))

    assert payload["teaching_enrichment_rows"] == list(enrichment)


def test_native_packet_rejects_enrichment_drift_before_delivery():
    selection, context, parent = _fixture("Z.C0")
    enrichment = ({"id": "z-enrichment", "capability": "Z.C0", "gold": "TRUE"},)
    request = priority_source_request(
        selection, context, parent, 1, enrichment_rows=enrichment)
    request["teaching_enrichment_rows"] = [
        {"id": "drift", "capability": "Z.C0", "gold": "TRUE"}]
    with pytest.raises(BilqisError) as failure:
        prepare_priority_source_packet(request)
    assert failure.value.context["reason"] == "BAMF_SOURCE_PREFETCH_ENRICHMENT_DRIFT"


def test_serial_and_prefetched_lanes_consume_the_same_exact_packet_identity_and_rows():
    selection, context, parent = _fixture()
    serial_requests = []

    def serial_prepare(request):
        serial_requests.append(request)
        return _packet(request)

    serial_metrics = SourcePrefetchMetrics()
    serial = CandidateSourceLane(
        selection, context, parent, 2, workers=0, executor=None,
        metrics=serial_metrics)
    with patch(
            "bilqis_mlx.runtime.bamf_operator.source_prefetch.prepare_priority_source_packet",
            side_effect=serial_prepare):
        serial_rows = (serial.rows(1), serial.rows(2))

    prefetched_requests = []

    def prefetched_prepare(request):
        prefetched_requests.append(request)
        return _packet(request)

    prefetch_metrics = SourcePrefetchMetrics()
    with ThreadPoolExecutor(max_workers=2) as executor, patch(
            "bilqis_mlx.runtime.bamf_operator.source_prefetch.prepare_priority_source_packet",
            side_effect=prefetched_prepare):
        prefetched = CandidateSourceLane(
            selection, context, parent, 2, workers=2, executor=executor,
            metrics=prefetch_metrics)
        prefetched_rows = (prefetched.rows(1), prefetched.rows(2))

    assert prefetched_rows == serial_rows
    assert sorted(serial_requests, key=lambda item: item["candidate_step"]) == sorted(
        prefetched_requests, key=lambda item: item["candidate_step"])
    assert len({item["content_identity"] for item in serial_requests}) == 1
    assert serial_metrics.serial_steps == 2
    assert prefetch_metrics.submitted_steps == 2
    assert prefetch_metrics.prepared_steps == 2


def test_source_lane_keeps_factory_enrichment_role_separate_from_direct_rows():
    selection, context, parent = _fixture("Z.C0")
    enrichment = ({"id": "z-extra", "capability": "Z.C0", "gold": "TRUE"},)

    with patch(
            "bilqis_mlx.runtime.bamf_operator.source_prefetch.prepare_priority_source_packet",
            side_effect=lambda request: _packet(request, enrichment)):
        lane = CandidateSourceLane(
            selection, context, parent, 1, workers=0, executor=None,
            metrics=SourcePrefetchMetrics())
        lesson = lane.lesson(1)

    assert lesson.direct == selection.offer.rows()
    assert lesson.enrichment == enrichment
    assert lesson.delivered == (*selection.offer.rows(), *enrichment)


def test_wrong_step_or_candidate_packet_fails_before_candidate_use():
    selection, context, parent = _fixture()
    wrong_selection, _, _ = _fixture("capability:wrong", visit="visit:wrong")
    wrong_request = priority_source_request(wrong_selection, context, parent, 1)
    wrong_packet = _packet(wrong_request)

    with ThreadPoolExecutor(max_workers=1) as executor, patch(
            "bilqis_mlx.runtime.bamf_operator.source_prefetch.prepare_priority_source_packet",
            return_value=wrong_packet):
        lane = CandidateSourceLane(
            selection, context, parent, 1, workers=1, executor=executor,
            metrics=SourcePrefetchMetrics())
        with pytest.raises(BilqisError) as failure:
            lane.rows(1)
    assert failure.value.context["reason"] == "BAMF_SOURCE_PREFETCH_PACKET_IDENTITY_DRIFT"


def test_prefetch_overlap_reduces_sovereign_lane_source_wait():
    selection, context, parent = _fixture()

    def slow_prepare(request):
        time.sleep(0.04)
        return _packet(request)

    serial_metrics = SourcePrefetchMetrics()
    with patch(
            "bilqis_mlx.runtime.bamf_operator.source_prefetch.prepare_priority_source_packet",
            side_effect=slow_prepare):
        serial = CandidateSourceLane(
            selection, context, parent, 2, workers=0, executor=None,
            metrics=serial_metrics)
        serial.rows(1)
        time.sleep(0.06)  # representative sovereign neural work
        serial.rows(2)

    prefetch_metrics = SourcePrefetchMetrics()
    with ThreadPoolExecutor(max_workers=1) as executor, patch(
            "bilqis_mlx.runtime.bamf_operator.source_prefetch.prepare_priority_source_packet",
            side_effect=slow_prepare):
        prefetched = CandidateSourceLane(
            selection, context, parent, 2, workers=1, executor=executor,
            metrics=prefetch_metrics)
        prefetched.rows(1)
        time.sleep(0.06)  # step 2 source work overlaps this sovereign work
        prefetched.rows(2)

    assert prefetch_metrics.wait_seconds < serial_metrics.wait_seconds * 0.75
    assert prefetch_metrics.overlap_seconds >= 0.04


@pytest.mark.parametrize("workers", [0, 1, 2])
def test_native_operator_preserves_zero_one_two_worker_configuration(workers):
    current = SimpleNamespace(
        generation=3, retained_state=SimpleNamespace(optimizer_step=7))
    created = []
    executors = {}

    @contextmanager
    def pool(count):
        created.append(count)
        executor = object()
        executors[count] = executor
        yield executor

    with TemporaryDirectory() as temporary, patch(
            "bilqis_mlx.runtime.source_prefetch.source_prefetch_pool",
            side_effect=pool), patch(
            "bilqis_mlx.runtime.bamf_operator.session._visit",
            return_value="HELD") as visit, patch(
            "bilqis_mlx.runtime.bamf_operator.session.load_accepted_generation",
            return_value=current):
        result = operate_bamf(
            temporary, minutes=1, max_visits=1, reserve_gib=0.0,
            source_prefetch_workers=workers)

    assert result.source_prefetch_workers == workers
    assert created == ([] if workers == 0 else [workers])
    assert visit.call_args.kwargs["source_prefetch_workers"] == workers
    assert visit.call_args.kwargs["source_prefetch_executor"] is (
        None if workers == 0 else executors[workers])
