"""Reproduce raw input identity and native formal signatures from source owners."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path

from ...errors import BilqisError
from ...generated_assessment import digest
from ...semantics.domains import contract_digest
from ...semantics.frame_compiler import SourceAtom, StreamingAST
from ...semantics.source_atom_binding.common import invalid
from ...semantics.source_atom_binding.witness import SourceAtomOwnerProjection


ROOT = Path(__file__).resolve().parents[3]
PROJECTION_SCHEMA = "bilqis.source-atom-owner-projection/v1"
REFERENCE_SCHEMA = "bilqis.source-atom-reference/v1"
GRAPH_EXTENSION_SCHEMA = "bilqis.source-atom-graph-extension/v1"


def canonical_graph_for(generator: str, source_root: str | Path, row: dict | None = None) -> dict:
    """Resolve only existing source owners, never a caller-selected token graph."""
    from ..copular import GENERATOR as COPULAR_GENERATOR, ORACLE as COPULAR_ORACLE
    from ..school import live_source_registry
    from ...semantics.frame_adapters.registry import source_frame_strategy

    owner = live_source_registry().resolve_owner(generator)
    if (generator == COPULAR_GENERATOR and
            COPULAR_ORACLE in owner.descriptor.accepted_oracle_ids):
        from ..copular_curriculum import expanded_graph
        from ...live_grade_c import registry_graph
        expected_root = ROOT
        graph = expanded_graph(registry_graph())
    else:
        try:
            expected_root, graph = source_frame_strategy(
                owner.descriptor.adapter_id).graph_resolver(row)
        except (BilqisError, KeyError, OSError, TypeError, ValueError):
            invalid("SOURCE_ATOM_SOURCE_ADAPTER_UNSUPPORTED")
    if Path(source_root).resolve() != expected_root.resolve():
        invalid("SOURCE_ATOM_SOURCE_ROOT_DRIFT")
    return graph


def require_canonical_graph(row: dict, graph: dict, source_root: str | Path) -> dict:
    canonical = canonical_graph_for(row["generator"], source_root, row=row)
    if digest(graph) != digest(canonical):
        invalid("SOURCE_ATOM_SOURCE_GRAPH_DRIFT")
    return canonical


def project_verified_row(row, graph, snapshot, witness) -> SourceAtomOwnerProjection:
    """Project a row already reproduced by the canonical adapter.

    The accepted prior registry is the type owner for the historical ABI.
    A formal signature such as Entity*Entity->Boolean stays intact; it is
    neither replaced with Boolean nor asserted to be an A06 categorical type.
    """
    source_id = row.get("source_id") or row.get("id")
    if not isinstance(source_id, str) or not source_id:
        invalid("SOURCE_ATOM_INSTANCE_AUTHORITY_UNAVAILABLE")
    path = ROOT / "bilqis_mlx/semantics/copular_registry_v1.json"
    payload = path.read_bytes()
    if hashlib.sha256(payload).hexdigest() != snapshot.prior_abi_sha256:
        invalid("SOURCE_ATOM_NATIVE_REGISTRY_DRIFT")
    native = json.loads(payload)
    if digest(native["rows"]) != native["native_rows_sha256"]:
        invalid("SOURCE_ATOM_NATIVE_REGISTRY_DRIFT")
    records = native["rows"][1:]
    atoms, signatures, mappings = [], [], []
    semantic_ids, abi_indices = [], []
    for position, token_index in enumerate(witness.token_indices):
        node = graph["nodes"][token_index]
        token = graph["tokens"][token_index]
        row_contract = graph["row_contract_sha256"].get(token)
        if token_index < len(records):
            record = records[token_index]
            if (int(record[0]) != token_index or record[1] != token
                    or node.get("id") != token
                    or record[4] != node.get("signature")
                    or record[13] != row_contract
                    or not record[4]):
                invalid("SOURCE_ATOM_NATIVE_ABI_CONTRACT_DRIFT")
            signature = record[4]
            semantic_id = record[2]
            abi_index = token_index
            mapping_authority = tuple(record)
        else:
            from ...semantics.frame_adapters.registry import source_frame_strategy
            resolver = source_frame_strategy(
                witness.source_adapter_id).atlas_semantic_resolver
            if resolver is None:
                invalid("SOURCE_ATOM_GRAPH_EXTENSION_AUTHORITY_DRIFT")
            try:
                atlas_semantic_id = resolver(row)
                entry = snapshot.abi_for_semantic(atlas_semantic_id)
            except (BilqisError, TypeError, ValueError):
                invalid("SOURCE_ATOM_GRAPH_EXTENSION_AUTHORITY_DRIFT")
            signature = node.get("signature")
            if (node.get("id") != token
                    or not isinstance(node.get("semantic_id"), str)
                    or not node.get("semantic_id")
                    or not isinstance(signature, str) or not signature
                    or not isinstance(row_contract, str) or not row_contract):
                invalid("SOURCE_ATOM_GRAPH_EXTENSION_AUTHORITY_DRIFT")
            mapping_authority = (
                GRAPH_EXTENSION_SCHEMA, token_index, token,
                node["semantic_id"], entry.index, entry.symbol,
                entry.semantic_id,
                signature, row_contract)
            semantic_id = entry.semantic_id
            abi_index = entry.index
        reference = "source-atom:" + contract_digest((
            REFERENCE_SCHEMA, witness.source_adapter_id, source_id, position))
        atoms.append(SourceAtom(position, token, reference))
        signatures.append(signature)
        semantic_ids.append(semantic_id)
        abi_indices.append(abi_index)
        mappings.append(contract_digest((
            PROJECTION_SCHEMA, snapshot.prior_abi_sha256,
            witness.mapping_digest(position, token_index, token),
            source_id, reference, mapping_authority)))
    return SourceAtomOwnerProjection(
        StreamingAST(source_id, tuple(atoms), ()),
        tuple(signatures), tuple(mappings),
        tuple(semantic_ids), tuple(abi_indices))
