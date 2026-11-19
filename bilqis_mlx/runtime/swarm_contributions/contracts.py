"""C14.4 immutable remote-work and contribution contracts."""
from __future__ import annotations

from dataclasses import asdict, dataclass, field
from enum import Enum
from hashlib import sha256
import json
import math
import re

from bilqis_mlx.errors import ErrorBus, SCHOOL

MANIFEST_SCHEMA = "bilqis.c14.remote-work-manifest/v1"
ARTIFACT_SCHEMA = "bilqis.c14.contribution-artifact/v1"
WORKER_SCHEMA = "bilqis.c14.worker-identity/v1"
RECEIPT_SCHEMA = "bilqis.c14.worker-receipt/v2"
EVALUATION_SCHEMA = "bilqis.c14.independent-evaluation/v1"
DECISION_SCHEMA = "bilqis.c14.contribution-decision/v2"
LEDGER_SCHEMA = "bilqis.c14.replay-ledger/v1"
USAGE_SCHEMA = "bilqis.c14.resource-usage/v1"

_SHA = re.compile(r"[0-9a-f]{64}\Z")
_SIG = re.compile(r"[0-9a-f]{128}\Z")
_PUBLIC_KEY = re.compile(r"[0-9a-f]{64}\Z")
_PUBLIC_RIGHTS = frozenset({"PUBLIC_FIXTURE", "PUBLIC_DERIVED"})


def invalid(reason: str) -> None:
    ErrorBus.raise_(SCHOOL.STATE.HISTORICAL_ARTIFACT_INVALID, reason=reason)


def text(value: object) -> bool:
    return type(value) is str and bool(value.strip())


def digest(value: object) -> bool:
    return type(value) is str and _SHA.fullmatch(value) is not None


def finite(value: object) -> bool:
    return type(value) in (int, float) and math.isfinite(float(value))


def canonical_bytes(payload: object) -> bytes:
    return (json.dumps(
        payload, sort_keys=True, separators=(",", ":"),
        ensure_ascii=False, allow_nan=False) + "\n").encode("utf-8")


def content_digest(payload: object) -> str:
    return sha256(canonical_bytes(payload)).hexdigest()


class ContributionClass(str, Enum):
    EVALUATION = "evaluation"
    CURRICULUM = "curriculum"
    ADAPTER_DELTA = "adapter_delta"
    MOTIF_CANDIDATE = "motif_candidate"
    REGRESSION = "regression"
    DENSE_UPDATE = "dense_update"


class ContributionDisposition(str, Enum):
    ADMITTED = "ADMITTED"
    REJECTED = "REJECTED"


def expected_artifact_type(contribution_class: ContributionClass) -> str | None:
    match contribution_class:
        case ContributionClass.EVALUATION:
            return "evaluation_receipt"
        case ContributionClass.CURRICULUM:
            return "curriculum_candidate"
        case ContributionClass.ADAPTER_DELTA:
            return "c12_cognitive_package"
        case ContributionClass.MOTIF_CANDIDATE:
            return "motif_candidate"
        case ContributionClass.REGRESSION:
            return "regression_evidence"
        case _:
            return None


@dataclass(frozen=True)
class ResourceBudget:
    max_examples: int
    max_steps: int
    max_seconds: int
    max_bytes: int

    def __post_init__(self) -> None:
        if any(type(value) is not int or value < 1 for value in asdict(self).values()):
            invalid("BAMF_C14_RESOURCE_BUDGET_INVALID")


@dataclass(frozen=True)
class AcceptanceContract:
    contract_digest: str
    minimum_score: float
    requires_retention: bool

    def __post_init__(self) -> None:
        if (not digest(self.contract_digest)
                or not finite(self.minimum_score)
                or not 0.0 <= float(self.minimum_score) <= 1.0
                or type(self.requires_retention) is not bool):
            invalid("BAMF_C14_ACCEPTANCE_CONTRACT_INVALID")


