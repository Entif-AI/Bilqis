"""Freeze -> qualify teacher -> freeze cohort -> continue -> evaluate -> replay.

The inherited spiral owns allocation and independent generation. The teacher
policy owns admission and feedback; Kev may choose a causal exercise reservoir.
Final worlds are physically absent from the teacher/training executor's inputs.
"""
from __future__ import annotations

import argparse
from collections import Counter
import copy
import gzip
import hashlib
import json
from pathlib import Path
import random
import resource
import subprocess
import sys
import time

import torch

from bilqis_logic.kernel import canonical, digest
from bilqis_logic.geometry import tensor_hash
from bilqis_micro.run import optimizer_receipt
from bilqis_ref.model import state_hash
from bilqis_development import run as student
from bilqis_development.continuation import load, save
from bilqis_development.vendor.kev_teacher import KevTeacher
from bilqis_development.registry import RECIPES
from bilqis_spiral import run as spiral
from bilqis_spiral.sampler import MIX, Sampler, build_pools, existing_ids, family_key
from bilqis_teacher.policy import load_policy, source_manifest, novelty, feedback, validate_lesson
from bilqis_teacher.grammar import exercises, compile_exercise, validate_witness, DEFINITIONS
from bilqis_teacher.battery import make_battery, run_battery, verify_trace

ROOT, PARENT, CURRENT = spiral.ROOT, spiral.PARENT, spiral.CURRENT
DEFAULT_RUN = ROOT / 'docs/evidence/u7b/run-01'
UPDATES, SEED = 256, 73971
U7 = ROOT / 'docs/evidence/spiral-u7/run-01'
read, write, compressed, sha = spiral.read, spiral.write, spiral.compressed, spiral.sha


def sources():
    paths = set(spiral.SOURCES) | {'bilqis_ref/model.py', 'bilqis_micro/model.py', 'bilqis_micro/graph.py', 'bilqis_logic/kernel.py',
                                   'bilqis_logic/geometry.py', 'bilqis_development/vendor/kev_teacher.py', 'bilqis_development/registry.py'}
    paths.update(str(p.relative_to(ROOT)) for package in ('bilqis_teacher', 'bilqis_u7b')
                 for p in (ROOT / package).glob('*') if p.suffix in ('.py', '.json'))
    return {p: sha(ROOT / p) for p in sorted(paths)}


def jsonlines(path):
    with (gzip.open(path, 'rt') if path.suffix == '.gz' else path.open()) as f:
        return [json.loads(line) for line in f]


def preserved_start(model, optimizer, payload):
    receipt = optimizer_receipt(optimizer)
    if (state_hash(model) != payload['state_sha256'] or receipt != payload['optimizer_receipt'] or
        receipt['steps'] != [13400] or payload['state_sha256'] != '5ec251f79620156a83be5ae3cdcdc961d071e75ff1f6bcc3ed721f4482952034'):
        raise ValueError('U6 trained weights or AdamW moments/counters changed')
    return {'state_sha256': state_hash(model), 'optimizer': receipt,
            'parameter_tensors': {name: tensor_hash(t) for name, t in model.state_dict().items()},
            'semantic_graph_sha256': digest(payload['graph']), 'semantic_ids': len(payload['graph']['tokens']),
            'parameters': sum(p.numel() for p in model.parameters()), 'new_rows': 0}


def freeze_battery(run):
    run.mkdir(parents=True, exist_ok=False)
    write(run / 'plan.json', {'epoch': 'U7B', 'updates': UPDATES, 'seed': SEED, 'teacher_battery_calls': 48,
         'pedagogical_calls': 8, 'teacher_cadence': 64, 'dev_cadence': 16, 'batch': MIX,
         'policy': load_policy(), 'source_hashes': sources(), 'semantic_sources': source_manifest(),
         'parent_checkpoint_sha256': sha(CURRENT), 'parent_head': '66e44542abf429699f541ee272e2827d39be3f09',
         'code_commit': subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=ROOT, text=True).strip(),
         'environment': {'python': sys.version, 'torch': torch.__version__, 'student_device': 'cpu', 'student_dtype': 'float32', 'threads': 1},
         'historical_u7_files': {str(p.relative_to(ROOT)): sha(p) for p in U7.iterdir() if p.is_file()},
         'scientific_status': 'exploratory single-seed alternative continuation; no efficacy attribution control'})
    write(run / 'battery.json', make_battery())
    write(run / 'battery-freeze.json', {'plan_sha256': sha(run / 'plan.json'), 'battery_sha256': sha(run / 'battery.json')})
    return {'status': 'BATTERY_FROZEN', 'updates_predeclared': UPDATES, 'calls': 48}


