"""#70 deterministic finite candidate panels. Scorers never define continuations."""
import copy
import random
from .semantics import digest
from .navigation_fixture import VERSION, resolve_object, context

RESERVED=('other','insufficient','clarify','abstain')
STATES={'active','resolved','ambiguous','absent','unsupported','insufficient','abstained'}


def initial(corpus,case):
    if corpus['version']!=VERSION:raise ValueError('FIXTURE_VERSION')
    for ids in case['scopes'].values():
        for identity in ids:resolve_object(corpus,identity)
    for identity in case['resolved_refs']:resolve_object(corpus,identity)
    return {'fixture_id':case['id'],'fixture_version':corpus['version'],'corpus_sha256':digest(corpus),
            'revision':0,'scope':'root','constraints':{},'hints':copy.deepcopy(case['hints']),
            'evidence_index':0,'resolved_refs':case['resolved_refs'].copy(),'status':'active','object_id':None,
            'unsupported_distinctions':[],'history':[]}


def _validate(corpus,case,state):
    if (state['fixture_id']!=case['id'] or state['fixture_version']!=corpus['version']
        or state['corpus_sha256']!=digest(corpus) or state['scope'] not in case['scopes']
        or state['status'] not in STATES):raise ValueError('STATE_FIXTURE_IDENTITY')
    if type(state['revision']) is not int or state['revision']!=len(state['history']):raise ValueError('STATE_REVISION')
    index=state['evidence_index']
    if type(index) is not int or not 0<=index<=len(case['evidence_schedule']):raise ValueError('STATE_EVIDENCE_INDEX')
    hints=copy.deepcopy(case['hints'])
    for update in case['evidence_schedule'][:index]:hints.update(update)
    if hints!=state['hints'] or state['resolved_refs']!=case['resolved_refs']:raise ValueError('STATE_EVIDENCE_BINDING')
    for factor,value in state['constraints'].items():
        if factor not in case['factor_path'] or factor not in case['capabilities']:raise ValueError('ILLEGAL_FACTOR')
        if not any(corpus['objects'][i].get(factor)==value for ids in case['scopes'].values() for i in ids):raise ValueError('ILLEGAL_FACTOR_VALUE')


def live(corpus,case,state):
    _validate(corpus,case,state)
    return sorted(i for i in case['scopes'][state['scope']]
                  if all(corpus['objects'][i].get(k)==v for k,v in state['constraints'].items()))


def panel(corpus,case,state,seed=None):
    ids=live(corpus,case,state)
    if state['status']!='active':raise ValueError('TERMINAL_STATE')
    remaining=[x for x in case['factor_path'] if x not in state['constraints']]
    factor=remaining[0] if remaining else None
    candidates=[]
    def add(effect,delta,description):
        identity=digest({'version':corpus['version'],'fixture':case['id'],'effect':effect,'delta':delta})
        candidates.append({'candidate_id':identity,'semantic_delta':delta,'effect_class':effect,
                           'description':description,'prerequisites':{'scope':state['scope'],'capabilities':case['capabilities']},
                           'provenance':case['provenance']})
    # Unknown evidence retains its alternatives. It cannot be guessed into a constraint.
    if factor in case['capabilities'] and factor in state['hints']:
        values=sorted({corpus['objects'][i][factor] for i in ids if factor in corpus['objects'][i]})
        for value in values:add('constrain',{'factor':factor,'value':value},f'Interpret {factor} as {value}.')
    compatible=all(state['hints'].get(k)==v for k,v in state['constraints'].items())
    if factor is None and len(ids)==1 and compatible:
        add('resolve',{'object_id':ids[0]},'Resolve the single supported canonical object.')
    for reserved in RESERVED:add(reserved,{}, {'other':'The target is outside this candidate neighborhood; seek a deeper scope.',
        'insufficient':'Current evidence or capabilities cannot support resolution.',
        'clarify':'Request the next bounded distinction, or retain unresolved alternatives.',
        'abstain':'Stop without asserting a canonical target.'}[reserved])
    identity=digest({'state':state,'candidate_ids':sorted(x['candidate_id'] for x in candidates)})
    if seed is not None:random.Random(seed).shuffle(candidates)
    return {'panel_id':identity,'revision':state['revision'],'fixture_id':case['id'],'factor':factor,
            'live_ids':ids,'candidates':candidates,'unsupported_distinctions':[factor] if factor and factor not in case['capabilities'] else []}


def apply(corpus,case,state,offered,candidate_id):
    expected=panel(corpus,case,state)
    if any(offered.get(k)!=expected[k] for k in ('panel_id','revision','fixture_id','factor','live_ids','unsupported_distinctions')):
        raise ValueError('STALE_OR_MISMATCHED_PANEL')
    if sorted(offered.get('candidates',[]),key=lambda x:x['candidate_id'])!=sorted(expected['candidates'],key=lambda x:x['candidate_id']):
        raise ValueError('TAMPERED_PANEL')
    candidate=next((x for x in expected['candidates'] if x['candidate_id']==candidate_id),None)
    if candidate is None:raise ValueError('ILLEGAL_TRANSITION')
    result=copy.deepcopy(state);effect=candidate['effect_class'];delta=candidate['semantic_delta'];factor=expected['factor']
    if effect=='constrain':result['constraints'][delta['factor']]=delta['value']
    elif effect=='resolve':result.update(status='resolved',object_id=delta['object_id'])
    elif effect=='other':
        if state['scope']=='root' and set(case['scopes']['deeper'])!=set(case['scopes']['root']):result['scope']='deeper'
        else:result['status']='absent' if factor and state['hints'].get(factor) not in {corpus['objects'][i].get(factor) for i in expected['live_ids']} else 'insufficient'
    elif factor and factor not in case['capabilities']:
        result['status']='unsupported';result['unsupported_distinctions']=[factor]
    elif effect=='clarify' and state['evidence_index']<len(case['evidence_schedule']):
        update=case['evidence_schedule'][state['evidence_index']]
        if any(k not in case['factor_path'] for k in update):raise ValueError('ILLEGAL_CLARIFICATION')
        result['hints'].update(update);result['evidence_index']+=1
    else:
        result['status']='ambiguous' if len(expected['live_ids'])>1 else 'absent' if not expected['live_ids'] else 'abstained' if effect=='abstain' else 'insufficient'
    result['history'].append({'panel_id':expected['panel_id'],'candidate_id':candidate_id,'effect_class':effect,
                              'semantic_delta':delta,'prior_live_ids':expected['live_ids']})
    result['revision']+=1
    _validate(corpus,case,result)
    return result


def reference_view(corpus,case,state):
    _validate(corpus,case,state)
    value=context(corpus,case,state['hints'])
    for identity in state['resolved_refs']:
        resolve_object(corpus,identity);value['objects'].pop(identity,None)
    return value


def expand_view(corpus,value):
    result=copy.deepcopy(value)
    for identity in value['resolved_refs']:
        resolve_object(corpus,identity);result['objects'][identity]=copy.deepcopy(corpus['objects'][identity])
    return result
