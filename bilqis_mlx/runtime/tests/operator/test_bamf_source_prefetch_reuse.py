"""Immutable-content reuse witnesses for BAMF native source prefetch."""
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

import pytest

from bilqis_mlx.runtime.bamf_operator.source_prefetch import (
    CandidateSourceLane, SourcePrefetchMetrics, prepare_priority_source_packet,
    priority_source_request,
)
from bilqis_mlx.runtime.source_execution import (
    SourceExecutionContext, source_content_digest,
)
from bilqis_mlx.runtime.source_prefetch import (
    SCHEMA, freeze_source_packet, source_prefetch_pool,
)
from bilqis_mlx.semantics.domains import contract_digest

from .test_bamf_source_prefetch import _fixture


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
    context = SourceExecutionContext(release, graph, None, sources, answers)
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
