"""Small source-located registry; helper suggestions never define its meanings."""
from __future__ import annotations

import copy
import itertools

from bilqis_logic.kernel import digest

SOURCES = {name: 'https://github.com/Entif-AI/Bilqis/issues/' + name for name in ('80','85','84')}
# Input types, result type, developmental stage. Definitions are executable in kernel.py.
SIGNATURES = {
    'MEMBER': (('Entity','Set'),'Boolean',5), 'SUBSET': (('Set','Set'),'Boolean',5),
    'INTERSECTION': (('Set','Set'),'Set',5), 'DIFFERENCE': (('Set','Set'),'Set',5),
    'DOMAIN': (('Function',),'Set',5), 'RANGE': (('Function',),'Set',5),
    'INVERSE': (('Function',),'Function',5), 'COMPOSITION': (('Function','Function'),'Function',5),
    'MAPS': (('Function','Entity','Entity'),'Boolean',5),
    'NEIGHBORS': (('Entity',),'Set',5), 'EDGE': (('Entity','Entity'),'Boolean',5),
    'PATH': (('Entity','Entity'),'Boolean',5),
    'IS_PROPOSITION': (('Proposition',),'Boolean',6), 'IS_ASSERTION': (('Event',),'Boolean',6),
    'IS_OBSERVATION': (('Event',),'Boolean',6),
    'ASSERTED_BY': (('Source','Proposition'),'Boolean',6), 'OBSERVED_BY': (('Source','Proposition'),'Boolean',6),
    'FORMAL_ENTAILS': (('Proposition',),'Boolean',6),
    'DERIVED_FROM': (('Event','Event'),'Boolean',6), 'DEPENDENCY': (('Event','Event'),'Boolean',6),
    'SUPERSEDES': (('Event','Event'),'Boolean',6), 'REVISES': (('Event','Event'),'Boolean',6),
    'IS_CURRENT': (('Event',),'Boolean',6),
    'CURRENT_STATE': (('Proposition',),'Evidence',6), 'HISTORICAL_STATE': (('Proposition',),'Evidence',6),
}

RECIPES = [
    ('set-membership','sets',['MEMBER'],'Test finite membership; changing one membership changes its Boolean answer.'),
    ('set-subset','sets',['SUBSET','MEMBER'],'Subset is universal membership, not one shared member; include empty sets.'),
    ('set-intersection','sets',['INTERSECTION','MEMBER'],'Membership in intersection requires membership in both input sets.'),
    ('set-difference','sets',['DIFFERENCE','MEMBER'],'Membership in directed difference requires the left set and exclusion from the right.'),
    ('function-domain','functions',['DOMAIN','MEMBER'],'A partial function domain contains inputs with defined mappings.'),
    ('function-range','functions',['RANGE','MEMBER'],'A function range contains outputs, contrasting domain and range.'),
    ('function-inverse','functions',['INVERSE','MAPS'],'An inverse is a partial function only for injective mappings; reverse the ordered pair.'),
    ('function-composition','functions',['COMPOSITION','MAPS'],'Composition g after f needs a matched intermediate output/input, and order matters.'),
    ('graph-neighborhood','graphs',['NEIGHBORS','MEMBER','EDGE'],'An outgoing neighborhood contains direct targets; reverse-edge targets are a hard contrast.'),
    ('graph-path','graphs',['PATH','EDGE'],'A directed positive-length path can exist without a direct edge; direction and missing links matter.'),
    ('epistemic-proposition','types',['IS_PROPOSITION','IS_ASSERTION'],'A proposition is a declared Boolean statement; declaring it is not an assertion event.'),
    ('epistemic-observation','types',['IS_OBSERVATION','IS_ASSERTION'],'An observation event and an assertion event retain distinct types even with identical content.'),
    ('source-attribution','attribution',['ASSERTED_BY','OBSERVED_BY','FORMAL_ENTAILS'],'An attributed assertion is not self-observation or formal entailment; reports do not rewrite facts.'),
    ('formal-entailment','attribution',['FORMAL_ENTAILS','ASSERTED_BY'],'Formal Horn-rule entailment comes from premises and rules, independently of source attribution.'),
    ('provenance-ancestry','lineage',['DERIVED_FROM','DEPENDENCY'],'Transitive provenance ancestry uses DERIVED_FROM edges, not declared proof-dependency edges.'),
    ('inferential-dependency','lineage',['DEPENDENCY','DERIVED_FROM'],'Inferential dependency follows separately declared DEPENDS_ON edges; ancestry alone cannot establish it.'),
    ('historical-supersession','revision',['SUPERSEDES','DERIVED_FROM','REVISES'],'SUPERSEDES replaces an earlier same-proposition event, without implying provenance or changed content.'),
    ('evidence-revision','revision',['REVISES','SUPERSEDES'],'Revision requires supersession and changed support/refutation; same-content supersession is not revision.'),
    ('current-evidence','state',['CURRENT_STATE','IS_CURRENT'],'Current evidence aggregates unsuperseded reports; removing supersession changes active evidence only.'),
    ('historical-evidence','state',['HISTORICAL_STATE','CURRENT_STATE'],'Historical evidence retains every report, including superseded reports; current and historical conflict may differ.'),
]


