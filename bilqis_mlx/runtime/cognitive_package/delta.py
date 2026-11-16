"""Pure compatible plastic-delta application before C05 retention/adoption."""
from dataclasses import dataclass, field
from hashlib import sha256
import json
from pathlib import Path

import mlx.core as mx
import numpy as np

from bilqis_mlx.learning.atlas_acceptance import candidate_identity_digest
from bilqis_mlx.learning.atlas_package_import import (
    ImportSlice, PackageImportTransaction, prepare_package_import,
)
from bilqis_mlx.learning.atlas_retention_decision import (
    CandidateRetentionDecision, issue_factory_retention_decision,
)
from bilqis_mlx.runtime.factory_retention_owner import evaluate_factory_package_import
from bilqis_mlx.runtime.baseline.lifecycle import BaselineLedger

from .contracts import PackageBinding, PackageKind, digest_string, invalid, name, require
from .records import CognitivePackage
from .staging import stage_import


DELTA_SCHEMA = "bilqis.c12.plastic-delta/v1"
_CANDIDATE_ISSUER = object()
_SCREEN_ISSUER = object()


@dataclass(frozen=True)
class DeltaSlice:
    parameter_name: str
    start: int
    stop: int
    parent_slice_sha256: str
    delta_fp32: bytes

    def __post_init__(self):
        require(name(self.parameter_name), "invalid delta parameter name")
        require(type(self.start) is int and type(self.stop) is int
                and 0 <= self.start < self.stop, "invalid delta slice range")
        require(digest_string(self.parent_slice_sha256), "invalid parent slice digest")
        require(type(self.delta_fp32) is bytes
                and len(self.delta_fp32) == 4 * (self.stop - self.start),
                "invalid delta slice bytes")
        values = np.frombuffer(self.delta_fp32, dtype="<f4")
        require(bool(np.all(np.isfinite(values))), "nonfinite delta slice")


@dataclass(frozen=True)
class ReceiverTensor:
    parameter_name: str
    shape: tuple[int, ...]
    values_fp32: bytes

    def __post_init__(self):
        require(name(self.parameter_name), "invalid receiver parameter name")
        require(type(self.shape) is tuple and bool(self.shape)
                and all(type(v) is int and v > 0 for v in self.shape),
                "invalid receiver tensor shape")
        count = 1
        for extent in self.shape:
            count *= extent
        require(type(self.values_fp32) is bytes and len(self.values_fp32) == count * 4,
                "invalid receiver tensor bytes")
        values = np.frombuffer(self.values_fp32, dtype="<f4")
        require(bool(np.all(np.isfinite(values))), "nonfinite receiver tensor")


@dataclass(frozen=True, init=False)
class DisposableDeltaCandidate:
    parent_generation: str
    generation_digest: str
    package: CognitivePackage
    binding: PackageBinding
    parent_tensors: tuple[ReceiverTensor, ...]
    tensors: tuple[ReceiverTensor, ...]
    schema_version: str = "bilqis.c12.disposable-delta-candidate/v1"
    _issuance: object = field(init=False, repr=False, compare=False)

    def __init__(self, *args, **kwargs):
        invalid("delta candidate must be issued by apply_plastic_delta")

    def __post_init__(self):
        require(getattr(self, "_issuance", None) is _CANDIDATE_ISSUER,
                "unissued delta candidate")
        require(all(digest_string(v) for v in (
            self.parent_generation, self.generation_digest)),
            "invalid candidate identity")
        require(type(self.package) is CognitivePackage, "invalid candidate package")
        require(type(self.binding) is PackageBinding, "invalid candidate binding")
        parent = _canonical_tensors(self.parent_tensors)
        current = _canonical_tensors(self.tensors)
        require(parent == self.parent_tensors and current == self.tensors,
                "candidate tensors must be canonical")
        expected = _apply_delta_tensors(self.package, self.binding, parent)
        require(current == expected, "candidate tensors do not replay package delta")
        require(self.generation_digest
                == _candidate_digest(self.parent_generation, self.package.digest, current),
                "candidate generation digest mismatch")
        require(self.schema_version == "bilqis.c12.disposable-delta-candidate/v1",
                "invalid candidate schema")

    @property
    def package_digest(self):
        return self.package.digest


