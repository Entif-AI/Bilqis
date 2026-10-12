# Formal foundational teaching, v0.3.0

**Status: accepted bounded exploratory implementation and preregistration, not
accepted scientific efficacy.** This human/Chat-authored contract corrects
v0.2's conflation of Boolean truth evaluation with grading another student's
proposed answer. Prior e1–e5 local evidence and v0.1/v0.2 implementations
are immutable historical experiments, not v0.3 training initialization.

## Curriculum and authority

| Stage | Student's permitted answer | Formal target | Prerequisites |
| --- | --- | --- | --- |
| V00.BOOLEAN | TRUE/FALSE | Boolean values, atomic valuation; teacher gives feedback | None |
| V01.NOT | TRUE/FALSE | Unary negation, including constant arguments | V00 |
| V02.AND | TRUE/FALSE | Four atomic conjunction cases | V00 |
| V03.AND_NOT_RIGHT | TRUE/FALSE | AND of a value and a negated operand | V01 + V02 |
| V04.AND_NOT_LEFT | TRUE/FALSE | AND of a negated operand and a value | V01 + V02 |
| V05.NOT_AND | TRUE/FALSE | Negate a complete conjunction | V01 + V02 |
| J00.PROPOSED_ANSWER | JUDGMENT.CORRECT/INCORRECT | Assess a **proposed answer** to a learned Boolean expression | All V00–V05 |

These are versioned **provisional competency boundaries**. They do not
resolve the complete #82 Stage-A law/quantifier/inference curriculum.
NOT and AND have independent prerequisite branches. A failed NOT gate
still permits the independent atomic AND lesson, but must block every
composition/judgment that requires NOT. The runner records blocked
descendants without training them. Completion of
V00–V05 does not certify named laws, inference, metasyntax or language.

The teacher always has `FEEDBACK.CORRECT` and `FEEDBACK.INCORRECT` plus
`ACT.CORRECT_ANSWER` at its disposal, even before the student is capable of
judging anybody else's answers. The *student's* later metacognitive outputs
have **different semantic identities**, `JUDGMENT.CORRECT` and
`JUDGMENT.INCORRECT`. This two-token addition creates a new 46-token ABI
and scratch model; it never imports any v0.2 model or optimizer state.

The Python evaluator supplies all gold answers. It also marks a prior
student prediction correct or incorrect, returning the correct typed answer
after a mistake. Completed prior exchanges may appear in the subsequent
causal attention window. A current question's answer or teacher assessment
is never inserted into its own input. No Kev choice can define gold,
prerequisites, difficulty class or promotion thresholds.

## Single preregistered e6 experiment

**Exact output path:** `runs/formal-foundations-20261012-e6-v03/`, new,
never replace an older experiment.

**Seeds:** 401, 409, 419. All three are committed before observing their
learning results. **No selecting a lucky seed and no rerunning an unsuccessful
seed under the same epoch identifier.**

**Learner:** separate freshly initialized 2-layer, width-64, 4-head,
96-token-window causal transformer, 46-token identity space, AdamW
lr=0.002, beta=(0.9,0.95), eps=1e-8, weight decay=0.01, gradient norm
clipped to 1; batch size 32. PyTorch deterministic algorithm mode.

**Budget:** 320 optimizer updates per admitted stage, up to 96 further
updates from selected formative remediation only after an eligible formative
failure; no extra training after exposure to the promotion gate. Maximum
seven stages; failed gates or teacher abstention block that competency
and its descendants, not unrelated already eligible primitive branches.
Four conditions are matched by seed and question-ID sampler:

1. **Full feedback:** prior student first attempt plus true teacher
   CORRECT/INCORRECT verdict and true correction on errors.
2. **Answer-only:** the student's prior question and answer, but **no**
   teacher verdict or corrective answer.
3. **Answer-only, length matched:** the same prior student question/answer,
   with the absent teacher response replaced by six neutral PAD tokens.
   Every full teacher turn has six response positions regardless of whether
   the previous answer was correct, so PAD count does not reveal correctness.
4. **No history:** only the current standalone question.

Every full-feedback and answer-only stage, including the padded control,
intentionally teaches half the
batch in standalone format and half with earlier completed turns (where
available). The no-history control trains entirely standalone.

Remediation is triggered by **each arm's own formative errors**, never by
errors in a different arm. Controls reuse the reference arm's admissible
remediation choice when it exists. If the reference arm needed no special
remediation, a control with errors can reuse the reference's already
admitted lesson contrast, marked as shared-lesson remediation. This
preserves the target/tier and avoids an unmatched extra Kev call. The
up-to-96 extra updates may therefore differ by arm; reports show actual
budgets and comparisons must not pretend identical token/optimizer exposure.

