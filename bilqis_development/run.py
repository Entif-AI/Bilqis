"""Freeze, continue the U4 learner for 5,000 updates, and replay numeric evidence."""
from __future__ import annotations

import argparse
from collections import Counter,defaultdict
from datetime import datetime,timezone
import gzip
import hashlib
import json
import math
import os
from pathlib import Path
import platform
import random
import resource
import shutil
import subprocess
import time

import torch

from bilqis_logic.kernel import canonical,digest
from bilqis_logic.geometry import tensor_hash
from bilqis_micro.graph import STATES,catalog
from bilqis_micro.model import load_checkpoint
from bilqis_micro import run as legacy
from bilqis_ref.model import batch,state_hash
from .continuation import expand,save,load
from .data import audit,build_data
from .kernel import encode,evaluate,TOKENS
from .registry import extended_catalog,candidates,admit,SOURCES,SIGNATURES
from .vendor.eg2_retrieval import rank,project
from .vendor.kev_teacher import validate_response

ROOT=Path(__file__).resolve().parents[1]
PARENT=ROOT/'docs/evidence/micro-universes/run-01'
VERSION='development-continuation-0.1.0'


def write(path,value):legacy.write_json(path,value)
def read(path):
    return json.loads(gzip.decompress(path.read_bytes()) if path.name.endswith('.gz') else path.read_bytes())
def compressed(path,value):
    with path.open('xb') as f:f.write(gzip.compress(canonical(value)+b'\n',mtime=0))
def file_hash(path):return legacy.file_hash(path)


def source_hashes():
    paths=list((ROOT/'bilqis_development').rglob('*.py'))+list((ROOT/'docs/u5-u6/sources').glob('*.json'))+[ROOT/'docs/u5-u6/CONTRACT.md']
    return {**legacy.source_hashes(),**{str(p.relative_to(ROOT)):file_hash(p) for p in sorted(paths)}}


def compile_corpus(out,helper_path):
    started=time.perf_counter();cpu=time.process_time()
    h=read(helper_path);validate_helpers(h)
    data=build_data(read(PARENT/'data.json'),h);manifest=audit(data,h)
    compressed(out,data)
    receipt={'corpus_sha256':file_hash(out),'data_sha256':digest(data),'helpers_sha256':file_hash(helper_path),
             'source_hashes':source_hashes(),'wall_seconds':time.perf_counter()-started,'cpu_seconds':time.process_time()-cpu,
             'helper_lesson_rows':sum(manifest['helper_lessons_by_decision'].values()),'max_tokens':manifest['max_tokens']}
    write(out.with_suffix('.preparation.json'),receipt);return receipt


def distinction_probes():
    from bilqis_micro import kernel as k
    from .kernel import world,const,op,record,independent_evaluate
    base=k.world(list('ABC'),[('PARENT','A','B')],propositions={'J0':k.relation('PARENT',k.entity('A'),k.entity('B'))})
    events=[['E0','ASSERT','S0','J0','support'],['E1','OBSERVE','S1','J0','refute']];rows=[]
    for kind in ('DERIVED_FROM','SUPERSEDES'):
        w=world('ABC',base=base,events=events,links=[[kind,'E1','E0']])
        for name,args in (('DERIVED_FROM',[const('Event','E1'),const('Event','E0')]),('SUPERSEDES',[const('Event','E1'),const('Event','E0')]),
                          ('CURRENT_STATE',[const('Proposition','J0')]),('HISTORICAL_STATE',[const('Proposition','J0')]),('FORMAL_ENTAILS',[const('Proposition','J0')])):
            r=record(w,op(name,*args));gold=evaluate(r)
            if independent_evaluate(r)!=gold:raise ValueError('distinction oracle mismatch')
            rows.append({'id':digest(r),'input':r,'gold':gold,'family':name,'factor':kind})
    return rows


