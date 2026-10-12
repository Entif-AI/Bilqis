# Fresh formal-foundations pilot: actual local evidence, 2026-10-12

**Posture:** exploratory, source-backed, independently scratch-trained;
no previous Bilqis model, optimizer or token IDs were copied. No user-authorized
later stage was reached or promoted by fiat. Tested on an Apple Silicon runtime
with live operator-owned local Kev-4B, using a pinned model identity.

## Deliberately preserved first attempt (e1): invalid prerequisite probe

The first run incorrectly asked whether fresh `NOT(NOT(R))` and triple-NOT
compositions were understood **before** teaching double negation as its own
named law. It stopped after 320 student optimizer updates:

| Stage | Pre / fixed gate | Post / fixed gate | Why it stopped |
| --- | --- | --- | --- |
| F01.NOT | 3/6 | 4/6 | Double-NOT failed 0/2; single-NOT succeeded 2/2 |

Its Kev lesson choice was `ORDER_UNSTABLE` (votes 2–1); Kev exam selection was
stable, but the composition requested by this early exam was unauthorized by
the learning order. The old e1 files are preserved as evidence of the harness
error; **do not represent its aggregate result as a failure of atomic NOT**.

The error was corrected *in source* before a second, separate scratch run:
F01 now tests the two fresh single-NOT valuation cases, and the repeated-NOT
evaluations live under the later named `LAW.NOT.INVOLUTION` gate. F01 has no
invented Kev composition decision because no meaningful composition exists yet.

## Corrected second attempt (e2)

The second run reset scratch weights from the same explicitly frozen seed and
kept the prior evidence untouched. Budget: at most six stages, 320 optimizer
updates per attempted stage, three order-rotations per Kev lesson/exam choice.
It stopped as soon as a stage failed its fixed promotion gate.

| Stage | Before | After | Easy | Medium | Hard | Promotion |
| --- | ---: | ---: | ---: | ---: | ---: | --- |
| F01.NOT | 1/2 | **2/2** | 2/2 | Not introduced | Not introduced | **Passed local gate** |
| F02.AND | 6/12 | **8/12** | 4/4 | 3/4 | 1/4 | **Stopped**, not mastered |

NOT retention after the AND stage was **2/2**. The model learned the held-out
single-NOT cases and the simple AND combinations. It *did not* handle
mixed/composed operations reliably. One miss was `P AND NOT(R)` under
`P=TRUE, R=FALSE`: formal TRUE, neural FALSE. Three further misses were
`NOT(Q AND R)` when the conjunction was false: formal TRUE, neural FALSE.

Kev was reached in F02 on both roles, using the same live three-rotation panel
policy. It returned stable choices in both cases:

- **Lesson:** `Q AND P` reversed operands (3/3 votes; mean probability ~0.453).
- **Formative exam:** `P AND R` (3/3 votes; mean probability ~0.731).

Kev's selected formative exam scored **4/4**, but the fixed gate scored **8/12**.
The selected panels were the simple choices, rather than those probing NOT+AND
composition. **This is evidence of a lesson/exam selection defect**: a
teacher-choice policy unconstrained by competency-specific difficulty can make
an incomplete student look ready. The fixed gate successfully prevented this
from becoming a false promotion.

The run used **640 actual optimizer updates** and **6 actual Kev choice calls**;
it did not consume the remaining stage budgets or enter named-law teaching.
The complete decision probabilities, local usage records, student predictions,
checkpoint optimizer states and hashes are preserved in ignored local run files:

```
runs/formal-foundations-20261012-e1/
runs/formal-foundations-20261012-e2/
```

e2 replay using the saved model produced the exact post-run state hash
`af73ca3c695325b85af05623002f2d08e52612890a6007a392e6309f9610da3e`
and the same `8/12` gate predictions. Full repository suite: **40 tests passed**.

## Open educational decision, before another run

The observed problem is *not* lack of available future laws. We have law IDs
and schema oracles waiting, but the learner must first master the compositions
that connect them. A defensible next curriculum revision is to require each
Kev-selected lesson and formative exam panel to provide candidate compositions
**within an approved difficulty tier**, or to cover each already admitted tier,
rather than permitting Easy to crowd out Medium and Hard. This should be
settled with the human curriculum designer, tested with mocked order
permutations, and then run as a clearly separate third epoch. At this
initial e1/e2 checkpoint, no third run had occurred and no later law was
claimed as learned. The separate e3-e5 follow below.

