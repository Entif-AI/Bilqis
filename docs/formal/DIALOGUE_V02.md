# Formal dialogue curriculum v0.2: human-authored teaching contract

This is a **new versioned experimental protocol** alongside the original
`bilqis.formal.f0/v0.1.0`. It does not rewrite the original e1/e2 run
directories, trained states, optimizer history, or two-output student ABI.

## Educational decisions

The human and Chat designed the goals and prerequisites; formal Python generates
typed questions and gold; Kev chooses between comparable admitted exercises;
the scratch student predicts; promotion requires observable evidence.

The first competencies are:

| Stage | Target | Required prior competencies |
| --- | --- | --- |
| D00.PROTOCOL | Distinguish question, answer, truth value, and correctness judgment | None |
| D01.NOT | Evaluate and judge atomic NOT | D00 |
| D02.AND | Evaluate and judge atomic AND (all four cases) | D00 |
| D03.AND_NOT_RIGHT | Conjunction with negated right operand | D01, D02 |
| D04.AND_NOT_LEFT | Conjunction with negated left operand | D01, D02 |
| D05.NOT_AND | Negate the whole conjunction | D01, D02 |

The last three are **composition-specific competencies**, not harder variants
silently substituted for basic AND. The Easy/Medium/Hard names are only
structural hypotheses; learner error and held-out transfer provide empirical
difficulty evidence. Independent law schema IDs remain registered in the
underlying semantic space. Named-law training and metasyntax come **after**
these primitives and their prerequisites, not as an implicit reward for time
spent training.

## Answer and feedback ontology

The v0.2 vocabulary extends the original tokens with roles TEACHER/STUDENT,
acts QUESTION/ANSWER/FEEDBACK/CORRECT_ANSWER/PROPOSED_ANSWER/TURN_END,
TASK.JUDGE_ANSWER, separate FEEDBACK.CORRECT/INCORRECT, PROC.DIALOGUE and
explicit composition IDs. The four candidate output labels have separate
types: ATOM.FALSE/TRUE answer truth questions; FEEDBACK.INCORRECT/CORRECT
answer whether a *proposed answer* was right. Both output types are represented
by tied but distinct embeddings. Invalid output domains are masked.

An authentic training step has (1) an oracle-validated current question, (2)
the student's first prediction, (3) independent teacher feedback, and (4)
correction if wrong. The correction is visible only in **later** inputs, never
in the current question. Completed prior exchanges are placed in the actual
causal transformer's <=96-token attention window as complete turns; excess
history is dropped by turn, never cut in the middle. A past identical question
is excluded from prompt history. Batch lanes carry the student's *actual*
first-attempt predictions, not scripted claims of learning.

The first v0.2 implementation compares full teacher feedback in context,
student question/answer history **without teacher feedback**, and no history.
All arms use newly initialized identical 44-token-space architectures,
same seed/sampling plan and teacher-selected panels. The three conditions
isolate whether feedback content adds evidence beyond sequence context.

## What an exam measures

Mandatory lessons, Kev lesson candidates, Kev formative exam candidates and
the sealed promotion gate have nonoverlapping exact question IDs.
Formative testing permits per-answer feedback, records first attempts and
supports at most one bounded lesson remediation from formative errors. **No
gold/probability/gradient from sealed promotion items is offered to Kev or
the student while selecting, training, or remediating.**

### e3 finding and explicit v0.2.1 gate correction

The initial `v0.2.0` e3 experiment required closed-book success even for
the foundational *interaction-protocol* lesson. On 320 matched updates, the
feedback learner got 9/12 standalone, while the no-context control got 12/12.
A **read-only** contextual ablation of the saved models found:

- Feedback-trained learner: 12/12 with either a previously correct turn,
  a previously corrected error, or both; 9/12 with no prior turn.
- No-context learner: 12/12 without prior dialogue; 8/12 with a correct
  turn, and 6/12 with a corrected error or two-turn prefix.

This is a small but real context-distribution difference. It **does not** prove
the model used the *meaning* of the feedback. A generic prior-turn boundary
could explain it. Therefore version `v0.2.1` **preregisters** the following
before a fresh, separately named e4 run:

1. D00.PROTOCOL promotion requires the **contextual** sealed gate, using the
   same fixed two-turn teacher-demonstration primer in all comparison arms.
   The unprimed/standalone probe remains mandatory **reported evidence** but
   is not the admission criterion for a dialogue-structure lesson.
2. D01 and all later **logical** competencies require BOTH sealed
   standalone and contextual success. Their meaning must generalize beyond
   the particular teacher dialogue that presented them.
