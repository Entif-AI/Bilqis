"""Release errors, digests, bindings, and verification receipts."""
from __future__ import annotations

from dataclasses import dataclass

from .. import executable_release as _api


class _ReleaseError:
    """Stable legacy wire codes owned by the executable-release contract."""

    MODALITY_DRIFT = "FACTORY_EXECUTABLE_RELEASE_MODALITY_DRIFT"
    PROVIDER_DRIFT = "FACTORY_EXECUTABLE_RELEASE_PROVIDER_DRIFT"
    ANSWER_HEAD_DRIFT = "FACTORY_EXECUTABLE_RELEASE_ANSWER_HEAD_DRIFT"
    CATALOG_INVALID = "FACTORY_EXECUTABLE_RELEASE_CATALOG_INVALID"
    CATALOG_DRIFT = "FACTORY_EXECUTABLE_RELEASE_CATALOG_DRIFT"
    SEMANTIC_GRAPH_INVALID = "FACTORY_EXECUTABLE_RELEASE_SEMANTIC_GRAPH_INVALID"
    SEMANTIC_GRAPH_DRIFT = "FACTORY_EXECUTABLE_RELEASE_SEMANTIC_GRAPH_DRIFT"
    SEMANTIC_CATALOG_REQUIRED = "FACTORY_EXECUTABLE_RELEASE_SEMANTIC_CATALOG_REQUIRED"
    VERIFICATION_INVALID = "FACTORY_EXECUTABLE_RELEASE_VERIFICATION_INVALID"
    VERIFICATION_DRIFT = "FACTORY_EXECUTABLE_RELEASE_VERIFICATION_DRIFT"
    ASSESSMENT_DRIFT = "FACTORY_EXECUTABLE_RELEASE_ASSESSMENT_DRIFT"
    LINEAGE_DRIFT = "FACTORY_EXECUTABLE_RELEASE_LINEAGE_DRIFT"
    FOUNDATION_CAPABILITY_IDS_REQUIRED = (
        "FACTORY_EXECUTABLE_RELEASE_FOUNDATION_CAPABILITY_IDS_REQUIRED")
    FOUNDATION_CAPABILITY_DRIFT = (
        "FACTORY_EXECUTABLE_RELEASE_FOUNDATION_CAPABILITY_DRIFT")


def _require(condition: bool, code: str) -> None:
    """Fail one named release invariant without duplicating its wire identity."""
    if not condition:
        raise ValueError(code)


def _digest(value) -> str:
    return _api.hashlib.sha256(_api.json.dumps(
        value, sort_keys=True, separators=(",", ":"), ensure_ascii=False,
        allow_nan=False).encode("utf-8")).hexdigest()


def _require_sha256(value: str, code: str) -> str:
    if (not isinstance(value, str) or len(value) != 64 or
            any(char not in "0123456789abcdef" for char in value)):
        raise ValueError(code)
    return value


def _tuples(value):
    if isinstance(value, list):
        return tuple(_api._tuples(item) for item in value)
    if isinstance(value, dict):
        return {key: _api._tuples(item) for key, item in value.items()}
    return value


@dataclass(frozen=True)
class AnswerHeadBinding:
    kind: str
    values: tuple[str, ...]
    semantic_identities: tuple[str, ...]
    token_ids: tuple[int, ...]
    modality_id: str
    implementation_sha256: str

    def __post_init__(self) -> None:
        if (not self.kind or not self.modality_id or not self.values or
                len(self.values) != len(self.semantic_identities) or
                len(self.values) != len(self.token_ids) or
                len(set(self.values)) != len(self.values) or
                len(set(self.semantic_identities)) != len(self.semantic_identities) or
                len(set(self.token_ids)) != len(self.token_ids) or
                any(type(item) is not int or item < 0 for item in self.token_ids)):
            raise ValueError("FACTORY_EXECUTABLE_RELEASE_ANSWER_HEAD_INVALID")
        _api._require_sha256(
            self.implementation_sha256,
            "FACTORY_EXECUTABLE_RELEASE_ANSWER_HEAD_IMPLEMENTATION_INVALID")


@dataclass(frozen=True)
class CapabilityVerificationReceipt:
    capability_id: str
    verification_seed: int
    specimen_count: int
    specimen_ids_sha256: str
    specimen_content_sha256: str
    source_projection_sha256: str
    coverage_projection_sha256: str
    answer_schema_projection_sha256: str

    def __post_init__(self) -> None:
        _api._require(
            bool(self.capability_id) and type(self.verification_seed) is int and
            type(self.specimen_count) is int and self.specimen_count >= 1,
            _api._ReleaseError.VERIFICATION_INVALID,
        )
        for value in (
                self.specimen_ids_sha256, self.specimen_content_sha256,
                self.source_projection_sha256, self.coverage_projection_sha256,
                self.answer_schema_projection_sha256):
            _api._require_sha256(
                value, "FACTORY_EXECUTABLE_RELEASE_VERIFICATION_DIGEST_INVALID")

    def digest(self) -> str:
        return _api._digest(_api.asdict(self))