def candidates():
    rows=[]
    for identity,scope,ops,text in RECIPES:
        source='85' if SIGNATURES[ops[0]][2]==5 else '84'
        rows.append({'candidate_id':identity,'scope':scope,'source':source,'source_locator':SOURCES[source],
                     'operations':ops,'relation':'composition' if len(ops)>1 else 'prerequisite',
                     'description':text,'prerequisites':['micro.proof.entails','micro.compare.EQ'],
                     'law':identity})
    rows += [
        {'candidate_id':'collapse-provenance-supersession','scope':'revision','source':'84','source_locator':SOURCES['84'],
         'operations':['DERIVED_FROM','SUPERSEDES'],'relation':'equivalent','description':'Treat provenance ancestry as identical to historical supersession.',
         'prerequisites':['micro.proof.entails'],'law':'false-equivalence'},
        {'candidate_id':'collapse-report-truth','scope':'attribution','source':'84','source_locator':SOURCES['84'],
         'operations':['ASSERTED_BY','FORMAL_ENTAILS'],'relation':'equivalent','description':'Every attributed assertion proves its proposition true.',
         'prerequisites':['micro.proof.entails'],'law':'false-equivalence'},
    ]
    return rows


def law_check(identity):
    """Finite independent algebra witnesses; never a helper score threshold."""
    if identity.startswith('collapse-'):
        return {'valid':False,'counterexample':{'provenance':True,'supersession':False,'asserted':True,'entailed':False}}
    if identity not in {r[0] for r in RECIPES}: return {'valid':False,'reason':'unknown executable law'}
    scope=next(r[1] for r in RECIPES if r[0]==identity)
    def require(condition):
        if not condition:raise ValueError('independent finite law check failed')
    # Exhaust all subsets of a three-element domain, validating reusable set identities.
    subsets=[{i for i in range(3) if mask>>i&1} for mask in range(8)]
    for a,b in itertools.product(subsets,repeat=2):
        require((a<=b)==all(x in b for x in a))
        for x in range(3):
            require((x in a&b)==(x in a and x in b))
            require((x in a-b)==(x in a and x not in b))
    witnesses={'set_pairs':64}
    if scope=='functions':
        maps=[{i:v for i,v in enumerate(values) if v!=3} for values in itertools.product(range(4),repeat=3)]
        for f,g in itertools.product(maps,repeat=2):
            composed={(a,g[b]) for a,b in f.items() if b in g}
            require(composed=={(a,d) for a,b in f.items() for c,d in g.items() if b==c})
            if len(set(f.values()))==len(f):
                inverse={b:a for a,b in f.items()}
                require(all(inverse[f[a]]==a for a in f))
        witnesses['partial_function_pairs']=len(maps)**2
    if scope=='graphs':
        for mask in range(16):
            edges={(a,b) for i,(a,b) in enumerate(itertools.product(range(2),repeat=2)) if mask>>i&1}
            closure=set(edges)
            for _ in range(2):closure|={(a,d) for a,b in closure for c,d in closure if b==c}
            m=[[bool(mask & (1<<(2*a+b))) for b in range(2)] for a in range(2)]
            for k in range(2):
                for a,b in itertools.product(range(2),repeat=2):m[a][b]=m[a][b] or (m[a][k] and m[k][b])
            require(closure=={(a,b) for a,b in itertools.product(range(2),repeat=2) if m[a][b]})
        witnesses['directed_graphs']=16
    if scope in ('types','attribution','lineage','revision','state'):
        # Independently vary provenance, dependency, supersession and polarity.
        for derived,dependency,supersedes,old,new in itertools.product((False,True),repeat=5):
            edges={kind for kind,exists in zip(('DERIVED_FROM','DEPENDS_ON','SUPERSEDES'),(derived,dependency,supersedes)) if exists}
            require(('DERIVED_FROM' in edges)==derived and ('SUPERSEDES' in edges)==supersedes)
            history=(old or new,not old or not new)
            current=(new,not new) if supersedes else history
            require(current==((any(p for p in ([new] if supersedes else [old,new]))),any(not p for p in ([new] if supersedes else [old,new]))))
            revision=supersedes and old!=new
            require(revision==('SUPERSEDES' in edges and old!=new))
        witnesses['independent_event_edge_polarity_worlds']=32
        witnesses['attribution_counterexample']={'asserted':True,'observed':False,'entailed':False}
    return {'valid':True,'witnesses':witnesses,'definition_id':identity,
            'further_gate':'typed codec and two kernel oracles must agree on every compiled lesson before training'}


