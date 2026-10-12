# Bilqis formal foundations v0.4: standalone-first prerequisite experiment

**Status:** Human/Chat-authorized bounded exploratory *new* training epoch.
Independent successor to the preserved v0.1–v0.3 experiments; no inherited
student weights, optimizer, research promotions or reinterpretation of e6.

## Educational choice

The user's explicit hypothesis is that complicated teacher feedback may be
premature for the Boolean foundations, but become valuable later when the
student learns enough nuance to benefit from precise corrections in already
learned terms. e6 showed all twelve 46-token scratch students could answer
their *standalone* four-item Boolean gate, while eleven failed the same
questions behind two genuine teacher/student historical turns. That result
tests contextual sensitivity, not proof that feedback is harmful or that
dialogue should be abandoned forever.

**This epoch removes only the premature conversational promotion requirement.**
The learner still receives a single typed teacher QUESTION and a current
student ANSWER target, but never sees *previous* completed teacher/student
turns during training. All oracle labels and semantic IDs remain first-class.
No student task of grading proposed answers is admitted.

The six attempted competencies follow the accepted formal course's DAG:

1. `V00.BOOLEAN`: TRUE/FALSE, basic valuation.
2. `V01.NOT`: unary negation, dependent only on V00.
3. `V02.AND`: conjunction, independently dependent only on V00.
4. `V03.AND_NOT_RIGHT`: composition requiring passed V01 and V02.
5. `V04.AND_NOT_LEFT`: composition requiring passed V01 and V02.
6. `V05.NOT_AND`: composition requiring passed V01 and V02.

If V01 fails, V02 remains eligible. Failed stages block only dependent
descendants. Loss of an already admitted stage's retention ends the current
arm immediately. Student judgment `J00.PROPOSED_ANSWER`, all named Boolean
laws, algebraic rewriting, quantified logic, broad maths, and Ithkuil are
**deliberately not** in this experiment.

## Immutable plan for e7

Output: `runs/formal-foundations-20261012-e7-standalone-v04/`.
Seeds (fixed before seeing any outcome): **463, 467, 479**.
One scratch student per seed, initialized independently with the existing
46-token causal student topology (two layers, width 64, four heads, context
96), fresh AdamW optimizer `lr=.002, betas=(.9,.95), eps=1e-8,
weight_decay=.01`. Deterministic PyTorch execution, batch size 32.

Per eligible competency: **exactly 320 optimizer updates** and zero
remediation updates. The sampler balances oracle-gold output labels and
includes up to eight old retained-stage rehearsal examples per batch.
Stage-specific training is the human-authored mandatory set, plus the
full prevalidated pair of two-case compositional lesson contrasts
for V03–V05. Duplicate question identities are deduplicated.

There is **no Kev/LLM selection** or live teacher-model cost. This isolates
the feasibility of formal standalone acquisition before testing teacher
selection. No native Kev calls may appear in e7.

No current question's gold/feedback is included in its input. Frozen
train/lesson/formative/fixed-gate/structural identities were verified
disjoint in the preceding v0.3 curriculum and must remain so here.
Compositional formative exam panels are observed after instruction, never
backpropagated. The held-out fixed standalone gate is first **evaluated
against the student** for a given stage **after** all instruction for that
stage. The pure formal oracle may construct and validate its identities
during preflight to prove disjointness; those records cannot reach the
optimizer before the gate. Its answers never become training, remediation
or teacher-selection data.

**Promotion** requires every question in the fixed standalone gate
correct and every prior promoted stage's standalone fixed gate still
entirely correct. Exact tiny gates are provisional engineering indicators,
not calibrated general mastery. A context-bearing frozen gate remains
visible **only as a read-only diagnostic** at the end of each attempted
stage. Valid/counterfactual teacher-history sensitivity and fresh AST
structural transfer are also read-only post-training diagnostics, not
promotion criteria. Deliberately invalid past-teacher corrections never
appear in optimizer input.

The explicit research questions:

- Can a scratch learner progress into NOT, AND, and composition without
  premature dialogue-history prerequisites?
- Do the newly admitted standalone truth skills survive rehearsal and
  later stage training?
- Are contextual and new-structure transfer failures still visible when
  they no longer veto prerequisite advancement?

No feedback efficacy, general logic mastery, algebraic competence, model
scale-effect or later linguistic-learning benefit can be claimed from this
single small study. The next lesson plan must be chosen from actual
stagewise errors, not lucky seed hunting.

## Freeze, replay, and stop contract

Before the **first e7 optimizer step**, commit this protocol, the exact
runner, and its tests. A SHA-256 digest covers all imported executable
formal teaching/model code and this document, and a checked clean Git
head plus Python/PyTorch runtime is recorded in the unique
preregistration manifest. Existing output directories cannot be reused,
even after failure. All attempted stage checkpoint states, optimizer
states, seals, structural probes, per-seed results and stopped prerequisites
are preserved in the ignored local run directory.

After the complete one-time run, reload and independently reproduce
**each stage's** standalone gate and frozen contextual diagnostic against
its saved model state; report the exact pass/fail frontier for **every**
seed, including failures. No repeated seeds, modified thresholds, extra
training, curriculum promotion, merge, or closing issue #82 follows from
the outcome without a new review.

```sh
python -m unittest discover -s tests -q
python -m bilqis_formal.pilot_v4 --out runs/formal-foundations-20261012-e7-standalone-v04
python -m bilqis_formal.pilot_v4 --out runs/formal-foundations-20261012-e7-standalone-v04 --replay
```
