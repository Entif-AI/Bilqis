"""BILQIS-DN-01: immutable preparation, native engines, one matched pair, replay."""
import argparse
from collections import Counter, defaultdict
from dataclasses import asdict
import hashlib
import json
from pathlib import Path
import resource
import subprocess
import sys
import time
from uuid import uuid4

import torch
from torch.nn import functional as F
from bilqis_ref.model import batch, state_hash
from .decision_episodes import build, DATASET_SHA256, BATCHES_SHA256
from .decision_features import compile_embeddings, feature_map, token_manifest
from .decision_navigation import (RESERVED, apply, candidate_tokens, focus, initial,
                                  oracle_trace, panel, render, state_tokens, target)
from .decision_student import initialize, load_checkpoint, save_checkpoint
from .decision_baseline import CueBaseline, audit
from .eg2_retrieval import filter_retrieval, hard_negative_separation, rank
from .kev_teacher import KevTeacher, MIN_MARGIN
from .semantics import canonical, digest, registry, sid

VERSION='bilqis-decision-epoch-02-0.1.0'
DEFAULT_RUN=Path('runs/decision-epoch-02')
HISTORICAL=Path('/Users/emilie/.codex/worktrees/bilqis-alpha-102/Bilqis/runs/alpha/epoch-01/model.pt')
HISTORICAL_SHA='002cffcfbdf44eec2e509704d5a530bb134d655919ec129f46eeffda6b99a3eb'
EG2_PYTHON='/Users/emilie/Code/Bilqis/.venv-eg2/bin/python'
EG2_MODEL=Path('/Users/emilie/.lmstudio/models/mlx-community/embeddinggemma-2-bf16')


def read(path): return json.loads(Path(path).read_text())


def write(path, value):
    path=Path(path); path.parent.mkdir(parents=True,exist_ok=True)
    with path.open('x') as f: f.write(json.dumps(value,sort_keys=True,indent=2,allow_nan=False)+'\n')


def file_hash(path):
    with Path(path).open('rb') as f: return hashlib.file_digest(f,'sha256').hexdigest()


def archived_request(trace):
    serialized=trace['serialized_request']
    request=json.loads(serialized)
    if (hashlib.sha256(serialized.encode()).hexdigest()!=trace['request_sha256']
        or request!=trace['payload']
        or list(request['questions']['decision']['criteria'])!=trace['offered_candidate_ids']):
        raise ValueError('ARCHIVED_REQUEST_BINDING')
    return request


def amended_source_hash(path,frozen_hash,manifest,receipt):
    # One explicit append-only repair; the original training/evaluation source stays frozen.
    if (path!='bilqis_alpha/decision_experiment.py' or receipt['file']!=path
        or receipt['frozen_source_commit']!=manifest['source_commit']
        or receipt['old_file_sha256']!=frozen_hash
        or receipt['scope']!='archived Kev request order and explicit replay-source admission only'):
        raise ValueError('SOURCE_AMENDMENT_BINDING')
    committed=subprocess.check_output(['git','show',receipt['new_source_commit']+':'+path])
    if hashlib.sha256(committed).hexdigest()!=receipt['new_file_sha256']:
        raise ValueError('SOURCE_AMENDMENT_BINDING')
    return receipt['new_file_sha256']


def check_frozen(data, manifest):
    if digest(data)!=manifest['dataset_sha256']: raise ValueError('FROZEN_DATASET_TAMPER')


def validate_initial(model,payload,manifest):
    if (state_hash(model)!=manifest['initial_state_sha256'] or payload['initializer']!=manifest['initializer']
        or asdict(model.config)!=manifest['config'] or payload['metadata']!={'epoch':VERSION,'dataset_sha256':manifest['dataset_sha256']}):
        raise ValueError('PREPARED_INITIAL_CHECKPOINT_BINDING')


def verified_arm(run,paired,arm,manifest):
    path=run/f'{arm}.pt'
    if file_hash(path)!=paired['arms'][arm]['checkpoint_sha256']: raise ValueError('CHECKPOINT_TAMPER')
    model,payload=load_checkpoint(path)
    expected={'epoch':VERSION,'arm':arm,'order':paired['arms'][arm]['order'],'dataset_sha256':manifest['dataset_sha256']}
    if (state_hash(model)!=paired['arms'][arm]['final_state_sha256'] or payload['metadata']!=expected
        or paired['version']!=VERSION or paired['dataset_sha256']!=manifest['dataset_sha256']
        or asdict(model.config)!=manifest['config'] or payload['initializer']!=manifest['initializer']):
        raise ValueError('PAIRED_CHECKPOINT_BINDING')
    return model,payload


def qualified_inputs(run,manifest):
    qualification=read(run/'qualification.json')
    if (qualification['version']!=VERSION or qualification['dataset_sha256']!=manifest['dataset_sha256']):
        raise ValueError('QUALIFICATION_BINDING')
    if qualification['disposition']!='ENGINES_VERIFIED': raise ValueError('HYBRID_ENGINE_BLOCKED')
    if file_hash(run/'retrieval.json')!=qualification['retrieval_sha256']: raise ValueError('RETRIEVAL_TAMPER')
    retrieval=read(run/'retrieval.json')
    if (retrieval['corpus_sha256']!=manifest['retrieval_input_sha256']
        or retrieval['runtime']!=qualification['eg2_runtime'] or retrieval['model']!=qualification['eg2_model']):
        raise ValueError('QUALIFICATION_RETRIEVAL_BINDING')
    return qualification,retrieval


