# BILQIS-DN-01 result: null / reversal

As of 2026-10-11, **HYBRID_PILOT_NULL_OR_REVERSAL**. Both required native engines operated, exactly one matched scratch-student pair completed, and archived/live replay passed. The guided arm lost one HELDOUT path: **2/34 (5.88%) versus fixed 3/34 (8.82%), −2.94 percentage points**. No further seed, tuning round, curriculum adjustment or training rerun occurred.

The successful HELDOUT paths were all reserved outcomes. **Neither arm resolved any of the 30 HELDOUT truth cases correctly, and neither reached a logical-fold action.** This run does not demonstrate learned compositional semantic reasoning. The token-only cue baseline achieved 4/34 (11.76%). See the [frozen evaluation](evaluation-summary.json), [input audit](input-audit.json), and complete [fixed](fixed-predictions.jsonl) / [guided](guided-predictions.jsonl) error inventories.

| Split | Fixed exact paths | Guided exact paths | Guided − fixed | Fixed / guided final-terminal correctness |
|---|---:|---:|---:|---:|
| TRAIN | 8/128 (6.25%) | 6/128 (4.69%) | −2/128 | 8/128 / 6/128 |
| DEV | 2/34 (5.88%) | 2/34 (5.88%) | 0/34 | 2/34 / 2/34 |
| HELDOUT, primary | 3/34 (8.82%) | 2/34 (5.88%) | −1/34 | 3/34 / 2/34 |

Every active HELDOUT family scored 0/6 complete paths in both arms: orientation, scope, binding, evidence and consequence. Reserved cases scored fixed 3/4 and guided 2/4. Intermediate counts below concern actual student trajectories; unequal denominators reflect early unresolved termination, not teacher forcing. The ordinary-case view excludes reserved cases whose placeholder focus is called `read` or `orient`.

| HELDOUT diagnostic | Fixed | Guided |
|---|---:|---:|
| Structurally valid selection, all cases | 47/47 | 36/36 |
| Oracle-matching selection, all cases | 10/47 | 4/36 |
| Ordinary-case directed orientation | 0/25 | 1/13 |
| Explicit binding instruction alignment | 6/12 | 1/12 |
| Explicit evidence-add instruction alignment | 1/6 | 0/6 |
| Ordinary evidence truth reading | 0 attempts | 0/1 |
| Logical folding / downstream consequence | 0 attempts | 0 attempts |
| Final expected evidence-world preservation | 29/34 | 28/34 |
| Final TRUE/FALSE/UNKNOWN/CONFLICT correctness | 0/30 | 0/30 |
| Wrong intermediate, correct resolved terminal | 0 observed | 0 observed |

Formal HELDOUT truth targets contained 9 TRUE, 8 FALSE, 3 UNKNOWN and 10 CONFLICT cases. Students terminated unresolved instead of emitting these labels. The formal evaluator preserves these distinctions; model recognition of them was not demonstrated. The full confusion inventories also retain missing, outside, ambiguous, unsupported and abstained states separately.

The controlled regression `test_wrong_relation_can_leave_terminal_label_right` deliberately reverses the first relation in `OR(relation(a,b), NOT(relation(b,a)))`, then follows formal transitions. Its coarse terminal label matches while its path differs. That is a grading regression fixture, **not an observed neural success or a manufactured student prediction**. The observed models usually terminated before such a case could occur.

DEV retention is recorded after every 96-step block, including per-family competence and confusion. Both arms ended at 2/34; stage curves and observed maxima are in [paired-training.json](paired-training.json). These observations suggest poor retention and premature reserved routing; this pair does not isolate their causal mechanism.

The teaching policy was distinguishable but weakly exercised. Kev accepted **1/16 choices**, with a meaningful eligible alternative; **15/16 (93.75%)** used fallback. Eleven proposals selected abstain, seven had margins below 0.05; those counts overlap. No native scoring error occurred. Fixed order was B00–B15. Guided order was B00, B01, **B03, B02**, B04–B15. Thus the only ordering change swapped two blocks. This supports the code's identifiability flag, not a broad claim that Kev organized the curriculum effectively. Treatment also received nonsealed DEV feedback, so the intervention is the integrated EG2/Kev/DEV policy.

