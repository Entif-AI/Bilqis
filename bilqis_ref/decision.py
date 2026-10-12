"""One bounded research harness for native MLX decisions and loopback comparators."""
from __future__ import annotations
import argparse
import copy
import hashlib
import json
import math
import random
import time
from pathlib import Path
from .semantics import canonical, digest
from .teacher import STAGE_NAMES, PREREQUISITES
from .local_http import local_json, encode_body

RESERVED = {'other','insufficient','clarify','abstain'}


def native_item(item):
    if item.get('split') != 'DEV': raise ValueError('DECISION_DEV_ONLY')
    row = {k:copy.deepcopy(item[k]) for k in ('id','state','question','options')}
    ids = [x['id'] for x in row['options']]
    if not 2 <= len(ids) <= 16 or len(ids) != len(set(ids)) or any(not x for x in ids):
        raise ValueError('DECISION_CANDIDATE_IDENTITY')
    if not row['id'] or not row['question']: raise ValueError('DECISION_ID_QUESTION')
    canonical(row)
    return row


def permute(item, seed):
    result = copy.deepcopy(item); random.Random(seed).shuffle(result['options']); return result


def normalize(item, engine, native, identity, latency_ms, warm_state):
    row = native_item(item); ids = [x['id'] for x in row['options']]
    if engine == 'semif':
        if native['option_ids'] != ids: raise ValueError('DECISION_OPTION_ORDER')
        probs = dict(zip(ids,native['probabilities']))
        if len(native['probabilities']) != len(ids): raise ValueError('DECISION_PROBABILITY_COUNT')
        selected = max(probs,key=probs.get)
    elif engine == 'kev':
        answer = native['answers']['decision']; probs = answer['probabilities']; selected = answer['choice']
    elif engine == 'generative':
        try:selected = json.loads(native['choices'][0]['message']['content'])['selected_id']
        except (ValueError,KeyError,TypeError):selected = None
        if selected not in ids:selected = None
        probs = None
    else: raise ValueError('DECISION_ENGINE')
    if selected not in ids and engine!='generative': raise ValueError('DECISION_SELECTED_ID')
    if probs is not None:
        if set(probs) != set(ids) or any(type(p) not in (int,float) or not math.isfinite(p) or not 0<=p<=1 for p in probs.values()):
            raise ValueError('DECISION_PROBABILITIES')
        # Kev's public API rounds each coordinate to four decimal places.
        tolerance = len(ids)*0.00005+1e-6 if engine=='kev' else 1e-5
        if abs(sum(probs.values())-1)>tolerance: raise ValueError('DECISION_PROBABILITY_SUM')
        if probs[selected]+1e-6<max(probs.values()): raise ValueError('DECISION_SELECTED_NOT_ARGMAX')
    if not math.isfinite(latency_ms) or latency_ms < 0: raise ValueError('DECISION_LATENCY')
    return {'fixture_id':row['id'],'engine':engine,**identity,'candidate_ids':ids,'probabilities':probs,
            'selected_id':selected,'latency_ms':latency_ms,'warm_state':warm_state,
            'prompt_or_state_hash':native.get('prompt_sha256',digest(row)),
            'state_sha256':digest(row['state']),'runtime_metadata':{'native':native},
            'probability_serialization':'upstream four-decimal scores retained' if engine=='kev' else 'native scores' if probs else 'unavailable',
            'validation_error':'GENERATION_INVALID_CHOICE' if selected is None else None,
            'authority':'proposal evidence only; never gold, student initialization or promotion'}


def route(result, policy):
    if result['selected_id'] is None or result['selected_id'] in RESERVED or result['probabilities'] is None: return 'review'
    values = sorted(result['probabilities'].values(),reverse=True)
    return 'local' if values[0]>=policy['local_probability'] and values[0]-values[1]>=policy['local_margin'] else 'review'


def curriculum_proposal(teacher, result):
    fallback = teacher.choose()
    selected = result.get('selected_id')
    stage = STAGE_NAMES.index(selected) if selected in STAGE_NAMES else None
    eligible = [i for i in range(5) if i not in teacher.promoted and all(p in teacher.promoted for p in PREREQUISITES[i])]
    accepted = result.get('route')=='local' and stage in eligible
    return {'stage':stage if accepted else fallback,'disposition':'bounded_proposal' if accepted else 'deterministic_fallback',
            'eligible_stages':eligible,'promotion_authority':False}


