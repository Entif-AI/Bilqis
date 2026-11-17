"""Explicit generation-zero migration into #1314 active-grade custody."""
from __future__ import annotations

from dataclasses import dataclass, replace
import hashlib
from pathlib import Path

from bilqis_mlx.errors import ErrorBus, SCHOOL
from bilqis_mlx.factory import candidate_realizations
from bilqis_mlx.factory.atlas_frontier_contracts import _bytes
from bilqis_mlx.factory.generated_grade.definition import (
    GENERATED_GRADE_DEFINITION_V1,
    GeneratedGradeDefinition,
    GeneratedGradeMember,
)
from bilqis_mlx.runtime.state import _fingerprint


SCHEMA = "bilqis.bamf.initial-generated-grade-bootstrap/v1"
POLICY_SCHEMA = "bilqis.bamf.initial-generated-grade-bootstrap-policy/v1"
LEARNER_FOOT_SCHEMA = "bilqis.bamf.initial-generated-grade-bootstrap-foot/v1"
REASON = "DATA_DEFINED_INITIAL_GRADE_BOOTSTRAP"


def _fail(reason: str):
    ErrorBus.raise_(SCHOOL.BAMF_ATLAS_ADMISSION.INVALID, reason=reason)


def _semantic_ids(release, capability_id: str) -> tuple[str, ...]:
    spec = release.curriculum.capability_map[capability_id]
    result = set((*spec.taught_roots, *spec.examined_roots))
    try:
        result.add(candidate_realizations.realized_atlas_semantic_id(capability_id))
    except ValueError:
        pass
    return tuple(sorted(result))


def _members(release) -> tuple[GeneratedGradeMember, ...]:
    grades = release.execution_plan.grades
    if not grades or not grades[0].capabilities:
        _fail("BAMF_INITIAL_GENERATED_GRADE_SOURCE_MISSING")
    bindings = release.source_bindings.by_capability
    execution = release.execution_plan.capability_map
    curriculum = release.curriculum.capability_map
    result = []
    for capability_id in grades[0].capabilities:
        if (capability_id not in execution or capability_id not in curriculum
                or capability_id not in bindings):
            _fail("BAMF_INITIAL_GENERATED_GRADE_SOURCE_INVALID")
        semantics = _semantic_ids(release, capability_id)
        if not semantics:
            _fail("BAMF_INITIAL_GENERATED_GRADE_SOURCE_INVALID")
        for semantic_id in semantics:
            result.append(GeneratedGradeMember(
                semantic_id=semantic_id,
                capability_id=capability_id,
                source_anchor=bindings[capability_id].source_anchor,
                family_ids=(),
                proposal_disposition="SELECTED_TARGET",
                reason_codes=(REASON,),
            ))
    members = tuple(result)
    if len({item.semantic_id for item in members}) != len(members):
        _fail("BAMF_INITIAL_GENERATED_GRADE_MEMBER_AMBIGUOUS")
    return members


def _member_record(item: GeneratedGradeMember) -> dict:
    return {
        "semantic_id": item.semantic_id,
        "capability_id": item.capability_id,
        "source_anchor": item.source_anchor,
        "family_ids": list(item.family_ids),
        "proposal_disposition": item.proposal_disposition,
        "reason_codes": list(item.reason_codes),
    }


