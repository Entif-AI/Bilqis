# Kev-4B capability map

Observed canonical performance: 29 / 36 cells; 34 / 42 decisions. Permuted performance: 31 / 36 cells; 35 / 42 decisions.

## Strongest capabilities

Families perfect in both orders: New Ithkuil → English, Semantic roles, Grammatical features, Morpheme / form selection, Near-miss diagnosis, Minimal-pair discrimination, Semantic equivalence, Complete-expression validation. These are observed successes on three frozen cells per family, with recurring anchors.

## Weakest capabilities

Sequential reconstruction: 0 / 3 joint paths, despite 2 / 3 final answers. Insufficient-evidence recognition: 1 / 3 in both orders. Root/stem recovery: 2 / 3 in both orders. Follow each specific confusion below rather than treating the aggregate as a capability guarantee.

## Capability structure

| Capability family | Canonical | Permuted |
|---|---|---|
| English → New Ithkuil | 2 / 3 | 3 / 3 |
| New Ithkuil → English | 3 / 3 | 3 / 3 |
| Root / stem recovery | 2 / 3 | 2 / 3 |
| Semantic roles | 3 / 3 | 3 / 3 |
| Grammatical features | 3 / 3 | 3 / 3 |
| Morpheme / form selection | 3 / 3 | 3 / 3 |
| Near-miss diagnosis | 3 / 3 | 3 / 3 |
| Minimal-pair discrimination | 3 / 3 | 3 / 3 |
| Semantic equivalence | 3 / 3 | 3 / 3 |
| Sequential reconstruction | 0 / 3 | 1 / 3 |
| Complete-expression validation | 3 / 3 | 3 / 3 |
| Insufficient / clarify | 1 / 3 | 1 / 3 |

## Semantic dimensions

| Dimension | Canonical | Permuted |
|---|---|---|
| Affiliation | 9 / 12 | 11 / 12 |
| Configuration | 10 / 14 | 12 / 14 |
| Specification | 2 / 2 | 2 / 2 |
| case morphology | 9 / 11 | 9 / 11 |
| holistic composition | 4 / 6 | 5 / 6 |
| reconstruction | 0 / 3 | 1 / 3 |
| root/stem | 2 / 3 | 2 / 3 |
| semantic role | 12 / 14 | 12 / 14 |
| uncertainty/clarification | 1 / 3 | 1 / 3 |

## Source chapters and task structure

| Slice | Canonical | Permuted |
|---|---|---|
| Chapter 2 — root/stem/Specification | 3 / 4 | 3 / 4 |
| Chapter 3 — Configuration | 10 / 14 | 12 / 14 |
| Chapter 3 — Affiliation | 9 / 12 | 11 / 12 |
| Chapter 4 — semantic roles | 12 / 14 | 12 / 14 |
| Chapter 4 — case morphology | 9 / 11 | 9 / 11 |
| Single decision, one annotated dimension | 14 / 15 | 14 / 15 |
| Single decision, multiple annotated dimensions | 15 / 18 | 16 / 18 |
| Sequential paths (joint) | 0 / 3 | 1 / 3 |

## Observed confusions

These are gold-to-selected candidate confusions. A multi-dimension wrong answer does not identify which internal feature caused the error.

- F01-SIMPLE: COA(-r-) + DSS(-c-) → COA(-r-) + DDS(-ţs-).
- F03-MEDIUM: -DN-, Stem 2: designation/reference → -DN-, Stem 1: name.
- F10-SIMPLE.S1: DSS → DPX.
- F10-MEDIUM.S2: COA → CSL.
- F10-HARD.S1: ERG → IND.
- F10-HARD.S2: ABS → LOC.
- F12-MEDIUM: CLARIFY / INSUFFICIENT → MSS.
- F12-HARD: CLARIFY / INSUFFICIENT → EFF.

## Order stability

39 / 42 atomic choices and 33 / 36 canonical cells retain exact choice identity. Correctness changes in 3 decisions. Mean total variation distance is 0.0828.
Order-sensitive cells: F01-SIMPLE, F10-HARD, F10-MEDIUM.

Sequential final accuracy and joint accuracy remain separate: canonical 2 / 3 final, 0 / 3 joint. Wrong-path/right-final cells: F10-MEDIUM, F10-HARD.

Forward/reverse family totals include segmented recognition and their one HARD whole-sentence cell. Whole-sentence recognition specifically scores 1 / 1 English → New Ithkuil and 1 / 1 New Ithkuil → English.

The F10-HARD permuted final answer matches the preceding wrong path while missing the fixed target. See [RESULTS.md](RESULTS.md#execution-identity-and-interpretation-limits) before treating that switch as a standalone case-morphology failure. Full confusion counts, including the correct diagonal, are in [capability.json](capability.json).

## Next recommendation

Adjust the interface/context representation in a separately frozen experiment. Recognition is stronger here than reconstruction and clarification. A consistent textual rendering of target and prior path is the most useful next variable to test; the current evidence does not isolate the cause or establish that a larger model or fine-tune is necessary.

For SIMPLE/MEDIUM/HARD, source-exact versus derived/compositional tasks, complete-expression validation, latency and runtime, see [RESULTS.md](RESULTS.md). Every confusion can be inspected with all probabilities in [FAILURES.md](FAILURES.md). These observations apply to this frozen source packet, calibration and rendering.