def compare_neural_replay(actual,saved):
    for field in ('path_correct','status','outcome'):
        if actual[field]!=saved[field]: raise ValueError('NEURAL_REPLAY_CHOICE_DRIFT')
    if len(actual['steps'])!=len(saved['steps']): raise ValueError('NEURAL_REPLAY_STEP_COUNT')
    for a,b in zip(actual['steps'],saved['steps']):
        if (a['state_sha256']!=b['state_sha256'] or a['panel']!=b['panel']
            or any(a['neural'][f]!=b['neural'][f] for f in ('choice','candidate_ids'))):
            raise ValueError('NEURAL_REPLAY_IDENTITY')
        for field in ('logits','probabilities'):
            left=torch.tensor(a['neural'][field]); right=torch.tensor(b['neural'][field])
            if left.shape!=right.shape or not torch.allclose(left,right,atol=1e-6,rtol=0):
                raise ValueError('NEURAL_REPLAY_NUMERIC_DRIFT')


def eg2_command(retrieval,input_path,output_path):
    return [retrieval['runtime']['executable'],'-m','bilqis_alpha.eg2_retrieval',
            '--input',str(input_path),'--output',str(output_path),'--model',retrieval['model']['path']]


def validate_eg2_replay(current,archived):
    if current['model']!=archived['model'] or current['runtime']!=archived['runtime']:
        raise ValueError('EG2_RUNTIME_DRIFT')


def eligible(blocks, completed):
    numbers={int(x[1:]) for x in completed}
    return [b['block_id'] for b in blocks if b['block_id'] not in completed and set(b['prerequisites'])<=numbers]


def exposure_identity(blocks, order):
    by_id={b['block_id']:b for b in blocks}
    counts=Counter(i for block in order for batch_rows in by_id[block]['batches'] for i in batch_rows)
    return {'sha256':digest(dict(sorted(counts.items()))),'exposures':sum(counts.values()),
            'steps':sum(len(by_id[b]['batches']) for b in order),'unique_rows':len(counts)}


def pack(rows):
    state_ids,lengths=batch([r['state_tokens'] for r in rows])
    k=max(len(r['candidate_tokens']) for r in rows)
    width=max(len(c) for r in rows for c in r['candidate_tokens'])
    candidates=torch.zeros(len(rows),k,width,dtype=torch.long)
    candidate_lengths=torch.zeros(len(rows),k,dtype=torch.long)
    mask=torch.zeros(len(rows),k,dtype=torch.bool)
    for i,r in enumerate(rows):
        for j,c in enumerate(r['candidate_tokens']):
            candidates[i,j,:len(c)]=torch.tensor(c)
            candidate_lengths[i,j]=len(c); mask[i,j]=True
    return state_ids,lengths,candidates,candidate_lengths,mask


@torch.no_grad()
def prediction(model,state,offered):
    model.eval()
    c=offered['candidates']
    logits=model(*pack([{'state_tokens':state_tokens(state),'candidate_tokens':[candidate_tokens(x) for x in c]}]))[0]
    if not bool(torch.isfinite(logits).all()): raise ValueError('NONFINITE_NEURAL_SCORE')
    probabilities=logits.softmax(-1)
    # Explicit semantic-ID tie break, never candidate display position.
    chosen=sorted(range(len(c)),key=lambda i:(-float(logits[i]),c[i]['candidate_id']))[0]
    return {'choice':c[chosen]['candidate_id'],'candidate_ids':[x['candidate_id'] for x in c],
            'logits':logits.tolist(),'probabilities':probabilities.tolist(),
            'provenance':'live scratch-neural candidate inference'}


def rollout(model,episode):
    reference,expected=oracle_trace(episode)
    state=initial(episode); steps=[]
    while state['status']=='active':
        offered=panel(state); output=prediction(model,state,offered)
        chosen=next(c for c in offered['candidates'] if c['candidate_id']==output['choice'])
        index=len(steps)
        expected_id=reference[index]['gold_id'] if index<len(reference) else None
        steps.append({'index':index,'kind':focus(state)['kind'],'canonical_state':render(state),
                      'state_sha256':digest(state),'panel':offered,'neural':output,
                      'expected_candidate_id':expected_id,'correct':output['choice']==expected_id,'valid':True,
                      'semantic_delta':chosen['semantic_delta'],'oracle_provenance':'independent formal trajectory'})
        state=apply(state,offered,output['choice'])
    path_correct=len(steps)==len(reference) and all(s['correct'] for s in steps)
    final_correct=state['status']==expected['status'] and state['outcome']==expected['outcome']
    return {'episode_id':episode['episode_id'],'split':episode['split'],'family':episode['family'],
            'pattern':episode['pattern'],'mode':episode['mode'],'steps':steps,
            'expected_status':expected['status'],'expected_outcome':expected['outcome'],
            'status':state['status'],'outcome':state['outcome'],'path_correct':path_correct and final_correct,
            'final_correct':final_correct,'truth_correct':final_correct if expected['status']=='resolved' else None,
            'evidence_preserved':state['world']==expected['world'],
            'wrong_intermediate_right_terminal':not path_correct and final_correct and expected['status']=='resolved'}