@dataclass(frozen=True)
class InitialGradeBootstrapProposal:
    run_id: str
    generation: int
    manifest_sha256: str
    acceptance_sha256: str
    current_release_sha256: str
    checkpoint_sha256: str
    optimizer_step: int
    a09_snapshot_sha256: str
    a09_closure_sha256: str
    learner_foot_sha256: str
    learner_evidence_epoch: int
    policy_epoch: int
    policy_sha256: str
    members: tuple[GeneratedGradeMember, ...]
    proposal_sha256: str
    schema: str = SCHEMA

    def to_record(self) -> dict:
        return {
            "schema": self.schema,
            "run_id": self.run_id,
            "generation": self.generation,
            "manifest_sha256": self.manifest_sha256,
            "acceptance_sha256": self.acceptance_sha256,
            "current_release_sha256": self.current_release_sha256,
            "checkpoint_sha256": self.checkpoint_sha256,
            "optimizer_step": self.optimizer_step,
            "a09_snapshot_sha256": self.a09_snapshot_sha256,
            "a09_closure_sha256": self.a09_closure_sha256,
            "learner_foot_sha256": self.learner_foot_sha256,
            "learner_evidence_epoch": self.learner_evidence_epoch,
            "policy_epoch": self.policy_epoch,
            "policy_sha256": self.policy_sha256,
            "members": [_member_record(item) for item in self.members],
            "proposal_sha256": self.proposal_sha256,
        }

    def expected_digest(self) -> str:
        payload = self.to_record()
        payload["proposal_sha256"] = "0" * 64
        return _fingerprint(payload)

    def verify(self) -> None:
        digests = (
            self.manifest_sha256, self.acceptance_sha256,
            self.current_release_sha256, self.checkpoint_sha256,
            self.a09_snapshot_sha256, self.a09_closure_sha256,
            self.learner_foot_sha256, self.policy_sha256, self.proposal_sha256,
        )
        if (self.schema != SCHEMA or not self.run_id or self.generation != 0
                or self.optimizer_step != 0 or self.learner_evidence_epoch < 0
                or self.policy_epoch < 0 or not self.members
                or any(not _sha(value) for value in digests)
                or len({item.semantic_id for item in self.members}) != len(self.members)
                or self.proposal_sha256 != self.expected_digest()):
            _fail("BAMF_INITIAL_GENERATED_GRADE_BOOTSTRAP_INVALID")

    @classmethod
    def from_record(cls, record: dict):
        expected = {
            "schema", "run_id", "generation", "manifest_sha256",
            "acceptance_sha256", "current_release_sha256", "checkpoint_sha256",
            "optimizer_step", "a09_snapshot_sha256", "a09_closure_sha256",
            "learner_foot_sha256", "learner_evidence_epoch", "policy_epoch",
            "policy_sha256", "members", "proposal_sha256",
        }
        try:
            if set(record) != expected:
                raise ValueError
            members = tuple(GeneratedGradeMember(
                semantic_id=item["semantic_id"], capability_id=item["capability_id"],
                source_anchor=item["source_anchor"], family_ids=tuple(item["family_ids"]),
                proposal_disposition=item["proposal_disposition"],
                reason_codes=tuple(item["reason_codes"]),
            ) for item in record["members"])
            result = cls(**{key: record[key] for key in expected - {"members"}}, members=members)
        except (KeyError, TypeError, ValueError):
            _fail("BAMF_INITIAL_GENERATED_GRADE_BOOTSTRAP_INVALID")
        result.verify()
        if result.to_record() != record:
            _fail("BAMF_INITIAL_GENERATED_GRADE_BOOTSTRAP_INVALID")
        return result


def _sha(value) -> bool:
    return (type(value) is str and len(value) == 64
            and all(char in "0123456789abcdef" for char in value))


def _path(run_dir: Path, proposal_sha256: str) -> Path:
    return (Path(run_dir) / "generated-grade-proposals" / "initial-bootstrap"
            / f"{proposal_sha256}.json")


def _build_proposal(identity, planning_epoch) -> InitialGradeBootstrapProposal:
    run_id, generation, manifest, acceptance = identity
    release = planning_epoch.current_release
    checkpoint = planning_epoch.checkpoint
    policy_sha256 = _fingerprint({
        "schema": POLICY_SCHEMA,
        "selection": "FIRST_EXECUTION_PLAN_GRADE",
        "factory_release_sha256": release.release_sha256,
        "capability_ids": list(release.execution_plan.grades[0].capabilities),
    })
    learner_foot_sha256 = _fingerprint({
        "schema": LEARNER_FOOT_SCHEMA,
        "checkpoint_sha256": checkpoint.sha256,
        "optimizer_step": checkpoint.optimizer_step,
        "factory_release_sha256": release.release_sha256,
        "qualification_epoch": planning_epoch.snapshot.qualification_epoch,
    })
    draft = InitialGradeBootstrapProposal(
        run_id, generation, manifest, acceptance, release.release_sha256,
        checkpoint.sha256, checkpoint.optimizer_step,
        planning_epoch.snapshot.snapshot_sha256, planning_epoch.closure.closure_sha256,
        learner_foot_sha256, planning_epoch.snapshot.qualification_epoch,
        planning_epoch.snapshot.policy_epoch, policy_sha256, _members(release),
        "0" * 64)
    result = replace(draft, proposal_sha256=draft.expected_digest())
    result.verify()
    return result


def issue_initial_grade_bootstrap(run_dir: Path, planning_epoch):
    from bilqis_mlx.runtime.priority_planning_owner import PriorityPlanningEpoch
    if type(planning_epoch) is not PriorityPlanningEpoch:
        _fail("BAMF_INITIAL_GENERATED_GRADE_PLANNING_EPOCH_REQUIRED")
    root = Path(run_dir)
    from .active_generated_grade_custody import _accepted_generation_identity, _persist_immutable
    identity = _accepted_generation_identity(root)
    from .atlas_lease_storage import classify_accepted_atlas_epoch
    if identity[1] != 0 or classify_accepted_atlas_epoch(root) != "staged":
        _fail("BAMF_INITIAL_GENERATED_GRADE_BOOTSTRAP_NOT_APPLICABLE")
    from .atlas_admission import read_accepted_atlas_factory_release
    accepted = read_accepted_atlas_factory_release(root)
    if accepted.release_sha256 != planning_epoch.current_release.release_sha256:
        _fail("BAMF_INITIAL_GENERATED_GRADE_ACCEPTED_RELEASE_DRIFT")
    from bilqis_mlx.factory.autonomy import evidence_complete_capabilities
    mastered = evidence_complete_capabilities(
        accepted, planning_epoch.evidence_ledger, plan=planning_epoch.autonomy_plan,
        current_checkpoint_sha256=planning_epoch.checkpoint.sha256,
        current_optimizer_step=planning_epoch.checkpoint.optimizer_step)
    if mastered or planning_epoch.checkpoint.optimizer_step != 0:
        _fail("BAMF_INITIAL_GENERATED_GRADE_LEARNER_NOT_NEWBORN")
    proposal = _build_proposal(identity, planning_epoch)
    _persist_immutable(
        _path(root, proposal.proposal_sha256), proposal.to_record(),
        "BAMF_INITIAL_GENERATED_GRADE_BOOTSTRAP_INVALID")
    return proposal


