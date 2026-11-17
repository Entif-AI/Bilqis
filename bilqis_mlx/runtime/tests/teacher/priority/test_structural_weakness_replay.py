"""R13 currentness and fresh-equivalent structural weakness proofs."""
from dataclasses import replace
from pathlib import Path
from types import SimpleNamespace

from bilqis_mlx.factory.adapters import (
    RegisteredSourceAdapter, SourceAdapterRegistry,
)
from bilqis_mlx.factory.model import SourceAdapter
from bilqis_mlx.factory._model.weakness import classify_weakness
from bilqis_mlx.runtime.accepted_priority_visit_contracts import (
    _issue_result,
)
from bilqis_mlx.runtime import structural_weakness_replay as weakness_replay
from bilqis_mlx.runtime.priority_rejection_projection import RejectionProjection


CAPABILITY = "Z.NOVEL"
PROVIDER = "source.future-z/v1"
IMPLEMENTATION = "a" * 64


def _frontier(*, policy_epoch=7, capability=CAPABILITY):
    return SimpleNamespace(
        ready_capability_ids=(capability,),
        active_grade_activation_sha256="1" * 64,
        active_grade_definition_sha256="2" * 64,
        policy_epoch=policy_epoch,
        rights_epoch=3,
        correction_generation=4,
        source_authority_registry_sha256="5" * 64,
        exclusions=(),
    )


def _selection(*, policy_epoch=7, rubric="d", capability=CAPABILITY):
    identity = SimpleNamespace(
        capability_id=capability,
        visit_id="visit:z",
        policy_key="policy:z",
        to_record=lambda: {
            "capability_id": capability,
            "visit_id": "visit:z",
            "policy_key": "policy:z",
        },
    )
    offer = SimpleNamespace(capability_id=capability)
    how = {
        "grade": "Z",
        "phase": "TEACHING",
        "curriculum_scope": "factory/z",
        "grade_definition_sha256": "c" * 64,
        "source_binding_sha256": "b" * 64,
        "factory_release_sha256": "c" * 64,
        "rubric_sha256": rubric * 64,
        "diagnostics": {},
    }
    return _issue_result(
        "TEACHER_SELECTED", capability, offer,
        SimpleNamespace(identity=identity), {"family": "fixture"},
        {"how_context": how}, "Z", (), "/tmp",
        _frontier(policy_epoch=policy_epoch, capability=capability),
    )


def _registered_adapter():
    descriptor = SourceAdapter(
        PROVIDER, "fixture.future-z/v1", ("fixture.oracle/v1",),
        IMPLEMENTATION,
        weakness_classifier_id="fixture.weakness.future-z/v1",
        weakness_classifier_sha256="6" * 64,
    )
    return RegisteredSourceAdapter(
        descriptor,
        lambda **_: (),
        lambda *_args, **_kwargs: True,
        weakness_classifier=lambda row: {
            "family": "future-z", "shape": row["shape"],
        },
    )


def _weakness_record(selection, row):
    adapter = _registered_adapter()
    execution = SimpleNamespace(
        capability_id=CAPABILITY, provider_id=PROVIDER,
        provider_implementation_sha256=IMPLEMENTATION,
    )
    weakness = classify_weakness(adapter, execution, row)
    record = {
        "schema": weakness_replay.EVIDENCE_SCHEMA,
        "state": "UNRESOLVED",
        "freshness": "FRESH_EQUIVALENT_REQUIRED",
        "capability_id": CAPABILITY,
        "weakness_class": weakness.to_record(),
        "context": weakness_replay.issue_weakness_context(selection),
        "candidate_evidence_sha256": "e" * 64,
        "outcome_sha256": "f" * 64,
        "retention_reason": "NO_MEASURABLE_TARGET_GAIN",
    }
    record["weakness_evidence_sha256"] = weakness_replay._digest(record)
    return record


