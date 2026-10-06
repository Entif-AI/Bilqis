# Kev-4B New Ithkuil — frozen v0.1 capability result

Canonical order: **29 / 36 canonical cells**, **34 / 42 atomic decisions**.
Permuted order: **31 / 36 canonical cells**, **35 / 42 atomic decisions**.
Option order changed the choice in **3 / 42 decisions** across **3 / 36 cells**.

This is a capability map of this supplied grammar slice. Gold comes from the frozen human-authored #77 contract. Model scores are evidence, not truth authority. No invalid fixture cells were found.

[Every failure and unstable decision](FAILURES.md) · [Capability map](CAPABILITY_MAP.md) · [Source verification](SOURCE_VERIFICATION.md)

## What the result means

Kev meaningfully recognizes and distinguishes much of this small, supplied grammar slice: excluding sequential paths, it answers 29 / 33 cells in canonical order. This tests selection among four frozen candidates with the source packet available; it does not establish unconstrained sentence generation or general New Ithkuil fluency.

The clearest limitation is reconstruction: 5 / 9 intermediate decisions, 2 / 3 final answers, and 0 / 3 fully correct paths. Clarification is also limited: 1 / 3 in both orders. Final recognition can recover the target answer despite earlier wrong choices; those paths still fail joint correctness.

**Next recommendation:** adjust the interface/context representation in a separately frozen experiment. Present the sequence target and prior choices in a consistent textual state alongside the unchanged source packet, then test the observed reconstruction and clarification failures. The current run preserves the frozen prompts and results; it does not perform that follow-up.

## Metrics

| Slice | Canonical order | Permuted order |
|---|---|---|
| SIMPLE | 10 / 12 | 11 / 12 |
| MEDIUM | 9 / 12 | 10 / 12 |
| HARD | 10 / 12 | 10 / 12 |
| F01 — English → New Ithkuil | 2 / 3 | 3 / 3 |
| F02 — New Ithkuil → English | 3 / 3 | 3 / 3 |
| F03 — Root / stem recovery | 2 / 3 | 2 / 3 |
| F04 — Semantic roles | 3 / 3 | 3 / 3 |
| F05 — Grammatical features | 3 / 3 | 3 / 3 |
| F06 — Morpheme / form selection | 3 / 3 | 3 / 3 |
| F07 — Near-miss diagnosis | 3 / 3 | 3 / 3 |
| F08 — Minimal-pair discrimination | 3 / 3 | 3 / 3 |
| F09 — Semantic equivalence | 3 / 3 | 3 / 3 |
| F10 — Sequential reconstruction | 0 / 3 | 1 / 3 |
| F11 — Complete-expression validation | 3 / 3 | 3 / 3 |
| F12 — Insufficient / clarify | 1 / 3 | 1 / 3 |
| Chapter 2 — root/stem/Specification | 3 / 4 | 3 / 4 |
| Chapter 3 — Configuration | 10 / 14 | 12 / 14 |
| Chapter 3 — Affiliation | 9 / 12 | 11 / 12 |
| Chapter 4 — semantic roles | 12 / 14 | 12 / 14 |
| Chapter 4 — case morphology | 9 / 11 | 9 / 11 |
| Single decision, one annotated dimension | 14 / 15 | 14 / 15 |
| Single decision, multiple annotated dimensions | 15 / 18 | 16 / 18 |
| Sequential paths (joint) | 0 / 3 | 1 / 3 |
| Affiliation (overlapping canonical membership) | 9 / 12 | 11 / 12 |
| Configuration (overlapping canonical membership) | 10 / 14 | 12 / 14 |
| Specification (overlapping canonical membership) | 2 / 2 | 2 / 2 |
| case morphology (overlapping canonical membership) | 9 / 11 | 9 / 11 |
| holistic composition (overlapping canonical membership) | 4 / 6 | 5 / 6 |
| reconstruction (overlapping canonical membership) | 0 / 3 | 1 / 3 |
| root/stem (overlapping canonical membership) | 2 / 3 | 2 / 3 |
| semantic role (overlapping canonical membership) | 12 / 14 | 12 / 14 |
| uncertainty/clarification (overlapping canonical membership) | 1 / 3 | 1 / 3 |
| Sequential atomic | 5 / 9 | 5 / 9 |
| Sequential final | 2 / 3 | 1 / 3 |
| Sequential joint | 0 / 3 | 1 / 3 |
| Whole expression — English_to_New_Ithkuil | 1 / 1 | 1 / 1 |
| Whole expression — New_Ithkuil_to_English | 1 / 1 | 1 / 1 |
| Whole expression — validation | 3 / 3 | 3 / 3 |
| source_exact | 15 / 16 | 15 / 16 |
| source_derived | 9 / 15 | 11 / 15 |
| controlled_mutation | 5 / 5 | 5 / 5 |