def summarize(rows):
    summary={'cases':len(rows),'path_correct':sum(r['path_correct'] for r in rows),
             'final_correct':sum(r['final_correct'] for r in rows),
             'truth_cases':sum(r['truth_correct'] is not None for r in rows),
             'truth_correct':sum(r['truth_correct'] is True for r in rows),
             'evidence_preserved':sum(r['evidence_preserved'] for r in rows),
             'wrong_intermediate_right_terminal':sum(r.get('wrong_intermediate_right_terminal',False) for r in rows)}
    for metric,kinds in [('selection',None),('orientation',('orient',)),('binding',('bind',)),
                         ('consequence',('fold',)),('evidence_state',('read','add','remove'))]:
        steps=[s for r in rows for s in r['steps'] if kinds is None or s['kind'] in kinds]
        summary[metric]={'steps':len(steps),'correct':sum(s['correct'] for s in steps),'valid':sum(s['valid'] for s in steps)}
    families=defaultdict(list)
    for r in rows: families[r['family']].append(r)
    summary['per_family']={k:{'cases':len(v),'path_correct':sum(r['path_correct'] for r in v),
                              'final_correct':sum(r['final_correct'] for r in v)} for k,v in families.items()}
    summary['reserved']={'cases':sum(r['expected_status']!='resolved' for r in rows),
                        'correct':sum(r['path_correct'] for r in rows if r['expected_status']!='resolved')}
    confusion=Counter((str(r['expected_outcome']),str(r['outcome']),r['status']) for r in rows)
    summary['final_confusion']=[{'expected':a,'observed':b,'status':s,'count':n} for (a,b,s),n in sorted(confusion.items())]
    return summary


def _description(c):
    kind=c['effect_class']; d=c['semantic_delta']
    if kind in RESERVED:
        return {'other':'The required semantic continuation is outside the offered neighborhood.',
                'insufficient':'A required source or capability is missing; preserve insufficiency.',
                'clarify':'The interpretation is ambiguous; request a distinguishing fact.',
                'abstain':'The construction is unsupported; assert no semantic resolution.'}[kind]
    return 'Legal '+kind+' semantic continuation: '+canonical(d).decode()


def _relationships(c, candidates):
    types=('equivalent_meaning','semantic_sibling','near_neighbor','inverse','contrast',
           'exclusion','prerequisite_dependency','hard_negative')
    relations={t:[] for t in types}
    for other in candidates:
        if c['candidate_id']==other['candidate_id']: continue
        kind='inverse' if c['effect_class']==other['effect_class']=='orient' else 'contrast'
        relations[kind].append(other['candidate_id'])
        relations['exclusion'].append(other['candidate_id'])
        if c['effect_class']==other['effect_class']:
            relations['semantic_sibling'].append(other['candidate_id'])
            relations['near_neighbor'].append(other['candidate_id'])
        if kind=='inverse': relations['hard_negative'].append(other['candidate_id'])
    if c['effect_class']=='orient': relations['prerequisite_dependency']=[sid('relation'),sid('role-source'),sid('role-target')]
    elif c['effect_class']=='bind': relations['prerequisite_dependency']=[sid('variable'),sid('role-binder')]
    return [{'type':t,'targets':targets,'authority':'deterministic typed structure; exclusion is single-step choice exclusivity; empty means no asserted edge'}
            for t,targets in relations.items()]