def verify_plan(run):
    plan = read(run / 'plan.json'); frozen = read(run / 'battery-freeze.json')
    if (sha(run / 'plan.json') != frozen['plan_sha256'] or sha(run / 'battery.json') != frozen['battery_sha256'] or
        plan['source_hashes'] != sources() or plan['semantic_sources'] != source_manifest() or
        plan['parent_checkpoint_sha256'] != sha(CURRENT) or plan['policy'] != load_policy()):
        raise ValueError('immutable U7B plan/source/battery drift')
    for path, expected in plan['historical_u7_files'].items():
        if sha(ROOT / path) != expected: raise ValueError('historical U7 freeze changed')
    return plan


def qualify(run):
    verify_plan(run)
    with (run / 'battery-traces.jsonl').open('xb') as f:
        result = run_battery(read(run / 'battery.json'), KevTeacher(), lambda r: f.write(canonical(r) + b'\n'))
    result['traces_sha256'] = sha(run / 'battery-traces.jsonl')
    write(run / 'teacher-result.json', result)
    return result


def with_sources(row):
    row = dict(row)
    if row['stage'] < 5: row['source_locator'] = 'https://github.com/Entif-AI/Bilqis/issues/80'
    return validate_lesson(row)


def frozen_u7_rows():
    pools = read(U7 / 'train-pools.json.gz'); final = read(U7 / 'final-evaluation.json.gz')
    rows = [r for cat in ('fresh', 'cross', 'weak') for group in pools[cat].values() for r in group]
    rows += [r for splits in final.values() for group in splits.values() for r in group]
    rows += [r for p in pools['causal'] for r in (p['old_contrast'], p['new_contrast'])]
    return rows


