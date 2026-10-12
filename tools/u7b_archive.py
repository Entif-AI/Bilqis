"""Preserve the frozen run; rehydrate order from actual native request bytes.

Canonical JSON sorts an archived payload's dictionary keys. Option order is
authoritative only in serialized_request, which retains the exact HTTP bytes.
This audit adapter changes the in-memory reader, never any historical artifact,
student generator, policy, teacher decision, optimizer or frozen source file.
"""
from __future__ import annotations

import argparse
import copy
import hashlib
import json
from pathlib import Path
import time

from bilqis_u7b import run
from bilqis_teacher.battery import render, verify_trace

VERSION = 'u7b-archive-audit-1.0.0'


def restore_request_order(trace):
    fixed = copy.deepcopy(trace)
    raw = fixed['serialized_request']
    if hashlib.sha256(raw.encode()).hexdigest() != fixed['request_sha256']:
        raise ValueError('archived native request bytes changed')
    actual = json.loads(raw)
    if actual != fixed['payload']: raise ValueError('archived request snapshot disagrees with bytes')
    fixed['payload'] = actual
    return verify_trace(fixed)


def gate_prediction(row):
    gate = row['input']['query']['op']
    if gate not in ('AND', 'OR'): raise ValueError('not a spiral cross-stage gate')
    return 'TRUE' if gate == 'AND' else 'FALSE'


def replay(path):
    original = run.jsonlines
    def reader(name):
        rows = original(name)
        for row in rows:
            if 'trace' in row: row['trace'] = restore_request_order(row['trace'])
        return rows
    # Inject only the lossless archive decoder into the frozen replay engine.
    run.jsonlines = reader
    started = time.perf_counter()
    try: result = run.replay(path)
    finally: run.jsonlines = original
    run.write(path / 'archive-replay-receipt.json', {'version': VERSION, 'audit_source_sha256': run.sha(Path(__file__)),
              'frozen_sources_unchanged': True, 'request_order_rehydrated_from_exact_bytes': True,
              'scope': 'archive decoder only; same frozen engine, gradients, decisions and gold',
              'wall_seconds': time.perf_counter() - started, 'result': result})
    return result


def audit(path):
    manifest, pools, _ = run.verify(path)
    final = run.read(path / 'final-evaluation.json.gz')['cross']
    train = [r for rows in pools['cross'].values() for r in rows]
    contrasts = [r for w in pools['causal'] for r in (w['old_contrast'], w['new_contrast'])]
    battery = {c['id']: c for c in run.read(path / 'battery.json')}
    for row in run.jsonlines(path / 'battery-traces.jsonl'):
        trace = restore_request_order(row['trace'])
        context, question, options = render(battery[row['cell']], row['mode'], row['permutation'], row['validated_state_before'])
        if (trace['payload']['state'] != context or trace['payload']['questions']['decision']['instructions'] != question or
            list(trace['payload']['questions']['decision']['criteria'].items()) != [(o['candidate_id'], o['description']) for o in options] or
            row['gold'] != battery[row['cell']]['gold'] or row['correct'] != (trace.get('choice') == row['gold'])):
            raise ValueError('actual native battery panel/gold replay')
    before, _, _ = run.load(run.CURRENT); after, _, _ = run.load(path / 'after.pt')
    result = {'version': VERSION, 'posthoc_diagnostic': True, 'no_teaching_or_training_changes': True,
              'finding': 'gate chosen conditional on aligned operand truth creates a perfect root-operator label shortcut',
              'gate_only_train': {'correct': sum(gate_prediction(r) == r['gold'] for r in train), 'n': len(train)},
              'gate_only_final': {'correct': sum(gate_prediction(r) == r['gold'] for r in final), 'n': len(final)},
              'gate_only_frozen_contrasts': {'correct': sum(gate_prediction(r) == r['gold'] for r in contrasts), 'n': len(contrasts)},
              'counterfactual_scope': 'before-training-frozen, untrained single-arm siblings of TRAIN worlds; posthoc diagnostic, not independently sealed final',
              'counterfactual_before': run.student.score(before, contrasts), 'counterfactual_after': run.student.score(after, contrasts),
              'interpretation': 'formal influence of both operands is insufficient to rule out generator shortcuts; cross-final accuracy does not prove acquired compositional semantics',
              'audit_source_sha256': run.sha(Path(__file__))}
    run.compressed(path / 'shortcut-audit.json.gz', result)
    return {k: result[k] for k in ('gate_only_train', 'gate_only_final', 'gate_only_frozen_contrasts')} | {
             'counterfactual_before': result['counterfactual_before']['correct'], 'counterfactual_after': result['counterfactual_after']['correct'],
             'counterfactual_n': len(contrasts), 'battery_byte_and_panel_replay': True}


def main():
    p = argparse.ArgumentParser(); p.add_argument('action', choices=('replay', 'audit')); p.add_argument('--run', type=Path, default=run.DEFAULT_RUN)
    args = p.parse_args()
    print(json.dumps({'replay': replay, 'audit': audit}[args.action](args.run), sort_keys=True))


if __name__ == '__main__': main()