Chapter slices require both the named source chapter and the annotated dimension. Chapter-2 root/stem/Specification therefore covers F01-MEDIUM, F02-MEDIUM, F03-SIMPLE and F03-MEDIUM; F03-HARD is a Chapter-4 worked predicate. The task-structure groups partition all 36 cells. Source-exact/derived/mutation categories describe provenance, not task complexity. Atomic decision totals count model calls; a single call can test multiple dimensions.

## Choices changed by permutation

| Decision | Gold | Canonical → permuted | Correctness | Gold ΔP | Total variation |
|---|---|---|---|---:|---:|
| [F01-SIMPLE](FAILURES.md#f01-simple) | A | C → A | incorrect → correct | +0.4909 | 0.4909 |
| [F10-MEDIUM.S2](FAILURES.md#f10-medium) | C | A → C | incorrect → correct | +0.0318 | 0.0465 |
| [F10-HARD.S4](FAILURES.md#f10-hard) | A | A → B | correct → incorrect | -0.1401 | 0.1977 |

## Every canonical cell

A/B/C/D are the frozen source candidate labels, not display positions. Sequential parent correctness is joint correctness; parent Top P and Margin are the minima across its steps, and latency is their sum. Atomic step rows sit immediately beneath each parent. Permutation stability means the same candidate identity, irrespective of display position.

| Cell | Family | Difficulty | Gold | Kev choice | Correct? | Top P | Margin | Permutation stable? | Latency |
|---|---|---|---|---|---|---:|---:|---|---:|
| [F01-SIMPLE](FAILURES.md#f01-simple) | F01 | SIMPLE | A | C | ✗ | 0.3801 | 0.0114 | NO | 340.6 ms |
| F01-MEDIUM | F01 | MEDIUM | A | A | ✓ | 0.3080 | 0.0324 | yes | 182.0 ms |
| F01-HARD | F01 | HARD | A | A | ✓ | 0.8009 | 0.7106 | yes | 188.5 ms |
| F02-SIMPLE | F02 | SIMPLE | A | A | ✓ | 0.8365 | 0.7391 | yes | 161.8 ms |
| F02-MEDIUM | F02 | MEDIUM | A | A | ✓ | 0.9479 | 0.9269 | yes | 191.4 ms |
| F02-HARD | F02 | HARD | B | B | ✓ | 0.9396 | 0.8975 | yes | 156.3 ms |
| F03-SIMPLE | F03 | SIMPLE | A | A | ✓ | 0.9721 | 0.9602 | yes | 142.7 ms |
| [F03-MEDIUM](FAILURES.md#f03-medium) | F03 | MEDIUM | B | A | ✗ | 0.6917 | 0.5288 | yes | 148.0 ms |
| F03-HARD | F03 | HARD | A | A | ✓ | 0.9456 | 0.9121 | yes | 158.4 ms |
| F04-SIMPLE | F04 | SIMPLE | C | C | ✓ | 0.9939 | 0.9912 | yes | 134.4 ms |
| F04-MEDIUM | F04 | MEDIUM | A | A | ✓ | 0.9688 | 0.9554 | yes | 150.3 ms |
| F04-HARD | F04 | HARD | A | A | ✓ | 0.9294 | 0.8719 | yes | 152.7 ms |
| F05-SIMPLE | F05 | SIMPLE | B | B | ✓ | 0.7748 | 0.6609 | yes | 138.0 ms |
| F05-MEDIUM | F05 | MEDIUM | A | A | ✓ | 0.8653 | 0.7743 | yes | 146.6 ms |
| F05-HARD | F05 | HARD | A | A | ✓ | 0.9270 | 0.8986 | yes | 143.7 ms |
| F06-SIMPLE | F06 | SIMPLE | C | C | ✓ | 0.9797 | 0.9677 | yes | 139.1 ms |
| F06-MEDIUM | F06 | MEDIUM | B | B | ✓ | 0.5824 | 0.3133 | yes | 137.7 ms |
| F06-HARD | F06 | HARD | A | A | ✓ | 0.6457 | 0.4469 | yes | 149.9 ms |
| F07-SIMPLE | F07 | SIMPLE | B | B | ✓ | 0.5805 | 0.2762 | yes | 155.7 ms |
| F07-MEDIUM | F07 | MEDIUM | A | A | ✓ | 0.8662 | 0.7574 | yes | 194.7 ms |
| F07-HARD | F07 | HARD | A | A | ✓ | 0.5600 | 0.3483 | yes | 203.5 ms |
| F08-SIMPLE | F08 | SIMPLE | A | A | ✓ | 0.9579 | 0.9278 | yes | 167.1 ms |
| F08-MEDIUM | F08 | MEDIUM | A | A | ✓ | 0.5809 | 0.2567 | yes | 154.4 ms |
| F08-HARD | F08 | HARD | A | A | ✓ | 0.7415 | 0.6008 | yes | 189.5 ms |
| F09-SIMPLE | F09 | SIMPLE | A | A | ✓ | 0.9651 | 0.9490 | yes | 181.9 ms |
| F09-MEDIUM | F09 | MEDIUM | A | A | ✓ | 0.7946 | 0.6998 | yes | 151.6 ms |
| F09-HARD | F09 | HARD | A | A | ✓ | 0.7527 | 0.6443 | yes | 207.5 ms |
| [F10-SIMPLE](FAILURES.md#f10-simple) | F10 | SIMPLE | B → C | A → C | ✗ | 0.2736 | 0.0132 | yes | 23613.1 ms |
| ↳ F10-SIMPLE.S1 | F10 | step 1 | B | A | ✗ | 0.2736 | 0.0276 | yes | 11793.2 ms |
| ↳ F10-SIMPLE.S2 | F10 | step 2 | C | C | ✓ | 0.3106 | 0.0132 | yes | 11819.9 ms |
| [F10-MEDIUM](FAILURES.md#f10-medium) | F10 | MEDIUM | C → C → C | C → A → C | ✗ | 0.3164 | 0.0455 | NO | 35458.2 ms |
| ↳ F10-MEDIUM.S1 | F10 | step 1 | C | C | ✓ | 0.3711 | 0.0826 | yes | 11785.3 ms |
| ↳ F10-MEDIUM.S2 | F10 | step 2 | C | A | ✗ | 0.3164 | 0.0455 | NO | 11794.0 ms |
| ↳ F10-MEDIUM.S3 | F10 | step 3 | C | C | ✓ | 0.4457 | 0.1997 | yes | 11878.9 ms |
| [F10-HARD](FAILURES.md#f10-hard) | F10 | HARD | A → A → A → A | B → C → A → A | ✗ | 0.4434 | 0.1607 | NO | 47350.1 ms |
| ↳ F10-HARD.S1 | F10 | step 1 | A | B | ✗ | 0.4581 | 0.2240 | yes | 11797.9 ms |
| ↳ F10-HARD.S2 | F10 | step 2 | A | C | ✗ | 0.4434 | 0.1607 | yes | 11815.3 ms |
| ↳ F10-HARD.S3 | F10 | step 3 | A | A | ✓ | 0.6226 | 0.4385 | yes | 11845.3 ms |
| ↳ F10-HARD.S4 | F10 | step 4 | A | A | ✓ | 0.5074 | 0.2267 | NO | 11891.6 ms |
| F11-SIMPLE | F11 | SIMPLE | A | A | ✓ | 0.7297 | 0.5598 | yes | 11836.9 ms |
| F11-MEDIUM | F11 | MEDIUM | A | A | ✓ | 0.6136 | 0.3229 | yes | 195.1 ms |
| F11-HARD | F11 | HARD | A | A | ✓ | 0.5055 | 0.3208 | yes | 163.8 ms |
| F12-SIMPLE | F12 | SIMPLE | D | D | ✓ | 0.6696 | 0.5457 | yes | 146.0 ms |
| [F12-MEDIUM](FAILURES.md#f12-medium) | F12 | MEDIUM | D | A | ✗ | 0.3423 | 0.0786 | yes | 138.2 ms |
| [F12-HARD](FAILURES.md#f12-hard) | F12 | HARD | D | B | ✗ | 0.6945 | 0.5045 | yes | 150.7 ms |

## Execution identity and interpretation limits

Runtime details: [runtime-identity.json](runtime-identity.json). Full scored rows: [A/rows.jsonl](A/rows.jsonl) and [B/rows.jsonl](B/rows.jsonl). Aggregate replay: [summary.json](summary.json).

The supplied context packet SHA-256 is `c178cd133d051cddcca0eae8a69111b4696418425a6a99c27723786a6af898be`. It remains byte-identical and outside the public repository; [source-manifest.json](source-manifest.json) identifies its official snapshots.

F10 canonical steps consume previous choices. For the paired permutation, each atomic decision replays the exact canonical input state, including that preceding path. Thus only candidate order changes. Permuted final/joint metrics score the permuted outputs against the same frozen gold; they do not represent a fresh adaptive sequence with changed preceding inputs. A correct final choice never retroactively repairs a wrong intermediate step.

The API exposes scores rounded to four decimal places; raw provider vectors are retained without claiming hidden higher precision. The examples recur across families, so 36 cells are not 36 independent linguistic anchors. Dimension totals overlap and diagnose performance on the associated tasks; they do not isolate a causal mechanism.

F10-HARD final scoring follows the fixed target gold. Its prompt also asks for consistency with the selected path. After canonical errors produce IND + LOC + INS, permuted choice B agrees with that preceding wrong path but disagrees with the fixed target A. This is a path/target scoring tension in the frozen contract, not a contradiction in the official sentence examples; do not interpret this final switch as an independent loss of grammatical understanding. Both paths fail joint target correctness.

## Retained epochs and runtime

The initial canonical run is preserved byte-for-byte in [initial-canonical/A](initial-canonical/A/RECEIPT.json). Before any initial permutation inference, an HTTP test found that sorted JSON criteria would erase the requested option order. [epoch-declaration.json](epoch-declaration.json) declares the order-preserving serializer correction. These reported A/B runs then executed 84 calls; the retained initial run adds 42, for 126 total. No linguistic prompts, options, gold, source bytes, runtime or calibration were tuned.

Model `jaredpalmer/kev-4b` at revision `6cfce5c2fa4b4bd64026336ab649c5ca78857d52`; Kev source `6b719c3c3f367295f6ef336f4f751cf5ff970abc`. Backend `mlx`, dtype `bfloat16`, temperature `2.406050072164233`. Endpoint remains loopback-only: `http://127.0.0.1:8008/v1/systemone`.

Canonical median/mean POST latency: 165.4 / 2943.3 ms; decision throughput 0.340/s. Permuted: 163.2 / 2941.3 ms; 0.340/s. Complete epoch wall throughput is in summary.json. Latency excludes the adapter's identity GET calls.

Canonical cache telemetry records 32/42 warm decisions. Ten requests in each order take roughly 11.8 seconds; most take roughly 0.15–0.2 seconds. F10 changes the structured state at each step. This association explains the reported latency split observationally; it does not prove a model-internal cause.
Permuted cache telemetry records 32/42 warm decisions. Ten requests in each order take roughly 11.8 seconds; most take roughly 0.15–0.2 seconds. F10 changes the structured state at each step. This association explains the reported latency split observationally; it does not prove a model-internal cause.