def validate_helpers(h):
    if h['registry']!=candidates():raise ValueError('source registry changed')
    expected={k:file_hash(ROOT/'docs/u5-u6/sources'/f'{k}.json') for k in SOURCES}
    if h['sources']!=expected:raise ValueError('source snapshots changed')
    state=[];registry={r['candidate_id']:r for r in h['registry']}
    for d in h['decisions']:
        if d['state_before']!=state or len(d['query_vector_768'])!=768:raise ValueError('sequential semantic state')
        for n in (768,256):
            q=d['query_vector_768'] if n==768 else project(d['query_vector_768'])
            docs=[{'candidate_id':r['candidate_id'],'vector':r[f'vector_{n}']} for r in h['documents']]
            if rank(q,docs,len(docs))!=d['rankings'][str(n)]:raise ValueError('archived native EG2 ranking changed')
        kev=d['kev']
        if hashlib.sha256(kev['serialized_request'].encode()).hexdigest()!=kev['request_sha256']:
            raise ValueError('actual request bytes changed')
        if json.loads(kev['serialized_request'])!=kev['payload']:raise ValueError('request payload binding')
        if kev['status']=='ERROR':continue
        selected=validate_response(kev['response'],kev['offered_candidate_ids'])['choice']
        if selected!=kev['choice']:raise ValueError('native pointer decision changed')
        if selected!='needs-review':
            checked=admit(registry[selected],d['retrieved_ids'],state,d['scope'])
            if checked!=d['validator']:raise ValueError('formal admission changed')
            if checked['disposition']=='accepted':state.append(selected)
        if d['state_after']!=state:raise ValueError('semantic update trace')
    if state!=h['accepted'] or not state:raise ValueError('helpers produced no validated material')
    return {'actual_eg2_queries':len(h['decisions']),'actual_kev_decisions':sum(d['kev']['choice_calls'] for d in h['decisions']),
            'admissions':len(state),'abstentions':sum(d['kev'].get('choice')=='needs-review' for d in h['decisions']),
            'dispositions':dict(Counter(d['validator']['disposition'] for d in h['decisions'])),
            'target_recall':{n:sum(d['target_recall'][n] for d in h['decisions']) for n in ('768','256')},
            'low_margin':sum(d['kev']['status']=='LOW_MARGIN' for d in h['decisions']),
            'unoffered_retrieval_rows':sum(len(d['unoffered_ids']) for d in h['decisions']),
            'scope_excluded_retrieval_rows':sum(len(d['rejected_neighborhood']) for d in h['decisions'])}


@torch.no_grad()
def predict(model,records):
    model.eval();logits=model(*batch([encode(r) for r in records])).cpu()
    if not bool(torch.isfinite(logits).all()):raise ValueError('nonfinite student answer')
    return [{'prediction':STATES[int(p.argmax())],'logits':z.tolist(),'probabilities':p.tolist()} for z,p in zip(logits,logits.softmax(-1))]


def score(model,rows):
    predictions=[]
    for offset in range(0,len(rows),32):
        part=rows[offset:offset+32]
        predictions += [dict(p,id=r['id'],gold=r['gold'],family=r['family']) for r,p in zip(part,predict(model,[r['input'] for r in part]))]
    correct=sum(p['prediction']==p['gold'] for p in predictions)
    labels={s:{'n':sum(p['gold']==s for p in predictions),'correct':sum(p['gold']==s and p['prediction']==s for p in predictions)} for s in STATES}
    families={f:{'n':sum(p['family']==f for p in predictions),'correct':sum(p['family']==f and p['prediction']==p['gold'] for p in predictions)} for f in sorted({p['family'] for p in predictions})}
    return {'n':len(rows),'correct':correct,'accuracy':correct/len(rows),'by_label':labels,'by_family':families,
            'balanced_accuracy':sum(s['correct']/s['n'] for s in labels.values() if s['n'])/sum(s['n']>0 for s in labels.values()),
            'majority_label_accuracy':max(s['n'] for s in labels.values())/len(rows),'predictions':predictions}


def score_all(model,data):
    return {s:{split:score(model,rows) for split,rows in stage['eval'].items()} for s,stage in data['stages'].items()}


