"""Deterministic #70-style transitions over the sourced alpha COGAL slice.

Scorers propose offered actions. Validation owns transition admissibility; oracle
targets are a separate API and never enter state/candidate neural encodings.
"""
import copy
import random
from .codec import encode as alpha_encode
from .decision_features import control, token_manifest
from .semantics import ABI, BITS, LABELS, SemanticError, atom, canonical, digest, evaluate, normalize, sid

VERSION = 'decision-navigation-0.1.0'
RESERVED = ('other', 'insufficient', 'clarify', 'abstain')


def _tasks(query):
    tasks = []
    def visit(q, key, bindings):
        op = q['op']
        if op in (sid('exists'), sid('forall')):
            children = []
            for entity in ('a','b'):
                binding = key + '/bind-' + entity
                tasks.append({'kind':'bind','key':binding,'query':q,'entity':sid(entity),'bindings':bindings})
                children.append(visit(q['body'],key+'/'+entity,bindings+[binding]))
            tasks.append({'kind':'fold','key':key,'query':q,'children':children,'bindings':bindings})
        elif op in (sid('and'), sid('or'), sid('not')):
            children = [visit(a,key+'/'+str(i),bindings) for i,a in enumerate(q['args'])]
            tasks.append({'kind':'fold','key':key,'query':q,'children':children,'bindings':bindings})
        else:
            if op == sid('relation'):
                tasks.append({'kind':'orient','key':key,'query':q,'bindings':bindings})
            tasks.append({'kind':'read','key':key,'query':q,'bindings':bindings})
        return key
    visit(query,'root',[])
    return tasks


def initial(episode):
    e = copy.deepcopy(episode)
    if e['version'] != 'decision-episodes-0.1.0' or e['mode'] not in ('active','ambiguous','missing','unsupported','outside'):
        raise ValueError('EPISODE_CONTRACT')
    if e['mode'] != 'unsupported': e['semantic'] = normalize(e['semantic'])
    else:
        # Unsupported query capability never relaxes the ABI/world boundary.
        world=normalize({'abi':e['semantic']['abi'],'world':e['semantic']['world'],'query':atom('a','b')})['world']
        try: normalize(e['semantic'])
        except SemanticError as error:
            if error.code!='UNSUPPORTED_CONSTRUCT': raise
        else: raise ValueError('SUPPORTED_QUERY_MISCLASSIFIED')
        e['semantic']['world']=world
    tasks = [] if e['mode'] in ('ambiguous','missing','unsupported') else _tasks(e['semantic']['query'])
    if e.get('update'):
        tasks.insert(0,{'kind':e['update']['kind'],'key':'world-update','query':e['semantic']['query'],'bindings':[]})
    return {'version':VERSION,'episode':e,'episode_sha256':digest(e),'world':copy.deepcopy(e['semantic']['world']),
            'tasks':tasks,'cursor':0,'bindings':{},'interpretations':{},'values':{},
            'status':'active','outcome':None,'history':[]}


def _ground(state, task):
    env = {sid('x'):state['bindings'][k] for k in task.get('bindings',[]) if k in state['bindings']}
    def visit(q):
        if q['op'] in (sid('relation'),sid('equal')):
            args = [({'kind':'constant','id':env[t['id']]} if t['kind']=='variable' and t['id'] in env else t) for t in q['args']]
            return {'op':q['op'],'args':args}
        if 'body' in q: return copy.deepcopy(q)
        return {'op':q['op'],'args':[visit(a) for a in q['args']]}
    return visit(task['query'])


def focus(state):
    if not state['tasks']: return {'kind':'read','key':'reserved','query':state['episode']['semantic']['query'],'bindings':[]}
    return state['tasks'][state['cursor']]


def _candidate(kind, delta):
    return {'candidate_id':digest({'version':VERSION,'kind':kind,'delta':delta}),
            'effect_class':kind,'semantic_delta':delta,
            'description':kind+' '+canonical(delta).decode(),
            'prerequisites':'current typed focus and unchanged panel binding',
            'provenance':['Bilqis #7/#80 alpha COGAL','Bilqis #70 transition discipline']}


