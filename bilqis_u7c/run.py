"""U7C: verified U6 continuation, English-only Kev and balanced grammar."""
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
import sys
import time

import torch

from bilqis_logic.kernel import canonical, digest
from bilqis_micro.run import optimizer_receipt
from bilqis_ref.model import state_hash
from bilqis_development import run as student
from bilqis_development.continuation import load, save
from bilqis_development.vendor.kev_teacher import KevTeacher
from bilqis_spiral import run as spiral
from bilqis_spiral.sampler import MIX, Sampler, build_pools, existing_ids
from bilqis_teacher.grammar import DEFINITIONS
from bilqis_teacher.policy import feedback, novelty, validate_lesson
from bilqis_teacher.battery import verify_trace
from bilqis_u7b.run import (preserved_start, frozen_u7_rows,
                            evaluation_inputs, score_all)
from .grammar import (ARMS, FAMILIES, accepted_specs, generate_split, audit_cohort)

ROOT, PARENT, CURRENT = spiral.ROOT, spiral.PARENT, spiral.CURRENT
RUN = ROOT / "docs/evidence/u7c/run-02"
read, write, compressed, sha = spiral.read, spiral.write, spiral.compressed, spiral.sha
UPDATES, SEED = 256, 78163
VERSION = "u7c-english-balanced-1"
# Declared before gradients: DEV-only interference alarms, not final selection.
RETENTION = {"primitive_min": 24, "u4_composite_min": 42,
             "u4_varied_min": 73, "u0_composite_min": 66,
             "lineage_min": 4, "cadence": 16}


def source_hashes():
    files = sorted({*spiral.SOURCES, "bilqis_u7c/run.py", "bilqis_u7c/grammar.py",
                    "bilqis_teacher/grammar.py", "bilqis_teacher/policy.py",
                    "bilqis_teacher/battery.py", "bilqis_u7b/run.py",
                    "bilqis_development/vendor/kev_teacher.py",
                    "bilqis_ref/model.py", "bilqis_micro/model.py"})
    return {p: sha(ROOT / p) for p in files}


def excluded_history():
    # An excluded identity never becomes an actual TRAIN exposure.
    rows = frozen_u7_rows()
    u7b = ROOT / "docs/evidence/u7b/run-01"
    saved = read(u7b / "train-pools.json.gz")
    rows += [r for cat in ("fresh", "cross", "weak") for group in saved[cat].values() for r in group]
    final = read(u7b / "final-evaluation.json.gz")
    rows += [r for split in final["stages"].values() for group in split.values() for r in group]
    rows += final["cross"]
    rows += [r for pair in saved["causal"] for r in (pair["old_contrast"], pair["new_contrast"])]
    return rows


def _critical(model, corpus):
    primitives = [dict(r, family="Boolean-primitive") for r in read(PARENT / "primitive-retention.json")["rows"]]
    distinction = read(PARENT / "distinction-probes.json")
    return {"primitives": student.score(model, primitives)["correct"],
            "u4_composite": student.score(model, corpus["stages"]["4"]["eval"]["composite"])["correct"],
            "u4_varied": student.score(model, corpus["stages"]["4"]["eval"]["varied"])["correct"],
            "u0_composite": student.score(model, corpus["stages"]["0"]["eval"]["composite"])["correct"],
            "lineage": student.score(model, distinction)["correct"]}


def _retained(scores):
    return (
        scores["primitives"] >= RETENTION["primitive_min"] and
        scores["u4_composite"] >= RETENTION["u4_composite_min"] and
        scores["u4_varied"] >= RETENTION["u4_varied_min"] and
        scores["u0_composite"] >= RETENTION["u0_composite_min"] and
        scores["lineage"] >= RETENTION["lineage_min"])


