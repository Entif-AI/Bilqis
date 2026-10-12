# BILQIS: U5–U6 HELPER-GUIDED SEMANTIC DEVELOPMENT

## Mission

Continue the existing scratch-trained Bilqis student from PR #109, introducing richer cognitive and epistemic meaning through **EG2-assisted semantic discovery, Kev-4B bounded discrimination, deterministic semantic admission, and cumulative training in tiny universes**.

The previous developmental run used no helpers. This one must make EG2 and Kev operational participants in constructing training material, not optional add-ons or occasional curriculum schedulers.

This is exploratory capability development, not a confirmatory comparison or new research-program planning exercise.

## Existing assets

Repository: `Entif-AI/Bilqis`.

Base: PR #109 at verified head `c858e086df93f5ca1c27be207d72fafd405dae88`.

Student checkpoint: `docs/evidence/micro-universes/run-01/after-U4.pt`.

Reuse:
- The trained 348,192-parameter student and AdamW moments.
- The 68-identity typed semantic graph and finite-world evaluators.
- Existing EG2 MLX runtime and native embedding assets from PR #106.
- Existing Kev-4B native MLX service/harness from PRs #76, #78 and #106.
- Source-grounded semantic contracts from #80, #85 and #84.
- Prior task-aligned Kev capability/failure evidence from PR #78.

Verify actual runtimes before using them. Reuse pinned code and models where possible. Do not redownload or recreate functioning services unnecessarily.

Create an isolated successor branch stacked against #109. Preserve all historical runs.

## 1. Integrate EG2 as the semantic-neighborhood engine

Retrieve candidate relations, contrasts, inverse relationships, prerequisites, and possible compositions from a **small source-grounded semantic registry**.

Prioritize concepts from the current logic, mathematical and Rosetta developmental stages.

Do not start broad New Ithkuil lexical training.

Correct PR #106's retrieval weakness: almost every previous query hit the 256-token truncation limit. Encode concise, typed semantic descriptions with source identifiers and relevant context, not enormous serialized worlds.

Keep the existing model's 768-dimensional output available. Use the appropriate measured projection profile without treating cosine similarity as truth.

For each query retain:
- Semantic identity and source locator.
- Query/context representation.
- Retrieved candidate IDs and ranks.
- Explicit relation being proposed.
- Hard contrasts and alternatives.
- Missing and rejected candidates.

**EG2 should generate candidate neighborhoods used to build new exercises.** It should not merely rank existing evaluation answers.

The formal #88 qualification is not required for exploratory proposal-only use of the already functioning EG2 runtime. Record that distinction.

## 2. Make Kev a semantic curriculum builder

Use the existing trained Kev-4B pointer-head/typed-choice API.

Present each bounded decision with:
- The relevant source-grounded semantic context.
- Already established cognitive primitives.
- EG2's candidate neighborhood.
- Explicit typed alternatives.
- A genuine abstain/needs-review option.

Ask Kev to discriminate relation family, semantic scope, valid composition, relevant inverse or contrast, and the best next concept or example to introduce.

For sequential decisions, maintain and update the semantic state after each validated step. Retrieve a fresh EG2 neighborhood if that state materially changes.

Do not repeat PR #106's mostly inert sixteen-choice scheduler. The useful output here is **validated semantic material entering the curriculum**, not a one-time swap in lesson order.

Record Kev's options, selected candidate, complete probability vector, source context, abstentions and resulting admission disposition.

No score or model output becomes authoritative merely because Kev selected it.

## 3. Validate and compile actual teaching material

Every proposed concept or relationship passes deterministic checks for:

- Source/provenance validity.
- Existing semantic identity and type compatibility.
- Logical consistency and declared scope.
- Dependency/prerequisite satisfaction.
- Collisions with existing meanings.
- Clear accepted, rejected, provisional or deferred disposition.

Authoritative meanings come from formal definitions and accepted source contracts, not EG2 or Kev.

Compile accepted relationships into stable typed semantic features and tiny worlds with mechanically checked oracle answers.

Every admitted helper contribution should be traceable through:

`source -> EG2 candidate -> Kev decision -> validator disposition -> semantic identity/relation -> lesson examples`

If a candidate fails, preserve the failure. Never fabricate an accepted concept just to satisfy a helper-use target.

No pretrained EG2 vectors, Kev weights, hidden states or answer probabilities enter the student's neural parameters or become gold labels.

## 4. U5: Necessary relational mathematics

Continue beyond elementary predicates and quantifiers into a small subset of #85:

- Sets, membership and subset relations.
- Intersection and difference.
- Functions, domain/range, inverse and composition.
- Small directed graphs, paths and neighborhoods.

Teach only the mathematical machinery needed for subsequent epistemic constructions.

Generate many tiny variations, including single-factor changes and examples combining these concepts with existing Boolean, relational and inference knowledge.

## 5. U6: Rosetta epistemic interoperation

Use accepted #84 distinctions to introduce:

- Proposition versus assertion versus observation.
- Source attribution versus formal entailment.
- Provenance ancestry versus inferential dependency.
- Evidence revision versus historical supersession.
- Current versus historical evidence state.

Example:

`DERIVED_FROM(B,A)` and `SUPERSEDES(B,A)` must remain distinct.

Construct tiny worlds where changing one typed relationship changes one conclusion without silently altering unrelated truths.

Have EG2 propose neighboring semantic distinctions and Kev discriminate typed candidate constructions before source/formal validation.

Do not introduce these as mere English vocabulary labels. They must have executable compositional meaning.

## 6. Cumulative student training

Load U4 weights and AdamW state without resetting.

Append semantic identities safely, preserving all old trained embedding rows and optimizer moments. Record new-row initialization and checkpoint lineage. Never present a fresh model as the old learner continuing.

Train a bounded local batch, targeting approximately 4,000–6,000 additional optimizer updates as hardware permits.

Mix:
- Newly admitted semantic relationships.
- Validated EG2/Kev-assisted lesson constructions.
- Cross-stage logical and mathematical compositions.
- Prior Boolean, relational, quantifier, proof and evidence tasks.
- Contrastive single-factor perturbations.

Keep the worlds tiny. The complexity should come from semantic integration.

Evaluate fixed prior-stage probes and new varied/composite probes before and after training. Retain mistakes and forgetting.

## 7. Results required

Demonstrate both sides of the system.

**Semantic production**
- Actual EG2 retrievals.
- Actual Kev decisions and abstentions.
- Admitted/rejected concept graph changes.
- New lesson families traceable to helper contributions.
- Retrieval truncation and candidate-recall diagnostics.
- Actual runtime and resource costs.

**Neural learning**
- Same-student and optimizer continuation proof.
- New-family acquisition and cross-family compositions.
- Retention of earlier abilities.
- Unseen-world performance.
- Real neural answers beside formal gold.
- Checkpoint and numerical replay evidence.

The report must distinguish:
1. Helper activity that successfully created validated teaching material.
2. Helper activity that was rejected or did nothing.
3. Student learning observed afterward.

Do not claim that helpers caused a score improvement without evidence supporting that inference.

Do not run a large attribution matrix, repeated controls, SYS-01 experiments, or expensive model scaling.

## Completion

Commit the implementation, immutable corpus and run receipts, checkpoints or reconstructible checkpoint artifacts, `RESULTS.md`, and `HANDOFF.md`.

Create a stacked draft PR against #109. Do not merge.

**Success means a continuing Bilqis has learned new, source-grounded semantic constructions whose teaching material was materially assisted by EG2 and Kev, while preserving and combining as much of her previous education as possible.**

Use the tools. Build the little worlds. Train the student. Show the answers.