class _SourceContext:
    def __init__(self, rows):
        adapter = _registered_adapter()
        self.source_registry = SourceAdapterRegistry((adapter,))
        from bilqis_mlx.factory.curriculum_definition import CapabilitySourceBinding
        binding = CapabilitySourceBinding(
            CAPABILITY, "repo:fixture/z",
            adapter.descriptor.generator_id,
            adapter.descriptor.accepted_oracle_ids[0])
        self.release = SimpleNamespace(
            release_sha256="c" * 64,
            curriculum=SimpleNamespace(),
            source_bindings=SimpleNamespace(by_capability={
                CAPABILITY: binding,
            }),
            source_adapters=(adapter.descriptor,),
        )
        self.graph = {}
        self.source_root = None
        self.run_dir = Path("/tmp")
        self._rows = tuple(rows)

    def execution_for(self, capability):
        assert capability == CAPABILITY
        return SimpleNamespace(
            capability_id=CAPABILITY, provider_id=PROVIDER,
            provider_implementation_sha256=IMPLEMENTATION,
        )

    def draw_rows(self, *, seed, capability, each):
        assert type(seed) is int and capability == CAPABILITY and each >= 1
        return list(self._rows)


def _selection_for_context(context, **kwargs):
    from dataclasses import asdict
    from bilqis_mlx.runtime.state import _fingerprint
    binding = context.release.source_bindings.by_capability[CAPABILITY]
    selected = _selection(**kwargs)
    how = dict(selected.metadata["how_context"])
    how["source_binding_sha256"] = _fingerprint(asdict(binding))
    return _issue_result(
        "TEACHER_SELECTED", CAPABILITY, selected.offer, selected.visit,
        selected.policy, {"how_context": how}, "Z", (), "/tmp",
        _frontier(
            policy_epoch=kwargs.get("policy_epoch", 7),
            capability=CAPABILITY))


def test_source_rubric_and_policy_drift_make_old_debt_non_authorizing():
    row = {"id": "old", "capability": CAPABILITY, "shape": ["edge", 2]}
    context = _SourceContext((row,))
    current = _selection_for_context(context)
    record = _weakness_record(current, row)
    wrapper = {
        "weakness": record,
        "candidate_evidence": {"object": {"sha256": "e" * 64}},
    }
    assert weakness_replay.weakness_is_current(wrapper, context, current)
    assert not weakness_replay.weakness_is_current(
        wrapper, context, _selection_for_context(context, rubric="9"))
    assert not weakness_replay.weakness_is_current(
        wrapper, context, _selection_for_context(context, policy_epoch=8))
    context.release.release_sha256 = "9" * 64
    assert not weakness_replay.weakness_is_current(wrapper, context, current)


def test_unsupported_provider_has_no_false_current_debt():
    row = {"id": "old", "capability": CAPABILITY, "shape": ["edge", 2]}
    context = _SourceContext((row,))
    selection = _selection_for_context(context)
    record = _weakness_record(selection, row)
    wrapper = {
        "weakness": record,
        "candidate_evidence": {"object": {"sha256": "e" * 64}},
    }
    unsupported = replace_registered_without_classifier(context)
    assert not weakness_replay.weakness_is_current(
        wrapper, unsupported, selection)


def test_cold_projection_rehydrates_exact_weakness_evidence(tmp_path):
    from bilqis_mlx.data_plane import DataPlane

    selection = _selection()
    row = {"id": "old", "capability": CAPABILITY, "shape": ["edge", 2]}
    weakness = _weakness_record(selection, row)
    wrapper = {
        "weakness": weakness,
        "candidate_evidence": {"object": {"sha256": "e" * 64}},
        "rejection_receipt_sha256": "9" * 64,
    }
    event = {"event": "fixture-rejection"}
    journal = tmp_path / "events.jsonl"
    journal.write_text('{"event":"fixture-rejection"}\n')

    def validate(value):
        assert value == event
        return (
            "9" * 64,
            (CAPABILITY, "visit:z", "NO_MEASURABLE_TARGET_GAIN", "9" * 64),
            1, 1, (wrapper,),
        )

    projection_key = "r13-weakness-fixture"
    plane_path = tmp_path / "events.sqlite3"
    plane = DataPlane(plane_path)
    hot = RejectionProjection()
    hot.refresh(
        tmp_path, projection_key, plane, validate,
        lambda reason: (_ for _ in ()).throw(AssertionError(reason)))
    plane.close()

    plane = DataPlane(plane_path)
    cold = RejectionProjection()
    cold.refresh(
        tmp_path, projection_key, plane,
        lambda _value: (_ for _ in ()).throw(
            AssertionError("cold hydration rescanned indexed event")),
        lambda reason: (_ for _ in ()).throw(AssertionError(reason)))
    plane.close()

    assert hot.weaknesses_view() == (wrapper,)
    assert cold.weaknesses_view() == hot.weaknesses_view()


