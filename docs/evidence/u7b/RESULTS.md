# U7B: teacher-interface reversal, inert curriculum selection, shortcut-sensitive learning

Completed 2026-10-11 as one exploratory continuation from the exact U6 model/AdamW at step 13,400. The learner reached **13,656** after 256 updates. The historical U7 cohort remains frozen and untrained. This run does not establish bilingual-teacher benefit or acquired compositional semantics.

## Teacher results

The same eight source-grounded cells and two option orders were tested under three renderings before pupil training. Expectations and candidate identities were frozen; teacher questions did not name the intended construction. Raw correctness includes low-margin decisions and is separate from lesson admission.

| Context | Correct / 16 | Correct required reviews / 2 | Sequence atomic / 4 | Sequence joint / 2 | Order changes / 8 | Wall seconds |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| english | 13 | 2 | 4 | 2 | 2 | 3.76 |
| canonical | 9 | 0 | 2 | 0 | 2 | 5.92 |
| combined | 11 | 0 | 1 | 0 | 1 | 6.49 |

**English-only was selected by the frozen fallback rule.** Combined scored below English and did not earn use. This is an authored eight-cell development battery with generated alternatives; it is not an independent general-language or teacher-utility qualification.

Kev then made eight pedagogical decisions at updates 0, 64, 128 and 192, two recent-stage panels each time. Each panel offered three competing valid grammar productions and REVIEW. **All eight chose REVIEW; zero proposals narrowed a lesson reservoir.** The frozen broad grammar/oracle fallback supplied every cross-stage lesson. There is no pedagogical gold, and semantic-discrimination accuracy cannot be substituted for teaching utility.

## Acquisition and conservation

Fresh final varied/composite worlds were excluded from teaching and opened after training. The aggregate changed 228/448 → 247/448, with large family-specific gains and regressions. These are exact-world holdouts sharing the source generators with TRAIN; they are not an independent scientific seal.

| Stage | Fresh varied before → after / 32 | Fresh composite before → after / 32 | Historical familiar before → after / 128 | Historical varied before → after | Historical composite before → after |
| --- | ---: | ---: | ---: | ---: | ---: |
| U0 | 17 → 19 | 16 → 15 | 76 → 70 | 70 → 72 / 128 | 74 → 67 / 128 |
| U1 | 19 → 18 | 13 → 22 | 89 → 85 | 81 → 76 / 128 | 64 → 74 / 128 |
| U2 | 16 → 19 | 15 → 10 | 97 → 101 | 70 → 73 / 128 | 68 → 68 / 128 |
| U3 | 15 → 17 | 12 → 14 | 81 → 73 | 71 → 65 / 128 | 67 → 74 / 128 |
| U4 | 14 → 13 | 13 → 2 | 97 → 90 | 81 → 78 / 128 | 50 → 22 / 128 |
| U5 | 25 → 22 | 16 → 25 | 72 → 60 | 174 → 160 / 320 | 157 → 156 / 320 |
| U6 | 22 → 25 | 15 → 26 | 98 → 83 | 213 → 216 / 320 | 168 → 152 / 320 |

**Critical retention failures:** Boolean primitives 26/26 → 20/26; U4 historical composites 50/128 → 22/128; fresh U4 composites 13/32 → 2/32. Fresh U4 composite UNKNOWN, CONFLICT and AMBIGUOUS cases all failed after continuation. The fixed provenance/supersession diagnostic remained 4/10, with the same wrong ancestry/replacement and conflict answers. No stage promotion or conservation success is claimed. The cross-stage subset fails the no-answer-hint integrity boundary: its oracle-informed gate is an unintended answer cue. Focused unit checks do not override this failed research acceptance condition.

## Counterfactual and shortcut audit

Fresh grammar cross-world accuracy rose **28/120 → 110/120**. However, the inherited generator chooses AND when both operands are TRUE, and OR when both are FALSE. A root-operator-only baseline, reading no worlds or operands, scores **1,024/1,024 TRAIN and 120/120 final**. Formal two-arm causal witnesses are real, but this sampling rule exposes a perfect answer shortcut.

The before-training-frozen, untrained single-arm counterfactual siblings score **1,496/2,048 → 266/2,048** for the neural learner, while the gate-only baseline scores 0/2,048. This posthoc diagnostic uses sibling worlds of TRAIN examples and is not a new independent final endpoint. It rejects a mastery interpretation of the headline cross-stage gain; it does not prove a specific internal neural mechanism.

No data or policy was repaired after unblinding. A future version should counterbalance gate × operand truth × gold, include sibling cases in a disjoint predeclared final plane and require a gate-only/operand-blind shortcut audit before training. Rehearsal allocation alone did not preserve critical distinctions in this run.

## Semantic authorship and actual exposure

