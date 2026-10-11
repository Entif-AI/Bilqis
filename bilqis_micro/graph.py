"""Append-only semantic identities and row-local, stable keyed projection.

Incoming edges never rewrite an existing node's feature contract. New nodes may
refer to old nodes; existing outgoing features/edges and token IDs are immutable.
"""
from __future__ import annotations

import copy
import hashlib
import math

from bilqis_logic.kernel import TOKENS as BOOLEAN_TOKENS, OPERATORS, TABLES, digest
from bilqis_logic.geometry import tensor_hash

VERSION = "micro-typed-graph-0.1.0"
FEATURE_VERSION = "micro-keyed-features-0.1.0"
RULE = "micro.rule.parent_parent_grandparent"
ENTITIES = tuple("ABCDE")
RELATIONS = ("PARENT", "CHILD", "LINK", "GRANDPARENT")
STATES = ("FALSE", "TRUE", "UNKNOWN", "CONFLICT", "AMBIGUOUS")

EXTRA = (["micro.syntax." + s for s in ("world", "entities", "facts", "rules", "propositions", "reports", "interpretations", "query", "section_end")]
         + ["micro.entity." + e for e in ENTITIES]
         + ["micro.role." + r for r in ("source", "target", "mediator")]
         + ["micro.relation." + r for r in RELATIONS]
         + ["micro.quantifier.EXISTS", "micro.quantifier.FORALL", "micro.bound.0", "micro.bound.1",
            "micro.compare.EQ", "micro.compare.NEQ", "micro.compose", "micro.proof.entails",
            "micro.proof.rule_step", "micro.proof.countermodel", RULE]
         + ["micro.source.S" + str(i) for i in range(3)]
         + ["micro.proposition.J" + str(i) for i in range(3)]
         + ["micro.report.support", "micro.report.refute", "micro.interpretation.0", "micro.interpretation.1",
            "micro.state.UNKNOWN", "micro.state.CONFLICT", "micro.state.AMBIGUOUS",
            "micro.evidence.observe", "micro.evidence.NOT", "micro.evidence.AND", "micro.evidence.OR",
            "micro.proof.premise", "micro.proof.conclusion"])
TOKENS = list(BOOLEAN_TOKENS) + EXTRA
ID = {identity: i for i, identity in enumerate(TOKENS)}


