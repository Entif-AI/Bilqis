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
permutations, and then run as a clearly separate third epoch. No third run was
silently executed and no later law was claimed as learned.