def freeze(run):
    if run.exists():
        raise FileExistsError("U7C run identity already exists; preserve prior evidence")
    corpus = read(PARENT / "data.json.gz")
    model, optimizer, parent = load(CURRENT)
    start = preserved_start(model, optimizer, parent)
    excluded = excluded_history()
    augmented = copy.deepcopy(corpus)
    # Generation-only exclusion: do not insert historical rows into the U6
    # current-stage TRAIN reservoir.
    augmented["stages"]["0"]["train"]["exclude-history"] = excluded
    pools = build_pools(augmented, SEED, UPDATES)
    base_final = pools.pop("final")
    # Remove shortcut candidates in their entirety; never expose them.
    pools.pop("cross")
    pools.pop("causal")
    all_ancestors = existing_ids(corpus) | {r["id"] for r in excluded}
    all_others = {r["id"] for stage in base_final.values() for rows in stage.values() for r in rows}
    for cat in ("fresh", "weak"):
        all_others.update(r["id"] for rows in pools[cat].values() for r in rows)
    grammar_rng = random.Random(SEED + 405)
    candidate_exclusions = set(all_ancestors | all_others)
    specs = accepted_specs()
    cross, witness_train = generate_split(specs, grammar_rng, candidate_exclusions, multiplier=3)
    final_cross, witness_final = generate_split(specs, grammar_rng, candidate_exclusions,
                                                multiplier=2, varied=True)
    train_audit = audit_cohort(cross, witness_train, forbidden=all_ancestors | all_others)
    final_audit = audit_cohort(final_cross, witness_final,
                               forbidden=all_ancestors | all_others |
                               {r["id"] for rows in cross.values() for r in rows})
    pools["cross"] = cross
    # Do not pass causal or sibling worlds to sampler.
    pools["causal"] = [{"base": w["base"], "gate": w["gate"], "truth": w["truth"],
                         "stage": w["stage"], "old": w["old"], "new": w["new"]}
                        for w in witness_train]
    for cat in ("fresh", "weak"):
        for k, rows in pools[cat].items():
            pools[cat][k] = [dict(r, source_locator=
                                  "https://github.com/Entif-AI/Bilqis/issues/80")
                             if r["stage"] < 5 else r for r in rows]
            for r in pools[cat][k]: validate_lesson(r)
    from bilqis_teacher.policy import source_manifest
    # Known meanings only; EG2 is intentionally not invoked.
    for s in specs:
        example = next(r for r in cross[str(s["stage"])] if r["teacher_spec_id"] == s["id"])
        resolution = novelty({"source": s["source"], "record": example["input"]}, parent["graph"])
        if resolution["eg2_permitted"]:
            raise ValueError("unexpected unfamiliar source meaning requires separate authority")
    baseline = spiral.dev(model, corpus)
    feedback(baseline, corpus)
    critical = _critical(model, corpus)
    if not _retained(critical):
        raise ValueError(f"U6 already under the declared conservation gate: {critical}")
    final_ids = {r["id"] for stage in base_final.values()
                 for rows in stage.values() for r in rows} | {
                     r["id"] for rows in final_cross.values() for r in rows}
    candidate_ids = {r["id"] for cat in ("fresh", "weak", "cross")
                     for rows in pools[cat].values() for r in rows}
    if candidate_ids & final_ids or candidate_ids & all_ancestors or final_ids & all_ancestors:
        raise ValueError("TRAIN/DEV/SEALED/legacy cohort identity collision")
    run.mkdir(parents=True, exist_ok=False)
    compressed(run / "train-pools.json.gz", pools)
    compressed(run / "final-evaluation.json.gz", {"stages": base_final,
                                                  "cross": [r for rows in final_cross.values() for r in rows]})
    compressed(run / "dev-before.json.gz", baseline)
    compressed(run / "paired-causal-final.json.gz", witness_final)
    compressed(run / "paired-causal-train.json.gz", witness_train)
    write(run / "preflight.json", {
        "status": "PASS", "before_gradients": True,
        "train": train_audit, "final": final_audit,
        "split": {"train": len(candidate_ids), "final": len(final_ids),
                  "historical_forbidden": len(all_ancestors), "intersection": 0},
        "answer_hint": {"perfect_root_operator": False, "teacher_receives_oracle_gold": False,
                        "typed_primitives_to_kev": False},
        "old_semantics_internals_only": True, "eg2_calls": 0,
        "retention_start": critical, "retention_policy": RETENTION})
    manifest = {
        "epoch": "U7C", "version": VERSION, "seed": SEED, "updates_cap": UPDATES,
        "batch": MIX, "presentation": "english-only",
        "source_hashes": source_hashes(), "start": start,
        "prior_corpus_sha256": sha(PARENT / "data.json.gz"),
        "parent_checkpoint_sha256": sha(CURRENT),
        "inherited_u7b_state_forbidden": True, "parent_step": 13400,
        "retention": RETENTION, "evaluation": "one-time final opening after training",
        "files": {name: sha(run / name) for name in
                  ("train-pools.json.gz", "final-evaluation.json.gz", "dev-before.json.gz",
                   "paired-causal-train.json.gz", "paired-causal-final.json.gz", "preflight.json")}}
    write(run / "freeze.json", manifest)
    return {"status": "FROZEN_PREFLIGHT_PASS", "train": train_audit["rows"],
            "final": final_audit["rows"], "critical": critical,
            "parent_step": 13400, "optimizer_updates": 0}


