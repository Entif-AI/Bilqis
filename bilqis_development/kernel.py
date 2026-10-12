"""Finite set/function/graph worlds and distinct typed epistemic event graphs.

The codec supplies only raw symbolic worlds and unreduced prefix queries. The
student never receives closures, set results, current masks or oracle answers.
"""
from __future__ import annotations

import copy

from bilqis_micro import kernel as prior
from bilqis_micro.graph import ID as OLD_ID
from .registry import SIGNATURES,extended_catalog

TOKENS=extended_catalog()['tokens']
ID={name:i for i,name in enumerate(TOKENS)}
TYPES={'Entity':list('ABCDE'),'Set':['K0','K1'],'Function':['F0','F1'],
       'Event':['E0','E1','E2','E3'],'Source':['S0','S1','S2'],'Proposition':['J0','J1','J2']}
BITS={'UNKNOWN':(False,False),'TRUE':(True,False),'FALSE':(False,True),'CONFLICT':(True,True)}


def const(kind,name):return {'kind':'const','type':kind,'name':name}
def op(name,*args):return {'kind':'op','op':name,'args':list(args)}
def inherited(expression):return {'kind':'prior','expression':copy.deepcopy(expression)}


def world(entities,*,base=None,sets=None,functions=None,edges=(),events=(),links=()):
    entities=sorted(entities)
    return {'base':copy.deepcopy(base) if base is not None else prior.world(entities),
            'sets':{k:sorted((sets or {}).get(k,[])) for k in ('K0','K1')},
            'functions':{k:sorted(copy.deepcopy((functions or {}).get(k,[]))) for k in ('F0','F1')},
            'edges':sorted(copy.deepcopy(list(edges))),'events':sorted(copy.deepcopy(list(events))),
            'links':sorted(copy.deepcopy(list(links)))}


def _keys(x,*keys):
    if not isinstance(x,dict) or set(x)!=set(keys):raise ValueError('exact typed fields required')


def _ordered(rows):
    if not isinstance(rows,list) or rows!=sorted(rows) or len({str(r) for r in rows})!=len(rows):
        raise ValueError('canonical unique symbolic list required')


def validate_world(w):
    _keys(w,'base','sets','functions','edges','events','links')
    prior.validate_world(w['base']);entities=w['base']['entities']
    if w['base']['reports'] or w['base']['live']!=[0]:raise ValueError('new event worlds use one interpretation; legacy reports remain in prior tasks')
    _keys(w['sets'],'K0','K1');_keys(w['functions'],'F0','F1')
    for values in w['sets'].values():
        _ordered(values)
        if any(v not in entities for v in values):raise ValueError('set outside finite universe')
    for pairs in list(w['functions'].values())+[w['edges']]:
        _ordered(pairs)
        if any(not isinstance(p,list) or len(p)!=2 or any(v not in entities for v in p) for p in pairs):
            raise ValueError('finite ordered pair required')
    for pairs in w['functions'].values():
        if len({a for a,b in pairs})!=len(pairs):raise ValueError('mapping is not a partial function')
    _ordered(w['events']);_ordered(w['links']);event_map={}
    for e in w['events']:
        if (not isinstance(e,list) or len(e)!=5 or e[0] not in TYPES['Event'] or e[1] not in ('ASSERT','OBSERVE','INFER')
                or e[2] not in TYPES['Source'] or e[3] not in w['base']['propositions'] or e[4] not in ('support','refute')
                or e[0] in event_map):raise ValueError('typed event declaration')
        event_map[e[0]]=e
    for link in w['links']:
        if (not isinstance(link,list) or len(link)!=3 or link[0] not in ('DERIVED_FROM','DEPENDS_ON','SUPERSEDES')
                or any(e not in event_map for e in link[1:]) or link[1]<=link[2]):
            raise ValueError('acyclic newer-to-earlier event relation')
        a,b=[event_map[e] for e in link[1:]]
        if link[0]=='SUPERSEDES' and a[3]!=b[3]:raise ValueError('supersession must retain proposition identity')
        if link[0]=='DEPENDS_ON' and a[1]!='INFER':raise ValueError('declared proof dependency requires an inference event')


