"""BMF v0.3.8 normative training-objective identity and constants."""
from __future__ import annotations

from dataclasses import dataclass
import hashlib
import json
from typing import Mapping

from bilqis_mlx.errors import ErrorBus, SCHOOL


TRAINING_OBJECTIVE_SCHEMA = "bilqis.mlx.training-objective-contract/v1"
TRAINING_OBJECTIVE_ID = "BMF-0.3.8-OBJECTIVE-001"
TRAINING_OBJECTIVE_VERSION = "0.3.8"
REFINEMENT_ROUTING_WEIGHT = 0.05
FRAME_ATOMIC_CONSISTENCY_WEIGHT = 0.05
FAMILY_WEIGHTS = (
    ("VALUE", 1.0),
    ("CONTROL", 1.0),
    ("OPERATOR", 1.0),
    ("OPERAND", 1.0),
    ("ROLE", 0.10),
    ("EPISTEMIC", 0.10),
    ("IMPACT", 0.05),
    ("EXIGENCY", 0.05),
    ("NOVELTY", 0.05),
    ("REFINEMENT_ROUTING", REFINEMENT_ROUTING_WEIGHT),
    ("FRAME_ATOMIC_CONSISTENCY", FRAME_ATOMIC_CONSISTENCY_WEIGHT),
)
INACTIVE_FAMILIES = ("FRAME_ATOMIC_CONSISTENCY",)
FP32_RTOL = 1e-5
FP32_ATOL = 1e-6


def _invalid(reason: str) -> None:
    ErrorBus.raise_(SCHOOL.BAMF_TRAINING_ADAPTER.INVALID, reason=reason)


def _canonical(record: Mapping) -> bytes:
    return (json.dumps(
        record, sort_keys=True, separators=(",", ":"),
        ensure_ascii=False, allow_nan=False) + "\n").encode("utf-8")


@dataclass(frozen=True)
class TrainingObjectiveContract:
    schema_version: str = TRAINING_OBJECTIVE_SCHEMA
    objective_id: str = TRAINING_OBJECTIVE_ID
    objective_version: str = TRAINING_OBJECTIVE_VERSION
    family_weights: tuple[tuple[str, float], ...] = FAMILY_WEIGHTS
    inactive_families: tuple[str, ...] = INACTIVE_FAMILIES
    local_loss: str = "FP32_LEGAL_CATEGORICAL_CROSS_ENTROPY"
    within_kind_reduction: str = "ARITHMETIC_MEAN"
    row_composition: str = "WEIGHTED_FAMILY_SUM"
    row_supervision_strength: str = "BOUNDED_SOURCE_GATED_MULTIPLIER"
    logical_batch_reduction: str = "ARITHMETIC_MEAN_OVER_DELIVERED_ROWS"
    microbatch_reduction: str = "FP32_ROW_COUNT_WEIGHTED_MEAN"
    fp32_rtol: float = FP32_RTOL
    fp32_atol: float = FP32_ATOL

    def __post_init__(self) -> None:
        if (
            self.schema_version != TRAINING_OBJECTIVE_SCHEMA
            or self.objective_id != TRAINING_OBJECTIVE_ID
            or self.objective_version != TRAINING_OBJECTIVE_VERSION
            or self.family_weights != FAMILY_WEIGHTS
            or self.inactive_families != INACTIVE_FAMILIES
            or self.local_loss != "FP32_LEGAL_CATEGORICAL_CROSS_ENTROPY"
            or self.within_kind_reduction != "ARITHMETIC_MEAN"
            or self.row_composition != "WEIGHTED_FAMILY_SUM"
            or self.row_supervision_strength != "BOUNDED_SOURCE_GATED_MULTIPLIER"
            or self.logical_batch_reduction != "ARITHMETIC_MEAN_OVER_DELIVERED_ROWS"
            or self.microbatch_reduction != "FP32_ROW_COUNT_WEIGHTED_MEAN"
            or self.fp32_rtol != FP32_RTOL
            or self.fp32_atol != FP32_ATOL
        ):
            _invalid("TRAINING_OBJECTIVE_CONTRACT_INVALID")

    def to_record(self) -> dict:
        return {
            "schema_version": self.schema_version,
            "objective_id": self.objective_id,
            "objective_version": self.objective_version,
            "family_weights": [list(item) for item in self.family_weights],
            "inactive_families": list(self.inactive_families),
            "local_loss": self.local_loss,
            "within_kind_reduction": self.within_kind_reduction,
            "row_composition": self.row_composition,
            "row_supervision_strength": self.row_supervision_strength,
            "logical_batch_reduction": self.logical_batch_reduction,
            "microbatch_reduction": self.microbatch_reduction,
            "fp32_rtol": self.fp32_rtol,
            "fp32_atol": self.fp32_atol,
        }

    @property
    def digest(self) -> str:
        return hashlib.sha256(_canonical(self.to_record())).hexdigest()

    @property
    def ref(self) -> str:
        return self.objective_id

    @classmethod
    def from_record(cls, record: Mapping) -> "TrainingObjectiveContract":
        expected = {
            "schema_version", "objective_id", "objective_version",
            "family_weights", "inactive_families", "local_loss",
            "within_kind_reduction", "row_composition",
            "row_supervision_strength", "logical_batch_reduction",
            "microbatch_reduction", "fp32_rtol", "fp32_atol",
        }
        if not isinstance(record, Mapping) or set(record) != expected:
            _invalid("TRAINING_OBJECTIVE_CONTRACT_INVALID")
        try:
            value = cls(
                schema_version=record["schema_version"],
                objective_id=record["objective_id"],
                objective_version=record["objective_version"],
                family_weights=tuple(
                    (str(name), float(weight))
                    for name, weight in record["family_weights"]),
                inactive_families=tuple(record["inactive_families"]),
                local_loss=record["local_loss"],
                within_kind_reduction=record["within_kind_reduction"],
                row_composition=record["row_composition"],
                row_supervision_strength=record["row_supervision_strength"],
                logical_batch_reduction=record["logical_batch_reduction"],
                microbatch_reduction=record["microbatch_reduction"],
                fp32_rtol=float(record["fp32_rtol"]),
                fp32_atol=float(record["fp32_atol"]),
            )
        except (KeyError, TypeError, ValueError):
            _invalid("TRAINING_OBJECTIVE_CONTRACT_INVALID")
        value.__post_init__()
        return value


_CURRENT = TrainingObjectiveContract()


def current_training_objective() -> TrainingObjectiveContract:
    return _CURRENT


def require_current_training_objective(value) -> TrainingObjectiveContract:
    if type(value) is not TrainingObjectiveContract:
        _invalid("TRAINING_OBJECTIVE_CONTRACT_REQUIRED")
    value.__post_init__()
    if value != _CURRENT or value.digest != _CURRENT.digest:
        _invalid("TRAINING_OBJECTIVE_CONTRACT_DRIFT")
    return value


def require_training_objective_digest(digest: str) -> str:
    if digest != _CURRENT.digest:
        _invalid("TRAINING_OBJECTIVE_CONTRACT_DRIFT")
    return digest


__all__ = (
    "FAMILY_WEIGHTS", "FP32_ATOL", "FP32_RTOL",
    "FRAME_ATOMIC_CONSISTENCY_WEIGHT", "INACTIVE_FAMILIES",
    "REFINEMENT_ROUTING_WEIGHT", "TRAINING_OBJECTIVE_ID",
    "TRAINING_OBJECTIVE_SCHEMA", "TRAINING_OBJECTIVE_VERSION",
    "TrainingObjectiveContract", "current_training_objective",
    "require_current_training_objective", "require_training_objective_digest",
)