def _node(identity):
    node = {"id": identity, "family": "syntax", "subtype": "delimiter", "signature": "Syntax", "arity": 0, "stage": 0, "edges": []}
    if identity.startswith("cogal.value."):
        node.update(family="Boolean", subtype="literal", signature="Boolean")
        other = "false" if identity.endswith("true") else "true"
        node["edges"] = [{"kind": "complement", "target": "cogal.value." + other}]
    elif identity.startswith("cogal.variable."):
        node.update(family="Boolean", subtype="free_variable", signature="Boolean")
    elif identity.startswith("cogal.operator."):
        op = identity.split(".")[-1]
        node.update(family="Boolean", subtype="operator", signature="Boolean->Boolean" if OPERATORS[op] == 1 else "Boolean*Boolean->Boolean",
                    arity=OPERATORS[op], truth_signature=TABLES[op], roles=["operand"] if OPERATORS[op] == 1 else ["left", "right"],
                    symmetric=OPERATORS[op] == 2 and TABLES[op][1] == TABLES[op][2], directional=op == "IMPLIES")
        for other, arity in OPERATORS.items():
            if other == op or arity != OPERATORS[op]:
                continue
            if TABLES[other] == TABLES[op]:
                node["edges"].append({"kind": "equivalent", "target": "cogal.operator." + other})
            elif all(a != b for a, b in zip(TABLES[other], TABLES[op])):
                node["edges"].append({"kind": "complement", "target": "cogal.operator." + other})
    elif identity.startswith("micro.entity."):
        node.update(family="entity", subtype="individual", signature="Entity", stage=1)
    elif identity.startswith("micro.role."):
        node.update(family="role", subtype=identity.split(".")[-1], signature="ArgumentRole", stage=1)
    elif identity.startswith("micro.relation."):
        name = identity.split(".")[-1]
        node.update(family="relation", subtype="binary", signature="Entity*Entity->Boolean", arity=2,
                    stage=3 if name == "GRANDPARENT" else 1, roles=["source", "target"], symmetric=name == "LINK", directional=name != "LINK")
        node["edges"] = [{"kind": "argument", "target": "micro.role." + r} for r in ("source", "target")]
        if name in ("PARENT", "CHILD"):
            node["edges"].append({"kind": "inverse", "target": "micro.relation." + ("CHILD" if name == "PARENT" else "PARENT")})
        if name == "GRANDPARENT":
            node["edges"] += [{"kind": "composition", "target": "micro.compose"}, {"kind": "prerequisite", "target": "micro.relation.PARENT"}]
    elif identity.startswith("micro.quantifier."):
        name = identity.split(".")[-1]
        node.update(family="quantifier", subtype=name, signature="(Entity->Boolean)->Boolean", arity=1, stage=2, binding="de-Bruijn-nearest-first", scope="finite-world-domain")
        node["edges"] = [{"kind": "binding", "target": "micro.bound.0"}, {"kind": "prerequisite", "target": "micro.relation.PARENT"}]
    elif identity.startswith("micro.bound."):
        node.update(family="binding", subtype="de_Bruijn_" + identity.split(".")[-1], signature="Entity", stage=2, scope="lexical")
    elif identity.startswith("micro.compare."):
        name = identity.split(".")[-1]
        node.update(family="identity", subtype=name, signature="Entity*Entity->Boolean", arity=2, symmetric=True, stage=1 if name == "EQ" else 2)
        node["edges"] = [{"kind": "exclusion", "target": "micro.compare." + ("NEQ" if name == "EQ" else "EQ")}]
    elif identity == "micro.compose":
        node.update(family="composition", subtype="two_hop", signature="Relation*Relation*Entity*Entity->Boolean", arity=4, stage=2, roles=["source", "mediator", "target"])
        node["edges"] = [{"kind": "prerequisite", "target": "micro.relation.PARENT"}, {"kind": "equivalent_form", "target": "micro.quantifier.EXISTS"}]
    elif identity in ("micro.proof.premise", "micro.proof.conclusion"):
        node.update(family="role", subtype=identity.split(".")[-1], signature="BooleanStatementRole", stage=3)
        node["edges"] = [{"kind": "argument", "target": "micro.proof.rule_step"}]
    elif identity.startswith("micro.proof.") or identity == RULE:
        name = identity.split(".")[-1]
        node.update(family="proof", subtype=name, signature="ProofContext->Boolean", stage=3,
                    arity={"entails":1,"rule_step":3,"countermodel":2}.get(name,0))
        node["edges"] = [{"kind": "prerequisite", "target": "micro.compose"}, {"kind": "prerequisite", "target": "cogal.operator.IMPLIES"}]
        if identity == RULE:
            node.update(signature="PARENT(x,y)*PARENT(y,z)->GRANDPARENT(x,z)", arity=2)
            node["edges"] += [{"kind": "premise", "target": "micro.relation.PARENT"}, {"kind": "conclusion", "target": "micro.relation.GRANDPARENT"}]
    elif identity.startswith("micro.source."):
        node.update(family="evidence", subtype="source", signature="EvidenceSource", stage=4)
    elif identity.startswith("micro.proposition."):
        node.update(family="evidence", subtype="proposition", signature="BooleanStatement", stage=4)
    elif identity.startswith("micro.report."):
        node.update(family="evidence", subtype=identity.split(".")[-1], signature="EvidencePolarity", stage=4)
        node["edges"] = [{"kind": "contrast", "target": "micro.report." + ("refute" if identity.endswith("support") else "support")}]
    elif identity.startswith("micro.interpretation."):
        node.update(family="evidence", subtype="live_interpretation", signature="Interpretation", stage=4)
    elif identity.startswith("micro.state."):
        node.update(family="evidence", subtype=identity.split(".")[-1], signature="EvidenceState", stage=4)
    elif identity.startswith("micro.evidence."):
        name = identity.split(".")[-1]
        signature = {"observe":"Proposition->Evidence", "NOT":"Evidence|Boolean->Evidence",
                     "AND":"(Evidence|Boolean)*(Evidence|Boolean)->Evidence", "OR":"(Evidence|Boolean)*(Evidence|Boolean)->Evidence"}[name]
        node.update(family="evidence", subtype=name, signature=signature, arity=1 if name in ("observe", "NOT") else 2, stage=4)
        target = "micro.proposition.J0" if name == "observe" else "cogal.operator." + name
        node["edges"] = [{"kind": "lift_of", "target": target}, {"kind": "prerequisite", "target": "micro.proof.entails"}]
    return node