@dataclass(frozen=True)
class VerifiedAssessmentSeal:
    grade_id: str
    cumulative_scope: tuple[str, ...]
    assessment_blueprint_sha256: str
    capability_receipt_sha256s: tuple[str, ...]
    seal_sha256: str

    def __post_init__(self) -> None:
        if (not self.grade_id or not self.cumulative_scope or
                len(set(self.cumulative_scope)) != len(self.cumulative_scope) or
                len(self.cumulative_scope) != len(self.capability_receipt_sha256s)):
            raise ValueError("FACTORY_EXECUTABLE_RELEASE_ASSESSMENT_SEAL_INVALID")
        _api._require_sha256(
            self.assessment_blueprint_sha256,
            "FACTORY_EXECUTABLE_RELEASE_ASSESSMENT_BLUEPRINT_INVALID")
        for value in self.capability_receipt_sha256s:
            _api._require_sha256(
                value, "FACTORY_EXECUTABLE_RELEASE_ASSESSMENT_RECEIPT_INVALID")
        _api._require_sha256(
            self.seal_sha256,
            "FACTORY_EXECUTABLE_RELEASE_ASSESSMENT_SEAL_DIGEST_INVALID")

    def expected_digest(self) -> str:
        return _api._digest({
            "schema": "bilqis.mlx.verified-assessment/v1",
            "grade_id": self.grade_id,
            "cumulative_scope": self.cumulative_scope,
            "assessment_blueprint_sha256": self.assessment_blueprint_sha256,
            "capability_receipt_sha256s": self.capability_receipt_sha256s,
        })


@dataclass(frozen=True)
class ExecutableVerificationReceipt:
    verification_seed: int
    execution_plan_sha256: str
    source_binding_sha256: str
    provider_descriptors_sha256: str
    answer_modalities_sha256: str
    semantic_catalog_sha256: str
    answer_heads_sha256: str
    capabilities: tuple[CapabilityVerificationReceipt, ...]
    assessments: tuple[VerifiedAssessmentSeal, ...]

    def __post_init__(self) -> None:
        _api._require(
            type(self.verification_seed) is int and
            bool(self.capabilities) and bool(self.assessments),
            _api._ReleaseError.VERIFICATION_INVALID,
        )
        for value in (
                self.execution_plan_sha256, self.source_binding_sha256,
                self.provider_descriptors_sha256, self.answer_modalities_sha256,
                self.semantic_catalog_sha256, self.answer_heads_sha256):
            _api._require_sha256(
                value, "FACTORY_EXECUTABLE_RELEASE_VERIFICATION_DIGEST_INVALID")


@dataclass(frozen=True)
class ExecutableAdmissionReceipt:
    factory_release_sha256: str
    execution_plan_sha256: str
    curriculum_sha256: str
    source_binding_sha256: str
    semantic_catalog_sha256: str
    semantic_graph_sha256: str
    student_sha256: str
    optimizer_step: int

    def __post_init__(self) -> None:
        for value in (
                self.factory_release_sha256, self.execution_plan_sha256,
                self.curriculum_sha256, self.source_binding_sha256,
                self.semantic_catalog_sha256, self.semantic_graph_sha256,
                self.student_sha256):
            _api._require_sha256(
                value, "FACTORY_EXECUTABLE_ADMISSION_DIGEST_INVALID")
        if type(self.optimizer_step) is not int or self.optimizer_step < 0:
            raise ValueError("FACTORY_EXECUTABLE_ADMISSION_STEP_INVALID")

    def verify(self, release: "ExecutableFactoryRelease") -> None:
        if not isinstance(release, _api.ExecutableFactoryRelease):
            raise TypeError("FACTORY_EXECUTABLE_ADMISSION_RELEASE_REQUIRED")
        release.verify()
        if (self.factory_release_sha256 != release.release_sha256 or
                self.execution_plan_sha256 != release.execution_plan.digest() or
                self.curriculum_sha256 != release.curriculum.digest() or
                self.source_binding_sha256 != release.source_bindings.digest() or
                self.semantic_catalog_sha256 != release.semantic_catalog_sha256):
            raise ValueError("FACTORY_EXECUTABLE_ADMISSION_RELEASE_MISMATCH")
        if release.semantic_graph_sha256 is not None:
            _api._require(self.semantic_graph_sha256 == release.semantic_graph_sha256,
                     _api._ReleaseError.SEMANTIC_GRAPH_DRIFT)


    def verify_baseline(self, *, student_sha256: str, optimizer_step: int,
                        semantic_graph_sha256: str) -> None:
        """Preserve the admitted baseline while its causal student advances."""
        _api._require_sha256(student_sha256, "FACTORY_EXECUTABLE_ADMISSION_CURRENT_STUDENT_INVALID")
        _api._require_sha256(semantic_graph_sha256, "FACTORY_EXECUTABLE_ADMISSION_CURRENT_GRAPH_INVALID")
        if (type(optimizer_step) is not int or optimizer_step < 0
                or self.semantic_graph_sha256 != semantic_graph_sha256
                or self.optimizer_step > optimizer_step
                or (self.optimizer_step == optimizer_step and self.student_sha256 != student_sha256)):
            raise ValueError("FACTORY_EXECUTABLE_ADMISSION_BASELINE_DRIFT")
