"""R13 provider-declared structural weakness contracts."""
from dataclasses import replace
from types import SimpleNamespace

import pytest

from bilqis_mlx.errors import BilqisError
from bilqis_mlx.factory.adapters import (
    RegisteredSourceAdapter, SourceAdapterRegistry,
)
from bilqis_mlx.factory.model import SourceAdapter
from bilqis_mlx.factory._model.weakness import (
    WeaknessClassId, classify_weakness,
)


def _adapter(*, classifier=True):
    descriptor = SourceAdapter(
        "source.future-z/v1", "fixture.future-z/v1", ("fixture.oracle/v1",),
        "a" * 64,
        **({
            "weakness_classifier_id": "fixture.weakness.future-z/v1",
            "weakness_classifier_sha256": "c" * 64,
        } if classifier else {}),
    )
    kwargs = {}
    if classifier:
        kwargs = {
            "weakness_classifier": lambda row: {
                "family": "future-z",
                "shape": row["shape"],
                "answer_kind": row["answer_kind"],
            },
        }
    return RegisteredSourceAdapter(
        descriptor, lambda **_: (), lambda *_args, **_kwargs: True, **kwargs)


def _execution():
    return SimpleNamespace(
        capability_id="Z.NOVEL",
        provider_id="source.future-z/v1",
        provider_implementation_sha256="a" * 64,
    )


def test_future_provider_defines_equivalence_without_trainer_branching():
    adapter, execution = _adapter(), _execution()
    old = {
        "id": "old-row", "capability": "Z.NOVEL",
        "shape": ["relation", 2], "answer_kind": "typed-z",
    }
    fresh = {**old, "id": "fresh-row"}
    different = {**fresh, "id": "other-row", "shape": ["relation", 3]}

    weakness = classify_weakness(adapter, execution, old)
    same = classify_weakness(adapter, execution, fresh)
    other = classify_weakness(adapter, execution, different)

    assert isinstance(weakness, WeaknessClassId)
    assert same.class_sha256 == weakness.class_sha256
    assert other.class_sha256 != weakness.class_sha256
    assert weakness.to_record()["capability_id"] == "Z.NOVEL"
    assert "old-row" not in str(weakness.to_record())

def test_provider_without_declared_classifier_is_honestly_unsupported():
    assert classify_weakness(
        _adapter(classifier=False), _execution(),
        {"id": "row", "capability": "Z.NOVEL"}) is None


def test_classifier_contract_is_both_or_neither_and_tamper_evident():
    adapter = _adapter()
    SourceAdapterRegistry((adapter,))
    with pytest.raises(ValueError, match="CONSTRUCTOR_AND_CHECKER_REQUIRED"):
        SourceAdapterRegistry((replace(
            adapter, descriptor=replace(
                adapter.descriptor,
                weakness_classifier_id=None,
                weakness_classifier_sha256=None)),))

    weakness = classify_weakness(
        adapter, _execution(),
        {"id": "row", "capability": "Z.NOVEL",
         "shape": ["relation", 2], "answer_kind": "typed-z"})
    record = weakness.to_record()
    record["signature"]["shape"] = ["relation", 99]
    with pytest.raises(BilqisError) as failure:
        WeaknessClassId.from_record(record)
    assert failure.value.context["reason"] == "FACTORY_WEAKNESS_CLASS_DIGEST_INVALID"


def test_provider_context_drift_fails_closed():
    adapter = _adapter()
    row = {
        "id": "row", "capability": "Z.NOVEL",
        "shape": ["relation", 2], "answer_kind": "typed-z",
    }
    with pytest.raises(BilqisError) as failure:
        classify_weakness(
            adapter,
            SimpleNamespace(
                capability_id="Z.NOVEL",
                provider_id="source.future-z/v1",
                provider_implementation_sha256="b" * 64,
            ),
            row,
        )
    assert failure.value.context["reason"] == "FACTORY_WEAKNESS_PROVIDER_CONTEXT_DRIFT"


def test_sealed_classifier_digest_participates_in_weakness_identity():
    adapter = _adapter()
    row = {
        "id": "row", "capability": "Z.NOVEL",
        "shape": ["relation", 2], "answer_kind": "typed-z",
    }
    first = classify_weakness(adapter, _execution(), row)
    changed_descriptor = replace(
        adapter.descriptor, weakness_classifier_sha256="d" * 64)
    changed = replace(adapter, descriptor=changed_descriptor)
    second = classify_weakness(changed, _execution(), row)
    assert first.classifier_sha256 == "c" * 64
    assert second.classifier_sha256 == "d" * 64
    assert first.class_sha256 != second.class_sha256
