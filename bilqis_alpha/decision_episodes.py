"""Frozen epoch-specific trajectory identities and exactly matched batch multisets."""
import copy
import random
from .decision_navigation import candidate_tokens, oracle_trace, state_tokens
from .decision_navigation import VERSION as NAVIGATION_VERSION
from .semantics import ABI, atom, combine, digest, negate, normalize, quantify, sid, variable, world_from_states

VERSION = 'decision-episodes-0.1.0'
SEED = 202
DATASET_SHA256 = '4f56c4285a10d1166ed443c32f2a49bfe46b488274404ab8256103a450b2cd0b'
BATCHES_SHA256 = '015239fc785b27aaaf9e5f8c1ba81f0237183bb34c9b96bc6acf1225e838a9ea'


def pattern(episode):
    def visit(q):
        name=q['op'].rsplit(':',1)[-1].upper()
        if 'body' in q: return name+'('+visit(q['body'])+')'
        if name in ('RELATION','EQUAL'): return name
        return name+'('+','.join(sorted(visit(a) for a in q['args']))+')'
    return episode['mode']+'/'+(episode['update']['kind']+'/' if episode.get('update') else '')+visit(episode['semantic']['query'])


def _query(index):
    r=atom('a','b'); reverse=atom('b','a'); bound=atom('a',variable())
    return [r,reverse,r,atom('a','b','equal'),r,r,negate(r),combine('and',r,reverse),
            combine('or',r,reverse),quantify('exists',bound),quantify('forall',bound),
            negate(quantify('exists',bound)),quantify('exists',negate(bound)),
            combine('and',negate(r),reverse),combine('or',quantify('exists',bound),reverse),r][index]


def _held_query(family):
    r=atom('a','b'); reverse=atom('b','a'); bound=atom('a',variable()); inverse=atom(variable(),'a')
    return [combine('or',negate(reverse),combine('and',r,reverse)),
            negate(quantify('forall',combine('or',bound,inverse))),
            quantify('forall',combine('and',bound,inverse)),
            negate(combine('and',r,reverse)),
            combine('and',combine('or',r,reverse),negate(reverse))][family]


def _make(query, states, family, split, *, mode='active', update=None):
    semantic={'abi':ABI,'world':world_from_states(states),'query':query}
    if mode!='unsupported': semantic=normalize(semantic)
    e={'version':VERSION,'split':split,'family':family,'mode':mode,'semantic':semantic,'update':update,
       'provenance':['Bilqis #7/#80 alpha slice','#70 candidate transition contract'],
       'historically_exposed_domain':True}
    e['pattern']=pattern(e)
    e['episode_id']='DN02-'+digest(e)[:24]
    return e


def build(seed=SEED):
    if seed!=SEED: raise ValueError('NEW_SEED_REQUIRES_NEW_EPOCH')
    rng=random.Random(seed); episodes=[]; rows=[]; blocks=[]
    prerequisites=[[],[],[],[],[0,2],[0,2],[0,2],[2],[2],[0,2],[0,2],[6,9],[6,9],[6,7],[8,9],[0,2]]
    families=['orientation','orientation','evidence','orientation','evidence','evidence','scope','consequence',
              'consequence','binding','binding','scope','binding','consequence','consequence','reserved']
    seen=set()
    def add(index,split,number,held=False):
        states=[rng.randrange(4) for _ in range(4)]
        q=_held_query(index) if held else _query(index)
        family=('orientation','scope','binding','evidence','consequence')[index] if held else families[index]
        mode='active'; update=None
        if index==15 and not held:
            mode=('ambiguous','missing','unsupported','outside')[number%4]
            if mode=='unsupported': q={'op':sid('implication'),'args':[atom('a','b'),atom('b','a')]}
            if split=='HELDOUT':
                q=_held_query(number%5)
                if mode=='unsupported': q={'op':sid('implication'),'args':[q,negate(atom('a','b'))]}
        if (not held and index in (4,5)) or (held and index==3):
            kind='remove' if index==5 else 'add'
            states[1]=3 if kind=='remove' else 0
            fact={'predicate':sid('relation'),'roles':{'source':sid('a'),'target':sid('b')},
                  'polarity':sid('refute'),'source':sid('source-1')}
            update={'kind':kind,'fact':fact}
        e=_make(q,states,family,split,mode=mode,update=update)
        content=digest({'semantic':e['semantic'],'mode':mode,'update':update})
        if content in seen: return add(index,split,number,held)
        seen.add(content); episodes.append(e)
        return e
    for index in range(16):
        indices=[]
        for number in range(8):
            e=add(index,'TRAIN',number)
            trace,_=oracle_trace(e)
            for step,row in enumerate(trace):
                candidates=row['panel']['candidates']
                tokens=state_tokens(row['state'])
                if len(tokens)>384: raise ValueError('STATE_CONTEXT_OVERFLOW')
                indices.append(len(rows))
                rows.append({'row_id':digest({'navigation_version':NAVIGATION_VERSION,'state':row['state'],
                                              'panel':row['panel'],'gold_id':row['gold_id']}),
                    'episode_id':e['episode_id'],'step':step,'state_tokens':tokens,
                    'candidate_tokens':[candidate_tokens(c) for c in candidates],
                    'candidate_ids':[c['candidate_id'] for c in candidates], 'gold_id':row['gold_id'],
                    'kind':row['panel']['focus_kind']})
        batches=[[rng.choice(indices) for _ in range(32)] for _ in range(96)]
        blocks.append({'block_id':f'B{index:02d}','family':families[index],
                       'prerequisites':prerequisites[index],'row_indices':indices,'batches':batches,
                       'steps':96,'examples':3072})
    for i in range(15):
        for n in range(2): add(i,'DEV',n)
    for i in range(5):
        for n in range(6): add(i,'HELDOUT',n,held=True)
    for n in range(4): add(15,'DEV',n)
    for n in range(4): add(15,'HELDOUT',n)
    train_patterns=sorted({e['pattern'] for e in episodes if e['split']=='TRAIN'})
    held_patterns=sorted({e['pattern'] for e in episodes if e['split']=='HELDOUT'})
    if set(train_patterns)&set(held_patterns): raise ValueError('PATTERN_LEAKAGE')
    result={'version':VERSION,'seed':seed,'episodes':episodes,'rows':rows,'blocks':blocks,
            'train_patterns':train_patterns,'heldout_patterns':held_patterns,
            'historically_exposed_domain':True,'sealed':False,
            'optimization_policy':'frozen oracle transition rows, same 16x96x32 batches; only block order may differ',
            'heldout_policy':'no heldout oracle labels/results in curriculum context; final scoring after both checkpoints'}
    if digest(result)!=DATASET_SHA256: raise ValueError('EPOCH_DATASET_DRIFT')
    if digest([{'block_id':b['block_id'],'batches':b['batches']} for b in blocks])!=BATCHES_SHA256:
        raise ValueError('EPOCH_BATCH_DRIFT')
    return result
