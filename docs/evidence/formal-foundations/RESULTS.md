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
