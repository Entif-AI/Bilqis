"""Semantically coherent versus shuffled teaching with matched row exposure.

This is a teaching-order experiment. Semantic labels never enter learner input;
all five arms use the same model, target oracle and stage update budget. For
every stage and 64-update block, every arm in a rehearsal-budget stratum sees
EXACTLY the same multiset of training rows, assigned to different batches.
"""
from __future__ import annotations

from collections import Counter
import hashlib
import json
import random

import torch
from torch.nn import functional as F

from .curriculum_v6 import STAGES, RELATIONS, concept_key, expression_id, rows, signature
from .dialogue_v3 import STUDENT_LABELS
from .student_v3 import inputs_for, predict, typed_logits

VERSION = "bilqis.formal.controller/v0.6.0"
SEEDS = (503, 509, 521, 523, 541)
STEPS_PER_STAGE = 320
BLOCK_UPDATES = 64
BATCH_SIZE = 32
ARMS = {
    "uniform8": ("uniform", 8),
    "semantic8": ("semantic", 8),
    "sham8": ("sham", 8),
    "uniform16": ("uniform", 16),
    "semantic16": ("semantic", 16),
}


def _hash_rows(rows, *, order_sensitive):
    identities = [row["id"] for row in rows]
    if not order_sensitive:
        identities.sort()
    return hashlib.sha256("\n".join(identities).encode()).hexdigest()


def _slot_sizes(stage, prior, prior_per_batch):
    """Every batch has 16 TRUE / 16 FALSE, with even rehearsal per skill."""
    if not prior:
        return [(stage, BATCH_SIZE)]
    if prior_per_batch not in (8, 16) or len(prior) > 2:
        raise ValueError("INVALID_V06_REHEARSAL_ALLOCATION")
    if len(set(prior)) != len(prior) or stage in prior:
        raise ValueError("DUPLICATED_V06_PRIOR")
    if prior_per_batch % (2 * len(prior)):
        raise ValueError("UNBALANCED_V06_REHEARSAL")
    share = prior_per_batch // len(prior)
    return [(stage, BATCH_SIZE - prior_per_batch),
            *((old, share) for old in prior)]


def _sort_semantic(rows, *, mode, shuffle_seed):
    if mode == "uniform":
        return rows
    if mode == "semantic":
        keys = {expression_id(r["input"]["expression"]):
                concept_key(r["input"]["expression"]) for r in rows}
        return _interleaved_groups(rows, keys)
    if mode == "sham":
        # Permute the true signatures ACROSS expression identities. The
        # resulting groups have similar occupancy, but their assignments
        # do not preserve algebraic equivalence or complementation.
        unique = sorted({expression_id(row["input"]["expression"]):
                         concept_key(row["input"]["expression"])
                         for row in rows}.items())
        false_keys = [key for _, key in unique]
        random.Random(shuffle_seed).shuffle(false_keys)
        aliases = {expression: key for (expression, _), key in zip(unique, false_keys)}
        return _interleaved_groups(rows, aliases)
    raise ValueError("BAD_V06_ARM_MODE")


def _interleaved_groups(selected, keys):
    """Group related concepts, round-robin distinct expression shapes first.

    Blind sorting of replacement samples would make consecutive batches full
    of duplicate questions; that is repetition, not relational instruction.
    Keep the exact input multiset while interleaving examples from distinct
    ASTs inside each teacher-defined neighborhood.
    """
    groups = {}
    for item in selected:
        expr_id = expression_id(item["input"]["expression"])
        groups.setdefault(keys[expr_id], {}).setdefault(expr_id, []).append(item)
    result = []
    for concept in sorted(groups):
        by_expr = groups[concept]
        while any(by_expr.values()):
            for expr_id in sorted(by_expr):
                if by_expr[expr_id]:
                    result.append(by_expr[expr_id].pop())
    return result


def _align_with_current(chunks, batches, stage):
    """Reorder already selected prior TRAIN rows beside related current rows.

    Alignment operates only on the TRAIN ASTs, preserves each prior-stage/gold
    chunk and the block's whole row multiset, and never examines a gate/DEV.
    Both operands are actual distinct expressions, not repeated-question hits.
    """
    remaining = list(chunks)
    ordered = []
    for batch in batches:
        current = [(concept_key(r["input"]["expression"]),
                    expression_id(r["input"]["expression"]))
                   for r in batch if r["stage"] == stage]
        def affinity(chunk):
            return sum(1 for r in chunk
                       for key, expression in current
                       if concept_key(r["input"]["expression"]) == key
                       and expression_id(r["input"]["expression"]) != expression)
        winner = max(range(len(remaining)), key=lambda j: affinity(remaining[j]))
        ordered.append(remaining.pop(winner))
    return ordered


