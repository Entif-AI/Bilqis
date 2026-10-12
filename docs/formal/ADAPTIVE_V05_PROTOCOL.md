# Bilqis trainee comptroller v0.5: adaptive foundations, matched e8

**Research posture:** New bounded experiment, deliberately not a modification
of frozen e6/v0.3 or e7/v0.4. No merge authorization or #82 acceptance.
This answers the user's concern that 320 fixed updates can prematurely end
improving learning or discover forgetting only after all 320 updates.

## Actual input format, no free-form correction prose

Both earlier dialogue and this experiment use Python records and a typed
**token-ID sequence** rather than textual JSON. The old full dialogue's
completed turn is `ROLE.TEACHER ACT.QUESTION <typed expression>
ACT.TURN_END ROLE.STUDENT ACT.ANSWER <student atom>
ACT.TURN_END ROLE.TEACHER ACT.FEEDBACK FEEDBACK.INCORRECT
ACT.CORRECT_ANSWER <oracle atom> ACT.TURN_END`, or
`FEEDBACK.CORRECT` with equal-length PAD filler when it was correct.
The correction belongs to that preceding completed turn; the teacher
does not repeat a nested JSON copy of its question.

As in e7, **e8 optimizer input contains only the current question prefix**
ending in `ROLE.STUDENT ACT.ANSWER`, with the current supervised oracle
truth label supplied to the loss function separately. No completed prior
turns, metacognitive correctness judgment, or native Kev calls are used.
Nothing in this control experiment establishes that the student can
interpret retrospective teacher feedback.

## Corrected educational split

The finite e7 stage V01 trained only `NOT(P/Q)`, but its tiny frozen exam
also tested `NOT(TRUE/FALSE)`. No amount of repeating the old variable-only
questions guaranteed learning the unpresented constant form.

e8 therefore deliberately **changes the versioned split**. The three
atomic competencies are:

| Competency | Training | Periodic DEV (selection permitted) | SEALED (one post-stage evaluation) |
|---|---|---|---|
| V00 Boolean | TRUE, FALSE, P | Q | R |
| V01 NOT | NOT(P), NOT(TRUE), NOT(FALSE) | NOT(Q) | NOT(R) |
| V02 AND | AND(P,Q), four literal pairs, AND(P,TRUE), AND(FALSE,P) | AND(Q,R), AND(TRUE,Q), AND(Q,FALSE) | AND(R,P), AND(TRUE,R), AND(R,FALSE) |

All valuation rows are exhaustively enumerated within each expression
shape and source IDs are disjoint **within e8**. The old e7 exam literals
are now explicitly **training** examples, so e8 cannot be read as a rerun
of e7's sealed exam. The literal-NOT domain is tiny and exhausted;
literal retention is a *taught-domain coverage* check, **not unseen
literal generalization**. The sealed NOT(R) tests variable transfer.
No learner weights, optimizer or labels from e7 are reused.

No V03–V05 compositions, J00 correctness-judgment student task, laws,
maths, Rosetta or Ithkuil are taught in this **controller calibration**
experiment. Later versions can extend the graph once atomic retention is
demonstrably stable.

## Preregistered budget, arms and curriculum steering

**One run only**, at
`runs/formal-foundations-20261012-e8-adaptive-v05/`.
Three fixed seeds **463, 467, 479**. For each seed initialize three distinct
scratch students with **identical weights**, fresh AdamW optimizer, same
versioned train/DEV/gate sets and the same 46-token ABI,
64-dimensional embeddings and two-layer scratch model from e7; compare:

- `fixed320`: five **64-update** blocks per admitted stage; do not use DEV
  or mistakes to steer sampling, extension or retention repairs. DEV and
  training curves still recorded. Total 320 updates per stage.
- `fixed1280`: twenty **64-update** blocks, exactly 1,280 updates
  per eligible stage, without DEV-directed prioritization or retention
  repair. This **compute-matched long-training reference** distinguishes
  extra optimizer time from an adaptive training-policy improvement.
- `adaptive`: **minimum 320**, **maximum 1,280 total updates per stage**,
  in 64-update blocks. Every block records mean/final training loss,
  first-attempt performance, sample/label-family exposures, current DEV
  accuracy, taught-domain literal coverage and previous-stage DEV/literal
  retention.