def prepare(run):
    start=time.perf_counter()
    if file_hash(HISTORICAL)!=HISTORICAL_SHA: raise ValueError('HISTORICAL_ALPHA_CHANGED')
    data=build(); model,initializer=initialize()
    input_audit=audit(data['episodes'])
    baseline_rows=[rollout(CueBaseline(),e) for e in data['episodes']]
    input_audit['cue_only_rollout']={s:summarize([r for r in baseline_rows if r['split']==s]) for s in ('TRAIN','DEV','HELDOUT')}
    write(run/'input-audit.json',input_audit)
    write(run/'dataset.json',data)
    write(run/'initializer.json',initializer); write(run/'features.json',feature_map()[2])
    write(run/'token-manifest.json',token_manifest())
    documents={}; queries=[]
    for entry in registry()['entries']:
        relations=[]
        for field,kind in (('inverse','inverse'),('contrast','contrast'),('dual','contrast')):
            if field in entry: relations.append({'type':kind,'targets':[entry[field]],'authority':'frozen alpha registry'})
        relations.append({'type':'prerequisite_dependency','targets':entry['dependencies'],'authority':'frozen alpha registry'})
        documents[entry['id']]={'candidate_id':entry['id'],'text':'Canonical '+entry['id'].rsplit(':',1)[-1]+': '+canonical(entry).decode(),
                                'relationships':relations,'provenance':['alpha semantic registry','#7/#80/#81']}
    for e in data['episodes']:
        s=initial(e); p=panel(s)
        for c in p['candidates']:
            documents.setdefault(c['candidate_id'],{'candidate_id':c['candidate_id'],'text':_description(c),
                'effect_class':c['effect_class'],'semantic_delta':c['semantic_delta'],
                'relationships':_relationships(c,p['candidates']),'provenance':c['provenance']})
        # Query focus precedes the long world so any truncation is explicit and bounded.
        text='Semantic goal '+canonical(focus(s)).decode()+'; availability '+e['mode']+'; world '+canonical(s['world']).decode()
        queries.append({'query_id':e['episode_id'],'text':text,'split':e['split'],'family':e['family']})
    # Include all offered continuations appearing in TRAIN, without using HELDOUT targets.
    for e in data['episodes']:
        if e['split']!='TRAIN': continue
        trace,_=oracle_trace(e)
        for r in trace:
            candidates=r['panel']['candidates']
            for c in candidates:
                documents.setdefault(c['candidate_id'],{'candidate_id':c['candidate_id'],'text':_description(c),
                    'effect_class':c['effect_class'],'semantic_delta':c['semantic_delta'],
                    'relationships':_relationships(c,candidates),'provenance':c['provenance']})
    retrieval_input={'version':VERSION,'documents':list(documents.values()),'queries':queries,
                     'curriculum':[{'block_id':b['block_id'],'text':'Teach '+b['family']+'; prerequisite blocks '+str(b['prerequisites'])} for b in data['blocks']]}
    write(run/'retrieval-input.json',retrieval_input)
    sources={str(p):file_hash(p) for p in sorted(list(Path('bilqis_alpha').glob('*.py'))+list(Path('bilqis_ref').glob('*.py')))}
    manifest={'version':VERSION,'dataset_sha256':digest(data),'retrieval_input_sha256':digest(retrieval_input),
              'input_audit_sha256':file_hash(run/'input-audit.json'),
              'batch_multiset_sha256':BATCHES_SHA256,
              'split_sha256':{s:digest([e for e in data['episodes'] if e['split']==s]) for s in ('TRAIN','DEV','HELDOUT')},
              'source_commit':subprocess.check_output(['git','rev-parse','HEAD'],text=True).strip(),
              'source_files':sources,'historical_checkpoint_sha256':HISTORICAL_SHA,
              'semantic_abi':initializer['semantic_abi'],'initializer':initializer,'config':asdict(model.config),
              'parameter_count':sum(p.numel() for p in model.parameters()),'initial_state_sha256':state_hash(model),
              'optimizer':{'name':'AdamW','learning_rate':.001,'weight_decay':.01},
              'blocks':16,'steps_per_block':96,'batch_size':32,'steps_per_arm':1536,
              'guidance_policy':{'minimum_margin':MIN_MARGIN,'fallback':'lowest prerequisite-eligible block',
                                 'dev_feedback':'integrated treatment advantage; no heldout context'},
              'historically_exposed_domain':True,'independent_sealed_evidence':False,
              'prepared_wall_seconds':time.perf_counter()-start,'peak_process_rss_bytes':resource.getrusage(resource.RUSAGE_SELF).ru_maxrss}
    save_checkpoint(run/'initial.pt',model,initializer,{'epoch':VERSION,'dataset_sha256':digest(data)})
    manifest['initial_checkpoint_sha256']=file_hash(run/'initial.pt')
    write(run/'manifest.json',manifest)
    print(json.dumps({'prepared':str(run),'episodes':dict(Counter(e['split'] for e in data['episodes'])),
                      'training_rows':len(data['rows']),'parameter_count':manifest['parameter_count']}),flush=True)


def _inputs(run):
    data=read(run/'dataset.json'); manifest=read(run/'manifest.json'); check_frozen(data,manifest)
    if digest(data)!=DATASET_SHA256: raise ValueError('EPOCH_DATASET_DRIFT')
    if file_hash(run/'input-audit.json')!=manifest['input_audit_sha256']: raise ValueError('INPUT_AUDIT_TAMPER')
    if digest(read(run/'retrieval-input.json'))!=manifest['retrieval_input_sha256']: raise ValueError('RETRIEVAL_INPUT_TAMPER')
    if file_hash(HISTORICAL)!=HISTORICAL_SHA: raise ValueError('HISTORICAL_ALPHA_CHANGED')
    for p,h in manifest['source_files'].items():
        if file_hash(p)!=h:
            amendment=run/'replay-source-amendment-01.json'
            if not amendment.exists() or file_hash(p)!=amended_source_hash(p,h,manifest,read(amendment)):
                raise ValueError('SOURCE_DRIFT '+p)
    if file_hash(run/'initial.pt')!=manifest['initial_checkpoint_sha256']: raise ValueError('INITIAL_FILE_TAMPER')
    model,payload=load_checkpoint(run/'initial.pt'); validate_initial(model,payload,manifest)
    return data,manifest


