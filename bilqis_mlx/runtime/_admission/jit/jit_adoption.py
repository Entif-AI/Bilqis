"""Revalidate and commit a selected JIT proposal through the native transaction.

The public C07 policy owns lease/source scope. This owner removes the old executor
gap after those checks have succeeded: its native path independently replays the
persisted lease and accepted B13 parent, then publishes the exact A02-staged
candidate. A provisional ``DISPOSABLE_CONTRACT`` value by itself is never authority.
"""
from __future__ import annotations

from dataclasses import dataclass, replace
from pathlib import Path

from ..factory.jit_curriculum import ProposalDisposition, propose_curriculum_delta
from .atlas_lease_contracts import LeaseRunIdentity, _invalid, _sha
from .jit_adoption_native import (
    _accepted_native_retry,
    _authenticate_native_staged_candidate,
    _publish_native_staged_candidate,
)


def _accepted_lease_run_identity(run_identity) -> LeaseRunIdentity:
    """Project accepted B13 birth identity into the lease's frozen identity shape.

    The projection is a comparison value only.  It does not turn the
    ``DISPOSABLE_CONTRACT`` record into B13 authority; the accepted run remains
    authoritative and must be reloaded independently before mutation.
    """
    from bilqis_mlx.learning.champions import Checkpoint
    from bilqis_mlx.runtime.bamf_bundle.genesis import BamfRunIdentity

    if type(run_identity) is not BamfRunIdentity:
        _invalid("BAMF_ATLAS_ACCEPTED_RUN_IDENTITY_REQUIRED")
    return LeaseRunIdentity(
        run_identity.run_id,
        run_identity.initial_candidate_identity_sha256,
        run_identity.initial_topology_digest,
        Checkpoint(
            run_identity.origin_checkpoint_sha256,
            run_identity.origin_checkpoint_filename,
            run_identity.origin_optimizer_step,
            True,
        ),
    )


def resolve_ready_candidate(frontier, current, ledger, plan, checkpoint, proposal, staged):
    proposal.verify()
    if proposal.disposition is not ProposalDisposition.PROPOSAL:
        raise ValueError("JIT_ADOPTION_READY_PROPOSAL_REQUIRED")
    for item in staged:
        item.verify(frontier, current)
    fresh = propose_curriculum_delta(frontier, current, ledger, plan,
        checkpoint.sha256, checkpoint.optimizer_step,
        candidate_bindings=tuple(item.binding for item in staged))
    if fresh != proposal:
        raise ValueError("JIT_ADOPTION_PROPOSAL_CONTEXT_CHANGED")
    matches = tuple(item for item in staged if
        (item.candidate_id,) == proposal.selected_candidate_ids and
        item.successor.release_sha256 == proposal.selected_successor_sha256)
    if len(matches) != 1:
        raise ValueError("JIT_ADOPTION_EXACT_SUCCESSOR_REQUIRED")
    return matches[0]


def verify_current_implementations(successor, source_registry, answer_registry):
    """A sealed historical package cannot authorize changed provider code."""
    from bilqis_mlx.compatibility.source_adapter_resume import resume_adapter_compatible

    sources = {item.adapter_id: item for item in successor.source_adapters}
    for execution in successor.execution_plan.capabilities:
        binding = successor.source_bindings.by_capability[execution.capability_id]
        actual = source_registry.require(binding.generator_id, binding.oracle_id).descriptor
        admitted = sources.get(execution.provider_id)
        if (actual != admitted and
                not resume_adapter_compatible(admitted, actual)):
            raise ValueError("JIT_ADOPTION_SOURCE_IMPLEMENTATION_DRIFT")
    if tuple(answer_registry.require(item.kind).descriptor
             for item in successor.answer_modalities) != successor.answer_modalities:
        raise ValueError("JIT_ADOPTION_ANSWER_IMPLEMENTATION_DRIFT")


@dataclass(frozen=True)
class _PreparedSuccessorRuntime:
    """The one mutable learner lane as immutable executor inputs.

    Constructing this record grants no admission authority.  Every execution
    re-reads the admitted Factory release and school checkpoint from ``receipt``
    immediately before entering the existing prepared-successor transaction.
    """

    mx: object
    run_dir: Path
    receipt: dict
    grade_a_course: object
    source_root: Path | None
    graph: dict
    parameters: object
    optimizer: object
    reserve_gib: float
    native_pointer: dict | None = None

    def __post_init__(self):
        if (not isinstance(self.run_dir, Path) or not isinstance(self.receipt, dict)
                or not isinstance(self.graph, dict)
                or not isinstance(self.reserve_gib, (int, float))
                or self.reserve_gib < 0
                or (self.native_pointer is not None
                    and not isinstance(self.native_pointer, dict))):
            _invalid("BAMF_ATLAS_EXECUTOR_CONTEXT_INVALID")


def _execute_prepared_successor_adoption(
        runtime: _PreparedSuccessorRuntime, *, frontier, current, ledger, plan,
        checkpoint, proposal, staged, source_registry, answer_registry,
        native_staged=None, atlas_lease=None, source_authority=None):
    """Freshly revalidate then enter the existing atomic prepared-successor owner.

    This is deliberately a concrete owner, not a caller callback.  It cannot
    create a lease, reinterpret a source approval, or claim that a disposable
    C07 contract is production run authority.
    """
    if not isinstance(runtime, _PreparedSuccessorRuntime):
        _invalid("BAMF_ATLAS_EXECUTOR_RUNTIME_INVALID")
    selected = resolve_ready_candidate(
        frontier, current, ledger, plan, checkpoint, proposal, staged)
    verify_current_implementations(
        selected.successor, source_registry, answer_registry)

    from . import release_adoption, state as runtime_state
    from ..factory.schedule import schedule_program_from_executable_release

    native_inputs = (native_staged, atlas_lease, source_authority)
    if any(value is not None for value in native_inputs):
        if any(value is None for value in native_inputs):
            _invalid("BAMF_ATLAS_NATIVE_ADOPTION_ARGUMENT_INVALID")
        pointer = _publish_native_staged_candidate(
            runtime, selected, proposal, native_staged, atlas_lease,
            source_authority, current=current, checkpoint=checkpoint)
        return replace(runtime, native_pointer=pointer)

    from . import admission as runtime_admission
    admitted = runtime_admission._require_executable_factory_admission(
        runtime.run_dir, runtime.receipt, runtime.graph)
    program = schedule_program_from_executable_release(admitted)
    school = runtime_state._state_from_json(runtime.receipt["school"], program)
    if (admitted.release_sha256 != current.release_sha256
            or school.current_student != checkpoint):
        _invalid("BAMF_ATLAS_RUNTIME_CONTEXT_CHANGED")

    parameters, optimizer, graph, receipt, course = (
        release_adoption._adopt_prepared_successor(
            runtime.mx, runtime.run_dir, runtime.receipt,
            runtime.grade_a_course, runtime.source_root, runtime.graph,
            runtime.parameters, runtime.optimizer, selected,
            reserve_gib=float(runtime.reserve_gib)))
    return replace(
        runtime, receipt=receipt, grade_a_course=course, graph=graph,
        parameters=parameters, optimizer=optimizer)
