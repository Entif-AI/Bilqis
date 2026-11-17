"""Provider-owned structural weakness classes for fresh-equivalent teaching."""
from __future__ import annotations

from dataclasses import dataclass
import hashlib
import json

from bilqis_mlx.errors import ErrorBus, FACTORY


SCHEMA = "bilqis.factory.weakness-class/v1"
_SHA256_LENGTH = 64


def _invalid(reason: str):
    ErrorBus.Raise(FACTORY.WEAKNESS.INVALID, reason=reason)


def _canonical(value) -> bytes:
    try:
        return json.dumps(
            value, sort_keys=True, separators=(",", ":"), ensure_ascii=False,
            allow_nan=False,
        ).encode("utf-8")
    except (TypeError, ValueError) as exc:
        _invalid("FACTORY_WEAKNESS_SIGNATURE_INVALID")
        raise AssertionError from exc


def _plain(value):
    return json.loads(_canonical(value))


def _digest(value) -> str:
    return hashlib.sha256(_canonical(value)).hexdigest()


@dataclass(frozen=True)
class WeaknessClassId:
    """Typed provider-relative semantic construction class, never a row identity."""

    capability_id: str
    provider_id: str
    provider_implementation_sha256: str
    classifier_id: str
    classifier_sha256: str
    signature: object
    class_sha256: str
    schema: str = SCHEMA

    def __post_init__(self) -> None:
        if (self.schema != SCHEMA
                or not isinstance(self.capability_id, str) or not self.capability_id
                or not isinstance(self.provider_id, str) or not self.provider_id
                or not isinstance(self.classifier_id, str) or not self.classifier_id
                or not isinstance(self.provider_implementation_sha256, str)
                or len(self.provider_implementation_sha256) != _SHA256_LENGTH
                or any(char not in "0123456789abcdef"
                       for char in self.provider_implementation_sha256)
                or not isinstance(self.classifier_sha256, str)
                or len(self.classifier_sha256) != _SHA256_LENGTH
                or any(char not in "0123456789abcdef"
                       for char in self.classifier_sha256)):
            _invalid("FACTORY_WEAKNESS_CLASS_ID_INVALID")
        signature = _plain(self.signature)
        object.__setattr__(self, "signature", signature)
        if self.class_sha256 != _digest(self._identity_record()):
            _invalid("FACTORY_WEAKNESS_CLASS_DIGEST_INVALID")

    def _identity_record(self) -> dict:
        return {
            "schema": self.schema,
            "capability_id": self.capability_id,
            "provider_id": self.provider_id,
            "provider_implementation_sha256": self.provider_implementation_sha256,
            "classifier_id": self.classifier_id,
            "classifier_sha256": self.classifier_sha256,
            "signature": self.signature,
        }

    def to_record(self) -> dict:
        return {**self._identity_record(), "class_sha256": self.class_sha256}

    @classmethod
    def from_record(cls, record: dict) -> "WeaknessClassId":
        if not isinstance(record, dict) or set(record) != {
            "schema", "capability_id", "provider_id",
            "provider_implementation_sha256", "classifier_id", "signature",
            "classifier_sha256", "class_sha256",
        }:
            _invalid("FACTORY_WEAKNESS_CLASS_RECORD_INVALID")
        return cls(**record)


def classify_weakness(
        adapter, execution, row: dict, *, provider_descriptor=None,
) -> WeaknessClassId | None:
    """Ask the declared source provider for semantic structure; never infer it here."""
    descriptor = provider_descriptor or adapter.descriptor
    classifier = getattr(adapter, "weakness_classifier", None)
    classifier_id = descriptor.weakness_classifier_id
    classifier_sha256 = descriptor.weakness_classifier_sha256
    if classifier_id is None and classifier_sha256 is None:
        return None
    if (not callable(classifier)
            or adapter.descriptor.weakness_classifier_id != classifier_id
            or adapter.descriptor.weakness_classifier_sha256 != classifier_sha256):
        _invalid("FACTORY_WEAKNESS_CLASSIFIER_INVALID")
    if (not isinstance(row, dict)
            or row.get("capability") != getattr(execution, "capability_id", None)
            or getattr(execution, "provider_id", None) != descriptor.adapter_id
            or getattr(execution, "provider_implementation_sha256", None)
            != descriptor.implementation_sha256):
        _invalid("FACTORY_WEAKNESS_PROVIDER_CONTEXT_DRIFT")
    signature = _plain(classifier(row))
    identity = {
        "schema": SCHEMA,
        "capability_id": execution.capability_id,
        "provider_id": execution.provider_id,
        "provider_implementation_sha256": execution.provider_implementation_sha256,
        "classifier_id": classifier_id,
        "classifier_sha256": classifier_sha256,
        "signature": signature,
    }
    return WeaknessClassId(
        capability_id=execution.capability_id,
        provider_id=execution.provider_id,
        provider_implementation_sha256=execution.provider_implementation_sha256,
        classifier_id=classifier_id,
        classifier_sha256=classifier_sha256,
        signature=signature,
        class_sha256=_digest(identity),
    )


__all__ = (
    "SCHEMA", "WeaknessClassId", "classify_weakness",
)