def qualify(run,eg2_python,model_path):
    data,manifest=_inputs(run)
    if not (run/'retrieval.json').exists():
        subprocess.run([eg2_python,'-m','bilqis_alpha.eg2_retrieval','--input',str(run/'retrieval-input.json'),
                        '--output',str(run/'retrieval.json'),'--model',str(model_path)],check=True)
    retrieval=read(run/'retrieval.json')
    if (retrieval['runtime']['executable']!=str(Path(eg2_python).expanduser().absolute())
        or retrieval['model']['path']!=str(model_path.expanduser().resolve())):
        raise ValueError('QUALIFIED_EG2_PATH_BINDING')
    if retrieval['corpus_sha256']!=manifest['retrieval_input_sha256'] or retrieval['model']['backend']!='native MLX':
        raise ValueError('RETRIEVAL_BINDING')
    smoke=read(run/'preflight/eg2-live.json')
    if retrieval['model']['file_sha256']!=smoke['local_file_sha256']:
        raise ValueError('EG2_MODEL_FILE_DRIFT')
    teacher=KevTeacher()
    by_query={r['query_id']:r for r in retrieval['queries']}
    chosen=[]
    for family in ('orientation','scope','binding','evidence','consequence','reserved'):
        chosen.extend([e for e in data['episodes'] if e['split']=='DEV' and e['family']==family][:2])
    traces=[]
    for e in chosen:
        s=initial(e); p=panel(s); legal={c['candidate_id']:c for c in p['candidates']}
        ranked=by_query[e['episode_id']]['rankings']['256']; filtered=filter_retrieval(ranked,legal)
        selected=[legal[r['candidate_id']] for r in filtered['accepted']]
        selected += [c for c in p['candidates'] if c['effect_class'] in RESERVED and c not in selected]
        gold=target(s,p)
        row={'episode_id':e['episode_id'],'split':'DEV','family':e['family'],'panel':p,
             'retrieval':{'rankings':ranked,**filtered,'recall':gold in {r['candidate_id'] for r in ranked},
                          'selected_top_legal':filtered['accepted'][0]['candidate_id'] if filtered['accepted'] else None},
             'oracle_candidate_id':gold}
        for name,options in [('direct',p['candidates']),('hybrid',selected)]:
            trace=teacher.score(canonical(render(s)).decode(),'Select the semantic continuation matching the canonical current goal; preserve unresolved distinctions.',
                                [{'candidate_id':c['candidate_id'],'description':_description(c)} for c in options],
                                {'epoch':VERSION,'episode_id':e['episode_id'],'panel_id':p['panel_id'],'profile':name})
            row[name]=trace
            if trace['status']!='ERROR':
                apply(s,p,trace['choice'])
                trace['correct']=trace['choice']==gold
        hybrid_choice=next((c for c in p['candidates'] if c['candidate_id']==row['hybrid'].get('choice')),None)
        needs_fallback=row['hybrid']['status']!='OK' or hybrid_choice is None or hybrid_choice['effect_class'] in RESERVED
        fallback_choice=row['direct'].get('choice') if row['direct']['status']=='OK' else next(c['candidate_id'] for c in p['candidates'] if c['effect_class']=='abstain')
        if needs_fallback: apply(s,p,fallback_choice)
        row['fallback']={'used':needs_fallback,'choice':fallback_choice if needs_fallback else None,
                         'correct':fallback_choice==gold if needs_fallback else None,
                         'attribution':'complete legal panel uses separately recorded direct Kev decision, or explicit abstention; never changes retrieval recall'}
        traces.append(row)
    result={'version':VERSION,'dataset_sha256':manifest['dataset_sha256'],'retrieval_sha256':file_hash(run/'retrieval.json'),
            'eg2_runtime':retrieval['runtime'],'eg2_model':retrieval['model'],
            'kev_runtime':teacher.identity,'traces':traces,'attempted_scores':len(traces)*2,
            'calls':sum(r[k]['choice_calls'] for r in traces for k in ('direct','hybrid')),
            'correct':{k:sum(r[k].get('correct',False) for r in traces) for k in ('direct','hybrid')},
            'retrieval_recall':sum(r['retrieval']['recall'] for r in traces),
            'errors':sum(r[k]['status']=='ERROR' for r in traces for k in ('direct','hybrid')),
            'wall_seconds':sum(r[k]['wall_seconds'] for r in traces for k in ('direct','hybrid'))}
    if not any(r['direct']['status']!='ERROR' and r['hybrid']['status']!='ERROR' for r in traces):
        result['disposition']='HYBRID_ENGINE_BLOCKED'
    else: result['disposition']='ENGINES_VERIFIED'
    write(run/'qualification.json',result)
    print(json.dumps({k:result[k] for k in ('disposition','calls','correct','retrieval_recall','errors','wall_seconds')}),flush=True)


def _dev(model,episodes):
    return summarize([rollout(model,e) for e in episodes if e['split']=='DEV'])


