# CODEX: BILQIS DEVELOPMENTAL MICRO-UNIVERSES

**Mission:** Implement and train the next Bilqis learner through a sequence of tiny, purpose-built semantic universes. Each universe introduces new meaning while requiring the learner to combine it with previously taught semantics.

This is an **exploratory capability-building run**, not a confirmatory research experiment. Prioritize richer semantic embeddings, cumulative neural learning, and working demonstrations over controls, ablations, statistical attribution, or research infrastructure.

## Starting point

Repository: `Entif-AI/Bilqis`.

The completed Boolean T0/T1 pilot is PR #107, branch `codex/t0-t1-logic-pilot`, head `d4a7d36dabfd0c322589888a56c220d96da866bb`.

Its `bilqis_logic` package provides working typed ASTs, deterministic evaluation, a scratch transformer, training, checkpoints, and replay. Its Boolean-only DCT geometry and 17-token vocabulary are **engineering precedents, not architectural limits**.

Create a **new isolated branch/worktree** from PR #107's head. Stack your new PR against #107 while it remains unmerged. Preserve #107's evidence and all earlier PRs. Do not merge anything.

The implementation work is tracked in Bilqis #108. This prompt supplies its executable objective. **Do not spend execution time rereading GitHub issue bodies or reconstructing the roadmap.** Inspect source code only to identify reusable components and repository conventions.

## 1. Build richer semantic embeddings

Replace the Boolean-only feature geometry with an extensible, versioned, **typed semantic graph**.

Its machine-native identities and initial embeddings must encode meaningful distinctions, including:

- Semantic family, subtype, type signature and operator arity.
- Argument roles, directional relations, inverses and negation.
- Identity, equality, exclusion and relational composition.
- Variable binding, scope, quantifiers and prerequisite relationships.
- Proof-rule relationships and, when introduced, evidence-state distinctions.
- Typed graph neighborhoods and composition links between old and new concepts.

Compile accepted, project-owned semantic structure deterministically into initial neural embeddings. **No pretrained teacher vectors, hidden states or task-capable weights enter the student.** EG2/Kev may help generate upstream candidates if genuinely useful, but are not required.

Avoid the existing DCT initializer's feature-basis expansion problem: adding semantic features must not silently change previously assigned coordinates. Use a stable keyed projection, fixed feature slots, or another demonstrably stable method.

For this experimental cohort, you may freeze the complete admitted token/geometry map before training and expose identities by stage. Future expansion must support append-only semantic identities without renumbering old tokens or reinterpreting existing meanings.

Choose a sensible larger student architecture if useful. **Initialize this developmental learner once, then keep training the same weights across stages.** Reusing #107's Boolean checkpoint is optional, not required, if its architecture is incompatible.

## 2. Teach through tiny universes

Every universe should contain only the entities, relationships, states and operators needed to teach its specific semantic distinction.

Generate many deterministic variations of each small world rather than creating a large, noisy simulation.

**Universe 0: Cognitive-algebra refresh**

Use the existing Boolean operations, including negation, conjunction, XOR and implication, as starting knowledge. Keep them active in subsequent worlds. Do not demand perfect Boolean mastery before proceeding.

**Universe 1: Entities, roles and directional relations**

Introduce 2–5 entities and a handful of typed relations. Teach identity, role binding, inverse relations, directionality and elementary composition.

Example formal world:

- `PARENT(A,B)`
- `PARENT(B,C)`
- `PARENT(A,C)` is not automatically true.
- `CHILD(B,A)` follows from the declared inverse semantics.

Changing one edge or reversing its arguments should change appropriate answers. Combine these facts with existing Boolean operators.

**Universe 2: Quantification and relational composition**

Reuse these small worlds to introduce bound variables, `EXISTS`, `FORALL`, equality, inequality and two-hop relational composition.

Example:

`EXISTS x (PARENT(A,x) AND PARENT(x,C)) → TRUE`

Reverse the second parent edge and the answer should become FALSE in the explicitly closed finite world.

Generate different entity assignments, relation topologies, witnesses and counterexamples. Force the learner to combine quantifiers with relations and previously learned Boolean algebra.

**Universe 3: Inference and proof state**

Using similarly tiny relational worlds, introduce premises, rule application, entailment, derivation and countermodels.

Example:

`PARENT(A,B) ∧ PARENT(B,C)`

together with a declared two-hop ancestry rule entails `GRANDPARENT(A,C)`.

Distinguish a derivable conclusion from an unsupported one. Reuse relation directionality, quantification and Boolean implication.

**Next universe, if the first three are working: Evidence**

Introduce 1–3 propositions and 1–3 evidence sources. Teach FALSE, UNKNOWN, CONFLICT and multiple live interpretations without collapsing them. Build on existing propositions, inference and relations.

Keep missing information distinct from explicit falsity. This epistemic extension leads toward later Rosetta semantics, not toward English-language training.

## 3. Cumulative development is mandatory

The new universe is never an isolated dataset.

At every stage, train on a mixture of:

1. Examples emphasizing the newly introduced semantics.
2. Selected earlier tasks.
3. Compositions combining new and old semantics.
4. Small contrastive perturbations that change one semantic factor.

Use the **same continuing neural learner** throughout. Preserve trained parameters and optimizer continuity unless an explicitly recorded technical change requires otherwise.

Keep universe sizes small but vary structural configurations. Novelty should arise from semantic combinations, not arbitrary names or memorized templates.

Gold answers come from deterministic, typed, independently checked finite-world evaluators. The model receives semantic inputs, never their evaluated answers or reduced solutions.

Before training, print several **actual encoded model inputs**, their formal gold outputs and the neural prediction interface, including examples from the first two new universes. This is a quick objective-alignment check, not a new planning exercise.

## 4. Execute and train

Reuse the proven training, batching and checkpoint machinery. Choose the fastest already workable local backend. Do not build an accelerator framework before obtaining results.

Perform one substantive cumulative developmental run through Universes 0–3. Continue into the evidence universe if it does not require a major detour.

Record stage transitions, semantic-identity additions, initial geometry hashes, checkpoint lineage, optimizer steps, exposures, time and memory.

Evaluate familiar, structurally varied, and new-plus-old composite tasks. Preserve mistakes rather than concealing them or stopping development over imperfect early mastery.

**Do not run random/permuted controls, attribution studies, ablation matrices or confirmatory SYS-01 experiments. Do not build a polished UI.**

## 5. Deliver the working result

Commit and push:

- The extensible semantic identity/embedding implementation.
- Typed finite-universe generators and executable evaluation semantics.
- The continuing multi-stage neural training path.
- Reproducible stage and checkpoint manifests.
- A compact gallery showing real neural answers, oracle answers, successes, mistakes and semantic perturbations.
- `RESULTS.md` and a standalone `HANDOFF.md`.

At minimum, demonstrate **two genuinely new trainable semantic families beyond Boolean logic** and a student trained across their stages without resetting. Aim to complete all three new universes described above.

Create the stacked PR and verify committed artifacts and tests. No merge.

If implementation becomes blocked, preserve the completed working increment and exact next executable step rather than branching into a lengthy architecture exercise.

**Success means Bilqis has a richer structured semantic space and has actually trained through several little worlds, using new concepts together with what she learned earlier.**

Build it. Train it. Show me what she can do.

And remember: **we're raising a strange little intelligence, not assembling a dissertation committee.**