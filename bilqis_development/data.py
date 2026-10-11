"""Deterministic, provenance-bearing lessons and frozen unseen-world probes."""
from __future__ import annotations

from collections import Counter
import copy
import random

from bilqis_logic.kernel import digest
from bilqis_micro import kernel as prior
from bilqis_micro.graph import RULE
from .kernel import world,const,op,inherited,record,evaluate,independent_evaluate,encode,decode,_closure
from .registry import RECIPES,SOURCES

FAMILIES={str(stage):[r[0] for r in RECIPES if (5 if r[1] in ('sets','functions','graphs') else 6)==stage] for stage in (5,6)}


def make_world(stage,rng,varied=False):
    entities=list('ABCDE')[:rng.choice((4,5)) if varied else rng.choice((2,3,4))]
    a,b,c=[rng.choice(entities) for _ in range(3)]
    pairs=[(x,y) for x in entities for y in entities]
    facts=[('PARENT',x,y) for x,y in rng.sample(pairs,rng.randrange(3))]
    rules=[RULE] if rng.random()<.5 else []
    props={} if stage==5 else {'J0':prior.relation('PARENT',prior.entity(a),prior.entity(b)),
                               'J1':prior.relation('GRANDPARENT',prior.entity(a),prior.entity(c))}
    base=prior.world(entities,facts,rules=rules,propositions=props)
    sets={name:[e for e in entities if rng.random()<.4] for name in ('K0','K1')}
    functions={}
    for name in ('F0','F1'):
        count=rng.randrange(min(len(entities),3)+1) if stage==5 else rng.randrange(2)
        inputs=rng.sample(entities,count);outputs=rng.sample(entities,count)
        functions[name]=[list(p) for p in zip(inputs,outputs)]
    edges=[list(p) for p in rng.sample(pairs,rng.randrange(4 if stage==5 else 3))]
    events=[];links=[]
    if stage==6:
        for i in range(rng.randrange(5)):
            events.append(['E'+str(i),rng.choice(('ASSERT','OBSERVE','INFER')),rng.choice(('S0','S1','S2')),
                           rng.choice(('J0','J1')),rng.choice(('support','refute'))])
        for newer in events:
            for older in events:
                if newer[0]<=older[0]:continue
                if rng.random()<.22:links.append(['DERIVED_FROM',newer[0],older[0]])
                if newer[1]=='INFER' and rng.random()<.3:links.append(['DEPENDS_ON',newer[0],older[0]])
                if newer[3]==older[3] and rng.random()<.35:links.append(['SUPERSEDES',newer[0],older[0]])
    return world(entities,base=base,sets=sets,functions=functions,edges=edges,events=events,links=links)


