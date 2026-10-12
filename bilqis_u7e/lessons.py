"""Meaning-first paired lessons for one continuously developing Bilqis student.

Each two-row episode differs in exactly one typed link's presence or kind.
The independent finite-world oracle provides supervised targets, never student
input. Relationships among derivation, supersession and proof dependency are
presented before increasingly compositional event-chain problems.
"""
from __future__ import annotations

from collections import defaultdict
import copy
import random

from bilqis_logic.kernel import digest
from bilqis_micro import kernel as micro
from bilqis_development import data as source
from bilqis_development import kernel as dev

VERSION = "bilqis.continuous-lineage-lessons/v0.1"
KINDS = ("DERIVED_FROM", "SUPERSEDES", "DEPENDS_ON", None)
RELATIONS = ("DERIVED_FROM", "SUPERSEDES", "DEPENDENCY", "REVISES", "CURRENT_STATE")


def _template(rng, *, compositional):
    entities = list("ABCD")[:rng.choice((2, 3, 4))]
    a, b = rng.sample(entities, 2)
    facts = [] if rng.random() < .5 else [("PARENT", a, b)]
    definitions = {
        "J0": micro.relation("PARENT", micro.entity(a), micro.entity(b)),
        "J1": micro.relation("PARENT", micro.entity(b), micro.entity(a)),
    }
    base = micro.world(entities, facts=facts, propositions=definitions)
    events = [
        ["E0", rng.choice(("ASSERT", "OBSERVE")), rng.choice(("S0", "S1", "S2")),
         "J0", rng.choice(("support", "refute"))],
        ["E1", "INFER", rng.choice(("S0", "S1", "S2")),
         "J0", rng.choice(("support", "refute"))],
    ]
    if compositional:
        events.append(["E2", "INFER", rng.choice(("S0", "S1", "S2")),
                       "J0", rng.choice(("support", "refute"))])
    # The first edge in a chain stays unchanged, so paired variants change
    # exactly one *later* edge while retaining its earlier semantic context.
    fixed = [] if not compositional else [[
        rng.choice(KINDS[:-1]), "E1", "E0"]]
    return base, events, fixed


def _queries(compositional):
    source_id, target_id = ("E2", "E1") if compositional else ("E1", "E0")
    pair = (dev.const("Event", source_id), dev.const("Event", target_id))
    items = [(name, (source_id, target_id), dev.op(name, *pair))
             for name in ("DERIVED_FROM", "SUPERSEDES", "DEPENDENCY", "REVISES")]
    if compositional:
        across = (dev.const("Event", "E2"), dev.const("Event", "E0"))
        items.extend((name, ("E2", "E0"), dev.op(name, *across))
                     for name in ("DERIVED_FROM", "SUPERSEDES", "DEPENDENCY"))
    for p in ("J0",):
        for name in ("CURRENT_STATE", "HISTORICAL_STATE"):
            items.append((name, (p,), dev.op(name, dev.const("Proposition", p))))
    return items


def _world(base, events, fixed, kind):
    changing = [] if kind is None else [[kind, "E2" if fixed else "E1",
                                           "E1" if fixed else "E0"]]
    return dev.world(base["entities"], base=base, events=events,
                     links=fixed + changing)


def build(seed: int, templates: int, *, compositional: bool):
    """Return real causal episodes and unchanged-history contrast anchors.

    The same template is sampled across all allowed link kinds. A witness pair
    may differ only in one link, and the oracle's gold must actually change.
    This prevents a 'semantic group' that merely repeats a single question.
    """
    rng = random.Random(seed)
    grouped = defaultdict(list)
    invariant = []
    for index in range(templates):
        base, events, fixed = _template(rng, compositional=compositional)
        for kind in KINDS:
            w = _world(base, events, fixed, kind)
            for relation, target, q in _queries(compositional):
                try:
                    row = source.row(dev.record(w, q), 6, "guided:" + relation.lower())
                except ValueError:
                    continue
                row["lesson_relation"] = relation
                row["lesson_level"] = "chain" if compositional else "direct"
                row["lesson_template"] = index
                row["lesson_edge"] = kind or "NONE"
                if relation == "HISTORICAL_STATE":
                    invariant.append(row)
                else:
                    grouped[index, relation, target].append(row)
    lessons = defaultdict(list)
    for (index, relation, target), variants in grouped.items():
        truth = [v for v in variants if v["gold"] in ("TRUE", "CONFLICT")]
        false = [v for v in variants if v["gold"] not in ("TRUE", "CONFLICT")]
        for a in truth:
            for b in false:
                if a["gold"] != b["gold"] and a["lesson_edge"] != b["lesson_edge"]:
                    lessons[relation].append((a, b))
                    break
            if lessons[relation] and lessons[relation][-1][0] == a:
                break
    for needed in ("DERIVED_FROM", "SUPERSEDES", "DEPENDENCY", "REVISES",
                   "CURRENT_STATE"):
        if len(lessons[needed]) < 6:
            raise ValueError(f"insufficient paired semantic lessons {needed}: {len(lessons[needed])}")
    return {"version": VERSION, "level": "chain" if compositional else "direct",
            "episodes": {k: v for k, v in lessons.items()},
            "invariants": invariant}


def paired_batch(easy, complex_set, *, iteration, rng):
    """16 teacher-guided examples, ordered as eight counterfactual pairs."""
    taught = easy if iteration < 96 else complex_set if iteration >= 224 else (
        easy if iteration % 3 == 0 else complex_set)
    priority = ("DERIVED_FROM", "DERIVED_FROM", "SUPERSEDES", "SUPERSEDES",
                "DEPENDENCY", "REVISES", "CURRENT_STATE", "CURRENT_STATE")
    selected = []
    for relation in priority:
        pair = rng.choice(taught["episodes"][relation])
        # Preserve adjacency; varying order never supplies a gold shortcut.
        selected.extend(pair if rng.randrange(2) else pair[::-1])
    return selected


def without_exposed(source, train_ids):
    """Keep a development dashboard genuinely unfamiliar to the new trainer."""
    retained = {}
    for relation, pairs in source["episodes"].items():
        retained[relation] = [
            (a, b) for a, b in pairs
            if a["id"] not in train_ids and b["id"] not in train_ids
        ]
        if len(retained[relation]) < 6:
            raise ValueError("not enough fresh development examples: " + relation)
    return {**source, "episodes": retained}


def validate_pair(a, b):
    if a["input"]["query"] != b["input"]["query"] or a["gold"] == b["gold"]:
        raise ValueError("no changing-outcome paired lesson")
    aw, bw = a["input"]["world"], b["input"]["world"]
    for key in ("base", "sets", "functions", "edges", "events"):
        if aw[key] != bw[key]:
            raise ValueError("contrast accidentally changed the world facts")
    al, bl = aw["links"], bw["links"]
    if len(al) > 2 or len(bl) > 2 or len(al) == len(bl) == 0:
        raise ValueError("invalid minimal link contrast")
    common = set(map(tuple, al)) & set(map(tuple, bl))
    if len(al) - len(common) > 1 or len(bl) - len(common) > 1:
        raise ValueError("not a single-link intervention")
    if a["id"] != digest(a["input"]) or b["id"] != digest(b["input"]):
        raise ValueError("lesson identity corruption")
    for row in (a, b):
        source.row(row["input"], 6, row["family"])
    return True
