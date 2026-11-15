"""Revalidate source atoms and derive all supported compiled vectors in B01 custody."""
from ...semantics.source_atom_binding.common import invalid
from ...semantics.frame_schema import AtomicFrame
from ..frame_embeddings import ConceptBatch, embed_atoms
from ..frame_encoder import (
    AtomicFrameEmbedding, CompiledEncoderInput, CompiledEmbeddingVectors,
    MemberEmbedding, encode_frames,
)
from .embedding import source_atom_vectors


def _atomic_source_embeddings(compiled, atom_rows):
    """Bind one-atom fallbacks to the exact already-authorized source vector."""
    if any(compiled.atomic_handles) and (
            compiled.source_asts is None
            or compiled.partial_forest_receipts is None):
        invalid("BAMF_SOURCE_ATOM_ATOMIC_FRAME_SOURCE_PROOF_REQUIRED")
    rows = []
    for handles, vectors, row in zip(
            compiled.atomic_handles, atom_rows, compiled.compiled.rows):
        embeddings = []
        for handle in handles:
            frame = handle.projection.frame(handle.frame_handle)
            span = frame.source_span
            if (type(frame) is not AtomicFrame or span.end != span.start + 1
                    or not 0 <= span.start < row.visible_end):
                invalid("BAMF_SOURCE_ATOM_ATOMIC_FRAME_SPAN_UNAVAILABLE")
            embeddings.append(AtomicFrameEmbedding(handle, vectors[span.start]))
        rows.append(tuple(embeddings))
    return tuple(rows)


def encode_source_compiled_with_handoffs(
    compiled, parameters, sources, feature_schema, banks, artifact_owner, *, snapshot=None,
):
    """Encode actual A05 rows and return the verified source handoff closure.

    Atomic fallbacks preserve their exact source atom embedding unchanged. A
    fallback spanning more than one raw atom remains held because no composition
    law is declared for it. Raw atoms, ordinary frames and verified nested frames
    use the existing B02/B03 operations. The returned handoffs are observations
    from the same validation that produced the vectors; callers cannot supply them.
    """
    if (type(compiled) is not CompiledEncoderInput or type(sources) is not tuple
            or len(sources) != len(compiled.compiled.rows)):
        invalid("BAMF_SOURCE_ATOM_COMPILED_INPUT_INVALID")
    compiled.__post_init__()
    atom_rows, member_rows, handoffs = [], [], []
    for row, config, source, requests in zip(
            compiled.compiled.rows, compiled.compiler_configs,
            sources, compiled.member_requests):
        vectors, row_banks, handoff = source_atom_vectors(
            parameters, row, config, source, compiled.features,
            feature_schema, compiled.extents, banks, artifact_owner,
            snapshot=snapshot)
        atom_rows.append(vectors)
        handoffs.append(handoff)
        if requests:
            members = embed_atoms(
                parameters, ConceptBatch((requests,), row_banks, compiled.extents),
                compiled.features, atlas_selection=source.selection)[0]
            member_rows.append(tuple(MemberEmbedding(request, members[index])
                                     for index, request in enumerate(requests)))
        else:
            member_rows.append(())
    atomic_rows = _atomic_source_embeddings(compiled, tuple(atom_rows))
    generated = CompiledEmbeddingVectors(
        tuple(atom_rows), tuple(member_rows), atomic_rows)
    return encode_frames(
        compiled, generated, parameters,
        atlas_selections=tuple(source.selection for source in sources)), tuple(handoffs)


def encode_source_compiled(
        compiled, parameters, sources, feature_schema, banks, artifact_owner, *, snapshot=None):
    """Compatibility surface returning only the differentiable encoded frames."""
    encoded, _ = encode_source_compiled_with_handoffs(
        compiled, parameters, sources, feature_schema, banks, artifact_owner,
        snapshot=snapshot)
    return encoded