@dataclass(frozen=True, init=False)
class ScreenedDeltaCandidate:
    candidate: DisposableDeltaCandidate
    transaction: PackageImportTransaction
    decision: CandidateRetentionDecision
    baseline_ledger: BaselineLedger
    _issuance: object = field(init=False, repr=False, compare=False)

    def __init__(self, *args, **kwargs):
        invalid("screened delta candidate must be issued by C05 screening")

    def __post_init__(self):
        require(getattr(self, "_issuance", None) is _SCREEN_ISSUER,
                "unissued screened delta candidate")
        require(type(self.candidate) is DisposableDeltaCandidate,
                "invalid screened candidate")
        self.candidate.__post_init__()
        require(type(self.transaction) is PackageImportTransaction,
                "invalid package import transaction")
        self.transaction.__post_init__()
        require(type(self.decision) is CandidateRetentionDecision,
                "invalid screened decision")
        self.decision.__post_init__()
        require(type(self.baseline_ledger) is BaselineLedger, "invalid baseline ledger")
        require(self.decision.parent_generation
                == candidate_identity_digest(self.transaction.parent)
                and self.decision.candidate_generation
                == candidate_identity_digest(self.transaction.candidate),
                "screened decision identity mismatch")


def encode_plastic_delta(slices):
    require(type(slices) is tuple and bool(slices)
            and all(type(value) is DeltaSlice for value in slices),
            "invalid plastic delta slices")
    _require_nonoverlap(slices)
    raw = {
        "schema": DELTA_SCHEMA,
        "slices": [{
            "parameter_name": value.parameter_name,
            "start": value.start,
            "stop": value.stop,
            "parent_slice_sha256": value.parent_slice_sha256,
            "delta_fp32": value.delta_fp32.hex(),
        } for value in slices],
    }
    return json.dumps(raw, sort_keys=True, separators=(",", ":"),
                      ensure_ascii=False, allow_nan=False).encode("utf-8")


def _decode_plastic_delta(payload):
    try:
        raw = json.loads(payload.decode("utf-8"), object_pairs_hook=_unique_object)
        require(raw.get("schema") == DELTA_SCHEMA and set(raw) == {"schema", "slices"},
                "invalid plastic delta schema")
        require(type(raw["slices"]) is list and bool(raw["slices"]),
                "invalid plastic delta slices")
        slices = tuple(DeltaSlice(
            value["parameter_name"], value["start"], value["stop"],
            value["parent_slice_sha256"], bytes.fromhex(value["delta_fp32"]),
        ) for value in raw["slices"])
        require(encode_plastic_delta(slices) == payload, "noncanonical plastic delta")
        return slices
    except (KeyError, TypeError, ValueError, UnicodeError, RecursionError):
        invalid("invalid plastic delta record")


def _unique_object(pairs):
    result = {}
    for key, value in pairs:
        require(key not in result, "duplicate plastic delta key")
        result[key] = value
    return result


def _require_nonoverlap(slices):
    spans = {}
    for value in slices:
        value.__post_init__()
        current = spans.setdefault(value.parameter_name, [])
        require(all(value.stop <= start or stop <= value.start for start, stop in current),
                "overlapping plastic delta slices")
        current.append((value.start, value.stop))


def _all_delta_slices(package):
    slices = []
    for artifact in package.artifacts:
        if artifact.kind in (PackageKind.ADAPTER_DELTA, PackageKind.WEIGHT_DELTA):
            slices.extend(_decode_plastic_delta(artifact.payload))
    require(bool(slices), "plastic delta artifact required")
    result = tuple(slices)
    _require_nonoverlap(result)
    return result


def _candidate_digest(parent_generation, package_digest, tensors):
    raw = {
        "parent_generation": parent_generation,
        "package_digest": package_digest,
        "tensors": [{
            "parameter_name": value.parameter_name,
            "shape": list(value.shape),
            "sha256": sha256(value.values_fp32).hexdigest(),
        } for value in tensors],
    }
    encoded = json.dumps(raw, sort_keys=True, separators=(",", ":"),
                         ensure_ascii=False, allow_nan=False).encode("utf-8")
    return sha256(encoded).hexdigest()


def receiver_weight_digest(tensors):
    """Derive exact base-weight identity from canonical receiver tensor bytes."""
    ordered = _canonical_tensors(tensors)
    raw = [{
        "parameter_name": value.parameter_name,
        "shape": list(value.shape),
        "sha256": sha256(value.values_fp32).hexdigest(),
    } for value in ordered]
    return _json_digest(raw)


def receiver_parameter_schema_digest(tensors):
    """Derive the portable float32 parameter-schema identity from the receiver."""
    ordered = _canonical_tensors(tensors)
    raw = [{
        "parameter_name": value.parameter_name,
        "shape": list(value.shape),
        "dtype": "<f4",
    } for value in ordered]
    return _json_digest(raw)


def _json_digest(value):
    encoded = json.dumps(value, sort_keys=True, separators=(",", ":"),
                         ensure_ascii=False, allow_nan=False).encode("utf-8")
    return sha256(encoded).hexdigest()


def _canonical_tensors(tensors):
    require(type(tensors) is tuple and bool(tensors)
            and all(type(value) is ReceiverTensor for value in tensors),
            "invalid receiver tensors")
    by_name = {value.parameter_name: value for value in tensors}
    require(len(by_name) == len(tensors), "duplicate receiver parameter")
    return tuple(by_name[name] for name in sorted(by_name))


