"""Shared non-neural source/context fixtures for Atlas training tests."""
from bilqis_mlx.semantics.atlas_features import AtlasFeatures, ConceptFeature
from bilqis_mlx.semantics.context_eligibility import (
    PUBLIC_FORMAL, ContextEligibility, ContextMember, ContextPolicy,
    SourceFrontier, SourceGrant, TaskScope, frame_evidence_digest,
    member_evidence_digest,
)
from bilqis_mlx.semantics.frame_compiler import (
    SourceAtom, StreamingAST, atom_evidence_digest,
)
from bilqis_mlx.semantics.frame_schema import (
    ConceptRef, FrameSchema, FrameTree, RoleOccurrence, RoleSpec, SourceSpan,
    make_frame_instance,
)


def _source_context(rows, release, visible_ends, policy_mode, graph=None):
    """Issue real A13 synthetic source grants for the actual visible ASTs."""
    principal, tenant = "synthetic:person", "synthetic:tenant"
    region, scope = "synthetic:region", "synthetic:task"
    semantic_release = '0' * 64
    policy_epoch = 1
    envelopes = {}
    grants = {}
    for row in rows:
        tokens = row.get("tokens", ())
        end = visible_ends.get(
            row.get("id"), len(tokens) if isinstance(tokens, (tuple, list)) else 0)
        if not isinstance(tokens, (tuple, list)) or not 0 < end <= len(tokens):
            continue
        ast = source_ast_for(tuple(tokens[:end]), release, graph)
        if ast.source_instance_id in envelopes:
            continue
        identity = ast.source_instance_id
        frame = ast.frames[0].root
        member = ContextMember(
            "subject", 0, "source:member:" + ast.source_instance_id, end)
        frame_source = "source:frame:" + ast.source_instance_id
        evidence = (
            (frame_source, frame_evidence_digest(frame)),
            (member.source_handle, member_evidence_digest(frame, member)),
            *((atom.source_reference,
               atom_evidence_digest(ast.source_instance_id, atom, semantic_release))
              for atom in ast.atoms[:end]),
        )
        for handle, digest in evidence:
            grants[handle] = SourceGrant(
                handle, principal, tenant, PUBLIC_FORMAL, semantic_release, digest,
                ("TRAINING",), (region,), (scope,),
                rights_epoch=1, correction_generation=1,
                observed_at=2, effective_from=0)
        envelopes[identity] = ContextEligibility(
            frame_handle="frame:" + identity, frame=frame,
            source_handle=frame_source, members=(member,),
            principal_id=principal, tenant_id=tenant,
            purpose="TRAINING", source_regime=PUBLIC_FORMAL,
            semantic_release=semantic_release, jurisdiction=region,
            scope=scope, join_class=PUBLIC_FORMAL,
            policy_epoch=policy_epoch, rights_epoch=1,
            correction_generation=1, observed_at=2,
            effective_from=0, effective_until=None,
            causal_prefix_end=end)
    prefix = max((item.causal_prefix_end for item in envelopes.values()), default=1)
    task = TaskScope(
        principal, tenant, "TRAINING", semantic_release, region, scope,
        observed_frontier=3, effective_time=5, causal_prefix_end=prefix)
    allowed_purposes = ("TRAINING",) if policy_mode == "allow" else ("SERVING",)
    policy = ContextPolicy(
        "synthetic:policy", policy_epoch, 1,
        allowed_purposes, (PUBLIC_FORMAL,), (region,), (scope,),
        (PUBLIC_FORMAL,), ((PUBLIC_FORMAL, PUBLIC_FORMAL),),
        ((PUBLIC_FORMAL, PUBLIC_FORMAL, PUBLIC_FORMAL),))
    frontier = SourceFrontier(
        1, 1, tuple(sorted(grants.values(), key=lambda item: item.source_handle)))

    def frames_for_ast(ast):
        item = envelopes.get(ast.source_instance_id)
        return (item,) if item is not None else ()

    return frames_for_ast, task, frontier, policy


def _training_schema():
    return FrameSchema(
        'fixture:training-frame', 1, 'source:factory-fixture',
        (RoleSpec('subject', ('Entity',), 1, 1),),
        'ORDERED', 'synthetic')


def source_ast_for(tokens, release='fixture-release', graph=None):
    value = ','.join(str(token) for token in tokens)
    source_instance_id = 'synthetic:ast:' + value
    token_names = (
        graph.get('tokens') if isinstance(graph, dict)
        and isinstance(graph.get('tokens'), list) else
        ['fixture.padding', 'cogal.value.false', 'cogal.value.true'])
    atoms = tuple(
        SourceAtom(index, token_names[token], f'{source_instance_id}#atom:{index}')
        for index, token in enumerate(tokens))
    schema = _training_schema()
    frame = make_frame_instance(
        schema,
        source_instance_id=source_instance_id,
        structural_path=(),
        source_span=SourceSpan(0, len(tokens)),
        parent_occurrence_id=None,
        bindings=(RoleOccurrence(
            'subject', 0, concept=ConceptRef(
                'fixture:entity:' + value, '0' * 64, 0,
                ('Entity',), source_instance_id)),),
        causal_prefix_end=len(tokens))
    return StreamingAST(source_instance_id, atoms, (FrameTree(frame),))


def answer_plan_for(prefix, release, capability, kind):
    head = next(head for head in release.answer_heads if head.kind == kind)
    return {'modalityID': head.modality_id, 'input_prefix_end': prefix.visible_end,
            'decisions': [{'id': 'value', 'roleID': 'answer', 'occurrence': 0,
                           'kind': 'VALUE', 'legalValues': list(head.values), 'depends_on': []},
                          {'id': 'end', 'roleID': 'end', 'occurrence': 0,
                           'kind': 'CONTROL', 'legalValues': ['END_FRAME'], 'depends_on': ['value']}],
            'allowedOutputSchema': 'fixture', 'maximum_decisions': 2,
            'generation_binding': release.release_sha256}


def _atlas_features(asts: tuple[StreamingAST, ...], semantic_release: str) -> AtlasFeatures:
    concepts = {}
    for ast in asts:
        for tree in ast.frames:
            frame = tree.root
            if not hasattr(frame, 'bindings'):
                continue
            for binding in frame.bindings:
                candidates = ((binding.concept,) if binding.concept is not None
                              else binding.alternatives)
                for concept in candidates:
                    concepts[concept.semantic_id] = ConceptFeature(
                        concept.semantic_id, concept.abi_index, concept.type_ids,
                        (0.0,) * 64, 'ADMITTED_SOURCE')
    return AtlasFeatures(
        semantic_release, 'fixture:atlas', 'fixture:source', None,
        (('Entity', 2),), (('subject', 2),),
        (('fixture:training-frame', 2),),
        tuple(concepts[key] for key in sorted(concepts)), ())