def verify(run):
    frozen = read(run / "freeze.json")
    if (frozen["version"] != VERSION or frozen["source_hashes"] != source_hashes() or
        frozen["parent_checkpoint_sha256"] != sha(CURRENT) or
        frozen["prior_corpus_sha256"] != sha(PARENT / "data.json.gz") or
        frozen["batch"] != MIX or frozen["presentation"] != "english-only"):
        raise ValueError("U7C freeze drift")
    for name, value in frozen["files"].items():
        if sha(run / name) != value: raise ValueError("frozen input drift: " + name)
    preflight = read(run / "preflight.json")
    if preflight["status"] != "PASS" or preflight["answer_hint"]["perfect_root_operator"]:
        raise ValueError("pre-gradient shortcut/integrity gate rejected")
    return frozen, read(run / "train-pools.json.gz"), read(PARENT / "data.json.gz")


def teacher_panel(stage, signals, period):
    # One exact weak recent family, three contrasting valid prerequisite arms.
    eligible = [(f, signals[f"{stage}:{f}"]) for f in FAMILIES[stage]]
    target, metrics = sorted(eligible, key=lambda x: (-x[1]["weight"], x[0]))[period % min(2, len(eligible))]
    offered = [s for s in accepted_specs() if s["stage"] == stage and s["family"] == target]
    assert len(offered) == 3
    return {"stage": stage, "period": period, "target": target,
            "mistakes": metrics["errors"], "n": metrics["n"],
            "candidates": offered + [{"id": "REVIEW"}]}


def _english_case(row):
    """Prose-only example from the actual independently validated reservoir."""
    w, query = row["input"]["world"], row["input"]["query"]
    old, new = query["args"]
    people = ", ".join(w["base"]["entities"])
    links = ", ".join(f"{a} is parent of {b}" for kind, a, b in w["base"]["facts"]
                      if kind == "PARENT") or "no stated parent relationships"
    old_arm = old["expression"]
    if old_arm["kind"] == "quantify":
        old_phrase = f'{old_arm["body"]["args"][0]["name"]} has a child'
    elif old_arm["kind"] == "entails":
        expression = old_arm["conclusion"]
        old_phrase = f'it follows from the stated facts and rules that {expression["args"][0]["name"]} is parent of {expression["args"][1]["name"]}'
    else:
        old_phrase = f'{old_arm["args"][0]["name"]} is parent of {old_arm["args"][1]["name"]}'
    event_names = {"E0": "first", "E1": "second", "E2": "third", "E3": "fourth"}
    statement_names = {"J0": "first", "J1": "second", "J2": "third"}
    if new["op"] == "MEMBER" and new["args"][1].get("kind") == "const":
        noun = "first group" if new["args"][1]["name"] == "K0" else "second group"
        recent = f'{new["args"][0]["name"]} belongs to the {noun}'
    elif new["op"] == "SUBSET":
        recent = "everyone in the first group also belongs to the second group"
    elif new["op"] == "MEMBER" and new["args"][1].get("op") == "DOMAIN":
        recent = f'{new["args"][0]["name"]} appears as an input in the first mapping'
    elif new["op"] == "IS_PROPOSITION":
        recent = f'the {statement_names[new["args"][0]["name"]]} statement is declared in this world'
    elif new["op"] == "IS_OBSERVATION":
        recent = f'the {event_names[new["args"][0]["name"]]} recorded event is an observation'
    elif new["op"] == "DERIVED_FROM":
        recent = (f'the {event_names[new["args"][0]["name"]]} event was derived directly or indirectly '
                  f'from the {event_names[new["args"][1]["name"]]} event')
    else:
        raise ValueError("unrenderable English lesson example")
    context = f"People: {people}. Parent facts: {links}."
    if new["op"] in ("MEMBER", "SUBSET"):
        groups = w["sets"]
        context += " First group contains " + (", ".join(groups["K0"]) or "nobody") + "."
        context += " Second group contains " + (", ".join(groups["K1"]) or "nobody") + "."
        if new["op"] == "MEMBER" and new["args"][1].get("op") == "DOMAIN":
            context += " First mapping: " + (", ".join(f"{a} maps to {b}" for a,b in w["functions"]["F0"]) or "empty") + "."
    else:
        context += " Declared statements: " + (", ".join(
            statement_names[s] for s in w["base"]["propositions"]) or "none") + "."
        context += " Reported events: " + ("; ".join(
            f"the {event_names[e[0]]} was a { {'ASSERT':'claim', 'OBSERVE':'recorded observation', 'INFER':'reasoned inference'}[e[1]]}"
            for e in w["events"]) or "none") + "."
        context += " Event links: " + ("; ".join(
            f"the {event_names[a]} event {kind.lower().replace('_', ' ')} the {event_names[b]}"
            for kind,a,b in w["links"]) or "none") + "."
    how = "both propositions hold" if query["op"] == "AND" else "at least one proposition holds"
    return f'{context} Ask whether {old_phrase}, and whether {recent}, to decide if {how}.'


