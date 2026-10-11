"""Pinned live-inference microscope; formal traces never impersonate the learner."""
from __future__ import annotations

import argparse
import copy
import json
from pathlib import Path
import subprocess

import torch

from . import ROOT
from .codec import VERSION as CODEC_VERSION, decode, encode
from .data import audit_cases, composition, frozen_corpus, known_cases
from .model import load_checkpoint, predict
from .run import file_hash, write_json
from .semantics import SemanticError, canonical, digest, evaluate, negate, normalize, sid

VERSION = "alpha-microscope-0.1.0"


def fixture_registry():
    return json.loads((ROOT / "fixtures/alpha/microscope.json").read_text())


def validate_intervention(before, after, factor):
    a, b = normalize(before), normalize(after)
    if a["abi"] != b["abi"]:
        raise ValueError("intervention ABI")
    if factor == "evidence":
        if a["query"] != b["query"] or any(a["world"][k] != b["world"][k] for k in ("entities", "sources")):
            raise ValueError("evidence intervention changed unrelated fields")
        x = {canonical(f) for f in a["world"]["facts"]}
        y = {canonical(f) for f in b["world"]["facts"]}
        if len(x ^ y) != 1:
            raise ValueError("evidence intervention must add/remove exactly one record")
    else:
        if a["world"] != b["world"]:
            raise ValueError("query intervention changed world")
        q, r = a["query"], b["query"]
        if factor == "role_assignment":
            if q["op"] != sid("relation") or r != dict(q, args=list(reversed(q["args"]))):
                raise ValueError("role intervention")
        elif factor == "negation":
            if r != negate(q):
                raise ValueError("negation intervention")
        elif factor == "scope":
            if q["op"] != sid("not") or q["args"][0]["op"] != sid("exists"):
                raise ValueError("scope source")
            inner = q["args"][0]
            if r != dict(inner, body=negate(inner["body"])):
                raise ValueError("scope intervention")
        else:
            raise ValueError("unsupported intervention factor")


def delta(before, after, factor):
    validate_intervention(before, after, factor)
    a, b = normalize(before), normalize(after)
    if factor == "evidence":
        x = {canonical(f) for f in a["world"]["facts"]}
        y = {canonical(f) for f in b["world"]["facts"]}
        return {"factor": factor, "added_facts": [json.loads(f) for f in sorted(y - x)],
                "removed_facts": [json.loads(f) for f in sorted(x - y)], "unrelated_fields_preserved": True}
    return {"factor": factor, "before_query": a["query"], "after_query": b["query"],
            "world_unchanged": True, "unrelated_fields_preserved": True}


def render_query(q):
    op = q["op"].rsplit(":", 1)[-1]
    if op in ("relation", "equal"):
        a, b = [t["id"].rsplit(":", 1)[-1] for t in q["args"]]
        return f"R(source={a}, target={b})" if op == "relation" else f"({a} = {b})"
    if op == "not":
        return "NOT[" + render_query(q["args"][0]) + "]"
    if op in ("and", "or"):
        return "(" + (" " + op.upper() + " ").join(render_query(a) for a in q["args"]) + ")"
    return op.upper() + " x[" + render_query(q["body"]) + "]"


def render_world(w):
    facts = []
    for f in w["facts"]:
        a, b = [f["roles"][k].rsplit(":", 1)[-1] for k in ("source", "target")]
        polarity, source = [f[k].rsplit(":", 1)[-1] for k in ("polarity", "source")]
        facts.append(f"{polarity} R({a}->{b}) by {source}")
    return "domain={a,b}; " + ("; ".join(facts) if facts else "no evidence")


