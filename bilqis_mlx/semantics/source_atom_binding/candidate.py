"""An ABI candidate is source evidence, not permission to embed an atom."""
from dataclasses import dataclass

from ...errors import BilqisError


@dataclass(frozen=True)
class AtomCandidate:
    token_index: int | None = None
    semantic_id: str | None = None
    abi_index: int | None = None
    type_ids: tuple[str, ...] = ()
    reason_codes: tuple[str, ...] = ()


def find_candidate(atom, witness, snapshot, graph, source_projection):
    if atom.index >= len(witness.token_indices):
        return AtomCandidate(reason_codes=("SOURCE_ATOM_ROW_POSITION_UNMAPPED",))
    index = witness.token_indices[atom.index]
    tokens = graph["tokens"]
    if index >= len(tokens) or tokens[index] != atom.token:
        return AtomCandidate(index, reason_codes=("SOURCE_ATOM_ROW_TOKEN_MISMATCH",))
    if source_projection is not None:
        if (atom.index >= len(source_projection.semantic_ids)
                or atom.index >= len(source_projection.abi_indices)
                or atom.index >= len(source_projection.formal_signatures)):
            return AtomCandidate(index, reason_codes=("SOURCE_ATOM_OWNER_PROJECTION_INVALID",))
        return AtomCandidate(
            index,
            source_projection.semantic_ids[atom.index],
            source_projection.abi_indices[atom.index],
            (source_projection.formal_signatures[atom.index],),
        )
    try:
        entry = snapshot.abi(index)
    except BilqisError:
        entry = None
    if entry is None or entry.symbol != atom.token or not entry.active:
        return AtomCandidate(index, reason_codes=("SOURCE_ATOM_A01_ABI_UNMAPPED",))
    concept = next((item for item in snapshot.concepts
                    if item.concept.semantic_id == entry.semantic_id), None)
    types = tuple(sorted(set(concept.concept.types))) if concept is not None else ()
    reasons = () if types else ("SOURCE_ATOM_TYPE_AUTHORITY_UNAVAILABLE",)
    return AtomCandidate(index, entry.semantic_id, entry.index, types, reasons)