Both students had 110,272 parameters, width 64, two transformer layers, four heads, context 384, and AdamW at learning rate 0.001 / weight decay 0.01. Each consumed 16 × 96 optimizer steps, batch 32: **49,152 transition exposures and 5,942,706 nonpadding tokens**, from the same 592-row pool and exact frozen batches. Their common initial neural-state hash was `b260787fcc0ed0df38a0c5c0af9dc5235d495b26717875af969ff9b5db95ac70`; exposure hash was `fae68c0022fcf845c49e67c4646d0221d76ff4786fd02791f8451492586e7649`. Both final state hashes changed. No pretrained helper weights, vectors, hidden states or soft targets entered the optimizer. Ternary forward operations used FP32 master weights and float emulation.

The formal substrate remains `bilqis-alpha-cogal-0.1.0`. New feature / initializer / codec identities are `decision-structural-features-0.1.0`, `decision-dct-initializer-0.1.0`, and `decision-control-codec-0.1.0`. Historical source/target collision remains a regression; new role rows recompute exactly and have L2 distance 0.144957. Feature basis, projection and tensor hashes are preserved in [initializer.json](initializer.json), [features.json](features.json) and [geometry-proof.json](geometry-proof.json).

The frozen pool contains 128 TRAIN, 34 DEV and 34 HELDOUT episodes. Dataset digest is `4f56c4285a10d1166ed443c32f2a49bfe46b488274404ab8256103a450b2cd0b`; batch digest is `015239fc785b27aaaf9e5f8c1ba81f0237183bb34c9b96bc6acf1225e838a9ea`. All HELDOUT compositions are absent from TRAIN patterns, and their labels/results were excluded from teacher guidance. The domain is historically exposed and these compositions are **not independent SEALED evidence**. [Manifest and split hashes](manifest.json).

Native `mlx-community/embeddinggemma-2-bf16` used MLX 0.32.3 / MLX-VLM 0.7.4, pinned VCS source `3d87e88402f307efbf68e568971aa887ee7d9ed0`, the required embedding loader and local-only tokenizer. It cached 147 documents, 196 queries and 16 curriculum descriptors: 359 encodings, 768-dimensional references and separately normalized leading 256 dimensions. Retrieval used K=8 without gold insertion. Native trained Kev used `jaredpalmer/kev-4b@6cfce5c2fa4b4bd64026336ab649c5ca78857d52`, MLX/BF16 on MPS with rank-16 LoRA/pointer head; source `6b719c3c3f367295f6ef336f4f751cf5ff970abc`. Its environment used MLX 0.32.2 and MLX-LM 0.32.0. [Resolved identities and local file hashes](runtime-identities.json).

| Initial-panel retrieval diagnostic | 256 dimensions | 768 dimensions |
|---|---:|---:|
| Top-8 target recall, all frozen cases | 155/196 (79.08%) | 167/196 (85.20%) |
| Top legal candidate correct, all cases | 78/196 (39.80%) | 80/196 (40.82%) |
| HELDOUT target recall | 30/34 | 30/34 |
| HELDOUT top legal candidate correct | 18/34 | 18/34 |
| Gold cosine exceeds all measured hard negatives | 77/176 | 73/176 |
| Mean gold-minus-strongest-hard-negative cosine | −0.002839 | −0.002874 |

Hard negatives are substantive, structurally legal alternatives that mismatch the independent oracle target. Missing / inapplicable margins remain explicit. Query truncation affected **195/196** cases at 256 tokens. Goals appeared first, but world descriptions could be incomplete. Typed inverse, contrast, dependency, exclusion and other relationships remain separate from cosine ranking. [Per-query ranks, rejections, misses and margins](retrieval-metrics.json).