def metrics(items, results, policy):
    by_id = {x['fixture_id']:x for x in results}
    if len(by_id)!=len(results) or set(by_id)!={x['id'] for x in items}: raise ValueError('DECISION_RESULT_COVERAGE')
    labeled = [(x,by_id[x['id']]) for x in items if x.get('label') is not None]
    n = len(labeled); correct = sum(x['label']==r['selected_id'] for x,r in labeled)
    probabilistic = [(x,r) for x,r in labeled if r['probabilities'] is not None]
    confident_wrong = sum(r['selected_id']!=x['label'] and max(r['probabilities'].values())>=policy['confident_wrong_probability']
                          for x,r in probabilistic)
    brier = (sum(sum((p-int(k==x['label']))**2 for k,p in r['probabilities'].items()) for x,r in probabilistic)/len(probabilistic)
             if probabilistic else None)
    ece = None
    if len(probabilistic)>=policy['ece_min_labeled']:
        ece = 0.
        for bin_index in range(10):
            subset = [(x,r) for x,r in probabilistic if min(9,int(max(r['probabilities'].values())*10))==bin_index]
            if subset:
                confidence = sum(max(r['probabilities'].values()) for _,r in subset)/len(subset)
                accuracy = sum(x['label']==r['selected_id'] for x,r in subset)/len(subset)
                ece += len(subset)/len(probabilistic)*abs(confidence-accuracy)
    local = [r for r in results if route(r,policy)=='local']
    elapsed = sum(r['latency_ms'] for r in results)
    return {'items':len(items),'labeled':n,'correct':correct,'accuracy':correct/n if n else None,
            'brier':brier,'ece':ece,'ece_status':'measured' if ece is not None else 'insufficient_labeled_sample',
            'confident_wrong':confident_wrong,'local_proposals':len(local),'review':len(results)-len(local),
            'false_confident_local_completions':sum(r in local and r['selected_id']!=x['label'] for x,r in labeled),
            'decision_latency_total_ms':elapsed,'decisions_per_second':1000*len(results)/elapsed if elapsed else None,
            'resource_ms_per_local_proposal':elapsed/len(local) if local else None,
            'qualification_scope':'owned public diagnostic only; no general or SYS-01 quality claim'}


def kev_payload(item):
    row = native_item(item)
    # Preserve the established canonical layout outside the ordered Choice map.
    payload = json.loads(canonical({'model':'kev-latest','state':row['state'],'questions': {'decision':{
        'type':'choice','instructions':row['question'],'criteria':{o['id']:o['description'] for o in row['options']}}}}))
    payload['questions']['decision']['criteria'] = {o['id']:o['description'] for o in row['options']}
    return payload


def kev_score(item, endpoint, identity):
    payload = kev_payload(item)
    before = local_json(endpoint+'/v1/models','/v1/models')['models'][0]
    if before['backend']!='mlx' or before['run']!=identity['model']+'@'+identity['model_revision']:
        raise ValueError('KEV_RUNTIME_IDENTITY')
    start = time.perf_counter(); native = local_json(endpoint+'/v1/systemone','/v1/systemone',payload,preserve_order=True)
    elapsed = (time.perf_counter()-start)*1000
    after = local_json(endpoint+'/v1/models','/v1/models')['models'][0]
    result = normalize(item,'kev',native,identity,elapsed,after['prefix_cache']['hits']>before['prefix_cache']['hits'])
    result['runtime_metadata'].update(models=after,prefix_cache_before=before['prefix_cache'])
    result['request_payload_sha256'] = hashlib.sha256(encode_body(payload,True)).hexdigest()
    result['http_candidate_order'] = list(payload['questions']['decision']['criteria'])
    return result