def teacher_text(panel, reservoir):
    human = panel["target"].replace("-", " ")
    state = (f"The learner made {panel['mistakes']} mistakes out of {panel['n']} "
             f"development exercises about {human}. Focus only on improving this "
             "recent skill while preserving earlier Boolean, evidence, and "
             "relationship skills. These are development observations, "
             "not a final test. Each offered lesson has been checked separately "
             "for formal correctness.")
    question = ("Which single lesson family should receive extra practice to "
                f"address the observed weakness in {human}? Compare how the "
                "earlier skill supports the recent one. Choose Review only when "
                "none of the three options fits the goal or you lack enough "
                "information. There is no predefined winning answer.")
    examples = {
        "direction": "Compare the consequence of a relationship from Ada to Bea with its reverse from Bea to Ada.",
        "quantifier": "Ask whether a witness exists in a small group, then combine the witnessed fact with the recent reasoning problem.",
        "entailment": "Distinguish a stated relationship from a conclusion supported by a declared inference rule, then combine with the recent problem."
    }
    options = []
    for candidate in panel["candidates"]:
        if candidate["id"] == "REVIEW":
            desc = "Review: request clarification because these exercises do not suit the described weakness."
        else:
            gloss = DEFINITIONS[candidate["family"]].rstrip(".")
            matching = [r for r in reservoir if r["teacher_spec_id"] == candidate["id"]
                        and r["input"]["query"]["op"] == "AND"]
            if len(matching) < 2: raise ValueError("missing teacher examples")
            positive = next(r for r in matching if r["gold"] == "TRUE")
            negative = next(r for r in matching if r["gold"] == "FALSE")
            samples = [positive, negative] if int(candidate["id"][-1], 16) % 2 else [negative, positive]
            desc = (f"Practice {gloss.lower()}. Earlier focus: {examples[candidate['old_arm']]} "
                    f"Example one: {_english_case(samples[0])} "
                    f"Contrasting example: {_english_case(samples[1])} "
                    "Compare which practice is most likely to correct the observed weakness while maintaining prerequisite skill.")
        options.append({"candidate_id": candidate["id"], "description": desc})
    options = options[(panel["period"] + panel["stage"]) % 4:] + options[:(panel["period"] + panel["stage"]) % 4]
    # No semantic JSON, token identities, primitive names, typed ASTs or oracle answers.
    if any(ch in (state + question + " ".join(x["description"] for x in options)) for ch in ("{", "}", "[", "]")):
        raise ValueError("internal serialized expression leaked into Kev prose")
    return state, question, options


def choice(panel, trace, rows):
    offered = {s["id"] for s in panel["candidates"]}
    selected = trace.get("choice")
    if selected not in offered and trace["status"] != "ERROR":
        raise ValueError("unoffered teacher candidate")
    if trace["status"] == "ERROR" or selected == "REVIEW" or \
            trace.get("margin", 0.) < .05:
        return rows, "REVIEW"
    chosen = [r for r in rows if r["teacher_spec_id"] == selected]
    if not chosen: raise ValueError("selected teacher production has no examples")
    return chosen, "ACCEPTED"