def terms(w,rng,family=None,assisted=False):
    a,b,c=[const('Entity',rng.choice(w['base']['entities'])) for _ in range(3)]
    p=const('Proposition',rng.choice(('J0','J1','J2')));s=const('Source',rng.choice(('S0','S1','S2')))
    e=const('Event',rng.choice(('E0','E1','E2','E3')));h=const('Event',rng.choice(('E0','E1','E2','E3')))
    # Sample both witnessed and unconstrained queries. No witness or computed
    # result is encoded; the complete raw world and query are still supplied.
    if rng.random()<.5:
        f0=set(map(tuple,w['functions']['F0']));f1=set(map(tuple,w['functions']['F1']))
        domain={x for x,y in f0};image={y for x,y in f0};chosen=[]
        if family=='set-membership':chosen=w['sets']['K0']
        elif family=='set-intersection':chosen=sorted(set(w['sets']['K0'])&set(w['sets']['K1']))
        elif family=='set-difference':chosen=sorted(set(w['sets']['K0'])-set(w['sets']['K1']))
        elif family=='function-domain':chosen=sorted(domain-image if assisted else domain)
        elif family=='function-range':chosen=sorted(image-domain if assisted else image)
        if chosen:a=const('Entity',rng.choice(chosen))
        if family=='function-inverse':
            choices=[(y,x) for x,y in sorted(f0) if not assisted or (y,x) not in f0]
            if choices:x,y=rng.choice(choices);a,b=const('Entity',x),const('Entity',y)
        if family=='function-composition':
            forwards={(x,z) for x,y in f0 for t,z in f1 if y==t}
            backwards={(x,z) for x,y in f1 for t,z in f0 if y==t}
            choices=sorted(forwards-backwards if assisted else forwards)
            if choices:x,z=rng.choice(choices);a,c=const('Entity',x),const('Entity',z)
        if family in ('graph-neighborhood','graph-path'):
            edges=set(map(tuple,w['edges']))
            choices=edges if family=='graph-neighborhood' else _closure(w['edges'],w['base']['entities'],False)
            if assisted:
                choices=({(x,y) for x,y in choices if (y,x) not in edges} if family=='graph-neighborhood' else choices-edges)
            if choices:x,y=rng.choice(sorted(choices));a,b=const('Entity',x),const('Entity',y)
        events={ev[0]:ev for ev in w['events']}
        if family in ('provenance-ancestry','inferential-dependency','historical-supersession','evidence-revision'):
            kind={'provenance-ancestry':'DERIVED_FROM','inferential-dependency':'DEPENDS_ON',
                  'historical-supersession':'SUPERSEDES','evidence-revision':'SUPERSEDES'}[family]
            choices=set(tuple(l[1:]) for l in w['links'] if l[0]==kind)
            if family in ('provenance-ancestry','inferential-dependency'):
                choices=_closure(choices,list(events),False)
            if family=='evidence-revision':choices={(x,y) for x,y in choices if events[x][4]!=events[y][4]}
            if assisted and family!='evidence-revision':
                other='DEPENDS_ON' if kind=='DERIVED_FROM' else 'DERIVED_FROM'
                choices-=_closure([l[1:] for l in w['links'] if l[0]==other],list(events),False)
            if choices:x,y=rng.choice(sorted(choices));e,h=const('Event',x),const('Event',y)
        if family=='epistemic-observation':
            choices=[ev[0] for ev in w['events'] if ev[1]=='OBSERVE']
            if choices:e=const('Event',rng.choice(choices))
        if family=='source-attribution':
            choices=[ev for ev in w['events'] if ev[1]=='ASSERT']
            if choices:ev=rng.choice(choices);s,p=const('Source',ev[2]),const('Proposition',ev[3])
        if family=='formal-entailment':
            choices=[j for j,q in w['base']['propositions'].items() if prior.evaluate(prior.record(w['base'],prior.entails(q)))=='TRUE']
            if choices:p=const('Proposition',rng.choice(choices))
        if family in ('current-evidence','historical-evidence') and w['events']:
            p=const('Proposition',rng.choice(w['events'])[3])
    return a,b,c,const('Set','K0'),const('Set','K1'),const('Function','F0'),const('Function','F1'),p,s,e,h


def query(family,w,rng):
    a,b,c,k,l,f,g,p,s,e,h=terms(w,rng,family)
    expressions={
        'set-membership':op('MEMBER',a,k),'set-subset':op('SUBSET',k,l),
        'set-intersection':op('MEMBER',a,op('INTERSECTION',k,l)),
        'set-difference':op('MEMBER',a,op('DIFFERENCE',k,l)),
        'function-domain':op('MEMBER',a,op('DOMAIN',f)), 'function-range':op('MEMBER',a,op('RANGE',f)),
        'function-inverse':op('MAPS',op('INVERSE',f),a,b),
        'function-composition':op('MAPS',op('COMPOSITION',f,g),a,c),
        'graph-neighborhood':op('MEMBER',b,op('NEIGHBORS',a)), 'graph-path':op('PATH',a,b),
        'epistemic-proposition':op('IS_PROPOSITION',p), 'epistemic-observation':op('IS_OBSERVATION',e),
        'source-attribution':op('ASSERTED_BY',s,p),'formal-entailment':op('FORMAL_ENTAILS',p),
        'provenance-ancestry':op('DERIVED_FROM',e,h),'inferential-dependency':op('DEPENDENCY',e,h),
        'historical-supersession':op('SUPERSEDES',e,h),'evidence-revision':op('REVISES',e,h),
        'current-evidence':op('CURRENT_STATE',p),'historical-evidence':op('HISTORICAL_STATE',p),
    }
    return expressions[family]