Both arms use batch size 32, real gradients with AdamW
`lr=.002, betas=(.9,.95), eps=1e-8, weight_decay=.01`, and zero
previous dialogue history. Normal blocks draw 24 current + 8 prior
rehearsal rows when earlier skills exist. Rehearsal uses previous
**actually taught** lessons, not just those whose tiny sealed exams
passed, to avoid letting a sibling's gate dictate its inclusion in
future training. **Repair monitors include all earlier actually taught
skills**, regardless of sealed exam outcomes or DEV perfection; the sealed
exam determines prerequisite admission only, not which independent-sibling
skill receives repair.
At the start of a new stage, record each monitored prior skill's actual
DEV and taught-literal accuracy: a passing SEALED gate does not imply
the distinct DEV was perfect. If a monitored prior skill drops
**below its measured pre-stage performance**, the adaptive controller
may spend at most
**256 steps total on retention repairs** for that stage, drawing
24 from the damaged prior + 8 current. Classifier family weighting
uses TRAIN and DEV errors only, with **at most 4:1 relative
family-level draw weights** after compulsory family floors; family size
does not silently change its priority. Each batch is 50/50
oracle TRUE/FALSE with at least one sample from each available
train-family/label combination. A repair never trains on DEV rows.

At each block end adaptive policy uses **only** DEV and taught-domain
coverage:

1. If any monitored DEV or taught-domain literal skill deteriorates
   below its **pre-stage baseline** (not simply below a perfect score),
   allocate the next block to limited prior-skill repair.
2. If the 256-step repair allowance is exhausted while forgetting
   persists, **rollback the model and optimizer to the pre-stage state**.
   Record the spent updates separately from the surviving model's steps.
   The current stage is not admitted, and an independent later stage can
   still be attempted.
3. Below 320 updates, continue (unless repair allowance forces rollback).
4. At or above 320, stop on **two consecutive** complete DEV/literal
   coverage and healthy prior retention checks; otherwise stop if the
   last **three** block-to-block transitions fail to increase combined
   correct count, with DEV negative log-likelihood as a tie-breaker
   for equal accuracy, or when hitting the 1,280-step cap. Continuing
   improvement retains a budget to proceed.

The DEV sets are intentionally tiny and repeatedly reused. This policy
can overfit them, so its result is a *controller feasibility test*, not
a claim that generalized learning rates are reliably estimated.

**SEALED gate firewall:** final heldout gate and prior sealed retention
are first evaluated only after the stage's chosen blocks stop. A
sealed result **does govern admission to dependent later competencies**,
but cannot guide an otherwise eligible stage's extra block count, repair
choice or sampling weights, nor independently select repair targets
for sibling competencies. Final promotion requires 100% of sealed target,
100% of taught-domain literal coverage and unchanged previous sealed
competences + literal coverage. If a previous skill loses its
sealed performance **or taught literal coverage** at this final boundary,
mark an unrepaired scientific failure and stop
the arm; **never repair against final-exam feedback in the same run**.
The standalone correctness of current/previous stage is the only
promotion authority. A missed current exam blocks only its dependents.

## Durable evidence and acceptance limits

Before the first e8 optimizer step: source+protocol+tests must be
committed, clean, locked to source SHA-256 and captured in a new
immutable preregistration. The source lock covers code, ABI and this
protocol. Each block stores policy decision, training loss/accuracy
curve, row-family exposure tally, sample digest, DEV per-question
correctness, class-conditional truth scores, DEV log-loss and
retention. Each 64-update block saves a model/optimizer checkpoint
and replay independently re-evaluates its DEV evidence, recomputes
sampler identity and selection decisions from the saved model.
Each stage also saves model/optimizer checkpoint with exact
stage/seed/arm identity. Per-seed/arm reporting is exhaustive, including
failures, rollback steps, unused budget, and skipped prerequisites.
Replay independently checks actual saved model gates, source SHA,
accepted DAG, optimizer state including AdamW moments, effective step,
budget, DEV-based controller decisions, sampled-row custody,
retention and aggregate consistency. This is *checkpoint replay*
and not a full from-scratch replay of every historical gradient.

This is a **matched-source/controller comparison with both an efficiency
anchor (320) and compute-matched nonadaptive reference (1,280)**,
not fixed versus adaptive evidence in the old e7 curriculum.
The adaptive arm may stop early, so actual compute must be reported
alongside outcome. None of these arms establish
general logic mastery, future Ithkuil benefits or causal efficacy of
teacher dialogue. No cherry-picking, changed caps, retrials, or merges.

```sh
python -m unittest discover -s tests -q
python -m bilqis_formal.pilot_v5 --out runs/formal-foundations-20261012-e8-adaptive-v05
python -m bilqis_formal.pilot_v5 --out runs/formal-foundations-20261012-e8-adaptive-v05 --replay
```