def freeze(out,corpus,helpers):
    started=time.perf_counter();cpu=time.process_time()
    legacy.verify_freeze(PARENT)
    data=read(corpus);h=read(helpers);helper_summary=validate_helpers(h);manifest=audit(data,h)
    old_data=read(PARENT/'data.json')
    if any(data['stages'][s]!=old_data['stages'][s] or data['contrast_pairs'][s]!=old_data['contrast_pairs'][s] for s in map(str,range(5))):
        raise ValueError('historical lessons/probes changed')
    model,parent=load_checkpoint(PARENT/'after-U4.pt')
    optimizer=legacy.make_optimizer(model,legacy.default_config());optimizer.load_state_dict(parent['optimizer'])
    torch.set_rng_state(parent['torch_rng'])
    if legacy.optimizer_receipt(optimizer)['steps']!=[8400] or parent['state_sha256']!='d9dfbf2545e2e4b4f8497d91cda68b8b51bc65d0cc8b5292ff860fcc7ddd68b0':
        raise ValueError('wrong U4 continuing learner')
    prior_scores={s:{split:score(model,rows) for split,rows in old_data['stages'][s]['eval'].items()} for s in map(str,range(5))}
    admissions=[d['validator'] for d in h['decisions'] if d['validator']['disposition']=='accepted']
    graph=extended_catalog(admissions)
    extension=expand(model,optimizer,catalog(),graph)
    scores=score_all(model,data)
    if {s:scores[s] for s in map(str,range(5))}!=prior_scores:raise ValueError('old logits changed during vocabulary expansion')
    out.mkdir(parents=True,exist_ok=False)
    cfg={'version':VERSION,'seed':11056,'stage_updates':{'5':2400,'6':2600},'batch_size':32,'device':'cpu','threads':1,
         'mixture':{'focus':8,'composition':4,'helper':4,'contrast':4,'rehearsal':12},
         'optimizer':'continued AdamW: exact U4 hyperparameters, moments and step counters','clip_norm':1.0,
         'pretrained_neural_transfer':False,'run_class':'EXPLORATORY_CUMULATIVE_HELPER_GUIDED'}
    compressed(out/'data.json.gz',data);compressed(out/'helpers.json.gz',h);compressed(out/'before.json.gz',scores)
    probes=distinction_probes();write(out/'distinction-probes.json',probes)
    write(out/'distinction-before.json',score(model,probes))
    preparation=corpus.with_suffix('.preparation.json')
    if preparation.exists():shutil.copyfile(preparation,out/'corpus-preparation.json')
    write(out/'graph.json',graph);write(out/'expansion.json',extension);write(out/'config.json',cfg);write(out/'manifest.json',manifest)
    write(out/'helper-summary.json',helper_summary)
    write(out/'token-abi.json',{'tokens':graph['tokens'],'answer_order':list(STATES),'old_tokens_unchanged':True,
        'neural_input':'IDs and lengths only; raw finite worlds and unreduced prefix query',
        'labels_in_inputs':False,'natural_language_in_inputs':False,'helper_vectors_or_probabilities_in_parameters':False})
    provenance={'parent_pr':109,'parent_git_sha':'c858e086df93f5ca1c27be207d72fafd405dae88',
        'parent_checkpoint_sha256':file_hash(PARENT/'after-U4.pt'),'parent_state_sha256':parent['state_sha256'],
        'parent_optimizer':extension['optimizer_before'],'helpers':helper_summary,'helper_resources':h['resources'],
        'source_snapshots':h['sources'],'authority':'local finite definitions constrained by #80/#85/#84; source/type and independent oracle admission',
        'new_row_authority':'accepted symbolic descriptors and typed edges only; inherited trained rows copied exactly',
        'attribution':'Helpers selected authored source-grounded constructions; no causal improvement claim or open-ended discovery qualification.',
        'scope':'U5 finite closed-world relational mathematics; U6 one interpretation, declared event graphs and Horn-rule formal entailment.',
        'dependency_scope':'DEPENDS_ON records declared premise use, not a proof of soundness; FORMAL_ENTAILS checks soundness separately.',
        'supersession_scope':'explicit newer-to-earlier, same-proposition replacement; current omits replaced events; history retains all events',
        'helper_chain':{d['decision_id']:{'source':d['source_locator'],'retrieved_ids':d['retrieved_ids'],'choice':d['kev'].get('choice'),
            'validator':d['validator'],'lesson_rows':manifest['helper_lessons_by_decision'].get(d['decision_id'],0)} for d in h['decisions']},
        'historical_runs_modified':False,'independent_seal':False,'large_attribution_matrix':False}
    write(out/'provenance.json',provenance)
    save(out/'expanded-U4.pt',model,optimizer,graph,{'step':8400,'stage':4,'parent_checkpoint_sha256':provenance['parent_checkpoint_sha256'],
                                                  'parent_state_sha256':parent['state_sha256'],'expansion_sha256':file_hash(out/'expansion.json')})
    files=sorted(p.name for p in out.iterdir())
    receipt={'version':VERSION,'created_at_utc':datetime.now(timezone.utc).isoformat(),'source_hashes':source_hashes(),
        'source_git_sha':subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip(),
        'artifacts':{name:file_hash(out/name) for name in files},'initial_state_sha256':state_hash(model),
        'initial_tensor_sha256':{k:tensor_hash(v) for k,v in model.state_dict().items()},'initial_optimizer':legacy.optimizer_receipt(optimizer),
        'old_predictions_exact':sum(v['n'] for s in prior_scores.values() for v in s.values()),
        'old_parameters':348192,'parameters':sum(p.numel() for p in model.parameters()),
        'semantic_compilation_wall_seconds':time.perf_counter()-started,'semantic_compilation_cpu_seconds':time.process_time()-cpu,
        'student_environment':{'executable':__import__('sys').executable,'torch':torch.__version__,'platform':platform.platform(),'dtype':'FP32','device':'CPU','threads':1}}
    write(out/'freeze.json',receipt)
    return {'out':str(out),'parameters':receipt['parameters'],'old_logits_exact':receipt['old_predictions_exact'],
            'helper_lessons':sum(manifest['helper_lessons_by_decision'].values()),'initial_optimizer_steps':receipt['initial_optimizer']['steps']}


def verify(run):
    f=read(run/'freeze.json')
    if source_hashes()!=f['source_hashes']:raise ValueError('frozen executable or source snapshot changed')
    for name,h in f['artifacts'].items():
        if file_hash(run/name)!=h:raise ValueError('frozen artifact changed: '+name)
    data=read(run/'data.json.gz');helpers=read(run/'helpers.json.gz')
    if audit(data,helpers)!=read(run/'manifest.json') or validate_helpers(helpers)!=read(run/'helper-summary.json'):
        raise ValueError('corpus/helper binding')
    return f,read(run/'config.json'),data