def freeze(run):
    plan = verify_plan(run); teacher = read(run / 'teacher-result.json')
    if teacher['traces_sha256'] != sha(run / 'battery-traces.jsonl'): raise ValueError('teacher qualification drift')
    if (run / 'freeze.json').exists(): raise FileExistsError('cohort is immutable')
    started = time.perf_counter()
    corpus = read(PARENT / 'data.json.gz')
    augmented = copy.deepcopy(corpus)
    augmented['stages']['6']['train']['excluded-u7'] = frozen_u7_rows()
    pools = build_pools(augmented, plan['seed'], plan['updates'])
    final = pools.pop('final')
    for category in ('fresh', 'cross', 'weak'):
        for key, rows in pools[category].items(): pools[category][key] = [with_sources(r) for r in rows]
    specs = [s for stage in (5, 6) for s in exercises(stage)]
    lookup = {(s['stage'], s['family'], s['old_arm']): s for s in specs}
    rows_by_id = {r['id']: r for rows in pools['cross'].values() for r in rows}
    witnesses = []
    for proof in pools['causal']:
        r = rows_by_id[proof['base']]
        spec = lookup[(r['stage'], proof['new_family'], proof['old_family'].split(':')[1])]
        r['teacher_spec_id'] = spec['id']
        witness = {'base': r['id'], 'spec_id': spec['id'], 'old_contrast': with_sources(proof['old_contrast']), 'new_contrast': with_sources(proof['new_contrast'])}
        validate_witness(r, witness); witnesses.append(witness)
    pools['causal'] = witnesses
    excluded = existing_ids(corpus) | {r['id'] for r in frozen_u7_rows()}
    excluded.update(r['id'] for cat in ('fresh', 'cross', 'weak') for rows in pools[cat].values() for r in rows)
    excluded.update(r['id'] for w in witnesses for r in (w['old_contrast'], w['new_contrast']))
    for splits in final.values():
        for key, rows in splits.items():
            splits[key] = [with_sources(r) for r in rows]; excluded.update(r['id'] for r in rows)
    # All panel candidates have a realizable TRAIN reservoir; fill any absent
    # production rather than substituting a handpicked candidate after a decision.
    represented = {r['teacher_spec_id'] for rows in pools['cross'].values() for r in rows}
    rng = random.Random(plan['seed'] + 2)
    for spec in specs:
        if spec['id'] not in represented:
            for _ in range(8):
                r, proof = compile_exercise(spec, rng, excluded)
                r['teacher_spec_id'] = spec['id']; pools['cross'][str(spec['stage'])].append(r); pools['causal'].append(proof)
    final_cross = []
    for spec in specs:
        for _ in range(2):
            r, _ = compile_exercise(spec, rng, excluded, varied=True)
            final_cross.append(dict(r, teacher_spec_id=spec['id']))
    model, optimizer, payload = load(CURRENT)
    start = preserved_start(model, optimizer, payload)
    before = spiral.dev(model, corpus)
    archived = read(PARENT / 'after-U6.json.gz')
    if any([(p['id'], p['prediction']) for p in before[s][split]['predictions']] !=
           [(p['id'], p['prediction']) for p in archived[s][split]['predictions']]
           for s in before for split in ('varied', 'composite')): raise ValueError('U6 baseline does not reproduce')
    feedback(before, corpus)
    new_ids = {r['id'] for cat in ('fresh', 'cross', 'weak') for rows in pools[cat].values() for r in rows}
    final_ids = {r['id'] for splits in final.values() for rows in splits.values() for r in rows} | {r['id'] for r in final_cross}
    if new_ids & final_ids or final_ids & existing_ids(corpus): raise ValueError('U7B TRAIN/final overlap')
    novelty_rows = [{'candidate': {'identity': t}, 'resolution': novelty({'identity': t}, payload['graph'])} for t in payload['graph']['tokens']]
    for spec in specs:
        representative = next(r for r in pools['cross'][str(spec['stage'])] if r['teacher_spec_id'] == spec['id'])
        candidate = {'source': spec['source'], 'record': representative['input']}
        novelty_rows.append({'candidate_id': spec['id'], 'resolution': novelty(candidate, payload['graph'])})
    if any(r['resolution']['eg2_permitted'] for r in novelty_rows): raise ValueError('this known-meaning epoch unexpectedly needs retrieval')
    compressed(run / 'train-pools.json.gz', pools)
    compressed(run / 'final-evaluation.json.gz', {'stages': final, 'cross': final_cross})
    compressed(run / 'dev-before.json.gz', before)
    write(run / 'grammar-candidates.json', specs)
    write(run / 'novelty.json', {'records': novelty_rows, 'categories': dict(Counter(r['resolution']['category'] for r in novelty_rows)), 'eg2_calls': 0, 'eg2_cost': {'request_seconds': 0, 'encoded_texts': 0}})
    manifest = {'epoch': 'U7B', 'policy_identity': load_policy()['identity'], 'updates': plan['updates'], 'seed': plan['seed'], 'start': start,
                'source_hashes': sources(), 'presentation': teacher['presentation'], 'batch': MIX,
                'files': {name: sha(run / name) for name in ('plan.json', 'battery.json', 'teacher-result.json', 'grammar-candidates.json', 'novelty.json', 'train-pools.json.gz', 'final-evaluation.json.gz', 'dev-before.json.gz')},
                'prior_corpus_sha256': sha(PARENT / 'data.json.gz'), 'new_train_rows': len(new_ids), 'final_rows': len(final_ids),
                'cross_witnesses': len(pools['causal']), 'preparation_wall_seconds': time.perf_counter() - started}
    write(run / 'freeze.json', manifest)
    return {'status': 'FROZEN', **{k: manifest[k] for k in ('updates', 'presentation', 'new_train_rows', 'final_rows', 'cross_witnesses')}}


def verify(run):
    verify_plan(run); manifest = read(run / 'freeze.json')
    if manifest['source_hashes'] != sources() or manifest['prior_corpus_sha256'] != sha(PARENT / 'data.json.gz'):
        raise ValueError('cohort source drift')
    for name, expected in manifest['files'].items():
        if sha(run / name) != expected: raise ValueError('frozen U7B artifact changed: ' + name)
    return manifest, read(run / 'train-pools.json.gz'), read(PARENT / 'data.json.gz')