def read_initial_grade_bootstrap(run_dir: Path, proposal_sha256: str):
    from .active_generated_grade_custody import _json
    return InitialGradeBootstrapProposal.from_record(_json(
        _path(run_dir, proposal_sha256),
        "BAMF_INITIAL_GENERATED_GRADE_BOOTSTRAP_INVALID"))


def seal_initial_grade_bootstrap(proposal, release) -> GeneratedGradeDefinition:
    proposal.verify()
    release.verify()
    if (proposal.current_release_sha256 != release.release_sha256
            or proposal.members != _members(release)):
        _fail("BAMF_INITIAL_GENERATED_GRADE_BOOTSTRAP_DRIFT")
    verification_sha256 = hashlib.sha256(_bytes(release.verification)).hexdigest()
    draft = GeneratedGradeDefinition(
        adopted_release_sha256=release.release_sha256,
        release_lineage_sha256s=(release.release_sha256,),
        release_verification_sha256=verification_sha256,
        proposal_sha256=proposal.proposal_sha256,
        learner_foot_sha256=proposal.learner_foot_sha256,
        learner_evidence_epoch=proposal.learner_evidence_epoch,
        policy_epoch=proposal.policy_epoch,
        policy_sha256=proposal.policy_sha256,
        members=proposal.members,
        definition_sha256="0" * 64,
        schema=GENERATED_GRADE_DEFINITION_V1,
    )
    result = replace(draft, definition_sha256=draft.expected_digest())
    result.verify()
    return result


def require_initial_grade_bootstrap(run_dir: Path, active) -> None:
    proposal = read_initial_grade_bootstrap(run_dir, active.proposal_sha256)
    identity = (
        proposal.run_id, proposal.generation,
        proposal.manifest_sha256, proposal.acceptance_sha256)
    observed = (
        active.run_id, active.activation_generation,
        active.activation_manifest_sha256, active.activation_acceptance_sha256)
    if identity != observed or active.transition_receipt_sha256 != proposal.proposal_sha256:
        _fail("BAMF_INITIAL_GENERATED_GRADE_BOOTSTRAP_DRIFT")
    from .admission import _read_executable_factory_release_artifact
    release = _read_executable_factory_release_artifact(Path(run_dir), {
        "factory_release_sha256": proposal.current_release_sha256,
        "factory_release_file": (
            "factory-releases/" + proposal.current_release_sha256 + ".json"),
    })
    if seal_initial_grade_bootstrap(proposal, release) != active.definition:
        _fail("BAMF_INITIAL_GENERATED_GRADE_BOOTSTRAP_DRIFT")


def activate_initial_grade_bootstrap(run_dir: Path, planning_epoch):
    """Publish one explicit, neural-inert generation-zero migration activation."""
    root = Path(run_dir)
    proposal = issue_initial_grade_bootstrap(root, planning_epoch)
    identity = (
        proposal.run_id, proposal.generation,
        proposal.manifest_sha256, proposal.acceptance_sha256)
    definition = seal_initial_grade_bootstrap(
        proposal, planning_epoch.current_release)
    from .active_generated_grade_contracts import issue_active_generated_grade
    run_id, generation, manifest, acceptance = identity
    active = issue_active_generated_grade(
        run_id=run_id,
        activation_generation=generation,
        activation_manifest_sha256=manifest,
        activation_acceptance_sha256=acceptance,
        generated_grade_id=definition.definition_sha256,
        definition=definition,
        proposal_sha256=proposal.proposal_sha256,
        a09_snapshot_sha256=proposal.a09_snapshot_sha256,
        a09_closure_sha256=proposal.a09_closure_sha256,
        a09_proposal_sha256=None,
        predecessor_activation_sha256=None,
        predecessor_definition_sha256=None,
        transition_kind="BOOTSTRAP",
        transition_receipt_sha256=proposal.proposal_sha256,
        transition_reason=REASON,
    )
    from .active_generated_grade import _publish_if_current
    return _publish_if_current(
        root, identity, active, None, predecessor=None)
