"""Resolve visible raw atoms without promoting missing source authority."""
from __future__ import annotations

from ..atlas_projection import FrozenAtlasSnapshot
from ..context_eligibility import PUBLIC_FORMAL
from ..domains import contract_digest
from ..frame_compiler import (
    CompiledFrameBatch, FrameCompilerConfig, PositionKind,
    _grant_allows, atom_evidence_digest,
)
from .binding import make_binding
from .candidate import find_candidate
from .common import AtomBindingDisposition, SOURCE_ATOM_RIGHTS_SCHEMA, invalid
from .handoff import SourceAtomHandoff, make_handoff
from .witness import SourceAtomOwnerProjection, SourceRowWitness


def _rights_digest(config: FrameCompilerConfig, atom, source_id: str) -> tuple[str, bool]:
    evidence = atom_evidence_digest(source_id, atom, config.task.semantic_release)
    grant = next((item for item in config.frontier.grants
                  if item.source_handle == atom.source_reference), None)
    task = config.task
    state = (
        SOURCE_ATOM_RIGHTS_SCHEMA,
        (
            task.principal_id, task.tenant_id, task.purpose,
            task.semantic_release, task.jurisdiction, task.scope,
            task.observed_frontier, task.effective_time,
        ),
        config.policy,
        config.frontier.rights_epoch,
        config.frontier.correction_generation,
        grant,
    )
    return contract_digest(state), (
        grant is not None and grant.source_regime == PUBLIC_FORMAL
        and _grant_allows(grant, evidence, config, config.task.semantic_release))


def _resolve_atom(atom, compiled, config, snapshot, witness, graph, source_projection):
    rights_digest, rights_ok = _rights_digest(config, atom, compiled.source_instance_id)
    owned = (source_projection is not None
             and source_projection.ast.source_instance_id == compiled.source_instance_id
             and atom.index < len(source_projection.ast.atoms)
             and source_projection.ast.atoms[atom.index] == atom)
    candidate = find_candidate(
        atom, witness, snapshot, graph, source_projection if owned else None)
    reasons = set(candidate.reason_codes)
    if not rights_ok:
        reasons.add("SOURCE_ATOM_CURRENT_RIGHTS_HELD")
    if candidate.semantic_id is None:
        disposition = AtomBindingDisposition.UNMAPPED
    else:
        if not owned:
            reasons.update(("SOURCE_ATOM_REFERENCE_AUTHORITY_UNAVAILABLE",
                            "SOURCE_ATOM_INSTANCE_AUTHORITY_UNAVAILABLE"))
        disposition = (AtomBindingDisposition.SOURCE_HELD if reasons
                       else AtomBindingDisposition.BOUND)
    mapping_digest = (source_projection.mapping_digests[atom.index] if owned
                      else witness.mapping_digest(atom.index, candidate.token_index or 0, atom.token))
    return make_binding(
        source_instance_id=compiled.source_instance_id,
        atom_index=atom.index, token=atom.token, source_reference=atom.source_reference,
        source_evidence_digest=atom_evidence_digest(
            compiled.source_instance_id, atom, compiled.semantic_release),
        semantic_release=compiled.semantic_release,
        a01_bundle_id=snapshot.bundle_id, a01_source_bundle_id=snapshot.source_bundle_id,
        source_adapter_id=witness.source_adapter_id, source_token_index=candidate.token_index,
        mapping_record_digest=mapping_digest,
        candidate_semantic_id=candidate.semantic_id, candidate_abi_index=candidate.abi_index,
        candidate_type_ids=candidate.type_ids, rights_epoch=config.frontier.rights_epoch,
        correction_generation=config.frontier.correction_generation, rights_digest=rights_digest,
        visible_at_prefix=atom.index + 1, disposition=disposition,
        reason_codes=tuple(sorted(reasons)),
    )


