"""Seal generated-grade proposals only against one exact executable Factory release."""
from __future__ import annotations

from dataclasses import dataclass, fields, replace
import hashlib

from bilqis_mlx.factory.atlas_frontier_contracts import _bytes, _fail
from bilqis_mlx.factory.executable_release import ExecutableFactoryRelease

from .contracts import GeneratedGradeProposal


@dataclass(frozen=True)
class GeneratedGradeMember:
    semantic_id: str
    capability_id: str
    source_anchor: str
    family_ids: tuple[str, ...]
    proposal_disposition: str


@dataclass(frozen=True)
class GeneratedGradeDefinition:
    adopted_release_sha256: str
    release_lineage_sha256s: tuple[str, ...]
    release_verification_sha256: str
    proposal_sha256: str
    learner_foot_sha256: str
    learner_evidence_epoch: int
    policy_epoch: int
    policy_sha256: str
    members: tuple[GeneratedGradeMember, ...]
    definition_sha256: str
    schema: str = "bilqis.generated-grade-definition/v1"

    @property
    def member_semantic_ids(self) -> tuple[str, ...]:
        return tuple(item.semantic_id for item in self.members)

    def expected_digest(self) -> str:
        return hashlib.sha256(_bytes({
            field.name: getattr(self, field.name)
            for field in fields(self) if field.name != "definition_sha256"
        })).hexdigest()

    def verify(self) -> None:
        digests = (
            self.adopted_release_sha256, self.release_verification_sha256,
            self.proposal_sha256, self.learner_foot_sha256,
            self.policy_sha256, self.definition_sha256,
        )
        if (self.schema != "bilqis.generated-grade-definition/v1"
                or any(not _sha(value) for value in digests)
                or not self.release_lineage_sha256s
                or any(not _sha(value) for value in self.release_lineage_sha256s)
                or self.release_lineage_sha256s[-1] != self.adopted_release_sha256
                or not self.members
                or self.members != tuple(self.members)
                or len({item.semantic_id for item in self.members}) != len(self.members)
                or self.definition_sha256 != self.expected_digest()):
            _fail("BAMF_GENERATED_GRADE_DEFINITION_INVALID")


def seal_generated_grade(
    proposal: GeneratedGradeProposal,
    adopted_release: ExecutableFactoryRelease,
    member_capability_bindings: tuple[tuple[str, str], ...],
    *,
    release_lineage: tuple[ExecutableFactoryRelease, ...] | None = None,
) -> GeneratedGradeDefinition:
    """Bind a proposal to executable members; activation remains #1314 authority."""
    if (type(proposal) is not GeneratedGradeProposal
            or not isinstance(adopted_release, ExecutableFactoryRelease)
            or type(member_capability_bindings) is not tuple):
        _fail("BAMF_GENERATED_GRADE_DEFINITION_INPUT_INVALID")
    proposal.verify()
    adopted_release.verify()
    lineage = release_lineage or (adopted_release,)
    if (not lineage or lineage[-1].release_sha256 != adopted_release.release_sha256
            or lineage[0].release_sha256 != proposal.current_release_sha256):
        _fail("BAMF_GENERATED_GRADE_RELEASE_LINEAGE_INVALID")
    for predecessor, successor in zip(lineage, lineage[1:]):
        successor.verify_successor_of(predecessor)
    binding_map = dict(member_capability_bindings)
    if (len(binding_map) != len(member_capability_bindings)
            or set(binding_map) != set(proposal.member_semantic_ids)):
        _fail("BAMF_GENERATED_GRADE_MEMBER_BINDING_INVALID")
    capability_map = adopted_release.curriculum.capability_map
    executable_capabilities = adopted_release.execution_plan.capability_map
    source_bindings = adopted_release.source_bindings.by_capability
    decisions = {item.semantic_id: item for item in proposal.decisions}
    members = []
    for semantic_id in proposal.member_semantic_ids:
        capability_id = binding_map[semantic_id]
        capability = capability_map.get(capability_id)
        source_binding = source_bindings.get(capability_id)
        decision = decisions.get(semantic_id)
        if (capability is None or capability_id not in executable_capabilities
                or source_binding is None
                or decision is None or capability_id not in decision.compiled_capability_ids
                or source_binding.source_anchor not in decision.source_anchor_ids
                or decision.disposition not in {"SELECTED_TARGET", "SELECTED_BRIDGE"}):
            _fail("BAMF_GENERATED_GRADE_MEMBER_NOT_EXECUTABLE")
        members.append(GeneratedGradeMember(
            semantic_id,
            capability_id,
            source_binding.source_anchor,
            decision.family_ids,
            decision.disposition,
        ))
    verification_sha256 = hashlib.sha256(_bytes(adopted_release.verification)).hexdigest()
    provisional = GeneratedGradeDefinition(
        adopted_release.release_sha256,
        tuple(item.release_sha256 for item in lineage),
        verification_sha256,
        proposal.proposal_sha256,
        proposal.learner_foot_sha256,
        proposal.learner_evidence_epoch,
        proposal.policy_epoch,
        proposal.policy_sha256,
        tuple(members),
        "0" * 64,
    )
    result = replace(provisional, definition_sha256=provisional.expected_digest())
    result.verify()
    return result


def _sha(value: object) -> bool:
    return (type(value) is str and len(value) == 64
            and all(char in "0123456789abcdef" for char in value))