def _execute(run, frozen, pools, corpus, model, optimizer, emit, emit_teacher, *,
             archived=None, enforce_critical=True):
    baseline = read(run / "dev-before.json.gz")
    signals = feedback(baseline, corpus)
    sampler = Sampler(corpus, copy.deepcopy(pools), frozen["seed"]+1, signals)
    category_totals, row_totals, teacher_dispositions = Counter(), Counter(), Counter()
    consumed, gradient_losses, critical_history = 0, [], []
    for i in range(frozen["updates_cap"]):
        if i and i % frozen["retention"]["cadence"] == 0:
            critical = _critical(model, corpus)
            critical_history.append({"after_updates": i, "scores": critical,
                                     "passed": _retained(critical)})
            if enforce_critical and not _retained(critical):
                break
            signals = feedback(spiral.dev(model, corpus), corpus, baseline)
            sampler.update_signals(signals)
        if i % 64 == 0:
            for stage in (5, 6):
                panel = teacher_panel(stage, signals, i//64)
                state, question, options = teacher_text(panel, pools["cross"][str(stage)])
                if archived is None:
                    trace = KevTeacher().score(state, question, options,
                        {"epoch": "U7C", "update": i, "stage": stage, "decision_class": "pedagogical_selection"})
                else:
                    trace = archived[sum(teacher_dispositions.values())]["trace"]
                    if (trace["payload"]["state"] != state or
                        trace["payload"]["questions"]["decision"]["instructions"] != question):
                        raise ValueError("Kev English prompt replay drift")
                    saved_offered = json.loads(trace["serialized_request"])["questions"]["decision"]["criteria"]
                    if list(saved_offered.items()) != [(o["candidate_id"], o["description"]) for o in options]:
                        raise ValueError("Kev options/order replay drift")
                verify_trace(trace)
                chosen, disposition = choice(panel, trace, pools["cross"][str(stage)])
                sampler.pools["cross"][str(stage)] = chosen
                teacher_dispositions[disposition] += 1
                emit_teacher({"update": i, "stage": stage, "panel": panel,
                              "trace": trace, "disposition": disposition,
                              "row_ids": [r["id"] for r in chosen]})
        rows, categories, weak = sampler.batch()
        if Counter(categories) != Counter(MIX): raise ValueError("32-example allocation drift")
        for row in rows: validate_lesson(row)
        loss, gradient, tokens, padded = spiral._step(model, optimizer, rows)
        gradient_losses.append(loss)
        receipt = {"step": 13401+i, "row_ids": [r["id"] for r in rows],
                   "categories": categories, "category_counts": dict(Counter(categories)),
                   "weak_keys": weak, "teacher_spec_ids": [r.get("teacher_spec_id") for r in rows],
                   "signals_sha256": digest(sampler.signals),
                   "stages": [r["stage"] for r in rows], "loss": loss,
                   "gradient_norm": gradient, "tokens": tokens, "padded": padded}
        emit(receipt)
        consumed += 1
        category_totals.update(categories)
        row_totals.update(receipt["row_ids"])
    final_critical = _critical(model, corpus)
    critical_history.append({"after_updates": consumed, "scores": final_critical,
                             "passed": _retained(final_critical)})
    return {"actual_updates": consumed, "cap": frozen["updates_cap"],
            "early_stopped": consumed < frozen["updates_cap"],
            "stop_reason": "critical DEV retention gate" if consumed < frozen["updates_cap"] else "budget",
            "optimizer_step": 13400+consumed, "optimizer": optimizer_receipt(optimizer),
            "state_sha256": state_hash(model), "categories": dict(category_totals),
            "row_exposures": dict(row_totals), "teacher_dispositions": dict(teacher_dispositions),
            "critical_history": critical_history,
            "loss_first": gradient_losses[0] if gradient_losses else None,
            "loss_last": gradient_losses[-1] if gradient_losses else None}


def train(run):
    frozen, pools, corpus = verify(run)
    if any((run/p).exists() for p in ("after.pt", "training.jsonl.gz", "pedagogical-traces.jsonl")):
        raise FileExistsError("U7C cannot overwrite a training receipt")
    model, optimizer, payload = load(CURRENT)
    if preserved_start(model, optimizer, payload) != frozen["start"]:
        raise ValueError("incorrect U6 AdamW parent")
    before = time.perf_counter()
    with (run/"training.jsonl.gz").open("xb") as raw, (run/"pedagogical-traces.jsonl").open("xb") as decisions:
        with gzip.GzipFile(fileobj=raw, mode="wb", mtime=0) as log:
            result = _execute(run, frozen, pools, corpus, model, optimizer,
                              lambda r: log.write(canonical(r)+b"\n"),
                              lambda r: decisions.write(canonical(r)+b"\n"))
    if (result["optimizer"]["steps"] != [result["optimizer_step"]] or
        result["categories"] != {k: v*result["actual_updates"] for k,v in MIX.items()}):
        raise ValueError("optimizer or sampler step-accounting drift")
    save(run/"after.pt", model, optimizer, payload["graph"],
         {"epoch": "U7C", "step": result["optimizer_step"],
          "parent_checkpoint_sha256": sha(CURRENT), "freeze_sha256": sha(run/"freeze.json")})
    result.update({"elapsed_wall_seconds": time.perf_counter()-before,
                   "checkpoint_sha256": sha(run/"after.pt"),
                   "artifacts": {p: sha(run/p) for p in ("training.jsonl.gz",
                                                         "pedagogical-traces.jsonl", "freeze.json")}})
    write(run/"training-result.json", result)
    return {k:result[k] for k in ("actual_updates", "cap", "early_stopped",
                                  "stop_reason", "optimizer_step", "teacher_dispositions",
                                  "critical_history")}


def evaluate(run):
    frozen, _, corpus = verify(run)
    if (run/"evaluation.json.gz").exists(): raise FileExistsError("final opened before; cannot reopen")
    results = read(run/"training-result.json")
    if results["checkpoint_sha256"] != sha(run/"after.pt"):
        raise ValueError("checkpoint bytes drift")
    after, _, _ = load(run/"after.pt")
    before, _, _ = load(CURRENT)
    # Shape accepted by historical score_all: keys stages/cross
    inputs = evaluation_inputs(run, corpus)
    scored = {"final_opened_after_training": True,
              "before": score_all(before, inputs),
              "after": score_all(after, inputs),
              "actual_updates": results["actual_updates"],
              "early_stopped": results["early_stopped"]}
    compressed(run/"evaluation.json.gz", scored)
    return {"status": "OPENED_ONCE", "updates": results["actual_updates"],
            "fresh_final": sum(s["correct"] for splits in scored["after"]["fresh_final"].values()
                               for s in splits.values()),
            "cross_final": [scored[x]["cross_final"]["correct"] for x in ("before","after")],
            "primitives": [scored[x]["primitives"]["correct"] for x in ("before","after")],
            "u4_composites": [scored[x]["historical"]["4"]["composite"]["correct"] for x in ("before","after")]}


def replay(run):
    frozen, pools, corpus = verify(run)
    result = read(run/"training-result.json")
    for filename, digest_sha in result["artifacts"].items():
        if sha(run/filename) != digest_sha:
            raise ValueError("training evidence drift")
    model, optimizer, payload = load(CURRENT)
    preserved_start(model, optimizer, payload)
    with gzip.open(run/"training.jsonl.gz", "rt") as f:
        original = [json.loads(line) for line in f]
    with (run/"pedagogical-traces.jsonl").open() as f:
        decisions = [json.loads(line) for line in f]
    observed, teacher_observed = [], []
    again = _execute(run, frozen, pools, corpus, model, optimizer,
                     observed.append, teacher_observed.append, archived=decisions)
    if (original != observed or
        [(r["update"],r["stage"],r["disposition"],r["row_ids"]) for r in decisions] !=
        [(r["update"],r["stage"],r["disposition"],r["row_ids"]) for r in teacher_observed]):
        raise ValueError("gradient or Kev-replay divergence")
    for key in ("actual_updates", "optimizer_step", "optimizer", "state_sha256",
                "categories", "row_exposures", "teacher_dispositions", "critical_history"):
        if again[key] != result[key]: raise ValueError("replay mismatch: " + key)
    live_eval = score_all(model, evaluation_inputs(run, corpus))
    archived_eval = read(run/"evaluation.json.gz")
    if live_eval != archived_eval["after"]: raise ValueError("all prediction replay divergence")
    if sha(run/"after.pt") != result["checkpoint_sha256"]:
        raise ValueError("checkpoint file drift")
    for x in decisions: verify_trace(x["trace"])
    receipt = {"status": "EXACT_REPLAY", "updates": again["actual_updates"],
               "optimizer_step": again["optimizer_step"],
               "state_sha256": again["state_sha256"],
               "optimizer_sha256": again["optimizer"]["state_sha256"],
               "same_U6_parent": True, "new_helper_calls": 0,
               "all_gradient_exposure_predictions_replayed": True}
    write(run/"replay.json", receipt)
    return receipt


def main():
    p = argparse.ArgumentParser()
    p.add_argument("action", choices=("freeze","train","evaluate","replay"))
    p.add_argument("--run", type=Path, default=RUN)
    args = p.parse_args()
    answer = {"freeze":freeze,"train":train,"evaluate":evaluate,"replay":replay}[args.action](args.run)
    print(json.dumps(answer, sort_keys=True))


if __name__=="__main__": main()