def train_pair(run):
    data,manifest=_inputs(run); qualification,retrieval=qualified_inputs(run,manifest)
    teacher=KevTeacher()
    docs=[{'candidate_id':r['candidate_id'],'vector':r['vector_256']} for r in retrieval['documents']]
    neighborhoods={b['block_id']:rank(b['vector_256'],docs) for b in retrieval['curriculum']}
    write(run/'training-start.json',{'version':VERSION,'dataset_sha256':manifest['dataset_sha256'],
                                    'policy':'exactly one pair; no tuning after endpoints'})
    initial_model,initializer=load_checkpoint(run/'initial.pt'); initial_hash=state_hash(initial_model)
    results={}; dev_episodes=[e for e in data['episodes'] if e['split']=='DEV']
    for arm in ('fixed','guided'):
        model,payload=load_checkpoint(run/'initial.pt')
        if state_hash(model)!=initial_hash: raise ValueError('INITIAL_STATE_MISMATCH')
        optimizer=torch.optim.AdamW(model.parameters(),lr=.001,weight_decay=.01)
        order=[]; trajectory=[]; decisions=[]; total_tokens=0; started=time.perf_counter(); cpu=time.process_time()
        train_seconds=0.; dev_seconds=0.; checkpoint_seconds=0.
        dev_started=time.perf_counter(); competence=_dev(model,dev_episodes); dev_seconds+=time.perf_counter()-dev_started
        trajectory.append({'steps':0,'dev':competence})
        while len(order)<16:
            allowed=eligible(data['blocks'],order); chosen=allowed[0]
            if arm=='guided':
                context={'completed_blocks':order,'dev_competence':competence,'eligible_blocks':allowed,
                         'cached_eg2_neighbors':{b:[dict(n,description=next(d['text'] for d in retrieval['documents'] if d['candidate_id']==n['candidate_id']),
                                                        typed_relations=next(d['relationships'] for d in retrieval['documents'] if d['candidate_id']==n['candidate_id']))
                                                     for n in neighborhoods[b]] for b in allowed},
                         'meaning':'EG2 proximity is retrieval, not semantic truth; DEV summaries are nonsealed feedback.'}
                options=[{'candidate_id':b['block_id'],'description':'Teach '+b['family']+' for 96 steps; prerequisites '+str(b['prerequisites'])} for b in data['blocks'] if b['block_id'] in allowed]
                options.append({'candidate_id':'abstain','description':'No confident scheduling preference; deterministic fallback.'})
                trace=teacher.score(canonical(context).decode(),'Which eligible curriculum block best addresses the measured DEV weaknesses? Choose only an eligible block or abstain.',options,
                                    {'epoch':VERSION,'completed':order.copy(),'dataset_sha256':manifest['dataset_sha256']})
                accepted=trace['status']=='OK' and trace.get('choice') in allowed
                if accepted: chosen=trace['choice']
                trace.update({'eligible':allowed,'accepted':accepted,'fallback':not accepted,'executed_block':chosen,
                              'meaningful_alternative':len(allowed)>1})
                decisions.append(trace)
            block=next(b for b in data['blocks'] if b['block_id']==chosen)
            block_start=time.perf_counter(); last_loss=None
            model.train()
            for indices in block['batches']:
                rows=[data['rows'][i] for i in indices]
                tensors=pack(rows)
                gold=torch.tensor([r['candidate_ids'].index(r['gold_id']) for r in rows])
                optimizer.zero_grad(set_to_none=True)
                logits=model(*tensors); loss=F.cross_entropy(logits,gold)
                if not bool(torch.isfinite(loss)): raise ValueError('NONFINITE_LOSS')
                loss.backward(); optimizer.step(); last_loss=float(loss.detach())
                total_tokens+=sum(len(r['state_tokens'])+sum(len(c) for c in r['candidate_tokens']) for r in rows)
            train_seconds+=time.perf_counter()-block_start
            order.append(chosen)
            dev_started=time.perf_counter(); competence=_dev(model,dev_episodes); dev_seconds+=time.perf_counter()-dev_started
            trajectory.append({'steps':len(order)*96,'completed_block':chosen,'loss':last_loss,'dev':competence})
            checkpoint_start=time.perf_counter()
            save_checkpoint(run/f'{arm}-step-{len(order)*96:04d}.pt',model,payload['initializer'],
                            {'epoch':VERSION,'arm':arm,'order':order,'dataset_sha256':manifest['dataset_sha256']},optimizer=optimizer)
            checkpoint_seconds+=time.perf_counter()-checkpoint_start
            write(run/f'{arm}-block-{len(order):02d}.json',{'trajectory':trajectory[-1],
                                                         'decision':decisions[-1] if decisions else None})
            print(f'{arm}: {len(order)*96}/1536, block={chosen}, DEV paths={competence["path_correct"]}/{competence["cases"]}',flush=True)
        final=run/f'{arm}.pt'
        save_checkpoint(final,model,payload['initializer'],{'epoch':VERSION,'arm':arm,'order':order,'dataset_sha256':manifest['dataset_sha256']},optimizer=optimizer)
        if state_hash(model)==initial_hash: raise ValueError('NO_LEARNING_UPDATE')
        results[arm]={'order':order,'initial_state_sha256':initial_hash,'final_state_sha256':state_hash(model),
                      'checkpoint_sha256':file_hash(final),'exposures':exposure_identity(data['blocks'],order),
                      'nonpadding_tokens':total_tokens,'trajectory':trajectory,'decisions':decisions,
                      'resource':{'wall_seconds':time.perf_counter()-started,'cpu_seconds':time.process_time()-cpu,
                                  'optimizer_seconds':train_seconds,'dev_seconds':dev_seconds,'checkpoint_seconds':checkpoint_seconds,
                                  'peak_process_rss_bytes':resource.getrusage(resource.RUSAGE_SELF).ru_maxrss}}
        write(run/f'{arm}-training.json',results[arm])
    if results['fixed']['exposures']!=results['guided']['exposures'] or results['fixed']['nonpadding_tokens']!=results['guided']['nonpadding_tokens']:
        raise ValueError('EXPOSURE_MISMATCH')
    accepted=sum(d['accepted'] for d in results['guided']['decisions'])
    meaningful=sum(d['accepted'] and d['meaningful_alternative'] for d in results['guided']['decisions'])
    identifiable=results['fixed']['order']!=results['guided']['order'] and meaningful>0
    write(run/'paired-training.json',{'version':VERSION,'dataset_sha256':manifest['dataset_sha256'],
                                     'arms':results,'accepted_kev_decisions':accepted,
                                     'accepted_with_alternatives':meaningful,'fallbacks':16-accepted,'identifiable':identifiable,
                                     'guidance_dev_advantage':'explicit nonsealed DEV feedback only in treatment scheduling'})


