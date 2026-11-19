"""B09.2 owner-issued execution provenance for one optimizer step.

The owner derives the participation and the final legal mask from the executed
step and seals them into provenance. A caller cannot substitute an alternate
mask and keep a valid proof, because the mask is derived here and the record
cannot be minted outside this module.
"""
from __future__ import annotations

import hashlib
import json
from dataclasses import asdict, dataclass, field

from bilqis_mlx.errors import ErrorBus, SCHOOL

from .atlas_participation import (
    ActiveAdmittedRows, RoleReadParticipation, SemanticDenominator,
    StepParticipation, StepParticipationInputs, UpdateMask, parameter_update_mask,
    step_participation,
)

EXECUTION_PROVENANCE_SCHEMA = "bilqis.mlx.b09-execution-provenance/v1"
DIGEST_HEX_LENGTH = 64
_PROVENANCE_ISSUER = object()
_BOUND_AUTHORITY_DIGEST_INDEX = 3


def _invalid() -> None:
    ErrorBus.Raise(SCHOOL.MODEL_TOPOLOGY.INVALID)


def _is_digest(value) -> bool:
    """One lowercase hex digest identity, expressed as a domain contract."""
    return (isinstance(value, str) and len(value) == DIGEST_HEX_LENGTH
            and all(char in "0123456789abcdef" for char in value))


def _canonical(value) -> bytes:
    return (json.dumps(value, sort_keys=True, separators=(",", ":"),
                       ensure_ascii=False, allow_nan=False) + "\n").encode("utf-8")


def _digest(value) -> str:
    return hashlib.sha256(_canonical(value)).hexdigest()


def participation_digest(participation: StepParticipation) -> str:
    """Stable digest of one derived participation record."""
    return _digest(asdict(participation))


def mask_digest(mask: UpdateMask) -> str:
    """Stable digest of one derived update mask."""
    return _digest({
        "parameters": [asdict(item) for item in mask.parameters],
        "participating_identity_rows": [list(row) for row in mask.participating_identity_rows],
        "has_loss_bearing_target": mask.has_loss_bearing_target,
        "schema_version": mask.schema_version,
    })


@dataclass(frozen=True)
class StepExecutionProvenance:
    """One owner-issued proof of the executed step behind an optimizer update.

    The record carries the derived participation and the derived mask. It is
    minted only by `issue_execution_provenance`, so no caller can present an
    alternate mask as the executed truth.
    """

    participation: StepParticipation
    mask: UpdateMask
    eligible_parameter_names: tuple[str, ...]
    extents_sha256: str
    run_id: str
    generation: int
    parent_manifest_sha256: str
    parent_candidate_identity_sha256: str
    parent_optimizer_step: int
    topology_digest: str
    candidate_step: int
    schema_version: str = EXECUTION_PROVENANCE_SCHEMA
    _issuance: object = field(init=False, default=None, repr=False, compare=False)

    def __post_init__(self) -> None:
        if getattr(self, "_issuance", None) is not _PROVENANCE_ISSUER:
            _invalid()
        if (type(self.participation) is not StepParticipation
                or type(self.mask) is not UpdateMask
                or type(self.eligible_parameter_names) is not tuple
                or self.eligible_parameter_names != tuple(sorted(set(
                    self.eligible_parameter_names)))
                or not _is_digest(self.extents_sha256)
                or not isinstance(self.run_id, str) or not self.run_id
                or type(self.generation) is not int or self.generation < 1
                or not _is_digest(self.parent_manifest_sha256)
                or not _is_digest(self.parent_candidate_identity_sha256)
                or type(self.parent_optimizer_step) is not int
                or self.parent_optimizer_step < 0
                or not _is_digest(self.topology_digest)
                or type(self.candidate_step) is not int
                or self.candidate_step < 1
                or self.schema_version != EXECUTION_PROVENANCE_SCHEMA):
            _invalid()
        self.participation.__post_init__()
        self.mask.__post_init__()

    @property
    def digest(self) -> str:
        return _digest({
            "participation_sha256": participation_digest(self.participation),
            "mask_sha256": mask_digest(self.mask),
            "eligible_parameter_names": list(self.eligible_parameter_names),
            "extents_sha256": self.extents_sha256,
            "run_id": self.run_id,
            "generation": self.generation,
            "parent_manifest_sha256": self.parent_manifest_sha256,
            "parent_candidate_identity_sha256": self.parent_candidate_identity_sha256,
            "parent_optimizer_step": self.parent_optimizer_step,
            "topology_digest": self.topology_digest,
            "candidate_step": self.candidate_step,
            "schema_version": self.schema_version,
        })