def teaching_panel(stage, signals, period):
    choices = sorted(exercises(stage), key=lambda s: (-signals[f'{stage}:{s["family"]}']['weight'], s['family'], s['old_arm']))
    families = []
    for spec in choices:
        if spec['family'] not in families: families.append(spec['family'])
    selected = [next(s for s in choices if s['family'] == family and s['old_arm'] == ('direction', 'quantifier', 'entailment')[(period + i) % 3]) for i, family in enumerate(families[:3])]
    return {'decision_class': 'pedagogical_selection', 'stage': stage, 'period': period,
            'candidates': selected + [{'id': 'REVIEW'}], 'dev_signals': signals,
            'question': 'Select a valid exercise reservoir to address the observed developmental deficits while composing recent and prerequisite skills. All offered exercises are semantically valid; there is no gold pedagogical winner. Request review if no exercise is appropriate.'}


def render_teaching(panel, mode):
    english = 'Teaching objective: improve compositional reasoning without losing earlier skills. Deficits below are adaptive DEV measurements; they are not final results. '
    english += '; '.join(f'{key}: {s["errors"]}/{s["n"]} mistakes' for key, s in sorted(panel['dev_signals'].items()))
    canonical_context = json.dumps({'DEV': panel['dev_signals'], 'allocation': MIX, 'stage': panel['stage'], 'validated_previous_state': 'U6 semantic catalog unchanged'}, sort_keys=True)
    state = english if mode == 'english' else canonical_context if mode == 'canonical' else english + '\n' + canonical_context
    options = []
    for spec in panel['candidates']:
        if spec['id'] == 'REVIEW': text = 'Request review; retain broad formally valid exercise reservoirs'
        else:
            gloss = DEFINITIONS[spec['family']] + ' Compose this with earlier ' + spec['old_arm'] + ' reasoning. Both components must change the oracle answer under a single-factor contrast.'
            canonical_spec = json.dumps(dict(spec, typed_operations=next(r[2] for r in RECIPES if r[0] == spec['family'])), sort_keys=True)
            text = gloss if mode == 'english' else canonical_spec if mode == 'canonical' else gloss + ' | ' + canonical_spec
        options.append({'candidate_id': spec['id'], 'description': text})
    # Rotate panels independently of quality; never keep the apparent best first.
    shift = (panel['period'] + panel['stage']) % len(options)
    options = options[shift:] + options[:shift]
    return state, panel['question'], options


def apply_choice(panel, trace, reservoir):
    choice = trace.get('choice')
    offered = {s['id'] for s in panel['candidates']}
    if trace['status'] == 'ERROR' or trace.get('margin', 0) < load_policy()['kev']['min_margin'] or choice == 'REVIEW':
        return reservoir, 'review-fallback'
    if choice not in offered: raise ValueError('teacher selected outside admissible grammar')
    chosen = [r for r in reservoir if r['teacher_spec_id'] == choice]
    if not chosen: raise ValueError('admissible teacher production has no compiled lessons')
    return chosen, 'accepted'