def _apply_delta_tensors(package, receiver_binding, tensors):
    plan = stage_import(package, receiver_binding)
    require(plan.disposition == "EXACT_BINDING", "delta requires exact receiver binding")
    require(receiver_weight_digest(tensors) == receiver_binding.base_weight_digest,
            "receiver base-weight digest mismatch")
    require(receiver_parameter_schema_digest(tensors)
            == receiver_binding.parameter_schema_digest,
            "receiver parameter-schema digest mismatch")
    by_name = {value.parameter_name: value for value in tensors}
    candidate = {name: value for name, value in by_name.items()}
    for delta in _all_delta_slices(package):
        require(delta.parameter_name in by_name, "delta parameter is not allocated")
        parent = by_name[delta.parameter_name]
        values = np.frombuffer(parent.values_fp32, dtype="<f4")
        require(delta.stop <= values.size, "delta slice exceeds receiver tensor")
        parent_bytes = values[delta.start:delta.stop].astype("<f4", copy=False).tobytes()
        require(sha256(parent_bytes).hexdigest() == delta.parent_slice_sha256,
                "parent slice digest mismatch")
        updated = values.copy()
        updated[delta.start:delta.stop] += np.frombuffer(delta.delta_fp32, dtype="<f4")
        require(bool(np.all(np.isfinite(updated))), "nonfinite candidate tensor")
        candidate[delta.parameter_name] = ReceiverTensor(
            parent.parameter_name, parent.shape, updated.astype("<f4", copy=False).tobytes())
    return tuple(candidate[name] for name in sorted(candidate))


def _issue_candidate(parent_generation, package, binding, parent_tensors, tensors):
    candidate = object.__new__(DisposableDeltaCandidate)
    generation_digest = _candidate_digest(parent_generation, package.digest, tensors)
    for key, value in (
        ("parent_generation", parent_generation), ("generation_digest", generation_digest),
        ("package", package), ("binding", binding), ("parent_tensors", parent_tensors),
        ("tensors", tensors), ("schema_version", "bilqis.c12.disposable-delta-candidate/v1"),
        ("_issuance", _CANDIDATE_ISSUER),
    ):
        object.__setattr__(candidate, key, value)
    candidate.__post_init__()
    return candidate


def _issue_screened(candidate, transaction, decision, baseline_ledger=None):
    baseline_ledger = baseline_ledger or BaselineLedger.empty()
    screened = object.__new__(ScreenedDeltaCandidate)
    for key, value in (("candidate", candidate), ("transaction", transaction),
                       ("decision", decision), ("baseline_ledger", baseline_ledger),
                       ("_issuance", _SCREEN_ISSUER)):
        object.__setattr__(screened, key, value)
    screened.__post_init__()
    return screened


def _candidate_parameters(candidate):
    parameters = {}
    for tensor in candidate.tensors:
        array = np.frombuffer(tensor.values_fp32, dtype="<f4").copy().reshape(tensor.shape)
        parameters[tensor.parameter_name] = mx.array(array, dtype=mx.float32)
    return parameters


def _import_slices(package):
    return tuple(ImportSlice(item.parameter_name, item.start, item.stop)
                 for item in sorted(
                     _all_delta_slices(package),
                     key=lambda item: (item.parameter_name, item.start, item.stop)))


def _package_transaction(candidate, run_dir):
    from .receiver import _load_current_generation, _receiver_tensors
    pointer, parent = _load_current_generation(run_dir)
    require(candidate.parent_generation == pointer["manifest_sha256"],
            "screened import parent is stale")
    require(candidate.parent_tensors == _receiver_tensors(parent),
            "screened import parent tensors drifted")
    return prepare_package_import(
        parent.retained_state, _candidate_parameters(candidate),
        _import_slices(candidate.package))


def apply_plastic_delta(package, receiver_run_dir):
    """Build a disposable candidate from the current B13 receiver generation."""
    from .receiver import apply_from_current_generation
    require(type(package) is CognitivePackage, "invalid cognitive package")
    return apply_from_current_generation(package, receiver_run_dir)


def screen_delta_candidate(
        candidate, source_context, artifact_path, target_capability, *, run_dir):
    """Run the Factory-owned C05 screen over the B12 package-import proposal."""
    require(type(candidate) is DisposableDeltaCandidate, "invalid delta candidate")
    candidate.__post_init__()
    run_dir = Path(run_dir)
    transaction = _package_transaction(candidate, run_dir)
    evaluation = evaluate_factory_package_import(
        source_context, transaction, str(artifact_path), target_capability,
        run_dir=run_dir)
    decision = issue_factory_retention_decision(evaluation)
    return _issue_screened(candidate, transaction, decision, evaluation.baseline_ledger)
