"""#1314-owned certification transition authority backed by #1334 success."""
from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path

from bilqis_mlx.errors import ErrorBus, SCHOOL
from bilqis_mlx.factory.generated_grade import GeneratedGradeProposal
from bilqis_mlx.factory.generated_grade.definition import GeneratedGradeDefinition
from bilqis_mlx.runtime.state import _fingerprint

from .active_generated_grade_contracts import ActiveGeneratedGrade
from .generated_grade import _read_issued_proposal


CERTIFICATION_TRANSITION_SCHEMA = (
    "bilqis.bamf.active-grade-certification-transition/v1")
_ISSUER = object()


def _fail(reason: str):
    ErrorBus.raise_(
        SCHOOL.BAMF_ATLAS_ADMISSION.INVALID,
        reason=reason,
    )


def _sha(value: object) -> bool:
    return (
        type(value) is str and len(value) == 64
        and all(char in "0123456789abcdef" for char in value)
    )


@dataclass(frozen=True, init=False)
class CertificationGradeTransitionAuthority:
    accepted_manifest_sha256: str
    certification_receipt_sha256: str
    predecessor_activation_sha256: str
    predecessor_definition_sha256: str
    predecessor_learner_foot_sha256: str
    successor_proposal_sha256: str
    successor_definition_sha256: str
    successor_learner_foot_sha256: str
    reason_code: str
    authority_sha256: str
    schema: str = CERTIFICATION_TRANSITION_SCHEMA
    _issuance: object = field(init=False, repr=False, compare=False)

    def __init__(self, *args, **kwargs):
        _fail("BAMF_ACTIVE_GENERATED_GRADE_CERTIFICATION_AUTHORITY_FORBIDDEN")

    def to_record(self) -> dict:
        return {
            "schema": self.schema,
            "accepted_manifest_sha256": self.accepted_manifest_sha256,
            "certification_receipt_sha256": self.certification_receipt_sha256,
            "predecessor_activation_sha256":
                self.predecessor_activation_sha256,
            "predecessor_definition_sha256":
                self.predecessor_definition_sha256,
            "predecessor_learner_foot_sha256":
                self.predecessor_learner_foot_sha256,
            "successor_proposal_sha256": self.successor_proposal_sha256,
            "successor_definition_sha256": self.successor_definition_sha256,
            "successor_learner_foot_sha256":
                self.successor_learner_foot_sha256,
            "reason_code": self.reason_code,
            "authority_sha256": self.authority_sha256,
        }

    def expected_digest(self) -> str:
        record = self.to_record()
        record["authority_sha256"] = "0" * 64
        return _fingerprint(record)

    def verify(self) -> None:
        if (
            getattr(self, "_issuance", None) is not _ISSUER
            or self.schema != CERTIFICATION_TRANSITION_SCHEMA
            or not all(_sha(value) for value in (
                self.accepted_manifest_sha256,
                self.certification_receipt_sha256,
                self.predecessor_activation_sha256,
                self.predecessor_definition_sha256,
                self.predecessor_learner_foot_sha256,
                self.successor_proposal_sha256,
                self.successor_definition_sha256,
                self.successor_learner_foot_sha256,
                self.authority_sha256,
            ))
            or self.reason_code != "GRADE_CERTIFIED"
            or self.authority_sha256 != self.expected_digest()
        ):
            _fail("BAMF_ACTIVE_GENERATED_GRADE_CERTIFICATION_AUTHORITY_INVALID")


def _issue(**values) -> CertificationGradeTransitionAuthority:
    expected = set(CertificationGradeTransitionAuthority.__dataclass_fields__) - {
        "_issuance"}
    if set(values) != expected:
        _fail("BAMF_ACTIVE_GENERATED_GRADE_CERTIFICATION_AUTHORITY_INVALID")
    authority = object.__new__(CertificationGradeTransitionAuthority)
    for name, value in (*values.items(), ("_issuance", _ISSUER)):
        object.__setattr__(authority, name, value)
    authority.verify()
    return authority


def _transition_root(run_dir: Path) -> Path:
    root = Path(run_dir) / "generated-grades" / "certification-transitions"
    if root.is_symlink() or (root.exists() and not root.is_dir()):
        _fail("BAMF_ACTIVE_GENERATED_GRADE_CERTIFICATION_CUSTODY_UNSAFE")
    return root


def _record_path(run_dir: Path, digest: str) -> Path:
    return _transition_root(run_dir) / f"{digest}.json"


