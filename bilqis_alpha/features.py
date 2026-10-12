"""Inspectable structural features -> fixed DCT width transform -> FP32 rows."""
from __future__ import annotations

import math

import torch

from .codec import token_manifest
from .semantics import digest, registry, sid

VERSION = "alpha-structural-features-0.1.0"
INITIALIZER = "alpha-dct-initializer-0.1.0"


def tensor_hash(tensor: torch.Tensor) -> str:
    import hashlib
    t = tensor.detach().cpu().contiguous()
    return hashlib.sha256(str(t.dtype).encode() + str(tuple(t.shape)).encode() + t.numpy().tobytes()).hexdigest()


def feature_map():
    entries = registry()["entries"]
    sparse = {}
    for r in entries:
        v = {"family:" + r["family"]: 1., "type:" + r["type"]: 1.,
             "tranche:" + r["tranche"]: 1., "arity:" + str(r["arity"]): 1.}
        for role in r["roles"]:
            v["argument:" + role] = 1.
        for dependency in r["dependencies"]:
            v["dependency:" + dependency] = .5
        for flag, key in (("binding", "binding"), ("symmetric", "symmetric"), ("role_sensitive", "role-sensitive"),
                          ("bivalent", "bivalent"), ("support", "evidence-support"), ("refute", "evidence-refute")):
            if flag in r:
                v[key] = float(r[flag])
        # Contrast/dual axes are derived from registry edges, never token ordinals.
        for edge in ("contrast", "dual", "inverse"):
            if edge in r:
                endpoints = sorted({r["id"], r[edge]})
                v[edge + ":" + "|".join(endpoints)] = 1. if r["id"] == endpoints[0] else -1.
        if "instance" in r:
            v["instance:" + r["id"]] = 1.
        table = registry()["semantics"]["truth_tables"]["operators"].get(r["id"])
        if table:
            flat = table if isinstance(table[0], str) else [state for row in table for state in row]
            for i, state in enumerate(flat):
                # Independent support/refute channels describe each frozen truth function.
                v[f"truth-function:{i}:support"] = float(state in ("TRUE", "CONFLICT"))
                v[f"truth-function:{i}:refute"] = float(state in ("FALSE", "CONFLICT"))
        sparse[r["id"]] = v
    basis = sorted({key for row in sparse.values() for key in row})
    ids = sorted(sparse)
    phi = torch.tensor([[sparse[i].get(k, 0.) for k in basis] for i in ids], dtype=torch.float64)
    manifest = {"version": VERSION, "basis": basis, "semantic_ids": ids,
                "vectors": phi.tolist(), "registry_sha256": digest(registry()),
                "meaning": "typed family/arity/roles, prerequisite edges, signed dual/contrast and independent evidence channels",
                "truth_weight_boundary": "features describe semantic relations; no truth state is a ternary weight value"}
    return ids, phi, manifest


def compile_embeddings(width: int, profile="semantic_aligned", seed=102, *, tokens=None):
    if type(width) is not int or width < 1 or profile not in ("semantic_aligned", "iid_random", "semantic_permuted"):
        raise ValueError("initializer width/profile")
    m = token_manifest()
    tokens = list(m["tokens"] if tokens is None else tokens)
    if not tokens or tokens[0] != sid("pad") or len(tokens) != len(set(tokens)) or set(tokens) != set(m["tokens"]):
        raise ValueError("token identity bijection")
    ids, phi, features = feature_map()
    n = phi.shape[1]
    # A fixed real-valued cosine basis, normalized by n. Repetition for widths > n
    # is explicit; this alpha uses width < n and does not claim lossless projection.
    rows = torch.arange(n, dtype=torch.float64)[:, None] + .5
    cols = torch.arange(width, dtype=torch.float64)[None, :]
    projection = torch.cos(math.pi * rows * cols / n) * math.sqrt(2. / n)
    projection[:, 0] /= math.sqrt(2.)
    aligned = phi @ projection
    aligned = (aligned / aligned.square().mean(1, keepdim=True).sqrt().clamp_min(1e-12) * .02).float()
    by_id = {s: row for s, row in zip(ids, aligned)}
    table = torch.stack([by_id[t] for t in tokens])
    table[0].zero_()
    assignment = {t: t for t in tokens}
    if profile == "semantic_permuted":
        # Nonpadding cyclic bijection. Multiset preserved; semantic alignment broken.
        assignment.update({t: tokens[1:][(i + 1) % (len(tokens) - 1)] for i, t in enumerate(tokens[1:])})
        table = torch.stack([torch.zeros(width) if t == sid("pad") else by_id[assignment[t]] for t in tokens])
    elif profile == "iid_random":
        table = torch.randn(len(tokens), width, generator=torch.Generator().manual_seed(seed)) * .02
        table[0].zero_()
    manifest = {"version": INITIALIZER, "profile": profile, "seed": seed,
                "semantic_registry_sha256": digest(registry()), "token_abi_sha256": digest(m),
                "feature_map_version": VERSION, "feature_map_sha256": digest(features),
                "width": width, "feature_dimensions": n, "parameter_class": "token_embedding",
                "transform": "phi @ fixed DCT-II prefix; per-row RMS normalized to 0.02; FP32 cast",
                "projection_sha256": tensor_hash(projection), "tensor_sha256": tensor_hash(table),
                "token_assignment": assignment, "padding": "exact zero row; excluded from semantic permutation",
                "dtype": "torch.float32", "embedding_quantized": False, "embedding_geometry_distortion": 0.,
                "stochastic_embedding_residual": False, "scratch_no_pretrained_weights": True,
                "other_parameters": "seeded normal(0,0.02); LayerNorm defaults; no inherited weights",
                "tolerance": {"atol": 1e-7, "rtol": 0.}}
    return table, manifest