## Versioned teacher-dialogue experiments e3, e4, e5 (October 12)

The new `dialogue.py`, `course_v2.py`, `student_v2.py`, `kev_v2.py`
and `pilot_v2.py` form a **separate 44-token experiment**. They do not load
old Bilqis checkpoints or optimizer states. The output domain has distinct
truth values (`ATOM.FALSE/TRUE`) and feedback judgments
(`FEEDBACK.INCORRECT/CORRECT`). During instruction each new question may
attend to earlier completed question/answer/teacher-feedback turns, including
oracle-checked correction after an actual wrong student prediction. The
current question's gold/feedback is never included in its input.

| Epoch | Seed | Full-feedback contextual D00 /12 | Answer-only contextual D00 /12 | No-context contextual D00 /12 | Progress |
| --- | ---: | ---: | ---: | ---: | --- |
| e3 v0.2.0 | 211 | 12 in read-only contextual ablation, **9 standalone** | Not run | 6–8 depending on primer, **12 standalone** | Original standalone D00 rule stopped feedback arm |
| e4 v0.2.1 | 293 | **12** (4 standalone) | **10** | **6** (12 standalone) | Full-feedback passed contextual D00, then failed NOT |
| e5 v0.2.2 | 337 | **10** (8 standalone) | **9** | **6** (12 standalone) | All arms stopped at D00 |

At D00 the *actual sampled training-question ID digests matched* across
the participating arms in each run. Each attempted stage received 320
optimizer updates; e4's full-feedback arm received 640 across D00 and D01.
No composition competency was reached. **Zero native Kev selection calls**
occurred in e3-e5 because no run passed the prerequisites for the first
nontrivial compositional Kev panel. The equal-tier, same-AST, balanced
diagnostic selection and answer-order checks are regression-tested using
deterministic stub teachers, not experimentally validated with live Kev.

In e4, NOT truth-function **evaluation passed 2/2** both standalone and
contextually. Its *proposed-answer correctness judgment* failed: 2/4
standalone, 3/4 with prior dialogue. The 4/6 and 5/6 totals therefore
should **not** be described as failure of the NOT truth table. In e5,
the full-feedback learner answered all four basic D00 truth questions
correctly, but falsely called each incorrect proposed answer CORRECT
in the standalone condition; it missed two such cases with a full
dialogue primer. That is evidence of a correctness-label shortcut or
transfer failure, **not a proven causal diagnosis**.

### Frozen gates and the corrections they exposed

e3 originally demanded no-context transfer to promote a lesson whose
declared target was the interactive *dialogue protocol*. The saved result
was preserved, not retroactively passed. The predeclared v0.2.1 e4 rule
tested D00 with the same fixed, two-turn corrected teacher primer for
all arms; logical operators required BOTH contextual and standalone
held-out success. e4 then failed NOT, exposing that its teaching had
only used dialogue-conditioned instruction even though its gate also
required standalone performance. v0.2.2 prespecified 50/50 standalone
and context-bearing *operator teaching* before e5, but e5 stopped at
D00 and never actually exercised that new operator-teaching procedure.
These changes are new research plans, **not retroactive relabeling**.

Each arm's final checkpoint and saved gate results in e3, e4 and e5
reloaded successfully with `pilot_v2 --replay`, with matching state hashes.
This checks model/prediction replay, not a complete optimizer or Kev replay.
These runs did **not** pre-record a full source checksum, a reproducibility
gap shared with the historical e1 first attempt. The current runner now
calculates a runtime-source SHA-256 in future run manifests, checks it
during a run and rejects mismatched source on replay. Do not retroactively
claim e3-e5 were source-locked.

Ignored, locally preserved evidence:

```text
runs/formal-foundations-20261012-e3/
runs/formal-foundations-20261012-e4/
runs/formal-foundations-20261012-e5/
```

### Next Chat-authored educational decision

