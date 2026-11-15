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
)
from bilqis_mlx.semantics.domains import contract_digest


def _fixture(capability="capability:prefetch", *, visit="visit:prefetch"):
    rows = ({"id": capability, "capability": capability, "gold": "TRUE"},)
    offer = SimpleNamespace(
        accepted_manifest_sha256="a" * 64,
        generation_binding="b" * 64,
        release_sha256="c" * 64,
        capability_id=capability,
        source_seed=17,
        source_each=1,
        source_family_id="family:" + capability,
        source_binding_digest="d" * 64,
        source_authority=SimpleNamespace(
            content_sha256=source_content_digest(rows)),
        rows=lambda: rows,
    )
    selection = SimpleNamespace(
        offer=offer, visit=SimpleNamespace(
            identity=SimpleNamespace(visit_id=visit)))
    context = SimpleNamespace(
        source_root=Path("/source"), graph={"tokens": []},
        release=SimpleNamespace(release_sha256="c" * 64))
    parent = SimpleNamespace(retained_state=SimpleNamespace(optimizer_step=41))
    return selection, context, parent


def _packet(request):
    return freeze_source_packet({
        "schema": SCHEMA,
        "identity": request["identity"],
        "fresh": [{"id": request["capability"], "gold": "TRUE"}],
        "prior": [],
        "preservation": [],
        "retention_support": [],
        "teaching_enrichment_rows": [],
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


@pytest.mark.parametrize("capability", [
    "A.IDENTITY", "A.PARENT", "A.LINK",
    "A.MEMBER", "A.EDGE", "A.MAPS",
])
def test_live_grade_a_rows_survive_immutable_packet_roundtrip_without_content_drift(capability):
    from bilqis_mlx.grade_a_probe import read_sources
    from bilqis_mlx.live_grade_a import draw_predicates

    source_root = Path(__file__).resolve().parents[4] / "vendor" / "legacy-v16"
    graph = read_sources(source_root)[2]
    rows = list(draw_predicates(
        source_root, graph, seed=31, capability=capability, each=4))
    selection, context, parent = _fixture(capability)
    selection.offer.source_each = len(rows)
    selection.offer.source_authority = SimpleNamespace(
        content_sha256=source_content_digest(rows))
    selection.offer.rows = lambda: tuple(rows)
    request = priority_source_request(selection, context, parent, 1)
    packet = freeze_source_packet({
        "schema": SCHEMA,
        "identity": request["identity"],
        "fresh": rows,
        "prior": [],
        "preservation": [],
        "retention_support": [],
        "teaching_enrichment_rows": [],
    })
    lane = CandidateSourceLane(
        selection, context, parent, 1, workers=0, executor=None,
        metrics=SourcePrefetchMetrics())
    with patch(
            "bilqis_mlx.runtime.bamf_operator.source_prefetch.prepare_priority_source_packet",
            return_value=packet):
        roundtripped = lane.rows(1)
    assert roundtripped == tuple(rows)
    assert source_content_digest(roundtripped) == source_content_digest(rows)


def test_native_worker_transports_issued_content_without_redrawing_provider():
    from bilqis_mlx.factory.tests.lifecycle.test_teaching import closed_source_fixture

    _course, graph, sources, answers, release = closed_source_fixture()
    context = SourceExecutionContext(
        release, graph, None, sources, answers)
    capability = "Z.C0"
    seed = 17
    rows, authority = context.draw_bound_rows(
        seed=seed, capability=capability, each=1)
    selection, _fixture_context, parent = _fixture(capability)
    selection.offer.release_sha256 = release.release_sha256
    selection.offer.source_seed = seed
    selection.offer.source_family_id = authority.source_family_id
    selection.offer.source_authority = authority
    selection.offer.rows = lambda: tuple(rows)
    selection.offer.source_binding_digest = contract_digest(
        release.source_bindings.by_capability[capability])
    source_context = SimpleNamespace(
        source_root=None, graph=graph, release=release)
    request = priority_source_request(selection, source_context, parent, 1)

    with patch.object(
            SourceExecutionContext, "draw_rows",
            side_effect=AssertionError("provider redraw forbidden")):
        packet = prepare_priority_source_packet(request)

    assert packet.identity == request["identity"]
    lane = CandidateSourceLane(
        selection, source_context, parent, 1, workers=0, executor=None,
        metrics=SourcePrefetchMetrics())
    with patch(
            "bilqis_mlx.runtime.bamf_operator.source_prefetch.prepare_priority_source_packet",
            return_value=packet):
        assert lane.rows(1) == tuple(rows)


def test_sixteen_step_horizon_reuses_one_source_draw_and_one_content_identity():
    from bilqis_mlx.factory import generation
    from bilqis_mlx.factory.tests.lifecycle.test_teaching import closed_source_fixture

    _course, graph, sources, answers, release = closed_source_fixture()
    context = SourceExecutionContext(release, graph, None, sources, answers)
    capability, seed, each = "Z.C0", 17, 1
    rows, authority = context.draw_bound_rows(
        seed=seed, capability=capability, each=each)
    selection, _fixture_context, parent = _fixture(capability)
    selection.offer.release_sha256 = release.release_sha256
    selection.offer.source_seed = seed
    selection.offer.source_each = each
    selection.offer.source_family_id = authority.source_family_id
    selection.offer.source_binding_digest = contract_digest(
        release.source_bindings.by_capability[capability])
    selection.offer.source_authority = authority
    selection.offer.rows = lambda: tuple(rows)
    source_context = SimpleNamespace(release=release)
    requests = tuple(
        priority_source_request(selection, source_context, parent, ordinal)
        for ordinal in range(1, 17))
    assert len({request["identity"] for request in requests}) == 16
    assert len({request["content_identity"] for request in requests}) == 1

    metrics = SourcePrefetchMetrics()
    lane = CandidateSourceLane(
        selection, source_context, parent, 16, workers=0, executor=None,
        metrics=metrics)
    with patch.object(
            generation, "draw_executable_release_rows",
            side_effect=AssertionError("candidate horizon redrew source provider")):
        delivered = tuple(lane.rows(ordinal) for ordinal in range(1, 17))
    assert all(item == tuple(rows) for item in delivered)
    assert context._source_preparation_metrics.provider_draws == 1
    assert metrics.serial_steps == 16


def test_spawned_native_prefetch_preserves_real_a_identity_source_content():
    import json
    from bilqis_mlx.factory.curriculum_definition import from_legacy_course
    from bilqis_mlx.factory.executable_release import compile_executable_factory_release
    from bilqis_mlx.factory.execution import CurriculumProfile
    from bilqis_mlx.factory.live_answers import live_answer_registry
    from bilqis_mlx.grade_a_probe import read_sources
    from bilqis_mlx.grade_a_release import accepted_grade_a
    from bilqis_mlx.live_grade_a import live_course as initial_course
    from bilqis_mlx.source_adapters.school import live_source_registry

    root = Path(__file__).resolve().parents[4]
    source_root = root / "vendor" / "legacy-v16"
    graph = read_sources(source_root)[2]
    manifest = json.loads((
        root / "docs/provenance/GRADE_A_CANDIDATE_MANIFEST_V2.json").read_text())
    curriculum, bindings = from_legacy_course(initial_course(accepted_grade_a(manifest)))
    sources, answers = live_source_registry(), live_answer_registry()
    release = compile_executable_factory_release(
        curriculum, bindings, CurriculumProfile.full(), sources, answers,
        source_root=source_root, graph=graph, verification_seed=31)
    context = SourceExecutionContext(release, graph, source_root, sources, answers)
    capability, seed, each = "A.IDENTITY", 31, 4
    rows, authority = context.draw_bound_rows(
        seed=seed, capability=capability, each=each)
    selection, _fixture_context, parent = _fixture(capability)
    selection.offer.release_sha256 = release.release_sha256
    selection.offer.source_seed = seed
    selection.offer.source_each = each
    selection.offer.source_family_id = authority.source_family_id
    selection.offer.source_authority = authority
    selection.offer.rows = lambda: tuple(rows)
    selection.offer.source_binding_digest = contract_digest(
        release.source_bindings.by_capability[capability])
    source_context = SimpleNamespace(
        source_root=source_root, graph=graph, release=release)
    with source_prefetch_pool(1) as executor:
        lane = CandidateSourceLane(
            selection, source_context, parent, 1, workers=1, executor=executor,
            metrics=SourcePrefetchMetrics())
        prepared = lane.rows(1)
    assert prepared == tuple(rows)
    assert context.bind_rows(
        prepared, seed=seed, capability=capability, each=each) == authority


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
