"""Exact correction-transition authority for #1314 generated grades."""
from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path

from bilqis_mlx.errors import ErrorBus, SCHOOL
from bilqis_mlx.factory.generated_grade import GeneratedGradeProposal
from bilqis_mlx.factory.generated_grade.definition import GeneratedGradeDefinition
from bilqis_mlx.runtime.state import _fingerprint

from .active_generated_grade_contracts import (
    ActiveGeneratedGrade,
    active_from_record,
    definition_from_record,
)
from .generated_grade import _read_issued_proposal


CORRECTION_TRANSITION_SCHEMA = "bilqis.bamf.active-grade-correction-transition/v1"
_ISSUER = object()


def _fail(reason: str):
    ErrorBus.raise_(SCHOOL.BAMF_ATLAS_ADMISSION.INVALID, reason=reason)


def _sha(value: object) -> bool:
    return (type(value) is str and len(value) == 64
            and all(char in "0123456789abcdef" for char in value))


@dataclass(frozen=True, init=False)
class CorrectionGradeTransitionAuthority:
    accepted_manifest_sha256: str
    correction_record_sha256: str
    correction_event_id: str
    correction_source_receipt_sha256: str
    correction_old_evidence_sha256: str
    correction_new_evidence_sha256: str
    correction_dependency_kind: str
    correction_dependency_key: str
    predecessor_activation_sha256: str
    predecessor_definition_sha256: str
    predecessor_learner_foot_sha256: str
    successor_proposal_sha256: str
    successor_definition_sha256: str
    successor_learner_foot_sha256: str
    relation_kind: str
    relation_value: str
    reason_code: str
    authority_sha256: str
    schema: str = CORRECTION_TRANSITION_SCHEMA
    _issuance: object = field(init=False, repr=False, compare=False)

    def __init__(self, *args, **kwargs):
        _fail("BAMF_ACTIVE_GENERATED_GRADE_CORRECTION_AUTHORITY_FORBIDDEN")

    def to_record(self) -> dict:
        return {
            key: getattr(self, key)
            for key in (
                "schema", "accepted_manifest_sha256", "correction_record_sha256",
                "correction_event_id", "correction_source_receipt_sha256",
                "correction_old_evidence_sha256", "correction_new_evidence_sha256",
                "correction_dependency_kind", "correction_dependency_key",
                "predecessor_activation_sha256", "predecessor_definition_sha256",
                "predecessor_learner_foot_sha256", "successor_proposal_sha256",
                "successor_definition_sha256", "successor_learner_foot_sha256",
                "relation_kind", "relation_value", "reason_code", "authority_sha256",
            )
        }

    def expected_digest(self) -> str:
        record = self.to_record()
        record["authority_sha256"] = "0" * 64
        return _fingerprint(record)

    def verify(self) -> None:
        digests = (
            self.accepted_manifest_sha256, self.correction_record_sha256,
            self.correction_source_receipt_sha256, self.correction_old_evidence_sha256,
            self.correction_new_evidence_sha256, self.predecessor_activation_sha256,
            self.predecessor_definition_sha256, self.predecessor_learner_foot_sha256,
            self.successor_proposal_sha256, self.successor_definition_sha256,
            self.successor_learner_foot_sha256, self.authority_sha256,
        )
        if (getattr(self, "_issuance", None) is not _ISSUER
                or self.schema != CORRECTION_TRANSITION_SCHEMA
                or not all(_sha(value) for value in digests)
                or not all(type(value) is str and value for value in (
                    self.correction_event_id, self.correction_dependency_kind,
                    self.correction_dependency_key, self.relation_kind,
                    self.relation_value, self.reason_code))
                or self.relation_kind not in {"NEW_EVIDENCE", "DEPENDENCY"}
                or self.authority_sha256 != self.expected_digest()):
            _fail("BAMF_ACTIVE_GENERATED_GRADE_CORRECTION_AUTHORITY_INVALID")


def _issue(**values) -> CorrectionGradeTransitionAuthority:
    expected_fields = set(CorrectionGradeTransitionAuthority.__dataclass_fields__) - {
        "_issuance"
    }
    if set(values) != expected_fields:
        _fail("BAMF_ACTIVE_GENERATED_GRADE_CORRECTION_AUTHORITY_INVALID")
    authority = object.__new__(CorrectionGradeTransitionAuthority)
    for name, value in (*values.items(), ("_issuance", _ISSUER)):
        object.__setattr__(authority, name, value)
    authority.verify()
    return authority


