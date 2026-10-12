# The smallest Bilqis formal foundation (exploratory, v0.1)

This is an **independent new scratch semantic space**, not a repair that changes
the existing U0–U7 semantic ABI, checkpoint, or historical evidence. It is a
bounded implementation of the user's curriculum direction: the human and Chat
own semantics, source selection, prerequisite order and promotion policy;
mechanical tools construct well-typed, oracle-checked samples; native Kev scores
candidate **teaching compositions** and **formative exam compositions** using
identical option-position-audited choices. Kev neither grades nor adds laws.

## What this implementation teaches

There are 29 immutable token identities. Their stable names and actual numeric
IDs are in `bilqis_formal/semantics.py` and in each run's `manifest.json`.
The language contains Boolean atoms `TRUE`, `FALSE`, `P`, `Q`, `R`, typed
operators `NOT`, `AND`, `OR`, `IMPLIES`, and separately addressable law schemas.
The number of token IDs **is not** a count of mastered semantics. OR, IMPLIES,
and multiple law names are reserved but not introduced in the first gates.

Every law owns its own ID, typed source/target schema using formula metavariables
`$A`, `$B`, `$C`, prerequisite operator identities, and an exact schema-rewrite
checker. `LAW.AND.ASSOCIATIVITY` and `LAW.AND.ANNIHILATOR.RIGHT` are not label
aliases for TRUE. The example `(P AND FALSE) -> FALSE` passes the latter but not
`LAW.AND.IDENTITY.RIGHT`; conversely `(FALSE AND P) -> FALSE` requires the
left-hand annihilator law if the one-step direction matters.

`LAW_APPLIES` checks rule/schema identity and uniform substitution, including a
specific rewrite location. It differs from global truth-functional equivalence.
The formal evaluator also checks *every* valuation of all variables involved in
each admitted law identity. The student sees only a prefix-encoded task, formula,
named law if relevant, and valuation; oracle gold is stored out of input.

## Declared initial dependency chain

| Gate | New exposed meaning | Prerequisites | Frozen independent probe |
| --- | --- | --- | --- |
| F01.NOT | `OP.NOT` | Boolean atoms and simple syntax | NOT applied to unseen variable R, both values |
| F02.AND | `OP.AND` | F01.NOT | AND with new operands; AND composed with learned NOT |
| F03.NOT_INVOLUTION | `LAW.NOT.INVOLUTION` | NOT, AND | Named double-negation substitutions and nested evaluations |
| F04.AND_IDENTITY | `LAW.AND.IDENTITY.RIGHT` | AND, involution | Reject wrong law despite equivalence; use fresh substitutions |
| F05.AND_ANNIHILATOR | `LAW.AND.ANNIHILATOR.RIGHT` | AND, identity | Differentiate FALSE annihilator from TRUE identity |
| F06.AND_ASSOCIATIVITY | `LAW.AND.ASSOCIATIVITY` | Previous gates | Regroup three independent formula metavariables |

Only a *passed* full fixed gate makes its new semantic primitive eligible for
subsequent teaching. Previously learned gates are retested after every stage.
The first stage deliberately offers **no Kev composition selection**: with
only NOT introduced, there is no already mastered multi-connective composition
to choose from. Inventing three superficial panels misstates the pedagogy.

From F02 onward, Kev sees three source-checked candidate compositions, each
occupying every presented answer position. The policy accepts a choice only if
all permutations agree and every winning margin is at least 0.05. Otherwise
it records `ORDER_UNSTABLE`, `LOW_MARGIN`, or `KEV_ERROR` and abstains.
An abstention means **no extra Kev-chosen material**; the mandatory training and
fixed diagnostic probes remain usable without pretending the selection occurred.
Both lesson and exam decisions use the same `bilqis_formal.kevlab.choose`.

The present v0.1 sampler offers candidates of different depths, which makes
its **selected exam susceptible to easier-example preference**. Its fixed gate
always tests Easy, Medium and Hard, preventing false promotion, but future
revisions should require *each* candidate lesson/exam panel to cover the target
tier rather than permitting Kev to implicitly select the tier. That curriculum
revision remains a human/Chat decision; do not quietly change the historical run.

