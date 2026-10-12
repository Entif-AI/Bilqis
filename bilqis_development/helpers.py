"""Run the reused native EG2 encoder and Kev pointer API in upstream preparation."""
from __future__ import annotations

import argparse
import importlib.metadata
import json
from pathlib import Path
import platform
import resource
import sys
import time

from bilqis_logic.kernel import canonical,digest
from .registry import candidates,admit,SOURCES
from .vendor import eg2_retrieval as eg2
from .vendor.kev_teacher import KevTeacher

ROOT=Path(__file__).resolve().parents[1]
EXPECTED_MODEL='ffaf2604b011ad0634022529bac930a4f6a2feba22687d8d5890434d186b459c'
EXPECTED_LOADER='be41d5142d63888bf288b53d4443b7762f7e052801f1616a60d317ff60e3761e'


def produce(out,model_path):
    out.mkdir(parents=True,exist_ok=False)
    started=time.perf_counter();cpu=time.process_time()
    registry=candidates();by_id={r['candidate_id']:r for r in registry}
    source_hashes={k:eg2._sha256(ROOT/'docs/u5-u6/sources'/f'{k}.json') for k in SOURCES}
    for k in SOURCES:
        snapshot=json.loads((ROOT/'docs/u5-u6/sources'/f'{k}.json').read_text())
        if snapshot['number']!=int(k) or snapshot['url']!=SOURCES[k]:raise ValueError('source locator mismatch')
    with (out/'started.json').open('xb') as f:
        f.write(canonical({'sources':source_hashes,'registry_sha256':digest(registry),'pid':__import__('os').getpid()})+b'\n')
    import mlx.core as mx
    from mlx_vlm import embedding_loader
    from mlx_vlm.embedding_loader import load_embedding_model
    from transformers import AutoTokenizer
    files=eg2._model_hashes(model_path)
    if files.get('model.safetensors')!=EXPECTED_MODEL or eg2._sha256(Path(embedding_loader.__file__))!=EXPECTED_LOADER:
        raise ValueError('existing EG2 runtime/model identity changed')
    teacher=KevTeacher()
    model=load_embedding_model(model_path)
    tokenizer=AutoTokenizer.from_pretrained(model_path,local_files_only=True)
    prefixes=json.loads((model_path/'config_sentence_transformers.json').read_text())['prompts']
    doc_prefix=prefixes.get('document',prefixes.get('doc',eg2.DOCUMENT_PREFIX_DEFAULT))
    query_prefix=prefixes.get('query',eg2.QUERY_PREFIX_DEFAULT)
    loaded=time.perf_counter()
    texts=[f"{r['source_locator']} | {r['scope']} | {','.join(r['operations'])} | {r['description']}" for r in registry]
    vectors,doc_tokens,doc_truncated=eg2._encode(model,tokenizer,mx,texts,doc_prefix,8)
    documents=[dict(r,text=t,vector_768=v,vector_256=eg2.project(v)) for r,t,v in zip(registry,texts,vectors)]
    state=[];decisions=[];query_tokens=0;query_truncated=0;encoding_seconds=time.perf_counter()-loaded
    # Fixed bounded focal needs, not repeated attempts to solicit an accepted answer.
    for index,focus in enumerate(registry[:20]):
        before=list(state)
        text=(f"{focus['source_locator']} | focus {focus['scope']}: {focus['description']} "
              f"Established constructions: {','.join(state[-3:]) or 'Boolean logic, ordered roles, finite entailment, evidence polarity'}. "
              'Retrieve typed prerequisites, inverse, contrasts and compositions for new tiny exercises.')
        t=time.perf_counter();q,nt,cut=eg2._encode(model,tokenizer,mx,[text],query_prefix,8)
        encoding_seconds+=time.perf_counter()-t;query_tokens+=nt;query_truncated+=cut
        if len(q[0])!=768:raise ValueError('native 768-dimensional reference required')
        rankings={str(n):eg2.rank(q[0] if n==768 else eg2.project(q[0]),
                   [{'candidate_id':r['candidate_id'],'vector':r[f'vector_{n}']} for r in documents],top_k=len(documents)) for n in (768,256)}
        retrieved=[r['candidate_id'] for r in rankings['768'][:8]]
        panel_ids=retrieved[:4]
        hard=('collapse-provenance-supersession' if focus['scope'] in ('lineage','revision','state','types') else 'collapse-report-truth')
        if focus['source']=='84' and hard not in panel_ids:panel_ids.append(hard)
        panel=[{'candidate_id':i,'description':by_id[i]['description']+' Scope: '+by_id[i]['scope']+'.'} for i in panel_ids]
        panel.append({'candidate_id':'needs-review','description':'Abstain: none of these constructions has adequate source, type or scope support; needs review.'})
        rotate=index%len(panel);panel=panel[rotate:]+panel[:rotate]
        context={'source':focus['source_locator'],'source_scope':focus['scope'],'focus':focus['description'],
                 'established_primitives':['Boolean connectives','ordered entity roles','finite set/typed mapping definitions','Horn-rule entailment','independent evidence polarities'],
                 'semantic_state':state,'eg2_neighborhood':[{'id':i,'description':by_id[i]['description'],'relation':by_id[i]['relation']} for i in retrieved],
                 'authority':'Only deterministic source/type/formal validation can admit a proposal. Cosine and probabilities are not truth.'}
        trace=teacher.score(json.dumps(context,sort_keys=True),
             'Choose the source-supported typed construction that best advances this semantic focus, discriminating its scope, inverse or contrast. Select needs-review if none applies.',
             panel,binding={'revision':len(state),'state_sha256':digest(state),'focus':focus['candidate_id']})
        chosen=trace.get('choice')
        if trace['status']=='ERROR':disposition={'disposition':'deferred','reason':'native helper error','candidate_id':chosen}
        elif chosen=='needs-review':disposition={'disposition':'deferred','reason':'genuine helper abstention','candidate_id':chosen}
        else:disposition=admit(by_id[chosen],retrieved,state,focus['scope'])
        # This proposal-only run uses formal validation, not the prior scheduler's
        # confidence/margin acceptance gate. Complete low-margin evidence remains.
        if disposition['disposition']=='accepted':state.append(chosen)
        decision={'decision_id':f'D{index:02d}','focus':focus['candidate_id'],'scope':focus['scope'],
                  'source_locator':focus['source_locator'],'source_sha256':source_hashes[focus['source']],
                  'query':text,'query_vector_768':q[0],'query_vector_256':eg2.project(q[0]),
                  'rankings':rankings,'selected_profile':768,'retrieved_ids':retrieved,'panel':panel,'kev':trace,
                  'validator':disposition,'state_before':before,'state_after':list(state),
                  'target_recall':{n:focus['candidate_id'] in [r['candidate_id'] for r in rows[:8]] for n,rows in rankings.items()},
                  'missing_ids':[r['candidate_id'] for r in registry if r['candidate_id'] not in retrieved],
                  'unoffered_ids':[i for i in retrieved if i not in panel_ids],
                  'hard_alternatives':[hard] if focus['source']=='84' else [],
                  'rejected_neighborhood':[{'id':i,'reason':'outside focal scope'} for i in retrieved if by_id[i]['scope']!=focus['scope']],
                  'untruncated_query_tokens':len(tokenizer(query_prefix+text,truncation=False)['input_ids']),
                  'fresh_query_after_state_change':True}
        decisions.append(decision)
        with (out/f'{index:02d}.json').open('xb') as f:f.write(canonical(decision)+b'\n')
        print(json.dumps({'helper_step':index,'focus':focus['candidate_id'],'choice':chosen,'disposition':disposition['disposition']}),flush=True)
    runtime={'eg2':{'name':eg2.MODEL_NAME,'path':str(model_path),'file_sha256':files,'backend':'native MLX',
               'loader_sha256':EXPECTED_LOADER,'direct_url':eg2._direct_url(),'mlx':importlib.metadata.version('mlx'),
               'mlx_vlm':importlib.metadata.version('mlx-vlm'),'executable':sys.executable,'python':sys.version},
             'kev':teacher.identity,'kev_source_commit':'6b719c3c3f367295f6ef336f4f751cf5ff970abc',
             'adapter_origin':{'pr':106,'sha':'6df36efacd6a5ad664c52b663bc14e9319bfb17a',
               'files':{p.name:eg2._sha256(p) for p in (ROOT/'bilqis_development/vendor').glob('*.py')}},
             'projection_profile':{'selected':768,'reason':'prior measured top-8 recall 167/196 at 768 vs 155/196 at 256; full native vectors preserved'},
             'formal_88_qualification':False,'use':'exploratory proposal-only; independent formal admission'}
    resources={'wall_seconds':time.perf_counter()-started,'cpu_seconds':time.process_time()-cpu,'load_seconds':loaded-started,
               'encoding_seconds':encoding_seconds,'kev_wall_seconds':sum(d['kev']['wall_seconds'] for d in decisions),
               'eg2_documents':len(documents),'eg2_queries':len(decisions),'kev_choice_calls':sum(d['kev']['choice_calls'] for d in decisions),
               'token_counts':{'documents':doc_tokens,'queries':query_tokens,
                   'kev_input':sum(d['kev'].get('usage',{}).get('input_tokens',0) for d in decisions),
                   'kev_output_accounting':sum(d['kev'].get('usage',{}).get('output_tokens',0) for d in decisions)},
               'truncation':{'max_length':256,'documents':doc_truncated,'queries':query_truncated},
               'rss_max_bytes':resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,'mlx_peak_memory_bytes':mx.get_peak_memory(),
               'external_spend':0,'student_training_resources_included':False}
    result={'version':'helper-semantic-production-0.1.0','sources':source_hashes,'registry':registry,'documents':documents,
            'decisions':decisions,'accepted':state,'runtime':runtime,'resources':resources,
            'policy':'No retries to seek acceptance; scores never become gold or student geometry.'}
    with (out/'helpers.json').open('xb') as f:f.write(canonical(result)+b'\n')
    return {'accepted':state,'resources':resources}


def main():
    p=argparse.ArgumentParser();p.add_argument('--out',type=Path,required=True);p.add_argument('--model',type=Path,required=True)
    a=p.parse_args();print(json.dumps(produce(a.out,a.model),indent=2),flush=True)


if __name__=='__main__':main()