def _panel(state, seed=None):
    if state['status'] != 'active': raise ValueError('TERMINAL_STATE')
    task = focus(state); kind = task['kind']; candidates = []
    mode = state['episode']['mode']
    if mode not in ('ambiguous','missing','unsupported'):
        if kind == 'orient':
            q = _ground(state,task)
            for args in (q['args'],list(reversed(q['args']))):
                c = _candidate(kind,{'key':task['key'],'query':{'op':q['op'],'args':args}})
                if c not in candidates: candidates.append(c)
        elif kind == 'bind':
            candidates = [_candidate(kind,{'key':task['key'],'entity':sid(e)}) for e in ('a','b')]
        elif kind in ('read','fold'):
            candidates = [_candidate(kind,{'key':task['key'],'value':label}) for label in LABELS]
        elif kind in ('add','remove'):
            desired = state['episode']['update']['fact']
            if kind == 'remove': facts = state['world']['facts']
            else:
                reverse = copy.deepcopy(desired); reverse['roles'] = dict(zip(('source','target'), reversed(list(desired['roles'].values()))))
                opposite = copy.deepcopy(desired); opposite['polarity'] = sid('refute' if desired['polarity']==sid('support') else 'support')
                opposite['source'] = sid('source-1' if opposite['polarity']==sid('refute') else 'source-0')
                facts = [f for f in (desired,reverse,opposite) if f not in state['world']['facts']]
            for f in facts:
                c = _candidate(kind,{'fact':f})
                if c not in candidates: candidates.append(c)
        if mode == 'outside' and state['cursor']==0:
            wanted = _desired(state)
            candidates = [c for c in candidates if c != wanted]
    candidates += [_candidate(r,{}) for r in RESERVED]
    result = {'state_sha256':digest(state),'revision':len(state['history']),
              'candidates':candidates,'focus_kind':kind}
    result['panel_id'] = digest({'state':result['state_sha256'],'candidates':sorted(c['candidate_id'] for c in candidates)})
    if seed is not None: random.Random(seed).shuffle(result['candidates'])
    return result


def _advance(state, c, panel_id):
    result = copy.deepcopy(state)
    kind = c['effect_class']; delta = c['semantic_delta']
    if kind in RESERVED:
        result['status'] = {'other':'outside','insufficient':'missing','clarify':'ambiguous','abstain':'unsupported' if state['episode']['mode']=='unsupported' else 'abstained'}[kind]
    elif kind == 'orient': result['interpretations'][delta['key']] = delta['query']
    elif kind == 'bind': result['bindings'][delta['key']] = delta['entity']
    elif kind in ('read','fold'): result['values'][delta['key']] = delta['value']
    elif kind in ('add','remove'):
        facts = result['world']['facts']
        if kind == 'add': facts.append(copy.deepcopy(delta['fact']))
        else: facts.remove(delta['fact'])
        result['world'] = normalize({'abi':ABI,'world':result['world'],'query':atom('a','b')})['world']
    result['history'].append({'panel_id':panel_id,'candidate_id':c['candidate_id'],'effect_class':kind,'semantic_delta':delta})
    result['cursor'] += 1
    if result['status']=='active' and result['cursor']==len(result['tasks']):
        result['status']='resolved'; result['outcome']=result['values']['root']
    return result


def _validate(state):
    if state['version']!=VERSION or digest(state['episode'])!=state['episode_sha256']:
        raise ValueError('STATE_BINDING')
    reconstructed = initial(state['episode'])
    for h in state['history']:
        p = _panel(reconstructed)
        c = next((c for c in p['candidates'] if c['candidate_id']==h['candidate_id']),None)
        if not c or h != {'panel_id':p['panel_id'],'candidate_id':c['candidate_id'],'effect_class':c['effect_class'],'semantic_delta':c['semantic_delta']}:
            raise ValueError('TAMPERED_HISTORY')
        reconstructed = _advance(reconstructed,c,p['panel_id'])
    if reconstructed != state: raise ValueError('TAMPERED_STATE')


def panel(state, seed=None):
    _validate(state)
    return _panel(state,seed)


def apply(state, offered, candidate_id):
    expected = panel(state)
    _check_panel(offered,expected)
    chosen = next((c for c in expected['candidates'] if c['candidate_id']==candidate_id),None)
    if chosen is None: raise ValueError('UNOFFERED_TRANSITION')
    return _advance(state,chosen,expected['panel_id'])


def _check_panel(offered, expected):
    if any(offered.get(k)!=expected[k] for k in ('state_sha256','revision','panel_id','focus_kind')):
        raise ValueError('STALE_PANEL')
    if sorted(offered.get('candidates',[]),key=lambda c:c['candidate_id']) != sorted(expected['candidates'],key=lambda c:c['candidate_id']):
        raise ValueError('TAMPERED_PANEL')