def evaluate_pair(run):
    data,manifest=_inputs(run); paired=read(run/'paired-training.json'); start=time.perf_counter()
    qualification,retrieval=qualified_inputs(run,manifest)
    results={}; summaries={}
    for arm in ('fixed','guided'):
        model,payload=verified_arm(run,paired,arm,manifest)
        results[arm]=[rollout(model,e) for e in data['episodes']]
        summaries[arm]={split:summarize([r for r in results[arm] if r['split']==split]) for split in ('TRAIN','DEV','HELDOUT')}
    a=summaries['fixed']['HELDOUT']['path_correct']; b=summaries['guided']['HELDOUT']['path_correct']
    disposition='GUIDANCE_NOT_IDENTIFIABLE' if not paired['identifiable'] else 'HYBRID_PILOT_NULL_OR_REVERSAL' if b<=a else 'HYBRID_PILOT_REPRODUCED'
    by_query={q['query_id']:q for q in retrieval['queries']}
    retrieval_rows=[]
    for e in data['episodes']:
        s=initial(e); p=panel(s); gold=target(s,p); q=by_query[e['episode_id']]
        legal={c['candidate_id'] for c in p['candidates']}
        row={'episode_id':e['episode_id'],'split':e['split'],'family':e['family'],'gold':gold}
        for dim in ('256','768'):
            ranked=q['rankings'][dim]; filtered=filter_retrieval(ranked,legal)
            documents=[{'candidate_id':d['candidate_id'],'vector':d['vector_'+dim]} for d in retrieval['documents']]
            negatives=[c['candidate_id'] for c in p['candidates'] if c['effect_class'] not in RESERVED and c['candidate_id']!=gold]
            row[dim]={'recall':gold in {r['candidate_id'] for r in ranked},'raw_rankings':ranked,**filtered,
                      'hard_negative_definition':'offered structurally legal substantive alternatives mismatching independent oracle target',
                      'hard_negative_separation':hard_negative_separation(q['vector_'+dim],documents,gold,negatives),
                      'top_legal_correct':bool(filtered['accepted']) and filtered['accepted'][0]['candidate_id']==gold}
        retrieval_rows.append(row)
    result={'version':VERSION,'disposition':disposition,'primary_endpoint':'exact heldout semantic path without teacher forcing',
            'prefrozen_input_audit':read(run/'input-audit.json'),
            'dataset_sha256':manifest['dataset_sha256'],'heldout_delta_paths':b-a,'summaries':summaries,'rows':results,
            'retrieval_rows':retrieval_rows,'evaluation_wall_seconds':time.perf_counter()-start,
            'peak_process_rss_bytes':resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,
            'neural_replay_tolerance':{'atol':1e-6,'rtol':0},'historical_model':'separate four-class alpha; not a matched arm'}
    write(run/'evaluation.json',result)
    write(run/'evaluation-binding.json',{'evaluation_sha256':file_hash(run/'evaluation.json'),
                                        'paired_training_sha256':file_hash(run/'paired-training.json'),
                                        'qualification_sha256':file_hash(run/'qualification.json')})
    print(json.dumps({'disposition':disposition,'heldout':{k:summaries[k]['HELDOUT'] for k in summaries}}),flush=True)