def replay(run_directory: Path):
    fixture = fixture_registry()
    binding = fixture["bindings"]
    path = run_directory / "model.pt"
    if file_hash(path) != binding["checkpoint_file_sha256"]:
        raise ValueError("unpinned checkpoint; no substitute permitted")
    for source, expected in binding["training_source_hashes"].items():
        if file_hash(ROOT / source) != expected:
            raise ValueError("frozen training source drift: " + source)
    model, payload = load_checkpoint(path)
    if payload["state_sha256"] != binding["final_state_sha256"] or not payload["metadata"].get("trained"):
        raise ValueError("trained model identity")
    corpus = frozen_corpus()
    if digest(corpus["split_manifest"]) != binding["split_manifest_sha256"]:
        raise ValueError("heldout split identity")
    corpus_by_semantic = {digest(r["semantic"]): r for r in corpus["cases"]}
    train_patterns = set(corpus["split_manifest"]["splits"]["TRAIN"]["patterns"])
    cases_by_id = {c["id"]: c for c in fixture["cases"]}
    results = []
    for case in fixture["cases"]:
        s = normalize(case["semantic"])
        answer = evaluate(s)
        if answer != case["expected"]:
            raise ValueError("showcase oracle expectation: " + case["id"])
        neural = predict(model, [s])[0]  # Every displayed answer comes from pinned saved parameters.
        tokens = encode(s)
        if decode(tokens) != s:
            raise ValueError("showcase codec information loss")
        entry = corpus_by_semantic.get(digest(s))
        pattern = composition(s["query"])
        heldout = pattern not in train_patterns
        if heldout and (entry is None or entry["split"] != "HELDOUT"):
            # The intentionally wrong candidate is a new candidate path, not a
            # scored corpus holdout. Preserve that distinction explicitly.
            heldout = False
        changes = None
        if "parent" in case:
            changes = delta(cases_by_id[case["parent"]]["semantic"], s, case["factor"])
        results.append({"id": case["id"], "semantic": s, "semantic_sha256": digest(s),
                        "world_id": digest(s["world"]), "query_id": digest(s["query"]),
                        "rendered_world": render_world(s["world"]), "rendered_query": render_query(s["query"]),
                        "rendering_provenance": "deterministic display; canonical semantic object is learner input",
                        "generic_typed_rendering": canonical(s).decode(),
                        "alternate_rendering_provenance": "information-matched JSON display; not a separately trained comparator",
                        "codec": {"version": CODEC_VERSION, "nonpadding_tokens": len(tokens),
                                  "token_sequence_sha256": digest(tokens), "roundtrip_verified": True},
                        "oracle": {"expected": case["expected"], "actual": answer,
                                   "provenance": "formal Belnap-Dunn finite evaluator"},
                        "neural": neural, "status": "PASS" if neural["prediction"] == answer else "FAIL",
                        "parent": case.get("parent"), "semantic_delta": changes,
                        "selection_provenance": case["selection_provenance"],
                        "composition": pattern, "withheld_from_train": heldout,
                        "split_evidence": {"corpus_id": entry["id"] if entry else None,
                           "membership": entry["split"] if entry else "candidate path outside scored corpus",
                           "split_manifest_sha256": binding["split_manifest_sha256"],
                           "pattern_in_train": pattern in train_patterns},
                        "explanation": "Oracle describes the declared evidence and logical composition. Neural logits expose a prediction, without an intermediate explanation interface.",
                        "explanation_provenance": fixture["explanation_provenance"]})
    wrong = fixture["wrong_candidate_path"]
    def query_answer(q):
        return evaluate(dict(wrong["intended"], query=q))
    intended_relation = query_answer(wrong["intended_relation"])
    candidate_relation = query_answer(wrong["candidate_relation"])
    wrong_path = {"provenance": wrong["provenance"],
                  "intended_semantic": wrong["intended"], "candidate_semantic": wrong["candidate"],
                  "intended_relation": wrong["intended_relation"], "candidate_relation": wrong["candidate_relation"],
                  "relation_identity_correct": wrong["intended_relation"] == wrong["candidate_relation"],
                  "relation_oracle_intended": intended_relation, "relation_oracle_candidate": candidate_relation,
                  "relation_consequence_correct": intended_relation == candidate_relation,
                  "unchanged_downstream_consequence": query_answer(wrong["unchanged_consequence"]),
                  "final_oracle_intended": evaluate(wrong["intended"]),
                  "final_oracle_candidate": evaluate(wrong["candidate"]),
                  "terminal_verdict_correct": evaluate(wrong["intended"]) == evaluate(wrong["candidate"]),
                  "neural_intermediate": None, "neural_intermediate_status": fixture["neural_intermediate_status"]}
    rejected = []
    for case in fixture["rejected_paths"]:
        try:
            predict(model, [case["semantic"]])
        except SemanticError as error:
            if error.code != case["expected_error"]:
                raise
            rejected.append({**case, "status": "REJECTED", "error": error.code,
                             "neural_status": "NOT_RUN: typed codec refused unsupported semantic input"})
        else:
            raise ValueError("unsupported path silently accepted")
    corrupted = copy.deepcopy(known_cases())
    next(c for c in corrupted if c["id"] == "K03-unknown")["expected"] = "FALSE"
    try:
        audit_cases(corrupted)
    except ValueError as error:
        defect = {"injected": "K03 UNKNOWN->FALSE label", "detected": True, "diagnostic": str(error),
                  "restored_expected": "UNKNOWN", "provenance": "formal regression check; not a neural repair claim"}
    else:
        raise ValueError("injected label defect escaped detection")
    run = json.loads((ROOT / "docs/evidence/alpha/epoch-01/run.json").read_text())
    original = fixture["cases"][0]["semantic"]
    reordered = copy.deepcopy(original)
    reordered["world"]["facts"].reverse()
    original_output = predict(model, [original])[0]
    reordered_output = predict(model, [reordered])[0]
    equivalence = {"original_surface": original, "reordered_surface": reordered,
                   "canonical_identity_equal": digest(normalize(original)) == digest(normalize(reordered)),
                   "compiled_tokens_equal": encode(original) == encode(reordered),
                   "oracle_original": evaluate(original), "oracle_reordered": evaluate(reordered),
                   "neural_original": original_output, "neural_reordered": reordered_output,
                   "provenance": "live inference on meaning-preserving evidence-order renderings; no causal comparison"}
    code_commit = subprocess.check_output(["git", "log", "-1", "--format=%H", "--", "bilqis_alpha/microscope.py"], cwd=ROOT, text=True).strip()
    return {"version": VERSION, "fixture_version": fixture["version"], "fixture_sha256": digest(fixture),
            "bindings": binding, "replay_code_sha256": file_hash(Path(__file__)),
            "replay_code_commit": code_commit or "uncommitted; file hash identifies code",
            "training_architecture": run["architecture"], "resources": run["resources"],
            "cases": results, "wrong_candidate_path": wrong_path, "rejected_paths": rejected,
            "label_defect_check": defect, "missing": run["unsupported"],
            "equivalent_representations": equivalence,
            "neural_intermediate_status": fixture["neural_intermediate_status"],
            "scientific_status": "Exploratory ALPHA; partial learning with visible failures; no SYS-01 or causal efficiency claim"}


