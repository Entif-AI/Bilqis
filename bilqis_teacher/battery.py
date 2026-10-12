"""A frozen matched context battery; semantic gold never becomes teaching utility."""
from __future__ import annotations

import hashlib
import json

from bilqis_logic.kernel import digest
from bilqis_micro import kernel as old
from bilqis_micro.graph import STATES
from bilqis_development import kernel as k
from bilqis_development.registry import SIGNATURES, extended_catalog
from bilqis_development.vendor.kev_teacher import validate_response
from .policy import load_policy

MODES = ('english', 'canonical', 'combined')
QUESTION = 'Choose the expression satisfying the requested criterion under the supplied source semantics. Choose REVIEW if the criterion is underdetermined. Do not resolve missing information by guessing.'
GLOSSES = {
    'DERIVED_FROM': 'content origin reachable through one or more origin links',
    'DEPENDENCY': 'declared premise use reachable through one or more proof-use links',
    'SUPERSEDES': 'explicit replacement of an earlier report about the same proposition',
    'REVISES': 'explicit replacement with changed supporting versus opposing content',
    'IS_ASSERTION': 'is a statement made by a source',
    'IS_OBSERVATION': 'is a recorded observation event',
    'IS_CURRENT': 'is an event retained after excluding replaced reports',
    'CURRENT_STATE': 'aggregate evidence from retained reports only',
    'HISTORICAL_STATE': 'aggregate evidence from every recorded report',
    'MAPS': 'maps the input to the output', 'COMPOSITION': 'apply first mapping then second mapping',
    'INVERSE': 'reverse an injective mapping',
    'FALSE': 'opposing evidence only', 'TRUE': 'supporting evidence only',
    'UNKNOWN': 'neither supporting nor opposing evidence', 'CONFLICT': 'both supporting and opposing evidence',
    'AMBIGUOUS': 'different evidence states across live interpretations'
}


def gloss(expression):
    if isinstance(expression, str): return GLOSSES.get(expression, expression)
    if expression['kind'] == 'const': return expression['name']
    return GLOSSES[expression['op']] + '(' + ', '.join(gloss(a) for a in expression['args']) + ')'


def options_for(args, result):
    types = tuple(a['type'] for a in args)
    return [k.op(name, *args) for name, signature in SIGNATURES.items() if signature[:2] == (types, result)]


def cell(identity, source, english, canonical, meanings, target, *, sequence=None, proofs=()):
    options = [{'candidate_id': 'Q' + digest(q)[:12], 'meaning': q, 'english': gloss(q)} for q in meanings]
    options.append({'candidate_id': 'REVIEW', 'meaning': 'REVIEW', 'english': 'Request the missing distinction or independent source review'})
    gold = 'REVIEW' if target is None else next(c['candidate_id'] for c in options if c['meaning'] == target)
    for proof in proofs:
        if k.evaluate(proof) != k.independent_evaluate(proof): raise ValueError('battery source/oracle mismatch')
    return {'id': identity, 'source': source, 'decision_class': 'semantic_discrimination',
            'english': english, 'canonical': canonical, 'candidates': options, 'gold': gold,
            'sequence': sequence, 'independent_proofs': list(proofs)}


