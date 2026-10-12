"""Teacher authority is limited to validated proposals and DEV scheduling."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path

from bilqis_development import kernel
from bilqis_development.registry import SOURCES
from bilqis_spiral.sampler import MIX, check_row, dev_signals

ROOT = Path(__file__).resolve().parents[1]
CONTRACT = Path(__file__).with_name('policy.json')


def load_policy():
    p = json.loads(CONTRACT.read_text())
    if p['identity'] != 'bilqis.developmental-teacher/1.0.0' or p['batch'] != MIX:
        raise ValueError('unsupported teacher policy')
    if p['coverage'] != {'weak_old_min': 2, 'weak_recent_min': 2, 'weak_family_max': 3, 'cross_per_recent_stage': 4}:
        raise ValueError('unsupported coverage contract')
    return p


def source_text(source):
    if source not in SOURCES:
        raise ValueError('unqualified semantic source')
    return json.loads((ROOT / 'docs/u5-u6/sources' / f'{source}.json').read_text())['body']


def source_manifest():
    return {s: {'url': SOURCES[s], 'sha256': hashlib.sha256(
        (ROOT / 'docs/u5-u6/sources' / f'{s}.json').read_bytes()).hexdigest()} for s in SOURCES}


def novelty(candidate, catalog):
    """Classify explicit registry evidence; never infer identity from similarity."""
    known = set(catalog['tokens'])
    identity = candidate.get('identity')
    category, reason = 'DEFERRED', 'source or representation evidence needed'
    qualified = candidate.get('source') in SOURCES
    if identity in known:
        category, reason = 'KNOWN_ID', 'exact canonical identity'
    elif candidate.get('referent') in known and candidate.get('surface') == candidate['referent'].rsplit('.', 1)[-1]:
        category, reason = 'SURFACE_ALIAS', 'canonical terminal token spelling'
    elif 'record' in candidate and qualified:
        try:
            kernel.validate_record(candidate['record'])
            encoded = kernel.encode(candidate['record'])
            if kernel.decode(encoded) != candidate['record'] or any(kernel.TOKENS[i] not in known for i in encoded):
                raise ValueError('noncanonical encoding')
            category, reason = 'COMPOSITION_ONLY', 'existing typed compositional closure'
        except ValueError:
            reason = 'unsupported or ill-typed composition; review required'
    elif candidate.get('history') in ('rejected', 'deferred', 'unresolved'):
        reason = 'prior disposition requires independent review'
    elif qualified and candidate.get('gap'):
        excerpt = candidate.get('source_excerpt', '')
        if len(excerpt) >= 24 and excerpt in source_text(candidate['source']):
            category, reason = 'UNRESOLVED_SEMANTIC_GAP', 'source-located residual with no admitted representation'
    return {'category': category, 'reason': reason, 'eg2_permitted': category == 'UNRESOLVED_SEMANTIC_GAP'}


def validate_lesson(row):
    allowed = set(SOURCES.values())
    if row.get('source_locator') not in allowed:
        raise ValueError('lesson source is not qualified')
    return check_row(row)


def feedback(scores, corpus, baseline=None):
    """Only exact inherited DEV predictions can drive the teacher or sampler."""
    if set(scores) != set(corpus['stages']):
        raise ValueError('DEV stage boundary')
    for stage, data in corpus['stages'].items():
        if set(scores[stage]) != {'varied', 'composite'}:
            raise ValueError('DEV split boundary')
        for split in ('varied', 'composite'):
            expected = [(r['id'], r['gold'], r['family']) for r in data['eval'][split]]
            actual = [(r['id'], r['gold'], r['family']) for r in scores[stage][split]['predictions']]
            if actual != expected:
                raise ValueError('DEV identity/gold/family boundary')
    return dev_signals(scores, baseline)