def compare_replay(actual, expected):
    # Exclude Git head: evidence/documentation commits do not change inference.
    for key in ("version", "fixture_sha256", "bindings", "replay_code_sha256", "wrong_candidate_path", "rejected_paths", "label_defect_check"):
        if actual[key] != expected[key]:
            raise ValueError("replay identity/trace mismatch: " + key)
    if len(actual["cases"]) != len(expected["cases"]):
        raise ValueError("replay case count")
    for a, b in zip(actual["cases"], expected["cases"]):
        for k in ("id", "semantic_sha256", "oracle", "status", "semantic_delta", "split_evidence"):
            if a[k] != b[k]:
                raise ValueError("replay case mismatch: " + a["id"] + ":" + k)
        compare_prediction(a["neural"], b["neural"])
    a, b = actual["equivalent_representations"], expected["equivalent_representations"]
    for key in a:
        if key.startswith("neural_"):
            compare_prediction(a[key], b[key])
        elif a[key] != b[key]:
            raise ValueError("equivalence replay mismatch: " + key)


def compare_prediction(actual, expected):
    if actual["prediction"] != expected["prediction"]:
        raise ValueError("replay prediction mismatch")
    for key in ("logits", "probabilities"):
        torch.testing.assert_close(torch.tensor(actual[key]), torch.tensor(expected[key]), atol=1e-6, rtol=0)