def _relation(proposal: GeneratedGradeProposal, correction) -> tuple[str, str]:
    selected = tuple(
        decision for decision in proposal.decisions
        if decision.semantic_id in set(proposal.member_semantic_ids))
    source_evidence = {
        digest for decision in selected for digest in decision.source_evidence_sha256s
    }
    if correction.new_evidence_sha256 in source_evidence:
        return "NEW_EVIDENCE", correction.new_evidence_sha256
    dependencies = set(proposal.member_semantic_ids)
    for decision in selected:
        dependencies.update(decision.compiled_capability_ids)
        dependencies.update(decision.source_anchor_ids)
        dependencies.update(decision.prerequisite_ids)
        dependencies.update(decision.required_semantic_ids)
        dependencies.update(item[4] for item in decision.a09_reason_receipts)
    if correction.dependency.key in dependencies:
        return "DEPENDENCY", correction.dependency.key
    _fail("BAMF_ACTIVE_GENERATED_GRADE_CORRECTION_NOT_SUCCESSOR_BOUND")


def _transition_root(run_dir: Path) -> Path:
    root = Path(run_dir) / "generated-grades" / "correction-transitions"
    if root.is_symlink() or (root.exists() and not root.is_dir()):
        _fail("BAMF_ACTIVE_GENERATED_GRADE_CORRECTION_CUSTODY_UNSAFE")
    return root


def _record_path(run_dir: Path, digest: str) -> Path:
    return _transition_root(run_dir) / f"{digest}.json"


def _accepted_correction_matches(authority, correction) -> bool:
    return (
        correction.event_id == authority.correction_event_id
        and correction.source_receipt_sha256
            == authority.correction_source_receipt_sha256
        and correction.old_evidence_sha256
            == authority.correction_old_evidence_sha256
        and correction.new_evidence_sha256
            == authority.correction_new_evidence_sha256
        and correction.dependency.kind.value
            == authority.correction_dependency_kind
        and correction.dependency.key == authority.correction_dependency_key
        and correction.reason_code == authority.reason_code
    )


def _historical_accepted_corrections(
    run_dir: Path,
    manifest_sha256: str,
):
    """Verify C09 evidence at one accepted historical manifest without currentness."""
    from bilqis_mlx.runtime.bamf_bundle.codec import load_bamf_bundle
    from bilqis_mlx.runtime.bamf_bundle.source_authority_custody import (
        resolve_source_authority_registry,
    )
    from bilqis_mlx.runtime.accepted_correction_ledger import (
        _accepted_corrections_from_records,
        read_records,
    )

    root = Path(run_dir)
    student = load_bamf_bundle(
        root / "bamf-bundles" / manifest_sha256,
        expected_manifest_sha256=manifest_sha256,
    )
    registry = resolve_source_authority_registry(root, student.correction_frontier)
    if registry is None:
        _fail("BAMF_ACTIVE_GENERATED_GRADE_CORRECTION_AUTHORITY_DRIFT")
    records = read_records(root, manifest_sha256)
    return _accepted_corrections_from_records(records, registry)


def _authority_is_committed(run_dir: Path, authority_sha256: str) -> bool:
    from . import active_generated_grade_custody as custody
    root, definitions, activations = custody._roots(run_dir)
    pointer = custody._pointer_path(run_dir)
    current_activation = None
    if pointer.exists() or pointer.is_symlink():
        current_activation = custody._json(
            pointer, "BAMF_ACTIVE_GENERATED_GRADE_POINTER_INVALID").get(
                "activation_sha256")
    if not activations.exists():
        return False
    commits = custody._commit_root(run_dir)
    for path in activations.glob("*.json"):
        record = custody._json(
            path, "BAMF_ACTIVE_GENERATED_GRADE_RECORD_INVALID")
        if record.get("transition_receipt_sha256") != authority_sha256:
            continue
        activation_sha256 = record.get("activation_sha256")
        if (activation_sha256 == current_activation
                or (commits / f"{activation_sha256}.json").is_file()):
            return True
    return False