def assisted_query(family,w,rng):
    """Each selected construction compiles a specific law/contrast exercise."""
    a,b,c,k,l,f,g,p,s,e,h=terms(w,rng,family,True)
    contrasts={
        'set-membership':op('AND',op('MEMBER',a,k),op('NOT',op('MEMBER',a,l))),
        'set-subset':op('AND',op('SUBSET',k,l),op('MEMBER',a,k)),
        'set-intersection':op('AND',op('MEMBER',a,op('INTERSECTION',k,l)),op('MEMBER',a,k)),
        'set-difference':op('AND',op('MEMBER',a,k),op('NOT',op('MEMBER',a,l))),
        'function-domain':op('AND',op('MEMBER',a,op('DOMAIN',f)),op('NOT',op('MEMBER',a,op('RANGE',f)))),
        'function-range':op('AND',op('MEMBER',a,op('RANGE',f)),op('NOT',op('MEMBER',a,op('DOMAIN',f)))),
        'function-inverse':op('AND',op('MAPS',op('INVERSE',f),a,b),op('NOT',op('MAPS',f,a,b))),
        'function-composition':op('AND',op('MAPS',op('COMPOSITION',f,g),a,c),op('NOT',op('MAPS',op('COMPOSITION',g,f),a,c))),
        'graph-neighborhood':op('AND',op('MEMBER',b,op('NEIGHBORS',a)),op('NOT',op('EDGE',b,a))),
        'graph-path':op('AND',op('PATH',a,b),op('NOT',op('EDGE',a,b))),
        'epistemic-proposition':op('AND',op('IS_PROPOSITION',p),op('NOT',op('IS_ASSERTION',e))),
        'epistemic-observation':op('AND',op('IS_OBSERVATION',e),op('NOT',op('IS_ASSERTION',e))),
        'source-attribution':op('AND',op('ASSERTED_BY',s,p),op('NOT',op('FORMAL_ENTAILS',p))),
        'formal-entailment':op('AND',op('FORMAL_ENTAILS',p),op('NOT',op('ASSERTED_BY',s,p))),
        'provenance-ancestry':op('AND',op('DERIVED_FROM',e,h),op('NOT',op('DEPENDENCY',e,h))),
        'inferential-dependency':op('AND',op('DEPENDENCY',e,h),op('NOT',op('DERIVED_FROM',e,h))),
        'historical-supersession':op('AND',op('SUPERSEDES',e,h),op('NOT',op('DERIVED_FROM',e,h))),
        'evidence-revision':op('AND',op('SUPERSEDES',e,h),op('REVISES',e,h)),
        'current-evidence':op('AND',op('CURRENT_STATE',p),op('NOT',op('HISTORICAL_STATE',p))),
        'historical-evidence':op('AND',op('HISTORICAL_STATE',p),op('NOT',op('CURRENT_STATE',p))),
    }
    return contrasts[family]


def row(r,stage,family,trace=None):
    answer=evaluate(r)
    if answer!=independent_evaluate(r):raise ValueError('finite independent oracles disagree')
    ids=encode(r)
    if len(ids)>96:raise ValueError('world exceeds preserved context')
    if decode(ids)!=r:raise ValueError('symbolic codec failed roundtrip')
    return {'id':digest(r),'input':r,'gold':answer,'stage':stage,'family':family,
            'source_locator':SOURCES['85' if stage==5 else '84'],'helper_traces':[] if trace is None else [trace]}


def lesson(stage,family,rng,category='focus',varied=False,trace=None):
    w=make_world(stage,rng,varied);q=assisted_query(family,w,rng) if category=='helper' else query(family,w,rng)
    a,b,c= [const('Entity',rng.choice(w['base']['entities'])) for _ in range(3)]
    old=inherited(prior.relation('PARENT',prior.entity(a['name']),prior.entity(b['name'])))
    if category=='composition':
        q=op(rng.choice(('AND','OR')),q,old if rng.random()<.5 else op('MEMBER',a,op('DOMAIN',const('Function','F0'))))
    if category=='held_composite':
        witness=inherited(prior.quantify('EXISTS',prior.logic('AND',
                prior.relation('PARENT',prior.entity(a['name']),prior.bound(0)),
                prior.relation('PARENT',prior.bound(0),prior.entity(c['name'])))))
        q=op('AND',op('OR',q,witness),op('NOT',op('MEMBER',a,const('Set','K0'))))
    return row(record(w,q),stage,('helper:' if category=='helper' else '')+family,trace)