def expression_type(e,w,depth=0):
    if not isinstance(e,dict) or depth>10:raise ValueError('typed expression/depth')
    if e.get('kind')=='const':
        _keys(e,'kind','type','name')
        if e['type'] not in TYPES or e['name'] not in TYPES[e['type']]:raise ValueError('typed constant identity')
        if e['type']=='Entity' and e['name'] not in w['base']['entities']:raise ValueError('entity outside universe')
        return e['type']
    if e.get('kind')=='prior':
        _keys(e,'kind','expression')
        return prior._type(e['expression'],w['base'])
    _keys(e,'kind','op','args')
    if e['kind']!='op' or not isinstance(e['args'],list):raise ValueError('typed application')
    name=e['op'];types=[expression_type(a,w,depth+1) for a in e['args']]
    if name in ('AND','OR','NOT'):
        if len(types)!=(1 if name=='NOT' else 2) or any(t not in ('Boolean','Evidence') for t in types):
            raise ValueError('logical scope/type mismatch')
        return 'Evidence' if 'Evidence' in types else 'Boolean'
    if name not in SIGNATURES or tuple(types)!=SIGNATURES[name][0]:raise ValueError('operator signature mismatch')
    if name=='INVERSE':
        pairs=_eval(e['args'][0],w,False)
        if len({b for a,b in pairs})!=len(pairs):raise ValueError('inverse is not a function for noninjective mapping')
    return SIGNATURES[name][1]


def record(w,q):
    r={'task':'development','world':copy.deepcopy(w),'query':copy.deepcopy(q)}
    validate_record(r);return r


def validate_record(r):
    if r.get('task')!='development':return prior.validate_record(r)
    _keys(r,'task','world','query');validate_world(r['world'])
    if expression_type(r['query'],r['world']) not in ('Boolean','Evidence'):raise ValueError('answer type')


def _closure(edges,nodes,independent):
    if independent:
        index={v:i for i,v in enumerate(nodes)};n=len(nodes)
        matrix=[[False]*n for _ in nodes]
        for a,b in edges:matrix[index[a]][index[b]]=True
        for k in range(n):
            for i in range(n):
                for j in range(n):matrix[i][j]=matrix[i][j] or (matrix[i][k] and matrix[k][j])
        return {(a,b) for a in nodes for b in nodes if matrix[index[a]][index[b]]}
    result=set(map(tuple,edges));changed=True
    while changed:
        extra={(a,d) for a,b in result for c,d in result if b==c}-result
        changed=bool(extra);result|=extra
    return result


def _eval(e,w,independent):
    if e['kind']=='prior':
        f=prior.independent_evaluate if independent else prior.evaluate
        return BITS[f(prior.record(w['base'],e['expression']))]
    if e['kind']=='const':
        if e['type']=='Set':return set(w['sets'][e['name']])
        if e['type']=='Function':return set(map(tuple,w['functions'][e['name']]))
        return e['name']
    name=e['op'];v=[_eval(a,w,independent) for a in e['args']]
    if name in ('AND','OR','NOT'):
        return (prior._evidence_operation if independent else prior._evidence_table)(name,v)
    if name=='MEMBER':
        if independent:
            domain=w['base']['entities'];mask=sum(1<<domain.index(x) for x in v[1]);return bool(mask & (1<<domain.index(v[0])))
        return v[0] in v[1]
    if name=='SUBSET':return all(x in v[1] for x in v[0]) if independent else v[0]<=v[1]
    if name=='INTERSECTION':return {x for x in v[0] if x in v[1]} if independent else v[0]&v[1]
    if name=='DIFFERENCE':return {x for x in v[0] if x not in v[1]} if independent else v[0]-v[1]
    if name=='DOMAIN':return {a for a,b in v[0]}
    if name=='RANGE':return {b for a,b in v[0]}
    if name=='INVERSE':return {(b,a) for a,b in v[0]}
    if name=='COMPOSITION':
        if independent:
            first,second=map(dict,v);return {(a,second[b]) for a,b in first.items() if b in second}
        return {(a,d) for a,b in v[0] for c,d in v[1] if b==c}
    if name=='MAPS':return dict(v[0]).get(v[1])==v[2] if independent else (v[1],v[2]) in v[0]
    if name=='NEIGHBORS':return {b for a,b in w['edges'] if a==v[0]}
    if name=='EDGE':return list(v) in w['edges']
    if name=='PATH':return tuple(v) in _closure(w['edges'],w['base']['entities'],independent)
    events={e[0]:e for e in w['events']}
    if name=='IS_PROPOSITION':return v[0] in w['base']['propositions']
    if name in ('IS_ASSERTION','IS_OBSERVATION'):
        return v[0] in events and events[v[0]][1]==('ASSERT' if name=='IS_ASSERTION' else 'OBSERVE')
    if name in ('ASSERTED_BY','OBSERVED_BY'):
        return any(e[1]==('ASSERT' if name=='ASSERTED_BY' else 'OBSERVE') and e[2:4]==v for e in events.values())
    if name=='FORMAL_ENTAILS':
        if v[0] not in w['base']['propositions']:return False
        f=prior.independent_evaluate if independent else prior.evaluate
        return f(prior.record(w['base'],prior.entails(w['base']['propositions'][v[0]])))=='TRUE'
    if name in ('DERIVED_FROM','DEPENDENCY'):
        kind='DERIVED_FROM' if name=='DERIVED_FROM' else 'DEPENDS_ON'
        return tuple(v) in _closure([l[1:] for l in w['links'] if l[0]==kind],list(events),independent)
    if name in ('SUPERSEDES','REVISES'):
        linked=['SUPERSEDES',*v] in w['links']
        return linked and (name=='SUPERSEDES' or events[v[0]][4]!=events[v[1]][4])
    superseded={l[2] for l in w['links'] if l[0]=='SUPERSEDES'}
    if name=='IS_CURRENT':return v[0] in events and v[0] not in superseded
    if name in ('CURRENT_STATE','HISTORICAL_STATE'):
        selected=[e for e in events.values() if e[3]==v[0] and (name=='HISTORICAL_STATE' or e[0] not in superseded)]
        if independent:
            mask=0
            for event in selected:mask|=1 if event[4]=='support' else 2
            return bool(mask&1),bool(mask&2)
        polarities={e[4] for e in selected};return 'support' in polarities,'refute' in polarities
    raise ValueError('unimplemented operator')