On the declared 12 DEV qualification panels, direct Kev and raw EG2→filter→Kev each chose 9/12 oracle targets; retrieval recall was 10/12. There were 24 real Choice calls, no errors, 3 direct and 4 hybrid low-margin responses. The separately attributed complete-panel fallback activated in 5/12 cases; the executed safe combined pipeline achieved 8/12. These initial-panel DEV diagnostics are not a full-path semantic qualification or complete #65/#88/#89 acceptance. [Actual requests, probability vectors and fallback records](qualification.json).

| Measured resource component | Seconds |
|---|---:|
| Semantic preparation / audit / initialization | 16.38 |
| EG2 loading / encoding / retrieval | 1.65 / 2.89 / 5.04 |
| Kev qualification, 24 calls | 10.80 |
| Fixed arm total wall / total CPU | 121.44 / 120.48 |
| Guided arm total wall / total CPU | 512.86 / 125.83 |
| Fixed / guided optimizer wall | 99.05 / 103.54 |
| Fixed / guided DEV wall | 22.33 / 23.46 |
| Fixed / guided intermediate checkpoint wall | 0.053 / 0.053 |
| Kev curriculum, 16 calls, included in guided wall | 385.78 |
| Evaluation process wall / user+system CPU | 14.41 / 14.11 |
| Archived replay process wall / CPU | 2.12 / 2.08 |
| Live replay process wall / CPU | 15.42 / 12.45 |

Host: Apple M3 Ultra, 96 GiB unified memory, 28 CPU cores. Student training used one CPU thread. Peak student-process RSS was 418/423 MB (decimal; sequential cumulative process maxima). EG2 native allocator peak was 2.20 GB; encoding process RSS was 2.06 GB. Kev's five-second sampled RSS peak was 5.29 GB, a lower bound rather than a unified-memory peak. Cache telemetry ended at 12 hits / 32 misses / zero OOM retries over 44 requests, including one preflight smoke, 24 qualification, 16 curriculum and 3 live-replay calls. No paid inference or optional engine was used. Kev loading time, separate DEV/checkpoint CPU time, total unified peak, engineering/Codex costs and monetary spend were not instrumented. Stage wall measurements exclude some serialization/hash overhead; they are not a complete end-to-end economic total. [Resource receipts](resources.json).

The full pretraining repository suite passed **82 tests**. The replay-only correction passed **12 focused tests**, including two new regressions. Red-stage failures are retained locally; an initial zero-test discovery command was corrected to use `-s tests`. No experiment phase failed or retrained. Final independent review closure was unavailable after the review agent reported workspace credit exhaustion; the concrete identified bindings were covered by passing regressions and actual replay. Tests are [recorded here](unit-tests.txt) and [here](replay-repair-tests.txt).

Archived replay reran **46 neural case/arm records** (23 showcased tasks), with exact step/state/panel/choice identities and logits/probabilities within absolute tolerance 1e−6. Live replay reran those students, reproduced **196/196 EG2 rankings exactly**, and reproduced **3/3 Kev choices and complete probability vectors with identical request hashes**. Full-engine traces exist for qualification DEV gallery cases; HELDOUT entries explicitly mark unavailable Kev traces rather than inventing them. [Replay summary](replay-summary.json).

A replay-only source correction followed the frozen evaluation: sorted receipt dictionaries could reorder Kev options. The live check now reconstructs the original serialized request and checks its hash. Frozen manifest, training and evaluation remain unchanged; the old source and exact patch are preserved under the [append-only amendment](replay-source-amendment-01.json). No neural behavior, corpus, oracle, teaching policy or evaluation endpoint was changed.

Historical alpha reported 58.7% DEV and 46.5% compositional final-label accuracy with 76,160 parameters; its checkpoint and microscope remain untouched. Those four-class results have different architecture, data exposure and endpoints and are **not a matched comparison** with this experiment. Neither the new initializer's independent causal benefit nor superiority over language-first learning, general language competence, universal efficiency or native low-bit acceleration follows from this single pair.

See [HANDOFF.md](HANDOFF.md) for source revisions and replay commands, and the [source/evidence ledger](source-evidence-ledger.json) for claim bindings and raw artifact checksums. Owners #5, #62, #65, #70, #81, #88 and #89 receive reusable implementation/evidence through the successor PR; their full acceptance is not asserted.