**Matched comparisons:** the same seed, model initialization, training
question IDs, core curriculum, eligible panel choice and steps for each
shared attempted stage **while their admitted rehearsal history remains
identical**. If independent branches diverge, rehearsed question IDs may
differ even in a commonly attempted later stage. The report explicitly
flags mismatched sampling; such observations are not paired efficacy
comparisons. Each arm's prior answers are generated by its own
student, so these are realistic adaptive trajectories and not identical
token streams; the recorded source-token counts expose that distinction.
When the full-feedback arm stops, a control cannot conjure further Kev
decisions past that common frontier. Cross-arm comparisons are confined to
the actually shared stages. Kev decisions, when eligible, are selected
using the full-feedback learner's errors and reused by controls. That
choice is treatment-dependent; a separate teacher-independent experiment
would be necessary for a clean causal attribution.

Kev is only permitted for V03–V05 compositions, where two equally sized
near-neighbor panels have the same operator schema, tier and answer balance.
Every candidate rotates through both positions. An unstable choice, error
or insufficient margin **halts** the affected stage; there is no easy-panel
fallback. The exact live Kev runtime must match the preconfigured model ID.

## Evidence and promotion

Training, offered lesson panels, formative exams, and sealed promotion
questions have **disjoint question identities**. Each sealed evaluation is
performed only after that stage's permitted training and formative correction.
For this tiny engineering pilot, promotion requires exact success on both
the standalone and fixed two-turn conversational held-out forms (one
correct student answer and one corrected mistake), plus
retention of both forms from every prior admitted stage. The context primer
comes exclusively from stage training examples and is **identical for every
held-out item**; its selection does not depend on any held-out gold.

This all-correct rule is a local hard gate, **not** a statistically powerful
mastery claim. Report every attempted stage, score by answer type, which
prerequisite stopped progression, retention, and whether each arm actually
received mixed instruction. Do not infer success from a model's confidence
or from a selected formative panel alone.

All arms receive the **same full-feedback contextual held-out test**, even
the answer-only and no-history controls; it is deliberately out-of-training
distribution for those controls. Their standalone score is the cleanest
common-presentation Boolean outcome; the contextual score measures
transfer into the target conversational interface, not just truth
under native treatment. Retention failure halts the entire arm rather
than permitting further study on revoked prerequisite evidence.

## Secondary, fixed diagnostic probes, NOT promotion

After that stage's gradients are finished, evaluate saved model predictions
under **five** frozen-input conditions, all holding the current question
constant and never choosing a primer from its gold:

- two distinct, equally long, **oracle-valid corrected** prior turns
  exhibiting opposite answer labels, chosen from training examples;
- a deliberately **invalid counterfactual correction** obtained by flipping
  exactly one *past* `ACT.CORRECT_ANSWER` value while preserving every
  other token, length and current question;
- the same prior student question/answer with teacher text replaced by
  equal-length neutral PAD tokens;
- no prior turn.

The counterfactual is an **adversarial probe only**. It is never legitimate
teacher feedback, a training example, a gold label or a promotion condition.
Raw prediction differences, number of switches and gold probabilities are
recorded. If a single teacher-correction token changes the prediction, that
is **token sensitivity**, not automatic proof of semantic learning. Opposite
valid examples can also prime the answer label. Reports must preserve
those competing explanations.

An additional **structural-transfer diagnostic** is frozen before the run
for V02–V05 and J00. It evaluates mixed literal/variable terms such as
`AND(TRUE,R)`, `AND(TRUE,NOT(R))`, `AND(NOT(R),TRUE)`,
`NOT(AND(TRUE,R))`, and downstream judged variants. These are new
expression shapes not in the stage's primary training set. They are
**not** used to select examples, remediate, or promote. Passing the core
same-shape gate alone cannot establish general structure transfer; this
probe exposes the gap rather than hiding it.

All source files necessary for the actual learner/teacher/oracle/runner
and this predeclared protocol are hashed before run creation. Each arm's
manifest includes the hash; the runner checks no source mutation during
the run; checkpoint replay rejects source drift and re-evaluates **every
saved stage**. The runner requires a clean Git checkout, captures its
exact source commit and Python/PyTorch/machine version, preflights
the pinned Kev runtime before creating the output directory, and uses
atomic checkpoint and JSON artifact publication. A missing aggregate
comparison is an incomplete run, not success. Older e1–e5 runs had
different source-lock provisions and must not be retroactively claimed
source-locked.

## Pre-execution verification and honest conclusions

Run the entire repository test suite and exercise short deterministic
engineering regressions, including incorrect/correct Boolean cases, stage
prerequisites, stage gate independence, prior-turn-only feedback, equal-length
diagnostic pairs and invalid feedback exclusion from optimizer input.
Commit this protocol and its exact source implementation **before** running
e6, then run precisely once.

**Primary descriptive outcome:** per-seed and per-arm stage scores, attempts,
promotion/stop point, and paired differences only on commonly attempted
stages. **Secondary:** history-length effects and sensitivity to a past
correction token. With three small seeds and very small Boolean gates,
this is **exploratory**, not a significance test, a proof of durable
generalization or a claim about language/AGI.

To run and verify:

```sh
python -m unittest discover -s tests -q
python -m bilqis_formal.pilot_v3 --out runs/formal-foundations-20261012-e6-v03
python -m bilqis_formal.pilot_v3 --out runs/formal-foundations-20261012-e6-v03 --replay
```