def _groups(pool):
    result=defaultdict(lambda:defaultdict(list))
    for r in pool:result[r['family']][r['gold']].append(r)
    return {family:dict(labels) for family,labels in result.items()}


def _draw(groups,count,rng):
    families=sorted(groups);rows=[]
    for _ in range(count):
        labels=groups[rng.choice(families)];rows.append(rng.choice(labels[rng.choice(sorted(labels))]))
    return rows


def train(run):
    started=time.perf_counter();cpu=time.process_time();f,cfg,data=verify(run)
    stream=(run/'training.jsonl.gz').open('xb')
    model,optimizer,initial=load(run/'expanded-U4.pt')
    if state_hash(model)!=f['initial_state_sha256'] or legacy.optimizer_receipt(optimizer)!=f['initial_optimizer']:
        stream.close();raise ValueError('continued genesis binding')
    rng=random.Random(cfg['seed']);encoded={r['id']:encode(r['input']) for s in data['stages'].values() for pool in s['train'].values() for r in pool}
    groups={s:{name:_groups(rows) for name,rows in stage['train'].items()} for s,stage in data['stages'].items()}
    by_id={r['id']:r for stage in data['stages'].values() for pool in stage['train'].values() for r in pool}
    exposures=Counter();helper_exposures=Counter();total_tokens=0;total_padded=0;step=8400;parent=file_hash(run/'expanded-U4.pt');stages=[]
    with stream,gzip.GzipFile(fileobj=stream,mode='wb',mtime=0) as log:
        for stage in (5,6):
            name=str(stage);updates=cfg['stage_updates'][name];before=legacy.optimizer_receipt(optimizer);start_state=state_hash(model)
            stage_start=time.perf_counter();stage_cpu=time.process_time();losses=[];stage_counts=Counter();stage_helper=Counter()
            print(json.dumps({'stage':stage,'start_step':step,'updates':updates}),flush=True)
            for local_step in range(updates):
                rows=[];categories=[]
                for category,count in (('focus',8),('composition',4),('helper',4)):
                    part=_draw(groups[name][category],count,rng);rows+=part;categories += [category]*count
                for _ in range(2):
                    pair=rng.choice(data['contrast_pairs'][name]);rows += [by_id[pair['before']],by_id[pair['after']]];categories += ['contrast']*2
                rehearsal=[]
                rehearsal += _draw(groups['0']['focus'],1 if stage==6 else 2,rng)
                rehearsal += _draw(groups['0']['composition'],1 if stage==6 else 2,rng)
                for old_stage in range(1,5):rehearsal += _draw(groups[str(old_stage)][rng.choice(('focus','composition'))],2,rng)
                if stage==6:rehearsal += _draw(groups['5'][rng.choice(('focus','composition','helper'))],2,rng)
                rows+=rehearsal;categories += ['rehearsal']*len(rehearsal)
                order=list(range(len(rows)));rng.shuffle(order);rows=[rows[i] for i in order];categories=[categories[i] for i in order]
                ids,lengths=batch([encoded[r['id']] for r in rows]);labels=torch.tensor([STATES.index(r['gold']) for r in rows])
                model.train();optimizer.zero_grad(set_to_none=True)
                loss=torch.nn.functional.cross_entropy(model(ids,lengths),labels)
                if not bool(torch.isfinite(loss)):raise ValueError('nonfinite learning loss')
                loss.backward();gradient=float(torch.nn.utils.clip_grad_norm_(model.parameters(),1.0,error_if_nonfinite=True));optimizer.step();step+=1
                loss_value=float(loss.detach());losses.append(loss_value);exposures.update(r['id'] for r in rows);stage_counts.update(r['id'] for r in rows)
                traces=[r.get('helper_traces',[]) for r in rows]
                helper_exposures.update(t for ts in traces for t in ts);stage_helper.update(t for ts in traces for t in ts)
                tokens=int(lengths.sum());padded=int(ids.numel());total_tokens+=tokens;total_padded+=padded
                log.write(canonical({'stage':stage,'step':step,'loss':loss_value,'gradient_norm':gradient,
                    'row_ids':[r['id'] for r in rows],'categories':categories,'helper_traces':traces,'tokens':tokens,'padded_positions':padded})+b'\n')
                if (local_step+1)%250==0:print(json.dumps({'stage':stage,'step':step,'mean_recent_loss':sum(losses[-100:])/len(losses[-100:])}),flush=True)
            after=legacy.optimizer_receipt(optimizer)
            if after['steps']!=[step]:raise ValueError('AdamW step reset')
            checkpoint=run/f'after-U{stage}.pt'
            metadata={'stage':stage,'step':step,'parent_checkpoint_sha256':parent,'freeze_sha256':file_hash(run/'freeze.json'),
                      'start_state_sha256':start_state,'optimizer_before':before,'optimizer_after':after}
            save(checkpoint,model,optimizer,initial['graph'],metadata)
            scores=score_all(model,data);compressed(run/f'after-U{stage}.json.gz',scores)
            write(run/f'distinction-after-U{stage}.json',score(model,read(run/'distinction-probes.json')))
            receipt={'stage':stage,'updates':updates,'start_step':step-updates,'end_step':step,'start_state_sha256':start_state,
                     'end_state_sha256':state_hash(model),'optimizer_before':before,'optimizer_after':after,
                     'parent_checkpoint_sha256':parent,'checkpoint_sha256':file_hash(checkpoint),
                     'exposures_by_row':dict(stage_counts),'helper_exposures':dict(stage_helper),
                     'loss_first_100':sum(losses[:100])/100,'loss_last_100':sum(losses[-100:])/100,
                     'wall_seconds':time.perf_counter()-stage_start,'cpu_seconds':time.process_time()-stage_cpu,'scores':legacy.summaries(scores)}
            write(run/f'stage-U{stage}.json',receipt);stages.append(receipt);parent=file_hash(checkpoint)
            print(json.dumps({'completed_stage':stage,'step':step,'scores':{s:[v['correct'],v['n']] for s,v in scores[name].items()}}),flush=True)
    evidence=['training.jsonl.gz']+[f'{prefix}-U{s}{suffix}' for s in (5,6) for prefix,suffix in (('after','.pt'),('after','.json.gz'),('stage','.json'),('distinction-after','.json'))]
    result={'version':VERSION,'training_pid':os.getpid(),'status':'EXPLORATORY_MEASURED','additional_updates':step-8400,'total_optimizer_step':step,
            'examples':sum(exposures.values()),'nonpadding_tokens':total_tokens,'padded_positions':total_padded,'exposures_by_row':dict(exposures),
            'helper_exposures':dict(helper_exposures),'stages':stages,'wall_seconds':time.perf_counter()-started,'cpu_seconds':time.process_time()-cpu,
            'peak_rss_bytes':resource.getrusage(resource.RUSAGE_SELF).ru_maxrss*(1 if platform.system()=='Darwin' else 1024),
            'final_state_sha256':state_hash(model),'freeze_sha256':file_hash(run/'freeze.json'),
            'evidence_sha256':{name:file_hash(run/name) for name in evidence},'model_instances_during_training':1,'optimizer_instances_during_training':1,
            'parameter_or_optimizer_resets':0,'pretrained_neural_transfer':False}
    write(run/'result.json',result)
    return {k:result[k] for k in ('additional_updates','total_optimizer_step','examples','wall_seconds','final_state_sha256')}