def replay(run,live=False):
    data,manifest=_inputs(run); receipt=read(run/'evaluation.json'); paired=read(run/'paired-training.json')
    bindings=read(run/'evaluation-binding.json')
    for name in ('evaluation','paired-training','qualification'):
        if file_hash(run/(name+'.json'))!=bindings[name.replace('-','_')+'_sha256']:
            raise ValueError('REPLAY_RECEIPT_TAMPER '+name)
    chosen=[]; episodes={e['episode_id']:e for e in data['episodes']}
    # Frozen deterministic selection includes successes, failures, reserved states,
    # each mandatory family and observed wrong-intermediate/right-terminal cases.
    for family in ('orientation','scope','binding','evidence','consequence','reserved'):
        chosen.extend([e['episode_id'] for e in data['episodes'] if e['split']=='HELDOUT' and e['family']==family][:1])
    for arm in ('fixed','guided'):
        for condition in ('path_correct','wrong_intermediate_right_terminal'):
            selected=next((r['episode_id'] for r in receipt['rows'][arm] if r[condition]),None)
            if selected: chosen.append(selected)
        selected=next((r['episode_id'] for r in receipt['rows'][arm] if not r['path_correct']),None)
        if selected: chosen.append(selected)
    chosen+= [e['episode_id'] for e in data['episodes'] if e['mode'] in ('ambiguous','missing','unsupported','outside')][:4]
    qualification,retrieval=qualified_inputs(run,manifest)
    chosen += [r['episode_id'] for r in qualification['traces']]
    chosen=list(dict.fromkeys(chosen)); output={'version':VERSION,'historical_checkpoint_sha256':HISTORICAL_SHA,
        'new_model_checkpoint_sha256':{a:paired['arms'][a]['checkpoint_sha256'] for a in ('fixed','guided')},
        'external_trace_provenance':'genuinely recorded native EG2/Kev; archived defaults','cases':[]}
    amendment=run/'replay-source-amendment-01.json'
    if amendment.exists(): output['replay_source_amendment']=read(amendment)
    teacher=KevTeacher() if live else None
    for arm in ('fixed','guided'):
        model,_=verified_arm(run,paired,arm,manifest)
        for identity in chosen:
            actual=rollout(model,episodes[identity]); saved=next(r for r in receipt['rows'][arm] if r['episode_id']==identity)
            compare_neural_replay(actual,saved)
            external=next((r for r in qualification['traces'] if r['episode_id']==identity),None)
            neighbors=next(q for q in retrieval['queries'] if q['query_id']==identity)
            output['cases'].append({'arm':arm,'live_neural':actual,'eg2_neighborhood':neighbors['rankings'],
                                    'kev_archived':external,'kev_missing':external is None})
    if live:
        comparisons=[]
        for row in qualification['traces'][:3]:
            original=row['direct']; request=archived_request(original)
            observed=teacher.score(request['state'],request['questions']['decision']['instructions'],
                                   [{'candidate_id':k,'description':v} for k,v in request['questions']['decision']['criteria'].items()],original['binding'])
            if observed['request_sha256']!=original['request_sha256']: raise ValueError('LIVE_REQUEST_BYTES_DRIFT')
            comparisons.append({'episode_id':row['episode_id'],'archived':original,'live':observed,
                                'same_choice':observed.get('choice')==original.get('choice')})
        output['live_kev_comparisons']=comparisons
        # Replay native EG2 with identical frozen texts; separate file, no cache rewrite.
        live_directory=run/'live-replays'/str(uuid4())
        live_path=live_directory/'retrieval.json'
        subprocess.run(eg2_command(retrieval,run/'retrieval-input.json',live_path),check=True)
        current=read(live_path)
        validate_eg2_replay(current,retrieval)
        if [q['query_id'] for q in current['queries']]!=[q['query_id'] for q in retrieval['queries']]:
            raise ValueError('EG2_QUERY_DRIFT')
        same=sum(a['rankings']==b['rankings'] for a,b in zip(current['queries'],retrieval['queries']))
        output['live_eg2_comparison']={'exact_rankings_matching':same,'queries':len(retrieval['queries']),
                                      'current_receipt':str(live_path)}
    path=live_directory/'replay.json' if live else run/'replay.json'
    if not path.exists(): write(path,output)
    print(json.dumps({'replayed_neural_cases':len(output['cases']),'showcase_ids':len(chosen),'live':live,
                      'disposition':receipt['disposition'],'receipt':str(path)}),flush=True)


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('phase',choices=('prepare','qualify','train-pair','evaluate','replay'))
    parser.add_argument('--run',type=Path,default=DEFAULT_RUN)
    parser.add_argument('--eg2-python',default=EG2_PYTHON)
    parser.add_argument('--eg2-model',type=Path,default=EG2_MODEL)
    parser.add_argument('--live',action='store_true')
    args=parser.parse_args(); args.run.mkdir(parents=True,exist_ok=True)
    functions={'prepare':lambda:prepare(args.run),'qualify':lambda:qualify(args.run,args.eg2_python,args.eg2_model),
               'train-pair':lambda:train_pair(args.run),'evaluate':lambda:evaluate_pair(args.run),'replay':lambda:replay(args.run,args.live)}
    functions[args.phase]()


if __name__=='__main__': main()