The new evidence favors decomposing operator **truth evaluation** and
**judging the correctness of a proposed answer** into separate explicitly
taught and tested competencies. That is a v0.3 *proposal*, not already
implemented/admitted curriculum. Further controlled probes should distinguish
feedback meaning from generic turn-boundary or input-length effects, and
test the mixed-context lesson before claims of retention or live Kev
pedagogical advantage. None of the named laws has been taught in e3-e5.
No issue #82 completion or general semantic mastery is claimed.

## Teacher-first v0.3, preregistered e6, 2026-10-12

### Frozen pre-run source and experimental contract

Human/Chat approved a new teaching order: first learn Boolean truth values,
atomic NOT/AND and their separate compositions with TRUE/FALSE student
responses; **only after all prerequisites** may Bilqis learn to judge
someone else's proposed answer. Throughout, the teacher can still say
`FEEDBACK.CORRECT`, `FEEDBACK.INCORRECT` and provide the correct answer
after a student's actual mistake. Student-side judgment identities
`JUDGMENT.CORRECT/INCORRECT` are distinct tokens, in a new **46-token**
scratch ABI. No v0.2 learner weights or optimizer state were imported.

Before any e6 optimizer update, the source + exact preregistration were
committed as **`6da9325b56a1fad82ed643ef71085da438c01653`**, with
runtime-source SHA-256:

```text
b0ce4a9b2abfba22dd44db8d609e8b92988c6bb329c7040f202e0d752b439abd
```

Exact protocol: `docs/formal/DIALOGUE_V03_PROTOCOL.md`; output:
`runs/formal-foundations-20261012-e6-v03/` (ignored, locally preserved).
Python 3.13.12, PyTorch 2.10.0, arm64, newly initialized 2-layer/64-width
student. Three preregistered seeds **401, 409, 419**, each with four
conditions, 320 optimizer updates per attempted stage and a hard maximum
96 extra remedial updates. Full-feedback and answer-history conditions
systematically mixed standalone and context-bearing inputs; the
no-history condition received standalone inputs. The answer-only/PAD arm
was designed to match the full-feedback arm's sequence lengths without
revealing the verdict through padding count. Both receive equal source
token exposure for each matched seed; ordinary answer-only and no-history
read fewer tokens.

### Actual e6 held-out results

| Preregistered seed | Full feedback, standalone / contextual | Answer history only, standalone / contextual | Answer-only + matched PAD, standalone / contextual | No-history, standalone / contextual |
| --- | --- | --- | --- | --- |
| 401 | 4/4 / **2/4** | 4/4 / **2/4** | 4/4 / **4/4** | 4/4 / **2/4** |
| 409 | 4/4 / **2/4** | 4/4 / **2/4** | 4/4 / **2/4** | 4/4 / **2/4** |
| 419 | 4/4 / **2/4** | 4/4 / **2/4** | 4/4 / **2/4** | 4/4 / **2/4** |
| **Totals** | **12/12 / 6/12** | **12/12 / 6/12** | **12/12 / 8/12** | **12/12 / 6/12** |

Across all 12 fresh students, the standalone V00.Boolean truth probe
passed **48/48**. Ten students failed their conversational gate at 2/4;
one additional failed it at 2/4 in the padded arm; only the seed-401 padded
arm passed both. More precisely: **11/12 failed contextual promotion**,
one passed, but that single successful padded arm could not continue into
V01 under the shared full-feedback reference-teacher frontier. No V01 NOT,
V02 AND, composition, student-judgment or named-law *training* actually
occurred in e6.

These data do **not** show a full-feedback learning advantage. Padded
answer history performed modestly better in this extremely small
single-epoch sample, but only one seed showed the difference. The same
source-verified question sampling digests match across all arms within
each seed's attempted V00 stage. The three-seed design is far too small
for a broad statistical or scientific generalization.

### Error mechanism observed, but not established

The fixed conversational gate uses one oracle-valid correct previous turn
and one oracle-valid, corrected previous error, taken from training
examples and held constant **for every** held-out current question.
In seed 401, the full-feedback student incorrectly answered TRUE for
both held-out FALSE valuations, despite getting both standalone FALSE
questions right. In seed 409, it incorrectly answered FALSE for both
TRUE valuations. This strongly indicates **input-history sensitivity**,
not loss of the plain atom/valuation truth lookup.