- 113 existing identities and 60 grammar products were resolved as KNOWN_ID or COMPOSITION_ONLY: **173 bypasses, zero EG2 retrievals, zero new identities or initialization rows**. No gap or semantic mapping was rejected/deferred; the eight pedagogical choices deferred to REVIEW.
- Source meanings and 20 recent-family leaf definitions remain authored in #80/#84/#85 and predecessor Python. Codex authored the reusable product grammar; native helpers authored no semantic definition.
- The independent cohort contains 3,421 new TRAIN identities: 1,085 fresh prior, 1,024 grammar cross-stage, 1,312 weak-skill. All 60 cross productions have formally admitted rows with both causal witnesses. Final contains 448 fresh varied/composite plus 120 grammar cross cases.
- 24 grammar candidate slots were actually offered to Kev across eight panels; **zero candidates and zero new rows were Kev-selected**. All eight explicit review outcomes and alternative sets are preserved.
- Exactly 8,192 exposures: 3,072 current / 1,024 fresh prior / 2,048 cross / 2,048 weak; all batches satisfy 12/4/8/8 and old/recent weak floors plus family ceilings. 5,365 distinct identities were exposed, including 3,237 new identities. Every one of 60 cross productions was exposed through broad fallback.
- 1,007 current-stage exposures retain historical #110 helper tags. They are inherited authored material and are not U7B teacher selections. Complete per-candidate/lesson attribution and related DEV/final scores are in [provenance.json.gz](run-01/provenance.json.gz).

## Lineage, resources and proof

Frozen training code: `e12f8a0` (full SHA in plan.json), based on #111 `66e44542abf429699f541ee272e2827d39be3f09`. 352,512 parameters, 113 IDs, width 96, three layers, six heads, context 96, FP32 CPU, one thread. All incoming tensors, graph rows, AdamW moments, hyperparameters, counters and RNG were loaded intact; no expansion or reset occurred.

Parent checkpoint SHA-256: `248a82ac92005f7b245751d6ea211d8296189de797f702349451f74383d75799`. Parent model-state SHA-256: `5ec251f79620156a83be5ae3cdcdc961d071e75ff1f6bcc3ed721f4482952034`.

Final checkpoint SHA-256: `020af0943478598c0bbd7345c9c625e3ad4a157591e4cb878c0006281ba0d0ab`. Final model-state SHA-256: `4f6e42564a49e78d77c4cc0832a08c766d7e939062d9f7ab64312d9ba665b3df`. AdamW state SHA-256: `5a0c45ba9e3b050047dec495e3da880021435f7c2038e134017fa0ebbb116002`. [Checkpoint](run-01/after.pt).

405,350 nonpadding tokens; 667,168 padded positions. Student process: 34.88s wall (includes eight helper calls), 35.00s CPU, 522.2 MiB peak RSS. Gradient operations: 12.18s; adaptive DEV scoring: 16.22s. Semantic/cohort preparation: 13.94s.

Native Kev: 48 qualification + eight pedagogy calls, 19.50s total request wall; 31,661 reported input and 8,411 reported output tokens. EG2: zero calls/texts/time. Native trained pointer head `jaredpalmer/kev-4b@6cfce5c2fa4b4bd64026336ab649c5ca78857d52`, source `6b719c3c3f367295f6ef336f4f751cf5ff970abc`, MLX/BF16/MPS, loopback service reused. Native unified-memory peak was not measured; process RSS is not a complete Metal-allocation metric. No paid provider, download, helper fine-tuning or rented GPU. Engineering/intake and machine ownership/energy costs were not metered.

Exact fresh-process replay reproduces **all 256 gradient updates, losses, exposures, final weights, AdamW moments and 4,060 predictions**, with no new helper inference. The first replay failed because canonical archive JSON sorted payload criteria. The separate archive adapter reconstructs order from exact saved HTTP bytes without editing frozen sources or decisions. Original failure, red/green logs, audit source hash and corrected readback receipt are retained. [Replay](run-01/replay.json), [archive receipt](run-01/archive-replay-receipt.json), [shortcut audit](run-01/shortcut-audit.json.gz).

23 focused tests cover policy/compiler admission, target/option identity, exact DEV boundaries, continuation, allocation, causal witnesses, archive order and inherited spiral behavior. Historical source/evidence and frozen U7 file hashes remain unchanged.

## Interpretation and next gate

This is an informative negative developmental epoch: combined context did not beat the simpler English interface; Kev abstained from the pedagogical job; a large sampled cross-stage gain coexists with a perfect structural shortcut and severe conservation loss. Live alternatives include shared-weight interference, shortcut pressure, insufficient critical rehearsal, generator distribution and limited feedback/utility information. No causality is attributed to EG2, bilingual context or Kev.

Preserve both checkpoints. Before another successor, specify a new counterbalanced cross-stage generator and pre-training integrity audit, keep critical truth/evidence/lineage probes separate from teacher feedback, and define a useful pedagogical objective that a bounded pointer engine can evaluate without a supplied winning answer. A/B/C canonical closeout receipts are in `closeout/`. The delivery remains draft and unmerged.
