"""Execute #77 with the existing native #65 Kev adapter and replay its evidence."""
from __future__ import annotations
import argparse
import copy
import hashlib
import json
import math
import statistics
import time
from pathlib import Path
from .decision import kev_score, permute
from .ithkuil_fixture import CONTEXT_SHA256, DIFFICULTIES, compile_issue, decisions, validate_fixture
from .local_http import local_json
from .semantics import digest

FAMILIES = {1:'English → New Ithkuil',2:'New Ithkuil → English',3:'Root / stem recovery',
            4:'Semantic roles',5:'Grammatical features',6:'Morpheme / form selection',
            7:'Near-miss diagnosis',8:'Minimal-pair discrimination',9:'Semantic equivalence',
            10:'Sequential reconstruction',11:'Complete-expression validation',12:'Insufficient / clarify'}


def file_hash(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def service_identity(model):
    keys=('name','run','base','lora','backend','device','dtype','temperature','max_state_tokens','truncate_states')
    value={k:model[k] for k in keys}
    value['prefix_cache_settings']={k:model['prefix_cache'][k] for k in ('size','min_state_tokens','max_tokens')}
    return value


def validate_rows(fixture, rows):
    validate_fixture(fixture)
    expected={d['id']:d for _,d in decisions(fixture)}
    ids=[r['decision_id'] for r in rows]
    if len(ids)!=len(expected) or set(ids)!=set(expected):raise ValueError('ITHKUIL_RESULT_COVERAGE')
    identity=rows[0]['runtime_identity']
    if identity.get('model')!='jaredpalmer/kev-4b' or not identity.get('model_revision'):raise ValueError('ITHKUIL_RUNTIME_IDENTITY')
    for row in rows:
        d=expected[row['decision_id']];options={o['id']:o['description'] for o in d['candidates']}
        p=row['probabilities'];order=row['candidate_order']
        if row['context_packet_sha256']!=CONTEXT_SHA256:raise ValueError('ITHKUIL_RESULT_CONTEXT')
        if row['runtime_identity']!=identity:raise ValueError('ITHKUIL_RUNTIME_CHANGED')
        if row['question']!=d['prompt'] or row['gold_id']!=d['gold_candidate']:raise ValueError('ITHKUIL_RESULT_PROMPT_GOLD')
        if {o['id']:o['description'] for o in row['candidates']}!=options or len(order)!=4 or set(order)!=set(options) or [o['id'] for o in row['candidates']]!=order:raise ValueError('ITHKUIL_RESULT_CANDIDATES')
        if set(p)!=set(options) or any(type(v) not in (float,int) or not math.isfinite(v) or not 0<=v<=1 for v in p.values()):raise ValueError('ITHKUIL_RESULT_PROBABILITIES')
        if abs(sum(p.values())-1)>.000201:raise ValueError('ITHKUIL_RESULT_PROBABILITY_SUM')
        if row['selected_id'] not in p or p[row['selected_id']]+1e-6<max(p.values()):raise ValueError('ITHKUIL_RESULT_SELECTION')
        if not math.isfinite(row['latency_ms']) or row['latency_ms']<0:raise ValueError('ITHKUIL_RESULT_LATENCY')
        if 'correct' in row and row['correct']!=(row['selected_id']==row['gold_id']):raise ValueError('ITHKUIL_RESULT_CORRECTNESS')


def count(values):
    values=list(values);return {'correct':sum(bool(v) for v in values),'total':len(values)}


def cell_results(fixture, rows):
    by_id={r['decision_id']:r for r in rows};result=[]
    for cell in fixture['cells']:
        atomic=[by_id[d['id']] for d in cell.get('steps',[cell])]
        correct=all(r['selected_id']==r['gold_id'] for r in atomic)
        if cell['family']==10 and cell['difficulty']=='SIMPLE':
            descriptions=[next(o['description'] for o in r['candidates'] if o['id']==r['selected_id']) for r in atomic]
            config,affiliation=descriptions
            ca={'DPX':'s','DSS':'c','DSC':'ks','DDS':'ţs'}
            af={'CSL':'null','ASO':'l','COA':'r','VAR':'ř'}
            selected=f'{affiliation}(-{af[affiliation]}-) + {config}(-{ca[config]}-)'
            final_correct=selected==cell['gold_answer']
        else:
            selected=next(o['description'] for o in atomic[-1]['candidates'] if o['id']==atomic[-1]['selected_id'])
            final_correct=atomic[-1]['selected_id']==atomic[-1]['gold_id']
        top=[max(r['probabilities'].values()) for r in atomic]
        margins=[sorted(r['probabilities'].values(),reverse=True)[0]-sorted(r['probabilities'].values(),reverse=True)[1] for r in atomic]
        result.append({'cell_id':cell['id'],'family':cell['family'],'difficulty':cell['difficulty'],
                       'correct':correct,'final_correct':final_correct,'selected_description':selected,
                       'selected_path':[r['selected_id'] for r in atomic],
                       'top_probability_min':min(top),'margin_min':min(margins),
                       'latency_ms':sum(r['latency_ms'] for r in atomic),
                       'wrong_path_right_final':len(atomic)>1 and not correct and final_correct})
    return result


def summarize(fixture, rows, wall_seconds=None):
    validate_rows(fixture,rows);cells=cell_results(fixture,rows);by_cell={c['cell_id']:c for c in cells}
    dimensions=sorted({d for c in fixture['cells'] for d in c['semantic_dimensions']})
    sequential=[c for c in cells if c['family']==10]
    steps=[r for r in rows if r['cell_id'].startswith('F10-')]
    latency=[r['latency_ms'] for r in rows]
    return {'canonical':count(c['correct'] for c in cells),
            'atomic':count(r['selected_id']==r['gold_id'] for r in rows),
            'difficulty':{d:count(c['correct'] for c in cells if c['difficulty']==d) for d in DIFFICULTIES},
            'families':{str(f):count(c['correct'] for c in cells if c['family']==f) for f in FAMILIES},
            'dimensions':{d:count(by_cell[c['id']]['correct'] for c in fixture['cells'] if d in c['semantic_dimensions']) for d in dimensions},
            'sequential':{'atomic':count(r['selected_id']==r['gold_id'] for r in steps),
                          'final':count(c['final_correct'] for c in sequential),
                          'joint':count(c['correct'] for c in sequential),
                          'wrong_path_right_final':[c['cell_id'] for c in sequential if c['wrong_path_right_final']]},
            'whole_expression':{'English_to_New_Ithkuil':count(c['correct'] for c in cells if c['cell_id']=='F01-HARD'),
                                'New_Ithkuil_to_English':count(c['correct'] for c in cells if c['cell_id']=='F02-HARD'),
                                'validation':count(c['correct'] for c in cells if c['family']==11)},
            'atomic_vs_compositional':{'source_exact':count(by_cell[c['id']]['correct'] for c in fixture['cells'] if c['classification']=='source-exact'),
                                       'source_derived':count(by_cell[c['id']]['correct'] for c in fixture['cells'] if c['classification']=='source-derived'),
                                       'controlled_mutation':count(by_cell[c['id']]['correct'] for c in fixture['cells'] if c['classification']=='controlled-mutation')},
            'latency':{'mean_ms':statistics.mean(latency),'median_ms':statistics.median(latency),'min_ms':min(latency),'max_ms':max(latency),
                       'total_decision_seconds':sum(latency)/1000,'decision_throughput_per_second':len(rows)/(sum(latency)/1000),
                       'epoch_wall_seconds':wall_seconds,'epoch_throughput_per_second':len(rows)/wall_seconds if wall_seconds else None,
                       'warm_decisions':sum(r.get('warm_state') is True for r in rows)},
            'cells':cells,'invalid_fixture_cells':[]}


def compare_orders(fixture, a, b):
    validate_rows(fixture,a);validate_rows(fixture,b);bmap={r['decision_id']:r for r in b};comparisons=[]
    for first in a:
        second=bmap[first['decision_id']]
        for key in ('question','gold_id','context_packet_sha256','runtime_identity','sequence_context','state_sha256'):
            if first[key]!=second[key]:raise ValueError('ITHKUIL_PERMUTATION_CHANGED_'+key)
        if {o['id']:o['description'] for o in first['candidates']}!={o['id']:o['description'] for o in second['candidates']}:raise ValueError('ITHKUIL_PERMUTATION_CONTENT')
        if first['candidate_order']==second['candidate_order']:raise ValueError('ITHKUIL_PERMUTATION_UNCHANGED_ORDER')
        movements={k:second['probabilities'][k]-v for k,v in first['probabilities'].items()}
        comparisons.append({'decision_id':first['decision_id'],'cell_id':first['cell_id'],
                            'choice_stable':first['selected_id']==second['selected_id'],
                            'correctness_stable':(first['selected_id']==first['gold_id'])==(second['selected_id']==second['gold_id']),
                            'probability_delta':movements,'gold_probability_delta':movements[first['gold_id']],
                            'total_variation_distance':sum(abs(v) for v in movements.values())/2})
    return {'seed':fixture['permutation_seed'],'atomic_unchanged':sum(r['choice_stable'] for r in comparisons),
            'atomic_changed':sum(not r['choice_stable'] for r in comparisons),
            'correctness_changed':sum(not r['correctness_stable'] for r in comparisons),
            'canonical_unchanged':sum(all(r['choice_stable'] for r in comparisons if r['cell_id']==c['id']) for c in fixture['cells']),
            'order_sensitive_cells':sorted({r['cell_id'] for r in comparisons if not r['choice_stable']}),
            'mean_total_variation_distance':statistics.mean(r['total_variation_distance'] for r in comparisons),
            'decisions':comparisons}


def fraction(value):
    return f"{value['correct']} / {value['total']}"


def md(value):
    return str(value).replace('|','\\|').replace('\n','<br>')


def choice_label(row, gold=False):
    identity=row['gold_id'] if gold else row['selected_id']
    return next(o.get('source_candidate_id',o['id']) for o in row['candidates'] if o['id']==identity)


def render_reports(fixture,a,b,review=None):
    sa=summarize(fixture,a);sb=summarize(fixture,b);comparison=compare_orders(fixture,a,b)
    amap={r['decision_id']:r for r in a};bmap={r['decision_id']:r for r in b}
    comp={r['decision_id']:r for r in comparison['decisions']};parents={r['cell_id']:r for r in sa['cells']}
    support={r['cell_id']:r for r in (review or {}).get('cells',[])}
    lines=['# Kev-4B New Ithkuil — frozen v0.1 capability result','',
           f"Canonical order: **{fraction(sa['canonical'])} canonical cells**, **{fraction(sa['atomic'])} atomic decisions**.",
           f"Permuted order: **{fraction(sb['canonical'])} canonical cells**, **{fraction(sb['atomic'])} atomic decisions**.",
           f"Option order changed the choice in **{comparison['atomic_changed']} / 42 decisions** across **{len(comparison['order_sensitive_cells'])} / 36 cells**.",'',
           'This is a capability map of this supplied grammar slice. Gold comes from the frozen human-authored #77 contract. Model scores are evidence, not truth authority. No invalid fixture cells were found.','',
           '[Every failure and unstable decision](FAILURES.md) · [Capability map](CAPABILITY_MAP.md) · [Source verification](SOURCE_VERIFICATION.md)','',
           '## Metrics','', '| Slice | Canonical order | Permuted order |','|---|---|---|']
    for d in DIFFICULTIES:lines.append(f"| {d} | {fraction(sa['difficulty'][d])} | {fraction(sb['difficulty'][d])} |")
    for f,name in FAMILIES.items():lines.append(f"| F{f:02d} — {name} | {fraction(sa['families'][str(f)])} | {fraction(sb['families'][str(f)])} |")
    for dim in sa['dimensions']:lines.append(f"| {dim} (overlapping canonical membership) | {fraction(sa['dimensions'][dim])} | {fraction(sb['dimensions'][dim])} |")
    for key in ('atomic','final','joint'):lines.append(f"| Sequential {key} | {fraction(sa['sequential'][key])} | {fraction(sb['sequential'][key])} |")
    for key in sa['whole_expression']:lines.append(f"| Whole expression — {key} | {fraction(sa['whole_expression'][key])} | {fraction(sb['whole_expression'][key])} |")
    for key in sa['atomic_vs_compositional']:lines.append(f"| {key} | {fraction(sa['atomic_vs_compositional'][key])} | {fraction(sb['atomic_vs_compositional'][key])} |")
    lines+=['','## Every canonical cell','',
            'A/B/C/D are the frozen source candidate labels, not display positions. Sequential parent correctness is joint correctness; parent Top P and Margin are the minima across its steps, and latency is their sum. Atomic step rows sit immediately beneath each parent. Permutation stability means the same candidate identity, irrespective of display position.','',
            '| Cell | Family | Difficulty | Gold | Kev choice | Correct? | Top P | Margin | Permutation stable? | Latency |',
            '|---|---|---|---|---|---|---:|---:|---|---:|']
    for cell in fixture['cells']:
        parent=parents[cell['id']];atomic=[amap[d['id']] for d in cell.get('steps',[cell])]
        stable=all(comp[r['decision_id']]['choice_stable'] for r in atomic)
        gold=' → '.join(choice_label(r,True) for r in atomic);chosen=' → '.join(choice_label(r) for r in atomic)
        link=f"[{cell['id']}](FAILURES.md#{cell['id'].lower()})" if not parent['correct'] or not stable else cell['id']
        lines.append(f"| {link} | F{cell['family']:02d} | {cell['difficulty']} | {gold} | {chosen} | {'✓' if parent['correct'] else '✗'} | {parent['top_probability_min']:.4f} | {parent['margin_min']:.4f} | {'yes' if stable else 'NO'} | {parent['latency_ms']:.1f} ms |")
        if cell['family']==10:
            for row in atomic:
                probs=sorted(row['probabilities'].values(),reverse=True)
                lines.append(f"| ↳ {row['decision_id']} | F10 | step {row['decision_id'].split('.S')[1]} | {choice_label(row,True)} | {choice_label(row)} | {'✓' if row['selected_id']==row['gold_id'] else '✗'} | {probs[0]:.4f} | {probs[0]-probs[1]:.4f} | {'yes' if comp[row['decision_id']]['choice_stable'] else 'NO'} | {row['latency_ms']:.1f} ms |")
    lines+=['','## Execution identity and interpretation limits','',
            'Runtime details: [runtime-identity.json](runtime-identity.json). Full scored rows: [A/rows.jsonl](A/rows.jsonl) and [B/rows.jsonl](B/rows.jsonl). Aggregate replay: [summary.json](summary.json).','',
            'The supplied context packet SHA-256 is `'+CONTEXT_SHA256+'`. It remains byte-identical and outside the public repository; [source-manifest.json](source-manifest.json) identifies its official snapshots.','',
            'F10 canonical steps consume previous choices. For the paired permutation, each atomic decision replays the exact canonical input state, including that preceding path. Thus only candidate order changes. Permuted final/joint metrics score the permuted outputs against the same frozen gold; they do not represent a fresh adaptive sequence with changed preceding inputs. A correct final choice never retroactively repairs a wrong intermediate step.','',
            'The API exposes scores rounded to four decimal places; raw provider vectors are retained without claiming hidden higher precision. The examples recur across families, so 36 cells are not 36 independent linguistic anchors. Dimension totals overlap and diagnose performance on the associated tasks; they do not isolate a causal mechanism.','',
            f"Canonical median/mean POST latency: {sa['latency']['median_ms']:.1f} / {sa['latency']['mean_ms']:.1f} ms; decision throughput {sa['latency']['decision_throughput_per_second']:.3f}/s. Permuted: {sb['latency']['median_ms']:.1f} / {sb['latency']['mean_ms']:.1f} ms; {sb['latency']['decision_throughput_per_second']:.3f}/s. Complete epoch wall throughput is in summary.json. Latency excludes the adapter's identity GET calls.",'']
    failures=['# Every incorrect or unstable Kev decision','',
              'Exact prompts, all original choices, both distributions, and source-based explanations follow. Labels preserve candidate identity; the separately recorded order is what Kev saw.','']
    for cell in fixture['cells']:
        affected=[d for d in cell.get('steps',[cell]) if any(r['selected_id']!=r['gold_id'] for r in (amap[d['id']],bmap[d['id']])) or not comp[d['id']]['choice_stable']]
        if not affected:continue
        failures+=['<a id="'+cell['id'].lower()+'"></a>','## '+cell['id'],'',
                   '**Failure categories:** '+', '.join(cell['semantic_dimensions']+(['order sensitivity'] if any(not comp[d['id']]['choice_stable'] for d in affected) else []))+'.','',
                   '**Source:** '+', '.join('['+l['section']+']('+next(s['url'] for s in (review or {}).get('sources',[]) if s['chapter']==l['chapter'])+')' if (review or {}).get('sources') else l['section'] for l in cell['source_locators'])+'.','',
                   '**Why the gold follows:** '+support.get(cell['id'],{}).get('inference',cell.get('rationale') or 'See the source verification entry for these locators.')+' ('+support.get(cell['id'],{}).get('gold_support',cell['classification'])+').','']
        if cell['family']==10:failures+=['**Sequence target:** '+cell['prompt'],'']
        for d in affected:
            ra,rb=amap[d['id']],bmap[d['id']]
            failures+=['### '+d['id'],'','**Exact prompt**','', '```text',d['prompt'],'```','',
                       '| Candidate | Exact description | P canonical | P permuted |','|---|---|---:|---:|']
            for o in d['candidates']:failures.append(f"| {o['source_candidate_id']} (`{o['id']}`) | {md(o['description'])} | {ra['probabilities'][o['id']]:.4f} | {rb['probabilities'][o['id']]:.4f} |")
            failures+=['',f"**Gold:** {choice_label(ra,True)}. **Kev canonical:** {choice_label(ra)}. **Kev permuted:** {choice_label(rb)}.",
                       '**Canonical order:** '+', '.join(ra['candidate_order'])+'.',
                       '**Permuted order:** '+', '.join(rb['candidate_order'])+'.',
                       f"**Probability movement:** gold ΔP {comp[d['id']]['gold_probability_delta']:+.4f}; total variation distance {comp[d['id']]['total_variation_distance']:.4f}.",'']
            if cell['family']==10:failures+=['**Canonical and paired-permutation input path:**','', '```json',json.dumps(ra['sequence_context'],ensure_ascii=False,indent=2),'```','']
    if len(failures)==4:failures+=['No incorrect or unstable decision occurred in either order.','']
    cap=['# Kev-4B capability map','',
         f"Observed canonical performance: {fraction(sa['canonical'])} cells; {fraction(sa['atomic'])} decisions. Permuted performance: {fraction(sb['canonical'])} cells; {fraction(sb['atomic'])} decisions.",'',
         '## Capability structure','', '| Capability family | Canonical | Permuted |','|---|---|---|']
    for f,name in FAMILIES.items():cap.append(f"| {name} | {fraction(sa['families'][str(f)])} | {fraction(sb['families'][str(f)])} |")
    cap+=['','## Semantic dimensions','', '| Dimension | Canonical | Permuted |','|---|---|---|']
    for d in sa['dimensions']:cap.append(f"| {d} | {fraction(sa['dimensions'][d])} | {fraction(sb['dimensions'][d])} |")
    cap+=['','## Observed confusions','',
          'These are gold-to-selected candidate confusions. A multi-dimension wrong answer does not identify which internal feature caused the error.','']
    for cell,d in decisions(fixture):
        row=amap[d['id']]
        if row['selected_id']!=row['gold_id']:
            describe=lambda k:next(o['description'] for o in row['candidates'] if o['id']==k)
            cap.append('- '+d['id']+': '+describe(row['gold_id'])+' → '+describe(row['selected_id'])+'.')
    cap+=['','## Order stability','',
          f"{comparison['atomic_unchanged']} / 42 atomic choices and {comparison['canonical_unchanged']} / 36 canonical cells retain exact choice identity. Correctness changes in {comparison['correctness_changed']} decisions. Mean total variation distance is {comparison['mean_total_variation_distance']:.4f}.",
          'Order-sensitive cells: '+(', '.join(comparison['order_sensitive_cells']) or 'none')+'.','',
          'Sequential final accuracy and joint accuracy remain separate: canonical '+fraction(sa['sequential']['final'])+' final, '+fraction(sa['sequential']['joint'])+' joint. Wrong-path/right-final cells: '+(', '.join(sa['sequential']['wrong_path_right_final']) or 'none')+'.','',
          'Forward/reverse family totals include segmented recognition and their one HARD whole-sentence cell. Whole-sentence recognition specifically scores '+fraction(sa['whole_expression']['English_to_New_Ithkuil'])+' English → New Ithkuil and '+fraction(sa['whole_expression']['New_Ithkuil_to_English'])+' New Ithkuil → English.','',
          'For SIMPLE/MEDIUM/HARD, source-exact versus derived/compositional tasks, complete-expression validation, latency and runtime, see [RESULTS.md](RESULTS.md). Every confusion can be inspected with all probabilities in [FAILURES.md](FAILURES.md). These observations apply to this frozen source packet, calibration and rendering.','']
    return {'RESULTS.md':'\n'.join(lines),'FAILURES.md':'\n'.join(failures),'CAPABILITY_MAP.md':'\n'.join(cap)}


def run_epoch(fixture_path,context_path,identity_path,output,epoch,paired_rows=None,endpoint='http://127.0.0.1:8008'):
    fixture=json.loads(fixture_path.read_text());validate_fixture(fixture)
    if fixture!=compile_issue(fixture_path.with_suffix('.issue.md').read_text()):raise ValueError('ITHKUIL_FIXTURE_TRANSCRIPTION_CHANGED')
    packet=context_path.read_bytes()
    if hashlib.sha256(packet).hexdigest()!=CONTEXT_SHA256:raise ValueError('ITHKUIL_CONTEXT_HASH')
    identity=json.loads(identity_path.read_text())
    if service_identity(local_json(endpoint+'/v1/models','/v1/models')['models'][0])!=identity['service']:raise ValueError('ITHKUIL_PREFLIGHT_RUNTIME_CHANGED')
    paired=[json.loads(line) for line in paired_rows.read_text().splitlines()] if paired_rows else None
    if epoch=='B' and paired is None:raise ValueError('ITHKUIL_PERMUTATION_REQUIRES_CANONICAL_STATES')
    if paired:validate_rows(fixture,paired)
    frozen={r['decision_id']:r for r in paired or []}
    output.mkdir(parents=True,exist_ok=False)
    receipt={'epoch':epoch,'fixture_file_sha256':file_hash(fixture_path),'context_packet_sha256':CONTEXT_SHA256,
             'runtime_identity':identity,'seed':fixture['permutation_seed'] if epoch=='B' else None,
             'canonical_state_replay':bool(paired),'model_calls_expected':42,'status':'STARTED'}
    (output/'START.json').write_text(json.dumps(receipt,indent=2)+'\n')
    rows=[];started=time.perf_counter()
    with (output/'rows.jsonl').open('x') as stream:
        for cell in fixture['cells']:
            path=[]
            for d in cell.get('steps',[cell]):
                seq={'target':cell['prompt'],'fixed_predicate':cell.get('fixed_predicate'),'selected_path':copy.deepcopy(path)} if cell['family']==10 else {}
                if paired:seq=frozen[d['id']]['sequence_context']
                state={'source_packet':packet.decode('utf-8'),'sequence':seq} if seq else packet.decode('utf-8')
                item={'id':d['id'],'split':'DEV','state':state,'question':d['prompt'],'options':copy.deepcopy(d['candidates'])}
                if epoch=='B':item=permute(item,fixture['permutation_seed'])
                if epoch=='B' and [o['id'] for o in item['options']]==[o['id'] for o in d['candidates']]:raise ValueError('ITHKUIL_NO_PERMUTATION')
                native=kev_score(item,endpoint,identity)
                if service_identity(native['runtime_metadata']['models'])!=identity['service']:raise ValueError('ITHKUIL_RUNTIME_CHANGED')
                values=sorted(native['probabilities'].values(),reverse=True)
                row={**native,'decision_id':d['id'],'cell_id':cell['id'],'sequence_step_id':d['id'] if cell['family']==10 else None,
                     'epoch':epoch,'fixture_file_sha256':receipt['fixture_file_sha256'],'context_packet_sha256':CONTEXT_SHA256,
                     'question':d['prompt'],'candidates':item['options'],'candidate_order':[o['id'] for o in item['options']],
                     'gold_id':d['gold_candidate'],'correct':native['selected_id']==d['gold_candidate'],
                     'top_probability':values[0],'margin':values[0]-values[1],'runtime_identity':identity,
                     'sequence_context':seq,'route':'evaluation_only; no runtime promotion policy applied',
                     'request_payload_sha256':digest({'model':'kev-latest','state':state,'questions':{'decision':{'type':'choice','instructions':d['prompt'],'criteria':{o['id']:o['description'] for o in item['options']}}}})}
                stream.write(json.dumps(row,ensure_ascii=False,allow_nan=False)+'\n');stream.flush()
                import os;os.fsync(stream.fileno())
                rows.append(row)
                selected=next(o for o in d['candidates'] if o['id']==row['selected_id'])
                path.append({'decision_id':d['id'],'candidate_id':selected['id'],'description':selected['description']})
                print(f"{epoch} {d['id']} {'correct' if row['correct'] else 'INCORRECT'} P={values[0]:.4f} margin={values[0]-values[1]:.4f}",flush=True)
    if file_hash(context_path)!=CONTEXT_SHA256:raise ValueError('ITHKUIL_CONTEXT_CHANGED_DURING_EPOCH')
    summary=summarize(fixture,rows,time.perf_counter()-started)
    receipt.update(status='COMPLETE',model_calls_completed=len(rows),rows_sha256=file_hash(output/'rows.jsonl'))
    (output/'summary.json').write_text(json.dumps(summary,ensure_ascii=False,indent=2)+'\n')
    (output/'RECEIPT.json').write_text(json.dumps(receipt,ensure_ascii=False,indent=2)+'\n')
    print(json.dumps({'epoch':epoch,'canonical':summary['canonical'],'atomic':summary['atomic']},ensure_ascii=False))


def main():
    p=argparse.ArgumentParser(description=__doc__);sub=p.add_subparsers(dest='command',required=True)
    run=sub.add_parser('run');run.add_argument('--fixture',type=Path,required=True);run.add_argument('--context',type=Path,required=True)
    run.add_argument('--identity',type=Path,required=True);run.add_argument('--output',type=Path,required=True);run.add_argument('--epoch',choices=['A','B'],required=True)
    run.add_argument('--paired-rows',type=Path)
    replay=sub.add_parser('report');replay.add_argument('--fixture',type=Path,required=True);replay.add_argument('--evidence',type=Path,required=True)
    a=p.parse_args()
    if a.command=='run':run_epoch(a.fixture,a.context,a.identity,a.output,a.epoch,a.paired_rows)
    else:
        f=json.loads(a.fixture.read_text());read=lambda path:[json.loads(s) for s in path.read_text().splitlines()]
        ar=read(a.evidence/'A/rows.jsonl');br=read(a.evidence/'B/rows.jsonl');review=json.loads((a.evidence/'source-verification.json').read_text())
        review['sources']=json.loads((a.evidence/'source-manifest.json').read_text())['sources']
        summaries={epoch:summarize(f,rows,json.loads((a.evidence/epoch/'summary.json').read_text())['latency']['epoch_wall_seconds']) for epoch,rows in [('A',ar),('B',br)]}
        combined={'fixture_file_sha256':file_hash(a.fixture),'context_packet_sha256':CONTEXT_SHA256,**summaries,'order_comparison':compare_orders(f,ar,br)}
        (a.evidence/'summary.json').write_text(json.dumps(combined,ensure_ascii=False,indent=2)+'\n')
        confusion={'dimensions':{k:v['dimensions'] for k,v in summaries.items()},'families':{k:v['families'] for k,v in summaries.items()},
                   'wrong_choices':{epoch:[{'decision_id':r['decision_id'],'gold':r['gold_id'],'selected':r['selected_id'],'probabilities':r['probabilities']} for r in rows if r['selected_id']!=r['gold_id']] for epoch,rows in [('A',ar),('B',br)]},
                   'order':combined['order_comparison']}
        (a.evidence/'capability.json').write_text(json.dumps(confusion,ensure_ascii=False,indent=2)+'\n')
        for name,content in render_reports(f,ar,br,review).items():(a.evidence/name).write_text(content)
        print(json.dumps({'canonical':combined['A']['canonical'],'atomic':combined['A']['atomic'],'order_changes':combined['order_comparison']['atomic_changed']}))


if __name__=='__main__':main()
