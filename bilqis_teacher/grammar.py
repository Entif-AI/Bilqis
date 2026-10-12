"""Typed exercise productions reuse canonical generators, never teacher gold.

Source definitions and leaf generators remain authored in the predecessor.
This grammar enumerates their cross-stage products and independently checks
both operands' counterfactual influence before admitting an instance.
"""
from __future__ import annotations

import itertools

from bilqis_logic.kernel import digest
from bilqis_micro import kernel as old
from bilqis_development import data, kernel as k
from bilqis_development.registry import RECIPES
from .policy import validate_lesson

ARMS = ('direction', 'quantifier', 'entailment')
DEFINITIONS = {r[0]: r[3] for r in RECIPES}


def exercises(stage):
    if stage not in (5, 6): raise ValueError('recent exercise stage')
    result = []
    for family, arm in itertools.product(data.FAMILIES[str(stage)], ARMS):
        spec = {'stage': stage, 'family': family, 'old_arm': arm, 'source': '85' if stage == 5 else '84'}
        result.append(dict(spec, id=digest(spec)))
    return result


def validate_spec(spec):
    if spec not in exercises(spec.get('stage')):
        raise ValueError('unadmitted grammar/source/identity')


def old_expression(w, arm, rng):
    a, b = (old.entity(x) for x in rng.sample(w['base']['entities'], 2))
    q = old.relation('PARENT', a, b)
    if arm == 'quantifier': q = old.quantify('EXISTS', old.relation('PARENT', a, old.bound(0)))
    elif arm == 'entailment': q = old.entails(q)
    return k.inherited(q)


def validate_witness(row, witness):
    validate_lesson(row)
    q = row['input']['query']
    if q.get('op') not in ('AND', 'OR') or q['args'][0].get('kind') != 'prior':
        raise ValueError('cross-stage grammar shape')
    for index, name in enumerate(('old_contrast', 'new_contrast')):
        altered = witness[name]
        validate_lesson(altered)
        expected = k.op(q['op'], *[k.op('NOT', a) if i == index else a for i, a in enumerate(q['args'])])
        if altered['input'] != k.record(row['input']['world'], expected) or altered['gold'] == row['gold']:
            raise ValueError('inactive or unbound causal witness')
    return witness


def compile_exercise(spec, rng, excluded, *, varied=False):
    validate_spec(spec)
    for _ in range(5000):
        try:
            w = data.make_world(spec['stage'], rng, varied)
            a = old_expression(w, spec['old_arm'], rng)
            b = data.query(spec['family'], w, rng)
            left, right = (k.independent_evaluate(k.record(w, q)) for q in (a, b))
            if left != right or left not in ('TRUE', 'FALSE'): continue
            gate = 'AND' if left == 'TRUE' else 'OR'
            family = f'cross:U{1 + ARMS.index(spec["old_arm"])}+U{spec["stage"]}:{spec["family"]}'
            r = data.row(k.record(w, k.op(gate, a, b)), spec['stage'], family)
            witness = {name: data.row(k.record(w, k.op(gate, *[
                k.op('NOT', operand) if i == index else operand for i, operand in enumerate((a, b))])),
                spec['stage'], family + ':' + name) for index, name in enumerate(('old_contrast', 'new_contrast'))}
            ids = {r['id'], *(p['id'] for p in witness.values())}
            if len(ids) != 3 or ids & excluded: continue
            validate_witness(r, witness)
        except ValueError:
            continue
        excluded.update(ids)
        return r, dict(witness, spec_id=spec['id'], base=r['id'])
    raise ValueError('grammar could not instantiate independent causal branches')