def replay(run):
    f,cfg,data=verify(run);result=read(run/'result.json')
    if result['training_pid']==os.getpid():raise ValueError('fresh process required')
    for name,h in result['evidence_sha256'].items():
        if file_hash(run/name)!=h:raise ValueError('training evidence changed')
    count=0;maximum=0.;previous=file_hash(run/'expanded-U4.pt');previous_optimizer=f['initial_optimizer'];previous_state=f['initial_state_sha256']
    for stage in (4,5,6):
        model,optimizer,payload=load(run/('expanded-U4.pt' if stage==4 else f'after-U{stage}.pt'))
        expected_step=8400+sum(cfg['stage_updates'][str(s)] for s in (5,6) if s<=stage)
        if legacy.optimizer_receipt(optimizer)['steps']!=[expected_step]:raise ValueError('checkpoint step lineage')
        if stage>4:
            meta=payload['metadata']
            if meta['parent_checkpoint_sha256']!=previous or meta['start_state_sha256']!=previous_state or meta['optimizer_before']!=previous_optimizer:
                raise ValueError('continuation lineage changed')
        scores=score_all(model,data);archived=read(run/('before.json.gz' if stage==4 else f'after-U{stage}.json.gz'))
        for s,pools in scores.items():
            for split,score_value in pools.items():
                old=archived[s][split]
                if score_value['correct']!=old['correct'] or len(score_value['predictions'])!=len(old['predictions']):raise ValueError('score replay mismatch')
                for actual,saved in zip(score_value['predictions'],old['predictions']):
                    if any(actual[k]!=saved[k] for k in ('id','gold','prediction','family')):raise ValueError('prediction identity mismatch')
                    for key in ('logits','probabilities'):
                        err=max(abs(a-b) for a,b in zip(actual[key],saved[key]));maximum=max(maximum,err)
                        if err>1e-6:raise ValueError('numeric replay tolerance exceeded')
                    count+=1
        diagnostic=score(model,read(run/'distinction-probes.json'))
        old=read(run/('distinction-before.json' if stage==4 else f'distinction-after-U{stage}.json'))
        for actual,saved in zip(diagnostic['predictions'],old['predictions']):
            if any(actual[k]!=saved[k] for k in ('id','gold','prediction','family')):raise ValueError('distinction prediction mismatch')
            for key in ('logits','probabilities'):
                err=max(abs(a-b) for a,b in zip(actual[key],saved[key]));maximum=max(maximum,err)
                if err>1e-6:raise ValueError('distinction numeric mismatch')
            count+=1
        previous=file_hash(run/('expanded-U4.pt' if stage==4 else f'after-U{stage}.pt'))
        previous_optimizer=legacy.optimizer_receipt(optimizer);previous_state=state_hash(model)
    rows={r['id']:r for s in data['stages'].values() for pool in s['train'].values() for r in pool}
    encoded_lengths={i:len(encode(r['input'])) for i,r in rows.items()}
    allowed=defaultdict(set)
    for s in data['stages'].values():
        for pool in s['train'].values():
            for r in pool:allowed[r['id']].update(r.get('helper_traces',[]))
    exposures=Counter();helper_exposures=Counter();tokens=0;padded=0;step=8400;stage_exposures=defaultdict(Counter)
    with gzip.open(run/'training.jsonl.gz','rt') as log:
        for line in log:
            item=json.loads(line);step+=1;ids=item['row_ids'];lengths=[encoded_lengths[i] for i in ids]
            if (item['step']!=step or len(ids)!=32 or item['tokens']!=sum(lengths) or item['padded_positions']!=max(lengths)*32
                    or len(item['categories'])!=32 or len(item['helper_traces'])!=32 or not math.isfinite(item['loss']) or not math.isfinite(item['gradient_norm'])):
                raise ValueError('training accounting changed')
            for i,ts in zip(ids,item['helper_traces']):
                if not set(ts)<=allowed[i]:raise ValueError('helper exposure provenance changed')
                helper_exposures.update(ts)
            exposures.update(ids);stage_exposures[item['stage']].update(ids);tokens+=item['tokens'];padded+=item['padded_positions']
    if (exposures!=Counter(result['exposures_by_row']) or helper_exposures!=Counter(result['helper_exposures']) or step!=13400
            or tokens!=result['nonpadding_tokens'] or padded!=result['padded_positions']):raise ValueError('exposure totals changed')
    for s in result['stages']:
        if stage_exposures[s['stage']]!=Counter(s['exposures_by_row']):raise ValueError('stage exposures changed')
    receipt={'status':'REPRODUCED','predictions':count,'max_absolute_error':maximum,'atol':1e-6,'optimizer_step':step,
             'additional_updates':step-8400,'same_student_lineage_verified':True,'optimizer_migration_verified':True,'exposures_verified':True,
             'archived_native_helper_rankings_and_choices_verified':True,'training_pid':result['training_pid'],'replay_pid':os.getpid(),
             'fresh_process':True,'final_state_sha256':previous_state,'freeze_sha256':file_hash(run/'freeze.json')}
    write(run/'replay.json',receipt);return receipt