def _issue_certification_transition_authority(
    run_dir: Path,
    *,
    accepted_manifest_sha256: str,
    certification_receipt_sha256: str,
    predecessor: ActiveGeneratedGrade,
    proposal: GeneratedGradeProposal,
    definition: GeneratedGradeDefinition,
) -> CertificationGradeTransitionAuthority:
    """Mint #1314 authority after #1334 and successor custody are both proven."""
    from bilqis_mlx.runtime.grade_certification_custody import (
        certification_receipt_for_predecessor,
    )
    certification_receipt = certification_receipt_for_predecessor(
        Path(run_dir),
        activation_sha256=predecessor.activation_sha256,
        definition_sha256=predecessor.definition.definition_sha256,
        receipt_sha256=certification_receipt_sha256,
    )
    proposal.verify()
    definition.verify()
    if (
        certification_receipt is None
        or certification_receipt.receipt_sha256 != certification_receipt_sha256
        or certification_receipt.predecessor_activation_sha256
           != predecessor.activation_sha256
        or certification_receipt.predecessor_definition_sha256
           != predecessor.definition.definition_sha256
        or proposal.predecessor_certification_sha256
           != certification_receipt.receipt_sha256
        or definition.predecessor_certification_sha256
           != certification_receipt.receipt_sha256
        or definition.proposal_sha256 != proposal.proposal_sha256
    ):
        _fail("BAMF_ACTIVE_GENERATED_GRADE_CERTIFICATION_AUTHORITY_REQUIRED")
    provisional = {
        "schema": CERTIFICATION_TRANSITION_SCHEMA,
        "accepted_manifest_sha256": accepted_manifest_sha256,
        "certification_receipt_sha256":
            certification_receipt.receipt_sha256,
        "predecessor_activation_sha256": predecessor.activation_sha256,
        "predecessor_definition_sha256":
            predecessor.definition.definition_sha256,
        "predecessor_learner_foot_sha256":
            predecessor.definition.learner_foot_sha256,
        "successor_proposal_sha256": proposal.proposal_sha256,
        "successor_definition_sha256": definition.definition_sha256,
        "successor_learner_foot_sha256": definition.learner_foot_sha256,
        "reason_code": "GRADE_CERTIFIED",
        "authority_sha256": "0" * 64,
    }
    provisional["authority_sha256"] = _fingerprint(provisional)
    authority = _issue(**provisional)
    from . import active_generated_grade_custody as custody
    custody._persist_immutable(
        _record_path(run_dir, authority.authority_sha256),
        authority.to_record(),
        "BAMF_ACTIVE_GENERATED_GRADE_CERTIFICATION_AUTHORITY_INVALID",
    )
    return authority


def require_certification_transition_authority(
    run_dir: Path,
    active: ActiveGeneratedGrade,
) -> CertificationGradeTransitionAuthority:
    """Cold-verify the #1314 authority and historical #1334 success."""
    if (
        active.transition_kind != "CERTIFICATION"
        or not _sha(active.transition_receipt_sha256)
    ):
        _fail("BAMF_ACTIVE_GENERATED_GRADE_CERTIFICATION_AUTHORITY_INVALID")
    from . import active_generated_grade_custody as custody
    record = custody._json(
        _record_path(run_dir, active.transition_receipt_sha256),
        "BAMF_ACTIVE_GENERATED_GRADE_CERTIFICATION_AUTHORITY_INVALID",
    )
    authority = _issue(**record)
    if (
        authority.authority_sha256 != active.transition_receipt_sha256
        or authority.predecessor_activation_sha256
           != active.predecessor_activation_sha256
        or authority.predecessor_definition_sha256
           != active.predecessor_definition_sha256
        or authority.successor_proposal_sha256 != active.proposal_sha256
        or authority.successor_definition_sha256
           != active.definition.definition_sha256
        or authority.successor_learner_foot_sha256
           != active.definition.learner_foot_sha256
        or authority.accepted_manifest_sha256
           != active.activation_manifest_sha256
        or authority.reason_code != active.transition_reason
        or active.definition.predecessor_certification_sha256
           != authority.certification_receipt_sha256
    ):
        _fail("BAMF_ACTIVE_GENERATED_GRADE_CERTIFICATION_AUTHORITY_DRIFT")
    proposal = _read_issued_proposal(
        run_dir, authority.successor_proposal_sha256)
    if (
        proposal.predecessor_certification_sha256
        != authority.certification_receipt_sha256
    ):
        _fail("BAMF_ACTIVE_GENERATED_GRADE_CERTIFICATION_ANCESTRY_DRIFT")
    from bilqis_mlx.runtime.grade_certification_custody import (
        certification_receipt_for_predecessor,
    )
    receipt = certification_receipt_for_predecessor(
        Path(run_dir),
        activation_sha256=authority.predecessor_activation_sha256,
        definition_sha256=authority.predecessor_definition_sha256,
        receipt_sha256=authority.certification_receipt_sha256,
    )
    if (
        receipt is None
        or receipt.receipt_sha256 != authority.certification_receipt_sha256
    ):
        _fail("BAMF_ACTIVE_GENERATED_GRADE_CERTIFICATION_ANCESTRY_DRIFT")
    return authority


__all__ = (
    "CertificationGradeTransitionAuthority",
    "require_certification_transition_authority",
)