def _resolve_visible_atoms(
    compiled: CompiledFrameBatch,
    config: FrameCompilerConfig,
    snapshot: FrozenAtlasSnapshot,
    witness: SourceRowWitness,
    graph: dict,
    *, source_projection: SourceAtomOwnerProjection | None = None,
) -> SourceAtomHandoff:
    """Resolve candidates; only rederived source projections can bind an atom."""
    if (type(compiled) is not CompiledFrameBatch
            or type(config) is not FrameCompilerConfig
            or type(snapshot) is not FrozenAtlasSnapshot
            or type(witness) is not SourceRowWitness
            or not isinstance(graph, dict)
            or not isinstance(graph.get("tokens"), list)
            or compiled.semantic_release != snapshot.release_sha256
            or config.task.semantic_release != compiled.semantic_release
            or config.schema_map.semantic_release != compiled.semantic_release
            or compiled.visible_end > config.task.causal_prefix_end
            or config.frontier.rights_epoch != config.policy.rights_epoch):
        invalid("BAMF_SOURCE_ATOM_AUTHORITY_INPUT_INVALID")
    compiled.__post_init__()
    config.__post_init__()
    witness.__post_init__()
    if source_projection is not None and (
            type(source_projection) is not SourceAtomOwnerProjection
            or len(source_projection.ast.atoms) != len(witness.token_indices)
            or len(source_projection.formal_signatures) != len(witness.token_indices)
            or len(source_projection.mapping_digests) != len(witness.token_indices)
            or len(source_projection.semantic_ids) != len(witness.token_indices)
            or len(source_projection.abi_indices) != len(witness.token_indices)):
        invalid("BAMF_SOURCE_ATOM_OWNER_PROJECTION_INVALID")
    atoms = tuple(
        item.atom for item in compiled.positions
        if item.kind is PositionKind.ATOM)
    if (len(atoms) != compiled.visible_end
            or tuple(atom.index for atom in atoms) != tuple(range(compiled.visible_end))):
        invalid("BAMF_SOURCE_ATOM_COMPILED_PREFIX_INVALID")

    bindings = tuple(_resolve_atom(
        atom, compiled, config, snapshot, witness, graph, source_projection) for atom in atoms)
    return make_handoff(
        source_instance_id=compiled.source_instance_id,
        visible_end=compiled.visible_end,
        semantic_release=compiled.semantic_release,
        a01_bundle_id=snapshot.bundle_id,
        a01_source_bundle_id=snapshot.source_bundle_id,
        source_adapter_id=witness.source_adapter_id,
        bindings=tuple(bindings),
    )


def _revalidate_from_verified_snapshot(
    handoff: SourceAtomHandoff,
    compiled: CompiledFrameBatch,
    config: FrameCompilerConfig,
    snapshot: FrozenAtlasSnapshot,
    witness: SourceRowWitness,
    graph: dict,
) -> SourceAtomHandoff:
    expected = _resolve_visible_atoms(compiled, config, snapshot, witness, graph)
    if handoff != expected:
        invalid("BAMF_SOURCE_ATOM_HANDOFF_AUTHORITY_DRIFT")
    return expected


def require_embedding_ready(
    handoff: SourceAtomHandoff,
    compiled: CompiledFrameBatch,
    config: FrameCompilerConfig,
    snapshot: FrozenAtlasSnapshot,
    witness: SourceRowWitness,
    graph: dict,
) -> tuple[tuple[int, tuple[str, ...]], ...]:
    """Internal B02/B03 seam: held/unmapped atoms never authorize raw vectors."""
    expected = _revalidate_from_verified_snapshot(
        handoff, compiled, config, snapshot, witness, graph)
    if not expected.embedding_ready:
        invalid("BAMF_SOURCE_ATOM_BINDING_HELD")
    return tuple(
        (item.candidate_abi_index, item.candidate_type_ids)
        for item in expected.bindings
        if item.candidate_abi_index is not None)