def _evaluate(r,independent):
    validate_record(r)
    if r['task']!='development':return (prior.independent_evaluate if independent else prior.evaluate)(r)
    value=prior._bits(_eval(r['query'],r['world'],independent))
    return {v:k for k,v in BITS.items()}[value]


def evaluate(r):return _evaluate(r,False)
def independent_evaluate(r):return _evaluate(r,True)


def _constant_id(kind,name):
    prefix={'Entity':'micro.entity.','Source':'micro.source.','Proposition':'micro.proposition.'}.get(kind,'development.'+kind+'.')
    return ID[prefix+name]


def _prefix(e):
    if e['kind']=='const':return [_constant_id(e['type'],e['name'])]
    if e['kind']=='prior':return [ID['development.syntax.prior']]+prior._prefix(e['expression'])
    token='micro.evidence.'+e['op'] if e['op'] in ('AND','OR','NOT') else 'development.op.'+e['op']
    return [ID[token]]+[t for a in e['args'] for t in _prefix(a)]


def encode(r):
    validate_record(r)
    if r['task']!='development':return prior.encode(r)
    w=r['world'];dummy=prior.record(w['base'],{'kind':'literal','value':True})
    old=prior.encode(dummy);ids=old[:old.index(OLD_ID['micro.syntax.query'])]
    ids += [ID['development.syntax.sets']]
    for name,values in w['sets'].items():ids += [_constant_id('Set',name)]+[_constant_id('Entity',v) for v in values]
    ids += [ID['development.syntax.functions']]
    for name,pairs in w['functions'].items():
        ids += [_constant_id('Function',name)]+[_constant_id('Entity',v) for pair in pairs for v in pair]
    ids += [ID['development.syntax.edges']]+[_constant_id('Entity',v) for pair in w['edges'] for v in pair]
    ids += [ID['development.syntax.events']]
    for name,kind,source,prop,polarity in w['events']:
        ids += [_constant_id('Event',name),ID['development.EventKind.'+kind],_constant_id('Source',source),
                _constant_id('Proposition',prop),ID['micro.report.'+polarity]]
    ids += [ID['development.syntax.links']]
    for kind,a,b in w['links']:ids += [ID['development.LinkKind.'+kind],_constant_id('Event',a),_constant_id('Event',b)]
    return ids+[ID['micro.syntax.query']]+_prefix(r['query'])+[ID['syntax.end']]