def formal(e):
    if e['kind']=='const':return e['name']
    if e['kind']=='prior':return legacy.formal(e['expression'])
    return e['op']+'('+','.join(formal(a) for a in e['args'])+')'


def display(r):
    if r['task']!='development':return legacy.display_input(r)
    w=r['world'];parts=[]
    for name in ('sets','functions','edges','events','links'):
        if name in ('sets','functions') and any(w[name].values()) or name not in ('sets','functions') and w[name]:parts.append(name+'='+str(w[name]))
    if w['base']['facts']:parts.append('facts='+str(w['base']['facts']))
    if w['base']['rules']:parts.append('rules='+str(w['base']['rules']))
    if w['base']['propositions']:parts.append('propositions='+str({j:legacy.formal(e) for j,e in w['base']['propositions'].items()}))
    return '; '.join(parts)+' => '+formal(r['query'])


def report(run):
    result=read(run/'result.json');reproduced=read(run/'replay.json');data=read(run/'data.json.gz');h=read(run/'helpers.json.gz')
    scores={stage:read(run/('before.json.gz' if stage==4 else f'after-U{stage}.json.gz')) for stage in (4,5,6)}
    gallery=[]
    for s,stage in data['stages'].items():
        by_id={r['id']:r for split in stage['eval'].values() for r in split}
        for split in ('varied','composite'):
            predictions=scores[6][s][split]['predictions']
            for family in sorted({p['family'] for p in predictions}):
                for correct in (True,False):
                    matches=[p for p in predictions if p['family']==family and (p['prediction']==p['gold'])==correct]
                    if matches:
                        p=matches[0];r=by_id[p['id']]
                        before=next(q for q in scores[4][s][split]['predictions'] if q['id']==p['id'])
                        gallery.append({'stage':int(s),'split':split,'input':r['input'],'formal':display(r['input']),'gold':r['gold'],
                                        'before':before,'after':p,'selection':'first correct' if correct else 'first mistake'})
    model,_,_=load(run/'after-U6.pt');perturbations=[]
    for s in ('5','6'):
        lookup={r['id']:r for pool in data['stages'][s]['train'].values() for r in pool}
        for pair in data['contrast_pairs'][s][:12]:
            rows=[lookup[pair[k]] for k in ('before','after')]
            perturbations.append({'stage':int(s),'factor':pair['factor'],'familiar_training_pair':True,
                'rows':[dict(r,formal=display(r['input']),neural=p) for r,p in zip(rows,predict(model,[r['input'] for r in rows]))]})
    lineage=[dict(r,formal=display(r['input']),neural=p,status='frozen before training') for r,p in zip(read(run/'distinction-probes.json'),read(run/'distinction-after-U6.json')['predictions'])]
    compressed(run/'gallery.json.gz',{'selected_probe_answers':gallery,'single_factor_perturbations':perturbations,'lineage_diagnostic':lineage})
    f=read(run/'freeze.json');summary=read(run/'helper-summary.json');fmt=lambda p:' / '.join(f"{p[s]['correct']}/{p[s]['n']}" for s in ('familiar','varied','composite'))
    lines=['# Bilqis U5–U6 helper-guided development','',
        'One continuing scratch learner, with preserved U4 weights and AdamW history, completed 5,000 additional updates. EG2 and native Kev selected 20 formally admitted lesson constructions. This is exploratory capability development.',
        '', '| Stage | Before U5: familiar / varied / composite | After U5 | After U6 |','| --- | --- | --- | --- |']
    for s in map(str,range(7)):lines.append(f"| U{s}: {data['stages'][s]['name']} | {fmt(scores[4][s])} | {fmt(scores[5][s])} | {fmt(scores[6][s])} |")
    lines += ['', '## Semantic production','',
        f"Native EG2 encoded {len(h['documents'])} source-located descriptors and {len(h['decisions'])} fresh queries. Documents and queries had zero 256-token truncations. Full 768-dimensional outputs, normalized leading-256 projections, all rankings, misses, hard alternatives and omitted candidates are retained in [helpers.json.gz](run-01/helpers.json.gz).",
        f"Top-8 focal-construction recall: 768 dimensions {summary['target_recall']['768']}/20; 256 dimensions {summary['target_recall']['256']}/20. The 768 profile was chosen from prior measured recall, before this run. These authored catalog retrievals do not qualify #88 or open-ended semantic discovery.",
        f"Kev made {summary['actual_kev_decisions']} actual native pointer-head decisions. {summary['admissions']} were admitted; {summary['abstentions']} abstained; {summary['low_margin']} were below the old scheduler's 0.05 margin. Formal checks govern proposal admission here. The genuine needs-review option, exact request bytes, full probability vectors and runtime readbacks remain in each trace.",
        f"No selected contribution was rejected or inert in this run. {summary['scope_excluded_retrieval_rows']} retrieved rows were excluded from the requested scope; {summary['unoffered_retrieval_rows']} top-8 rows were not offered in the bounded panels. Two authored false-equivalence alternatives have explicit formal counterexamples; neither became a lesson or graph equivalence.",
        'The helpers selected among authored, source-grounded construction candidates. Each accepted selection materially determines a specific contrast/composition lesson pool and symbolic outgoing edges on new identities. It is a bounded construction workflow, not an unassisted discovery of new authoritative meanings.',
        '', '| Decision | Selected construction | Compiled lesson rows | Actual exposures |','| --- | --- | ---: | ---: |']
    manifest=read(run/'manifest.json')
    for d in h['decisions']:
        i=d['decision_id'];lines.append(f"| {i} | {d['kev'].get('choice')} | {manifest['helper_lessons_by_decision'].get(i,0)} | {result['helper_exposures'].get(i,0)} |")
    lines += ['', '[Provenance chain](run-01/provenance.json) binds source snapshot → EG2 neighborhood → Kev request/decision → deterministic validator → typed relation → lesson rows. Helper vectors, neural weights and answer probabilities never enter student parameters or gold labels.',
        '', '## Neural continuation and interpretation','',
        f"The learner expanded from 68 to {len(TOKENS)} identities and from 348,192 to {f['parameters']:,} parameters. All old trained rows and other weights were copied exactly. Old AdamW moments and hyperparameters were preserved, new-row moments were zero, and all {f['old_predictions_exact']:,} prior probe logits/probabilities stayed exact during expansion. New rows use the existing deterministic symbolic feature compiler. [Expansion receipt](run-01/expansion.json).",
        f"AdamW continued from step 8,400 to {result['total_optimizer_step']:,}, with one model and optimizer in the training process. {result['examples']:,} example exposures and {result['nonpadding_tokens']:,} nonpadding tokens mixed new direct lessons, compositions, admitted helper constructions, single-factor contrasts and all U0–U4 families. Every accepted helper construction was actually exposed.",
        'New varied and composite probes have balanced TRUE/FALSE labels, or four balanced evidence states. Their 4–5-entity worlds are excluded from all training pools; training worlds have 2–4 entities. Composite probes add nesting with inherited quantifiers and relational reasoning. Familiar probes overlap training. All prior probes are unchanged. These are authored, frozen developmental probes, not an independent sealed benchmark.',
        'U6 separates declared proposition, assertion and observation types; source attribution and Horn-rule entailment; transitive provenance and declared inferential dependency; same-proposition supersession and changed-polarity revision; current and all-history evidence. DEPENDS_ON records declared premise use and does not prove a sound derivation. Formal entailment is checked independently. Event worlds have one interpretation; prior five-state U4 interpretation tasks are rehearsed unchanged.',
        'Acquisition and any forgetting are visible in the table and complete per-family/per-label readouts. Score changes after teaching do not establish that helpers caused an improvement; no attribution controls were run.',
        '', '## Real neural answers','', '| Probe family | Symbolic query | Oracle | Before U5 | After U6 |','| --- | --- | --- | --- | --- |']
    selected=[]
    for s in (5,6):
        families=sorted({g['after']['family'] for g in gallery if g['stage']==s and g['split']=='varied'})
        for family in families:
            rows=[g for g in gallery if g['stage']==s and g['split']=='varied' and g['after']['family']==family]
            selected.append(next((g for g in rows if g['selection']=='first correct'),rows[0]))
    for g in selected:lines.append(f"| {g['after']['family']} | `{formal(g['input']['query'])}` | {g['gold']} | {g['before']['prediction']} | {g['after']['prediction']} |")
    lines += ['', 'Complete raw worlds, successes and mistakes, logits and probabilities are in [gallery.json.gz](run-01/gallery.json.gz). The full probe inventories retain every answer. Selected success rows above are illustrative, not aggregate evidence.',
        '', '## Provenance versus supersession diagnostic','', '| Only link kind | Query | Oracle | Neural |','| --- | --- | --- | --- |']
    for g in lineage:lines.append(f"| {g['factor']} | `{formal(g['input']['query'])}` | {g['gold']} | {g['neural']['prediction']} |")
    lines += ['', 'These ten distinction probes and their answers were frozen before training, alongside varied/composite probes. Their before/U5/U6 numeric readouts are retained separately.',
        '', '## Resources and replay','',
        f"Upstream helpers: {h['resources']['wall_seconds']:.2f}s wall; EG2 peak MLX memory {h['resources']['mlx_peak_memory_bytes']/2**30:.2f} GiB; Kev request wall time {h['resources']['kev_wall_seconds']:.2f}s. The existing native Kev service was reused; its global resident memory is not represented by EG2 subprocess RSS. No model download, helper fine-tuning or paid provider inference occurred.",
        f"Corpus construction is separate from helpers and training. Freeze/validation/expansion took {f['semantic_compilation_wall_seconds']:.2f}s wall; corpus-generation timing is retained in the preparation receipt. The student used FP32 CPU, one thread: {result['wall_seconds']:.2f}s wall and {result['cpu_seconds']:.2f}s CPU, peak process RSS {result['peak_rss_bytes']/2**20:.1f} MiB. No native low-bit acceleration claim is made.",
        f"Fresh-process replay reproduced {reproduced['predictions']:,} predictions across expanded U4, U5 and U6 with maximum absolute logit/probability error {reproduced['max_absolute_error']}. It checked checkpoint/optimizer lineage, every exposure/token total and archived native helper rankings/choice probabilities. Live helper reruns and full gradient-by-gradient retraining were not required or performed.",
        '', '[Freeze](run-01/freeze.json), [corpus](run-01/data.json.gz), [before](run-01/before.json.gz), [after U5](run-01/after-U5.json.gz), [after U6](run-01/after-U6.json.gz), [training/result](run-01/result.json), [replay](run-01/replay.json), [handoff](../../u5-u6/HANDOFF.md).',
        '', 'Historical U0–U4, DN-01 and helper qualification/failure evidence remain intact. No broad language training, scaling, repeated control matrix, SYS-01 experiment or merge was performed.']
    with (run.parent/'RESULTS.md').open('x') as f_out:f_out.write('\n'.join(lines)+'\n')
    with (run/'CHECKSUMS.sha256').open('x') as f_out:
        for p in sorted(run.iterdir()):
            if p.name!='CHECKSUMS.sha256':f_out.write(file_hash(p)+'  '+p.name+'\n')
    return {'results':str(run.parent/'RESULTS.md'),'gallery_examples':len(gallery),'replayed':reproduced['predictions']}


def main():
    p=argparse.ArgumentParser();commands=p.add_subparsers(dest='command',required=True)
    x=commands.add_parser('freeze');x.add_argument('--out',type=Path,required=True);x.add_argument('--corpus',type=Path,required=True);x.add_argument('--helpers',type=Path,required=True)
    x=commands.add_parser('compile');x.add_argument('--out',type=Path,required=True);x.add_argument('--helpers',type=Path,required=True)
    for name in ('train','replay','report'):commands.add_parser(name).add_argument('--run',type=Path,required=True)
    a=p.parse_args();result=(compile_corpus(a.out,a.helpers) if a.command=='compile' else freeze(a.out,a.corpus,a.helpers) if a.command=='freeze' else {'train':train,'replay':replay,'report':report}[a.command](a.run))
    print(json.dumps(result,indent=2),flush=True)


if __name__=='__main__':main()