def make_battery():
    e, h = k.const('Event', 'E1'), k.const('Event', 'E0')
    p = k.const('Proposition', 'J0')
    base = old.world('ABC', [('PARENT', 'A', 'B')], propositions={'J0': old.relation('PARENT', old.entity('A'), old.entity('B'))})
    events = [['E0', 'ASSERT', 'S0', 'J0', 'support'], ['E1', 'OBSERVE', 'S1', 'J0', 'refute']]
    lineage = options_for([e, h], 'Boolean')
    world = k.world('ABC', base=base, events=events, links=[['SUPERSEDES', 'E1', 'E0']])
    result = []
    for identity, target, english, constraints in (
        ('origin', 'DERIVED_FROM', 'Test whether the later record has the earlier record as its direct or indirect content origin. Replacement and proof-premise use do not alone establish this.', {'path_role': 'content-origin', 'closure': 'positive-transitive', 'replacement_implies_origin': False}),
        ('replacement', 'SUPERSEDES', 'Test explicit replacement of an earlier report about the same proposition. Its polarity may stay the same; copying or premise use is insufficient.', {'role': 'replacement', 'same_proposition': True, 'polarity_change_required': False}),
        ('underspecified', None, 'The later event follows the earlier event. No relation kind was supplied. Which relation does this establish?', {'event_order': ['E0', 'E1'], 'edge_kind': None, 'inference_from_order': False})
    ):
        target_query = None if target is None else k.op(target, e, h)
        proofs = [k.record(k.world('ABC', base=base, events=events, links=[[kind, 'E1', 'E0']]), q)
                  for kind in ('DERIVED_FROM', 'SUPERSEDES') for q in lineage]
        result.append(cell(identity, '84', english, constraints, lineage, target_query, proofs=proofs))

    f, g = k.const('Function', 'F0'), k.const('Function', 'F1')
    a, c = k.const('Entity', 'A'), k.const('Entity', 'C')
    terms = [k.op('COMPOSITION', x, y) for x, y in ((f, g), (g, f))] + [k.op('INVERSE', x) for x in (f, g)]
    meanings = [k.op('MAPS', t, a, c) for t in terms]
    w = k.world('ABC', functions={'F0': [['A', 'B']], 'F1': [['B', 'C']]})
    result.append(cell('composition-order', '85', 'Test a two-step mapping from A to C, first through F0 and then through F1. Reversing order or a single inverted mapping is a different claim.',
                       {'input': 'A', 'output': 'C', 'pipeline': ['F0', 'F1']}, meanings, meanings[0], proofs=[k.record(w, q) for q in meanings]))

    for identity, reports in (('no-reports', []), ('opposed-reports', [['S0', 'J0', 'support', 0], ['S1', 'J0', 'refute', 0]])):
        w = old.world('ABC', propositions=base['propositions'], reports=reports)
        r = old.record(w, old.observe('J0'))
        gold = old.independent_evaluate(r)
        if gold != old.evaluate(r): raise ValueError('evidence oracle mismatch')
        description = 'No reports exist about the proposition.' if not reports else 'One source supports the proposition; another refutes it in the same live interpretation. Neither report is removed.'
        result.append(cell(identity, '80', 'Summarize the evidence, independently of the underlying factual truth. ' + description,
                           {'reports': reports, 'live_interpretations': [0], 'evidence_not_fact': True}, list(STATES), gold))

    meanings = options_for([e], 'Boolean')
    result.append(cell('sequence-1', '84', 'A later observation replaced the earlier assertion about the same proposition. Select a test of whether the later event remains in the retained record set.',
                       {'world': world, 'predicate_requirement': 'event-in-retained-set'}, meanings, k.op('IS_CURRENT', e), sequence='state-chain', proofs=[k.record(world, q) for q in meanings]))
    meanings = options_for([p], 'Evidence')
    result.append(cell('sequence-2', '84', 'Using the independently validated retained-record set from the preceding step, select the evidence summary that ignores replaced entries.',
                       {'world': world, 'predicate_requirement': 'aggregate-retained-only'}, meanings, k.op('CURRENT_STATE', p), sequence='state-chain', proofs=[k.record(world, q) for q in meanings]))
    return result


def render(cell, mode, permutation, validated_state):
    if mode not in MODES: raise ValueError('teacher rendering')
    parts = []
    if mode in ('english', 'combined'): parts.append('Source-grounded criterion: ' + cell['english'])
    if mode in ('canonical', 'combined'):
        operators = {q['meaning']['op'] for q in cell['candidates'] if isinstance(q['meaning'], dict)}
        primitives = [n for n in extended_catalog()['nodes'] if n['id'].rsplit('.', 1)[-1] in operators]
        parts.append(json.dumps({'source': cell['source'], 'constraints': cell['canonical'], 'typed_primitives': primitives,
                                 'signatures': {name: SIGNATURES[name][:2] for name in sorted(operators)}}, sort_keys=True))
    if validated_state:
        parts.append(('Independent preceding state: ' if mode != 'canonical' else 'VALIDATED_STATE=') + json.dumps(validated_state, sort_keys=True))
    candidates = list(cell['candidates'])
    if permutation: candidates.reverse()
    options = []
    for c in candidates:
        canonical = json.dumps(c['meaning'], sort_keys=True)
        text = c['english'] if mode == 'english' else canonical if mode == 'canonical' else c['english'] + ' | ' + canonical
        options.append({'candidate_id': c['candidate_id'], 'description': text})
    return '\n'.join(parts), QUESTION, options