## Source screening: user's October 12 references

Source exploration is evidence about useful **representation and proof design**,
not permission to merge unreviewed packages into the model or copy donor code.
The first pilot reuses **no third-party source code** from the list.

| Source | Observed purpose | Pilot disposition |
| --- | --- | --- |
| [hjbolus/mltp](https://github.com/hjbolus/mltp) | Propositional/FOL AST, valuations, axiom schemas, proof checking | Primary representation donor; no code copied; GitHub has no declared repository license |
| [alexprengere/FormalSystems](https://github.com/alexprengere/FormalSystems) | Hofstadter-inspired formal grammars and symbolic rewriting | Primary example of inspectable theorem-production rules (Apache-2.0) |
| [twisted/axiom](https://github.com/twisted/axiom) | Object database / ORM | Not formal-logic axioms; exclude |
| [dkubb/axiom](https://github.com/dkubb/axiom) | Ruby relational query algebra | Later relational-structure stage, not foundational Boolean logic |
| [TheAxiomFoundation/axiom-rules-engine](https://github.com/TheAxiomFoundation/axiom-rules-engine) | Executable legal RuleSpec, provenance and traceable rules | Useful later for source/trace patterns; not a Boolean theorem prover |
| [baziotis/metap](https://github.com/baziotis/metap) | Python AST metaprogramming | Optional later tooling, not an elementary semantic primitive |
| [gilch/drython](https://github.com/gilch/drython) | Macro / DRY Python metaprogramming | Later implementation tooling only |
| [Aunsiels/pyformlang](https://github.com/Aunsiels/pyformlang) | Formal grammars and automata | Strong future grammar/parser oracle (MIT); small pilot uses fixed typed AST |
| [mal-lang](https://github.com/mal-lang) | Domain-specific language for attack simulations | Not foundational logic; later domain modeling only |
| [BasisResearch/effectful](https://github.com/BasisResearch/effectful) | Algebraic effects and handlers | Later operator/context machinery; not needed for primitive gates |
| [digitalformallogic/mathesis](https://github.com/digitalformallogic/mathesis) | Formal semantics and natural-deduction/proof calculi | Primary future proof-rule donor (MIT); Boolean gate remains smaller |
| [abstract-algebra Python topic](https://github.com/topics/abstract-algebra?l=python) | Repository discovery collection, not one library | Literature/source search only |
| [aothmane-control/Algebraic-differentiators](https://github.com/aothmane-control/Algebraic-differentiators) | Numerical differentiation for control theory | Unrelated to initial algebraic logic; exclude |

Additional formal source authorities: classical Boolean algebra, propositional
syntax and axiom schemas, proof-theoretic semantics, and the [Open Logic Project](https://openlogicproject.org/).
These sources inform the **draft** grammar and future FOL bridge; they are not
proof of representation efficiency or of student understanding.

## How to inspect and reproduce

Use a Python 3.13 environment with PyTorch. No new model or source-package
download is required. The old `bilqis_ref.model.Block` is reused as an
untrained *architecture*, not as trained weights.

```
python -m unittest discover -s tests -q
python -m bilqis_formal.pilot --out runs/formal-foundations-new-run --max-stages 6 --steps 320
python -m bilqis_formal.pilot --out runs/formal-foundations-new-run --replay
```

The pilot requires the previously qualified operator-owned Kev-4B local service
at `http://127.0.0.1:8008`. The imported adapter pins its exact model/revision
and checks identity before and after every decision. It does not fall back to a
fictional Kev response. Runtime files, response traces, model weights and
optimizer checkpoints remain in the ignored `runs/` directory.

This is an exploratory experiment. Passing a fixed probe is **necessary** for
the local stage promotion, not a scientifically validated claim of learning
or generalization. A failure stops the run rather than broadening its ontology.