def _desired(state):
    task = focus(state); kind = task['kind']; key = task['key']
    if kind=='orient': return _candidate(kind,{'key':key,'query':_ground(state,task)})
    if kind=='bind': return _candidate(kind,{'key':key,'entity':task['entity']})
    if kind in ('add','remove'): return _candidate(kind,{'fact':state['episode']['update']['fact']})
    if kind=='read':
        q = state['interpretations'].get(key,_ground(state,task))
        value = evaluate({'abi':ABI,'world':state['world'],'query':q})
    elif kind=='fold':
        bits = [BITS[LABELS.index(state['values'][k])] for k in task['children']]
        op = task['query']['op']
        if op==sid('not'): result = tuple(reversed(bits[0]))
        elif op in (sid('and'),sid('forall')): result = (bits[0][0]&bits[1][0],bits[0][1]|bits[1][1])
        else: result = (bits[0][0]|bits[1][0],bits[0][1]&bits[1][1])
        value = LABELS[BITS.index(result)]
    else: raise ValueError('UNKNOWN_TRANSITION')
    return _candidate(kind,{'key':key,'value':value})


def target(state, offered=None):
    """Independent formal target; caller must keep it out of scorer inputs."""
    mode = state['episode']['mode']
    reserved = {'ambiguous':'clarify','missing':'insufficient','unsupported':'abstain'}.get(mode)
    p = panel(state)
    if offered is not None: _check_panel(offered,p)
    desired = _candidate(reserved,{}) if reserved else _desired(state)
    if desired not in p['candidates']: desired = _candidate('other',{})
    return desired['candidate_id']


def oracle_trace(episode):
    state = initial(episode); rows = []
    while state['status']=='active':
        p = panel(state); chosen = target(state,p)
        rows.append({'state':state,'panel':p,'gold_id':chosen})
        state = apply(state,p,chosen)
    return rows,state


def _query_tokens(world, q):
    return alpha_encode({'abi':ABI,'world':world,'query':q})


def state_tokens(state):
    """Only semantic state and current goal; no fixture/split/target IDs."""
    ids = token_manifest()['tokens']; task = focus(state)
    mode = state['episode']['mode']
    tokens = [control('state'),control(mode),control(task['kind'])]
    out = [ids.index(t) for t in tokens]
    if mode=='unsupported': return out
    out += _query_tokens(state['world'],state['episode']['semantic']['query'])
    if task['kind'] in ('orient','read'):
        out += _query_tokens(state['world'],state['interpretations'].get(task['key'],_ground(state,task)))
    elif task['kind']=='bind': out += [ids.index(sid('role-binder')),ids.index(task['entity'])]
    elif task['kind']=='fold':
        out += [ids.index(task['query']['op']),ids.index(control('operands'))]
        out += [ids.index(sid(state['values'][k].lower())) for k in task['children']]
    elif task['kind'] in ('add','remove'): out += _fact_tokens(state['episode']['update']['fact'])
    return out


def _fact_tokens(f):
    ids = token_manifest()['tokens']
    return [ids.index(t) for t in (sid('fact'),f['predicate'],sid('role-source'),f['roles']['source'],
            sid('role-target'),f['roles']['target'],f['polarity'],f['source'])]


def candidate_tokens(c):
    ids = token_manifest()['tokens']; kind = c['effect_class']; d = c['semantic_delta']
    out = [ids.index(control('candidate')),ids.index(control(kind))]
    if kind=='orient':
        out += _query_tokens({'entities':[sid('a'),sid('b')],'sources':[sid('source-0'),sid('source-1')],'facts':[]},d['query'])
    elif kind=='bind': out += [ids.index(sid('role-binder')),ids.index(d['entity'])]
    elif kind in ('read','fold'): out += [ids.index(sid(d['value'].lower()))]
    elif kind in ('add','remove'): out += _fact_tokens(d['fact'])
    return out


def render(state):
    task = focus(state)
    # Keep executable source and human-readable rendering separate. This surface
    # includes learner-produced operands, never the independent target function.
    return {'canonical_world':state['world'],'query':state['episode']['semantic']['query'],
            'availability':state['episode']['mode'],'current_goal':task,
            'selected_relations':state['interpretations'],'bindings':state['bindings'],
            'observed_operands':state['values'],'explanation_provenance':'deterministic canonical rendering'}