def verify_trace(trace):
    raw = trace['serialized_request']
    if hashlib.sha256(raw.encode()).hexdigest() != trace['request_sha256'] or json.loads(raw) != trace['payload']:
        raise ValueError('teacher request byte identity')
    ids = list(trace['payload']['questions']['decision']['criteria'])
    if ids != trace['offered_candidate_ids']: raise ValueError('teacher actual option order')
    if trace['status'] != 'ERROR':
        validated = validate_response(trace['response'], ids)
        if validated['choice'] != trace['choice'] or validated['probabilities'] != trace['probabilities']:
            raise ValueError('native teacher choice binding')
    return trace


def select_mode(summary):
    best = max(('canonical', 'english'), key=lambda m: summary[m]['correct'])
    combined = summary['combined']
    better = all(combined['correct'] >= summary[m]['correct'] + 2 and
                 combined['review_correct'] >= summary[m]['review_correct'] and
                 combined['sequential_correct'] >= summary[m]['sequential_correct'] for m in ('english', 'canonical'))
    return {'selected': 'combined' if better else best, 'combined_earned': better,
            'reason': 'predeclared paired score and review/state safeguards' if better else 'no qualifying combined advantage; simpler fallback'}


def run_battery(battery, teacher, emit):
    results = []
    for mode in MODES:
        for permutation in (0, 1):
            state = []
            for cell in battery:
                before = list(state) if cell['sequence'] else []
                context, question, options = render(cell, mode, permutation, before)
                trace = teacher.score(context, question, options, {'battery_cell': cell['id'], 'mode': mode, 'permutation': permutation})
                verify_trace(trace)
                choice = trace.get('choice')
                record = {'cell': cell['id'], 'mode': mode, 'permutation': permutation, 'gold': cell['gold'], 'correct': choice == cell['gold'],
                          'validated_state_before': before, 'trace': trace}
                if cell['id'] == 'sequence-1':
                    # Formal source state is rehydrated independently even after
                    # a wrong/rejected teacher choice; no erroneous teacher state becomes truth.
                    state = [{'E0_retained': False, 'E1_retained': True, 'source': '84', 'validated_by': 'independent finite oracle'}]
                record['validated_state_after'] = list(state)
                emit(record); results.append(record)
    summary = {}
    for mode in MODES:
        rows = [r for r in results if r['mode'] == mode]
        summary[mode] = {'n': len(rows), 'correct': sum(r['correct'] for r in rows),
                         'review_correct': sum(r['correct'] and r['gold'] == 'REVIEW' for r in rows),
                         'review_choices': sum(r['trace'].get('choice') == 'REVIEW' for r in rows),
                         'sequential_correct': sum(r['correct'] and r['cell'].startswith('sequence') for r in rows),
                         'sequential_joint': sum(all(r['correct'] for r in rows if r['permutation'] == p and r['cell'].startswith('sequence')) for p in (0, 1)),
                         'order_changes': sum(next(r for r in rows if r['cell'] == c['id'] and r['permutation'] == 0)['trace'].get('choice') != next(r for r in rows if r['cell'] == c['id'] and r['permutation'] == 1)['trace'].get('choice') for c in battery),
                         'low_margin': sum(r['trace']['status'] == 'LOW_MARGIN' for r in rows),
                         'errors': sum(r['trace']['status'] == 'ERROR' for r in rows),
                         'wall_seconds': sum(r['trace']['wall_seconds'] for r in rows)}
    usage = {}
    for row in results:
        for key, value in row['trace'].get('usage', {}).items():
            if type(value) in (int, float): usage[key] = usage.get(key, 0) + value
    return {'summary': summary, 'presentation': select_mode(summary), 'calls': len(results),
            'usage': usage or None, 'policy': load_policy()['identity']}