def display(result):
    print(result["scientific_status"])
    print("Checkpoint:", result["bindings"]["checkpoint_file_sha256"])
    print("Model training code:", result["bindings"]["training_code_commit"])
    print("Replay code:", result["version"], result["replay_code_sha256"])
    print("Replay code commit:", result["replay_code_commit"])
    print("Fixture:", result["fixture_version"], result["fixture_sha256"])
    print("Semantic registry:", result["bindings"]["semantic_manifest_sha256"])
    print("Canonical IDs use urn:bilqis:alpha:cogal:<identity>; role order is source -> target.")
    print("Explanations: deterministic/formal code. Model exposes final logits, no intermediate reasoning.")
    for case in result["cases"]:
        print(f"\n{case['id']} [{case['status']}] pattern={case['composition']} heldout={case['withheld_from_train']}")
        print("  world", case["world_id"], "query", case["query_id"])
        print(" ", case["rendered_world"])
        print(" ", case["rendered_query"])
        print("  neural", case["neural"]["prediction"], "probabilities(T,F,U,C)=", [round(x, 4) for x in case["neural"]["probabilities"]],
              "| formal oracle", case["oracle"]["actual"])
        if case["semantic_delta"]:
            print("  exact canonical delta", json.dumps(case["semantic_delta"], sort_keys=True))
        if case["withheld_from_train"]:
            print("  withheld membership", json.dumps(case["split_evidence"], sort_keys=True))
    p = result["wrong_candidate_path"]
    print("\nWrong candidate path (independently evaluated, not a network intermediate):")
    print("  relation identity correct:", p["relation_identity_correct"], "relation outcomes:", p["relation_oracle_intended"], "->", p["relation_oracle_candidate"])
    print("  downstream:", p["unchanged_downstream_consequence"], "terminal oracle:", p["final_oracle_intended"], "=", p["final_oracle_candidate"])
    print(" ", result["neural_intermediate_status"])
    print("Rejected paths:", json.dumps(result["rejected_paths"]))
    print("Injected defect:", json.dumps(result["label_defect_check"]))
    e = result["equivalent_representations"]
    print("Equivalent renderings: evidence order changes; canonical/tokens equal:", e["canonical_identity_equal"], e["compiled_tokens_equal"],
          "neural:", e["neural_original"]["prediction"], "=", e["neural_reordered"]["prediction"], "oracle:", e["oracle_original"])
    print("Full canonical JSON and information-matched typed display are available with --json.")
    print("Resource receipt:", json.dumps(result["resources"]))
    print("Unsupported families:", json.dumps(result["missing"]))
    print("Result:", sum(c["status"] == "PASS" for c in result["cases"]), "passed;",
          sum(c["status"] == "FAIL" for c in result["cases"]), "failed; live inference preserved.")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--run", type=Path, default=ROOT / "runs/alpha/epoch-01")
    parser.add_argument("--json", action="store_true")
    parser.add_argument("--record", type=Path)
    parser.add_argument("--verify", type=Path)
    args = parser.parse_args()
    result = replay(args.run)
    if args.verify:
        compare_replay(result, json.loads(args.verify.read_text()))
    if args.record:
        if args.record.exists():
            raise ValueError("replay receipt exists; preserve the original")
        write_json(args.record, result)
    if args.json:
        print(json.dumps(result, indent=2))
    else:
        display(result)


if __name__ == "__main__":
    main()