The preregistered, frozen, one-token deliberately-invalid *past*
correction diagnostic changed zero of four predictions for the
full-feedback model at all three seeds. It changed two for seed-401's
otherwise passing padded control, and varied among other controls.
The invalid correction was NEVER taught to the student and never used
for gold/promotion. Response/no-response to this token is not proof
of understanding correct feedback. The opposite-label honest-primer
and matched PAD conditions leave multiple plausible mechanisms:
attention to previous answer labels, position dependence, learned
prefix shortcuts, or inability to disentangle completed historical
utterances from the current question.

### Verification and hard limits

- All **71 repository tests passed** before the run, including
  truth-versus-grading separation, stage DAG, no current-answer leakage,
  oracle/panel validation, equal-length interventions, checkpoint
  recovery and unauthorized-parameter rejection.
- Exactly **12 × 320 = 3,840 optimizer updates** were executed in e6;
  no remedial budget was consumed and **zero native Kev selection calls**
  occurred because no composition skill was eligible.
- Every arm's checkpoint was reloaded and its model hash and **every
  completed stage's standalone/contextual gate** recalculated successfully
  via `python -m bilqis_formal.pilot_v3 --out
  runs/formal-foundations-20261012-e6-v03 --replay`: `VERIFIED`.
- The e6 local files include preregistration, source SHA, original Git
  commit, pinned teacher runtime identity, per-stage prediction errors,
  feedback-content sensitivities, actual token/update budgets, optimizer
  checkpoint and exact hash.
- A local shell wrapper returned a nonzero exit after Python had already
  finished because zsh reserves the shell variable `status`. Live
  inspection confirmed the complete `comparison.json` plus all
  12 reports, and **read-only checkpoint replay succeeded**. No
  training was repeated or experiment path reused to hide that artifact
  of the command wrapper.
- e6 contextual promotion applied the same **full teacher dialogue**
  to all arms. That is out-of-distribution for no-history and answer-only
  controls; their standalone scores are the cleaner common-format
  Boolean comparisons. The experiment used reference-arm-dependent
  teacher planning, although no Kev panels were ultimately eligible.
- V00 is only a four-question held-out gate. Passing 4/4 is evidence of
  bounded behavior in this small world, not durable semantic mastery.
  Likewise, an e6 prerequisite stop does not prove those students would
  have failed NOT or AND if subsequently taught.

**Next proposed Chat-mode research decision:** test whether Bilqis can
identify the *current* question invariantly under randomized, balanced,
genuinely completed historical turns, using frozen-position controls and
separate contextual-retention goals. Distinguish identity/value inference
from teacher-feedback comprehension. A newly approved version and new
preregistration would be required. Do **not** edit/relabel e6 after seeing
its scores, pick a more favorable seed, or merge #115 on this evidence.

## Standalone-first v0.4, preregistered e7, 2026-10-12

### Deliberate educational change, frozen before training

Following e6, the human/Chat decision was to let the learner acquire
fundamental Boolean truth functions **without making historical teacher
dialogue comprehension a prerequisite**. Teacher/proposed-answer judgment,
named laws, general mathematics, and Ithkuil remain planned but deferred.
The v0.3 course's semantic identities, oracle labels, and complete prior
e1–e6 evidence were preserved. e7 uses the same fresh 46-token scratch
student topology as v0.3 but only the current question and answer target
appear during training; earlier completed turns never enter attention.

The policy and source were committed and pushed **before any e7 optimizer
step**:

- Exact pre-run commit: `c830db239b5eb97bbaa0665b6e1fed98521a23ad`
- Runtime-source SHA-256:
  `ff8f11ce7e0485ffa4616814576f362a685a908678c2f1db4c2f5a6199e8d4a5`
- Contract: `docs/formal/DIALOGUE_V04_STANDALONE.md`
- Original run path:
  `runs/formal-foundations-20261012-e7-standalone-v04/` (ignored, locally retained)
- Seeds **463, 467, 479**, new scratch weights and AdamW per seed.
- Exactly 320 optimizer updates per eligible attempted competency, with
  oracle-validated fixed lessons and two deterministic composition contrasts
  when eligible. Zero remediation, zero native Kev decisions.
- **Promotion** based solely on independent held-out standalone answers
  and all earlier admitted standalone retention; full contextual dialogue
  and structural transfer remained frozen **diagnostics only**.
