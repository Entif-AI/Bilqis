"""Historical #1320 proposal acceptance and deterministic replay for #1314."""
from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path

from bilqis_mlx.errors import ErrorBus, SCHOOL
from bilqis_mlx.factory.generated_grade.definition import _seal_generated_grade
from bilqis_mlx.runtime.state import _fingerprint

from .active_generated_grade_contracts import ActiveGeneratedGrade
from .generated_grade import _accepted_release_lineage, _read_issued_proposal


ACCEPTANCE_SCHEMA = "bilqis.bamf.generated-grade-proposal-acceptance/v1"
_ISSUER = object()


def _fail(reason: str):
    ErrorBus.raise_(SCHOOL.BAMF_ATLAS_ADMISSION.INVALID, reason=reason)


@dataclass(frozen=True, init=False)
class ProposalAcceptanceReceipt:
    proposal_sha256: str
    definition_sha256: str
    run_id: str
    generation: int
    manifest_sha256: str
    acceptance_sha256: str
    current_release_sha256: str
    receipt_sha256: str
    schema: str = ACCEPTANCE_SCHEMA
    _issuance: object = field(init=False, repr=False, compare=False)

    def to_record(self) -> dict:
        return {
            "schema": self.schema,
            "proposal_sha256": self.proposal_sha256,
            "definition_sha256": self.definition_sha256,
            "run_id": self.run_id,
            "generation": self.generation,
            "manifest_sha256": self.manifest_sha256,
            "acceptance_sha256": self.acceptance_sha256,
            "current_release_sha256": self.current_release_sha256,
            "receipt_sha256": self.receipt_sha256,
        }

    def expected_digest(self) -> str:
        record = self.to_record()
        record["receipt_sha256"] = "0" * 64
        return _fingerprint(record)


def _issue(**values) -> ProposalAcceptanceReceipt:
    receipt = object.__new__(ProposalAcceptanceReceipt)
    for name, value in (*values.items(), ("_issuance", _ISSUER)):
        object.__setattr__(receipt, name, value)
    if (receipt.schema != ACCEPTANCE_SCHEMA
            or receipt.receipt_sha256 != receipt.expected_digest()):
        _fail("BAMF_ACTIVE_GENERATED_GRADE_PROPOSAL_ACCEPTANCE_INVALID")
    return receipt


def _root(run_dir: Path) -> Path:
    root = Path(run_dir) / "generated-grades" / "proposal-acceptances"
    if root.is_symlink() or (root.exists() and not root.is_dir()):
        _fail("BAMF_ACTIVE_GENERATED_GRADE_PROPOSAL_ACCEPTANCE_CUSTODY_UNSAFE")
    return root


def _values(active: ActiveGeneratedGrade, proposal) -> dict:
    values = {
        "schema": ACCEPTANCE_SCHEMA,
        "proposal_sha256": active.proposal_sha256,
        "definition_sha256": active.definition.definition_sha256,
        "run_id": active.run_id,
        "generation": active.activation_generation,
        "manifest_sha256": active.activation_manifest_sha256,
        "acceptance_sha256": active.activation_acceptance_sha256,
        "current_release_sha256": proposal.current_release_sha256,
        "receipt_sha256": "0" * 64,
    }
    values["receipt_sha256"] = _fingerprint(values)
    return values


def _persist_proposal_acceptance(
    run_dir: Path,
    active: ActiveGeneratedGrade,
    proposal,
) -> None:
    from . import active_generated_grade_custody as custody
    if proposal.proposal_sha256 != active.proposal_sha256:
        _fail("BAMF_ACTIVE_GENERATED_GRADE_PROPOSAL_ACCEPTANCE_INVALID")
    receipt = _issue(**_values(active, proposal))
    custody._persist_immutable(
        _root(run_dir) / f"{receipt.receipt_sha256}.json",
        receipt.to_record(),
        "BAMF_ACTIVE_GENERATED_GRADE_PROPOSAL_ACCEPTANCE_INVALID",
    )


def _require_proposal_acceptance(
    run_dir: Path,
    active: ActiveGeneratedGrade,
    proposal,
) -> ProposalAcceptanceReceipt:
    from . import active_generated_grade_custody as custody
    expected = _issue(**_values(active, proposal))
    record = custody._json(
        _root(run_dir) / f"{expected.receipt_sha256}.json",
        "BAMF_ACTIVE_GENERATED_GRADE_PROPOSAL_ACCEPTANCE_INVALID",
    )
    receipt = _issue(**record)
    if receipt != expected or not custody._activation_is_accepted_ancestor(
            run_dir, active):
        _fail("BAMF_ACTIVE_GENERATED_GRADE_PROPOSAL_ACCEPTANCE_DRIFT")
    return receipt


def _reconcile_accepted_generated_grade(
    run_dir: Path,
    active: ActiveGeneratedGrade,
    proposal,
) -> None:
    """Replay the exact proposal accepted at activation, never current synthesis."""
    receipt = _require_proposal_acceptance(run_dir, active, proposal)
    if (_read_issued_proposal(run_dir, receipt.proposal_sha256) != proposal
            or receipt.definition_sha256 != active.definition.definition_sha256):
        _fail("BAMF_GENERATED_GRADE_ACCEPTED_PROPOSAL_MISMATCH")
    lineage = _accepted_release_lineage(run_dir, proposal)
    digests = tuple(item.release_sha256 for item in lineage)
    try:
        adopted_index = digests.index(active.definition.adopted_release_sha256)
    except ValueError:
        _fail("BAMF_GENERATED_GRADE_ADOPTED_RELEASE_NOT_ACCEPTED")
    if digests.count(active.definition.adopted_release_sha256) != 1:
        _fail("BAMF_GENERATED_GRADE_ADOPTED_RELEASE_NOT_ACCEPTED")
    historical = lineage[:adopted_index + 1]
    reconciled = _seal_generated_grade(
        proposal, historical[-1], release_lineage=historical)
    if reconciled != active.definition:
        _fail("BAMF_GENERATED_GRADE_DEFINITION_ANCESTRY_DRIFT")