def test_rejected_candidate_evidence_compiles_provider_owned_weakness(
        monkeypatch, tmp_path):
    from bilqis_mlx.factory.adapters import SourceAdapterRegistry
    from bilqis_mlx.factory.curriculum_definition import from_legacy_course
    from bilqis_mlx.factory.executable_release import (
        compile_executable_factory_release,
    )
    from bilqis_mlx.factory.execution import CurriculumProfile
    from bilqis_mlx.factory.tests.test_executable_release import _answers
    from bilqis_mlx.factory.tests.test_execution_plan import (
        _synthetic_course, _synthetic_registry,
    )
    from bilqis_mlx.runtime.source_execution import SourceExecutionContext
    from bilqis_mlx.runtime.bamf_operator import evidence_validation

    course = _synthetic_course(1)
    curriculum, bindings = from_legacy_course(course)
    registered = next(iter(_synthetic_registry()._by_generator.values()))
    registered = replace(
        registered,
        descriptor=replace(
            registered.descriptor,
            weakness_classifier_id="fixture.weakness.z/v1",
            weakness_classifier_sha256="7" * 64),
        weakness_classifier=lambda row: {
            "family": "fixture-z", "gold": row["gold"],
        },
    )
    sources = SourceAdapterRegistry((registered,))
    graph = {"tokens": ["fixture.padding", "cogal.value.false", "cogal.value.true"]}
    release = compile_executable_factory_release(
        curriculum, bindings, CurriculumProfile.full(), sources, _answers(),
        source_root=None, graph=graph, verification_seed=17)
    context = SourceExecutionContext(
        release, graph, None, sources, _answers(), run_dir=tmp_path)
    row = context.draw_rows(seed=19, capability="Z.C0", each=1)[0]
    selection = _selection(capability="Z.C0")
    how = dict(selection.metadata["how_context"])
    how["factory_release_sha256"] = release.release_sha256
    selection = _issue_result(
        "TEACHER_SELECTED", "Z.C0", selection.offer, selection.visit,
        selection.policy, {"how_context": how}, "Z", (), str(tmp_path),
        _frontier(capability="Z.C0"),
    )
    payload = {
        "proposal": {"how_context": how},
        "source_objects": {"row-object": row},
        "steps": [{"positions": [{
            "roles": ["selected_option"], "row": "row-object",
        }]}],
    }
    monkeypatch.setattr(
        evidence_validation, "read_candidate_horizon_evidence",
        lambda _run_dir, _receipt: payload)
    candidate = {"object": {"sha256": "e" * 64}}

    records = weakness_replay.derive_rejected_weaknesses(
        tmp_path, context, selection, candidate,
        rejection_reason="NO_MEASURABLE_TARGET_GAIN",
        outcome_sha256="f" * 64)

    assert len(records) == 1
    assert records[0]["capability_id"] == "Z.C0"
    assert records[0]["weakness_class"]["classifier_id"] == "fixture.weakness.z/v1"
    assert records[0]["candidate_evidence_sha256"] == "e" * 64
    assert row["id"] not in str(records[0])


def replace_registered_without_classifier(context):
    current = context.source_registry.resolve_owner("fixture.future-z/v1")
    context.source_registry = SourceAdapterRegistry((
        RegisteredSourceAdapter(
            replace(
                current.descriptor,
                weakness_classifier_id=None,
                weakness_classifier_sha256=None),
            current.draw, current.check),
    ))
    return context