def admit(candidate,retrieved_ids,state,scope=None):
    result={'candidate_id':candidate.get('candidate_id'),'candidate_sha256':digest(candidate)}
    canonical={r['candidate_id']:r for r in candidates()}.get(candidate.get('candidate_id'))
    if canonical is None or candidate!=canonical:
        return dict(result,disposition='rejected',reason='source/identity/type/scope contract mismatch')
    if candidate['candidate_id'] not in retrieved_ids:
        return dict(result,disposition='deferred',reason='candidate absent from actual EG2 neighborhood')
    if scope is not None and candidate['scope']!=scope:
        return dict(result,disposition='rejected',reason='construction outside requested semantic scope')
    certificate=law_check(candidate['candidate_id'])
    if not certificate['valid']:
        return dict(result,disposition='rejected',reason='formal counterexample',certificate=certificate)
    if candidate['candidate_id'] in state:
        return dict(result,disposition='inert',reason='construction already admitted',certificate=certificate)
    if any(name not in SIGNATURES for name in candidate['operations']):
        return dict(result,disposition='rejected',reason='unresolved typed prerequisite')
    return dict(result,disposition='accepted',reason='source-located typed construction; independent formal admission',certificate=certificate,
                semantic_relations=[{'kind':candidate['relation'],'source':'development.op.'+candidate['operations'][0],
                                     'target':'development.op.'+o} for o in candidate['operations'][1:]],
                lesson_family=candidate['candidate_id'])


def extended_catalog(admissions=()):
    from bilqis_micro.graph import catalog,append_catalog
    additions=[]
    syntax=('sets','functions','edges','events','links','prior')
    literals={'Set':['K0','K1'],'Function':['F0','F1'],'Event':['E0','E1','E2','E3'],
              'EventKind':['ASSERT','OBSERVE','INFER'],'LinkKind':['DERIVED_FROM','DEPENDS_ON','SUPERSEDES']}
    for name in syntax:
        additions.append({'id':'development.syntax.'+name,'family':'syntax','subtype':name,'signature':'Syntax','arity':0,'stage':5,'edges':[]})
    for kind,names in literals.items():
        for name in names:
            additions.append({'id':'development.'+kind+'.'+name,'family':kind,'subtype':'identity','signature':kind,'arity':0,
                              'stage':5 if kind in ('Set','Function') else 6,'edges':[]})
    for name,(args,result,stage) in SIGNATURES.items():
        edges=[{'kind':'prerequisite','target':'micro.proof.entails' if stage==6 else 'micro.compare.EQ'}]
        for a in admissions:
            for e in a.get('semantic_relations',[]):
                if e['source']=='development.op.'+name: edges.append({'kind':e['kind'],'target':e['target']})
        additions.append({'id':'development.op.'+name,'family':'mathematics' if stage==5 else 'epistemic',
                          'subtype':name,'signature':'*'.join(args)+'->'+result,'arity':len(args),'stage':stage,
                          'scope':'finite-closed-world' if stage==5 else 'typed-declared-event-graphs',
                          'edges':list({digest(e):e for e in edges}.values())})
    return append_catalog(catalog(),additions)
