"""Epoch-local control codec and role-position geometry; no helper vectors."""
import math
import torch

from .codec import token_manifest as alpha_tokens
from .features import feature_map as alpha_features, tensor_hash
from .semantics import ABI, digest, sid

VERSION = 'decision-structural-features-0.1.0'
INITIALIZER = 'decision-dct-initializer-0.1.0'
CODEC = 'decision-control-codec-0.1.0'
CONTROL = ('state', 'candidate', 'orient', 'bind', 'read', 'fold', 'add', 'remove',
           'active', 'resolved', 'ambiguous', 'unsupported', 'missing', 'outside',
           'other', 'insufficient', 'clarify', 'abstain', 'operands', 'selected')


def control(name):
    if name not in CONTROL:
        raise ValueError('UNKNOWN_CONTROL_IDENTITY')
    return 'urn:bilqis:decision-epoch-02:' + name


def token_manifest():
    tokens = alpha_tokens()['tokens'] + sorted(control(n) for n in CONTROL)
    return {'version': CODEC, 'tokens': tokens, 'padding_id': 0,
            'semantic_abi': ABI, 'alpha_codec_sha256': digest(alpha_tokens()),
            'control_authority': 'experimental #70 navigation envelope; no new COGAL primitives',
            'oov_policy': 'reject'}


def feature_map():
    ids, old, original = alpha_features()
    rows = {s: {k: float(v) for k, v in zip(original['basis'], row) if v}
            for s, row in zip(ids, old.tolist())}
    for name, position in (('role-source', 1.), ('role-target', -1.)):
        rows[sid(name)]['role-position:directed'] = position
    for name, position in (('role-left', 1.), ('role-right', -1.)):
        rows[sid(name)]['role-position:ordered-display'] = position
    for name in ('role-binder', 'exists', 'forall', 'variable'):
        rows[sid(name)]['role-position:binder'] = 1.
    for name in CONTROL:
        rows[control(name)] = {'family:navigation-control': 1., 'control:' + name: 1.}
    basis = sorted({k for row in rows.values() for k in row})
    ids = sorted(rows)
    phi = torch.tensor([[rows[s].get(k, 0.) for k in basis] for s in ids], dtype=torch.float64)
    manifest = {'version': VERSION, 'basis': basis, 'semantic_ids': ids,
                'vectors': phi.tolist(), 'alpha_features_sha256': digest(original),
                'role_position_authority': '#7 ordered roles, #81/#62 deterministic feature projection',
                'pretrained_vectors': False, 'historical_features_mutated': False}
    return ids, phi, manifest


def compile_embeddings(width, seed=202):
    if type(width) is not int or width < 8:
        raise ValueError('DECISION_GEOMETRY_WIDTH')
    ids, phi, features = feature_map()
    n = phi.shape[1]
    rows = torch.arange(n, dtype=torch.float64)[:, None] + .5
    cols = torch.arange(width, dtype=torch.float64)[None, :]
    projection = torch.cos(math.pi * rows * cols / n) * math.sqrt(2. / n)
    projection[:, 0] /= math.sqrt(2.)
    mapped = phi @ projection
    mapped = (mapped / mapped.square().mean(1, keepdim=True).sqrt().clamp_min(1e-12) * .02).float()
    by_id = dict(zip(ids, mapped))
    tokens = token_manifest()['tokens']
    table = torch.stack([by_id[t] for t in tokens])
    table[0].zero_()
    if torch.equal(table[tokens.index(sid('role-source'))], table[tokens.index(sid('role-target'))]):
        raise ValueError('ROLE_GEOMETRY_COLLISION')
    manifest = {'version': INITIALIZER, 'feature_version': VERSION, 'codec_version': CODEC,
                'semantic_abi': ABI, 'token_sha256': digest(token_manifest()),
                'feature_sha256': digest(features), 'projection_sha256': tensor_hash(projection),
                'tensor_sha256': tensor_hash(table), 'width': width, 'seed': seed,
                'transform': 'fixed DCT-II prefix, row RMS 0.02, FP32; exact zero padding',
                'pretrained_vectors': False, 'other_parameters': 'seeded normal 0,0.02; no inherited weights'}
    return table, manifest