3. Retention repeats the applicable per-competency criterion; each full gate
   is exact-passing in this small pilot. This is a local provisional rule,
   not proof of statistical mastery.
4. e4 uses three conditions, a fresh prespecified seed, identical sampled
   training-question identities, shared Kev panel decisions, and fixed
   context-bearing evaluation primers. Each arm stops at its first failed
   prerequisite or retention gate. Controls do not invent teacher choices
   after the feedback arm's first stopped stage.

The change is a **new research-plan version**, not a retroactive recoding of
e3 as a successful promotion.

### e4 observation and predeclared v0.2.2 teaching correction

The fresh-seed e4 run produced D00 contextual scores of **12/12** for full
feedback, **10/12** for answer-only history, and **6/12** for no history, from
identical training-question IDs. The full-feedback arm then attempted atomic
NOT and failed: standalone **4/6**, contextual **5/6**. It did not enter AND
or any named-law training.

The training contract had required both dialogue-conditioned and standalone
NOT at promotion, but had supplied *only dialogue-conditioned examples* while
teaching NOT. Before running e5, `v0.2.2` fixes that mismatch: D00 remains
a contextual-only protocol lesson; each later logical lesson systematically
alternates **50% conversation-conditioned and 50% standalone instruction**
across the batch lanes. The control arms keep their exact selected context
conditions when context is present; the no-context control remains entirely
standalone. Identical sampler seeds and row identifiers remain auditable.

e5 uses a new prespecified seed **337**, fixed 320 main updates and at most
96 formative-remediation updates per admitted stage, the same gate policy and
max six stages. It is not a retroactive change of e4's outcomes. No gate is
weakened and no failed stage may be skipped.

**Observed e5:** full-feedback D00 10/12, answer-only 9/12, no-context
6/12. All arms stopped at D00, so no mixed-context operator training took
place. e4's NOT truth evaluation passed 2/2 both ways, while its separate
answer-correctness judgments failed. The next proposed v0.3 curriculum
would split these competencies instead of imposing both at once. This
proposal has **not** been implemented or experimentally promoted.

All e3-e5 saved model/checkpoint results replay, but a full source hash
was not captured *before* those runs. The current runner locks the runtime
source hash for future experiments; do not claim historical source locking.

## Kev's constrained task

For a composition, Kev sees two panels of exactly the same AST shape, tier,
task types, record count, and positive/negative answer distribution. The sole
difference is the Boolean valuation axis changed between a TRUE and FALSE
example. It sees concrete recent expected-versus-predicted answers and earlier
gate performance, plus the fixed human competency objective.

Every offered ID visits every answer position, and a change in winner or
low probability margin forces abstention. This is **selection stability**, not
proof of pedagogical utility. Its effectiveness must be evaluated by later
held-out learner performance. Kev does not manufacture formula ASTs, gold,
or decide that an easier competency should replace the one being taught.

## Limits

* Two-option, one-axis contrasts are intentionally narrow. No forward-transfer
  benefit or calibrated difficulty ranking has been demonstrated.
* An improvement with a fixed prefix can reflect boundary familiarity,
  attention length, or actual use of feedback. The answer-only arm and
  later adversarial feedback-content probes help distinguish these.
* Atomic Boolean inputs necessarily have few distinct truth combinations.
  Even exact success on a 12-item gate does not imply broad semantic mastery.
* Named-law schema training, causal error taxonomy and multi-seed confirmatory
  evaluations remain later, explicitly gated research.
* e1, e2 and e3 are preserved in separate ignored local directories. New
  intervention code must not reinterpret their historical scores as new runs.

## Commands

Use the existing Python 3.13 environment containing torch; do not import
pretrained student weights. The local pinned Kev service is required.

```sh
python -m unittest discover -s tests -q
python -m bilqis_formal.pilot_v2 --out runs/formal-foundations-20261012-e4 --seed 293 --max-stages 6 --steps 320 --remedy-steps 96
python -m bilqis_formal.pilot_v2 --out runs/formal-foundations-20261012-e4 --replay
python -m bilqis_formal.diagnose_v2 --out runs/formal-foundations-20261012-e4
python -m bilqis_formal.pilot_v2 --out runs/formal-foundations-20261012-e5 --seed 337 --max-stages 6 --steps 320 --remedy-steps 96
```

These commands deliberately use fresh output paths. Actual results belong in
`docs/evidence/formal-foundations/RESULTS.md`; no invented third or fourth
epoch outcome is authority.