def issue_execution_provenance(
        inputs: StepParticipationInputs,
        semantic_denominator: SemanticDenominator,
        motif_reads: tuple,
        role_reads: RoleReadParticipation,
        group_eligible,
        active_admitted: ActiveAdmittedRows,
        *, spec, extents, run_id: str, generation: int,
        parent_manifest_sha256: str, parent_candidate_identity_sha256: str,
        parent_optimizer_step: int, topology_digest: str,
        candidate_step_ordinal: int,
        precomputed_participation: StepParticipation | None = None,
) -> StepExecutionProvenance:
    """Derive the executed participation and mask, then seal them as provenance.

    The caller supplies what the execution path observed. The owner derives
    every participation and mask decision from that observation, so the
    returned proof cannot restate a different mask.
    """
    if precomputed_participation is None:
        participation = step_participation(
            inputs, semantic_denominator, motif_reads, role_reads)
    else:
        if any(value is not None for value in (
                inputs, semantic_denominator, motif_reads, role_reads)):
            _invalid()
        participation = precomputed_participation
        participation.__post_init__()
    mask = parameter_update_mask(
        group_eligible, participation, active_admitted, spec=spec, extents=extents)
    provenance = object.__new__(StepExecutionProvenance)
    for name, value in (
            ("participation", participation), ("mask", mask),
            ("eligible_parameter_names", tuple(sorted(
                group_eligible.eligible_parameter_names))),
            ("extents_sha256", extents.digest),
            ("run_id", run_id), ("generation", generation),
            ("parent_manifest_sha256", parent_manifest_sha256),
            ("parent_candidate_identity_sha256", parent_candidate_identity_sha256),
            ("parent_optimizer_step", parent_optimizer_step),
            ("topology_digest", topology_digest),
            ("candidate_step", candidate_step_ordinal),
            ("schema_version", EXECUTION_PROVENANCE_SCHEMA),
            ("_issuance", _PROVENANCE_ISSUER)):
        object.__setattr__(provenance, name, value)
    provenance.__post_init__()
    return provenance

def _make_execution_authority_registry():
    # Key by object identity, never dataclass equality. Weak references prevent stale
    # associations from surviving the provenance they authenticate.
    authorities = {}


    def _bind_execution_training_authority(provenance, loss_execution):
        import weakref
        from bilqis_mlx.runtime.atlas_model_contracts import require_bamf_loss_execution
        if type(provenance) is not StepExecutionProvenance:
            _invalid()
        provenance.__post_init__()
        require_bamf_loss_execution(loss_execution)
        authority = loss_execution.training_authority
        key = id(provenance)
        existing = authorities.get(key)
        if existing is not None and (existing[0]() is not provenance
                                     or existing[1] is not loss_execution):
            _invalid()
        digest = None if authority is None else authority.digest
        def remove(ref):
            current = authorities.get(key)
            if current is not None and current[0] is ref:
                authorities.pop(key, None)
        authorities[key] = (weakref.ref(provenance, remove), loss_execution, authority, digest)


    def require_execution_training_authority(provenance, training_authority):
        if type(provenance) is not StepExecutionProvenance:
            _invalid()
        current = authorities.get(id(provenance))
        if current is not None and current[0]() is not provenance:
            _invalid()
        bound = None if current is None else current[2]
        bound_closure = getattr(bound, 'artifact_closure_sha256', None)
        supplied_closure = getattr(training_authority, 'artifact_closure_sha256', None)
        if bound_closure is not None:
            if (training_authority is not bound
                    or bound.digest != current[_BOUND_AUTHORITY_DIGEST_INDEX]):
                _invalid()
        elif supplied_closure is not None:
            _invalid()

    return _bind_execution_training_authority, require_execution_training_authority


(_bind_execution_training_authority,
 require_execution_training_authority) = _make_execution_authority_registry()