def run(fixture, engine, identity, mode='direct', endpoint='http://127.0.0.1:8008', bits=None, cache_mib=256, record=None):
    items = fixture['items']; results=[]; loaded=None; started=time.perf_counter()
    def retain(result):
        result['route']=route(result,fixture['policy']);results.append(result)
        if record is not None:record(result)
    if engine=='semif' or (engine=='generative' and identity['backend']=='mlx'):
        from semif_phase1 import mlx_backend as backend
        import mlx.core as mx
        mark=time.perf_counter(); model,tokenizer,metadata=backend.load_model(identity['model'],identity['model_revision'],bits,cache_limit_mib=cache_mib)
        loaded=time.perf_counter()-mark
        identity={**identity,'runtime':metadata,'mode':mode}
        if engine=='generative':
            from mlx_lm import stream_generate
            from mlx_lm.sample_utils import make_sampler
            for item in items:
                row=native_item(item)
                messages=[{'role':'system','content':'Choose one listed option using the supplied evidence. Return only a JSON object with selected_id. Do not invent options.'},
                          {'role':'user','content':json.dumps(row,ensure_ascii=False)}]
                prompt=tokenizer.apply_chat_template(messages,tokenize=False,add_generation_prompt=True,enable_thinking=False)
                mark=time.perf_counter();text='';last=None
                for response in stream_generate(model,tokenizer,prompt,max_tokens=128,sampler=make_sampler(temp=0)):
                    text+=response.text;last=response
                value={'choices':[{'message':{'content':text}}],
                       'usage':{'prompt_tokens':last.prompt_tokens,'completion_tokens':last.generation_tokens} if last else None,
                       'prompt_sha256':digest(prompt),'decoding':{'temperature':0,'max_tokens':128,'enable_thinking':False}}
                retain(normalize(item,engine,value,{**identity,'mode':'generative'},(time.perf_counter()-mark)*1000,False))
        elif mode=='shared':
            groups={}
            for item in items: groups.setdefault(digest(item['state']),[]).append(item)
            for group in groups.values():
                native,timing=backend.score_shared(model,tokenizer,[native_item(x) for x in group],metadata)
                for item,value in zip(group,native):
                    result=normalize(item,engine,{**value,'shared_timing':timing},identity,timing['total_seconds']*1000/len(group),None)
                    result['latency_accounting']='amortized shared batch wall time'
                    retain(result)
        else:
            scorer=backend.SerialPrefixScorer(model,tokenizer,metadata) if mode=='serial' else None
            for item in items:
                row=native_item(item)
                value=scorer.score(row) if scorer else backend.score(model,tokenizer,row,metadata)
                retain(normalize(item,engine,value,identity,value['total_seconds']*1000,value.get('cache_hit',False)))
        memory={'active_bytes':mx.get_active_memory(),'peak_bytes':mx.get_peak_memory(),'cache_bytes':mx.get_cache_memory(),
                'scope':'MLX allocator; not total system unified memory'}
    elif engine=='kev':
        for item in items: retain(kev_score(item,endpoint,{**identity,'mode':mode}))
        memory=None
    elif engine=='generative':
        for item in items:
            row=native_item(item); payload={'model':identity['model'],'temperature':0,'max_tokens':128,
                'messages':[{'role':'system','content':'Choose one listed option using the supplied evidence. Return only a JSON object with selected_id. Do not invent options.'},
                            {'role':'user','content':json.dumps(row,ensure_ascii=False)}]}
            mark=time.perf_counter(); value=local_json(endpoint+'/v1/chat/completions','/v1/chat/completions',payload)
            retain(normalize(item,engine,value,{**identity,'mode':'generative'},(time.perf_counter()-mark)*1000,False))
        memory=None
    else: raise ValueError('DECISION_ENGINE')
    return results,{'fixture_sha256':digest(fixture),'engine':engine,'mode':mode,'model_load_seconds':loaded,
                    'wall_seconds':time.perf_counter()-started,'memory':memory,**metrics(items,results,fixture['policy'])}


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--fixture',type=Path,required=True);p.add_argument('--identity',type=Path,required=True)
    p.add_argument('--engine',choices=['kev','semif','generative'],required=True)
    p.add_argument('--mode',choices=['direct','serial','shared'],default='direct');p.add_argument('--bits',type=int,choices=[4,8])
    p.add_argument('--endpoint',default='http://127.0.0.1:8008');p.add_argument('--output',type=Path,required=True)
    p.add_argument('--permutation',type=int);p.add_argument('--cache-mib',type=int,default=256)
    a=p.parse_args()
    if a.output.exists():p.error('Output directory must be new; preserve interrupted evidence')
    fixture=json.loads(a.fixture.read_text());identity=json.loads(a.identity.read_text())
    if a.permutation is not None:fixture={**fixture,'items':[permute(x,a.permutation) for x in fixture['items']]}
    a.output.mkdir(parents=True)
    with (a.output/'rows.jsonl').open('x') as f:
        def record(row):f.write(json.dumps(row,allow_nan=False)+'\n');f.flush()
        results,summary=run(fixture,a.engine,identity,a.mode,a.endpoint,a.bits,a.cache_mib,record)
    (a.output/'summary.json').write_text(json.dumps(summary,indent=2,allow_nan=False)+'\n')
    print(json.dumps(summary,allow_nan=False))


if __name__=='__main__':main()