def perturb(r):
    original=r['input'];w=original['world'];changes=[]
    for set_id in ('K0','K1'):
        for entity in w['base']['entities']:
            new=copy.deepcopy(w);values=set(new['sets'][set_id]);values.symmetric_difference_update([entity]);new['sets'][set_id]=sorted(values)
            changes.append((new,'one set membership'))
    for field in ('edges','links'):
        for i in range(len(w[field])):
            new=copy.deepcopy(w);new[field].pop(i);changes.append((new,'one '+field+' edge removed'))
    for field in ('facts','rules'):
        for i in range(len(w['base'][field])):
            new=copy.deepcopy(w);new['base'][field].pop(i);changes.append((new,'one inherited '+field+' declaration removed'))
    for prop in w['base']['propositions']:
        new=copy.deepcopy(w);del new['base']['propositions'][prop];changes.append((new,'one proposition declaration removed'))
    for name in ('F0','F1'):
        for i in range(len(w['functions'][name])):
            new=copy.deepcopy(w);new['functions'][name].pop(i);changes.append((new,'one function mapping removed'))
    for i,event in enumerate(w['events']):
        for index,new_value,label in ((4,'refute' if event[4]=='support' else 'support','one evidence polarity'),
                                      (1,'OBSERVE' if event[1]=='ASSERT' else 'ASSERT','one event type'),
                                      (2,'S1' if event[2]=='S0' else 'S0','one source attribution')):
            new=copy.deepcopy(w);new['events'][i][index]=new_value;new['events'].sort();changes.append((new,label))
    for i,link in enumerate(w['links']):
        if link[0] in ('DERIVED_FROM','SUPERSEDES'):
            new=copy.deepcopy(w);new['links'][i][0]='SUPERSEDES' if link[0]=='DERIVED_FROM' else 'DERIVED_FROM';new['links'].sort()
            changes.append((new,'DERIVED_FROM versus SUPERSEDES'))
    for new,label in changes:
        try:changed=row(record(new,original['query']),r['stage'],r['family'])
        except ValueError:continue
        if changed['gold']!=r['gold']:return changed,label
    return None