def execute(run, manifest, pools, corpus, model, optimizer, emit, decision_emit, *, archived=None):
    baseline = read(run / 'dev-before.json.gz')
    signals = feedback(baseline, corpus)
    sampler = Sampler(corpus, copy.deepcopy(pools), manifest['seed'] + 1, signals)
    decisions, exposures, categories, specs = [], Counter(), Counter(), Counter()
    tokens = padded = 0; gradient_wall = helper_wall = dev_wall = 0.
    for iteration in range(manifest['updates']):
        if iteration and iteration % 16 == 0:
            started = time.perf_counter(); scores = spiral.dev(model, corpus)
            signals = feedback(scores, corpus, baseline); sampler.update_signals(signals)
            dev_wall += time.perf_counter() - started
        if iteration % 64 == 0:
            for stage in (5, 6):
                panel = teaching_panel(stage, signals, iteration // 64)
                state, question, options = render_teaching(panel, manifest['presentation']['selected'])
                if archived is None:
                    trace = KevTeacher().score(state, question, options, {'epoch': 'U7B', 'update': iteration, 'stage': stage, 'decision_class': 'pedagogical_selection'})
                else:
                    trace = archived[len(decisions)]['trace']
                    if (trace['payload']['state'] != state or trace['payload']['questions']['decision']['instructions'] != question or
                        list(trace['payload']['questions']['decision']['criteria'].items()) != [(o['candidate_id'], o['description']) for o in options]):
                        raise ValueError('DEV/candidate/teacher replay drift')
                verify_trace(trace)
                chosen, disposition = apply_choice(panel, trace, pools['cross'][str(stage)])
                sampler.pools['cross'][str(stage)] = chosen
                receipt = {'update': iteration, 'panel': panel, 'trace': trace, 'disposition': disposition,
                           'compiled_row_ids': [r['id'] for r in chosen], 'signals_sha256': digest(signals)}
                decisions.append(receipt); decision_emit(receipt); helper_wall += trace['wall_seconds'] if archived is None else 0
        rows, labels, keys = sampler.batch()
        for row in rows: with_sources(row)
        started = time.perf_counter(); loss, norm, used, positions = spiral._step(model, optimizer, rows)
        gradient_wall += time.perf_counter() - started; tokens += used; padded += positions
        record = {'step': 13401 + iteration, 'row_ids': [r['id'] for r in rows], 'categories': labels, 'weak_keys': keys,
                  'stages': [r['stage'] for r in rows], 'families': [r['family'] for r in rows],
                  'teacher_spec_ids': [r.get('teacher_spec_id') if label == 'cross_stage' else None for r, label in zip(rows, labels)],
                  'signals_sha256': digest(sampler.signals), 'loss': loss, 'gradient_norm': norm, 'tokens': used, 'padded_positions': positions}
        emit(record); exposures.update(record['row_ids']); categories.update(labels); specs.update(s for s in record['teacher_spec_ids'] if s)
    return {'updates': manifest['updates'], 'optimizer_step': 13400 + manifest['updates'], 'optimizer': optimizer_receipt(optimizer),
            'state_sha256': state_hash(model), 'exposures': dict(exposures), 'category_counts': dict(categories), 'spec_exposures': dict(specs),
            'tokens': tokens, 'padded_positions': padded, 'gradient_wall_seconds': gradient_wall, 'dev_wall_seconds': dev_wall,
            'helper_wall_seconds': helper_wall, 'teacher_calls': len(decisions), 'teacher_accepted': sum(d['disposition'] == 'accepted' for d in decisions)}


def train(run):
    manifest, pools, corpus = verify(run)
    if any((run / name).exists() for name in ('after.pt', 'training.jsonl.gz', 'pedagogical-traces.jsonl')): raise FileExistsError('one immutable student run only')
    model, optimizer, payload = load(CURRENT)
    if preserved_start(model, optimizer, payload) != manifest['start']: raise ValueError('pre-gradient continuation mismatch')
    start, cpu = time.perf_counter(), time.process_time()
    with (run / 'training.jsonl.gz').open('xb') as raw, (run / 'pedagogical-traces.jsonl').open('xb') as decisions:
        with gzip.GzipFile(fileobj=raw, mode='wb', mtime=0) as stream:
            result = execute(run, manifest, pools, corpus, model, optimizer,
                             lambda r: stream.write(canonical(r) + b'\n'), lambda r: decisions.write(canonical(r) + b'\n'))
    if result['optimizer']['steps'] != [13656] or result['category_counts'] != {k: v * UPDATES for k, v in MIX.items()}:
        raise ValueError('optimizer/exposure invariant failed')
    save(run / 'after.pt', model, optimizer, payload['graph'], {'epoch': 'U7B', 'step': result['optimizer_step'], 'parent_checkpoint_sha256': sha(CURRENT), 'freeze_sha256': sha(run / 'freeze.json')})
    result.update({'checkpoint_sha256': sha(run / 'after.pt'), 'wall_seconds': time.perf_counter() - start, 'cpu_seconds': time.process_time() - cpu,
                   'peak_process_rss_bytes': resource.getrusage(resource.RUSAGE_SELF).ru_maxrss * (1 if sys.platform == 'darwin' else 1024),
                   'artifacts': {name: sha(run / name) for name in ('training.jsonl.gz', 'pedagogical-traces.jsonl', 'freeze.json')}})
    write(run / 'training-result.json', result)
    return {k: result[k] for k in ('updates', 'optimizer_step', 'tokens', 'teacher_calls', 'teacher_accepted', 'wall_seconds', 'state_sha256')}


def evaluation_inputs(run, corpus):
    final = read(run / 'final-evaluation.json.gz')
    primitives = [dict(r, family='Boolean-primitive') for r in read(PARENT / 'primitive-retention.json')['rows']]
    return {'fresh_final': final['stages'], 'cross_final': final['cross'], 'historical': corpus['stages'],
            'distinctions': read(PARENT / 'distinction-probes.json'), 'primitives': primitives}


def score_all(model, inputs):
    return {'fresh_final': {s: {split: student.score(model, rows) for split, rows in splits.items()} for s, splits in inputs['fresh_final'].items()},
            'cross_final': student.score(model, inputs['cross_final']),
            'historical': {s: {split: student.score(model, rows) for split, rows in data['eval'].items()} for s, data in inputs['historical'].items()},
            'distinctions': student.score(model, inputs['distinctions']), 'primitives': student.score(model, inputs['primitives'])}


def evaluate(run):
    _, _, corpus = verify(run); result = read(run / 'training-result.json')
    if (run / 'evaluation.json.gz').exists(): raise FileExistsError('fresh final has already been opened')
    if sha(run / 'after.pt') != result['checkpoint_sha256']: raise ValueError('checkpoint drift')
    after, _, _ = load(run / 'after.pt'); before, _, _ = load(CURRENT)
    inputs = evaluation_inputs(run, corpus)
    results = {'final_opened_after_training': True, 'before': score_all(before, inputs), 'after': score_all(after, inputs)}
    compressed(run / 'evaluation.json.gz', results)
    return {'status': 'EVALUATED', 'fresh_final_n': 448, 'cross_final_n': results['after']['cross_final']['n'],
            'distinctions': [results[x]['distinctions']['correct'] for x in ('before', 'after')],
            'primitives': [results[x]['primitives']['correct'] for x in ('before', 'after')]}


def replay(run):
    manifest, pools, corpus = verify(run); recorded = read(run / 'training-result.json')
    for name, expected in recorded['artifacts'].items():
        if sha(run / name) != expected: raise ValueError('training receipt drift')
    model, optimizer, payload = load(CURRENT); preserved_start(model, optimizer, payload)
    expected = jsonlines(run / 'training.jsonl.gz'); actual = []
    decisions = jsonlines(run / 'pedagogical-traces.jsonl')
    outcome = execute(run, manifest, pools, corpus, model, optimizer, actual.append, lambda r: None, archived=decisions)
    if len(actual) != len(expected): raise ValueError('gradient count replay')
    for a, b in zip(actual, expected):
        if a != b: raise ValueError('exact gradient/curriculum replay mismatch')
        if Counter(a['categories']) != Counter(MIX): raise ValueError('allocation replay mismatch')
    for key in ('state_sha256', 'optimizer', 'exposures', 'category_counts', 'spec_exposures', 'tokens'):
        if outcome[key] != recorded[key]: raise ValueError('student/AdamW/exposure replay: ' + key)
    if sha(run / 'after.pt') != recorded['checkpoint_sha256']: raise ValueError('saved checkpoint drift')
    # Fresh-process prediction readback: does not feed or change the teacher.
    saved = read(run / 'evaluation.json.gz'); inputs = evaluation_inputs(run, corpus)
    predicted = score_all(model, inputs)
    if predicted != saved['after']: raise ValueError('post-training prediction replay')
    predictions = sum(len(s['predictions']) for stage in predicted['historical'].values() for s in stage.values()) + sum(len(s['predictions']) for stage in predicted['fresh_final'].values() for s in stage.values()) + sum(predicted[k]['n'] for k in ('cross_final', 'distinctions', 'primitives'))
    for r in jsonlines(run / 'battery-traces.jsonl') + decisions: verify_trace(r['trace'])
    receipt = {'status': 'EXACT_REPLAY', 'gradients': len(actual), 'optimizer_step': outcome['optimizer_step'], 'predictions': predictions,
               'state_sha256': outcome['state_sha256'], 'optimizer_sha256': outcome['optimizer']['state_sha256'], 'native_helpers_rerun': False,
               'training_and_predictions_exact': True, 'historical_u7_preserved': True}
    write(run / 'replay.json', receipt); return receipt


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('action', choices=('freeze-battery', 'qualify', 'freeze', 'train', 'evaluate', 'replay'))
    parser.add_argument('--run', type=Path, default=DEFAULT_RUN)
    args = parser.parse_args()
    action = {'freeze-battery': freeze_battery, 'qualify': qualify, 'freeze': freeze, 'train': train, 'evaluate': evaluate, 'replay': replay}[args.action]
    print(json.dumps(action(args.run), sort_keys=True))


if __name__ == '__main__': main()