- Independently gated NOT and AND branches; a failed NOT may block
  compositions but does not block eligible atomic AND.

### Actual e7 held-out outcomes, no seed selection

| Seed | V00 Boolean standalone / contextual | V01 NOT standalone / contextual | V02 AND standalone / contextual | Actual promotion |
| --- | --- | --- | --- | --- |
| 463 | **4/4** / 2/4 | **4/4** / 2/4 | **4/4** / 3/4 | V00 and V01 passed, but **retention stopped** after AND |
| 467 | **4/4** / 2/4 | **3/4** / 2/4 | **4/4** / 3/4 | V00 and V02 only; NOT failed |
| 479 | **4/4** / 2/4 | **2/4** / 2/4 | **4/4** / 3/4 | V00 and V02 only; NOT failed |

The standalone policy let **all three** students attempt both NOT and AND,
unlike e6, when failed dialogue-gate prerequisites prevented either
operator from being taught. This is a change of *experiment objective and
promotion policy*, **not a controlled efficacy comparison** between e6 and
e7 (different seeds, lesson mix and presentation distribution).

All three obtained 4/4 on fresh standalone AND truth questions, and
4/4 on the separately frozen mixed-constant/variable structural AND probe
(`AND(TRUE,R)` and `AND(FALSE,R)` instances). These are eight tiny
item results per student, **not** confirmation of general compositional
competence. V00 retention remained 4/4 at later gates.

**The decisive retention failure occurred for seed 463.** At the end of
its NOT lesson, it answered all four held-out NOT questions correctly.
After subsequent AND instruction, the current AND gate was still 4/4,
but retained NOT was only **2/4**. Its two fresh variable-negation
questions remained correct; both literal-constant forms failed:
`NOT(TRUE)` was predicted TRUE (oracle FALSE), and `NOT(FALSE)` was
predicted FALSE (oracle TRUE). The predeclared retention rule stopped
further teaching despite the apparently successful AND gate.

Seeds 467 and 479 did not pass NOT (3/4 and 2/4 respectively), but
still learned the independent AND gate, with V00 retention intact.
Every V03/V04/V05 composition remained **unattempted** because the
same student never held both prerequisite competencies at the required
retention gate. Student-side correctness judgment `J00`, algebraic
laws, broader maths, Ithkuil, and native Kev pedagogy were **not reached**.

### Separate dialogue diagnostic and technical proof

The same two-turn valid teacher-dialogue prompt was placed before
held-out questions **only after training**. Under this out-of-training
distribution input, V00 scored 2/4 in all seeds; NOT scored 2/4;
AND scored 3/4. Such differences document presentation/context
sensitivity, but do **not** show teacher corrections impair learning:
there were no prior completed turns during e7 optimization. The separate
counterfactual-correction probe was likewise read-only and never a label.

Exactly **nine stage attempts × 320 = 2,880** optimizer updates were
executed across three students. There were **zero historical-context
training exposures**, zero Kev calls, no retry, and no additional seeds.
The source-locked runner saved all three student reports and all
**nine** stage checkpoints with model and optimizer state, actual
retention, diagnostic scores, and source/commit provenance. After the
run, the replay checked each checkpoint's hash, optimizer-step count,
prerequisite path, retained earlier gates, promotion, structural/context
diagnostics, aggregate completeness, and independent oracle labels:
`REPLAY_VERIFIED`. **127 repository tests passed before the run.**
Historical e1–e6 source and local student experiments remain untouched.

### Next educational frontier (proposal, not silently authorized training)

Focus on the **NOT literal-constant versus variable distinction** and
retention under subsequent AND rehearsal. Use a separate source-locked
curriculum design that balances both representations, tests predictable
counterexamples and prevents a student from shortcutting one form through
position/operator-frequency patterns. Keep the conversational interface
as an observable diagnostic while foundational truth-function stability
is tested. Only when these prerequisites hold should more laws, algebra
and later Ithkuil lessons enter the learning path. Future teacher
explanations may be invaluable when a *specific* learned primitive can
name the missed nuance; e7 does not yet evaluate that claim.

Neither this experiment nor the restored mergeability of its parent
branches constitutes merge approval or #82 curriculum completion.

## Adaptive trainee comptroller v0.5: preregistered e8, 2026-10-12

### Frozen research design and proof boundary