@dataclass(frozen=True)
class RemoteWorkManifest:
    manifest_id: str
    retained_generation: str
    source_release: str
    capability_id: str
    seed: int
    partition_id: str
    resource_budget: ResourceBudget
    model_identity: str
    topology_identity: str
    mlx_identity: str
    rights_scope: str
    contribution_class: ContributionClass
    expected_artifact_type: str
    acceptance: AcceptanceContract
    expires_at: int
    replay_id: str
    base_binding_digest: str | None = None
    schema_version: str = field(default=MANIFEST_SCHEMA, init=False)

    @classmethod
    def create(
            cls, *, manifest_id: str, retained_generation: str,
            source_release: str, capability_id: str, seed: int,
            partition_id: str, resource_budget: ResourceBudget,
            model_identity: str, topology_identity: str, mlx_identity: str,
            rights_scope: str, contribution_class: ContributionClass,
            acceptance: AcceptanceContract, expires_at: int, replay_id: str,
            base_binding_digest: str | None = None,
    ) -> "RemoteWorkManifest":
        if contribution_class is ContributionClass.DENSE_UPDATE:
            invalid("BAMF_C14_DENSE_UPDATE_AGGREGATION_UNSPECIFIED")
        expected = expected_artifact_type(contribution_class)
        if expected is None:
            invalid("BAMF_C14_CONTRIBUTION_CLASS_UNSUPPORTED")
        return cls(
            manifest_id, retained_generation, source_release, capability_id,
            seed, partition_id, resource_budget, model_identity,
            topology_identity, mlx_identity, rights_scope,
            contribution_class, expected, acceptance, expires_at,
            replay_id, base_binding_digest)

    def __post_init__(self) -> None:
        if (not all(text(value) for value in (
                    self.manifest_id, self.capability_id, self.partition_id,
                    self.mlx_identity, self.replay_id))
                or not all(digest(value) for value in (
                    self.retained_generation, self.source_release,
                    self.model_identity, self.topology_identity))
                or type(self.seed) is not int or self.seed < 0
                or type(self.resource_budget) is not ResourceBudget
                or self.rights_scope not in _PUBLIC_RIGHTS
                or type(self.contribution_class) is not ContributionClass
                or self.contribution_class is ContributionClass.DENSE_UPDATE
                or self.expected_artifact_type
                    != expected_artifact_type(self.contribution_class)
                or type(self.acceptance) is not AcceptanceContract
                or type(self.expires_at) is not int or self.expires_at < 1
                or (self.contribution_class is ContributionClass.ADAPTER_DELTA
                    and (not digest(self.base_binding_digest)
                         or self.acceptance.requires_retention is not True
                         or float(self.acceptance.minimum_score) != 0.0))
                or (self.contribution_class is not ContributionClass.ADAPTER_DELTA
                    and self.base_binding_digest is not None)
                or self.schema_version != MANIFEST_SCHEMA):
            invalid("BAMF_C14_REMOTE_WORK_MANIFEST_INVALID")

    def canonical_payload(self) -> dict[str, object]:
        return {
            "schema_version": self.schema_version,
            "manifest_id": self.manifest_id,
            "retained_generation": self.retained_generation,
            "source_release": self.source_release,
            "capability_id": self.capability_id,
            "seed": self.seed,
            "partition_id": self.partition_id,
            "resource_budget": asdict(self.resource_budget),
            "model_identity": self.model_identity,
            "topology_identity": self.topology_identity,
            "mlx_identity": self.mlx_identity,
            "rights_scope": self.rights_scope,
            "contribution_class": self.contribution_class.value,
            "expected_artifact_type": self.expected_artifact_type,
            "acceptance": asdict(self.acceptance),
            "expires_at": self.expires_at,
            "replay_id": self.replay_id,
            "base_binding_digest": self.base_binding_digest,
        }

    @property
    def canonical_json(self) -> str:
        from .wire import encode_manifest
        return encode_manifest(self)

    @classmethod
    def from_canonical_json(cls, value: str) -> "RemoteWorkManifest":
        from .wire import decode_manifest
        return decode_manifest(value)

    @property
    def digest(self) -> str:
        self.__post_init__()
        return content_digest(self.canonical_payload())