def training_batches(*, seed, stage, block, arm, prior=()):
    """Materialize one deterministic block without observing model/gate state."""
    if seed not in SEEDS or stage not in STAGES or block not in range(
            STEPS_PER_STAGE // BLOCK_UPDATES) or arm not in ARMS:
        raise ValueError("V06_NOT_PREREGISTERED")
    mode, prior_count = ARMS[arm]
    prior = tuple(prior)
    slots = _slot_sizes(stage, prior, prior_count)
    rng = random.Random(seed * 100003 + STAGES.index(stage) * 13007 + block * 101)
    batches = [[] for _ in range(BLOCK_UPDATES)]
    for slot_index, (lesson, count) in enumerate(slots):
        lesson_rows = rows(lesson, "train")
        for gold in ("ATOM.FALSE", "ATOM.TRUE"):
            eligible = [row for row in lesson_rows if row["gold"] == gold]
            if not eligible:
                raise ValueError("UNBALANCED_V06_TRAINING_POOL")
            per_batch = count // 2
            selected = [rng.choice(eligible) for _ in range(BLOCK_UPDATES * per_batch)]
            rng.shuffle(selected)
            selected = _sort_semantic(
                selected, mode=mode,
                shuffle_seed=seed * 19 + block * 71 + slot_index * 701 +
                (1 if gold == "ATOM.TRUE" else 0))
            chunks = [selected[i * per_batch:(i + 1) * per_batch]
                      for i in range(BLOCK_UPDATES)]
            if mode == "semantic" and lesson != stage:
                chunks = _align_with_current(chunks, batches, stage)
            for i, chunk in enumerate(chunks):
                batches[i].extend(chunk)
    for i, batch in enumerate(batches):
        random.Random(seed * 500009 + i * 17 + block * 31).shuffle(batch)
        if len(batch) != BATCH_SIZE or Counter(row["gold"] for row in batch) != {
                "ATOM.FALSE": 16, "ATOM.TRUE": 16}:
            raise ValueError("V06_BATCH_QUOTA_BROKEN")
    return batches


def ledger(batches, *, stage):
    rows = [row for batch in batches for row in batch]
    if any(len(batch) != BATCH_SIZE for batch in batches):
        raise ValueError("INCOMPLETE_V06_BLOCK")
    per_stage = dict(sorted(Counter(row["stage"] for row in rows).items()))
    per_gold = dict(sorted(Counter(row["gold"] for row in rows).items()))
    # Within-batch current-stage equivalence/complement overlap, quantified
    # rather than assumed effective merely because a sort was performed.
    numerator = denominator = equivalence_pairs = complement_pairs = 0
    cross_equivalent = cross_complement = 0
    aligned_equivalent = aligned_complement = 0
    witnessed_relations = Counter()
    for batch in batches:
        for relation_index, (source, target) in enumerate(RELATIONS):
            left, right = expression_id(source), expression_id(target)
            witnesses = [r for r in batch if expression_id(r["input"]["expression"]) == left]
            counterparts = [r for r in batch if expression_id(r["input"]["expression"]) == right]
            witnessed_relations[f"relation_{relation_index+1:02d}"] += sum(
                a["input"]["valuation"] == b["input"]["valuation"]
                for a in witnesses for b in counterparts)
        current_items = [r for r in batch if r["stage"] == stage]
        prior_items = [r for r in batch if r["stage"] != stage]
        for a in current_items:
            a_expr = a["input"]["expression"]
            for b in prior_items:
                b_expr = b["input"]["expression"]
                if expression_id(a_expr) == expression_id(b_expr) or \
                        concept_key(a_expr) != concept_key(b_expr):
                    continue
                if signature(a_expr) == signature(b_expr):
                    cross_equivalent += 1
                    aligned_equivalent += int(a["input"]["valuation"] ==
                                              b["input"]["valuation"])
                else:
                    cross_complement += 1
                    aligned_complement += int(a["input"]["valuation"] ==
                                              b["input"]["valuation"])
        expressions = [(expression_id(row["input"]["expression"]),
                        signature(row["input"]["expression"]),
                        concept_key(row["input"]["expression"]))
                       for row in batch if row["stage"] == stage]
        for i, (a_id, a_bits, a_concept) in enumerate(expressions):
            for b_id, b_bits, b_concept in expressions[i + 1:]:
                if a_id == b_id:
                    continue  # identical copies cannot prove relational grouping
                denominator += 1
                if a_concept == b_concept:
                    numerator += 1
                    equivalence_pairs += int(a_bits == b_bits)
                    complement_pairs += int(a_bits != b_bits)
    return {
        "examples": len(rows),
        "row_order_sha256": _hash_rows(rows, order_sensitive=True),
        "row_multiset_sha256": _hash_rows(rows, order_sensitive=False),
        "by_stage": per_stage, "by_gold": per_gold,
        "semantic_pair_count": numerator, "semantic_equivalence_pairs": equivalence_pairs,
        "semantic_complement_pairs": complement_pairs,
        "cross_skill_equivalence_pairs": cross_equivalent,
        "cross_skill_complement_pairs": cross_complement,
        "cross_skill_same_valuation_equivalent": aligned_equivalent,
        "cross_skill_same_valuation_complement": aligned_complement,
        "relation_coexposures_same_valuation": dict(sorted(witnessed_relations.items())),
        "possible_distinct_expression_pairs": denominator,
    }


def predictions(model, rows):
    return predict(model, rows, mode="none")


def score(preds):
    return {"correct": sum(p["prediction"] == p["gold"] for p in preds),
            "n": len(preds)}


def evaluate_panel(model, rows):
    preds = predictions(model, rows)
    return {"accuracy": score(preds),
            "true": score([p for p in preds if p["gold"] == "ATOM.TRUE"]),
            "false": score([p for p in preds if p["gold"] == "ATOM.FALSE"]),
            "items": {p["id"]: p["prediction"] == p["gold"] for p in preds}}


def train_block(model, optimizer, *, seed, stage, block, arm, prior):
    batches = training_batches(seed=seed, stage=stage, block=block, arm=arm, prior=prior)
    receipt = ledger(batches, stage=stage)
    errors = 0
    losses = []
    for rows in batches:
        (ids, lengths), sequences = inputs_for(model, rows, mode="none")
        if any(len(seq) > model.cfg.context for seq in sequences):
            raise ValueError("V06_CONTEXT_OVERFLOW")
        model.train()
        optimizer.zero_grad(set_to_none=True)
        logits = typed_logits(model(ids, lengths), rows)
        targets = torch.tensor([STUDENT_LABELS.index(row["gold"]) for row in rows])
        errors += int((logits.argmax(-1) != targets).sum().item())
        loss = F.cross_entropy(logits, targets)
        if not bool(torch.isfinite(loss)):
            raise ValueError("V06_NONFINITE_LOSS")
        loss.backward()
        torch.nn.utils.clip_grad_norm_(model.parameters(), 1.0)
        optimizer.step()
        losses.append(float(loss.detach()))
    return {**receipt, "pre_update_errors": errors,
            "loss_mean": sum(losses) / len(losses),
            "loss_last": losses[-1], "optimizer_sha256": optimizer_digest(optimizer.state_dict())}


def optimizer_digest(state):
    """Hash complete AdamW tensor moments and all parameter groups."""
    digest = hashlib.sha256()
    digest.update(json.dumps(state["param_groups"], sort_keys=True,
                             separators=(",", ":")).encode())
    for parameter in sorted(state["state"]):
        digest.update(str(parameter).encode() + b"\0")
        for name, value in sorted(state["state"][parameter].items()):
            digest.update(name.encode() + b"\0")
            if isinstance(value, torch.Tensor):
                t = value.detach().cpu().contiguous()
                digest.update(str((str(t.dtype), tuple(t.shape))).encode())
                digest.update(t.numpy().tobytes())
            else:
                digest.update(repr(value).encode())
            digest.update(b"\0")
    return digest.hexdigest()


def optimizer_steps(optimizer):
    return {int(x["step"]) for x in optimizer.state.values() if "step" in x}
