# Bilqis developmental micro-universes

One scratch learner continued through U0–U4 with one AdamW optimizer. This is an exploratory capability-building run.

| Universe | At introduction: familiar / varied / composite | After U4: familiar / varied / composite |
| --- | --- | --- |
| U0: Boolean refresh | 90/128 / 82/128 / 75/128 | 92/128 / 71/128 / 66/128 |
| U1: entities and roles | 108/128 / 83/128 / 64/128 | 83/128 / 71/128 / 62/128 |
| U2: quantification and composition | 114/128 / 72/128 / 65/128 | 88/128 / 65/128 / 64/128 |
| U3: inference and proof | 111/128 / 75/128 / 66/128 | 68/128 / 56/128 / 57/128 |
| U4: evidence and interpretations | 111/128 / 78/128 / 59/128 | 111/128 / 78/128 / 59/128 |

8,400 optimizer updates; 268,800 example exposures; 6,718,889 nonpadding tokens.
Training process: 150.4s wall, 149.0s CPU; peak RSS 381.3 MiB. Semantic preparation: 3.8s, accounted separately.

The semantic graph freezes 68 identities with type signatures, roles, inverses, binding, composition, proof rules and evidence distinctions. SHA-256 keyed feature coordinates are row-local; appending a node leaves old rows and IDs exact. All neural weights are scratch initialized. Helper calls and external helper spend were zero.

Familiar examples overlap the training pools. Varied and composite inputs are excluded from every training pool; varied worlds have 4–5 entities while training uses 2–4. Composite readouts add new nesting. These are authored development readouts, not a sealed benchmark or evidence of general reasoning.

Proof means finite Horn-rule closure and candidate countermodel satisfaction. Evidence reports remain separate from closed-world facts: no report is UNKNOWN; explicit refutation is FALSE; support and refutation is CONFLICT; divergent live interpretation outcomes are AMBIGUOUS. Boolean operations retain their original identities; evidence operations use separate identities.

## Real neural demonstrations

All answers below come from the trained transformer. The complete inputs, logits, per-stage scores, successes and mistakes are retained in [gallery.json](run-01/gallery.json) and the checkpoint readouts.

| Universe | Input / perturbation | Gold | At introduction | After U4 |
| --- | --- | --- | --- | --- |
| U1 | `{PARENT(A,B); PARENT(B,C)} => PARENT(A,B)` | TRUE | TRUE | FALSE |
| U1 | `{PARENT(A,B); PARENT(B,C)} => CHILD(B,A)` | TRUE | FALSE | FALSE |
| U1 | `{PARENT(A,B); PARENT(B,C)} => PARENT(A,C)` | FALSE | TRUE | FALSE |
| U2 | `{PARENT(A,B); PARENT(B,C)} => EXISTS[AND(PARENT(A,v0),PARENT(v0,C))]` | TRUE | TRUE | FALSE |
| U2 | `{PARENT(A,B); PARENT(C,B)} => EXISTS[AND(PARENT(A,v0),PARENT(v0,C))]` | FALSE | TRUE | FALSE |
| U3 | `{PARENT(A,B); PARENT(B,C)} + GP rule => ENTAILS(GRANDPARENT(A,C))` | TRUE | TRUE | TRUE |
| U3 | `{PARENT(A,B); PARENT(B,C)} => ENTAILS(GRANDPARENT(A,C))` | FALSE | FALSE | FALSE |
| U4 | `{PARENT(A,B); PARENT(B,C)}; reports=[]; live=[0] => OBSERVE(J0)` | UNKNOWN | FALSE | FALSE |
| U4 | `{PARENT(A,B); PARENT(B,C)}; reports=[['S0', 'J0', 'refute', 0]]; live=[0] => OBSERVE(J0)` | FALSE | TRUE | TRUE |

## Retained mistakes

Examples below are deterministic first mistakes from the final varied readouts. The gallery also preserves composite failures and successful answers.

- U0: `IFF(IMPLIES(FALSE,TRUE),IFF(FALSE,TRUE))` — neural TRUE; oracle FALSE.
- U1: `{LINK(A,C); PARENT(A,C); PARENT(B,C); PARENT(C,E)} => PARENT(A,C)` — neural FALSE; oracle TRUE.
- U2: `{PARENT(B,E); PARENT(C,E)} => FORALL[EXISTS[EQ(v1,v0)]]` — neural FALSE; oracle TRUE.
- U3: `{LINK(A,D); PARENT(A,D); PARENT(E,D)} + GP rule => COUNTERMODEL(PARENT(A,D),PARENT(D,E),GRANDPARENT(A,E))` — neural TRUE; oracle FALSE.
- U4: `{LINK(B,C); PARENT(B,C); PARENT(C,E); PARENT(D,A)} + GP rule; reports=[['S1', 'J0', 'support', 0], ['S1', 'J1', 'refute', 0]]; live=[0] => OBSERVE(J0)` — neural CONFLICT; oracle TRUE.

## Reproduction and evidence

Fresh-process replay: 7,680 predictions; maximum absolute logit/probability error 0.0; optimizer/checkpoint lineage and all exposures verified.

[Freeze](run-01/freeze.json), [initializer](run-01/initializer.json), [stage and exposure result](run-01/result.json), [replay](run-01/replay.json), [pre-training encoded examples](run-01/samples.json), [handoff](../../micro-universes/HANDOFF.md).

No random/permuted controls, ablations, helper qualification, SYS-01 experiment, pretrained transfer or merge was performed. #107 and all earlier evidence are preserved.

## Acquisition, retention and evidence distinctions

The at-introduction readouts show acquisition on familiar lessons. U1 familiar accuracy fell from 108/128 to 83/128, U2 from 114/128 to 88/128, and U3 from 111/128 to 68/128 by the end of evidence training. Final U1 and U3 varied scores are below their own majority-label accuracy, and all final composite scores are close to or below that simple class-frequency reference. This run establishes executable cumulative training and partial task acquisition, not robust compositional transfer.

The final learner retains 26/26 Boolean primitive lessons. The complete primitive logits are in [primitive-retention.json](run-01/primitive-retention.json).

The following are the first pre-frozen varied-world examples for each oracle state, selected independently of whether the neural answer is correct. Full worlds and logits are in [state-gallery.json](run-01/state-gallery.json).

| Oracle state | Reports and live interpretations | Neural answer |
| --- | --- | --- |
| FALSE | `[['S0', 'J0', 'refute', 0]]; live=[0]` | FALSE |
| TRUE | `[['S1', 'J0', 'support', 0], ['S1', 'J1', 'refute', 0]]; live=[0]` | CONFLICT |
| UNKNOWN | `[['S1', 'J1', 'refute', 0]]; live=[0]` | UNKNOWN |
| CONFLICT | `[['S0', 'J0', 'support', 0], ['S2', 'J0', 'refute', 0]]; live=[0]` | CONFLICT |
| AMBIGUOUS | `[['S2', 'J0', 'refute', 1], ['S2', 'J0', 'support', 0]]; live=[0, 1]` | AMBIGUOUS |