def _pool(stage,families,seed,category,varied=False,trace=None,excluded=()):
    rng=random.Random(seed);rows={};exclude=set(excluded)
    for family in families:
        count=0;attempts=0;target=32 if varied else 128;labels=Counter()
        balanced=category in ('focus','helper','held_composite')
        expected=(('UNKNOWN','TRUE','FALSE','CONFLICT') if family in ('current-evidence','historical-evidence') and category!='helper'
                  else ('UNKNOWN','FALSE','CONFLICT') if family in ('current-evidence','historical-evidence') else ('FALSE','TRUE'))
        quotas={s:target//len(expected)+(i<target%len(expected)) for i,s in enumerate(expected)}
        while count<target and attempts<target*160:
            attempts+=1
            try:r=lesson(stage,family,rng,category,varied,trace)
            except ValueError:continue
            if balanced and (r['gold'] not in quotas or labels[r['gold']]>=quotas[r['gold']]):continue
            if r['id'] not in rows and r['id'] not in exclude:rows[r['id']]=r;count+=1;labels[r['gold']]+=1
        if count<target:raise ValueError('insufficient distinct tiny worlds: '+family)
    return list(rows.values())


def build_data(prior_data,helpers):
    data=copy.deepcopy(prior_data);data['version']='development-lessons-0.1.0'
    for stage in (5,6):
        s=str(stage);families=FAMILIES[s]
        focus=_pool(stage,families,31000+stage,'focus')
        composition=_pool(stage,families,32000+stage,'composition')
        helper=[]
        for d in helpers['decisions']:
            v=d['validator']
            if v['disposition']=='accepted' and v['lesson_family'] in families:
                helper+=_pool(stage,[v['lesson_family']],33000+stage*100+int(d['decision_id'][1:]),'helper',trace=d['decision_id'])
        pairs=[];contrasts={}
        for family in families:
            count=0
            for r in focus+composition+helper:
                if r['family'].removeprefix('helper:')!=family:continue
                result=perturb(r)
                if result:
                    changed,factor=result;contrasts[r['id']]=r;contrasts[changed['id']]=changed
                    pairs.append({'before':r['id'],'after':changed['id'],'factor':factor});count+=1
                if count>=12:break
            if count<12:raise ValueError('insufficient single-factor contrasts: '+family)
        data['stages'][s]={'name':'relational mathematics' if stage==5 else 'epistemic interoperation',
                            'train':{'focus':focus,'composition':composition,'contrast':list(contrasts.values()),'helper':helper},'eval':{}}
        data['contrast_pairs'][s]=pairs
    all_train={r['id'] for s in data['stages'].values() for pool in s['train'].values() for r in pool}
    for stage in (5,6):
        s=data['stages'][str(stage)];s['eval']['familiar']=s['train']['focus'][::10][:128]
        for split,category in (('varied','focus'),('composite','held_composite')):
            s['eval'][split]=_pool(stage,FAMILIES[str(stage)],41000+stage*100+(split=='composite'),category,True,excluded=all_train)
    data['policy']='Exploratory frozen probes; old probes unchanged; new varied/composite exact inputs excluded from every training pool; 4-5 entities versus 2-4 in train.'
    return data


def audit(data,helpers):
    if set(data['stages'])!={str(i) for i in range(7)}:raise ValueError('seven-stage cumulative data')
    accepted={d['decision_id']:d for d in helpers['decisions'] if d['validator']['disposition']=='accepted'}
    all_train={r['id'] for s in data['stages'].values() for pool in s['train'].values() for r in pool}
    maximum=0;counts={};traces=Counter();numeric={}
    for stage,s in data['stages'].items():
        counts[stage]={}
        for category in ('train','eval'):
            for name,rows in s[category].items():
                if not rows or len({r['id'] for r in rows})!=len(rows):raise ValueError('empty or repeated lesson pool')
                for r in rows:
                    ids=encode(r['input']);maximum=max(maximum,len(ids))
                    if r['id']!=digest(r['input']) or r['gold']!=evaluate(r['input']) or r['gold']!=independent_evaluate(r['input']) or decode(ids)!=r['input']:
                        raise ValueError('lesson meaning/identity/codec binding')
                    key=tuple(ids)
                    if key in numeric and numeric[key]!=r['id']:raise ValueError('numeric input collision')
                    numeric[key]=r['id']
                    if category=='eval' and name!='familiar' and r['id'] in all_train:raise ValueError('probe appears in training')
                    for trace in r.get('helper_traces',[]):
                        if trace not in accepted or r['family']!='helper:'+accepted[trace]['validator']['lesson_family']:
                            raise ValueError('unadmitted helper lesson')
                        if category=='train' and name=='helper':traces[trace]+=1
                counts[stage][category+':'+name]={'n':len(rows),'labels':dict(Counter(r['gold'] for r in rows)),'sha256':digest(rows)}
        by_id={r['id']:r for pool in s['train'].values() for r in pool}
        for pair in data['contrast_pairs'][stage]:
            if by_id[pair['before']]['gold']==by_id[pair['after']]['gold']:raise ValueError('contrast does not alter gold')
    if maximum>96 or set(traces)!=set(accepted):raise ValueError('context or admitted material coverage')
    return {'data_sha256':digest(data),'max_tokens':maximum,'stages':counts,'helper_lessons_by_decision':dict(traces),
            'old_eval_sha256':digest({s:data['stages'][s]['eval'] for s in map(str,range(5))}),
            'oracle_agreement':True,'codec_roundtrip':True,'numeric_collisions':0,'natural_language_in_neural_inputs':False}