def _issue_correction_transition_authority(
    run_dir: Path,
    *,
    accepted_manifest_sha256: str,
    correction_record_sha256: str,
    predecessor: ActiveGeneratedGrade,
    proposal: GeneratedGradeProposal,
    definition: GeneratedGradeDefinition,
) -> CorrectionGradeTransitionAuthority:
    """Bind one correction to one successor; caller holds the B13 pointer lock."""
    from bilqis_mlx.runtime.accepted_corrections import accepted_corrections
    records = accepted_corrections(Path(run_dir), accepted_manifest_sha256)
    matches = tuple(item for item in records if item[0] == correction_record_sha256)
    if len(matches) != 1 or not records or records[-1][0] != correction_record_sha256:
        _fail("BAMF_ACTIVE_GENERATED_GRADE_CORRECTION_AUTHORITY_REQUIRED")
    correction = matches[0][1]
    relation_kind, relation_value = _relation(proposal, correction)
    provisional = dict(
        schema=CORRECTION_TRANSITION_SCHEMA,
        accepted_manifest_sha256=accepted_manifest_sha256,
        correction_record_sha256=correction_record_sha256,
        correction_event_id=correction.event_id,
        correction_source_receipt_sha256=correction.source_receipt_sha256,
        correction_old_evidence_sha256=correction.old_evidence_sha256,
        correction_new_evidence_sha256=correction.new_evidence_sha256,
        correction_dependency_kind=correction.dependency.kind.value,
        correction_dependency_key=correction.dependency.key,
        predecessor_activation_sha256=predecessor.activation_sha256,
        predecessor_definition_sha256=predecessor.definition.definition_sha256,
        predecessor_learner_foot_sha256=predecessor.definition.learner_foot_sha256,
        successor_proposal_sha256=proposal.proposal_sha256,
        successor_definition_sha256=definition.definition_sha256,
        successor_learner_foot_sha256=definition.learner_foot_sha256,
        relation_kind=relation_kind,
        relation_value=relation_value,
        reason_code=correction.reason_code,
        authority_sha256="0" * 64,
    )
    provisional["authority_sha256"] = _fingerprint(provisional)
    authority = _issue(**provisional)
    from . import active_generated_grade_custody as custody
    root = _transition_root(run_dir)
    if root.exists():
        for path in root.glob("*.json"):
            record = custody._json(
                path, "BAMF_ACTIVE_GENERATED_GRADE_CORRECTION_AUTHORITY_INVALID")
            if (record.get("correction_record_sha256") == correction_record_sha256
                    and record != authority.to_record()
                    and _authority_is_committed(
                        run_dir, record.get("authority_sha256", ""))):
                _fail("BAMF_ACTIVE_GENERATED_GRADE_CORRECTION_ALREADY_CONSUMED")
    custody._persist_immutable(
        _record_path(run_dir, authority.authority_sha256), authority.to_record(),
        "BAMF_ACTIVE_GENERATED_GRADE_CORRECTION_AUTHORITY_INVALID")
    return authority


def require_correction_transition_authority(
    run_dir: Path,
    active: ActiveGeneratedGrade,
) -> CorrectionGradeTransitionAuthority:
    if active.transition_kind != "CORRECTION" or not _sha(active.transition_receipt_sha256):
        _fail("BAMF_ACTIVE_GENERATED_GRADE_CORRECTION_AUTHORITY_INVALID")
    from . import active_generated_grade_custody as custody
    record = custody._json(
        _record_path(run_dir, active.transition_receipt_sha256),
        "BAMF_ACTIVE_GENERATED_GRADE_CORRECTION_AUTHORITY_INVALID")
    authority = _issue(**record)
    if (authority.authority_sha256 != active.transition_receipt_sha256
            or authority.predecessor_activation_sha256
               != active.predecessor_activation_sha256
            or authority.predecessor_definition_sha256
               != active.predecessor_definition_sha256
            or authority.successor_proposal_sha256 != active.proposal_sha256
            or authority.successor_definition_sha256
               != active.definition.definition_sha256
            or authority.successor_learner_foot_sha256
               != active.definition.learner_foot_sha256
            or authority.accepted_manifest_sha256 != active.activation_manifest_sha256
            or authority.reason_code != active.transition_reason):
        _fail("BAMF_ACTIVE_GENERATED_GRADE_CORRECTION_AUTHORITY_DRIFT")
    accepted = tuple(
        correction for digest, correction in _historical_accepted_corrections(
            Path(run_dir), authority.accepted_manifest_sha256)
        if digest == authority.correction_record_sha256)
    if len(accepted) != 1 or not _accepted_correction_matches(authority, accepted[0]):
        _fail("BAMF_ACTIVE_GENERATED_GRADE_CORRECTION_ANCESTRY_DRIFT")
    proposal = _read_issued_proposal(
        run_dir, authority.successor_proposal_sha256)
    relation_kind, relation_value = _relation(proposal, accepted[0])
    if (relation_kind != authority.relation_kind
            or relation_value != authority.relation_value):
        _fail("BAMF_ACTIVE_GENERATED_GRADE_CORRECTION_RELATION_DRIFT")
    root, definitions, activations = custody._roots(run_dir)
    predecessor_record = custody._json(
        activations / f"{authority.predecessor_activation_sha256}.json",
        "BAMF_ACTIVE_GENERATED_GRADE_CORRECTION_PREDECESSOR_INVALID")
    predecessor_definition = definition_from_record(custody._json(
        definitions / f"{authority.predecessor_definition_sha256}.json",
        "BAMF_ACTIVE_GENERATED_GRADE_CORRECTION_PREDECESSOR_INVALID"))
    predecessor = active_from_record(predecessor_record, predecessor_definition)
    if (predecessor.activation_sha256 != authority.predecessor_activation_sha256
            or predecessor.definition.definition_sha256
               != authority.predecessor_definition_sha256
            or predecessor.definition.learner_foot_sha256
               != authority.predecessor_learner_foot_sha256):
        _fail("BAMF_ACTIVE_GENERATED_GRADE_CORRECTION_PREDECESSOR_DRIFT")
    return authority