def _prior_expression(ids,pos):
    token=TOKENS[ids[pos]];pos+=1
    if token.startswith('micro.entity.'):return prior.entity(token.split('.')[-1]),pos
    if token.startswith('micro.bound.'):return prior.bound(int(token.split('.')[-1])),pos
    if token in ('cogal.value.true','cogal.value.false'):return {'kind':'literal','value':token.endswith('true')},pos
    if token.startswith('micro.quantifier.'):
        a,pos=_prior_expression(ids,pos);return prior.quantify(token.split('.')[-1],a),pos
    if token=='micro.proof.entails':
        if TOKENS[ids[pos]]!='micro.proof.conclusion':raise ValueError('proof conclusion delimiter')
        a,pos=_prior_expression(ids,pos+1);return prior.entails(a),pos
    if token=='micro.evidence.observe':return prior.observe(TOKENS[ids[pos]].split('.')[-1]),pos+1
    if token.startswith(('micro.relation.','micro.compare.','cogal.operator.','micro.evidence.')):
        from bilqis_logic.kernel import OPERATORS
        name=token.split('.')[-1];arity=2 if token.startswith(('micro.relation.','micro.compare.')) else OPERATORS[name]
        args=[]
        for _ in range(arity):a,pos=_prior_expression(ids,pos);args.append(a)
        if token.startswith('micro.relation.'):return prior.relation(name,*args),pos
        if token.startswith('micro.compare.'):return prior.compare(name,*args),pos
        if token.startswith('micro.evidence.'):return prior.evidence_logic(name,*args),pos
        return prior.logic(name,*args),pos
    raise ValueError('unsupported inherited expression codec')


def _expression(ids,pos):
    token=TOKENS[ids[pos]];pos+=1
    if token=='development.syntax.prior':
        a,pos=_prior_expression(ids,pos);return inherited(a),pos
    for kind in TYPES:
        for name in TYPES[kind]:
            if token==TOKENS[_constant_id(kind,name)]:return const(kind,name),pos
    name=token.split('.')[-1]
    if token.startswith('development.op.'):arity=len(SIGNATURES[name][0])
    elif token in ('micro.evidence.AND','micro.evidence.OR','micro.evidence.NOT'):arity=1 if name=='NOT' else 2
    else:raise ValueError('unknown typed query token')
    args=[]
    for _ in range(arity):a,pos=_expression(ids,pos);args.append(a)
    return op(name,*args),pos


def decode(ids):
    if not isinstance(ids,list) or any(type(i)is not int or i<0 or i>=len(TOKENS) for i in ids):raise ValueError('token ABI')
    if ID['development.syntax.sets'] not in ids:return prior.decode(ids)
    try:
        start=ids.index(ID['development.syntax.sets'])
        base=prior.decode(ids[:start]+[OLD_ID['micro.syntax.query'],7,OLD_ID['syntax.end']])['world']
        sections={}
        for name,next_name in zip(('sets','functions','edges','events','links'),('functions','edges','events','links','query')):
            a=ids.index(ID['development.syntax.'+name])+1
            b=ids.index(ID[('micro.syntax.' if next_name=='query' else 'development.syntax.')+next_name])
            sections[name]=[TOKENS[i] for i in ids[a:b]]
        sets={k:[] for k in ('K0','K1')};functions={k:[] for k in ('F0','F1')}
        for name,kind,target in (('sets','Set',sets),('functions','Function',functions)):
            current=None;values=[]
            for token in sections[name]:
                if token.startswith('development.'+kind+'.'):
                    if current is not None:target[current]=values if name=='sets' else [values[i:i+2] for i in range(0,len(values),2)]
                    current=token.split('.')[-1];values=[]
                else:
                    if not token.startswith('micro.entity.'):raise ValueError('typed section token')
                    values.append(token.split('.')[-1])
            target[current]=values if name=='sets' else [values[i:i+2] for i in range(0,len(values),2)]
        tail=lambda x:x.split('.')[-1]
        edges=[list(map(tail,sections['edges'][i:i+2])) for i in range(0,len(sections['edges']),2)]
        events=[list(map(tail,sections['events'][i:i+5])) for i in range(0,len(sections['events']),5)]
        links=[list(map(tail,sections['links'][i:i+3])) for i in range(0,len(sections['links']),3)]
        q,end=_expression(ids,ids.index(ID['micro.syntax.query'])+1)
        if end!=len(ids)-1 or ids[-1]!=ID['syntax.end']:raise ValueError('query trailing tokens')
        r=record(world(base['entities'],base=base,sets=sets,functions=functions,edges=edges,events=events,links=links),q)
        if encode(r)!=ids:raise ValueError('noncanonical symbolic encoding')
        return r
    except (IndexError,KeyError,TypeError) as exc:raise ValueError('malformed developmental tokens') from exc