def catalog():
    nodes = [_node(s) for s in TOKENS]
    return {"version": VERSION, "tokens": list(TOKENS), "nodes": nodes,
            "row_contract_sha256": {n["id"]: digest(n) for n in nodes},
            "coordinate_policy": "immutable row-local features; incoming edges do not alter old rows; append tokens only"}


def validate_catalog(graph):
    nodes, tokens = graph["nodes"], graph["tokens"]
    if (graph["version"] != VERSION or tokens != [n["id"] for n in nodes] or len(set(tokens)) != len(tokens)
            or tokens[:len(BOOLEAN_TOKENS)] != list(BOOLEAN_TOKENS)):
        raise ValueError("semantic/token identity history")
    for node in nodes:
        if graph["row_contract_sha256"].get(node["id"]) != digest(node):
            raise ValueError("semantic row contract changed")
        if any(e["target"] not in tokens for e in node["edges"]):
            raise ValueError("graph edge outside admitted identity map")


def append_catalog(prior, additions):
    validate_catalog(prior)
    result = copy.deepcopy(prior)
    for node in additions:
        if node["id"] in result["tokens"]:
            raise ValueError("existing semantic identity cannot be replaced")
        result["nodes"].append(copy.deepcopy(node))
        result["tokens"].append(node["id"])
        result["row_contract_sha256"][node["id"]] = digest(node)
    validate_catalog(result)
    return result


def features(node):
    row = {"identity:" + node["id"]: 1., "family:" + node["family"]: 1.,
           "subtype:" + node["subtype"]: 1., "signature:" + node["signature"]: 1., "arity:" + str(node["arity"]): 1.}
    for key in ("scope", "binding"):
        if key in node:
            row[key + ":" + node[key]] = 1.
    for role in node.get("roles", []):
        row["role:" + role] = 1.
    for key in ("symmetric", "directional"):
        if node.get(key):
            row[key] = 1.
    for index, value in enumerate(node.get("truth_signature", [])):
        row[f"truth-signature:{index}:{str(value).lower()}"] = 1.
    for edge in node["edges"]:
        row["typed-neighbor:" + edge["kind"] + ":" + edge["target"]] = .5
        if edge["kind"] in ("complement", "contrast", "exclusion", "inverse"):
            pair = sorted((node["id"], edge["target"]))
            row[edge["kind"] + ":" + "|".join(pair)] = 1. if node["id"] == pair[0] else -1.
    return row


def compile_embeddings(width, graph=None):
    import torch
    graph = catalog() if graph is None else graph
    validate_catalog(graph)
    if type(width) is not int or width < 1:
        raise ValueError("embedding width")
    sparse = {n["id"]: features(n) for n in graph["nodes"]}
    # Each feature's coordinates depend on its immutable key, never global basis size/order.
    cache = {}
    for key in sorted({k for row in sparse.values() for k in row}):
        signs = [1. if hashlib.sha256(f"{FEATURE_VERSION}|{key}|{column}".encode()).digest()[0] & 1 else -1.
                 for column in range(width)]
        cache[key] = torch.tensor(signs, dtype=torch.float64) / math.sqrt(width)
    rows = []
    for identity in graph["tokens"]:
        row = sum((cache[k] * value for k, value in sorted(sparse[identity].items())), torch.zeros(width, dtype=torch.float64))
        row = (row / row.square().mean().sqrt().clamp_min(1e-12) * .02).float()
        if identity == "syntax.pad":
            row.zero_()
        rows.append(row)
    table = torch.stack(rows)
    manifest = {"version": FEATURE_VERSION, "graph_sha256": digest(graph), "token_map_sha256": digest(graph["tokens"]),
                "features": sparse, "feature_sha256": digest(sparse), "width": width,
                "transform": "SHA256(version,feature-key,column) sign projection; row-local sum; RMS 0.02; FP32",
                "transform_seed": "fixed feature version namespace; no stochastic residual", "tensor_sha256": tensor_hash(table),
                "row_sha256": {s: tensor_hash(row) for s, row in zip(graph["tokens"], table)},
                "profile": "semantic_aligned", "pretrained_neural_transfer": False, "embedding_quantized": False,
                "padding": "exact zero", "append_stability": "old token IDs, descriptors, outgoing features and initial rows remain exact"}
    return table, manifest
