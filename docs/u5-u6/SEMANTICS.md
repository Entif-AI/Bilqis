# Executable U5–U6 scope

The authority chain is [#80](sources/80.json), [#85](sources/85.json), [#84](sources/84.json), then the scoped local finite definitions. EG2 retrieves authored construction candidates; native Kev selects a candidate; deterministic source/type/formal validation admits or rejects it. Neither helper creates authoritative truth. The full execution contract is [CONTRACT.md](CONTRACT.md).

U5 uses a finite domain of 2–5 entities, two finite sets, two partial functions and a directed graph. Membership/subset/intersection/difference use ordinary finite-set semantics. Function composition is **g after f**; inverse is admitted only for injective partial functions. Paths have positive length, so a node reaches itself only through an actual cycle. Neighborhoods are outgoing direct targets. Independent set/matrix/pair-enumeration oracles agree on every compiled lesson.

U6 uses a proposition registry and typed assertion, observation or inference events with source and explicit support/refutation polarity. These events never rewrite the underlying facts or Horn rules. A reported or observed proposition can therefore be formally false or unentailed. `FORMAL_ENTAILS` uses the unchanged finite Horn-rule evaluator.

Three independently typed event graphs remain separate:

- `DERIVED_FROM`: transitive provenance ancestry.
- `DEPENDS_ON`: transitive declared premise-use dependency; its origin must be an inference event. Declaring dependency alone does not prove soundness.
- `SUPERSEDES`: explicit direct replacement of an earlier event about the same proposition. It does not imply ancestry or dependency. `REVISES` additionally requires changed polarity.

Edges point from newer event identities to earlier ones and are acyclic. Current evidence aggregates unsuperseded events. Historical evidence aggregates all events, retaining replaced evidence. Empty support/refutation is UNKNOWN; support alone TRUE; refutation alone FALSE; both CONFLICT. New event worlds use one interpretation. The historical five-state U4 tasks, including AMBIGUOUS interpretations, remain unchanged and enter cumulative rehearsal.

Cross-family exercises combine these operators with Boolean operations and inherited relations/quantifiers. Earlier proof and evidence families continue through their original codecs and evaluators. This tranche does not claim complete #84 semantics or Rosetta serialization conformance.

The learner sees numeric identity IDs, lengths, raw worlds and unreduced prefix queries. It never receives English text, closures, current masks, reduced function/set results, helper vectors, helper probabilities or oracle answers as input. The supervised targets come from the independent finite evaluators. Gold, provenance and helper trace IDs are dataset metadata, excluded by the codec.

The historical `bilqis_micro`, `bilqis_logic` and `bilqis_ref/model.py` sources are unchanged. New code occupies `bilqis_development`. Vendor adapters are exact copies of PR #106 at `6df36efacd6a5ad664c52b663bc14e9319bfb17a`; their hashes and actual runtime identities are retained in the helper receipt. No DN-01 learner training was resumed.

Appending vocabulary replaces only the live embedding parameter, copying all trained rows. AdamW retains every old moment, hyperparameter and step counter; new row moments are zero while the shared embedding step counter stays at 8,400. Symbolic keyed feature geometry initializes only new rows. The old learner's other parameters and all prior logits remain exact before new training begins.
