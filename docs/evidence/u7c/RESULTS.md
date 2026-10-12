# U7C balanced English-only continuation: measured results

Stacked on Bilqis draft PR #112. Successor run-02 started from the accepted U6 student at AdamW step 13,400. The failed U7B step-13,656 checkpoint was excluded. Historical U7B files are unchanged. U7C run-01 was a superseded pre-gradient freeze; its frozen source digest intentionally differs from this revised runner and it received no training.

## Pregradient integrity and actual execution

The independent-oracle frozen grammar has 432 balanced cross-stage TRAIN rows, 288 unseen final cross-stage rows, and 216 training / 144 final same-world causal witness pairs. Operator-only label accuracy was exactly 50% in both sets. Operator plus old-arm oracle truth and operator plus new-arm oracle truth each predicted 75%: these are oracle-informed audit upper features, not an executable learned model. No DEV, prior heldout or final identities entered new training pools. All 32-row optimizer batches used the exact 12 current, 4 fresh prior, 8 composition, 8 DEV weak split.

Kev received English-only source-grounded prose with real contrasting lesson worlds and optional REVIEW. No canonical typed JSON/AST, numeric embeddings or oracle gold labels entered Kev. English semantic glosses of the known source definitions were included by design. EG2 made zero calls. Both actual Kev decisions were REVIEW, leaving the broad admitted grammar fallback.

Training stopped at 32 of 256 allowed gradient updates at AdamW step 13432, after a predeclared DEV retention gate failure. No thresholds were relaxed.

| Critical DEV readout | U6 start | After U7C | Minimum |
| --- | ---: | ---: | ---: |
| primitives | 26/26 | 26/26 | 24/26 |
| u4 composite | 50/128 | 39/128 | 42/128 |
| u4 varied | 81/128 | 85/128 | 73/128 |
| u0 composite | 74/128 | 69/128 | 66/128 |
| lineage | 4/10 | 3/10 | 4/10 |

At 16 updates, all gates passed: primitives 26/26, U4 composite 46/128, U4 varied 89/128, U0 composite 71/128, lineage 5/10. At 32, U4 composite and lineage gates failed; the optimizer stopped.

## Full before/after readouts

| Stage | Fresh varied | Fresh composite | Historical familiar | Historical varied | Historical composite |
| --- | --- | --- | --- | --- | --- |
| U0 | 20/32 to 22/32 | 15/32 to 17/32 | 76/128 to 76/128 | 70/128 to 74/128 | 74/128 to 69/128 |
| U1 | 22/32 to 25/32 | 13/32 to 17/32 | 89/128 to 90/128 | 81/128 to 79/128 | 64/128 to 69/128 |
| U2 | 21/32 to 20/32 | 13/32 to 11/32 | 97/128 to 98/128 | 70/128 to 70/128 | 68/128 to 68/128 |
| U3 | 14/32 to 12/32 | 13/32 to 16/32 | 81/128 to 84/128 | 71/128 to 71/128 | 67/128 to 72/128 |
| U4 | 18/32 to 17/32 | 19/32 to 14/32 | 97/128 to 102/128 | 81/128 to 85/128 | 50/128 to 39/128 |
| U5 | 16/32 to 14/32 | 14/32 to 17/32 | 72/128 to 70/128 | 174/320 to 160/320 | 157/320 to 152/320 |
| U6 | 22/32 to 22/32 | 6/32 to 7/32 | 98/128 to 92/128 | 213/320 to 210/320 | 168/320 to 173/320 |

Fresh 448 total: 226/448 to 231/448. Balanced cross-final: 161/288 to 162/288. Boolean primitives: 26/26 to 26/26. Lineage: 4/10 to 3/10.

## Independent matched causal-sibling scoring

An additive posthoc analysis of a PRE-FROZEN final cohort scored 144 original/old-flip/new-flip triples and 288 previously unseen siblings. All-three-correct: 9/144 to 10/144. Original anchors correct: 46/144 to 63/144. Single-arm siblings correct: 187/288 to 176/288. These findings remain weak and do not support compositional mastery. The analysis definition was posthoc, although the inputs were frozen before gradients.

## Reproducibility, disclosure and disposition

Fresh-process replay reproduced 32 optimizer updates, all exact batches, DEV decisions, model state a8a6e2edfcae9871c163bec77b5969c5eac91e60e869a573e965dc3f8e7ffbd8, AdamW hash ee8072198e1983f8cb6409f4d8017e60a928cefe954bccd439d6c3e8355926de, and the archived predictions with zero native helper calls. The direct runner initially failed on archived JSON object-key ordering. A separate adapter restored the actual offered choice order using its saved SHA-256-validated serialized HTTP request. This repaired archive interpretation without changing frozen trainer code or training history.

The U7C integrity shortcut is repaired, but critical retention and paired causal tests remain negative. No stage promotion, neural composition mastery, Kev teaching benefit, scientific confirmatory claim, merge or release is justified. Preserve both the U7B negative and U7C negative records.
