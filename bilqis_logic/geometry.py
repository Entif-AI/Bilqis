"""Project-owned formal features, fixed DCT projection, and matched controls."""
from __future__ import annotations

import math

import torch

from .kernel import OPERATORS, TABLES, TOKENS, VERSION, digest, token_manifest

FEATURE_VERSION = "cogal-boolean-features-0.1.0"
INITIALIZER_VERSION = "cogal-dct-0.1.0"


def tensor_hash(tensor):
    import hashlib
    t = tensor.detach().cpu().contiguous()
    return hashlib.sha256(str(t.dtype).encode() + str(tuple(t.shape)).encode() + t.numpy().tobytes()).hexdigest()


def registry():
    nodes = []
    for identity in TOKENS:
        node = {"id": identity, "family": identity.split(".")[0], "arity": 0, "type": "syntax"}
        if identity.startswith("cogal.value."):
            node.update(type="Boolean", subtype="literal")
        elif identity.startswith("cogal.variable."):
            node.update(type="Boolean", subtype="variable")
        elif identity.startswith("cogal.operator."):
            op = identity.split(".")[-1]
            arity = OPERATORS[op]
            node.update(type="Boolean->Boolean" if arity == 1 else "Boolean*Boolean->Boolean",
                        subtype="operator", arity=arity, truth_table=TABLES[op],
                        roles=["operand"] if arity == 1 else ["left", "right"],
                        symmetric=arity == 2 and TABLES[op][1] == TABLES[op][2],
                        directional=arity == 2 and TABLES[op][1] != TABLES[op][2])
        nodes.append(node)
    edges = [{"left": "cogal.value.false", "right": "cogal.value.true", "relation": "complement"}]
    binary = [op for op, arity in OPERATORS.items() if arity == 2]
    for i, left in enumerate(binary):
        for right in binary[i + 1:]:
            if TABLES[left] == TABLES[right]:
                relation = "equivalent"
            elif all(a != b for a, b in zip(TABLES[left], TABLES[right])):
                relation = "complement"
            else:
                continue
            edges.append({"left": "cogal.operator." + left, "right": "cogal.operator." + right,
                          "relation": relation})
    return {"version": VERSION, "semantics": "two-valued classical Boolean",
            "table_order": {"unary": [True, False], "binary": [[True, True], [True, False], [False, True], [False, False]]},
            "nodes": nodes, "edges": edges,
            "validation": "exhaustive frozen truth tables; independent operational Boolean evaluator",
            "scope": "Boolean literals, P/Q and seven operators; no T2-T4 or many-valued semantics"}


def feature_map():
    graph = registry()
    sparse = {}
    for node in graph["nodes"]:
        row = {"identity:" + node["id"]: 1., "family:" + node["family"]: 1.,
               "type:" + node["type"]: 1., "arity:" + str(node["arity"]): 1.}
        if "subtype" in node:
            row["subtype:" + node["subtype"]] = 1.
        for role in node.get("roles", []):
            row["role:" + role] = 1.
        if node.get("symmetric"):
            row["operator:symmetric"] = 1.
        if node.get("directional"):
            row["operator:directional"] = 1.
        for i, value in enumerate(node.get("truth_table", [])):
            # These channels describe primitive truth functions, not any example's answer.
            row[f"truth-signature:{i}:{str(value).lower()}"] = 1.
        for edge in graph["edges"]:
            if node["id"] in (edge["left"], edge["right"]):
                row[edge["relation"] + ":" + "|".join(sorted((edge["left"], edge["right"])))] = (
                    1. if edge["relation"] == "equivalent" or node["id"] == edge["left"] else -1.)
        sparse[node["id"]] = row
    basis = sorted({key for row in sparse.values() for key in row})
    matrix = torch.tensor([[sparse[s].get(k, 0.) for k in basis] for s in TOKENS], dtype=torch.float64)
    manifest = {"version": FEATURE_VERSION, "basis": basis, "semantic_ids": TOKENS,
                "features": matrix.tolist(), "registry_sha256": digest(graph),
                "truth_weight_boundary": "truth values are semantic identities; signed contrasts are features, not ternary truth states",
                "per_example_gold_or_reduced_expression_features": False}
    return matrix, manifest


def compile_embeddings(width, profile="semantic_aligned", seed=111):
    if type(width) is not int or width < 1 or profile not in ("semantic_aligned", "iid_random", "semantic_permuted"):
        raise ValueError("initializer width/profile")
    phi, features = feature_map()
    n = phi.shape[1]
    columns = min(n, width)
    projection = torch.zeros(n, width, dtype=torch.float64)
    projection[:, :columns] = torch.cos(math.pi * (torch.arange(n, dtype=torch.float64)[:, None] + .5)
                                          * torch.arange(columns, dtype=torch.float64)[None, :] / n) * math.sqrt(2. / n)
    projection[:, 0] /= math.sqrt(2.)
    aligned = phi @ projection
    aligned = (aligned / aligned.square().mean(1, keepdim=True).sqrt().clamp_min(1e-12) * .02).float()
    aligned[0].zero_()
    assignment = list(range(len(TOKENS)))
    if profile == "semantic_permuted":
        assignment[1:] = assignment[2:] + [1]
    table = aligned[assignment].clone()
    if profile == "iid_random":
        table = torch.randn(len(TOKENS), width, generator=torch.Generator().manual_seed(seed)) * .02
        table[0].zero_()
    manifest = {"version": INITIALIZER_VERSION, "profile": profile, "seed": seed,
                "registry_sha256": digest(registry()), "token_abi_sha256": digest(token_manifest()),
                "feature_version": FEATURE_VERSION, "feature_sha256": digest(features),
                "width": width, "feature_dimensions": n, "transform": "fixed orthonormal DCT-II prefix; zero extension if width exceeds feature count; row RMS 0.02; FP32 cast",
                "projection_sha256": tensor_hash(projection), "tensor_sha256": tensor_hash(table),
                "token_assignment": {TOKENS[i]: TOKENS[j] for i, j in enumerate(assignment)},
                "padding": "exact zero, excluded from semantic permutation",
                "stochastic_embedding_residual": False, "embedding_quantized": False,
                "pretrained_weights_vectors_hidden_states": False,
                "other_parameters": "seeded normal(0,0.02); LayerNorm native defaults",
                "tolerance": {"atol": 1e-7, "rtol": 0.}}
    return table, manifest
