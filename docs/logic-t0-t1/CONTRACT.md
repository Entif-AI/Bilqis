# CODEX: BILQIS T0/T1 LOGIC LEARNING

**Single controlling execution contract.** This prompt contains the necessary research requirements. No prior conversation, prompt, or GitHub issue body is needed to interpret it. Inspect repository code and existing run state for implementation reuse, not to rediscover the research objective.

## Mission

Train one tiny scratch neural student on **primitive cognitive algebra**, beginning with Boolean truth functions and progressing to logical equivalence and unseen compositions.

This is an exploratory T0/T1 pilot, not a complete developmental curriculum or confirmatory study.

The first required lessons are:

- `TRUE AND TRUE → TRUE`
- `TRUE XOR TRUE → FALSE`
- `TRUE IMPLIES FALSE → FALSE`

All training inputs must be machine-native, typed semantic tokens/ASTs. The strings above are human-readable illustrations.

## Exact semantic contract

Use two-valued classical Boolean semantics for this pilot.

Supported atomic values: `TRUE`, `FALSE`.

Supported operators: `NOT`, `AND`, `OR`, `XOR`, `XNOR`, `IMPLIES`, `IFF`.

Supported abstract proposition variables: `P`, `Q`.

`NOT` is unary. Every other operator is binary.

| P | Q | AND | OR | XOR | XNOR | IMPLIES | IFF |
|---|---|---|---|---|---|---|---|
| T | T | T | T | F | T | T | T |
| T | F | F | T | T | F | F | F |
| F | T | F | T | T | F | T | F |
| F | F | F | F | F | T | T | T |

`NOT(TRUE)=FALSE`; `NOT(FALSE)=TRUE`.

`IMPLIES(P,Q)` is directional. `IFF` and `XNOR` are truth-functionally equivalent but retain distinct operator identities.

A typed expression consists of a Boolean literal or variable, or an operator applied to correctly typed operands. Evaluation with variables includes their Boolean assignments.

The deterministic oracle computes gold targets independently. **The neural forward pass must generate predictions without calling that oracle or receiving its answers through encoded inputs.**

## Initial semantic geometry

Use a versioned deterministic semantic initializer compiled from project-owned formal structure:

`semantic identity → validated features → deterministic width projection → initial embeddings`

Represent justified operator characteristics including arity, truth-functional signature, symmetry, complementarity, directionality and equivalence relationships.

The primary profile is `semantic_aligned`. Record its feature schema, seed/transform, token mapping, initial tensor hashes and pre-training predictions.

Preserve compatibility with matched `iid_random` and `semantic_permuted` controls. A cheap matched control is welcome after the first working learner, but is not a prerequisite.

Pretrained assistance is permitted **upstream**: EG2 may suggest semantic neighborhoods and Kev may score bounded mapping/curriculum proposals. Accept relationships only after formal validation. Do not transfer pretrained vectors, hidden states, or task-capable weights into the primary student. Existing truth tables are sufficient to compile this initial kernel without additional helper inference.

## Learning experiment

**Phase A: primitive acquisition.** Train on all exhaustive unary/binary truth-table cases. Record actual neural predictions before training and afterward.

**Phase B: algebraic compositions.** Train on a bounded set of short expressions and equivalence examples. Include double negation, identities, commutativity, De Morgan, implication rewriting and XOR/IFF complementarity.

**Phase C: held-out generalization.** Evaluate unfamiliar expression trees and operator nestings, plus balanced equivalent/non-equivalent pairs.

Equivalence means two expressions agree under every possible assignment of their free variables. Include a directional counterexample distinguishing `IMPLIES(P,Q)` from `IMPLIES(Q,P)`.

Freeze and verify TRAIN/DEV/HELDOUT structures before training. Do not leak exact held-out compositions or their canonicalized answers into model inputs, initialization or curriculum decisions. The model must see the expressions it is solving, not a precomputed solution.

Report primitive memorization and compositional transfer **separately**. Neither success is assumed.

## Execution and quota discipline

Recover the halted worktree safely. Preserve existing ALPHA-01/02 and Decision Epoch 02 evidence, including open PR #106 and predecessor PRs #104/#105. Create an independent feature branch for this experiment. Selectively reuse the working neural model, optimizer, checkpointing and local runtime.

Before substantial implementation, print three **actual encoded machine inputs** corresponding to the three initial examples, their formal gold outputs and the neural prediction interface. This is the objective-alignment gate.

Then:

1. Validate the truth-table oracle and token/AST round-trip.
2. Run a real neural forward/backward pass and verify gradients and parameter updates.
3. Execute one bounded training cycle on the existing fastest proven local backend.
4. Evaluate primitive accuracy, held-out composition, equivalence and hard negatives.
5. Save checkpoint hashes, training measurements and a compact results report.
6. Commit, push and verify the resulting feature branch.

Aim to reach the first genuine T0/T1 neural training step within approximately 15–20 minutes of active execution. If blocked, preserve the exact failure and hand off rather than expanding into another implementation campaign.

Use one focused repair only for a diagnosed defect. Record the complete attempt, including null or negative outcomes.

## Required completion evidence

Report:

- Step-zero versus trained neural predictions, with exhaustive truth-table scores.
- Held-out composition and equivalence/non-equivalence scores.
- At least one concrete successful or failed unseen expression.
- Architecture, parameter count, initializer identity, data/split hashes and checkpoint hashes.
- Examples, optimizer steps, elapsed time, resource consumption and any helper-preparation cost.
- Reproduction command, committed evidence path, remote commit and any remaining blocker.

Checkpoint meaningful work in the repository and leave a compact **standalone recovery handoff** before interruption or compaction. It must identify the mission and next executable step without referring to this conversation.

**Authorized:** create and push an independent feature branch and review PR with source and evidence. **Not authorized:** merge PRs or modify the frozen historical experiments.

**Success:** a real scratch-trained Bilqis neural student acquires Boolean cognitive-algebra operations and produces measurable, independently graded results on new compositions.

Implement the smallest correct experiment. Train it. Measure it. Preserve the evidence.