The user asked whether fixed 320-step stages prematurely stop an improving
student, and whether a teacher should identify missing concepts and repair
forgotten prerequisites. The e8 design was prepared, audited and source
committed **before any of its optimizer steps**. It continues **standalone
supervised question/answer training**, not corrective conversational history:
no completed prior teacher/student turns were included in the input.

- Pre-run source commit: `e81ce19725931403b621e14a0c60a963b833d9e5`.
- Pre-run source SHA-256: `f6d4753757793282d5a996c8fd77de6b9b49e1600e3f78fdfd86fc0f6b8de18c`.
- Source protocol: `docs/formal/ADAPTIVE_V05_PROTOCOL.md`.
- Draft stacked review: [PR #121](https://github.com/Entif-AI/Bilqis/pull/121),
  based on preserved e7 draft #120; neither is merge-authorized.
- Seeds: **463, 467, 479**, matched fresh starts across three
  preregistered arms: `fixed320`, `fixed1280`, `adaptive`.
- Atomic curricular scope: Boolean V00, unary NOT V01, binary AND V02.
  The adaptive arm trains in 64-update blocks, with minimum 320 and
  maximum 1280 optimizer updates per attempted stage, at most 256
  updates spent on prior-skill repairs, strict rollback on exhausted
  repair without retention, DEV-only intervention and a SEALED final
  exam. The two fixed arms use the same new curriculum at 320/1280
  respectively and do not use DEV to choose the next practice block.
- `NOT(TRUE)` and `NOT(FALSE)` are now **TRAIN** examples; their
  apparent mastery is *taught-domain coverage*, not unseen literal
  transfer. DEV `NOT(Q)` and SEALED `NOT(R)` are separately held out
  within v0.5. e8 must **not** be compared as a controlled efficacy
  rerun of e7: its educational split and outcomes differ by design.
- Exact e8 local run (ignored; not committed):
  `runs/formal-foundations-20261012-e8-adaptive-v05/`.
- Committed raw result projection:
  `docs/evidence/formal-foundations/E8_COMPARISON_V05.json`
  (SHA-256 `9f97d6955d77d4da26fdcac9612a3eda7d1b2535eaa64f0349d35861a960f697`);
  preregistration:
  `docs/evidence/formal-foundations/E8_PREREGISTRATION_V05.json`
  (SHA-256 `63060398fc2714526185f124eae5b6b2708931d8d4f7061096bf9adcdb7b6775`).

### Actual single-run outcomes: all three seeds and all three arms

The following cells report each competency's standalone SEALED **gate
score at that stage's end**, *not* proof that the competency survived later
teaching. **+** means admitted at that boundary; **-** means not
admitted. A later retention loss can invalidate simultaneous mastery
even if an earlier cell was admitted. `ROLL` means the attempted stage
was rolled back **before** its sealed exam was opened.

| Seed | Arm | Attempted optimizer updates | V00 gate | V01 NOT gate | V02 AND gate | Final outcome |
| --- | --- | ---: | --- | --- | --- | --- |
| 463 | fixed320 | 960 | 2/2 + | 1/2 - | 8/8 + | NOT failed transfer; Boolean/AND retained |
| 463 | fixed1280 | 2,560 | 2/2 + | 2/2 - | not attempted | NOT itself passed, but retained Boolean fell to 1/2; hard stop |
| 463 | adaptive | 960 | 2/2 + | 1/2 - | 8/8 + | Same final gates as fixed320; no extra budget used |
| 467 | fixed320 | 960 | 2/2 + | 2/2 + | 8/8 - | After AND, Boolean retention fell to 1/2 |
| 467 | fixed1280 | 3,840 | 2/2 + | 2/2 + | 8/8 - | After AND, Boolean retention fell to 1/2 |
| 467 | adaptive | 960 | 2/2 + | 2/2 + | 8/8 - | 192 prior-skill repair steps; Boolean still fell to 1/2 |
| 479 | fixed320 | 960 | 2/2 + | 2/2 + | 8/8 - | After AND, NOT retention fell to 0/2 |
| 479 | fixed1280 | 1,280 | 1/2 - | not attempted | not attempted | Longer V00 teaching failed its own sealed gate |
| 479 | adaptive | 1,024 | 2/2 + | ROLL - | 8/8 + | NOT rolled back after 384 attempted updates (256 repair); Boolean/AND retained |

**Totals:** nine fresh student arms, **13,504 real optimizer updates**
across 24 stage attempts, **211 saved 64-update block checkpoints**,
24 stage checkpoints, **zero completed-history training exposures,
zero native Kev calls**, no retries and no extra seeds. Exactly one
bounded e8 cohort was executed. The frozen source hash was unchanged
after completion. The complete locally retained checkpoints and
optimizer states passed independent postrun replay with status
`V05_CHECKPOINTS_VERIFIED`: blockwise DEV performance, training
sample ledgers, curriculum policy decisions, model hashes, AdamW state
digests, sealed scores, prior retention and skipped-stage accounting
were validated. Per-block training losses and correctness counts were
recorded but **historical per-update gradients were not independently
recomputed**. **142 repository tests passed before the full run.**

### Interpretation and unsolved educational frontier

**None of the nine students finished with stable simultaneous Boolean,
NOT and AND mastery.** More updates were not monotonically beneficial:
seed 463's long-training NOT itself passed 2/2 while Boolean fell to 1/2;
seed 479's 1,280-update Boolean student scored only 1/2, whereas its
320-update matched control reached 2/2. Seed 467's adaptive repair
spent 192 optimizer updates on prior-formative regressions, but its
final SEALED Boolean retention still fell to 1/2 after AND.

Seed 479's adaptive controller demonstrated a **mechanical recovery
safeguard**, not three-competency progress: NOT repair exhausted its
256-step allowance, the pre-NOT model/optimizer/RNG were restored,
and the independent AND branch subsequently passed 8/8 while the
Boolean 2/2 gate remained intact. The NOT student was not admitted
and the NOT final exam was not opened after the rollback.

The tiny DEV cases were often perfect even while final SEALED
transfer/retention failed; that is evidence of a **weak progress
signal**, not proof that adaptive learning is fundamentally inferior
or that increasing the model's capacity would solve the interference.
The V02 exam contains six FALSE and two TRUE cases, so the raw 8/8
score must not be treated as broad conjunction competence. The set
of possible short Boolean forms is extremely small, and these forms
were not historically blinded across prior experiments; controlled
generalization to structurally richer, genuinely fresh expressions
remains untested. Although `fixed1280` is a long-compute comparison,
the adaptive arm can stop earlier, so results need actual compute
accounting rather than an unqualified win/loss claim.

**Next bounded research choice, not automatically authorized here:**
grow the expression space, strengthen fresh and diverse DEV/SEALED
probes, and design more informative prior-skill retention monitoring
before promoting to NOT+AND compositions, laws or dialogue comprehension.
The user-facing teacher should keep using supervised gradient learning
for these primitives, rather than requiring a student to understand
the semantics of corrective conversation prematurely.

This evidence does not merge PR #121 or its ancestors, does not
promote any whole Stage A competency set and does **not** close #82.

## E9 v0.6: semantic-neighborhood lessons and matched rehearsal (2026-10-12)

**Disposition: completed, negative on the primary simultaneous-retention
endpoint; experimental teaching mechanism and checkpoint replay verified.**
This is a *new* preregistered study, not retroactive tuning of e8, not a
student architecture change and not a language/conversational-feedback study.

- Source-frozen commit: `b03dc466937a6632ae977610c42d4b954d34484c`.
- Frozen source SHA-256: `b3e2343aa0631905235c9237c889c3eb8b7814eed95a9fdbcf6ef5d83153a1eb`.
- Preregistered seeds: `503, 509, 521, 523, 541`; arms: `uniform8`,
  `semantic8`, `sham8`, `uniform16`, `semantic16`.
- Per admitted stage: 320 real AdamW updates, five 64-update blocks, 32
  supervised stand-alone samples per update. Same scratch model, optimizer,
  deterministic Boolean oracle, type-token input and no dialogue history.
- Executed **25 student arms, 69 competency-stage attempts, 22,080 real
  optimizer updates**. The original full run ended with exit code 0. The
  source was not altered or the run retried after observing results.
- Pre-experiment repo verification: **153 unit tests passed**. Independent
  checkpoint replay completed with exit code 0, validating all recorded
  per-block source/model/optimizer hashes, actual AdamW step accounting,
  sampler multiset and row order, DEV results, post-stage SEALED results,
  skipped stages and aggregate. Replay does **not** recompute gradients.
- Raw evidence: [E9 preregistration](E9_PREREGISTRATION_V06.json) and
  [E9 comparison](E9_COMPARISON_V06.json). Local ignored run path:
  `runs/formal-foundations-20261012-e9-semantic-v06/` (binary snapshots not
  committed). SHA-256 of raw JSON files: prereg
  `65cb9961bd79608eb9276789b134c0238c89e4934b0995c4b20a847cfca00ab4`;
  comparison `140bedd9f04e83eb0eb0ab9fdc45c9ff30ca93092764627fd4baa66f595d6890`.

### Complete arm outcomes

| Arm | Attempted stages (V00/V01/V02) | V00 promoted | NOT promoted | AND promoted | All three retained |
| --- | --- | ---: | ---: | ---: | ---: |
| Uniform, 8 prior | 5 / 5 / 4 | 5/5 | 0/5 | 3/4 | 0/5 |
| Semantic, 8 prior | 5 / 5 / 3 | 5/5 | 0/5 | 2/3 | 0/5 |
| Shuffled-category sham, 8 prior | 5 / 4 / 3 | 4/5 | 0/4 | 0/3 | 0/5 |
| Uniform, 16 prior | 5 / 5 / 5 | 5/5 | 1/5 | 3/5 | 0/5 |
| Semantic, 16 prior | 5 / 5 / 5 | 5/5 | 2/5 | 3/5 | 0/5 |

An admitted skill passes its exact current SEALED gate **and** retains
previous accepted skills; a 30/30 current AND score alone is not promotion
when prior Boolean or NOT retention drops. Some V02 attempts were skipped
after earlier retained-skill collapse or failed Boolean prerequisite. Thus
the different denominator in the table is a real ITT progression outcome,
not missing data or permission to compare conditional proportions naively.

### What changed, what did not, and what remains unknown

The semantic teacher grouped a fixed block's training examples by exact
eight-row Boolean function (or its complement), interleaved distinct
expression shapes, and aligned prior/current examples sharing verified
semantic relations and valuations. The fixed-row comparison preserved the
**exact same example-ID multiset in every 64-update block** for arms of the
same prior-rehearsal dose. A sham clustered by incorrectly assigned grouping
keys. Cohesion was measured through distinct-AST, cross-skill,
matched-valuation and predefined-relation coexposures, rather than inflated
by identical-question repetitions. This establishes that we actually tested
a semantics-guided instructional intervention.

**The hypothesis of improved simultaneous acquisition was not confirmed.**
Zero of 25 scratch students retained all three atomic competencies under the
specified gates. With 16 prior examples, semantic grouping passed the NOT
current gate in 2/5 seeds versus 1/5 for uniform grouping, but after teaching
AND neither arm sustained all three skills. With 8 prior examples neither
semantic nor uniform passed NOT in any seed. Some matched seeds saw higher
AND sealed scores under grouping; others worsened. The randomized sham was
often weaker, but five seeds and stage attrition cannot establish a causal
generalization benefit from its lower conditional counts.

Stronger AST variation made the V01 SEALED panel 6 items and V02 SEALED
30 items (compared with much smaller e8 panels). This increases within-study
diagnostic resolution but prevents a direct quantitative e8-vs-e9 treatment
comparison, and the grammar still uses only P/Q/R and Boolean primitives.
DEV/SEALED train-row IDs remain disjoint **within e9**; some formulas are
not historically novel relative to earlier public experiments. No teacher
or student was tested on natural-language instructions, learning semantic
set membership, predicate logic, full formal proof, native Ithkuil, Rosetta
semantics or corrective dialogue.

**Next research branch, not a post-hoc e9 repair:** retain the richer
semantically classified corpus and independently evaluate protection against
cross-stage gradient interference (for example preregistered regularization
or memory-gradient projection with equal-compute controls), as well as
per-stage conceptual weak-family targeting. Do not tune e9 after seeing its
sealed answers. E9 may be integrated as *versioned research infrastructure*
without declaring #82 scientifically satisfied; an explicit archival
integration decision and whole-stack verification are still necessary.
