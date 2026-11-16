# Architecture Decision Record

**Current curriculum direction: ADR-083/084 (2026-10-22), foundations before worlds; Boolean mastery does not gate C.**
Logic/cognitive algebra → mathematics → physics; selective lexicon Chapters 2, 3, 6.
The event-state experiment is historical, not the next teaching objective.

Append-only decisions from the user. New decisions get a dated entry; do not rewrite historical decisions into new authority. This log is private to the Bilqis MLX implementation.

## ADR-001 | 2026-10-15 | Private MLX successor

The user established `Entif-AI/bilqis-mlx` as the private implementation home. Controlling full text is the protected `IPR-0220` archive. Public Bilqis #160/#162 carry only publication-safe summaries. Preserve the complete old FP32 model and native AdamW, historical checkpoint archives, and prior code. Do not launch neural training as an agent.

## ADR-002 | 2026-10-15 | Genuine letter grades, not old G labels

Historical `G##` units are capabilities, not future school grades. Introduce actual lettered grades containing around six to nine comparably difficult, prerequisite-compatible capabilities, starting at A unless `--resume` was explicitly selected. Grade mastery requires one intact complete student and its own optimizer passing 100% of that grade's capabilities at one checkpoint. After each full grade pass, conduct two freshly ranked weakest-three recovery rounds from current and previously passed capabilities. Old-grade regressions need not block the current grade. A frozen champion earns one future teacher vote per mastered grade pointer, regardless of shared checkpoint file count; whole-school soup weights reflect the same pointer multiplicity, and soup is a teacher rather than a synthetic student. The old 1150/1150 rule is historical, not the new graduation criterion.

## ADR-003 | 2026-10-15 | Operator dry-runs and durable root docs

The user expressly authorizes agents to execute inert preflights and dry-runs directly. Keep concise current `AGENTS.md`, polished human-oriented `README.md`, this brief append-only `ADR.md`, and a short latest-state `HANDOFF.md`. The files may have multiple authors: coordinate with current contents and use minimal, checked edits rather than wholesale replacements.

## ADR-004 | 2026-10-15 | New Ithkuil alignment without legacy ABI rupture

Begin aligning newly introduced semantic primitives and concepts to **New Ithkuil** immediately. Preserve historical legacy semantic primitives *exactly as they are* to retain the previously trained model. New alignments are separate versioned mappings; a cognate, approximate analogy, or research seed never grants permission to relabel the original token graph, declare a new mastery gate satisfied, or test untaught abstractions. The uploaded curriculum registry is input and provenance, not automatic training authorization.

## ADR-005 | 2026-10-15 | Open-ended semantic vocabulary and lexicalized roots

The user explicitly rejects treating the historic 222-token checkpoint as a semantic ceiling. Extend Bilqis through New Ithkuil roots and morphology, external mathematical, logical and reasoning concepts, and independent lexicalized roots where composition would obscure a concept's distinctive meaning (examples supplied: `enshittification` and `shibboleth`). Preserve every legacy root/token ID and previously trained whole-student representation; allow future growth well beyond the 330 proposed Semantic Bridges entries. Research entries are not automatically acquired knowledge. Allocate and teach new identities only through source-grounded admission and prerequisite-respecting instruction, without silently rewriting the prior neural vocabulary.

## ADR-006 | 2026-10-15 | Foundational pasigraphy token identity and New Ithkuil conformance

The user expressly corrects the generic-LLM explanation: **every Bilqis token must map one-to-one to an identifiable, human-interpretable semantic identity/function in the shared pasigraphy catalog**. This includes meaningful syntax, operators, grammar, referents and lexical primitives; it is not a requirement that every token independently be a dictionary word. Every learned token must be tracked in the canonical **Bilqis Curriculum Registry** spreadsheet throughout the New Ithkuil training regimen at minimum. Preserve existing IDs with their original source semantics; an unreviewed legacy description is **not** an independently attested New Ithkuil equivalence or mastery receipt. More complex meanings are generally sequences of multiple registered tokens composed by faithful New Ithkuil lexicon/morphology/grammar rules, with independently source-attested formation, decoding, prerequisite, contrast, and conformance tests. The curriculum is fundamentally a progressive New Ithkuil specification test suite yielding a deliberately interpretable shared lingua franca for heterogeneous AI systems, vendors, security, governance and alignment experts, rather than opaque emergent Neuralese. Relaxation beyond the governed starter dialect may follow completion of New Ithkuil training, but is **not** an automatic termination of token accountability. The controlling verbatim correction and its protected authority are retained in `socr8s/private-ip#335` (IPR-0220, user clarification 2026-10-15). This decision **supersedes** any earlier suggestion that Bilqis tokens are semantically incidental or need not be individually cataloged.

## ADR-007 | 2026-10-15 | Versioned, approved living semantic catalog and New Ithkuil source-first review

The user supersedes an over-strict requirement that a trained model fail when the latest live spreadsheet rows differ from its frozen semantic projection. The canonical pasigraphy catalog evolves through explicit revision proposals, human review, versioned approval and compatible migration; historical model/token semantics remain pinned to their last approved version and continue unmodified while changes are evaluated. Editorial clarification or approved NI aliases do not destroy previously learned competence. Substantive meaning changes require a new curriculum/version and suitable instruction/assessment rather than retroactive renaming of the trained embedding. Every candidate root must **first** be sought in the current official New Ithkuil grammar and lexicon at ithkuil.net, whether or not it appears in the current Semantic Bridges sheet. Custom primitives should be rare and well justified, with plausible future exceptional research seams at Entif/Rosetta and the Metacognitive Atlas Rationality research frontier, not presumed novel from terminology alone. `syntax.bind` vs `NI-LX-009` is a priority review case, with no forced equivalence before checking actual codec and lexicon roles.

## ADR-008 | 2026-10-15 | Semantic alignment first, before further lessons or training

The user directed that as much of the existing historical semantic vocabulary as possible be mapped to **current official New Ithkuil grammar and lexicon before** authoring more lessons or resuming training qualification. The full 222-token historical inventory has now been given 222 distinct, source-linked **research proposals** in `Token Mapping Reviews`, not 222 approved equivalences. The new mapping draft is `mapping-draft/20261015-b`; the original complete student continues on pinned `legacy-source/v1`. Distinguish exact lexical root/stem matching, required morphology/syntax, typed referent placeholders, operator compositions, serialization-only functions, and unresolved formal-semantic differences. Source review and human semantic acceptance precede curriculum release. Consult `docs/provenance/NI_SEMANTIC_CENSUS_20261015.md` for findings and missing qualification evidence. This decision does not authorize neural training, relabeling the historical model, or adopting the preliminary proposals.

## ADR-009 | 2026-10-15 | Delegated semantic stewardship and scoped review successor

The user expressly delegated adjudication of the 222 historical Bilqis/New Ithkuil crosswalk proposals to the assistant, superseding the requirement for individual human signoff on these semantic annotations (protected IPR-0220 comment `6187168824`, independently read back). The assistant may approve qualified relatedness, grammar/composition strategies, and internal-protocol classification while rejecting misleading lexical equivalences and holding insufficiently substantiated grammatical mappings. The native registry now records `mapping-review/20261015-c`, a **partial semantic approval with holds**, not an NI conformance-certified or model-adopted version. Review counts at native readback: 19 approved qualified relationships, 89 approved composition strategies, 19 approved native protocol classifications, 1 rejection of exact equivalence (MOD versus division), and 94 held for source/grammar review. The 222 historical identities and `legacy-source/v1` pinned student remain unchanged. This decision does not authorize lessons, neural updates, new root admissions or model-weight changes. The status records bounded semantic judgments based on the source-accounted census and official number grammar; the held entries require deeper lexical/morphosyntactic analysis before release.

## ADR-010 | 2026-10-15 | Resolve 94 semantic holds by formal source semantics, not invented NI wordforms

Following the user's instruction to resolve the remaining holds, the assistant located original Boolean, finite-world, evidence, set/function, provenance and arithmetic interpreter operations and reviewed their official NI lexical/grammatical candidates. The `mapping-review/20261015-d` successor has **222 distinct scoped semantic dispositions**: 28 qualified, 90 compositional strategies, 21 native protocol, 21 named-referent strategies, 61 exact-source typed formal adapters, and 1 explicit rejection of exact lexical equivalence. Original c decisions and 94 pending statuses remain preserved in the vC snapshot; the new 94 decisions are individually recorded in `NI Adjudication vD` and `docs/provenance/NI_SEMANTIC_ADJUDICATION_VD_20261015.json`. The review corrects generic lexeme matches that would conflate finite-world entailment with universal consequence, paraconsistent support/refutation with NI validation, abstract graph kinship with human kinship, and formal mathematical operators with lexical analogies. **This closes the classification review only**, not NI morphological legality, independent wordform compilation, lesson admission, neural knowledge or training readiness. It does not change the original graph, checkpoint, token IDs or `legacy-source/v1` model pin. Further source-attested grammar compiler/conformance tests are required before lessons can resume.

## ADR-011 | 2026-10-15 | First executable NI construction, bounded morphology only

The assistant may implement independently source-checked language constructions under the user's continuing instruction to begin New Ithkuil conformance development. The first neural-inert Python module composes and reverse-parses official stem-1/BSC numerical roots 0..100 (nine-degree TNX, thematic/partitive case, explicit/default or wa shortcut morphology) and basic neutral monadic referentials. Exact published Ch.13 examples serve as external witnesses; the 101 historical numeric tokens receive a separate reproducible rule-based research projection that preserves IDs 121..221 and distinguishes five direct official wordforms from 96 derived candidates. New Ithkuil cardinality is not retroactively equated with Bilqis's typed scalar integers. This is a **bounded grammatical subset**, not full wordform legality, higher syntax, official fluency, new lexical admission, training readiness or model mastery. The original whole student and AdamW remain untouched; the remaining grammar/case/prosody, proper-name carrier, complex referentials and scope tests are next-stage gates. See `docs/provenance/NI_CONSTRUCTION_SCOPE_20261015.md`.

## ADR-012 | 2026-10-15 | Correct Grade A validity before human training; release only proven boundaries

The user directed an immediate repair of the Grade A defects to support an eventual human-operated training run while other New Ithkuil grades are developed independently. Source analysis found that `A.MEMBER` TRUE/FALSE answers were perfectly predicted by set cardinality (two vs one member); corrected examples use equal cardinality across both answers. Historic equality and edge predicate evaluations also had shared implementation paths masquerading as independent oracles. A third separately written interpreter now checks all six typed predicate records. A 216-record candidate manifest fixes 144 teaching and 72 full gold-bearing examination inputs, independently regenerated and source-bound, with frozen exam digest `7f351f93b81a1d08a45dd53d5f253ad34c238019015e84284d50ca40378a1370`. Exam scoring rejects any missing/extra typed answers or fabricated 1/1 perfect scores.

Partial courses may now graduate their **last published grade** into `AWAITING_NEXT_GRADE`, never `WHOLE_SCHOOL_MASTERED` without an explicitly complete full program. Append-only grade migration preserves each earlier grade's exact configuration, exam seal and champion/student checkpoint. Exam hashes remain fixed across visits and may change only at the explicit next-grade boundary to a separately sealed cumulative rubric. A full-size detached clone of the original 222-token FP32 student and all 39 native AdamW tensor identities demonstrated source-bound cross-entropy, gradients, clipping, one AdamW update and whole semantic-bundle save/reload parity against PyTorch on Apple GPU, with the original model unmodified. These are **candidate source, scheduler and disposable backend qualifications**, not Grade A New Ithkuil release, mastery, adaptive-teacher integration or authorization for actual neural optimizer updates. Keep `npm run train` fail-closed until a complete human-operated runner and source-conformant curriculum have their own verifiable release. See `docs/evidence/grades/GRADE_A_REPAIR_AND_BACKEND_20261015.md`.

## ADR-013 | 2026-10-15 | User accepts bounded Grade A and commissions an experimental human-only trainer

The user explicitly rejected the ongoing training hold as riskier than an
imperfect, improvable first release: **the existing six-capability Grade A
curriculum is accepted, and the assistant must write the trainer.** This
decision supersedes the previous hold on *admitting that exact tranche*.
It does not assert independent New Ithkuil morphological certification,
permit changes to historical 222 token identities, authorize the agent to
run the original optimizer, approve future grades, or waive intact
same-checkpoint graduation. The unchanged 144 teaching/72 examination
source manifest is adopted through a separate versioned acceptance contract,
`bilqis.mlx.grade-a-user-accepted/20261015`.

The human-only experimental trainer implements source-checked loading of
the complete original FP32 student/AdamW, inheritance of the original
teacher's learned selection policy rather than reset, native MLX binary
teaching steps, source-train-only policy rewards, complete own-AdamW
checkpoint and atomic school/teacher resume receipts, six-capability
same-checkpoint rubric, and the existing full-pass/weakest-three recovery
scheduler. Every initial or resumed run has explicit user ownership
(`--human-run`), bounded visits and disk reserve, and stops Grade A
completion at `AWAITING_NEXT_GRADE`. The assistant tests with disposable
synthetic weights and read-only original model conversion only. See
`docs/history/operations/GRADE_A_HUMAN_TRAINER_20261015.md`. Successful first real-user
training, learned competence and advanced NI grammar remain future
empirical milestones, not presumptive release gates.

## ADR-014 | 2026-10-15 | Curriculum AST generates lessons and probes; failed lessons trigger structural correction

The user rejected repeated lesson-specific repairs and reactive whack-a-mole
following previous training stalls. Diagnose *classes* of instructional failure,
prevent recurrence, and use a typed AST derived from the canonical Curriculum
Registry to deterministically construct families of semantically valid lessons,
metamorphic variations, counterexamples, generalization checks and future
construction tasks. Reusable mathematical axioms and source-grounded linguistic
grammar should generate their own exercises wherever gold semantics can be
independently verified. Instructional breadth is an engineered property, not
a collection of manually authored exceptions. The AST must reflect the
Registry's stable token meanings, prerequisites, grade dependencies, lesson
construction intents, and source/evidence status.

The first bounded importer snapshots the native Registry, preserves exact
sheet/row provenance and protected proposal states, binds the already
accepted Grade A curriculum to its 222-token historical ABI and creates a
deterministic *candidate* authoring frontier for proposed future stages.
Grade-level Sheet aliases and New Ithkuil research seeds are planning input,
not release decisions. A generated exercise or proposed next task does not
become a neural lesson without source/oracle and versioned admission. The
existing human-operated Grade A run, its teacher/AdamW, and its sealed exam
remain intact. See `docs/architecture/CURRICULUM_AST_COMPILER_20261015.md`.

## ADR-015 | 2026-10-15 | Trainer limits must announce and persist their stop causes

Three human-operated Grade A commands each reached the previous implicit
48-visit ceiling. The third invocation returned to the shell after exactly
48 more committed visits while the requested 90-minute time budget was still
the operator's visible intent. The trainer recorded individual visits and
assessments, but no session-ending event or terminal explanation. This was a
misleading operator contract and an observability failure, not observed
model corruption or Grade A mastery.

`--minutes` is now the default session budget without a hidden 48-visit cap.
The human may still set an explicit finite `--max-visits`; disk reserve and
exclusive writer lock remain enforced. Finish an already-due sealed grade
assessment before exiting normally. Every normal stop must produce a
human-legible reason and an append-only event identifying its limits, elapsed
time, committed visits, checkpoint step and resume status. Dashboard replay
and `npm run status` may display that event; the model/optimizer state pointer
must not be rewritten merely because a shell session completed. This pattern
applies to future letter grades so fast MLX execution does not look like a
silent failure. Agent tests remain neural-inert or disposable.

## ADR-016 | 2026-10-15 | School50 must expose grade-neutral, provenance-bound learning diagnostics

The human requested the historical six-panel dashboard's analytical depth
while Grade A MLX training was active, and explicitly instructed us to
restore **future-grade telemetry capability now** rather than revisiting
each missing statistic with every new grade. Retain all six legacy panel
identities, but project letter-grade receipts through a shared, versioned
read-only metric contract. Different curricula may have different rubrics,
answer types, construction families and available teachers. Interpret their
metrics by evidence and source identity, never by grade-specific strings or
the retired 1,150-item rubric.

Show first/latest/best sealed exam scores with each checkpoint step,
per-capability first/previous/latest correctness and gains, distance from
100%, candidate source-training gain/reward/loss/gradient, actual adaptive
teacher settings, cross-grade regressions and recorded qualification state.
Allow future independently sourced sentinel/retention, semantic-family and
teacher-only soup receipts to populate the existing panels without a new
dashboard rewrite. Source-training results are *not* independent
generalization evidence; absent measurements remain explicit, not invented.
Require source/model identity for purported independent evaluations, and
never combine grade scores from different student checkpoints into an
apparent whole-school pass. Dashboard diagnostics are observational and do
not influence the adaptive teacher, optimizer, or lesson admissions.

Implementation: `bilqis_mlx/school_telemetry.py`, adapted
`grade_a_dashboard.py`, with the old `spiral_dashboard.TABLES` preserved;
contract in `docs/architecture/SCHOOL50_TELEMETRY_V1_20261015.md`. Runtime code changes
take effect on the next human-owned trainer invocation, not the active
process. All evaluation and rendering must remain neural-inert.

## ADR-017 | 2026-10-15 | Disk reserve is a first-class, non-destructive stop condition

The human's long, uncapped MLX run ended without a normal stop event at
generation 1242 / 993 visits / optimizer step 132648. The checkpoint run
occupied approximately 120 GiB. Read-only disk headroom was 100.28 GiB,
insufficient to satisfy the original protected 100 GiB reserve plus the
estimated 600 MB next checkpoint. `assert_headroom` was raising
`DISK_BUDGET_EXHAUSTED` outside the trainer's normal stop-receipt path.
This is a *resource-protection stop*, not an observed neural crash, training
mastery, or a justification to delete checkpoint evidence.

Expose a single source-of-truth disk budget witness for both preflight and
dashboard telemetry. At a committed visit boundary, insufficient headroom
now causes a normal `DISK_RESERVE_REACHED` stop with durable receipt,
free/reserve/required bytes and human-readable explanation. The original
fail-closed check still guards the actual bundle write against free-space
changes. Nothing reduces the reserve, prunes historic/student checkpoints,
or relaxes human-only optimizer authority. A future storage-efficiency
strategy must preserve verifiable full model/own-AdamW custody and be approved
separately, not concealed as dashboard repair.

## ADR-018 | 2026-10-15 | Best-score capability frontier

Capability champions are the best measured per-capability rubric scores, even
below 100%. A new checkpoint inherits all capabilities where it establishes
or consolidates a best. Old checkpoint binaries are superseded when no active
student, capability leader, or grade champion still points to them. This is
distinct from 100% whole-grade mastery. Only tested candidates become long-term
champions. Short-lived complete student+AdamW recovery checkpoints remain
necessary at exam or operator-stop boundaries. Each old durable receipt remains
historical evidence after its superseded binary is retired.

## ADR-019 | 2026-10-15 | Preserve School50 pedagogical parity in the MLX successor

The human corrects our repeated pattern of redesigning solved PyTorch
School50 problems without reviewing their source and lessons learned. MLX
changes the backend, not the instructional specification. Before extending
curricula or assessment, read the predecessor's source, teacher strategy,
answer-type and acquisition/transfer contracts as a required design input.
Where meaningful, explicitly teach a direct high-fidelity typed result and
its lower-fidelity TRUE/FALSE assertion with a verified false counterexample.
Assess atomic acquired meaning first, then gated compositions; exposed
teaching replay is not independent transfer. Maintain distinct developmental
candidate selection and sealed whole-grade qualification evidence.

The original v10 numerical school taught direct 0..3 answers with the
existing tied numeral embeddings, used all five evidence states, replayed
exact taught questions, and reserved held-out arithmetic sources. The
accepted current MLX Grade A contains only 144 binary training and 72 binary
exam rows, and its current best-score selection repeatedly consults the
fixed rubric. The new read-only `pedagogical_parity.py` and disposable
`typed_answer_training.py` reconstruct the prior source/oracle contract;
they are not an admitted curriculum, model-training release or replacement
for the currently frozen Grade A test. See the new pedagogical parity report
for explicit remaining scientific and release gates.

## ADR-020 | 2026-10-15 | Native semantic-token outputs alongside typed answers

The human clarifies ADR-019: restricting training to a four-way number-answer
classification and five-state truth classification is insufficient. An answer
such as `ADD(1,2) -> 3` must **also** teach emission of the existing
`school.number.3` vocabulary token using a full-catalog tied-embedding
readout. Retain the original direct-number and TRUE/FALSE contrast training
as complementary perspectives; do not substitute one for the other.

The source-oracled direct numeral row therefore carries an exact token identity
and numeric ID from the model's pinned semantic ABI. One research-only MLX
objective now combines restricted numeric, full-vocabulary semantic-token,
and five-state evidence cross-entropies without new embeddings or invented
semantic identities. The full-vocabulary head size tracks append-only model
vocabulary changes and refuses mismatches. This is a single-token output
construction, not unrestricted multi-token language generation or proof of
learned meanings. The currently approved Grade A trainer, fixed teaching and
examination manifests, complete student and AdamW remain unmodified; no
actual neural training is authorized by this experimental parity adapter.

## ADR-021 | 2026-10-15 | One bounded integer type scope and on-demand test regeneration

## ADR-022 | 2026-10-15 | No item embargo in generated semantic assessment

The user rejects the inherited notion that questions used for assessment may
never be used for instruction or teacher feedback. The intended school teaches
by generating varied constructions from source-attested semantic rules.
Assessments likewise sample those rules, score without changing weights during
the measurement, and expose every missed construction to the adaptive teacher.
An independently checked oracle is required; a secret question inventory is
not. The original fixed Grade A exam is historical evidence, not a precedent
for future generated-exam embargo rules. Never delete or falsify its receipts.

Keep distinct source competence and comparable checkpoint scores: a challenger
and incumbent must be measured on the same fully materialized, seeded cohort
with a versioned rubric and preserved question/source IDs. A finite 100% score
means perfect on that cohort, not mathematical universal mastery. The standard
for graduation remains a complete same-checkpoint grade assessment and the
whole FP32 student with its own AdamW, not a synthetic mixture of winners.
Champion/custody retention remains aggressive and evidence-driven.

The new pure `generated_assessment.py` provides provenance-bound cohorts,
checkpoint scoring, feedback-ready failures, and same-cohort comparator
validation. The old human-operated Grade A path remains unchanged until the
replacement scheduler, teacher rewards, typed predictors, migration strategy,
telemetry and regression tests can be verified end-to-end. Historical sealed
files and saved training remain preserved throughout the transition.

The user requires integer concepts to start with a deliberately small range,
and to expand without rewriting any lesson or test case by hand. The single
`BILQIS_INTEGER_MAX` environment setting (default `3`, currently attested
range `1..100`) defines the upper bound of exposed number operands,
intermediate results, and direct answers. It does not restrict the original
model vocabulary or replace stable `school.number.N` token identities. The
source-pinned type signatures and independently agreeing arithmetic oracles
generate varied arithmetic/Boolean/eq/negation specimens from seeded ASTs.

**Generated assessment files are never regenerated just because the setting
changed.** An explicit `npm run curriculum:tests -- --regenerate-tests=type:integer`
rebuilds *every test family whose type-dependency graph contains Number* and
leaves unrelated Boolean-only suites byte-for-byte unchanged. A changed
integer scope makes old generated tests stale until this operation occurs;
normal verification fails closed rather than silently evaluating the old
limits. Sealed historical Grade A tests are outside this generated-test
system and must not be rewritten. Each generated release is content-addressed
and the current pointer is atomically published; source partition identities
are stable across seeds and limits. The developer may sample fresh training
examples on each pass without automatically resampling saved assessment
sets. These are still research-only typed constructions, not proof of
live neural acquisition or grade qualification. Full contract and example
commands: `docs/architecture/TYPED_INTEGER_GENERATED_TESTS_20261015.md`.

## ADR-023 | 2026-10-15 | Live six-predicate Grade A and human-run legacy migration

**Authority:** User-directed removal of permanent teaching/assessment item embargo after ADR-022, limited to the existing six accepted direct Boolean capabilities. The historical source manifest, 144 teaching specimens, fixed 72-item exam, original student and native AdamW remain immutable historical evidence. No broader new semantic grade or NI morphology is admitted.

**Runtime:** The ordinary `npm run train -- --human-run` entrypoint now compiles a new stable Grade A semantic rubric version from the accepted six predicates. Every visit and optimizer step samples reproducible, source-oracle-checked fresh teaching specimens. Every due exam draws twelve balanced fresh items per capability (72 total, truth and world-size coverage), records the sampled item payload/seed/content SHA under `cohorts/`, and requires 100% on that entire sample at one complete FP32 checkpoint and its own AdamW to certify Grade A.

**Fair promotion:** Before claiming a new capability best, reload and score every distinct currently pinned and historic checkpoint on the *same newly sampled cohort* as the challenger; save the individual replay receipts. Different cohort numerator scores are descriptive observations, not comparable gains. Only after model/optimizer pointer publication may unreferenced candidate bundles be retired; historical grade champions remain protected as archival evidence. Teacher feedback may reuse every missed semantic specimen after the assessment is fully scored. No sealed exam gold is exposed during inference.

**Saved runs:** On explicit human `--resume`, inspect legacy `v1` saved state and model+optimizer custody, preserve original generations and source histories, then write a new-generation stable-course pointer that transfers original student weights and teacher observations unchanged. Legacy bests remain held until same-cohort replay; historical grade champions stay archived and cannot certify the successor rubric automatically. Repeated human resumes validate generated cohort hashes and reject source or optimizer drift. There is no separate curriculum activation flag. School50 reports live cohort SHA/generator/provenance and never conflates different sampled cohorts with matched-score changes.

**Typed outputs:** `integer_curriculum` and `typed_answer_training` already provide independent source-oracled numeric, five-state and full-vocabulary token objectives, with bounded Number generator and separately persisted on-demand suites. These research facilities remain outside the six admitted live Boolean Grade A capabilities pending a distinct source-backed admission decision. Persisted generated-test releases continue to rebuild only with explicit `--regenerate-tests=type:integer`; their old partitions are historical release metadata, not a live teaching embargo.

**Execution constraint:** Agent tests may use disposable synthetic MLX weights only. Actual full-student updates require the human's explicit `--human-run` on an interactive terminal; this code migration itself neither starts neural training nor rewrites historical bundles.

**Crash and code identity supplements:** An immutable next-generation state file whose latest-pointer publish was interrupted is checked against run lineage, model/optimizer custody and source authority before pointer recovery. Whole-student bundles are written and fsynced under `.bundle-staging/`, then published into `bundles/` only after complete readback. Incomplete staged metadata may be discarded; any staged tensor binary is quarantined for human custody recovery rather than treated as a valid champion or destroyed. The stable live semantic rubric hashes generator implementation sources (`live_grade_a`, source probe and independent oracle), so a changed sampler cannot silently reinterpret a saved assessment.

## ADR-024 | 2026-10-15 | Revalidate every known grade after each new graduation

**Direct user correction:** "Close, but with one correction: after graduating Grade B, make it go back through A and then B like Billy Madison, using this formula from here on out. That way, we revalidate all known grades before starting Grade C."

**New graduation sequence:** First earn A, then B. Immediately after B's initial 100% grade result, replay the full A grade and then B, in order, before commencing C. After C's initial graduation, replay A, B, C before D. Continue the same complete ordered known-prefix sweep following every newly mastered grade. Every replayed grade uses its ordinary sequential full-capability pass and, while mastery remains incomplete, two independently re-ranked weakest-three remediation rounds (active plus all previously graduated capabilities). Passing the active replay grade remains an intact same-checkpoint 100% gate. To advance to the next new grade, the final sweep checkpoint must independently score 100% on *all* already-admitted grades, not merely the last replayed grade. For a partial program, a regression in any earlier grade at that final checkpoint restarts its A-through-current replay rather than entering an unadmitted next grade. If the entire program has been explicitly marked complete, the existing final teacher-soup / failed-grade recovery contract remains available instead of silently certifying whole-school mastery.

**Model, teacher, and saved-state custody:** No grade revalidation starts a fresh student, resets an optimizer, changes existing grade champion identities, or prematurely retires a previously superior complete model+own AdamW. The scheduler adds only an optional `revalidation_target_grade` to the existing `bilqis.mlx.letter-grade/v1` state, so older saved school states load with the field absent. During backward sweeps, all previously graduated grade champions can cast their grade-linked votes, even when an already-mastered grade alphabetically follows the grade being replayed; duplicate pointers remain physically deduplicated. New generated assessment samples must still be source/oracle verified and compared on matched cohorts when selecting champion checkpoints. No permanent examination-example embargo is restored.

**Implementation boundary:** This ADR governs the pure multi-grade scheduler and a future source-admitted multi-grade human trainer. It does not retroactively undo the observed real 72/72 Grade A completion, amend the Grade A source-generator fingerprint, admit Grade B curriculum, or authorize any agent-run optimization on the actual Bilqis student. Additional grade admission and training remain separately human-governed.

## ADR-025 | 2026-10-15 | Source-attested first-composition Grade B and human-only continuation

**Authorization and prior boundary:** After directing cumulative A→B revalidation, the user explicitly directed the agent to keep working without requiring further approval: "So, why stop, then? You don't need me for this part." Under the previously delegated semantic source-review authority in protected IPR-0220, the agent may source, author, verify and integrate a next grade using existing admitted typed meanings, but **may not initiate real Bilqis optimizer updates**. The human still owns the actual `--human-run` invocation. Grade A's observed 72/72 at step 153144 is preserved as the initial B prerequisite. Grade B was not admitted under ADR-023/024; this is a separately versioned source-admission decision, not a retroactive redefinition of A.

**Admitted bounded Grade B:** Exactly six original `cogal.operator` identities: `NOT`, `AND`, `OR`, `XOR`, `IMPLIES`, and `IFF`, each evaluated as a typed Boolean connective over already-mastered Grade A `IDENTITY`, `PARENT` or `LINK` operands from three-/four-entity micro-worlds. These are the student's **existing original token IDs**; no new token, unproven root, unapproved referent, or later formal mathematics is introduced. Source authorities are the pinned original `bilqis_logic/kernel.py` truth tables and `bilqis_micro/kernel.py` recursive AST and dual independent interpreters; a new independent record oracle separately reconstructs source facts and applies the truth functions without importing either original evaluator. A canonical complete 72-item B witness is independently generated and source checked before constructing the executable B course. Per-capability exams contain twelve reproducibly sampled balanced TRUE/FALSE constructions and both attested world sizes. Lessons vary with seeds on every visit and optimizer step. Scored misses are available for subsequent teaching, not permanently embargoed.

**Grade and whole-student semantics:** The Grade A source rubric and full historical receipts remain unchanged. The successor `bilqis.mlx.grade-a-b-live/20261015-v1` admits a cumulative A+B **144-item** semantic rubric, separate from each sampled cohort's content digest. The grader requires a complete whole FP32 student plus its own native AdamW; all twelve capabilities are scored at the same student step, and every retained incumbent is compared against the challenger on the **identical** sampled cohort before roles move. B graduation requires 12/12 for each of its six capabilities; it then enters ADR-024's explicit A→B replay, and Grade C is unavailable until the final cumulative A+B checkpoint is 144/144. The original grade champions remain protected during regression. Previous grade champion checkpoints (deduplicated by SHA) cast one **per represented grade** vote to prioritize source-verified teaching examples they misclassify; their predictions never rewrite oracle gold or become a hybrid trainable student. Grade-specific adaptive teacher observation continues with the inherited strategy history.

**Resume, durability and operator presentation:** The existing human `npm run train -- --human-run --resume` from the saved mastered-A boundary runs source witness verification and appends the B course as a new immutable state generation without restarting or replacing student, own AdamW, teacher, 222-token semantic graph, A champion or original source history. Subsequent B resumes validate course and saved cohort SHA, source and generator fingerprint, and whole-checkpoint custody. A B admission interrupted after writing `states/N.json` but before `state.json` pointer publication is recovered using the existing fail-closed immutable-generation mechanism; the recovered course identity is used rather than misparsed as A. In-progress A runs do not require a working future B release. School50 continues with the same six panels and grade-neutral event projection. No untracked unrelated semantic-transformation files, archived source binaries, or external disks are changed.

**Event-lineage and grade-attribution correction (2026-10-16):** Adversarial review found that a crash after publishing a whole student+AdamW and immutable generation but before writing JSONL visit/exam/admission events could leave the dashboard permanently missing causal evidence. Initialization and all newly committed A/B admission/exam/comparison boundaries now carry a deterministic, generation-bound `delivery_outbox` in the same immutable state; resume scans the existing ledger, verifies payload and identity, and emits only missing events. A partial append, lost acknowledgment or pointer-recovered generation never retrains the student as an event-recovery strategy; an invalid ID/content fails closed. Distinguish the *taught capability's grade* from the active grade in weakest-three rehearsals: an A lesson during B recovery advances A's teacher-policy statistics rather than attributing its reward to B. Similarly, publish capability-best events under the completed exam grade even when initial B mastery immediately moves the scheduler backward to A. Grade-neutral School50's operator summary identifies the actual exam target rather than whichever grade appears last in a cumulative A+B score table. A future explicitly complete course stops safely for whole-school mastery or separately required teacher-soup integration; it cannot silently invoke a nonexistent visit.

**Explicit exclusion and evidence limits:** This is a precisely scoped **formal pasigraphy adapter**, not a claim of legal composed New Ithkuil inflected surface forms or of learning New Ithkuil vocabulary, morphology, native integer outputs, evidence-pair operators, or newly admitted Grade C. Original NI-adjudicated typed adapters have source-driven semantic truth tables; surface-form conformance remains separately unverified. Passing synthetic neural/disposable tests and source-oracle checks establishes an executable implementation, **not** that the real Bilqis already acquired B or retained A under B optimizer updates. Future semantic-release code changes must not silently change the stable rubric digest of an active saved school.

## ADR-026 | 2026-10-16 | Preserve Grade B mistake feedback, rerank true weakest three, and reinforce decomposed semantic prerequisites

**Trigger and observed student evidence:** After Grade B began under explicit human ownership, the user reported repeated near-chance exams and asked whether permanently sealed tests had returned. Read-only inspection of the actual saved model at optimizer step 155640 identified real regression: the current model scored A=55/72 and B=33/72 while the frozen Grade A champion scored A=71/72 and B=39/72 on the **same exact sampled A+B cohort**. On the first human B exam at step 153240, the current model had already dropped to A=56/72 versus the retained A champion's A=72/72 on that cohort. This is model forgetting and poor B acquisition, not simply random cohort comparability noise. The active B teaching/exam constructor has **no permanent item holdout**; unrelated research-only test partition metadata is not the live B curriculum.

**Source-verified feedback defect:** Although the prior Grade A no-embargo contract made every scored mistake eligible for direct instruction, `grade_a_trainer._take_exam()` replaced the whole queue of prior missed rows with the latest cohort's failures. Across 38 successive actual B exam intervals, 1,179 of 2,103 wrong answers (56.1%) belonged to capabilities with *no intervening teaching visit* before their corresponding misses were overwritten. This is measured loss of direct remedial opportunity, not evidence that mathematically equivalent fresh examples never appeared. `school.assess()` also excluded all first-round weakest-three selections when ranking the second recovery trio, even if they remained weakest on the newly scored cohort. That exclusion was not part of the user's direction to perform two **fresh** weakest-three rankings.

**Correction:** Re-rank the complete active-plus-mastered capability pool after every remediation round; a still-weak concept may be selected again. Carry previously missed, still-incorrect source-verified specimens into future teaching alongside new misses, removing corrected errors and bounding the active queue to 24 examples per capability with explicit resolution/eviction telemetry. The queue is *instructional*, not a frozen qualification sample. During each live B optimizer step, generate supervised A.IDENTITY/PARENT/LINK operand micro-questions derived from the **same attested worlds as current B logic expressions**; independently source-verify all operand gold answers, dedicate no more than one-quarter of the B step to those prerequisites, and give post-assessment direct misses final teaching priority. This teaches actual constituent relationships without adding old-grade sequential passes, unapproved roots, a new output ABI, permanent test embargoes, or a new scheduler.

**Preservation and evidence boundary:** Leave both source generator implementation files and their stable A/B rubric/code digests unchanged, retain original 222-token semantic graph, saved student FP32+own AdamW, earlier whole champions, historical cohorts and their receipts, human-only training gate, complete 144-item qualification and same-cohort incumbent comparisons. Regression and disposable integration tests prove the corrected scheduling, persistent miss queue, source-checked operand lessons and bounded batch composition; they do **not** establish that the human student has regained Grade A mastery or learned B. The newly taught B connective curriculum remains experimental, with A.MEMBER/EDGE/MAPS retention and teacher reward/generalization alignment explicitly unverified. Details: `docs/evidence/diagnostics/GRADE_B_REGRESSION_FORENSICS_20261016.md`.

## ADR-027 | 2026-10-16 | Protected generative-curriculum course correction and mandatory remediation authority

**Decision and authoritative issue:** In response to the user's explicit eight-part architectural/accountability review and instruction to preserve the findings before compaction, create and treat [protected `socr8s/private-ip` issue #336](https://github.com/socr8s/private-ip/issues/336) as the **open, controlling remediation specification** associated with `IPR-0220`. It captures the user's original five bad-lesson warning signals, actual Grade B regression and feedback loss, generalized AST/semantic registry requirements, source and prerequisite coverage, admissible lesson/grade/test editing, real diagnostic feedback, evolving teacher and cross-grade spiral learning, BIOS incident triggers, proof gates, and privacy boundaries. Every future agent must read the issue and carry its URL/identity, status, baseline, unresolved obligations and next safe steps into every handoff. This **private issue URL and its protected algorithms must be screened before any future public migration** of `bilqis-mlx`; public projections use the opaque `IPR-0220` identity without publishing the issue URL or private methods.

**Correction to prior implementation posture:** Generated sampled questions are **not** the same as a self-maintaining, source-attested, registry/typed-AST-driven curriculum compiler. Grade B's hard-coded six Boolean constructors and three Grade A operand families do not close all relevant prerequisites. The current six-panel dashboard reports some events but has not implemented the five user-defined detector→diagnosis→teacher-response→measured-outcome loops. An item being permitted to return as instruction does not imply it is ever scheduled before a newer sampled exam overwrites it. Existing `ADR-026` bounded error retention and direct B constituent-example changes are **provisional code-level candidate repairs**, not a completed generic solution: specifically **24 retained examples per capability** and an assistant-selected **up-to-25% B-batch prerequisite allocation** are *not* standing cross-grade policies and must not silently overrule the inherited adaptive teacher or its accumulated strategy history. Their synthetic test pass does not certify real neural acquisition or Grade A retention. The user has repeatedly prohibited unapproved policy reweighting, including the error recorded as `PM-2026-10-14-014`.

**Target contract:** Treat approved semantic tokens/primitives as typed, versioned, source-oracle-attested graph nodes with immutable identities and dependencies. Add or substantively edit a primitive only by resolving official New Ithkuil grammar **and** lexicon or explicitly delimiting a typed formal adapter, preserving the 222 historical token IDs and native FP32/own AdamW lineage, and performing affected-dependency change impact and separately governed admission. Compile proposed lesson/grade/test plans from approved semantic ASTs and prerequisite closure, identify all relevant cross-grade constituents and legal/illegal/positive/negative/contrastive witnesses, track explicit coverage debt and unmet admission gates, and generate fresh reproducible teaching and assessment from the *same* verified rules with no permanent question embargo. Test per-capability answer types, source correctness, alternative/metamorphic constructions, actual prediction-label distributions, durable learning, relevant prior-knowledge links and introductory simplicity. Distinguish an unsupported **new** construction that must not be admitted from otherwise authorized prior learning that must continue.

**Spiral, teacher and evidence boundary:** Preserve the user's complete active-grade pass, two **freshly** ranked weakest-three remediation rounds over all known grades, permission for temporary earlier-grade regression during new-grade acquisition, and cumulative A→B→...→current revalidation before the next grade. Grade promotion still requires full 100% at one entire student+its own AdamW; a retained grade champion casts **one vote per represented grade** even when pointers deduplicate, and frozen soups are teachers, not trainable students. Every detected learning failure is evidence to the adaptive teacher, **not** an agent's automatic fixed rehearsal quota, arbitrary hard stop, or secret held-out-item embargo. Source-grounded, same-cohort paired checkpoint comparisons support champion decisions; longitudinal generated-cohort trends require uncertainty-aware measurements. Failing to measure a dimension must yield `NOT MEASURED`, not an invented favorable result.

**Governance and release proof:** Mandatory near-top `AGENTS.md` rules cite this issue and enforce read-first guidance for *all* new/edited primitives, lessons, grades, tests, monitors and handoffs. On any material bug, regression, user correction or reusable anti-pattern, activate BIOS `references/runtime/FAILURE_INTELLIGENCE.md` and its Post-Mortem Logger, reconcile the canonical ledger, file/enrich the incident **before** substantial reuse, and verify native readback; do not defer until feature completion. The current incident is `PM-2026-10-16-001` with `RC-083`, `RC-084` and `PAT-066`. Implementation requires a versioned grammar/AST/dependency compiler, complete tracked coverage obligations, five executable diagnostic signals with negative controls, proof of adaptive-teacher noninterference, mutation tests that add/edit primitives and later grades, and human-only empirical validation. Root documentation and this issue may be updated now; **neither this ADR nor passing synthetic tests authorizes agent-initiated actual-student optimizer updates or promotion of experimental Grade B data-mix policy**. Preserve all unrelated uncommitted research and historical receipts.

## ADR-028 | 2026-10-16 | Original-ID functional composition and evidence-first upstream reuse

**User-confirmed course correction:** Stop extending hand-authored Grade A/B semantic constructors and free-form `SemanticLaw` strings as the future curriculum architecture. Preserve the original Curriculum Registry semantic, token, and lesson identities. The **code-resident, versioned canonical semantic AST/catalog** owns their bindings, and alone assigns any future Bilqis domain identifiers. The living Sheet and external source publications provide research, proposals, history, and attested meaning evidence; changing a Sheet row or label does not change an admitted model's meaning. Earlier architecture drafts in `docs/architecture/archive/01-03` are superseded by the compositional specification `docs/architecture/04-06`.

**Design direction, not automatic dependency adoption:** Deconstruct the user-supplied ten GitHub research/implementation references, plus applicable SymPy, Z3, Hypothesis and NetworkX methods, into explicit behavioral contracts before implementation. Use small typed higher-order functions (apply, partial application, currying, lifting, composition) that construct **inspectable AST expressions** and are independent of individual semantic slugs or letter-grade branches. Reuse tested symbolic/finite-model/constraint/property methods where appropriate; independently rebuild missing mechanisms from those behavioral contracts and source evidence, not from incidental upstream code structure. Original source interpreters and independent oracles remain necessary; a shared Boolean output type does not prove world/grammar compatibility. Retain complete source, repository commit, method, experiment and verification receipts. Before any major new abstraction, show a successful constrained vertical slice with positive and falsifying controls and independent subagent review. Modules should be reorganized only as boundaries prove useful.

**Proof and authority boundaries:** This decision establishes the compositional architecture direction and governed staged research. It does **not** admit new token meanings, legal cross-interpreter operations, a new grade, a general-purpose transformation law, or any untested third-party backend. The pure first slice may bind historical source token indices, type-check callable compositions, enumerate original Boolean truth patterns and produce independent source/SymPy proof receipts. It is not the authoritative final catalog, completed generative curriculum, or evidence of new neural learning. Preserve the student's FP32 weights, native AdamW, teacher state, protected champions, already-admitted grade releases, temporary forgetting/spiral recovery and complete same-checkpoint 100% graduation. Agent-run live training remains prohibited.

**Traceability and continuity:** Protected issue [socr8s/private-ip#336](https://github.com/socr8s/private-ip/issues/336) remains open and controls full acceptance, including dynamic laws and coverage, learning diagnostics and actual teacher-selected delivered instruction. The architecture correction and upstream-reuse sequencing failure are recorded in `PM-2026-10-16-003`, `RC-085`, `RC-086`, `PAT-067`, and `PAT-068`. New work must include the exact source-revision/proof matrix and separate demonstrated behavior from proposed integration.

## ADR-029 | 2026-10-16 | Cohesive module boundaries and typed shared contracts

**Direct user correction and approval:** The user identified a recurring scalability defect: unrelated algebra, source-translation and proof responsibilities accumulating under `bilqis_mlx/composition/`, and machine status values such as `VERIFIED_FINITE_SCOPE` duplicated as literal strings in code and tests. The recent `LawContract` record also stores free-form identity and source-claim strings without demonstrating canonical catalog admission. The user directs us to organize in advance of future scale, learning from donor repository compartmentalization, and to centralize shared vocabulary as enums/constants so refactoring cannot silently desynchronize producers, consumers and tests.

**Decision:** Place each stable responsibility with one owner: semantic identities and law definitions under code-native catalog authority; pure typed expression construction and functional algebra; adapters for historical source semantics; and independent proof, countermodel and coverage methods. Give status/error vocabularies typed, imported definitions, preserving existing serialized values where they are compatibility contracts. A proposed law and a canonically registered law are different states, and a test must verify observed behavior independently of the method's self-declared label. The catalog alone can allocate future semantic IDs; preserve the original 222-token ABI and original lesson identities. Use focused package boundaries rather than creating unused speculative abstractions.

**Execution:** Move existing proven code in small source-checked units, migrate callers and remove obsolete entrypoints in the same tested change; add new packages only as they own real behavior. The module map and import direction live with active architecture references, not the archived speculative drafts. This refines ADR-028 under protected issue #336 without changing actual FP32 student, matching AdamW, learned teacher, historical receipts, or provisional uncommitted Grade B policy. The distinct user correction is filed as `PM-2026-10-16-004`; `RC-087` and `PAT-069` capture typed-contract/module-cohesion requirements and reuse `RC-085`/`PAT-067` for distributed semantic authority.

## ADR-030 | 2026-10-16 | One versioned vocabulary ABI contract, independently checked at merge

**User-confirmed correction:** A repository-wide search found roughly 191 appearances of `222` across source, tests, records and documentation. Repeating the historical model vocabulary count inside independent functions, tests and live operator instructions creates a source-of-truth failure. The approved remediation is to inventory occurrences with read-only subagents; distinguish immutable historical evidence, unrelated values (including random seeds), legacy message IDs and actual executable bounds; centralize model ABI count/identity in one code-owned contract and require dependent modules to import the typed value. Refactoring rules receive evaluation and evidence, not blanket agent authority to suppress them.

**Definition and distinction:** The original complete checkpoint's vocabulary has an immutable historical *prefix*; future approved model vocabulary is append-only and may grow. The historical size is derived from the code-owned versioned ABI manifest, whose source-derived prefix fingerprint records the entire index→(symbol, original semantic identity, meaning-contract digest) mapping, not merely its cardinality. Mutable Sheet row order, display labels, research counts and later training generations cannot redefine this prefix. Runtime heads and token allocations must use the relevant approved **current** catalog/graph size instead of imposing the historical prefix length as a universal maximum. Immutable prior receipts remain legible rather than being rewritten to appear contemporary.

**Independent enforcement:** Build a standard-library semantic ABI checker that recomputes the original-prefix fingerprint from actual snapshot/graph records, compares with the code-owned manifest, and accepts an **independently controlled** expected fingerprint as a CI input. The GitHub Actions workflow is advisory while private GitHub Free branch protection is unavailable; it becomes an enforced merge check only through separately configured public-repo branch protection, authorized variable/control ownership and protected validator review. A same-repository expected-value edit or silently missing external CI expectation is not sufficient to authorize a changed historical meaning. Never infer model training readiness or Grade C admission from passing this guard.

**Scope:** Private feature branch only. Preserve all preexisting dirty Grade B work, original snapshot and model/AdamW, teacher history and artifacts. Do not replace historical numbers in archival publications or source receipts with dynamic configuration values; use named contract references for live normative statements and exact fixed observations in read-only evidence. Execute source-only/synthetic negative tests and keep issue #336 OPEN until generative source closure, five actual longitudinal detectors and human-owned Grade A/B empirical qualification succeed.

## ADR-031 | 2026-10-16 | Classroom qualification lifetimes and practical A/B learning warnings

**Clarification (2026-10-16, governs assessment roles):** The fixed test lifetime here applies to **grade graduation**, not candidate checkpoint promotion. Candidate checkpoint comparisons must draw a fresh source-oracled cohort each boundary and compare challenger and all eligible incumbents on that exact same newly drawn cohort before allocating best-checkpoint roles. Grade graduation alone uses the grade enrollment's unchanged qualification cohort throughout failures and recovery rounds. On reenrollment, a different graduation cohort is generated. The two assessment results are distinct evidence surfaces and must never be substituted for one another. Per-visit teacher reward continues to use measured pre/post teaching performance; changed candidate questions do not erase reinforcement feedback, and only exact paired cohorts can justify challenger-versus-incumbent superiority. Preserve historical scored artifacts and existing learned teacher decisions. This corrects the earlier accidental overextension of the fixed exam to candidate selection.

**User-confirmed grade lifecycle:** The qualifying questions, rubric and graduation criteria belong to one grade enrollment. An unsuccessful examination is followed by instruction and a retry of **exactly the same** examination, however many recovery rounds are necessary. Once the grade is passed, the next visit to that grade starts a freshly generated examination; the A→B→... spiral retains complete same-checkpoint cumulative qualification. Teaching remains varied within every optimizer visit. Previously failed examination questions, including their independently computed gold answers, are legitimate supervised instruction. There is no permanently sealed holdout, and examination scoring inference receives no gold. Never add an exam embargo in the name of generalization.

**Elementary learning before ambitious transfer:** In early admitted A/B, and eventually C, the actual test concerns the prescribed and already taught semantics. Novel many-grade-ahead composition, a complete source-wide theorem prover, and exhaustive New Ithkuil morphology are separate research tasks, not new acceptance gates imposed retroactively on the bounded accepted early-grade course. Continue respecting original semantic IDs, approved source interpreters, intact FP32 student plus native AdamW, and the user's 100% same-checkpoint criterion. A capability's meaning must not silently change between instruction and assessment.

**Five practical warnings:** The original five failure questions are executable observational requirements, not a mandate to record the identity of every delivered instructional specimen before diagnosing anything. S1 tests repeated predictions against actual gold classes. S2 measures poor grades/capabilities against their actual baselines. S3 can compare unchanged qualifying questions scored at successive distinct checkpoints to identify absent, lost or retained measured gains, without claiming causal attribution to individual lessons. S4 uses code-owned prerequisite identities and the semantics visibly present in *delivered* source-valid constructions. S5 compares selected introductory optimizer batches with the simplest **offered and source-valid** examples, not a claim to have solved the global mathematical minimum. Missing/unsupported evidence is `NOT_MEASURED`, not an automatic stop. Distinguish a simple useful warning from independently proven neural learning, complete causal attribution, or user-authorized teacher-policy changes.

**Execution and evidence:** Keep semantic interpretation under the approved catalog/course and source adapters; keep warning statuses in imported typed enums rather than duplicated string labels; persist only compact methodology summaries on the established generation-bound event outbox. A future research ledger may preserve more individual specimen identities, but it cannot become a prerequisite for practical detectors or early-grade instruction. Do not impose assistant-selected old-grade ratios or suppress the inherited learned teacher. The current bounded changes are synthetic/disposable engineering evidence; actual student optimization remains human-owned. See protected issue #336, user correction comment `6215237912`, corrected `PM-2026-10-16-006`, and `docs/evidence/diagnostics/AB_CLASSROOM_DIAGNOSTICS_20261016.md`. Full generic AST curriculum and closed teacher-response/outcome loops remain open under issue #336.


## ADR-032 | 2026-10-16 | Graduation-perfect capability custody independent of candidate best

**User correction:** A whole student that scores 12/12 on an admitted capability during the fixed grade graduation examination must be retained as a capability-perfect witness, even when its score on the separately randomized candidate-comparison examination is lower. The two cohorts are not comparable raw-score ranking surfaces. A single student must still pass its whole grade at 100% to graduate; individual perfect witnesses are not grade graduation or mixed student assembly.

**Implementation:** `graduation_perfect` is a separate rubric-and-capability-keyed whole-model-plus-own-AdamW receipt, bound to the exact fixed graduation cohort. Any 12/12 graduation capability updates its protected pointer. Subsequent imperfect observations never demote the protected witness. Candidate bests continue to use paired challenger/incumbent scores on one fresh random cohort; grade graduation remains fixed for the enrollment. Resume custody verification and bundle retirement explicitly pin the graduation-perfect pointers. There is at most one active retained graduation-perfect witness per rubric/capability and its replacements must themselves score perfectly.

**Evidence and recovery limit:** Read-only historical human run receipts at generation 3828/optimizer step 165720 recorded B.IFF=12/12 on graduation and B.IFF=7/12 on the randomized candidate cohort, while the previous candidate-best pointer was 7/12. The generation-3828 bundle was no longer in the active bundles directory when inspected. This change cannot retroactively restore a pruned bundle; it protects new complete checkpoints after the human restarts the trainer. No agent-run neural optimizer updates are allowed. Protected issue #336 remains open.


## ADR-033 | 2026-10-16 | Breadth-ranked perfect champions and bounded student confidence guidance

**User supersession of ADR-032 tie replacement:** A capability can be represented by exactly one active whole-student+own-AdamW 12/12 champion for a given rubric. Of all whole-student checkpoints perfect on capability `c`, choose the one with the most simultaneously 12/12 capabilities on **that same complete scored exam**. A new checkpoint must remain 12/12 on `c` and have **strictly greater mastery breadth** to displace the incumbent; equal breadth keeps the incumbent. One checkpoint may hold many capability roles. If A.3-only loses to A.3+A.5, retire the former checkpoint when no longer active or otherwise pinned. If a subsequent A.5+A.7+A.11 checkpoint drops A.3, it gains those three roles while A.3 remains on the two-capability checkpoint. A later A.3+two-others checkpoint may beat A.3's incumbent. Only retire unreferenced complete bundles after durable state publication under the exclusive human-run operator lock.

**Saved evidence migration:** Historical `graduation_perfect` receipts lack source checkpoint breadth. Derive `breadth` and `perfect_capabilities` from the original immutable scored-exam event for the exact (rubric, cohort, whole-student SHA). Reject missing, conflicting or nonperfect provenance; never invent a count from the number of still-held roles and never rewrite old event/state/model bytes. On 2026-10-16 the read-only human run at generation 4653 / optimizer step 176280 had eight perfect-role pointers, including checkpoints with three original perfect scores despite retaining one role. Rehydration happens in memory upon human resume and persists with the next new generation.

**Learning contract:** Each *distinct*, frozen, current-grade graduation-perfect whole student gets a small confidence vote on **source-gold-agreeing** teaching examples, weighted proportional to its proven simultaneous breadth. Advisory influence in the supervised binary gradient is at most 0.08 per row and is additionally scaled by the inherited learned teacher's selected `distill` dimension; it neither replaces learned teacher strategy nor changes oracle labels, test inference, class decisions, teacher reward, model/optimizer lineage or fixed graduation scores. Gold-disagreeing champions do not reinforce wrong predictions. Raw student-only examinations remain the promotion authority. `champion_confidence.py` owns the policy and math; `grade_a_trainer.py` validates/pins the original frozen bundles and publishes versioned teacher-visit evidence. This is supervised confidence-shaping, **not a live answer ensemble** and not weight soup. The 0.08 engineering cap is provisional and must be calibrated against actual human-run learning. Typed nonbinary champion advice is not admitted; existing typed training is unchanged.

**Pre-MLX evidence, not asserted parity:** `bilqis_school/run_local_champions_v15.py` had an equal-logit prediction ensemble solely for research evaluation, never a causal student. The pre-MLX `engine.py::_train` did include gold-agreeing frozen consensus KL and teacher-policy distillation; these are the source-grounded analog for this explicit new confidence guidance. `capability_champion_policy_vnext.py` was a nontraining proposal that favored grade-average on perfect ties, not this newer user-specified mastery-breadth rule.

**Proof / ownership:** Dedicated strict-breadth test reproduced the previous missing-`breadth` failure before the fix; toy MLX gradient/advice tests and unchanged unassisted exam API prove the mechanical boundary. Full synthetic suite, source/ABI integrity and dry-run resume are only software assurance. Actual student convergence, retention, calibrated confidence and A+B 144/144 remain human-owned empirical gates. Protected IPR-0220 issue #336 remains OPEN; immediate incident PM-2026-10-16-007 (RC-089, PAT-072) records the omitted contract.


## ADR-034 | 2026-10-16 | Immediate frozen grade soups and grade-relative voting

**User-authorized extension of ADR-033:** At each committed grade examination, recompute the selected whole-student 12/12 champion map. For each grade, if the count of capability championship roles is a new coverage maximum, immediately materialize a **frozen, weights-only** soup from those grade champions. Rebuild also when a capability incumbent is unseated, even when the total role count is unchanged. If neither the role roster nor covered-capability maximum has changed, reuse the exact existing soup file and vote entitlement, with no new soup. Do not modify/replace the single causal student, its own AdamW, source/oracle, or original champion weights; optimizer moments must never be averaged.

**Recipe and voting:** Every mastered capability contributes one vote and one ingredient share; multiple capability roles held by the **same** checkpoint count multiple times in the FP32 weighted parameter mean. A grade-A soup formed with 7/12 covered capabilities therefore has immutable `vote_count=7`. When advising grade-A examples, its effective vote count is 7. When advising a different grade while the school has A/B/C, effective count is `7/3` (approximately 2.33). Only the foreign-grade denominator reflects the current admitted number of school grades; recipe, source weights and *base* votes remain unchanged until a new champion displaces an incumbent or coverage increases. Other same-grade capability champions retain their distinct source-gated votes per ADR-033. The soup votes enter the same teacher-policy-scaled, source-gold-agreeing, bounded **training-confidence** target, not candidate or graduation scoring. This reuses the user's prior explicit meaning of champion confidence guidance; test inference remains the current student alone.

**Durability:** Materialize each recipe under an immutable content-identified `.safetensors` artifact before the generation-bound outbox receipt is published. Save recipe identities, per-capability role ownership, per-checkpoint vote multiplicity, whole-model blob hash, token count and source graph metadata in that same committed state. Read back exact tensors, and verify source model, SHA and optimizer-step identity before averaging. The grading visit and champion retirement remain ordered by existing operator lock, with no orphaned uncommitted soup promoted. Keep the active soup and the immediately preceding recipe per grade for rollback, pruning only recognized unreferenced soup files after durable publication; never delete unknown files. Validate all active receipts on resume.

**Evidence and scope:** `grade_soup.py` owns the immutable recipe, vote and model-averaging contracts, while `grade_a_trainer.py` orchestrates the human-owned exam boundary, confidence inputs, storage and delivery outbox. Disposable regression tests cover role multiplicity, one-grade/three-grade scoped voting, unchanged frozen soup across repeated examinations, equal-coverage incumbent replacement, atomic/no-overwrite storage, hash drift, native MLX averaged values, safe retirement and full Grade B source-scored lifecycle. The 8% confidence influence cap inherited from ADR-033 remains a provisional engineering setting, **not** measured evidence of neural learning or the optimum calibration. Only the human starts/resumes real training. Protected issue #336 stays OPEN until empirical cumulative A+B 144/144 and other source/diagnostic gates are observed.


## ADR-035 | 2026-10-16 | Only grade soups advise across grade boundaries

**Latest user clarification, superseding prior-grade direct checkpoint votes:** Individual 12/12 capability champions may influence supervised answer confidence only for examples in their **own** grade. Frozen grade soups alone cross grade boundaries. A soup's recipe and base capability vote count remain immutable between qualifying champion replacements; a soup advising its own grade retains its entire base count, and a soup advising another grade has base votes divided by the total current count of admitted school grades. For the frozen A soup with seven mastered capabilities and three admitted grades, A lessons receive seven effective votes and B/C lessons receive 7/3. Do not introduce dynamic per-grade capability populations, prerequisite DAG connectivity, or dependency-specific vote weights now. That is a separate future model and human decision.

**Observed implementation conflict:** `champion_roster(receipt['graduation_perfect'], lesson_grade)` already constrains direct capability confidence advisers correctly. `_frozen_grade_soup_votes(..., lesson_grade, len(course.grades))` already spans grades using the correct simple divisor. But the older graduated-grade checkpoint mechanism `_champion_teacher_votes()` and `champion_directed_lessons()` could still **replace source-valid teaching examples** in another grade based on old checkpoint mispredictions. Although this was not direct examination-answer voting, it was an independent cross-grade instructional intervention. That path is retired from the active trainer, superseding historical ADR-001/ADR-025's inherited per-grade checkpoint-nomination votes. The pure historical `school.teacher_vote_weights` and `champions.vote_counts` calculations remain as read-only legacy state helpers; the live MLX trainer no longer calls them for selecting lessons. Existing immutable event history is untouched; new visit events maintain empty legacy `prior_grade_champion_votes` and `champion_directed_examples_available` fields for event schema continuity.

**Preserved boundaries and proof:** The adaptive teacher still chooses its own lesson strategy and distillation strength; source-gold supervision and unassisted student-only candidate/graduation scoring are unchanged. Same-grade direct capability champions remain breadth-weighted, while frozen cross-grade soups remain source-gold-gated, 8%-capped collectively with direct confidence advice, and weight model parameters only without optimizer mixing. Disposable regression first reproduced the old call and nonempty prior-grade votes; updated tests assert that old checkpoint loaders are not consulted for this intervention and that only A's soup, reduced to 7/3, reaches B confidence guidance. Do not mutate or restart a running human student. Further source graph/dependency-based weighting is deferred. Protected IPR-0220 issue #336 remains OPEN.

## ADR-036 | 2026-10-17 | Evergreen grade selection must challenge the proposed sequence

The user's original ten questions and correction are preserved in protected IPR-0220 issue #336 comment 6233567989. Their exact wording governs over earlier assistant summaries. The historical spreadsheet supplies candidate subjects and evidence, not an automatic teaching order. Every new grade must compare alternatives, justify immediate usefulness to a text-only learner, distinguish neural requirements from deterministic codecs, verify or stage all prerequisites, identify the smallest defensible complexity increase, and name near-term and downstream capabilities unlocked. New observations must trigger renewed comparison. Historical D phonology is not selected.

`bilqis_mlx.next_grade_review` and the evolving per-grade dossiers provide a reusable Q01-Q10 structural evidence check at selection, construction, admission, operation and retrospective. Grade C's actual admission now requires the admission-phase review in addition to its source and student safeguards. The checker does not establish substantive source truth or independent approval. The broader generative factory, learning-health policies, and future Grade D are not thereby implemented. Historical A/B state and the human-only neural training rule remain unchanged.

## ADR-037 | 2026-10-17 | Separate intrinsic semantic identity from contextual interpretation

**User clarification:** The original three pure-function description was an inadequate division of labor, not an exhaustive mandatory per-primitive interface. The protected verbatim source is IPR-0220 issue #336 comment `6234081376`, which supersedes the unconfirmed interpretation in the 2026-10-17 evergreen RFC. **Identification** means a primitive's positive, source-grounded meaning and behavior in terms of already established semantic prerequisites (or an explicit irreducible foundation), not a post-disambiguation catalog lookup or a list of other meanings it excludes. **Association** means candidate applicability retrieval from ambiguous inputs; **disambiguation** uses increasingly informative context to resolve the candidates while preserving uncertainty. Interpretation compares candidates outside their intrinsic definitions.

**Current-stage decision boundary:** Mathematics-first curriculum work does not require premature contextual-language implementations. The user has left open whether later association/disambiguation/identification instrumentation begins optional or minimally scaffolded. For now, preserve the existing canonical catalog/typed AST and independent tests, and require each future grade selection to consider the named non-exhaustive function families, explain deferral/foundational preparation, and name later prerequisites or unlocks. Grade review schema `bilqis.next-grade-review/v2` adds `semantic_function_families` with `DEFERRED`, `FOUNDATIONAL`, or `REQUIRES_QUALIFIED_IMPLEMENTATION` and includes it in review invalidation. The last disposition cannot be self-qualified through strings and remains blocked pending a separate executable qualification gate. These dispositions do not assert mastery, implement natural-language interpretation, alter the student's training, or select Grade D.


## ADR-038 | 2026-10-17 | Exact source receipts and independently checked factory candidates

The authorized evergreen implementation under protected [issue #336](https://github.com/socr8s/private-ip/issues/336) extends the existing semantic AST and verification owners. Review v3 requires an independently supplied manifest fingerprint binding exact source artifacts, parent/semantic release, claim scope and checker implementation. Retrospective outcome changes preserve earlier phase scope. These checks validate externally supplied attestations; the checker cannot establish source truth, reviewer independence or approval by assigning itself a status.

The bounded Boolean factory enumerates declared finite constructions before seeded sampling, reports missing closed-domain values and incomplete coverage, orders prerequisite stages, and verifies constituent/whole gold. Generic offline readiness additionally checks canonical roots including the outer operator, supported answer families, AST and coverage invariants, independently attested cumulative scores and checkpoint-bound prior-stage mastery. Conceptual/type `requires` are distinct from executable `composed_of` witness obligations. Source-only readiness never grows a model, writes a checkpoint, admits a grade or authorizes neural work. Wider answer types and generic runtime cutover remain unfinished.

Health/quarantine, paired candidate-retention and teacher-credit experiments remain unratified shadow observations. Alert receipts bind source/exam lineage and ordered checkpoint identities; repeated states are batched without dropping required mastery debt. Missing historical lineage yields visible gaps or `NOT_MEASURED`. The static import guard rejects explicit live wiring of shadow modules. Experiments do not alter the inherited teacher, candidate acceptance or saved student. The [acceptance report](docs/evidence/development/EVERGREEN_FACTORY_ACCEPTANCE_20261017.md) records tests, historical replay, custody and remaining gates. `PM-2026-10-17-003` was enriched with native readback; previous composition and teacher-boundary incidents remain applicable. C stays source-blocked and D unselected.

## ADR-039 | 2026-10-17 | Untested contract scaffolding and explicit qualification handoff

The human requested contract/scaffolding progress without running tests, preserving scarce current quota for a full handoff to the other machine. This authorized engineering draft adds opt-in finite-domain/answer declarations, existing-template construction-family planning, finite witness methods, a disposable cutover action plan and observational selection comparisons. It changes no live trainer, registered semantics, historical token ABI or student/teacher state. Decimal-text proposals preserve the existing Number wire representation; native mappings remain declarations requiring authentic catalog reconciliation.

These modules are unfinished, unexecuted and unwired. Source hashes, family dispositions, cutover observations and Pareto outcomes confer no approval or policy authority. Existing verification results end at baseline `a28b5f5`; the [WIP guide](docs/history/architecture/EVERGREEN_CONTRACTS_WIP_20261017.md) and current handoff carry the receiving agent's source review, focused negative controls, disposable custody work and unresolved boundaries. No tests or CI should be inferred from this draft checkpoint. C remains blocked, D unselected, and actual neural continuation human-only under protected [issue #336](https://github.com/socr8s/private-ip/issues/336), OPEN.


## ADR-040 | 2026-10-17 | Mechanical contract qualification preserves source and execution gates

The receiving-agent pass under protected [issue #336](https://github.com/socr8s/private-ip/issues/336), OPEN, tests and repairs ADR-039's previously unexecuted drafts. Domain hashes support nested immutable mappings; malformed identities and native maps fail explicitly. Construction plans bind executable templates and expose missing intermediate domains. Witness checks validate every input/intermediate/final scope, reconcile declared native identities against an actual supplied catalog, and retain complete transformation cohorts plus observed nondeterminism failures. Executable-law attestation remains required; finite agreement does not discharge source or family debt.

The opt-in `verification.curriculum.inspect_construction_contracts` composes the existing Boolean package checker and new contract witnesses. Its reports cannot grant source qualification or training authority. The external review fingerprint now covers the additional executing checker owners. Existing approved A/B releases and historical token meanings are unchanged.

Temporary toy-model tests exercise unchanged vocabulary, append-only growth, FP32/own-AdamW readback, the actual 100 GiB reserve, interrupted generation-pointer publication and lost event acknowledgement through the existing checkpoint/outbox owners. They do not implement a generic runtime admission executor. The planner now requires fresh readback even for a reported committed cutover. Selection remains an unqualified observational frontier with missing metrics and negative transfer preserved. The exact source/test/custody receipt is `docs/evidence/development/EVERGREEN_CONTRACT_QUALIFICATION_20261017.json`; authentic source packages, generic runtime cutover and empirical learning remain separate gates. No actual student or teacher updates are authorized.


## ADR-041 | 2026-10-17 | Prototype-first trials before research qualification

The user explicitly rejects publication-level rigor as a prerequisite for proof-of-concept progress: one person working at home on $50/month needs to try novel learning and self-optimization strategies cheaply. The immediate loop is **build a small working experiment → run a bounded trial → inspect learning/retention → keep, revise or discard**. Reuse current semantic, generation, training and checkpoint components. Basic correct answers, useful observations and recoverability are sufficient for exploratory progress.

Defer causal attribution, independent outcome attestations, matched research baselines, exhaustive transformation/family verification, externally reviewed source manifests, elaborate reporting and completion of the generic cutover executor until a concrete experiment needs them or a promising result merits further investigation. Earlier assistant-authored qualification-first instructions in ADR-038 through ADR-040 and their handoffs no longer govern exploratory trials. The user's ten questions remain design considerations, scaled to the experiment rather than a repeated research dossier. A short trial observation can justify the next iteration without establishing why it worked.

Preserve stable token meanings, correct source-backed gold for the chosen slice, original artifacts, the complete actual student and own AdamW, teacher ownership, disk protection and human-only actual training. Agent-run learning uses isolated disposable models. This decision changes development priorities and guidance; it does not bypass executable admission checks or admit C. Existing qualification machinery may remain unused. Next: generate one small curriculum through the existing AST path and run a cheap disposable trial with simple scoring and an earlier-skill retention check. No generic runtime cutover framework is required first. Authority: the user's latest correction in this chat, preserved in protected IPR-0220 issue #336; existing incident PM-2026-10-17-003 remains the related record.


## ADR-042 | 2026-10-17 | Human Grade C pilot through existing runtime owners

The human directs: “Fail fast. Thin vertical slices. Incorporate feedback. Save deconstruction for after,” then authorizes C catalog integration, removal of the research-review prerequisite, and a disposable resume check. C's existing staged numeric course is available for a short human trial once source/correctness/custody checks pass; the external-review dossier remains an optional planning tool.

Append five already-defined formal numeric/syntax tokens to the native Curriculum Registry, retain all 222 historical rows and identities, and package the actual readback. Reconcile columns by header, and preserve historical rows' original graph provenance during append-only growth. Keep complete cumulative A+B, source-oracle, full-vocabulary numeric output, own-AdamW, disk and checkpoint guards. Reuse `historical_live_release` for the exact trained A/B seal; the C receipt retains its parent course digest so later C resumes choose the same ancestors.

The actual-run source preflight has no blockers at integer maximum 10. A disposable copy admitted C at step 204072 with no optimizer updates, recovered a simulated state-pointer crash, and resumed repeatedly with one C event, unchanged prior tensors/moments, teacher, champions and soups. All five recorded actual-run file hashes remain unchanged. The saved experiment JSON records this check. Only the human starts actual C updates; this decision reports operational pilot readiness, not C mastery. Protected issue #336 remains OPEN; related PM-2026-10-17-003 was enriched and natively read back.


## ADR-043 | 2026-10-17 | Preferred numeric experiment separates operation and domain growth

The user proposes a smaller numeric staircase for future experiments: teach COUNT, NUMBER, SUCCESSOR, ADD and SUB first; increase the active integer semantics one at a time, mastering the expanded set after each addition, perhaps through 0..6 inclusive. Include division-by-zero boundary tests or an explicit undefined arithmetic outcome. Then introduce MUL and exact DIV within that small domain before trying either individual additions 7..10 or a batch expansion, optionally comparing both. The starting integer bound and optional comparison are not fixed decisions. The intended benefit is cheaper, more informative feedback when one semantic addition expands the construction space; that benefit remains to be tried.

This is a recorded design preference, not an instruction to rewrite the running C release. Current human C keeps its pinned 0..10 scope and staged seven-capability course. Its existing numeral identities 0..100 are already allocated, so incremental teaching need not allocate new tokens or grow the model. A genuinely new token currently adds one tied input/output embedding row; transformer width and depth remain fixed. Current symbolic exact division rejects zero divisors; teaching the neural model to report an undefined outcome is additional work, distinct from labeling an arithmetic error as logical contradiction. Preserve historical token meanings and the human-run boundary when implementing the next thin experiment.


## ADR-044 — Warm-start the user's 0..3 → 0..6 numeric staircase

The user explicitly requests pausing the current C run, keeping the latest complete student and own AdamW, and changing the order and scope of tests. The confirmed starting bound is 0..3. This supersedes ADR-043's disposition that the preference is only for a future experiment.

The opt-in `--resume --numeric-staircase` releases `bilqis.mlx.numeric-staircase/20261017-v1`. Reuse the admitted C source AST, numeric generator and native checkpoint/generation/outbox owners. Introduce COUNT, NUMBER, SUCCESSOR, ADD and SUB separately at 0..3. Require all five perfect at one current checkpoint before increasing the bound individually to 4, 5 and 6; each expansion teaches and reassesses those five. Introduce MUL and DIV only at 0..6, then use the existing A→B→C cumulative replay. Stop this experiment at 6. The teacher selects its existing strategies and prior-grade recovery remains active.

Enrollment and scope changes preserve the exact weights, optimizer, teacher, champions, soups and token catalog. Pin the pre-staircase complete checkpoint, retain each prior enrollment's immutable state, clear its active exam and start a fresh exam epoch at each scope. Keep each exam fixed within its scope. Retain wider unresolved mistakes without offering them in narrower lessons. Existing numeral embedding rows remain allocated and model size stays fixed. Symbolic 0/0 and nonzero/0 tests reject undefined exact division; a neural undefined-answer primitive is deferred.

The actual trainer had already exited when the pause operation checked its PID; no signal or agent-owned neural update was performed. The observed paused state is generation 7081, optimizer step 206968, complete student `f8d179c673eb04c9b79524a09fd6611c53a771155360007314c28e4898345470`. A disposable APFS copy passed interrupted enrollment and repeated resume with all parameters/moments identical and actual saved-file hashes unchanged. Disposable toy transitions exercise the entire scope sequence with source-gold predictions mocked only for transition testing, not as learned mastery. See `docs/evidence/experiments/20261017-numeric-staircase-resume.json`. Human learning under this staircase is the next observation.


## ADR-045 | 2026-10-17 | Consolidate human-operated training into one self-contained MLX repository

The user expressly supersedes the scattered worktree operation model. `~/Code/bilqis-mlx` is the single new runtime and source-development checkout. Pin and vendor the exact historical oracle, teacher and old-bootstrap inputs in an out-of-the-way internal `vendor/legacy-v16/`, without allowing implicit sibling repository dependencies. Keep the source manifest and historical SHA checks as integrity proof, not an obligation to continue work in the old repository. Historical checkpoint files stay ignored by Git.

Preserve the latest actual full student, its matching native AdamW and teacher/champion/soup/generation/event/curriculum evidence as the current ignored `runs/school-mlx-v1/` lineage. Copy and verify every file before changing the active pointer; preserve the former state as an ignored, recoverable archive. Future checkpoint storage is configurable, subject to strict safe path ownership, automatic bounded retirement of genuinely unreferenced bundles, and lossless independently verified archival of older metadata. An external backup must be selected and SHA-verified before any unique historical state is deleted; moving historical material to a different folder on the same volume does not free disk space.

Use a concise root README, append-only ADRs, protected historical documentation, conventional commit subjects, a shared npm/Python SemVer, `CHANGELOG.md`, the former code-smell baseline mechanism adapted to this codebase, a portable non-neural GitHub Actions verification job, and immutable annotated private release tags. The desired initial consolidated tag is `v0.2.0`; do not claim it was published until its exact remote Git ref and release are read back. Reintroducing unverified network expansion, restarting student/AdamW from scratch, or training in CI are prohibited. This decision does not infer neural mastery from a code release.


## ADR-046 | 2026-10-17 | Candidate promotion requires measured target improvement

The human operator requires **strictly positive improvement on the active capability's source-oracled parent-versus-candidate probe** before any trial student's weights and matching AdamW may be promoted. Zero or negative target gain means rejection in MAIN and both recovery phases, even when other sampled skills improve. The teacher must still record the measured rejected outcome and learn from it through the contextual channel; historical scalar rewards do not acquire a new meaning. A rejected optimizer trial must never replace the whole live student or its own AdamW.

The candidate safety budget for previously graduated grades is the mature budget in every scheduler phase. A C MAIN pass does not turn graduated A/B capabilities back into developmental skills. Controlled introduction-stage regression budgets remain available only to ungraduated capabilities; source-valid full-school examinations and graduation remain independent. Target probes draw fresh source-oracled questions in a bounded panel based on the capability's current same-scope exam count where available, while cross-capability sentinels retain their inexpensive fixed size. Trial-probe improvement is candidate admission evidence, **not** a claim of durable graduation.

Verification owner: `tests/test_learning_experiment.py` and `tests/test_causal_teacher_integration.py`. This decision updates no historical student/checkpoint and does not authorize agent-initiated neural training.


## ADR-047 | 2026-10-17 | Cumulative weakness scheduling and ratcheting whole-student strain references

The scheduler ranks up to three nonperfect capabilities over the cumulative admitted assessment pool, including earlier grades. Never fill the recovery quota with perfect skills. Avoid fruitless MAIN optimizer trials when source-oracled target evidence is already perfect, without removing cumulative assessments or allowing training to count as graduation. Preserve exam-scope identity and revalidation stages.

For lightweight matrix-wise movement diagnostics, pin the intact checkpoint at the beginning of the selected curriculum epoch as an immutable low/start reference. The high reference is the **best complete student** under the existing `whole_student_retention.advance_peaks` same-scope score authority. Promote this reference only when a newly evaluated whole-student champion strictly improves the cumulative same-cohort, same-rubric all-grades score. Do not promote it on a tie, one-grade soup refresh, or a locally accepted teaching trial. Candidate geometry compares parent and challenger against the references frozen before that transaction; tensor/vocabulary mismatch is explicitly not measured, never silently aligned. The strain result is initially advisory, not a hard rejection rule, and it neither modifies student nor native AdamW. The human alone resumes actual training.


## ADR-048 | 2026-10-17 | Make protected candidate retention the standard training mode

The human operator approved replacing the `--experimental-retention` opt-in with default-on parent/challenger retention. Ordinary human training, resumes and dry-run preflights should use the existing settings and preserve the complete student and its matching native AdamW. Omission of a flag must never silently revert to the unprotected teaching path. An explicit `--no-retention` escape hatch remains available only for separately rooted, deliberate legacy/control experiments; protected saved lineages reject opt-out before any neural or durable resume activity. Policy adjustments on protected resumes remain subject to existing fail-closed tightening rules. The CLI, generated resume instructions, current README, agent rules and regression fixtures must describe the new default, while preserving historical experimental documents as dated provenance. This is an operational-default promotion supported by working mechanisms, not evidence of cumulative neural graduation.


## ADR-049 | 2026-10-17 | Prevent known Grade B composition regression during candidate admission

The actual human-school examination showed that accepted C instruction can flip previously correct B.OR/B.XOR relational cases despite a zero-loss rotating protection panel. Retain the existing strict target-gain gate and sample-budget safeguards. Add one bounded, source-oracled guard over the 12 OR and 12 XOR examples already materialized in the latest fixed cumulative cohort, when both are admitted and available. Require that no previously correct anchored answer becomes wrong; newly fixed answers are welcome, but cannot cancel an individual regression. This guard rejects only the candidate model and its AdamW, not the teacher's opportunity to learn from the attempt. Keep the cohort SHA and item IDs in candidate evidence. No additional entire-school inference, checkpoint rewrites, new neural experiment, or agent-operated training. Label dashboard instructional percentages as **LESSON%** so they cannot be mistaken for full-cohort results. This protection is targeted, not proof against failures on unmeasured constructions.


## ADR-050 | 2026-10-17 | Distinct-checkpoint longitudinal diagnostics without erasing exam evidence

Repeated source-verified whole-student exams can legitimately occur at an unchanged optimizer step and identical model-and-own-AdamW checkpoint, especially when candidate admission rejects attempted lessons. Every event, immutable state, source cohort and outbox receipt still requires independent validation and remains individually represented in the raw audit. Deduplicate identical checkpoint identities **only for comparable longitudinal diagnostic analysis**, retaining the latest verified exam for that identity/scope. Do not promote repeated examinations to independent evidence of durable learning. Keep backwards optimizer steps and conflicting model identities at the same step as hard evidence errors. Preserve strict direct `diagnose_history` checks for callers that supply unnormalized trajectories. When optional history analysis fails, show its concrete diagnostic error alongside the unavailable S3 signal instead of suggesting longitudinal health has been measured. No changes to the student, teacher, AdamW, qualification or human-only training authority.

Because recovered S3 measurements can now be observed, do not mark a capability with a perfect initial and perfect latest score as "lack of durable gain" merely because improvement above 100% is impossible. Preserve warnings when a formerly perfect capability actually regresses or when a previously imperfect capability fails to retain improvement. Cache previously verified immutable exam receipts inside the running observer, invalidating on altered source files or a changed ledger prefix; the separate forensic audit still performs full source revalidation each run.


## ADR-051 | 2026-10-17 | Rejected candidate feedback must reach the primary strategy selector

With protected retention, a rejected candidate correctly leaves student and native AdamW unchanged. The trainer previously also forced the instructional accuracy delta to zero and passed that zero into the inherited strategy-selection bandit, even when the separate contextual teacher had already scored the failed candidate negatively. This made the primary grade/global strategy statistics unable to distinguish unsuccessful from harmless attempts, leaving the same failed policies eligible for repeated selection. Feed the existing source-oracled contextual credit to the primary bandit's existing `observe` method on protected attempts, preserving its exploration and avoiding any new policy bank, rejection gate or retrospective reward rewrite. Keep legacy no-retention scoring unchanged and record selection credit separately from retained instructional accuracy. This forward-only correction must not alter checkpoint, teacher history, native AdamW, or human-only neural training custody.


## ADR-052 | 2026-10-17 | Graduation resets champion geometry; cross-origin takeover requires cumulative superiority

The user corrected two repeated misinterpretations of champion succession. First, **only after graduation and admission of expanded curriculum semantics** do we reset every old active championship reference to the one graduating complete student as a new geometry baseline. Old champion and soup evidence remains archived, but cannot keep shaping training by default. This is a replacement of all active championship references, **not** proportional baseline weighting or gradual phase-out. The admission event must preserve the causal student and matching AdamW. A new unmastered capability cannot be declared champion merely because a baseline exists.

Second, a checkpoint from another grade can only contend for a grade's championship **after earning 100% on every capability of that target grade**. It must also score **strictly higher across the complete cumulative school** than each incumbent checkpoint it would replace, with all candidates and incumbents evaluated on the same current source-oracled cohort, rubric, graph and school scope. An aggregate tie, partial grade perfection or incomparable source cohort cannot transfer the roles. A saturated perfect grade may be superseded through the stricter cumulative-performance rule even where breadth cannot grow beyond the grade's total capability count. Per-capability rank from ADR-033 still governs other compatible within-grade succession. Every legitimate change in active role ownership refreshes the affected frozen soup, with vote multiplicity preserved and no model/AdamW substitution.

**Canonical rule and conformance suite:** `docs/specifications/0002_CHAMPIONSHIP_LIFECYCLE_V1.md`. This accepted specification supersedes contrary clauses in ADR-033 through ADR-035 and older AGENTS text, while preserving those documents as historical evidence. Implementation, integration and a human learning trial require separate verified results. No agent may launch the real optimizer.


## ADR-053 | 2026-10-17 | Empty championship roster, no baseline mentor, preserve student lineage

The user refined ADR-052's championship reset because stale champions, including a fallback graduation-baseline checkpoint, can give bad neural guidance. The correct **active** starting condition is **zero championship titles, zero vote-bearing grade soups and zero baseline adviser models**. The graduation-derived checkpoint remains immutable evidence for provenance/retention, never a privileged unearned teaching model. All older champion, soup, grade-graduation and source-score records remain archived and custody-protected; "wipe" means **withdraw eligibility and advice**, not erase trained student parameters, native AdamW or historical evidence.

On explicit human request, the existing isolated #340 mid-Grade-C trial can receive a **one-time, generation-bound, operator-locked, metadata-only administrative championship reset**. It must archive the trial's already-earned active roles/soups, retain the current student and its own AdamW at the actual last committed step, and admit fresh championship contenders only from strictly later optimizer steps. Normal grade admission resets to the same empty roster automatically after intact whole-school graduation, but ordinary resumes and weaker training attempts do not cause repeated resets. The first perfect entire-target-grade checkpoint may earn uncontested roles when there are no active incumbents; subsequent cross-origin replacements still require perfect target-grade mastery **and strictly superior comparable whole-school performance against every displaced incumbent**. Same-grade breadth ranking continues to govern compatible role succession. Only post-reset earned champions/soups advise in training. No model copy, rollback, archive deletion, arbitrary teacher-policy override, or agent-run neural updates.

**Current normative contract:** `docs/specifications/0002_CHAMPIONSHIP_LIFECYCLE_V1.md` as amended for zero-active-champion initialization. ADR-052's description of reassigning all active roles to the graduation baseline is historical and superseded by this ADR.


## ADR-054 | 2026-10-17 | Never retain a targeted gain at a larger same-grade cost

The human observed a B-grade update retained despite one capability gain and greater measured losses in two other B capabilities. The exact generation-11566 paired candidate receipt confirms B.XOR +1, B.IFF -1 and B.IMPLIES -1 (Grade B net -1), with 16 optimizer steps retained. The former target-only positive-gain condition, individually tolerated protected losses and B.OR/XOR fixed-replay guard all passed because the recorded protected aggregate did not govern admission. Independent whole-grade exams also document declines between retained checkpoint identities.

Candidate retention now requires complete fresh same-grade paired capability coverage, strictly positive aggregate same-grade correct-answer gain, and a nonregressing complete current-grade fixed-cohort screen whenever that source-bound exam belongs to the same grade and grade-test epoch. Existing cross-grade tolerances and the OR/XOR per-item replay remain separate stricter gates. Do not compare different cohorts or mistake a missing fixed test for an observed pass. Reuse persisted exam rows and model inference where possible; a rejected in-RAM candidate and its native trial AdamW never replace the parent. Preserve earlier student history and feed measured rejection evidence to the existing teacher.

Normative contract: docs/specifications/0003_CANDIDATE_RETENTION_GRADE_NET_V1.md. This is a forward-only change for the existing private human-training fork, without new full-model cloning or agent-run neural updates.


## ADR-055 | 2026-10-17 | Checkpoint-bound, staged grade qualification; atomic external-grade takeover

The user clarified that the corrections in ADR-054 and the championship lifecycle are **not** an instruction to examine every school capability on every provisional candidate. Qualification must be staged and scoped to the grade under consideration.

For provisional student admission, run the candidate's own target probe first. A failed target causes immediate rejection, without unnecessary inference on the other grade capabilities or fixed grade exam. Only after a positive target result may the candidate proceed to scoring **previously unscored peers in its own currently admitted grade**, using the same candidate checkpoint/optimizer step and source-bound paired question set. Reuse valid existing scores on that exact candidate and cohort; do not rescore them or borrow another checkpoint's results. A strictly positive same-grade aggregate and nonregressing matching fixed-grade examination remain necessary for retention. The cross-grade sentinels remain selectively bounded and do not grow with the entire school.

For championships, even a single same-origin perfect-capability title requires complete scoring of **all capabilities in that contender's own grade** on the same intact checkpoint. Missing or not-yet-admitted evidence defers the title, not a partial grant. For a champion proposing to invade another grade, first complete the **entire destination grade** on the checkpoint (only missing grade tests need evaluation). If any target-grade capability is less than perfect or lacks valid evidence, the challenger takes **zero** destination-grade titles. If the whole external grade is perfect, it can take **all** target-grade roles atomically; if there are actual incumbents to displace, it must additionally score strictly higher on a source-comparable **whole-school cumulative exam** than every incumbent. A vacant external grade needs no synthetic incumbent or gratuitous whole-school takeover replay. Candidate or school scores from different model/cohort identities can never be spliced into a championship.

Do not conflate this bounded championship proof with ordinary scheduled independent cumulative school examinations needed for graduation. Preserve the teacher, student, FP32 parameters, native AdamW, history and zero-baseline championship policy. Neither the assistant nor a source-only test starts real neural optimizer updates.

Normative contracts: docs/specifications/0003_CANDIDATE_RETENTION_GRADE_NET_V1.md and docs/specifications/0002_CHAMPIONSHIP_LIFECYCLE_V1.md, refined in place; ADR-054's eager testing interpretation is superseded here without discarding the earlier reproduced regression evidence.


## ADR-056 | 2026-10-18 | Rehearse fragile semantics before admission; reuse unchanged exams; rebase #340 on best-8355

The first human run after ADR-054/055 attempted **322** protected visits and retained **zero** optimizer updates. Of 131 target-improving trials, 84 also achieved a strictly positive fresh same-grade net, but every one of those 84 lost the same previously-correct B.OR fixed-exam item; the run recorded 148 B.OR item regressions versus 10 B.XOR regressions. This persisted down to learning rate 0.00004. The safety gate therefore exposed a candidate-construction problem rather than permission to weaken retention.

When a verified current fixed exam contains B.OR and B.XOR, every protected optimizer batch now reserves source-oracled **fresh semantic siblings** covering all four Boolean operand truth patterns for each admitted fragile connective. The fixed admission questions themselves remain excluded from lesson material. Exact unresolved exam misses keep their reserved batch slots. The existing 24-row fixed replay remains an independent post-training admission veto, so rehearsal cannot turn the referee's questions into homework.

The same failed run also scheduled 88 whole-school exams while the retained model SHA and native AdamW step never changed. A scheduled exam boundary may now reuse the already verified result only when checkpoint SHA, optimizer step, fixed cohort, rubric, school scope and semantic graph are identical and every pending visit retained zero optimizer updates. Stored wrong-answer predictions reconstruct and revalidate the exact prior score and miss set. A reuse advances scheduler and teacher bookkeeping but performs no new model inference, candidate-cohort scoring, capability-incumbent replay, championship minting or soup refresh. Any retained update or identity mismatch restores the ordinary full exam path.

At the user's direction, isolated run `runs/issue-340-mentor-epoch-trial` is rebased to the experiment-local, inode-distinct clone of canonical checkpoint `best-8355-a03fa6317bd4`, SHA `cda606f9b107059ef82f4d6d92edcc9c37f3d73f8856205584238e35bcadb98d`, native AdamW step **230184**. The canonical source bundle is read-only evidence and its three file hashes must remain unchanged. Historical source generation 10597 supplies the checkpoint's coherent Grade C RECOVERY_1 scheduler state and fixed cohort `16add0eca49b23b471a86c4ba5d0d9f9c1cfd9a9c5b1c96f0ff857d8f7c580c0`, on which the baseline scores **287/291**. The experiment keeps its evolved teacher but resets active epoch roles and active soups to empty.

For this explicit experiment rebase, a later checkpoint cannot mint any active championship role or derivative soup merely by being later. Until one intact challenger scores **strictly more whole-school correct answers than the non-teaching best-8355 baseline on the same cohort/rubric/scope/graph**, `baseline_surpassed` remains unset and all active titles remain empty. The baseline casts zero teaching votes. Historical roles, soups and prior baselines remain archived and custody-protected. This experiment-only baseline challenge refines ADR-053's ordinary later-step eligibility without changing normal graduation-reset semantics elsewhere.

No assistant operation in this ADR performs neural optimizer updates. The human remains the sole starter of `--human-run`.


## ADR-057 | 2026-10-18 | Late-stage retention uses aggregate grade and school non-regression, not item monotonicity

The first human run after ADR-056 made genuine progress but exposed a second retention blind spot. Retained candidates moved the fixed error set rather than monotonically shrinking it: one C.DIV candidate repaired the prior DIV miss while creating a different DIV miss at the same 20/21 total; a later B recovery candidate improved B.IMPLIES/B.NOT but moved error mass into B.IFF/C.DIV; finally a retained B.IFF candidate passed the fresh B panel yet the next immutable whole-school exam fell from **287/291 to 284/291**, with B.AND, B.IMPLIES and B.NOT all worse and no compensating fixed gain. The human stopped the run at generation 12836, optimizer step 230232. This proves that sampled candidate evidence alone is insufficient late in training.

The human also rejected the opposite overcorrection: individual fixed questions and capabilities MUST remain free to trade errors during learning. A retained candidate is not required to preserve every previously-correct item, and an OR/XOR replay flip is not by itself a late-stage veto. What matters is aggregate progress/non-regression at the appropriate scopes.

When a complete immutable whole-school fixed frontier exists for the exact retained parent, late-stage admission now requires:

1. the target capability's fresh paired probe improves strictly;
2. the complete fresh lesson-grade paired panel has net correct-answer change **>= 0**;
3. the fixed **lesson grade** has net correct-answer change **>= 0**;
4. the fixed **active school grade** has net correct-answer change **>= 0**; and
5. the fixed **whole school** has net correct-answer change **>= 0**.

Individual rows and individual capabilities may regress if those aggregate bounds hold. Thus a B lesson may be retained when B improves and active Grade C is unchanged; a B lesson may also leave B fixed-flat while another grade improves, provided its target fresh probe improved and the active grade and whole school do not decline. A B +1 / C -1 trade with active Grade C is rejected because the active school grade fell even if the whole-school total ties or improves elsewhere. The fresh target gain remains the causal evidence that the attempted lesson did something useful; fixed aggregate screens prevent that gain from being purchased by larger school damage.

This aggregate regime is enabled **only when the complete fixed whole-school frontier is measurable**. Before such a frontier exists, preserve the earlier stricter safeguards: strictly positive fresh same-grade net, individual protected-capability tolerances, B.OR/B.XOR parent-correct item replay veto, and any comparable fixed-grade non-regression. This keeps early curriculum runs from silently inheriting a policy that depends on evidence they do not yet possess.

The fixed frontier is reconstructed from the immutable cohort plus the retained parent's saved wrong predictions: every non-miss row is correct by definition, and reconstructed capability totals must exactly match the saved exam before comparison. Only the candidate requires new fixed-cohort inference. B recovery therefore receives a real fixed B aggregate even while the school scheduler is on Grade C, and the same candidate predictions provide the active-grade and whole-school totals without splicing checkpoints or cohorts.

Implementation clarification: that saved fixed exam is valid for late-stage admission only when its `student_sha256` and native AdamW `optimizer_step` exactly match the current retained parent. A mismatch fails closed; stale frontier evidence must never be reconstructed, spliced, or silently treated as the current parent's frontier.

Fragile B.OR/B.XOR replay remains valuable diagnostic evidence and candidate-construction guidance. Fresh preservation rehearsal now prefers rotating structural siblings matching truth pattern, ordered operand kinds and universe size, then gracefully falls back to the same operand shape across universe sizes and finally the same truth pattern. Fixed exam row identities remain excluded. Failure to sample one exact structural sibling does not block training.

This ADR supersedes ADR-054/055/056 only for **late-stage candidate admission when a complete fixed frontier exists**. Championship and graduation rules are unchanged. The stopped 284/291 student is preserved as forensic evidence; this decision does not itself roll back or start neural training.


## ADR-058 | 2026-10-18 | Capability championship means best measured score; perfection changes succession only at the ceiling

The human corrected a semantic flattening introduced by the newer epoch-active championship layer: "a champ is just whatever's best, not what makes it to the max. Max scores only change the rules a bit about what qualifies them after max scores are hit." This restores the original ADR-018 distinction between a best-score capability champion and whole-grade/perfect mastery. The historical `capability_frontier` implementation already retained that distinction; the later `epoch_championships` and grade-soup path had incorrectly made perfection a prerequisite for active championship ownership.

Within an active championship epoch, a capability role therefore represents the best source-scored comparable checkpoint for that capability and MAY be below 100%. A checkpoint must have complete scores for the relevant grade before any role in that grade moves. An empty role accepts the first such measured owner. A non-max incumbent is displaced only by a strictly higher comparable capability score; a tie or lower score preserves the incumbent. Different cohort/rubric/scope/graph strata are not compared as raw numerators and require the appropriate same-cohort incumbent evidence before displacement.

Perfection changes only the succession rule at the score ceiling. When a same-origin incumbent is already maxed, an equal-max challenger must have strictly greater simultaneous perfect-capability breadth to displace it. When a cross-origin incumbent is already maxed, an equal-max challenger additionally requires complete target-grade perfection and a strictly higher comparable cumulative school score than every max-role owner it would displace. Failure of that equal-max takeover leaves those maxed roles unchanged; it does not invalidate independent strict gains over non-max roles or first ownership of previously empty roles measured on the same complete exam.

Grade soups follow active championship ownership rather than mastery status: each active capability role contributes one vote, including a best-below-max role. Champion/soup predictions remain advisory and independently source-gold-gated; they never rewrite oracle gold or certify graduation. The epoch baseline remains a non-teaching custody/progress reference, not a champion or fictitious incumbent, and no longer globally blocks later empty-role bests behind a whole-school baseline-victory requirement.

For the current isolated issue #340 recovery, the next intended run begins with an otherwise empty active roster plus only three explicitly authorized recovery roles assigned to the preserved optimizer-step-230216 checkpoint: B.AND, B.IMPLIES and B.NOT. Immutable fixed exams prove 230216 scored 12/12, 12/12 and 11/12 respectively versus 230232's 11/12, 11/12 and 10/12. B.IFF, B.OR, B.XOR and every A/C capability tied between those two checkpoints and therefore are NOT preloaded by this recovery instruction. This role preload does not declare mastery. The exact 230216 model+native-AdamW bytes must be recovered or safely recreated from an exact surviving copy before the authorized state restore can occur; saved JSON metadata alone is not a neural checkpoint.

Human-only neural execution remains unchanged. This ADR authorizes no agent-started optimizer update and no canonical source mutation.


## ADR-059 | 2026-10-18 | Two weakest-three bursts are bounded; ordinary MAIN spirals every imperfect eligible grade

**Direct user correction:** `weakest_three()` is a bounded remediation mechanism, intended to run for a maximum of exactly two freshly re-ranked rounds before ordinary grade progression resumes. After the second weakest-three assessment, the scheduler must leave recovery mode and advance to the **next sequential eligible admitted grade that is still below 100%**, wrapping through the admitted grade order and skipping grades already perfect on the latest cumulative assessment. It must not return indefinitely to the same current letter while other imperfect grades exist.

An ordinary grade pass is grade-wide, not mistake-only. When the scheduler reaches an imperfect grade, it runs that grade's complete currently introduced capability sequence; already-correct sibling capabilities remain part of the ordinary pass for coverage, retention and representational variety. `RECOVERY_1` and `RECOVERY_2` are the only two globally ranked weakest-three bursts for that stop in the spiral, with a fresh cumulative ranking before each. After round two, move to the next imperfect grade. If every other eligible grade is perfect, wrapping back to the same still-imperfect grade is valid.

This correction changes scheduling only. It does not change capability or grade ownership, exam rubrics, 100% mastery criteria, ordered graduation/revalidation targets, candidate-retention gates, teacher policy ownership, or the human-only optimizer boundary. An off-grade lesson scheduled during a spiral still credits the grade of the capability actually taught while preserving the separately reported active scheduler grade. This ADR supersedes active-grade-only repetition language in ADR-002/024/031 and root guidance wherever they conflict with this direct clarification.


## ADR-060 | 2026-10-18 | Flash mode may defer title/qualification work, never scheduler evidence

The human observed a five-minute flash run perform 105 additional teaching visits without leaving Grade B after ADR-059. Live events showed the mechanism exactly: every six B MAIN visits reached `ASSESS_MAIN`, but flash mode reopened the same B queue without taking the fresh cumulative assessment that alone can rank recovery work or advance to the next imperfect grade. Flash therefore bypassed the governing scheduler despite the scheduler implementation itself being corrected.

Flash mode remains a throughput optimization, not an alternate curriculum. At every scheduled `ASSESS_MAIN`, `ASSESS_RECOVERY_1`, or `ASSESS_RECOVERY_2` boundary it MUST checkpoint the current causal student, draw and score a fresh routine source-oracled cumulative cohort, update teacher misses/diagnostics/stagnation evidence, and use that evidence to choose the next scheduler state. Thus the ADR-059 sequence remains operative in flash: ordinary grade pass, at most two freshly ranked weakest-three rounds, then the next sequential imperfect admitted grade. Flash MUST NOT indefinitely reopen the same letter merely because championship work is expensive.

To retain the intended speed/safety distinction, a flash scheduler assessment does NOT run candidate/incumbent championship competition, mint or move active championship titles, rebuild soups, add protected graduation witnesses, publish a golden ancestor, or qualify grade/program advancement. If the fresh scheduler-only evidence finds no remaining imperfect admitted grade, the state remains at its real `ASSESS_*` boundary and flash stops with full authoritative qualification still owed. A normal authoritative exam is required to establish mastery/advancement.

Dashboard championship telemetry must also distinguish observed facts. A fresh sampled exam with an existing champion is not itself a champion-save event. `GRADES & MASTERY` therefore reports actual title movement (`TITLE MOVED n`), explicit no-movement (`NO TITLE CHANGE`), current regression, or flash sample/no-title authority. `SYSTEM & QUALIFICATION` reports the capability scores for moved titles and any explicit denied cross-origin title decision. Capability-best slot events remain distinct from active championship titles and show their actual scored slots.

This ADR changes no neural optimizer authority. Only the human invokes `--human-run`; source/test work remains neural-inert.


## ADR-062 | 2026-10-18 | Maxed capability champions advise across grades; soups add a reduced aggregate vote

**Direct user correction of ADR-035:** active maxed capability champions are not confined to their own lesson grade. Each active capability role at 100% contributes one direct advisory vote to training examples in any admitted grade. A frozen grade soup remains a separate aggregate adviser. Same-grade soup advice keeps the soup's full frozen base vote count; foreign-grade soup advice divides that base count by the current number of admitted grades.

Direct votes are capability-role votes, not checkpoint votes. If one intact checkpoint owns several qualifying maxed roles, inference may load and evaluate that checkpoint once, but its advisory weight equals the number of active maxed roles it owns. Historical or global simultaneous-perfect breadth does not create extra direct votes. Active best-score roles below 100% remain valid championship and soup ingredients under ADR-058, but they contribute zero direct capability votes until maxed.

Current issue #340 state makes the intended arithmetic concrete. A owns six active roles and all six are maxed, so a B lesson receives six direct A capability votes. A's frozen soup has base vote count six and, with A/B/C admitted, contributes another `6/3 = 2` votes. C currently owns seven active roles, five maxed, so B receives five direct C capability votes plus the existing C soup weight `7/3`. B currently has no maxed active roles, so it contributes no direct B capability votes to itself, while its six-role soup remains available under the existing soup contract.

Direct and soup advice enter the same independently source-gold-agreeing, teacher-`distill`-scaled, bounded confidence target. They do not change source gold, exam scoring, capability scheduling, championship ownership, the causal student's identity, or AdamW. A mentor that predicts an example incorrectly contributes no advice for that example. This ADR supersedes ADR-035 and Championship Lifecycle v1 only where they forbid direct cross-grade maxed-capability advice. The epoch reset, earned-only roster, soup construction, score comparison, and human-only optimizer boundaries remain unchanged.


## ADR-061 | 2026-10-18 | Two weakest-three bursts occur between full imperfect-grade sweeps, not after every grade

**Direct user correction of ADR-059/060 cadence:** the user's intended note was that `weakest_three()` runs only twice **in between regular progression through all grades that do not yet have 100% mastery**. ADR-059 correctly bounded recovery to two fresh global rankings and correctly prohibited indefinite current-letter loops, but the implementation and its prose placed those two recovery bursts after every individual grade pass. That interpretation was too aggressive.

The governing scheduler cadence is now: perform ordinary `MAIN` progression through every currently eligible admitted grade that remains imperfect on fresh cumulative evidence, in canonical wrapped order and skipping grades already at 100%; only after that ordinary imperfect-grade sweep is exhausted, run `RECOVERY_1` over the complete eligible cumulative pool; take fresh cumulative evidence; run at most one freshly re-ranked `RECOVERY_2`; then reset the sweep and resume ordinary imperfect-grade progression. A still-weak capability may appear in both recovery rounds. Recovery remains global, so the genuinely weakest grade may dominate those six or fewer recovery visits, but it MUST NOT receive two additional recovery bursts merely because the scheduler has just finished each other grade's ordinary pass.

Live evidence motivating this correction is the five-minute non-flash command ending generation 15392. The scheduler itself moved across letters, but 30 of 40 committed teaching-visit events were B and only 10 were C. Active scheduler grades were B=18, C=16, A=6; all six A-active recovery visits and six C-active recovery visits selected B capabilities from the global weakest pool. Thus the residual B saturation was not another same-letter lock. It was the per-grade placement of otherwise-valid global recovery bursts.

This cadence applies identically to flash scheduler evidence. Flash may still defer championship, soup and promotion authority under ADR-060, but it follows the same complete ordinary-grade sweep before the two global recovery rankings. This ADR supersedes ADR-002, ADR-059, ADR-060 and current root guidance only where they say or imply that two weakest-three rounds occur after **each** grade. Grade mastery, cumulative same-checkpoint qualification, champion/soup semantics, candidate retention, source-oracled assessment, and the human-only neural optimizer boundary are unchanged.


## ADR-063 | 2026-10-18 | Start parallelism with three execution lanes: one causal MLX owner plus two deterministic source-preparation workers

**Direct user authorization:** begin the previously discussed multi-core acceleration conservatively at three execution lanes rather than jumping immediately from one to eight. The trainer keeps exactly one causal neural owner. Only that main lane may hold or mutate the live MLX parameter tree, the student's native AdamW, teacher credit, scheduler state, championship state, checkpoint pointers, or durable run receipts. Two additional worker processes may perform deterministic host-side preparation for upcoming optimizer steps, but they MUST NOT receive a model checkpoint, parameter tree, optimizer, writable run directory, state pointer, championship authority, or any other capability that could make them a second neural writer.

The first parallelized surface is source preparation, not speculative students. Workers may draw independently source-oracled fresh lesson rows, old-grade rehearsal rows, fragile-preservation candidates, Boolean-association rows, and other pure lesson-preparation material whose output is completely determined before the main neural step. Stateful miss replay, mentor inference, loss/gradient computation, AdamW updates, candidate-retention evidence, retention admission/rejection, teacher reward, scheduler advancement, exams, state persistence and checkpoint publication remain serialized on the main lane. No concurrent MLX/Metal inference or training is authorized by this ADR; that requires separate proof and a later decision.

The starter configuration is two preparation workers plus the main lane, i.e. three execution lanes total. A zero-worker mode MUST preserve the pre-ADR serial path for direct A/B comparison and recovery. Every prefetched packet MUST be bound to an inspectable identity including the current run/generation, source manifest, admitted course/source graph, durable parent checkpoint, causal parent optimizer step, scheduled capability, visit step and policy/seed inputs. A packet that does not match the consumer's expected identity is stale and MUST be discarded or fail closed before neural use. Bounded queues/backpressure are required; preparation workers may never advance curriculum or commit results merely because they finished first. The source/row bytes delivered to the optimizer must remain deterministic for a fixed run identity and seed regardless of whether prefetch is enabled.

Timing telemetry MUST distinguish preparation submission, wait/consume time, serial fallback and MLX training so the speedup can be measured rather than assumed. The initial goal is throughput improvement without changing the causal update sequence or teaching semantics. Scaling beyond two preparation workers, parallel MLX inference, or simultaneous neural candidate branches is explicitly outside this starter ADR and requires new empirical evidence plus a new authority decision.

The initial performance evidence supports pipelining rather than generic multiprocessing. An existing timing trace from the protected trainer measured mean per-step fragile-preservation generation at 45.50 ms, ordinary source drawing at 8.62 ms and the serialized MLX training step at 22.11 ms, with lesson selection and guidance adding additional main-lane work. Thus roughly 54 ms of pure source preparation can overlap two successive main-lane step windows. A disposable real-source benchmark over 48 full B packets including fragile OR/XOR preservation, old-grade rehearsal and Boolean bridge material measured 3.3402 s serial versus 2.5036 s with two spawned workers, a 1.334x preparation-throughput gain including process startup, with direct and spawned outputs exactly equal. These measurements justify the three-lane starter but do not predict or claim a particular end-to-end neural-training speedup; the new timing receipts must measure that on the next human run.


## ADR-064 | 2026-10-18 | If the current recovery does not show meaningful growth, the next experiment is a fresh ternary model trained from scratch

**Direct user fallback decision:** if the present FP32 Bilqis recovery run does not show meaningful growth to the human operator's satisfaction, the next major training experiment is a ternary model trained **from scratch**, as originally requested, rather than another rescue of the existing checkpoint. "Meaningful growth" remains a human experiment gate here; this ADR does not invent a hidden numeric threshold or automatically abandon a live lineage.

The ternary experiment is a new causal lineage. It MUST NOT warm-start from the current FP32 weights, copy the current AdamW moments, inherit active championships/soups as teaching votes, or masquerade as a continuation of optimizer-step history. The first reproducibility baseline should preserve the current admitted semantic/token ABI, source generators and independent golds, curriculum/admission order, scheduler/retention rules, assessment cohorts/seeds where applicable, and the current six-layer/width-384 topology before changing model capacity. The current topology contains 10,745,856 parameters; holding that topology constant lets the experiment ask what ternary weight geometry itself changes. Any widened ternary model is a separate capacity experiment, not silently folded into the first comparison.

The intended starting family is BitNet-b1.58-style quantization-aware training rather than post-training quantization: neural linear weights used by the forward path are ternary `{-1, 0, +1}` from the beginning, with the training implementation explicitly recording its higher-precision latent-weight/gradient treatment, quantizer scale rule, rounding/tie behavior, activation precision, optimizer, initialization and every export transformation. The exact ternary codes used for evaluation MUST be durably hashable and recoverable independently of any convenience BF16/FP16 serialization of latent weights. An export that can silently change ternary codes is a reproducibility failure, not an implementation detail.

The first ternary trial MUST distinguish weight representation from architecture. Current Bilqis uses centered normalization, learned absolute positional embeddings and a squared-ReLU feed-forward path; canonical BitNet-style models commonly change additional architectural choices such as normalization, positional encoding and feed-forward activation. Therefore the first ternary baseline retains Bilqis's present forward topology and changes only the intended trainable linear-weight representation/quantization machinery. A later RMSNorm/SwiGLU/RoPE or otherwise canonical BitNet-style sibling is a separate architecture experiment and must not be compared as though bit-width were its only changed variable.

Cross-bit reproducibility therefore means **experimental equivalence**, not byte-for-byte equality with the FP32 student: same source questions/golds, same curriculum and seeds, same architecture shape for the first trial, same evaluation contract, and fully recorded ternary training/export semantics. Weight tensors themselves are intentionally incommensurate. Comparisons should report learning trajectory, retained-update efficiency, capability/grade scores, robustness across fresh cohorts, storage/runtime costs and failure modes, while keeping the FP32 and ternary lineages permanently distinguishable. No ternary implementation is authorized to overwrite or convert the preserved FP32 experiment in place.


## ADR-065 | 2026-10-18 | Binary lessons preserve operand truth-table coverage and bridge the active connective

Live Grade-B evidence at optimizer step 233048 showed repeated fresh-cohort volatility across AND/IFF/IMPLIES/OR/XOR while the same retained checkpoint remained unchanged. Inspection found two lesson-shaping defects that could waste optimizer work without changing oracle correctness. First, retention-aware source selection preserved only final `TRUE`/`FALSE` labels and teacher-selected old-grade allocation; it could omit legal operand truth patterns for the active connective entirely. A deterministic regression using the observed `old=20`, `depth=3`, `contrast=0` shape reproduced an IFF batch containing only `00` and `01`, omitting `10` and `11`. Second, the opted-in Boolean association bridge appended eight A/C-derived examples per B optimizer step but selected their outer Grade-B operator independently of the capability currently being taught, so an IFF visit could spend adjunct capacity on unrelated AND/OR/XOR/IMPLIES examples.

**Decision:** when the current source rows expose explicit `operand_truths`, the lesson selector treats those patterns as structural semantic coverage. Before allocating old-grade rehearsal, it reserves enough current-grade capacity to deliver every source-valid operand pattern at least once. It then fills the remaining current-grade slots toward balanced final binary labels, preferring unique source rows before reuse. Teacher policy still controls learning rate, depth emphasis, contrast mode, distillation and requested old-grade pressure; only the minimum capacity needed to keep the active connective's semantic truth table represented may reduce the realized old-grade count. Telemetry records `current_semantic_patterns_required` and `current_semantic_patterns_delivered` so this constraint remains inspectable rather than implicit.

The Boolean association bridge is also target-aligned. During a B lesson, all A/C-derived bridge rows use the **active B capability's connective**. Binary connectives continue to compose two opaque source assertions; B.NOT composes one opaque assertion and is now supported explicitly. The standalone broad bridge generator retains its prior random-binary-connective mode when no target capability is supplied. This ADR changes lesson composition only: source/oracle truth, assessment rubrics, scheduler authority, retention gates, championship rules, causal student identity and native AdamW custody are unchanged.


## ADR-066 | 2026-10-18 | Do not recycle AST-boundary supervision or syntax reshaping as the next Grade-B rescue

The user correctly challenged a proposed return to explicit compositional/AST-boundary supervision on the grounds that the same Grade-B stagnation existed while the earlier composition stack was already present. Source-history inspection confirmed an important distinction: the earlier typed semantic AST, intermediate-domain contracts and source-witness composition audit were **neural-inert** (`training_authorized=False`). They proved source composition legality and operand truth; they never imposed a hidden-state training loss. The later A/C Boolean association bridge was live training, but it likewise did not create robust compositional transfer.

Before changing the live trainer, disposable experiments were run against an in-memory clone of the exact current retained checkpoint. A new operand-boundary auxiliary loss forced the hidden state at each source-defined operand endpoint to decode that operand's independent TRUE/FALSE gold while retaining the final connective loss. Across AND/OR and multiple auxiliary weights, this produced no material improvement over native training and often slowed it. Reordering B expressions to postfix/RPN, inserting `syntax.end` boundaries, inserting child query/end boundaries, and presenting children before the final composite likewise failed to outperform the native encoding consistently. A fresh AdamW on the same weights behaved materially like the inherited step-233k AdamW, so optimizer-moment history is not the dominant explanation. A frozen linear probe on final B hidden states reached only about 63.5% on fresh balanced B rows, and a probe at operand boundaries reached only about 60.9% overall, confirming that the missing signal is representational rather than merely a bad tied TRUE/FALSE classifier.

The repository's preserved historical micro-universe experiment independently corroborates the user's point. That scratch transformer used an explicit staged composition curriculum with focus/composition/contrast/rehearsal and one continuous AdamW for 8,400 updates / 268,800 example exposures. Its archived final report explicitly concludes "partial task acquisition, not robust compositional transfer." Final Boolean held-composite performance was 66/128; final varied Boolean was 71/128. Thus the present Grade-B difficulty is **not** a recent regression caused by removing a previously successful neural composition mechanism, and reintroducing AST language or intermediate truth supervision without new evidence would repeat a falsified direction.

The current evidence instead establishes a narrower negative result: literal Boolean gates are trivially learnable by the exact present model (disposable current-checkpoint AND/OR reach 100% within 32 direct truth-table updates), top-level Grade-A negative relation/equality semantics remain essentially perfect on fresh rows, but the current transformer family/pedagogy has repeatedly failed to turn those capabilities into robust nested compositional transfer. Do not claim another lesson-shaping tweak fixes this unless a disposable held-out experiment first beats the native baseline materially. Preserve ADR-064's ternary-from-scratch fallback as the next major experiment once the human meaningful-growth gate is deemed failed; do not silently copy the same failed compositional pedagogy into a new lineage and call bit-width the only changed variable without recording that limitation.


## ADR-067 | 2026-10-18 | Enforce the pre-existing curriculum architecture as the only runtime path

**Direct user correction and historical clarification:** Bilqis curriculum growth was already specified from the program's early authority surfaces as a functional, compositional, composable, modular, flexible, reusable semantic/curriculum system. This ADR does not create that architecture. The public issue graph, original roadmap, alpha checkpoint/supplement, semantic ABI, prerequisite/stage contracts, curriculum gate, private authority, registries/ledgers and later governing specifications all predate or independently restate the same direction. New grades must not be handwritten as separate trainer/evaluator/admission implementations. The prior repository violated the existing requirement by building typed AST/compiler/factory work beside the live handwritten school, then admitting Grade B and Grade C through bespoke runtime paths before the generic runtime cutover was complete.

The governing desired state is now `docs/specifications/0001_GENERATIVE_CURRICULUM_FACTORY.md` (**SPEC-0001**). Its runtime invariant is **no factory release, no grade**. Every executable grade must use the same typed factory contracts for semantic identity, source binding, construction, coverage, teaching options, routine assessment, promotion, fresh generalization, release, admission, telemetry and historical compatibility. A source-only compiler beside a grade-specific trainer does not conform.

The implementation packet is `docs/tasks/0001_IMPLEMENT_GENERATIVE_CURRICULUM_FACTORY.md` (**TASK-0001**). It requires A/B/C migration through one factory path, deletion of canonical grade-specific runtime bypasses after verified caller migration, static anti-bypass checks, a synthetic Grade Z extension proof, colocated focused tests, and a structured documentation migration. Existing user-directed championship and candidate-retention specifications are renumbered as SPEC-0002 and SPEC-0003 and remain governing within their domains.

Assessment lifetime must preserve the user's existing no-holdout rule: failed fixed promotion questions and gold remain teachable after scoring, and that promotion attempt may be retried. Promotion success is not treated as out-of-sample proof. SPEC-0001 adds a separate fresh generalization gate so a familiar qualification cohort cannot by itself certify broad mastery. Routine MAIN/RECOVERY assessments remain fresh and dynamic under the earlier direct correction.

Failure intelligence records this architecture defect as `PM-2026-10-18-007` / `RC-105`: extensive architecture authority already existed, but implementation repeatedly defected from it and a writable legacy grade runtime remained available because no structural enforcement made nonconforming paths impossible. The remediation is structural enforcement of existing authority, not another replacement architecture and not another instruction asking future agents to remember it. Human-only neural optimizer authority, existing student/AdamW custody, historical ABI, receipts and evidence remain unchanged by this ADR.


## ADR-068 | 2026-10-18 | Current-cohort champions absorb ancestral earning examinations

The human clarified that weaker current replays are useful: championship competition compares challenger and incumbent on the same current questions, without protecting an earlier numeric score. Until a replacement qualifies, the incumbent retains its titles and source-gold-gated advisory votes. A normal fresh run must award complete-grade capability roles before graduation. Equal-max breadth counts perfect capabilities within the target grade; when the whole grade ties at perfection, a challenger from any origin must strictly beat the actual incumbent owners across the same complete school cohort.

The human additionally requires the winner to absorb every displaced champion, “like the Highlander.” Preserve all questions that influenced each earning decision, including original misses: the relevant capability panels, grade-perfect breadth panels and complete-school takeover panels. Every external replacement must answer their entire ancestral union correctly as well as win the current paired competition. The obligations and parent/ancestor identities follow the checkpoint across every role it owns. No branch is dropped when several champions are consolidated. Same-checkpoint new evidence can strengthen a role without displacing itself; historical max proof remains advisory entitlement, not a stale numerical comparison floor.

This supersedes conflicting origin-based or historical-score interpretations in ADR-058 and SPEC-0002 revision 2. It does not change candidate retention, teacher policy, scheduling, source semantics, graduation, human-only actual optimizer ownership or ADR-060 flash deferral. Existing role witnesses are reconstructed only from their original immutable cohort and intact owning checkpoint; missing or mismatched evidence blocks transfer. Existing run files are not rewritten by this source repair. Incident PM-2026-10-18-008 tracks the fresh-run wiring gap and the corrected implementation interpretation.


## ADR-069 | 2026-10-19 | One lifetime title fight per checkpoint pair; champions are same-grade; quarantine cannot embargo unrelated contenders

**Direct user correction:** "even if anything changes, two checkpoints only match up against each other one time. Period."

For one capability, one unordered pair of complete checkpoint SHA identities may settle exactly one championship title fight for the lifetime of the run. The first settled result is immutable matchup history. A new cohort, changed current score, changed surviving battery, later title transfer, role reversal, scheduler phase, or any other changed condition does **not** reopen that pair. A duplicate pairing must be rejected before superficial championship replay, fan-out screening, defended-battery inference, role-score refresh, or battery mutation. The same two checkpoints may still have one independent first-ever fight for a different capability because capability titles remain separate roles. One-hop same-grade fan-out remains non-recursive and must skip any sibling matchup already present in the settled-match ledger.

Active capability championships are now strictly **grade-isolated**. The retained optimizer update that created the champion or contender checkpoint must originate in the same grade as the capability title. Merely examining a frozen checkpoint on another grade's questions does not relabel the checkpoint's origin. A Grade-B-origin checkpoint cannot own or defend a Grade-A capability title. Legacy active roles that violate this invariant are archived and removed from the live role/soup field rather than grandfathered. Missing origin provenance fails closed. Individual champion advice remains same-grade only; frozen soups are the championship-derived mechanism for cross-grade influence while the school geometry remains otherwise compatible. This supersedes the cross-grade direct-champion vote in ADR-062 and the cross-origin active-title assumptions in older championship ADRs where they conflict.

Stagnation quarantine is also separated from championship authority. Quarantine/withholding is capability-local teaching and scheduling authority; it must not become a blanket title embargo for the entire exam. If one capability is withheld but another same-grade capability is completely and source-validly measured at the intact checkpoint, that measured capability remains eligible to mint an empty role or challenge a valid incumbent. In particular, a valid same-grade `12/12` still opens that checkpoint pair's first-ever title match. A withheld capability simply cannot contend from absent evidence.

This correction is grounded in read-only evidence from `runs/codex-0001-prometheus`. Checkpoint step **125096**, SHA prefix `60d3731d5435`, was created during Grade-B training after Grade A had ended at step 125080, yet the superseded cross-grade rules let one Grade-B MAIN/GENERALIZATION exam mint all six A titles plus six B titles. Later, the same step-125096 incumbent and step-127512 challenger were repeatedly rematched, allowing defenses to refresh and enlarge the incumbent's surviving batteries. Separately, multiple later A-origin checkpoints produced source-valid capability-best `12/12` results with no championship decision because `_take_exam()` skipped all championship advancement whenever `blocked_before` or `blocked_after` quarantine was active. Those are three independent conformance defects, not evidence that the old A incumbent was legitimately unbeatable.

Durable implementation owners are protected issues **socr8s/private-ip #343** (pair idempotence and same-grade title provenance) and **#345** (quarantine-independent contender admission and live tournament replay). Governing desired state is `docs/specifications/0002_CHAMPIONSHIP_LIFECYCLE_V1.md` revision 7. No agent neural optimizer update is authorized by this ADR.


## ADR-070 | 2026-10-19 | Any holistic school-geometry change archives and clears every active champion and soup

**Direct user correction:** "remove all champs when the school changes holistically in any way, like I had asked for from the start: any change in the number of total questions being posed schoolwide, or the number of semantics in use schoolwide, or anything that would change the model's geometry substantially across multiple grades at once, is meant to negate all past champions and soups entirely, as we're no longer comparing apples-to-apples at that point. Their advisement is liable to do more harm than good."

Every active championship epoch therefore belongs to one exact **championship school identity**. The identity must be durably and deterministically bound, at minimum, to the admitted `course.digest()` (which includes grade/capability structure and exam-item counts), the active semantic-graph digest, the model parameter-shape inventory/neural geometry, and the active executable factory-release identity. These are comparison-geometry inputs, not advisory metadata.

Before any active champion or soup may advise, defend, qualify, or participate in fan-out, the stored championship school identity must equal the live identity. **Any mismatch invalidates the entire active field at once.** Archive the current active capability roles and all active grade soups losslessly, then clear all live roles and soups and bind the empty successor field to the new school identity. Do not selectively salvage, re-score, or grandfather prior active champions/soups across that boundary. New grade admission, a school-wide question-count/inventory change, semantic inventory change, parameter-shape/model-geometry change, or materially different executable school release therefore begins with zero live championship-derived authority.

The causal whole student and its own native AdamW continue unchanged across this metadata reset unless a separate training/admission rule says otherwise. Immutable champion/soup provenance also remains historical evidence, and the permanent settled-match ledger remains run history; neither grants live teaching or title authority in the new geometry. This rule is intentionally global rather than capability-local because the comparison system itself has changed. It supersedes narrower historical wording that preserved prior live advisers across curriculum/version transitions, including the active-voter implications of ADR-062 and any older golden-baseline interpretation that repopulated active titles automatically.

Protected implementation owner is **socr8s/private-ip #344**. Governing desired state is `docs/specifications/0002_CHAMPIONSHIP_LIFECYCLE_V1.md` revision 7. The canonical Specs/Failures Ledger records this as S098 / ADR-A59 / F027; the Curriculum Registry records the same reset in Decisions and Champion Lifecycle. No agent neural optimizer update is authorized by this ADR.


## ADR-071 | 2026-10-19 | Empty capability titles require 66% proficiency and begin with only their first passed questions

**Direct user decision:** after a championship field has been cleared, an empty capability title MUST remain vacant until one same-grade checkpoint reaches at least **66% proficiency on that capability**. On the current twelve-question capability exams this means **8/12 or better**. A checkpoint below that floor may be measured but cannot become the first owner merely because the slot is empty.

When a checkpoint first crosses that threshold and claims the empty title, its initial title-defense battery is exactly the set of questions for that capability that the checkpoint answered correctly on that threshold-crossing examination. No missed questions, sibling-capability questions, broader grade panel, historical battery, synthetic padding, or other evidence is added to the initial battery. Later valid contenders face the normal championship comparison against that battery under the existing one-lifetime-fight and same-grade rules.

This changes empty-slot admission and initial battery construction only. It does not change title ownership after an incumbent exists, grade soups, school-identity resets, scheduler authority, source gold, graduation, or the human-only optimizer boundary.


## ADR-072 | 2026-10-19 | Default Grade B is a reduced AND/IFF kernel; the full Boolean grade is explicit opt-in

**Direct user decision:** new Grade-B admission defaults to a reduced four-capability release containing only **B.AND**, **B.IFF**, **B.COMPOSITE**, and **B.IDBOOLOPS**. The latter two are simplified to use only AND and IFF. Every other existing Grade-B Boolean semantic remains implemented but withheld from the default admitted course. No legacy Boolean implementation is deleted.

The reduced grade teaches AND and IFF first, then the AND/IFF-only COMPOSITE capability, then the two-way AND/IFF IDBOOLOPS capability. IDBOOLOPS therefore exposes only the existing AND and IFF semantic-token answers. COMPOSITE may compose only those two operators. New A→B admission uses this reduced release unless the human explicitly supplies `--full-grade-b`, which selects the preserved legacy six-operator lineage.

For an existing A/B-only run whose saved curriculum is one of the preserved full Grade-B releases, ordinary resume on this profile performs one **neural-inert grade replacement** to the reduced release unless `--full-grade-b` is supplied. The causal student, exact checkpoint SHA, native AdamW and optimizer step remain unchanged. Because the B capability/question inventory changes holistically, the replacement archives and clears active championship roles/soups under ADR-070 and deactivates stale geometry-bound operational evidence from the old rubric (active capability frontier, whole-student retention peaks, miss replay/exposure state, current stagnation session, and old assessment/generalization caches). The immutable prior state/history remains preserved. Legacy `--boolean-composite` or `--boolean-idboolops` flags do not reactivate the old full-B releases under the reduced profile; the simplified capabilities are already admitted.

Legacy/full Grade-B-specific unit, source-adapter, migration, and trainer tests are retained as opt-in compatibility tests under `BILQIS_FULL_GRADE_B_TESTS=1`; they are not the default current-grade contract. The default suite owns separate reduced-B coverage. Downstream vocabulary growth into Grade C must preserve whichever Boolean-operator answer head the admitted B lineage actually owns; a reduced two-way head must not silently expand back to six operators.

This is a reversible curriculum/admission change, not a semantic deletion. Existing source identities, old run receipts, historical full-B release digests, student/AdamW custody, championship governance, and human-only optimizer authority remain intact. The currently admitted full profile may be retained explicitly with `--full-grade-b`.


## ADR-073 | 2026-10-19 | A defended title requires a fresh strict incumbent battery win; ties transfer to the challenger

**Direct user clarification:** once a challenger qualifies for a capability title fight, the incumbent does not defend with its historical winning answers. Both the incumbent and challenger MUST be freshly inferred on the same current capability panel and the incumbent's same surviving title-defense battery during the same adjudication. Cached neural answers, historical peak scores, or prior battery results do not satisfy the defense because model outputs are not assumed deterministic and the prior champion may have benefited from a lucky earlier draw/inference.

The incumbent retains the title only when its fresh battery score is **strictly greater** than the challenger's fresh battery score. If the challenger scores higher, it wins. If the two fresh battery scores tie, the challenger also wins. Qualification for the fight and winning the fight remain separate: a `12/12` current capability result forces an eligible title match but does not bypass the incumbent's fresh battery defense.

Checkpoint retained-update grade is provenance, not title jurisdiction. A complete intact checkpoint may challenge a capability title whenever it supplies complete comparable evidence for that capability, even if its most recent retained optimizer update occurred while another grade was active. The title itself remains attached to the capability's grade; direct title advice and one-hop fan-out remain title-grade-local, while `checkpoint_origin_grade` remains preserved as historical provenance.

This ADR supersedes ADR-058/069 and any earlier championship clause only where they say or imply that (a) a battery tie preserves the incumbent, (b) an incumbent may defend from cached/historical neural answers, or (c) optimizer-update origin grade vetoes otherwise valid capability-local title evidence. Pairwise one-fight lifetime idempotence, defended surviving batteries, source/rubric/graph comparability, school-identity reset, checkpoint custody, and the human-only optimizer boundary remain unchanged. Governing executable detail is SPEC-0002 revision 10; repair commits are `6e04ca0`, `ae31d98`, and `fcbe496` on the isolated repair branch pending safe installation into the human-owned live checkout.


## ADR-074 | 2026-10-19 | Substantial stagnation may carry mastery debt into the next grade without declaring the prior grade mastered

**Direct user correction after the 2026-10-19 B.IDBOOLOPS run:** two weakest-three rounds are intentionally too small to define the total patience budget for a difficult grade. They remain the bounded recovery cadence *inside* the ordinary spiral. At the same time, a grade that has received substantial human-observed rehabilitation must not monopolize the entire curriculum indefinitely merely because one or more capabilities have not reached cumulative 100%. After roughly half an hour of the observed A/B run, `B.IDBOOLOPS` was consistently near/perfect while `B.AND` and `B.IFF` continued oscillating despite 125 rehabilitation-era exams and 268 visits. The human explicitly ended that run and authorized moving on to Grade C.

**Decision:** clean graduation and progression into new learning territory are distinct. The default path still requires the existing cumulative same-checkpoint mastery contract before ordinary next-grade admission. A human may now explicitly authorize **next-grade admission with mastery debt** after the runtime has durable stagnation-rehabilitation evidence. The runtime derives the debt from a complete current-checkpoint assessment of the entire prior admitted course; every imperfect prior capability is carried exactly, including regressions outside the originally quarantined grade. It must not fabricate a B champion, graduation receipt, perfect score, or historical mastery claim.

The next grade is admitted through its normal release and transition machinery. For Grade C this means the same append-only vocabulary/ABI expansion, deterministic embedding-row extension, native AdamW extension, factory admission, championship-identity reset, and source/rubric contracts as ordinary C admission. The pre-growth checkpoint is archived explicitly as a **boundary checkpoint with debt**, not mislabeled as the “previous graduate.” The one-time human command is `--admit-next-grade-with-debt`; the durable state thereafter carries `carried_mastery_debt`, so the flag is not a sticky training mode.

While debt exists, cumulative assessment keeps all admitted grades in scope. Ordinary MAIN sweeps and the existing two global weakest-three rounds continue across every imperfect admitted grade. A later grade may earn a capability/grade champion without erasing earlier debt. The debt epoch closes only when one intact causal student and its own AdamW produce complete active-school mastery at one checkpoint; at that moment all active grade pointers may be rebound to that complete student and the ordinary next-grade boundary resumes.

This supersedes IPR-0220 / ADR-061 only where they make 100% prior-course mastery an absolute prerequisite to *opening* the next human-authorized learning grade. It does **not** weaken cumulative mastery as the condition for clearing carried debt, clean graduation, final qualification, or automatically opening subsequent grades. It also does not turn “two recovery rounds,” elapsed wall time, exam count, or optimizer steps into an automatic abandonment threshold. Choosing to carry debt forward remains an explicit human experimental decision until a separately evidenced adaptive policy is authorized.

## ADR-075 | 2026-10-20 | Source-realized thin JIT slices and stable token allocation provenance

Issue #349's direct user mandate selects the smallest currently justified semantic
slice. The v2 canonical definition may therefore begin a grade with one real
capability, up to the existing nine-capability upper bound. Profiles can skip
unrelated inactive grades while preserving prerequisite/constituent closure.
Historical v1 Course cardinality and release manifests are unchanged. SPEC-0001
records the refinement. A new source realization is factory data and an adapter,
never a new grade trainer or evaluator.

The first realization binds lexicon -Č-, Stem 1/BSC, sense
LEXSENSE-5286ade9db42c7, to total finite reference-map identity. It positively
compares denotations, requires current A.IDENTITY and A.MAPS, and claims no
Ithkuil morphology. A distinct token occupies index 227 after the separately
admitted numeric prefix; the native Token Atlas append was read back with all
227 previous rows unchanged. Source qualification is separate from student
adoption and learned mastery.

A second vocabulary allocation exposed a provenance defect: regenerating Token
Atlas rows assigned the new container hash to earlier tokens. Later graph versions
now carry prior allocation-source hashes as a sidecar. Node hashes and indices
remain immutable, native identity checks remain strict, and the original numeric
graph artifact is reproduced unchanged. PM-2026-10-20-003 / RC-116 records the
reproduction and containment.

JIT readiness is recomputed before adoption. Registered source/answer implementations
must match the sealed package. The normal student/own-AdamW transaction performs
catalog growth, scheduler adoption, identity reset, outbox persistence and fresh
evidence reconciliation. New-grade automation retains complete-prefix qualification;
the source frontier cannot grant itself a mastery-debt exception.


## ADR-076 | 2026-10-21 | Complete v2 rubric migration and observational readback

Continued issue349 system execution exposed stale legacy live-rubric metadata
after executable v2 migration, and diagnostic/replay readers reconstructing a
cohort with its storage schema in place of its actual rubric. Bind the migrated
live rubric to the active executable grade while retaining immutable historical
receipts/exams and causal student/own-AdamW identity. Own v1/v2 stored-rubric
interpretation once in generated_assessment; consume it in diagnostics, fixed
frontier and fragile replay. Validate v2 diagnostic source, release and scope
bindings and retain original content-digest/scoring checks. Routine observations
receive their actual released cohort pointer metadata. Diagnostics remain
observational and cannot redefine source meaning, teacher policy or admission.

Migrate disposable system fixtures through production admission/migration owners.
Preserve exact historical student/optimizer custody and verify same-checkpoint
recovery. Current championship behavior follows SPEC-0002 revision9/10; historical
same-training-origin and tie-defense assertions are superseded. No production
championship policy is changed here. Fix repository-root test import precedence
for file and dotted targets rather than relying on an installed tests package.
Focused red/green regressions and the combined511-test source-isolated run support
the repair. PM-2026-10-20-003 / RC-116 was enriched with native readback. Existing
issue-owned experiments alone remain authorized; no third run, canonical-run
mutation, AdamW merge, synthetic lineage, main merge or issue closure.


## ADR-077 | 2026-10-21 | Carry typed experiment custody through the training launcher

A registered issue-owned control could train without retention from an isolated
source archive, but normal retention resume refused its external data path before
updates. Passing only a budget callback had discarded the ownership contract.
Pass the existing ExperimentRunBudget owner through CLI and operate. The runtime
owner requires prior registration and measured collective budget compliance
before source/GPU loading; anonymous callables cannot authorize external runs.
Without an issue owner, the existing checkout-local isolation rule still applies.
Existing protected students still reject no-retention resume. No third run or
canonical/historical mutation is authorized. PM-2026-10-20-003 / RC-116 records
the integration gap and containment, with native ledger readback.

The same independently seeded control may tighten from its earlier unprotected
policy to ordinary causal retention without changing its student or own AdamW.
This sequential exploratory phase is not a matched retention ablation. Preserve
its original negative/interference evidence and report attempted and retained
updates separately. Repeated transfer specimens measure changes on that panel;
training-exposure overlap remains NOT_MEASURED and they never grant admission.


## ADR-078 | 2026-10-21 | Preserve routine history and refresh exact-parent frontier evidence

The live autonomous control retained a PARENT update at step118064, then the next
trial failed FIXED_FRONTIER_PARENT_IDENTITY_DRIFT: a durable mid-cycle flush had
advanced the student while last_exam still described step118048. Exact-parent
validation correctly contained stale evidence. Preserve that validation.

Retain last_exam as routine/diagnostic history. A separate fixed_frontier_exam
measures the current retained parent on the unchanged verified source cohort.
Validate the historical cohort, scores and misses first; then score actual current
parent predictions and require native AdamW step agreement. Bind the refreshed
pointer to the same cohort, rubric, scope, assessment grade and epoch. Persist its
zero-update receipt atomically with the stop boundary, and repair older stopped
issue state through the same measurement on resume. A newly committed routine
exam replaces this derived pointer. Refreshes grant no graduation, title, source
admission or diagnostic-history authority. Never copy historical predictions into
a changed parent. PM-2026-10-20-003 / RC-116 records the live failure and controls.

Restart also exposed a metadata publication defect: an autonomy queue reroute
inherited the prior generation's sealed outbox. Metadata-only _advance now
reconciles prior delivery, publishes its own generation-bound event and reads it
back. It never rehashes old teaching as new evidence. The issue-owned control
was repaired by matching immutable generations61/62 (only generation and queue
differed), verifying every inherited event exactly once in the ledger and the
unchanged native student/AdamW, then appending generation63. Historical snapshots
and events remain intact. The repair receipt is tracked separately.


## ADR-079 | 2026-10-22 | Protected candidate loss budgets scale with measured evidence

The live Prometheus run exposed a dimensional error in candidate retention. A retained `C.NUMBER` update improved its target by nine paired answers while degrading `C.COUNT` by six; later recovery repeatedly found candidates that improved `C.COUNT` but were classified against a raw one-answer protected-loss budget even when the protected capability was measured on a 33-question panel. The human rejected both extremes: neither unrestricted aggregate cannibalization nor a fixed one-answer veto matches the intended tradeoff. A two-answer loss must not automatically discard a substantially larger gain merely because the cohort is larger.

The configured loss counts are therefore reference-probe budgets, not absolute ceilings. For every protected capability, scale the applicable reference loss by that capability's actual paired-question total: `floor(actual_total * reference_loss / probe_each)`. Mature grades use `mature_max_loss`; non-mature MAIN instruction uses `mature_max_loss + introduction_extra_loss`; non-MAIN recovery uses `mature_max_loss`. With the current default recovery budget of 1 loss per 6 reference questions, a 33-question protected panel permits 5 losses. Thus a `+9 / -2` trade remains eligible, while the observed `+9 / -6` concentrated regression exceeds the proportional budget.

This proportional capability guard is additive to, not a replacement for, ADR-057's aggregate controls. The target fresh probe must improve, the fresh lesson grade must not regress in the late-stage regime, and fixed lesson-grade, active-school-grade and whole-school totals must remain non-regressing when the exact-parent fixed frontier is measurable. Individual rows may move and capabilities may trade bounded error mass, but any protected capability that exceeds its proportional budget rejects the candidate with `PROTECTED_CAPABILITY_REGRESSION` in both pre-frontier and late-stage evidence regimes. Late-stage B.OR/B.XOR item flips remain diagnostic-only.

This supersedes ADR-057 and SPEC-0003 only where they made protected-capability over-budget loss diagnostic-only after fixed-frontier admission. It does not roll back the live student, alter graduation/championship authority, weaken source-gold requirements, or authorize agent-owned neural training. The preserved current student and own AdamW recover forward under the corrected admission rule.

## ADR-080 | 2026-10-22 | Repeated no-target-gain trials must lose teacher-selection priority

The live Prometheus run showed hundreds of rejected visits with `NO_MEASURABLE_TARGET_GAIN`. Retention already sent each rejection to the inherited strategy bandit as `teacher_selection_reward=-0.05`, but the contextual UCB exploration term could still dominate that flat negative mean and repeatedly select the same policy. The human requires useless strategies to receive a small but effective negative incentive rather than remain neutral in practice.

**Amended by direct user approval on 2026-10-22 after live-scale audit.** The original additive `0.05 * phase-local streak` mechanism is empirically inadequate and is superseded prospectively. Do not replace it with a larger arbitrary coefficient.

Contextual ranking MUST use the same `0.6` UCB exploration scale as the inherited teacher. Keep phase-specific contextual outcome statistics, but maintain an additional consecutive no-target-gain debt keyed by **capability + curriculum scope + policy**, independent of MAIN / RECOVERY_1 / RECOVERY_2. Scheduler phase rotation MUST NOT erase that debt. Historical phase-local statistics remain immutable evidence; the shared debt begins prospectively when this amendment is first executed.

Repeated no-target-gain evidence MUST consume exploration privilege structurally: contextual exploration is divided by `1 + shared_no_target_gain_streak` rather than offset by another fixed penalty. A trial with `NO_MEASURABLE_TARGET_GAIN` must also send the inherited strategy bandit forward-only negative selection credit at least as large in magnitude as the inherited UCB exploration contribution that justified another trial, while preserving any stronger measured retention/interference penalty. This prevents the base bandit from immediately resurrecting a repeatedly useless policy merely because exploration dominates a flat `-0.05` mean.

Any later trial that produces measurable target gain resets the shared no-target-gain debt immediately, including a candidate later rejected for a different retention reason. Phase-local diagnostic streaks retain their existing reset behavior. This is selection evidence only: it is not a neural update, quarantine, permanent strategy ban, historical-statistics rewrite, or license to suppress all future exploration. Untried policies remain explorable and previously stagnant policies may naturally regain eligibility after real gain.

## ADR-081 | 2026-10-22 | Workstation-shared immutable state data plane

The Prometheus human run exposed a structural storage failure: the mutable `state.json` resume receipt had accumulated archival championship history, complete unresolved teaching rows, exposure maps, mentor ledgers and other audit evidence until one current receipt reached roughly 128 MB, while full-copy immutable generations consumed roughly 88 GB. Resume then traversed the embedded historical checkpoint graph and repeatedly SHA-256 verified immutable model/soup payloads, creating multi-minute silent startup latency. Compression of superseded JSON snapshots reduced disk pressure but preserved the defective full-copy state model.

School state now uses a persistent Merkle DAG backed by one workstation-shared SQLite/WAL data plane. Run directories retain tiny durable `state.json` and `states/<generation>.json` pointers. Each immutable DAG node names its parent and content-addressed field references. Unchanged fields share objects across generations and runs. Large `teacher_misses` collections are sharded by capability, miss-exposure maps by specimen-ID prefix, and championship epoch history stores content-addressed epoch references rather than recursively embedding history into every new generation. The field-reference manifest is the receipt identity; no legacy hash over a reconstructed monolith is required on each commit.

The data plane is durable user data, not an expendable cache. It defaults to the OS user's application-data location and may be overridden explicitly with `BILQIS_DATA_PLANE`. SQLite uses WAL, full synchronous durability, concurrent readers and content-addressed idempotent inserts so every local Bilqis process shares the same immutable object store without requiring Docker or a daemon. The run's tiny pointer files remain the authoritative mutable head/generation publication boundary. Legacy monolithic current heads remain readable and migrate only under the exclusive human-operator lock; immutable historical legacy snapshots remain readable during migration.

The same data plane owns a workstation-local integrity-proof cache for immutable model and soup files. A successful SHA-256 proof is reusable only while path, expected digest, device, inode, byte size, mtime and ctime are unchanged. Any identity/stat change forces a real rehash; explicit deep verification may always bypass the cache. This removes repeated multi-gigabyte hashing from ordinary resume without weakening detection of normal artifact mutation.

## ADR-082 | 2026-10-22 | Keep archival state and tensors off the hot training path

The first live Prometheus run after ADR-081 proved that deduplicating durable storage is insufficient when ordinary training still reconstructs or rewrites large historical structures. The current runtime therefore treats the Merkle data plane as an addressable database, not as a monolithic JSON surrogate. Hot consumers must read only the logical fields they require; archival championship history must not be materialized merely to refresh presentation state. `teacher_misses` must be subsharded below capability granularity so one changed specimen does not rewrite multi-megabyte unrelated miss lists. Old state-DAG encodings remain readable.

The append-only `events.jsonl` remains the human-readable audit authority, but it is not a query engine. Event delivery and reconciliation use the workstation-shared data plane's per-run event index for event-ID membership, exact payload identity and duplicate counts. The index tracks the durable byte offset already consumed and indexes only the unseen ledger tail; inode replacement, truncation or same-size mutation invalidates that cursor and rebuilds it from the source ledger. A missing or stale index may cost one source scan, never a repeated full-history scan on every generation.

Model bundles, frozen soups and assessment cohorts have separate logical identity from their physical storage. Active training keeps only the artifacts required by current teaching, assessment, rollback and custody checks in its hot namespace. Historical bytes may be moved into workstation-shared content-addressed archival storage and hydrated on explicit historical replay, provided every existing logical pointer, digest, optimizer identity and exact readback remains valid. Do not delete historical evidence merely because it is cold, and do not require hundreds of obsolete tensor/JSON artifacts to remain physically duplicated inside one run directory.

This supersedes prior operational language only where `state.json` and every `states/<generation>.json` were required to contain full logical receipts. Their authority is preserved as immutable DAG pointers to the exact logical state. The event ledger, checkpoint/AdamW ownership, outbox crash semantics, source evidence and human-only neural-update boundary are unchanged.


## ADR-083 | 2026-10-22 | Weakness chooses what to teach; teacher policy chooses how

**Direct user approval after live Prometheus evidence.** Capability-level recovery already selects weak capabilities, but the lesson path still treated source-verified unresolved semantic misses as an incidental replay obligation after generic lesson selection. Live C.NUMBER evidence showed that, after semantic miss deduplication, one current unresolved target could receive zero or one appearances across a 16-step teaching visit while hundreds of generic examples were optimized around it. This violates the intended no-starvation contract even though the capability itself was correctly selected as weak.

Teaching is therefore explicitly two-stage. **Weakness selection owns WHAT to teach.** Fresh source-scored unresolved semantic misses for the selected capability are first-class teaching targets. **Teacher policy owns HOW to teach those targets.** Strategy dimensions such as old-grade rehearsal, contrast, depth, learning rate and champion/distillation guidance may shape the surrounding lesson, but they may not displace all direct exposure to the active weak semantics.

For every optimizer batch in a visit, reserve source-grounded target slots before generic current-capability and old-grade material is filled. The reservation size is derived from the number of unresolved semantic targets and the available current-capability capacity; there is no fixed replay percentage or arbitrary quota. When all active targets fit, each target remains eligible on every optimizer step until later source-scored evidence shows it correct. When active targets exceed available target slots, rotate fairly by durable exposure count so the least-exposed targets are selected first. A target being selected earlier in the same visit does **not** make it ineligible later in that visit.

The remaining batch continues to provide source-grounded current-capability variation, prerequisite/old-grade retention material, structural preservation and any other already-governed support evidence. Direct target exposure must never synthesize golds, leak an unscored examination before scoring completes, weaken candidate-retention gates, or permit a rejected candidate to mutate the causal student/AdamW. Once a target is corrected by authoritative reassessment/reconciliation it leaves the unresolved-target set naturally; no permanent memorization list is created.

## ADR-084 | 2026-10-22 | Stable grade mean above 90% automatically opens the next tier

**Direct user approval, clarified in the same session.** A staged grade must not remain trapped behind one imperfect semantic when the grade-wide representation is already strong and stable. Promotion eligibility is therefore based on the **mean score across the complete currently introduced semantic set for that grade**, not on every individual semantic exceeding the threshold. An individual semantic may score below 90%. For example, `100, 100, 100, 85` is eligible because the grade mean remains above the floor.

A fresh complete assessment whose current-grade mean is **strictly greater than 90%** starts one automatic promotion sweep. The sweep visits every currently introduced semantic in that grade exactly once in canonical order. After **each** semantic visit, the runtime performs a fresh authoritative assessment of the complete currently introduced grade and recomputes the grade mean from that whole fresh snapshot. No stale score from an earlier sweep step may substitute for a freshly measured semantic score. The **fresh whole-grade mean must never fall below 90%**. Equality at exactly 90% is allowed; only a mean below 90% aborts the sweep.

If the running grade mean falls below 90% at any point, the promotion sweep ends immediately and the scheduler returns to the ordinary MAIN / weakest-three recovery routine with no tier advancement and no fabricated mastery. A later fresh assessment above 90% may start another promotion sweep.

If the sweep completes every currently introduced semantic without the grade mean falling below 90%, advance exactly one curriculum tier immediately. For a staged grade this opens the next semantic stage. At the last semantic stage it crosses the ordinary next-grade boundary. Promotion is **not mastery**: any capability that is not perfect remains explicit mastery debt and must continue to participate in cumulative assessment, targeted teaching, retention protection and later recovery. The sweep must never mint a grade champion, perfect score, or historical mastery claim from a merely >=90% mean.

This policy is automatic for every operator and Codex path using the canonical scheduler; it is not a run-local flag or human-only exception. It supersedes earlier staged-grade progression language only where 100% current-stage mastery was the sole prerequisite for opening the next semantic or grade, and supersedes ADR-074 only where that ADR required **explicit human authorization** before carrying mastery debt into the next grade. ADR-074's truth-preserving debt semantics remain binding. Perfect mastery remains the authority for championship, debt clearance and final whole-school mastery.

## ADR-085 | 2026-10-22 | Imperfect earlier grades receive teaching passes during staged later-grade instruction

**Direct user correction:** advancing to C with unfinished B semantics does not mean B can be left as permanent assessment-only debt. At the observed C.ADD/C.SUB frontier, B.AND, B.IFF, and B.COMPOSITE remained explicitly carried as mastery debt and continued to receive cumulative examination scores, but no direct B teaching passes were scheduled. The active prior-grade mean was roughly 64.6%. This was not an intentional waiver of B mastery.

The scheduler had three overlapping frontier monopolies: a partially introduced staged C grade could not yield its ordinary MAIN sequence to an earlier grade; both ordinary continuation and recovery resumption could force a return to the newest C frontier whenever it was imperfect; and the weakest-three instructional pool could filter out imperfect B simply because unfinished C existed. These are inconsistent with ADR-061's full imperfect-grade passes between bounded global recovery rounds.

**Decision:** after each complete ordinary MAIN pass over the currently introduced semantic stage, rotate through every other imperfect eligible admitted grade before running the two global weakest-three recovery rounds, even if a later grade has additional stages still to introduce. Record and retain each grade's introduction frontier so returning to C resumes its current stage without silently resetting or teaching future concepts. Recovery ranks the complete currently eligible cumulative pool, including earlier-grade debt, rather than hiding B behind a frontier-only filter. A qualifying ADR-084 promotion sweep remains uninterrupted and retains its strictly >90% trigger, fresh full-grade mean check after each semantic, and >=90% continuation floor. No grade champion or debt clearance is inferred from cross-grade visits.

**Source/exam safety:** when the active teaching grade changes, assessment eligibility for every represented staged grade follows that grade's own introduced stage or existing full-grade champion. Never test C.SUCCESSOR, C.ADD, or C.SUB merely because B is the current teaching grade when those C semantics have not yet been introduced. Explicit quarantine/withheld semantics and human-only causal student/AdamW ownership are unchanged.

This supersedes the prior newest-frontier instruction monopoly, including the assumption that a partially introduced later grade cannot participate in a cross-grade teaching spiral. It retains staged prerequisite ordering and the invariant that mastery debt is not graduation. The existing normal grade-rotation cadence supplies fairness; there is no new fixed B lesson percentage or invented number of visits.

## ADR-086 | 2026-10-22 | Grade B stagnation is diagnostic, never an exit actuator

**Direct user correction following a human-run stagnation review stop.** Grade B is still developmental learning territory. Incomplete or repeatedly unsuccessful B semantics must be revisited and taught, not treated as a reason to withhold instruction or end a training command. This applies automatically to all B semantics in the canonical trainer for every operator and Codex execution path, including after any finite historical grade-B grace budget expires.

The per-command stagnation controller continues to measure B scores, consecutive rejected recovery visits, lack of retained progress, source-grounded warnings, and unqualified mastery debt. However, after the normal two-round and time-window checks, a B capability **can only emit diagnostic evidence**. It may not enter the quarantined set, create a WITHHELD_FOR_REMAINDER_OF_SESSION alert, reduce the eligible teaching pool, or cause DEFERRED_STAGNATION / STAGNATION_REVIEW_REQUIRED. Record the distinction with suppression_reason=GRADE_B_DEVELOPMENTAL_LEARNING. Prior B failures remain unresolved; no perfect result, championship, score improvement, or promotion is manufactured. ADR-085's ordinary cross-grade teaching circuit keeps B receiving real lessons as other grades advance.

This exemption is specific to B. A different grade, including C, may still activate the existing repeated-recovery stagnation containment when its independent evidence supports it. A C quarantine must not stop the run while unquarantined B lessons remain eligible; the cumulative grade scheduler returns to B. Normal human-invoked time/visit/disk limits and student/AdamW retention safeguards remain intact. Historical alerts describing older B withhold decisions are provenance and must not be rewritten. Earlier optional finite Grade-B stagnation grace remains a readable historical setting but is not the authority for this unconditional B policy.

<!-- Incoming ADR-083–086 retain trunk identities. The two feature decisions below
were originally ADR-083/084 at b73f47e; canonical IDs reconciled without changing
their decisions. Historical receipts retain their original source-local references. -->

## ADR-087 | 2026-10-22 | Teach new concepts explicitly from understood foundations

**Authority:** direct user correction in the active issue349 conversation. The
user states: “We are not building tiny world models at this stage” and asks for
“a narrow staircase built exclusively upon its foundations.” The intended course
is logic and basic cognitive algebra, leading to mathematics and subsequently
physics with selective concepts from Lexicon Chapters 2, 3 and 6.

**Observed drift:** the issue experiment taught occurrence as the after Boolean,
commencement as NOT-before AND-after, and termination as before AND-NOT-after,
inside named event lists. The model saw encoded records and answer labels, not
an explicit construction through understood Boolean constituents. The declared
A.IDENTITY → occurrence → commencement → termination chain did not establish
Boolean or temporal prerequisites. Query contrasts and more events increased
record-processing demands without supplying the missing conceptual explanation.
Source-checked answers did not establish developmental suitability.

**Decision:** teach a positive definition through previously understood operands
and operations. Each step must make the constituent construction visible in its
instructional examples and check that same small meaning. Prerequisite metadata
alone is insufficient. Do not introduce temporal worlds, event identities or
physical interpretations before their constituent concepts are available. Extra
world size is not the current success criterion. This supersedes event-first
sequencing and Chapter-1/2-first or fixed D–O ordering as next-step authority;
historical prose and source records remain preserved.

**Immediate selection:** use the existing registered A-only `primary` lineage for
foundation repair (A.IDENTITY, A.PARENT, A.LINK, A.MEMBER, A.EDGE, A.MAPS), with
current-checkpoint observations guiding the actual targets. Next new learning is
a thin profile of canonical B: B.NOT followed by B.AND over understood A
propositions, using existing source/oracle/teacher/runtime owners. Check the
actual provider's constituent presentation before adoption; do not assume that
this selection has already taught a concept. The event-trained `plasticity-control`
stays stopped with its A+D release and debt intact. Do not reset it, remove its
vocabulary, erase debt or claim that a normal resume follows this new selection.

After logical foundations, use the existing numeric staircase COUNT → NUMBER →
SUCCESSOR → ADD → SUB, initially 0..3 and capped at 4 in present issue trials.
Broader algebraic and physical concepts are selected only as their ingredients
become available, not by chapter order. No filler grade, new qualification
framework, mandatory immediate transfer result, or automatic perfect-school gate
is added. Existing explicit debt-admission rules remain available; future
concepts may use only foundations actually understood by the learner.

**Custody and evidence:** preserve both registered runs, their own AdamW, frozen
releases and historical results. Exactly two issue-owned experiments remain the
limit; no third lineage, canonical mutation or optimizer merge is authorized.
This decision selects future work; it does not graduate A/B, admit a replacement D,
or establish understanding of any Ithkuil root. Selection drift is filed and
read-back verified as PM-2026-10-22-005, reusing RC-047/RC-096 and PAT-076. The
previous PM-2026-10-20-003 / RC-116 covers separate runtime migration defects.


## ADR-088 | 2026-10-22 | Introduce Boolean concepts without blocking designed numeric progression

The user explicitly directs continuation while noting that NOT and AND have
proved difficult to master: they may be introduced, but must not become
prerequisites for moving to Grade C as designed. This refines ADR-087; it does
not restore event-world training.

C.COUNT depends on A.IDENTITY/A.MEMBER; subsequent numeric capabilities retain
their existing count/number/successor/arithmetic dependencies. Do not add Boolean
mastery to those definitions or wait for cumulative A/B perfection before this
user-authorized C admission. Use the existing exact-checkpoint complete-boundary
measurement and explicit debt-carry admission, preserving all unresolved A/B
capabilities, the causal student and its own AdamW. Opening C does not graduate B.

Continue with bounded foundation/Boolean introductions, then open the designed
C foundation sequence at 0..3, capped at4 for this issue. This is a progression
decision, not a new automatic timeout or lesson quota. Keep ordinary source,
factory, retention, teacher, vocabulary and cumulative assessment owners.


ADR-088 execution readback: the issue-owned primary admitted A→thin B→C through
complete source-scored debt boundaries, with no admission optimizer updates.
NOT/AND remained imperfect. Subsequent0..3 COUNT teaching retained192 updates;
the preserved pre-teaching checkpoint scored69/180 on the same seeded panel,
versus154/180 afterward (numeric15/60→56/60; equality views54/120→98/120).
This is bounded task learning, not unexposed generalization or grade mastery.
Exact custody, failed-first cohort-schema repair and remaining storage-test debt
are in HANDOFF.md and the20261022 foundations-through-counting receipt.

## ADR-089 | 2026-10-23 | Cross-grade debt visits protect the developmental frontier without freezing local learning

ADR-085 made earlier imperfect grades first-class teaching stops during a later
staged grade. That scheduler correction changed the meaning of the current
school grade from a stable developmental-frontier identity into the grade
currently receiving instruction. ADR-057 retention still treated that temporary
teaching grade as the protected school frontier. In the live Prometheus run, a
retained B.COMPOSITE candidate therefore improved fixed B by +10 while fixed C
fell by -10, tied the whole-school total, and was admitted.

**Decision:** preserve ADR-057's aggregate plasticity. Individual fixed rows and
capabilities may still trade bounded error mass, and earlier-grade debt remains
teachable. During cross-grade rotation, however, the protected aggregate
frontier is the latest admitted grade, not merely the temporary lesson grade.
The fixed lesson grade, latest admitted developmental-frontier grade, and
whole-school total must each remain non-regressing when the exact-parent fixed
frontier is measurable. Existing proportional protected-capability budgets
remain unchanged. This is deliberately not item-level monotonicity and does not
make historical best or title scores admission gates.

Telemetry must also stop presenting unlike score roles under one TOP label.
Candidate panels label championship evidence as CHP; mastery panels retain
TOP for historical-best evidence. WAS and NOW remain the directly paired same-probe
values inside a candidate row. Cross-cohort title or best evidence remains useful
context but is not represented as a comparable maximum.

Mastery TOP remains intentionally cross-cohort context within one developmental
score era. Ordinary fresh cohort rotation does not reset it. Admitting the next
grade or replacing the active semantic program starts a new score era, clears
the active TOP/cumulative-best projection, and leaves the immutable historical
events intact. Operator telemetry names the era, cohort count, and the fact that
TOP is cross-cohort context rather than a paired delta.

## ADR-090 | 2026-10-23 | C progression owns at least 80% of candidate work while B is nongating debt

**Direct user correction after live Prometheus evidence.** Grade B remains
developmental mastery debt and must continue receiving occasional instruction,
but the currently admitted B capabilities are explicitly not prerequisites for
opening the next C semantic stages. They therefore may not dominate the
candidate/retention-probe budget while C is the active progression frontier.

While C is the latest active grade and both unfinished B debt and unfinished C
progression debt remain, C owns the primary learning lane. B may consume **no
more than one candidate visit in five (20%)** from the start of this policy
epoch. Four C visits must accrue before each supplemental B visit becomes
eligible. The budget is prefix-safe rather than an eventual average, so a short
window cannot begin with a burst of B work and claim later compensation.

This cap applies to the candidate-level training and paired retention-testing
work induced by those visits. Routine cumulative assessment may continue to
measure B as explicit debt, provided B does not become the scheduling actuator
for C progression; in the observed A+B+C rubric B already accounts for less
than 20% of scored exam rows. Promotion sweeps remain C-only progression
authority. B debt is neither forgiven nor marked mastered, and its scores,
mistakes and eventual bounded supplemental visits remain durable evidence.

This supersedes ADR-085 only where that decision required every imperfect
earlier grade to receive a full ordinary MAIN pass during staged C instruction,
and supersedes ADR-086 only where unrestricted B fallback would exceed the 20%
budget when C is unavailable. B remains non-quarantining developmental debt;
once four frontier visits have earned one B visit, that visit may still occur.
Source-gold authority, candidate retention gates, student/AdamW custody,
stagnation evidence, and the C promotion criteria are unchanged.

## ADR-091 | 2026-10-23 | Weakness evidence biases fresh teaching; it does not replace the curriculum

**Repair decision from live candidate-retention evidence.** The teacher's
unresolved-miss ledger had conflated an exact generated specimen with a semantic
teaching target. Freshly seeded worlds, entity orderings and numeric
permutations therefore accumulated as thousands of nominally distinct misses.
Exact replay could consume every current-capability slot in an optimizer batch,
and visit-local teacher reward was measured on a cohort polluted by those same
historical replay rows. In the live C.COUNT case, 40 consecutive candidates
improved that mixed training score while every candidate worsened the fresh
target probe.

Exact failed rows remain immutable evidence in their scored exam/cohort
provenance. Active teaching debt is instead reconciled by a source-grounded
structural class. Boolean connective classes preserve truth pattern, operand
kind and universe structure; composite/identification classes preserve their
source-expression/operator structure; numeric classes preserve capability,
answer kind/gold, operation shape and witness geometry. Unknown providers fail
back to exact identity rather than receiving a guessed equivalence. A freshly
scored source-equivalent construction can therefore clear an older teaching
miss even when its exact generated row ID differs.

Weakness replay may bias a lesson but may not erase fresh current-capability
variation. With replay active, structured Boolean lessons retain fresh coverage
of their source truth patterns and typed lessons retain one complete fresh
source family. Historical replay rows remain eligible in the remaining
capacity. Teacher local-gain/selection reward is measured only on the newly
drawn source cohort, never on exact historical replay rows, so memorizing the
ledger cannot masquerade as fresh capability acquisition.

Candidate preservation is aligned with what the optimizer sees. A B debt lesson
under a C frontier receives rotating fresh C source support; a C lesson receives
rotating fresh non-target C sibling support. Support uses newly generated
source-oracled rows, never fixed exam rows, and preserves one complete source
family rather than inventing an arbitrary replay percentage. Existing fresh
target, same-grade, fixed-grade, protected-frontier and whole-school retention
gates remain unchanged. This repairs the training geometry that was producing
validly rejected destructive candidates rather than weakening admission to make
the retention percentage look healthier.


## ADR-092 | 2026-10-23 | Bilqis-MLX repository and implementation are public

**Direct user governance change.** `Entif-AI/bilqis-mlx` is now a public
repository and its implementation posture is public. Repository-owned source
code, tests, architecture, specifications, implementation notes, evidence, and
ordinary project handoffs may be published directly without compiling a separate
screened implementation projection. This supersedes the earlier private-
implementation posture recorded in historical ADRs and agent instructions.

Protected source authority remains a distinct boundary. `IPR-0220` and any other
still-private source repository, message, attachment, credential, or verbatim
private instruction remain protected unless the user separately releases that
source material. Public repository artifacts should cite such authority by an
opaque stable identifier when needed and must not require or reproduce a private
repository URL. Public implementation derived from protected requirements is
permitted; protected source text is not thereby declassified.

Going forward, publication classification for ordinary Bilqis-MLX repository
work is **public by default**. A private/split classification is required only
when the artifact itself contains still-protected source material or another
independently private datum. This change does not alter human-only neural-update
authority, student/AdamW custody, source-truth requirements, or historical
provenance.


## ADR-093 | 2026-10-23 | Promotion sweeps update one semantic at a time

**Direct user correction of ADR-084's sweep interpretation.** The >90% trigger
remains a fresh complete assessment of the currently introduced active grade,
but that assessment also freezes the initial score vector for the promotion
sweep. The sweep then revisits each introduced semantic exactly once in canonical
order. After a semantic visit, only that semantic receives a fresh authoritative
score in the running sweep vector. Unswept semantics retain their score from the
triggering vector, and already swept semantics retain their most recent sweep
score.

The running grade mean is recomputed after each replacement. A mean of at least
90% continues the sweep; a mean below 90% aborts it. This means a semantic may
individually remain below 90% so long as the grade mean stays at or above the
floor. A rejected candidate with zero retained optimizer updates must not appear
to regress unrelated semantics merely because a new whole-grade cohort happened
to be harder. Fresh cumulative exams remain truthful evidence and may still be
recorded, but unrelated fresh-cohort variance does not overwrite unswept entries
inside the promotion-sweep decision vector.

Completing the sweep still opens exactly one next semantic stage or grade and
carries every imperfect semantic as mastery debt. It does not mint a champion,
clear debt, or fabricate mastery. This ADR supersedes ADR-084 and the ADR-085
cross-reference only for how scores are updated *during* a promotion sweep; the
strict >90% trigger, canonical one-pass order, >=90% continuation floor, staged
progression, cumulative evidence, and human-only neural custody remain unchanged.


## ADR-094 | 2026-10-23 | Nongating Grade B receives bounded complete training turns

**Direct user correction after continued Prometheus starvation.** ADR-090 solved a
real failure mode, namely Grade B consuming most of the run while C was the actual
progression frontier, but it bounded the wrong unit. Its one-B-candidate-per-five
candidate-visits rule gave B only isolated crumbs. Because the scheduler always
selected the weakest eligible B capability, `B.IDBOOLOPS` could repeatedly consume
those crumbs while the rest of the admitted Boolean grade received little or no
direct instruction. At generation 27187 all eight admitted B capabilities were
imperfect and the fresh cumulative B score was 51/96 (53.1%), so treating one weak
capability visit as an adequate Grade-B turn was not serving the developmental debt.

While C is the latest active progression grade and both unfinished B debt and
unfinished C debt remain, scheduling fairness is measured in **grade training
turns**, not candidate-capability visits. A training turn is one scheduled teaching
queue that reaches its assessment boundary. After **no more than four completed
non-B training turns**, B becomes due for one contiguous `MAIN` pass over **every
currently imperfect, admitted, eligible B capability** in canonical B order. A
temporarily perfect B capability need not be retrained merely to pad the pass. If an
otherwise imperfect B capability is explicitly withheld, it remains debt and is
not synthesized into the runnable queue.

Completing that B pass resets the cadence. B may not receive another ordinary
training pass until four additional non-B turns complete. C-frontier weakest-three
recovery is therefore C-only; it must not smuggle a single weakest B capability into
the recovery queue. This produces a hard anti-monopoly boundary at the grade-turn
level while still giving weak B semantics enough contiguous training time to learn.
The number of candidate visits inside a B pass may exceed ADR-090's former 20%
candidate-share ceiling because a full grade pass intentionally contains multiple
capabilities. ADR-090 is superseded on that allocation metric.

This cadence does **not** make B a promotion gate, C prerequisite, championship
shortcut, stagnation actuator, or permission to weaken retention/source-gold
requirements. Promotion sweeps remain owned by the active progression grade. B
scores, misses and mastery debt remain cumulative evidence. Existing pre-ADR-094
receipts migrate neural-inertly with one B pass due at the next safe assessment
boundary, avoiding another starvation epoch without rewriting historical visits or
claiming neural progress.


## ADR-095 | 2026-10-23 | Factory micro-specs decompose reusable mechanics, not semantic roots

**Direct user correction for issue #150 execution.** The factory/runway work is
primarily about making the curriculum factory capable of handling whatever future
source-qualified semantic roots are admitted through its typed contracts. The
micro-spec corpus MUST therefore decompose reusable factory invariants, ownership
boundaries, migrations, compatibility boundaries and proofs. It MUST NOT create a
specification or GitHub issue for every prospective semantic root merely because
that root may be taught later.

A particular root belongs in #150 only when it exposes a missing reusable factory
primitive or is required as a bounded conformance fixture. Curriculum selection,
root sourcing and future grade composition remain separately governed work. This
keeps #150 focused on the architecture originally intended from the beginning: one
generic factory through which later semantics become declarative inputs rather than
new implementation families.

## ADR-096 | 2026-10-25 | Conjoined Triangle authority, immutable identity and projection boundaries

**Direct user decision.** The Bilqis semantic corpus, curriculum factory, Akasha and Mission Control must converge without collapsing their authority boundaries. State transitions should follow functional, append-only semantics wherever practical: a correction or revision creates a new immutable artifact, event, receipt or projection version. Historical evidence is never rewritten to make current state look cleaner.

### Semantic authority and Rosetta boundary

The canonical New Ithkuil relational IR and its deterministic SKOS/RDF release own the meaning of Bilqis semantic primitives and their ontology relationships. SKOS is the dictionary. It does not own trainer mechanics, process execution, learner state or operational policy.

Rosetta is the narrow waist for representing and communicating meaning, process evidence and protocol relationships. It must not presume implementation mechanics, choose policies, express opinions, or turn an external vocabulary into Rosetta core semantics. The Bilqis SKOS corpus integrates through a governed Rosetta VocabPack with stable anchors. Standards such as OWL 2, SHACL and SPARQL may be used through packs, validators or projections where their own contracts apply. They do not expand Rosetta core by convenience. Rosetta core process semantics describe interoperable protocol artifacts and update propagation, not the internal algorithms of surrounding Entif projects.

The source vocabulary, Rosetta representation and executable implementation therefore remain separate authorities. A source term can retain one stable semantic identity across many implementation revisions.

### Identity taxonomy and provider attestation

Semantic identity MUST NOT depend on provider implementation bytes.

A stable semantic identity names what a concept or semantic contract means. An immutable semantic release digest identifies the exact released semantic content. A provider implementation has its own independently versioned implementation identity or digest. An admission receipt binds the semantic identity/release, provider implementation identity, applicable proof evidence and admitted runtime target.

A semantics-preserving provider refactor may change the provider implementation digest without changing semantic identity. A semantic change requires a new semantic release identity/version. Historical admission receipts remain immutable and continue to attest the exact semantic and implementation identities that existed when they were issued.

Cross-system contracts must use explicit identity classes rather than an ambiguous generic `id` where confusion is possible. The intended classes include stable semantic identity, exact content/release digest, external source anchor, provider implementation digest, run identity, checkpoint identity, projection identity and receipt identity.

### Akasha domain and projection model

Akasha is a governed data plane and query substrate, not a semantic source of truth. Its initial deployment may be physically consolidated, but its domains are logically federated. Semantic projection, learner evidence, factory/release state, training/run history, receipts/provenance and program/operational state remain distinct namespaces with explicit owners and mutation laws.

Derived Akasha projections must be disposable. Deleting a derived projection must not destroy canonical meaning or historical evidence. The system must be able to rebuild it from canonical immutable releases, artifacts, events and receipts.

Learner evidence is immutable event history. Corrections, disputes and later evaluations append new evidence or superseding relationships rather than overwriting prior observations. "Current mastery", confidence, fragility, debt and similar learner-state values are projections over that history, not mutable canonical facts.

### Curriculum admission state

Source availability does not imply curriculum admission. The normal progression is:

`SOURCE_AVAILABLE -> SEMANTICALLY_MAPPED -> CURRICULUM_CANDIDATE -> FACTORY_VALIDATED -> QUALIFIED -> STAGED -> ADMITTED`.

Automation may advance deterministic and evidence-backed stages through `STAGED`. `ADMITTED` remains an explicit human-authority transition unless a later ADR changes that boundary. Parsing, mapping, materializing or validating a semantic source must never silently authorize neural training.

Every cross-leg artifact must name the semantic/factory release it expects. Stale or mismatched identity fails explicitly. Implementations must not silently substitute "latest", guess a translation or repair identity drift by convenience.

### Integration and Mission Control

PR-level completion is not holistic qualification. Each implementation payload must first qualify independently. Exact qualified heads are then combined into an ephemeral integration candidate. Cross-boundary tests and one reproducible qualification receipt govern merge readiness. The tested combination, or a sequence proven equivalent to it, is the merge authority.

Mission Control begins as a read-only control plane over durable sources and projections. It must not become semantic, learner-evidence, factory or receipt authority through UI convenience. Operator status distinguishes at least implemented, turned in, individually qualified, integrated, launch qualified, blocked and superseded. These states must derive from their owning evidence rather than a generic mutable `done` flag.

The Conjoined Triangle tracker is temporary. Mission Control replaces bespoke project trackers only after the same Program, WorkItem, Dependency, Gate, Evidence, Risk, Decision and Notification model can onboard a second non-Bilqis project without a core schema fork or another spreadsheet.

### Write-admission boundary reserved for follow-up

The user agrees with the core direction that canonical mutations must pass through governed authority and that Mission Control or arbitrary workers must not write source meaning or canonical evidence directly. The detailed information-flow model, including writer topology, command brokering, authorization stages and propagation mechanics, is intentionally **not frozen by this ADR**. That design remains open for the next architecture discussion. Future implementation must not infer a more specific write topology from this ADR.

## ADR-097 | 2026-10-27 | Suspend developmental generalization until explicit maturity admission

**Direct user correction; supersedes the active-generalization portions of ADR-067 and SPEC-0001 as they existed before this decision.** Bilqis is currently a small developmental student learning a narrow semantic inventory. Fresh GENERALIZATION assessment is not appropriate as a routine, promotion-adjacent, or graduation-gating mechanism at this stage and must not be inferred from ordinary LLM evaluation practice.

The active developmental assessment lifecycle is therefore **fresh routine measurement plus fixed-within-attempt promotion**. The live runtime MUST NOT automatically generate fresh generalization cohorts, require generalization evidence for grade or whole-school graduation, inject generalization-only misses into teacher priorities, or mix generalization scores into routine/promotion longitudinal telemetry. Historical generalization cohorts, burn ledgers, readers, enums, and research fixtures remain preserved as compatibility evidence. They are not current execution authority.

Promotion authority is also narrowed structurally. Ordinary recovery, debt, spiral, or grade/stage movement does not open promotion. A promotion attempt may be created only when the scheduler records an actual qualification transition by advancing `grade_exam_epoch` after a complete assessment. This prevents recovery movement from manufacturing promotion/generalization work for an imperfect grade.

Generalization may return only through a future explicit human-directed maturity decision that defines when the student's semantic base is sufficiently stable, what kind of transfer/invariance is pedagogically appropriate, how the evidence is scored, and whether it can affect training or graduation. Until then, "generalization" is a dormant research/compatibility capability, not part of the school.


## ADR-098 | 2026-10-27 | Candidate retention protects the current parent, not an older cumulative peak

**SUPERSEDED by ADR-099.** This intermediate repair narrowed the diagnosed fault
to the historical retention anchor, but the subsequent exact-control experiment
showed that the correct operational recovery is to excise commit `1324082`
wholesale rather than retain selected mechanics from it.

**Direct user correction after the step-127096 retention deadlock.** The mature-grade anti-ratchet introduced on 2026-10-27 correctly intended to prevent later-grade learning from spending already-earned Grade-A performance, but its immutable cumulative retention anchor was the wrong baseline for individual candidate admission. Once the retained student itself sat below that older peak, each later candidate was required both to improve its target and to repair historical debt back to the old peak in the same local optimizer update. The run then produced more than two thousand consecutive zero-retention visits despite hundreds of target-positive candidates.

Candidate admission therefore compares the challenger against the **current retained parent** on the current parent's verified fixed whole-school cohort. The current parent SHA and native AdamW optimizer step must match that frontier exactly or the screen fails closed. Fresh target gain remains mandatory. Same-grade, fixed lesson-grade, active developmental-frontier grade, mature-grade, protected-capability and whole-school non-regression remain mandatory relative to that current parent. In particular, a candidate that makes mature Grade A worse than the retained parent is still rejected; Grade A is not currency for later-grade gains.

Historical cumulative/high-water frontier receipts remain immutable provenance and may continue to inform recovery, debt analysis and diagnostics. They are not a second candidate parent and MUST NOT veto a challenger merely because the retained parent already carries older debt relative to them. Existing cumulative same-checkpoint mastery and promotion/graduation requirements remain unchanged; this ADR does not forgive debt, mint mastery, alter source-gold, weaken student/native-AdamW custody, or authorize agent-operated production training.

The correction is empirically bounded. From the exact live step-127096 student, a disposable clone using current compatible code with only the candidate-frontier baseline corrected retained a `B.COMPOSITE` candidate on the 22nd actual candidate attempt: target 9→10, same-grade net +1, fixed B 41→41, mature A 58→58, whole school 99→99, and 16 optimizer updates retained. The production lineage was not mutated by that proof.


## ADR-099 | 2026-10-27 | Excise commit 1324082 wholesale after exact-old retention control

**Direct user correction after bounded regression isolation.** Do not preserve a
selected subset of commit `13240828cd15612e9a84f0f6222484cf2e18cb96`
(`fix(trainer): prevent cumulative mature-grade regression`). The commit is to be
reverted as a unit while retaining later independent work whose mechanics exist
without it.

The decisive control used the exact parent commit
`5b84eca610f471630ee5c2fb27c15359a58f6766`, with its tracked tree unchanged.
Because that executable cannot legally resume the newer durable factory receipt,
a one-time disposable initializer loaded only the exact then-current neural
student and its own AdamW (`7ea07d9d...`, optimizer step `127096`) into a fresh
old-code school. Actual training then ran with the plain unmodified old CLI. In
30 teacher-candidate visits it retained 4 candidates and 64 optimizer updates,
for **13.33% retention**, advancing only the disposable control from step 127096
to 127160. This restored the healthy retention range the user reported from
before the regression.

Accordingly, all code introduced by `1324082` is removed. Later changes remain
when they are independently meaningful after that removal. In particular, the
same-student unretained-policy rotation, the later fresh retention-support
selection change, developmental GENERALIZATION suspension, recovery-custody
repair, dashboard corrections, and unrelated subsequent work remain. A later
patch whose sole purpose was to modify machinery introduced by `1324082` does
not require preserving that removed machinery.

Candidate retention therefore returns to the pre-`1324082` contract already
specified by ADR-054 through ADR-057 and ADR-079: strict source-oracled target
gain, same-grade and fixed-frontier safeguards, protected-capability budgets,
exact current-parent frontier identity, and intact student/native-AdamW custody.
This ADR does not authorize weaker source gold, custody bypass, hand-edited run
state, or agent-operated production training. The human operator owns the live
verification run after this code excision.

**Rollback compatibility for existing admitted releases.** A run admitted while
`1324082` was active may still contain the exact Grade-A predicates provider
descriptor introduced by that commit (`source.micro.predicates/v1`, implementation
`f8e5aec...`, including `generalization-only-source-context-v3`). After the
wholesale revert and ADR-100 developmental-presentation correction, the runtime
provider uses implementation `c451c3e...` without that generalization-only axis.
Resume may recognize exactly that one-way
descriptor pair as the ADR-099 rollback of the same provider. This is not a
general provider-drift exemption: any other adapter identity, hash, axis, oracle,
generator, release, teaching option, or profile difference still fails closed.


## ADR-100 | 2026-10-27 | Bounded mature-grade debt with active repair

**User-directed replacement for the failed cumulative anti-ratchet.** Later-grade
optimization may temporarily spend a small amount of already-graduated skill,
because requiring every local candidate to match an older historical peak made
the admissible region collapse. The opposite extreme is also unacceptable:
before the failed anti-ratchet, Grade-B optimization could slowly erode Grade A
for hours. Retention therefore needs a bounded memory budget plus an explicit
repair loop.

For every retained candidate with measured fixed-frontier evidence, mature debt
is updated from the **net fixed-grade delta** for each already-graduated grade.
A net loss of two A answers adds two units of `mature_grade_debt`; a later net
gain of three pays three units back, clamped at zero. Do not carry row-level or
capability-local debt across changing fixed cohorts: those identities are useful
diagnostics inside one parent-versus-candidate screen, but they are not a stable
cross-visit currency. This ledger is derived only from successive current-parent
comparisons. It does not compare a challenger to an older checkpoint and cannot
resurrect ADR-098's historical-anchor deadlock.

The initial control thresholds are deliberately small and inspectable. A mature
grade with at least **2** debt answers enters repair priority. Debt identifies
the grade that needs attention; it does **not** narrow training to only the
capabilities carrying debt. One repair turn is a complete ordinary same-grade
MAIN pass, restoring direct access to the whole grade's earned champion,
frozen-soup guidance, miss replay, and neighboring semantics. A mature grade may
receive at most one such repair pass in one school sweep before the scheduler
must yield to other eligible work. This prevents a stubborn debt item from
re-arming the same tiny queue indefinitely. A mature grade may carry at most
**4** debt answers without additional restriction. A candidate that would
increase that grade above 4 is rejected as `MATURE_GRADE_DEBT_LIMIT`. Holding or
reducing debt is allowed even when the ledger is already at or above the limit,
so repair is never blocked by the safeguard itself. The repair pressure releases
once debt falls below the 2-answer trigger.

Existing pre-ADR-100 runs decode with an empty prospective ledger. Runs produced
by the initial ADR-100 implementation may contain legacy per-capability debt;
resume migrates that ledger by summing each capability amount into its owning
grade, then clears the obsolete capability ledger. Do not invent additional
retroactive debt from fresh-cohort score differences.

Separately, ordinary developmental Grade-A presentation returns to plain
`draw_predicates()` rows. The source-valid contextual/irrelevant presentation is
retained as dormant research machinery rather than mixed into routine learning
or examination. This is the presentation separation that was useful inside
`1324082`, reintroduced independently under ADR-097 without restoring any of the
offending commit's retention mechanics.


## ADR-101 | 2026-10-27 | Exploration must mean novel teacher strategy

**User-directed correction after repeated zero-retention loops.** The dashboard
previously rendered `UNCERTAIN_EXPLORING` as `EXPLORE`, although that health state
only meant that an exact capability/phase/policy tuple had fewer than eight
observations. Meanwhile the contextual teacher's rejection-pressure exploration
path deliberately called `pick_existing()`, so it could repeatedly select known
policies while the UI claimed exploration. Historical evidence confirmed this:
in one 90-visit zero-retention streak, 58 nominal policy IDs represented 55
effective strategies, but several exact effective policies recurred four to
eight times and some capabilities repeated the same policy before trying a new
one.

`EXPLORE` is therefore reserved for an actual fresh mutation. Low-support policy
health renders as `UNCERTAIN`. On every fourth sustained rejection-pressure
attempt for a capability/context, the teacher now tries to mint one genuinely
novel **effective** strategy from the existing bounded knob vocabulary. Novelty
is checked against the effective strategy inventory, so preview-only or other
behaviorally equivalent aliases do not count as exploration. The existing
512-strategy archive ceiling, knob ranges, context-size limit, and bounded
mutation-attempt count remain authoritative. If the active engine does not
expose that bounded mutation vocabulary, selection falls back to the existing
non-mutating compatibility behavior.

Each visit records `teacher_selection_reason`; a genuinely minted policy uses
`FRESH_MUTATED_CHALLENGER`. This makes later forensic review able to distinguish
real search expansion from ordinary UCB rotation through the existing archive.


## ADR-102 | 2026-10-27 | Capability cooldown survives checkpoints without permanent exile

**Conservative response to repeated incumbent resurrection.** A strategy that is
locally exhausted must not become immediately eligible merely because some other
capability retained and changed the student SHA. Conversely, historically useful
strategies must not be permanently blacklisted because one student neighborhood
was hostile.

The existing same-student retirement remains the first line of defense: four
unretained attempts against one exact capability/phase/student checkpoint retire
that effective strategy for the current checkpoint. Durable capability cooldown
requires stronger evidence: the same effective strategy must independently hit
that same-student unretained limit on **two distinct student checkpoints** for the
same capability and curriculum scope. Phase does not partition the durable
cooldown, because repeated failure in MAIN versus recovery is still evidence
about the capability neighborhood.

Once triggered, cooldown lasts for only **eight subsequent visits to that
capability**. Visits elsewhere do not consume it. Expiry decays one failed-student
epoch rather than deleting all evidence, so a reopened policy needs another
materially bad student epoch before cooling again. A retained candidate using
that policy on the cooled capability clears the durable cooldown immediately.
There is no permanent blacklist.

Cooldown is authoritative for exact-capability selection and therefore applies
to both contextual selection and Teacher vNext canary selection. Sibling
capabilities in the same grade receive only a small ranking penalty while the
cooldown is active: `0.025` per cooled sibling, capped at `0.05`. This is evidence
sharing, not exclusion; a policy exhausted for `B.IFF` may still be tried for
`B.COMPOSITE` when its own evidence warrants it.

Dashboard semantics must reflect selector authority. `EXHAUSTED` is reserved for
an active selector-visible durable cooldown. A policy with enough observations
but poor retention and no active cooldown is `LOW-YIELD`; low-support evidence is
`UNCERTAIN`; actual strategy mutation remains `EXPLORE`. Presentation history may
estimate retention probability, but it must not invent retirement authority.


## ADR-103 | 2026-10-27 | New frontier grades receive bounded catch-up priority

When a newly introduced highest active grade has far fewer semantics than the
already mature school, raw capability-count fairness under-allocates learning to
the frontier. Ten mature A/B semantics plus one new C semantic naturally gives C
about one eleventh of a plain full-school pass, even when C is dramatically
behind the rest of the student.

During an ordinary cross-grade MAIN sweep, compare the newest active grade's mean
accuracy across its currently introduced/eligible semantics with the median
accuracy of all currently introduced/eligible active semantics. If the frontier
is at or above that median, no catch-up applies. If it is below the median, give
that frontier enough separately assessed MAIN passes to target roughly one
quarter of visit opportunities for the sweep. The total frontier-pass budget is
`ceil(non_frontier_semantics / (3 * frontier_semantics))`, with a minimum of one.
Thus the current 10:1 A/B:C shape receives four C passes, about 29% of visits,
rather than permanent 1/11 capability-count weighting.

Catch-up is deliberately subordinate to existing safety/progression machinery.
It never replaces promotion-sweep handling, failed-sweep recovery, weakest-three
recovery, mature-grade debt repair, or explicit debt cadence. It only repeats the
frontier's ordinary MAIN pass after at least one other grade has already
completed its MAIN pass in that school sweep. The counter resets when the
ordinary sweep resets. Old receipts decode with zero catch-up passes.

Operator presentation must make qualification activity explicit. While the
school stage is `PROMOTION_SWEEP` or `ASSESS_PROMOTION_SWEEP`, the compact header
shows an explicit `SWEEP = GRADUATION <grade>` field rather than relying on the
generic phase text alone.


## ADR-104 | 2026-10-27 | Bespoke hereditary exploration with scalable live strategy ecology

**Direct user correction after renewed rejection hell.** Policy novelty must not
be confused with useful exploration. A policy that is merely new to one
capability does not regain epistemic innocence when its broader history is
already poor, and sustained rejection pressure must not devolve into cycling
through old archive members labeled `UNCERTAIN`.

When a capability reaches sustained rejection pressure (four consecutive
rejections), exploration becomes **bespoke hereditary search**. The teacher
attempts to breed a genuinely novel effective policy for that capability on
every exploratory visit rather than selecting another untried archive member.
Parent ancestry is evidence-seeded in this order:

1. retained policy for the same capability under the same diagnostic context;
2. retained policy for the same capability across phases;
3. retained same-grade policy under the same diagnostic context;
4. retained same-grade policy generally;
5. grade reward history, then global reward history as fallbacks.

Champion-derived weakness evidence participates through the diagnostic-context
identity, so a policy that previously retained when champion-directed examples
were present is preferred as ancestry for another champion-bearing attempt.
Children preserve the chosen parent and mutate one effective knob at a time;
behaviorally equivalent variants do not count as novelty. Teacher vNext may not
override a freshly bred challenger on that same visit.

New bespoke policies are capability-local while unproven. They may not
immediately become `FRESH_ACTIVE_CHALLENGER` material for sibling capabilities.
Once a bespoke policy has actually retained, that locality restriction is
released: a later numeric-scope revision within the same release family may give
the proven policy one fresh challenger trial for the same capability. Prior-scope
reward/context evidence is not copied forward; the revised scope must earn its
own evidence normally. Unproven children remain scope-local.
A retention on their originating capability marks them proven and permits
same-grade reuse thereafter. The newest eight unproven bespoke policies per
capability receive a probationary opportunity; older unproven siblings may be
retired from the live population.

The teacher population is now an **effective-strategy live ecology**, separate
from the immutable historical archive. Historical strategy definitions and
outcomes remain available for provenance and ancestry; pruning means retirement
from live selection, not deletion of evidence. Population limits scale with the
number of currently active capabilities:

- live effective capacity = `max(48, 24 * active_capabilities)`;
- active working set = `min(live_capacity, max(8, 2 * active_capabilities))`.

Thus the present 11-capability school has a 264-effective live population and a
22-effective active working set rather than a fixed 512/16 regime. Rebalancing
keeps newborn policies with fewer than four trials long enough to audition, then
ranks mature strategies by retained outcomes, retention rate, mean contextual
reward, historical reward, recent use, and birth/usage recency. Old,
never-retained, low-reward strategies therefore lose live slots before proven
productive ancestry. When the curriculum grows, capacity grows automatically
and strong retired historical strategies may re-enter the live population.

The historical nominal strategy ceiling no longer blocks invention merely
because aliases or retired definitions occupy archive slots. New effective
children may extend the immutable historical archive while the live effective
population remains bounded by the curriculum-scaled capacity. Visit receipts
record historical archive count, live effective count/capacity, active working
set count/capacity, retired effective count, mutation parent, ancestry basis and
changed fields.

Dashboard health also becomes cross-context aware. `UNCERTAIN` is reserved for
policies that are genuinely under-observed at every available evidence scope.
When exact capability evidence is sparse, health falls back through capability,
grade-phase, grade and global policy history. A policy with substantial
zero-retention evidence therefore remains `LOW-YIELD` when first tried on a new
capability instead of being relabeled `UNCERTAIN` merely because the local tuple
is new. Selector-visible durable cooldown remains the only authority for
`EXHAUSTED`.


## ADR-105 | 2026-10-27 | Restore integer-root scope telemetry and normalize repeated champion specimens

The compact operator header must expose the active integer-root training/test
scope as `INTROOT`, using the durable `numeric_maximum` authority. At startup a
saved maximum `N` renders as `0...N`; profile-adoption telemetry carries the new
maximum so the header updates immediately when numeric scope changes instead of
waiting for dashboard restart. Execution-profile and semantic-catalog adoption
events share this presentation contract. This restores the final compact 349
behavior from `c9ed590`/`7fef150` without making presentation state authoritative
over curriculum admission.

Source lesson cohorts may contain repeated occurrences of the same exact
specimen. Champion weakness discovery is set-valued evidence: if one or more
mentors identify the same source row, that exact row is emitted at most once as
a weakness target. This normalization occurs before weakness-target selection.
The downstream target identity validator remains strict; duplicate identities
arriving from any other malformed target construction still raise
`TEACHER_WEAKNESS_TARGET_IDENTITY_CONFLICT`. Do not weaken that guard to make a
run proceed.


## ADR-106 | 2026-10-27 | GRAD counts distinct model grades; Grade C climbs integer roots 4 through 10

The compact `GRAD` field has three coordinates on each side of `current / lifetime`:

`distinct grades reached . successful promotion sweeps . promotion-sweep attempts`.

The first coordinate is a model-progression count, not a count of repeated grade
boundary successes. Revalidating or re-promoting A/B must never inflate it. The
lifetime coordinate is reconstructed from distinct grade admission/discovery in
the full journal; the current-run coordinate increments only when a genuinely new
grade is admitted/reached during that execution. A model that has reached A, B,
and C therefore reports lifetime grade count `3` regardless of how many A/B
promotion sweeps were repeated. The second coordinate is likewise a progression
count, not a revalidation count: one grade/introduction frontier may contribute at
most one successful promotion sweep. Re-running an already-crossed A/B frontier,
or merely returning from an old-grade sweep to a later already-admitted grade,
must never mint another success. Attempts remain historical attempts and may
increase on repeated sweeps. For the current replay lineage, A→B and B→C are the
only two unique successful progression frontiers recorded so far; while the live
command continues to add attempts its journal reconstructs as `0.0.2 / 3.2.x`.

Grade C owns a mandatory integer-root staircase. Canonical C admission begins at
`0...4`. Once the student fully masters the current admitted C scope and reaches
the normal grade boundary, the runtime performs a neural-inert profile revision
to the next scope exactly one root wider: `0...5`, then `0...6`, through
`0...10`. Scope 10 is terminal for Grade C; no further numeric profile is
generated after it. The terminal numeric ceiling is the registry counting target
(`10`), while `4` is both the entry scope and the full-operation unlock.

The staircase is intrinsic to canonical Grade-C progression. It must not depend
on the legacy `--numeric-staircase` CLI flag. Normal B→C admission therefore
records `numeric_maximum=4` and `numeric_scope_final_maximum=10` (except bounded
experiment runs that intentionally cap themselves at the entry scope).

Existing replay state that was incorrectly admitted directly to profile
`numeric-0-10` with `numeric_maximum=10` and **no**
`numeric_scope_final_maximum` is treated as a one-shot wide-admission migration
signature, not as evidence that the model legitimately climbed the staircase.
When C next becomes the scheduler's active grade, the runtime rebinds that grade
neural-inertly to `numeric-0-4`, sets terminal scope 10, preserves the student and
native AdamW, and resumes ordinary staged C learning. A legitimately completed
scope-10 run has `numeric_scope_final_maximum=10` and is never rewound.

The current executable curriculum contains grades A/B/C only. Grade-D source
adapters exist, but no executable D grade is presently admitted in this release;
do not fabricate a D curriculum as part of the numeric staircase repair. Once a
future executable curriculum actually contains D, ordinary next-grade admission
is eligible only after terminal C@0...10 mastery.


## ADR-107 | 2026-10-28 | Teacher evolution refines bounded numeric genes and measures realized-action novelty

ADR-104 remains the governing ancestry, evidence, locality, population, and
retention contract, but exhausting the legacy discrete policy lattice must not
terminate invention. The immutable historical archive may contain every legacy
effective policy without making the teacher evolutionarily sterile.

The teacher first preserves the existing one-effective-knob hereditary search.
When that discrete neighborhood cannot produce a novel effective child, it may
refine exactly one controllable numeric gene locally around a retained parent:

- `old` remains an integer inside the historical `old` envelope;
- `lr` remains positive inside the historical learning-rate envelope;
- `distill` remains inside the historical distillation envelope;
- `depth` and `contrast` remain categorical until runtime behavior actually
  supports more than SHALLOW/DEEP and RANDOM/DIVERSE;
- `preview` remains excluded from effective identity while future-grade preview
  is intentionally unavailable.

Adaptive mutation bisects the local gap between the parent and its nearest
already-observed numeric neighbor, with deterministic bounded quantization. It
does not invent out-of-envelope optimizer or guidance settings, mutate more than
one effective gene in a child, rewrite any historical policy, or weaken
retention, source, custody, preservation, mature-debt, or frontier gates.

Static genotype novelty is insufficient evidence of useful exploration. Every
delivered candidate already emits a `teacher-realized-action` receipt describing
the optimizer experience that actually occurred. The teacher therefore maintains
an append-only realized-action ecology recording first-seen action identities,
trials, retained outcomes, and the effective policies that produced them.
Bespoke birth receipts record which realized actions they caused and whether
those actions were novel. Realized-action novelty may break otherwise-equal
exploration/ancestry ties, but is never retention credit and cannot authorize an
otherwise rejected candidate.

This keeps the proven ADR-104 control plane intact: evidence chooses ancestry,
mutation remains local and bounded, actual delivered behavior measures novelty,
and ordinary retention decides what survives.

**Status:** Accepted for bounded implementation and non-neural verification.


## ADR-117 | 2026-10-28 | Debt cadence is factory-role based, with B/C confined to legacy migration

**Follow-up after ADR-116 restored useful progression.** The current Prometheus
behavior is now the compatibility specimen, not the schema. Grade B is the
current bounded-debt grade and Grade C is the current progression-priority grade,
but later factory progression must not inherit those identities accidentally.

Persist candidate-level cadence state with role-neutral fields:
`bounded_debt_visits` and `priority_visits_since_bounded_debt`. Historical
`nongating_b_visits` and `non_b_training_turns_since_b_run` remain accepted only
at deserialization and are removed before constructing canonical `SchoolState`.
New state never writes the historical names.

For a factory append with explicit carried mastery debt, derive the cadence roles
from the admitted transition itself. The bounded-debt role is the latest prior
grade represented by the carried debt; the progression-priority role is the newly
appended grade. Preserve an existing cadence value when retargeting; otherwise use
the current default of four priority visits per bounded-debt visit. Reset the two
role-local counters when the roles change. A clean append with no carried mastery
debt clears any stale cadence policy and those counters.

Literal B/C construction remains only in the ADR-094 compatibility adapter for
historical receipts. A historical receipt with B-named counter fields and a
missing/null cadence policy may still rehydrate the old bounded-B / priority-C
contract neural-inertly. Once role-neutral counter fields exist, explicit null is
authoritative and must not trigger B/C inference.

Synthetic factory tests use non-letter semantic grade IDs and prove that a debt
append retargets `FOUNDATION -> RELATIONS` into `RELATIONS -> WORLD_MODEL`, that a
non-default cadence survives retargeting, and that a clean append clears stale
roles. Existing Prometheus B/C 20% cadence and rotation tests remain unchanged as
the behavioral compatibility gate.

**Status:** Accepted for bounded implementation and non-neural verification.


## ADR-112 | 2026-10-28 | Full Grade B is the default; reduced Boolean B is explicit only

The canonical U7C Grade B capability set is the normal executable curriculum:
`B.NOT`, `B.AND`, `B.OR`, `B.XOR`, `B.IMPLIES`, `B.IFF`, `B.COMPOSITE`, and
`B.IDBOOLOPS`. The historical reduced AND/IFF kernel is retained only as an
explicit experimental profile selected by `--reduced-grade-b` (alias
`--minimal-grade-b`). `--full-grade-b` remains accepted but is now the default.

Existing durable runs admitted under the known historical reduced profile must
not remain narrowed forever merely because later grades have already been
admitted. On resume under the default policy, the runtime performs a neural-inert
same-school profile expansion that restores the missing B semantics while
preserving the exact causal student and its native AdamW. Added B semantics become
carried mastery debt, stale B championship/assessment authority is invalidated,
and the scheduler returns to the newest active progression frontier before normal
debt cadence resumes. No historical score is fabricated for newly restored
semantics.

This expansion is curriculum/profile state only. It does not itself perform a
neural update, declare the restored semantics mastered, lower B's bounded debt
share, or weaken source/custody/promotion/retention gates.

**Status:** Accepted for implementation and neural-inert migration verification.


## ADR-113 | 2026-10-28 | Frontier recovery effort scales with measured weakness

Weakest-first recovery must allocate effort proportionally enough to matter. A
progression blocker near 50% while the school mean is near 90% must not receive
the same single recovery visit as a near-mastered capability around 90%.

Within the ADR-094/109 progression-priority recovery path, rank the up-to-three
imperfect frontier capabilities by accuracy as before, then assign each a bounded
visit weight from its deficit below the unweighted whole-school capability mean.
Each imperfect frontier capability receives one maintenance visit; for every
additional 10 percentage points below the school mean it receives one additional
visit, capped at six visits in one recovery queue. Interleave weighted visits by
rank rather than running one capability's entire weight consecutively.

Weighted visit multiplicity belongs only to the executable recovery `queue`.
`first_recovery` is stagnation-control membership metadata and must remain the
unique ordered capability set underlying that queue. Never copy repeated weighted
visits into `first_recovery`; doing so violates the stagnation cycle invariant and
can block resume with `STAGNATION_FIRST_RECOVERY_DUPLICATE`.

This is scheduling pressure, not evidence or retention credit. Exams remain
unchanged, near-mastered imperfect semantics still receive maintenance exposure,
and B debt cadence, promotion thresholds, plasticity bounds, mature-debt repair,
source/custody and retention gates remain authoritative. The weighting exists to
turn large measured deficits into correspondingly larger learning effort instead
of merely labeling them "weakest" once.

**Status:** Accepted for bounded implementation and scheduler verification.


## ADR-110 | 2026-10-28 | School-wide retention drought can activate plasticity for below-mean semantics

**Direct user correction to ADR-108's scaling behavior.** Capability-local
starvation remains useful for one stubborn semantic, but it scales poorly when
the school contains many active semantics and failures are distributed across
them. Plasticity therefore gains a second, school-wide activation path.

The teacher maintains a durable `school_attempts_since_retained` counter in its
causal state. It increments once for every committed teacher visit that does not
retain a candidate and resets to zero on any retained/provisional candidate whose
trial is actually committed. This counter is independent of which capability was
visited.

For each visit, plasticity activates when either:

1. the existing ADR-108 capability-local starvation threshold is reached; **or**
2. at least 24 school-wide visits have elapsed since any retention **and** the
   current capability's latest examination accuracy is strictly below the
   unweighted mean of all valid capability accuracies in the latest whole-school
   exam.

Each capability receives one vote in the school mean regardless of exam-row
count. A capability absent from the latest exam cannot activate the global-drought
path until it has authoritative score evidence. Equality with the mean is not
below mean. The global path remains disabled outside developmental MAIN /
RECOVERY_1 / RECOVERY_2 stages, exactly like local plasticity.

The new path changes only *eligibility for ADR-108's existing bounded slack*.
It does not widen any loss tolerance: strict positive target gain remains
mandatory; same-grade/fixed/frontier losses remain capped by ADR-108; fragile
replay, source/custody/semantic identity and mature-debt hard limits remain hard.
A single retained candidate anywhere in the school closes the global drought path
for subsequent visits by resetting the counter to zero.

Telemetry must distinguish `LOCAL_STARVATION` from
`SCHOOL_RETENTION_DROUGHT_BELOW_MEAN`, report the school-wide drought count and
threshold, and report the current capability score and school mean used by the
global predicate.

**Status:** Accepted for bounded implementation and non-neural verification.


## ADR-111 | 2026-10-28 | Failed promotion sweeps require blocker improvement before retry

**Direct user correction after repeated graduation attempts failed without
converging.** A changed whole-student checkpoint is not sufficient evidence that
the reason a promotion sweep failed has changed. Retentions on unrelated
capabilities must not repeatedly re-arm the same expensive sweep against an
unchanged blocker profile.

When a promotion sweep aborts below its hysteresis floor, or completes on an
already-admitted older grade without advancing that grade, the scheduler records
the imperfect capabilities in that sweep and their exact correct/total scores as
the retry baseline. A later assessment for the same promotion scope may re-arm the
sweep only when both ordinary entry eligibility is satisfied **and** the unweighted
mean accuracy across those recorded blockers is strictly better than the failed
baseline. A new student hash by itself is insufficient.

Successful semantic introduction, actual grade promotion, or reaching an
authorized next-grade boundary clears the failed-sweep blocker baseline. A changed
promotion scope also supersedes it naturally. The blocker baseline is evidence
about retry eligibility, not a new mastery threshold: existing 92% entry, 87%
hysteresis, promotion, retention, source/custody, and mature-debt rules remain
unchanged.

This is deliberately compatible with ADR-094 and ADR-109. Failed B revalidation
sweeps do not create extra B training share; B continues to receive its bounded
debt turns, and another B sweep waits until those turns have measurably improved
the B blocker set. Failed progression-frontier sweeps continue ordinary frontier
recovery, but unrelated A/B retentions cannot manufacture another nominal
graduation attempt.

**Status:** Accepted for bounded implementation and non-neural verification.


## ADR-108 | 2026-10-28 | Retention starvation opens a bounded plasticity escape hatch

**Direct user correction after sustained zero-retention calcification.** Normal
retention remains conservative, but a capability that has gone a long time
without retaining must not be forced to preserve every local optimum forever.
When the teacher has positive source-paired evidence that the active capability
actually improved, sustained retention starvation may temporarily tolerate a
small amount of collateral regression so the learner can move to a different
basin and repair displaced skills afterward.

This is a derived, capability-local mode, not a persistent switch. It activates
after 32 consecutive attempts without a retained candidate for an ordinary
capability, or after 16 for the newest active grade or a semantic in the current
introduction stage. A retained candidate resets `attempts_since_retained` to zero
and therefore closes the escape hatch immediately on the next visit.

Plasticity escape never waives the requirement for a strict positive gain on the
active capability. It also never waives fragile-composition replay, source-gold,
custody/provenance, semantic identity, or the mature-grade debt hard limit. When
active, it may relax only these retention boundaries:

- same-grade net change may be as low as `-1` correct answer;
- a protected capability may exceed its ordinary per-capability loss tolerance
  by at most one additional wrong answer;
- fixed same-grade cohort net change may be as low as `-1`;
- protected active-grade frontier change may be as low as `-1`;
- whole-school fixed-frontier net change may be as low as `-1`.

Anything worse remains rejected. Candidates with no measurable target gain remain
rejected. When frontier evidence makes mature-grade debt exceed its existing hard
limit, the candidate remains rejected even if every plasticity bound otherwise
passes. Accepted escape candidates carry explicit telemetry naming the ordinary
rejection reason that was conditionally waived, the starvation count, activation
threshold, frontier-priority status, and each temporary loss bound. Ordinary
assessment, recovery, and mature-debt repair then own earning displaced
capabilities back; plasticity mode itself does not declare those regressions
repaired.

**Status:** Accepted for bounded implementation and non-neural verification.


## ADR-109 | 2026-10-28 | Progression-frontier visit priority persists until advancement

**Direct user correction after `C.COUNT` fell back to roughly one visit in ten.**
ADR-103 correctly recognized that raw capability-count fairness starves a newly
introduced frontier semantic, but it ended catch-up priority once the frontier
mean reached the school median. That statistical condition is not the progression
condition. A frontier semantic can be near or above the school median and still be
the sole blocker preventing introduction of the next semantic.

While the newest active grade is the explicit progression-priority grade and any
currently introduced eligible semantic in that grade remains imperfect, its
ordinary MAIN sweep retains the existing ADR-103 visit-allocation floor of roughly
one quarter of candidate opportunities. The existing bounded pass formula remains:

`ceil(non_frontier_semantics / (3 * frontier_semantics))`

with a minimum of one frontier pass. The school-median comparison is no longer an
off-switch for this progression allocation. Once every currently introduced
frontier semantic is perfect, the extra passes disappear normally and ordinary
promotion/semantic-introduction machinery decides the next transition.

This is scheduler priority only. It does not lower promotion thresholds, change
retention gates, suppress mature-grade repair, erase A/B debt, or make B a
progression prerequisite. ADR-094's bounded B debt turns remain intact; this
correction prevents their surrounding multi-capability work from reducing the
actual progression frontier to raw 1/N capability frequency between boundaries.

Historical and migrated C-frontier receipts may carry an explicit
`debt_cadence_policy: null`. That value is stale compatibility state, not an
intentional revocation of ADR-094. When B and C are admitted and C is the newest
active grade, deserialization neural-inertly rehydrates the canonical bounded-B /
progression-C cadence exactly as it already does when the field is absent. The
policy remains dormant unless both B and C actually carry unfinished debt.

**Status:** Accepted for bounded implementation and non-neural verification.


## ADR-114 | 2026-10-28 | Plasticity trades normalized mastery debt, not raw correct-answer counts

**Direct user correction after active Grade-C plasticity still rejected useful
frontier trades.** A correct-answer loss has different developmental cost at
100% mastery than it has in an already weak capability. Plasticity therefore
must not compare collateral changes as raw answer counts or as one fixed
`-1` allowance across heterogeneous capability cohorts.

When plasticity is active, every measured capability receives one vote
independent of its row count. For capability accuracy `a`, define normalized
mastery debt `d = 1 - a` and mastery-debt energy `E = d^2`. The utility of a
candidate on one capability is `E_before - E_after`; scope utility is the sum of
those capability utilities. Positive utility means the candidate reduced total
normalized mastery debt. The square is deliberate: borrowing a few points from
a nearly perfect capability is cheap, but repeatedly degrading the same
capability becomes progressively more expensive.

The active capability must still show a strict positive source-paired gain.
Plasticity may relax an otherwise raw-count-based same-grade or protected-loss
rejection only when both the complete same-grade paired scope and the complete
paired protection scope have strictly positive mastery-debt utility. A negative
fixed same-grade, active-frontier, or whole-school fixed-frontier raw delta may
likewise be waived only when that exact evidence surface has detailed
per-capability scores and strictly positive mastery-debt utility. If an older
evidence surface lacks per-capability paired scores, a negative raw delta remains
non-relaxable rather than guessing a utility value.

This supersedes ADR-108's fixed `-1` plasticity loss caps and one-extra-answer
protected tolerance as the plasticity trade criterion. Ordinary retention outside
active plasticity remains unchanged. Fragile-composition replay, source-gold,
semantic identity, custody/provenance, strict target gain, and the mature-grade
debt hard limit remain hard gates. Plasticity still does not declare displaced
skills repaired; normal assessment and recovery own that work.

Because activation changes candidate admissibility, the teacher must not discard
a previously observed target-improving near miss merely because it was rejected
before plasticity opened. On the first eligible active-plasticity opportunity,
selection may retry an otherwise active, previously rejected target-gaining
policy that has not yet been evaluated under plasticity before breeding another
pressure challenger. The retry receives fresh source-paired scoring and ordinary
retention authority; historical rejection evidence is never rewritten.

Telemetry records the quadratic power and per-surface, per-capability utility so
operators can see why a raw regression was accepted or rejected.

**Status:** Accepted for bounded implementation and non-neural verification.


## ADR-115 | 2026-10-28 | Retained teacher policies outrank newborn pressure exploration

**Direct user correction after a 40-visit zero-retention run.** The run still
produced target gains, but the teacher selected a fresh mutated challenger on
39 of those 40 visits. The last policy that retained a candidate was not reused
after retention and was later absent from the live strategy population.

Two control-plane rules caused the failure. First, unproven newborn grace ranked
ahead of retention evidence in live-population pruning. A stream of one-trial
children could therefore displace a strategy that had passed the real retention
gate. Second, the sustained-pressure branch minted a child before current-context
retained evidence could be exploited. Together these rules turned rejection
pressure into nearly continuous mutation.

Retention evidence now has priority over newborn grace in the live population.
Newborn grace still protects young unretained strategies from older unretained
strategies, but it cannot evict an effective strategy with a retained outcome.

Sustained rejection pressure still enables ADR-104 hereditary exploration. It no
longer makes every pressure visit an exploration visit. If the current context
contains an active retained effective policy, the teacher uses the best retained
policy before minting another child. Existing checkpoint-local retirement remains
the bound: after four unretained or no-target-gain uses on the same student, that
effective policy leaves the active set and hereditary search resumes. This uses
the existing failure memory instead of adding a new cadence or timeout.

When no active retained policy exists in the current context, ADR-104 ancestry
still applies. Retained same-capability evidence from another phase may seed a
new child, followed by same-grade and reward fallbacks. Teacher vNext keeps its
bounded existing-policy canary cadence.

This correction changes policy selection and live-population survival only. It
does not weaken candidate retention, plasticity utility, fixed-frontier checks,
source or custody rules, fragile replay, or mature-grade debt limits.

**Status:** Accepted for bounded implementation and non-neural verification.


## ADR-116 | 2026-10-28 | Retention support follows veto surfaces; B returns to a 20% candidate-effort ceiling

**Direct correction after the restarted run remained near 3% retention.** The
post-restart session retained only about one candidate in forty even though many
rejected candidates still improved their target probe. Two allocation defects
were visible in the live receipts.

First, generic retention support rotated uniformly across the whole admitted
school. After full Grade B was restored, the same optimizer batch also reserved
four fresh B.OR and four fresh B.XOR preservation siblings. Generic support could
therefore spend another turn on those already-preserved connectives while a hard
lesson-grade or active-frontier surface received little rehearsal. Candidate
construction now spends generic support on the complete lesson grade and latest
active progression frontier. Verified fragile-preservation capabilities are
removed from that generic schedule. Short budgets rotate across the priority
surface between visits. Earlier-grade rehearsal remains controlled by the
teacher's existing `old` policy.

Second, ADR-094's full-grade B turn no longer matches the user's later operating
constraint. A due B turn could expand into seven consecutive candidate visits,
so B consumed roughly one quarter of live candidate work while C remained the
progression frontier. Full U7C B remains admitted, but allocation returns to a
candidate-effort boundary: four progression-frontier candidate visits earn one B
candidate visit. Each earned visit teaches one currently imperfect B semantic,
rotating in canonical order so no admitted Boolean semantic starves. The cadence
resets after that B visit. This supersedes ADR-094 only for the allocation unit;
it does not restore a reduced B curriculum or make B a C prerequisite.

These changes do not relax target gain, lesson-grade, active-frontier,
whole-school, protected-capability, fragile replay, mature-debt, source-gold,
semantic identity or AdamW custody requirements. They change what is taught
before those gates judge the candidate.

**Status:** Accepted for bounded implementation and non-neural verification.


## ADR-118 | 2026-10-28 | Current BAMF issues remain authoritative; future work carries its normative spec in-repo

For the three current BAMF-0.2 workstreams represented by GitHub issues
#341 through #545, GitHub remains the authoritative source for issue scope,
requirements, acceptance criteria, status, and any later issue-level correction.
The mirrored issue/specification files already present under
`docs/tasks/bamf-0.2/` are retained as durable planning and implementation
context, but they must not silently supersede a changed GitHub issue during these
existing workstreams. If an existing issue is intentionally migrated to repo-spec
authority, that migration must be explicit in both the issue and its specification.

This is a transition rule, not the long-term documentation model. For new work
created after this decision, the normative engineering specification should live
with the work in the repository and branch where it is being implemented, under
ordinary version control. GitHub issues should become deliberately smaller:
concise problem statements, ownership/navigation metadata, execution status, and
a direct pointer to the authoritative repository specification rather than a
second full copy of the same requirements.

The repository specification is authoritative because its changes travel through
the same commit graph as the implementation. A branch, fork, release, or archived
commit therefore carries an explicable specification snapshot for the code state
it contains. Requirements can be reviewed, diffed, reverted, blamed, and evolved
with the implementation instead of relying on mutable issue text whose edit
history is not part of the repository lineage.

Future issue creation and decomposition should preserve this single-source rule:
the issue may summarize or index the work, but normative detail belongs in the
versioned repo specification. Agents must not maintain two independently editable
full specifications and then guess which one wins.

**Status:** Accepted as the authority-transition contract for the BAMF unified
base and future Bilqis-MLX work shaping.


## ADR-119 | 2026-10-28 | BAMF uses three long-lived lane branches around a living reviewed integration trunk

The BAMF unified branch is not frozen after its initial composition. Git history
already preserves the exact common ancestor, so freezing the integration branch
would add no meaningful provenance while delaying useful cross-lane integration.

`codex/bamf-unified-base-20261028` is therefore the living reviewed integration
trunk. Lane A works on `codex/bamf02-a-semantics`, Lane B on
`codex/bamf02-b-neural`, and Lane C on `codex/bamf02-c-runtime`.

Every implementing issue begins with a sync-in boundary. The lane fetches `origin`
and merges the current `origin/codex/bamf-unified-base-20261028` into its own lane
branch before issue-owned edits. The receipt records the consumed unified SHA. If
the lane already equals that head, record the SHA rather than manufacturing a
no-op merge. Resolve conflicts and run the smallest affected verification before
continuing. Lanes do not merge `main` or sibling lanes directly; accepted
cross-lane work travels through unified.

Every completed issue has a reviewed return path. After its owned acceptance
passes, the lane pushes and opens a pull request from the lane branch into
`codex/bamf-unified-base-20261028`. Human sign-off is required before merge; issue
execution does not delegate self-merge authority. After accepted work lands on
unified, subsequent issues in all lanes consume it at their next sync-in boundary.
This exposes shared interfaces, tests, instrumentation, and conflict pressure
early while preserving lane ownership and an explicit integration approval gate.

The three lane branches remain long-lived across issues. Merge commits from unified
into a lane are preferred over rebasing because issue receipts, reviews, and other
agents may already reference lane commit SHAs. Non-implementing group or
integration-parent issues inherit this lifecycle through their implementing
descendants and do not create empty bookkeeping code PRs.

**Status:** Accepted as the BAMF branch topology and integration lifecycle.

## ADR-120 | 2026-10-28 | BAMF successor outcome, admission and baseline custody

**Scope:** BAMF-0.2 successor only; issue #486 under #347 and #344. This
records the selected policy and baseline evidence; it does not implement a
student, grant admission, authorize neural training or alter #324.

**Decision:** Judge useful capability by complete-system outcomes. Exact retrieval,
declared deterministic operators, learned memory, neural prediction and their
compositions each count equally when they solve a source-valid task. All admitted
grades use the same grade-neutral Factory, teacher, retention and assessment
policy. Source-gold, prerequisites, whole-school retention, checkpoint and own
optimizer custody, and the sovereign MLX writer remain binding.

Semantic releases default to staging. A human-started BAMF run may delegate later
source-valid expansion through an explicit persisted admission lease and the
existing Factory/admission owner. The source bridge can be built now. Its first
live adoption requires BAMF's disposable C16 ([#382](https://github.com/Entif-AI/Bilqis-MLX/issues/382)) source/custody/retained-learning
witness, including a strictly improved fresh target, preserved cumulative retention,
complete rejection rollback and equivalent cold-resume output and next update,
before the operator starts the first persistent lineage, rather than waiting for
the historical #324 model-size comparison. Persistent-student learning receipts
are subsequent operating evidence. The operator owns every
durable-student start, resume and stop. This is a desired-state contract, not
proof the lease or successor learner has been implemented.

**Baseline evidence:** Lane C starts from reviewed unified
`44f78431709ec3b8fc23f47b45d9b18f167c7354`. Replay
`d21797e72365bf93ea7cad3a4ef9020ec9817f23` is its Git ancestor. The historical
SKOS merge `175cdf6778b4eeaea23a5bd36ad7dc6664df3ae8` and its PR head
`0561e67eada816a999841aab3d9d5080e8f99bed` are **not** ancestors of unified.
Unified commit `77d4f6869b782fc24341e6e6ec8f2601e1dd3873` imported the SKOS
files. At this baseline, `lib/ithkuil/src/skos` and `lib/ithkuil/_data` match
the historical SKOS merge; `lib/ithkuil/RELEASE_REBUILD.md` differs. Content
inclusion is not Git ancestry. No second integration branch or main merge is
needed. The discrepancy is recorded as PM-2026-10-28-001.

**Custody:** The frozen #324 v3 executable
`2e5ee21a97a66c683c61f74419da03500c30d2c4` and manifest
`7f1968f38b2a062df7dbaae586ccecc3327ff5885a72cb7c368938ecec92aea1` remain
historical controls. Do not modify, substitute or rebase them or their student
and optimizer state. Disposable-witness retained learning remains unmeasured until
that witness runs; persistent-student learning remains unmeasured until the
human-owned successor run produces its own evidence.

## ADR-121 | 2026-10-31 | Close satisfied child issues; keep integration authority at parents

GitHub issue state now answers a narrow operational question: **does actionable work remain inside this issue's own durable contract?** It does not mirror the completion state of every ancestor, sibling, or downstream integration gate.

An implementing child or leaf issue should close once its own bounded outcome and acceptance contract are satisfied and its accepted work is integrated into the reviewed unified trunk. A parent issue may remain open for aggregate integration, cross-lane qualification, retained-learning proof, production authority, or other owner-level acceptance without forcing already-delivered children to remain open. Closing a satisfied child is therefore not a claim that its parent, workstream, BAMF gate, learner, or durable runtime is complete.

If a merged pull request delivered only a proper subset of the issue's own stated contract, either keep that issue open while concrete work still remains at the same durable boundary or, preferably when the residual is independently actionable, create a smaller successor issue for the residual gap and link it to the historical issue/PR. Later regressions, newly discovered integration gaps, and changed requirements should normally become new self-contained issues with a concise current reproduction, relevant authority/spec pointer, dependency context, and acceptance criteria. Reopen a closed issue only when its original acceptance was actually invalidated, reverted, or the delivered outcome itself must be restored.

Open parent/integration issues remain the durable place for unresolved aggregate acceptance. Closed children remain provenance and may be referenced by successors. The desired operational result is that the open-issue set approximates the **current executable frontier plus meaningful parent/integration containers**, rather than every historical work packet whose ancestors are still incomplete. This reduces triage noise and lets lower-reasoning agents act on bounded current tickets without reconstructing the full historical issue tree.

For the existing BAMF-0.2 hierarchy, this decision authorizes a reconciliation sweep of open issues: close merged-and-satisfied leaves, close superseded historical paths, split independently actionable residuals when useful, and leave genuinely unfinished leaves plus integration/acceptance parents open. GitHub remains authoritative for the current #341-#545 issue scopes under ADR-118; this lifecycle decision changes state semantics, not the normative requirements of those issues.

**Status:** Accepted as the GitHub issue-lifecycle and backlog-visibility contract for BAMF-0.2 and successor Bilqis-MLX work shaping.

## ADR-122 | 2026-11-01 | A09.4 proves exact A09.3 projection custody from release + projection evidence

**Scope:** BAMF-0.2 A09.4 issue #394 only. This is a narrow amendment to the
issue's `Precise inputs and existing owners` contract after adversarial review
proved that the A09.3 bounded proposal alone cannot authenticate its ordered
capability and semantic-identity introductions.

**Decision:** A09.4 direct-proposal validation MUST consume the current
`ExecutableFactoryRelease` together with the exact selected
`TargetDeltaProjection` used by A09.3, and MUST validate the supplied A09.3
selection against that derivation evidence before granting proposal/progress
credit. Staged/cold-resume custody MUST carry the exact projection evidence needed
to reproduce and revalidate the same derivation rather than trusting only a
self-consistent proposal digest or a successor transition that happens to match
caller-supplied introduction fields.

This closes the reproduced same-semantic forgery in which
`introduced_capability_ids` or `introduced_semantic_ids` could be changed and all
proposal/projection hashes recomputed consistently while A09.4 still accepted the
payload. Digest integrity remains necessary but is not derivation authority.

The amendment deliberately leaves the accepted A09.3 selection schema and ranking
semantics unchanged. It does not move staging ownership away from the existing
#296 Factory/adoption path, create a parallel registry, grant admission rights, or
alter the C07 persisted-lease boundary. A09.4 remains proposal/staging logic only;
runtime admission and durable mutation stay with their existing owners.

**Human ratification:** Option A from the #394 architecture checkpoint was
explicitly selected by the project owner on 2026-11-01. Option B, which would
change the already-accepted A09.3/#296 output contract to mint a new upstream
projection receipt, is not adopted.

**Status:** Accepted as the controlling A09.4 projection-custody amendment.



## ADR-123 | 2026-11-01 | A09.4 projection truth is deterministic derivation, not caller assertion

**Scope:** BAMF-0.2 A09.4 issue #394. This is the follow-on authority decision
required after fresh exact-head EGM proved that ADR-122's caller-supplied
`TargetDeltaProjection` evidence could still be forged self-consistently with a
matching `FrontierDeltaSelection`.

**Decision:** The authoritative `TargetDeltaProjection` is the deterministic
result of the trusted A09 planning derivation. A09.4 MUST independently derive
or invoke the canonical pure derivation of that projection from the authenticated
A09.3 inputs that determine it, including the current
`ExecutableFactoryRelease` and validated predecessor snapshot / legal-closure /
selection context. A projection supplied by a caller, proposal, staged receipt,
or cold-resume payload is evidence to compare against that derivation; it is not
itself projection authority.

For direct proposal validation, A09.4 MUST rederive the expected projection from
trusted inputs and require an exact match before granting `PROPOSAL` or progress
credit. A self-consistent caller pair of `FrontierDeltaSelection` and
`TargetDeltaProjection` that does not equal the independently derived projection
MUST fail closed with a typed planner/custody error.

For staged or cold-resume validation, persisted receipts MUST retain enough
authenticated predecessor coordinates to rerun the same deterministic derivation.
Persisting projection bytes or digests is useful for replay and corruption
detection, but those stored values do not become an independent trust root merely
because they were persisted. Current credit is granted only after rederivation
from authenticated predecessor authority and exact comparison.

This decision does **not** change A09.3 winner ranking, comparator semantics,
budget rules, or accepted selection behavior. It does not move staging ownership
away from #296, create a new registry or parallel source of truth, or alter C07's
exclusive admission / persisted-lease authority. The derivation may be factored
into a reusable pure planner owner, but its semantic authority remains the
existing A09 planning inputs rather than a new caller-controlled artifact.

**Supersession:** ADR-122 remains valid for carrying exact projection evidence,
but is superseded wherever it could be read to mean that supplying a
self-consistent projection is sufficient derivation authority. Exact evidence
must now be checked against an independently rederived expected projection.

**Human ratification:** The project owner explicitly approved this trust-anchor
rule on 2026-11-01 after requesting the architecture be stated in plain language:
the system must recreate the projection from trusted inputs rather than trust the
projection presented to it.

**Acceptance effect:** This removes the architecture/authority block on #394
implementation. #394 is not accepted until the implementation receives a fresh
independent exact-head adversarial EGM and ordinary turn-in gates. #395 remains
dependency-waiting until #394 is accepted sufficiently for its stated prerequisite.

**Status:** Accepted as the controlling A09.4 projection-authenticity rule.

## ADR-124 | 2026-11-02 | BAMF lane flow control freezes parked PRs and bounds active implementation WIP

**Scope:** BAMF-0.2 execution across Lanes A, B and C. This decision governs
work-in-progress classification, parked pull-request handling and lane take-up. It
does not weaken issue acceptance, EGM, human merge, dependency, custody or source
authority requirements.

**Problem:** Open PR count and owner-level `implementation incomplete` status had
begun to masquerade as active engineering concurrency. Review-waiting,
dependency-waiting and authority-waiting PRs were repeatedly merge-forwarded,
revalidated and re-reviewed whenever reviewed unified advanced. Those refreshes
consumed substantial execution capacity without moving the blocked gate, while the
existing WIP measure excluded the same PRs because their feature coding was not
actually active. The result was a feedback loop in which parked inventory generated
work merely by existing.

**Decision:** BAMF uses an explicit lane-local flow state. `ACTIVE` is the only
state that counts as implementation WIP and the only state that permits substantive
branch mutation. `READY`, `WAITING`, `BLOCKED` and `TURNED_IN` are non-WIP states.
The normal ceiling is **two ACTIVE implementation leaves per lane**. This is a
maximum, not a target: workers should preferentially drive the active item with the
fewest remaining gates to accepted integration before taking another leaf.

A `WAITING` or `BLOCKED` item MUST carry a concrete resume trigger. Parked work
MUST NOT be merge-forwarded, rebased, fully revalidated, sent for fresh exact-head
review or otherwise refreshed merely because the unified branch advanced. A newer
unified SHA is not, by itself, a resume trigger. When the recorded gate actually
changes, the operator verifies that trigger, updates the lane state to `ACTIVE`,
then performs the one synchronization/revalidation pass required by the leaf
contract.

Every active lane-owned BAMF implementation leaf and every open BAMF lane PR MUST be
represented in the lane's machine-readable state under `docs/tasks/bamf-0.2/flow-control/`.
`scripts/check_bamf_flow_control.py` validates the declared state, required resume
triggers and normal per-lane WIP ceiling, and is part of the repository quality
path. A lane may exceed the normal ceiling only with an explicit machine-readable
exception naming the reason, authority and expiry condition. Exceptions are
temporary evidence, not a new default.

**Limits of mechanical enforcement:** Repository checks can validate declared
state. They cannot observe an agent silently reading or mutating a remote branch
without updating the lane record. Therefore changing the lane state before
substantive mutation remains an agent/operator duty enforced by `AGENTS.md` and the
BAMF lane execution contracts. Future GitHub-event integration may strengthen
remote-drift detection without changing this decision.

**Operational effect:** Review and external-gate inventory remains visible but
stops consuming continuous refresh work. A lane with one ACTIVE leaf and several
WAITING PRs has WIP=1, not WIP equal to its open PR count. When an external gate
fires, the parked PR competes for the next active slot according to merge proximity,
dependency unlock and lane priority rather than waking automatically.

**Human ratification:** The project owner approved the proposed enforcement and
socialization controls on 2026-11-02 and explicitly required this decision to be
recorded in `ADR.md`.

**Status:** Accepted as the controlling BAMF-0.2 lane flow-control and parked-PR
discipline.
## ADR-125 | 2026-11-02 | Remediation artifacts close at local acceptance; parent owns aggregate EGM

**Problem:** BAMF review findings had begun to accumulate as open issues and draft
PRs even after their exact defects were repaired. Those artifacts were being kept
open until the entire parent feature, sibling set, dependency graph and final EGM
cycle completed. That turns GitHub's open set into historical storage. Every agent
that searches for related open issues or current PRs then pays a growing discovery,
classification and context cost for work that is already finished.

**Decision:** Open issues and PRs represent the current actionable working set.
Historical provenance belongs in closed issues and merged/closed PRs.

A remediation issue closes when its exact recorded defect has been reproduced,
repaired, regression-covered and verified on a durable PR/head. The issue does not
remain open merely because a parent issue or integration PR still awaits EGM,
sibling remediation, dependency acceptance or final human merge. The linked PR and
closed issue retain the implementation and provenance receipt.

A remediation PR remains draft only while its own scoped implementation is
incomplete or a known Blocker/Major against that scope remains unresolved. Parent
EGM debt is not a draft condition. Once the PR's scoped acceptance is satisfied,
mark it ready for review. Merge or close it promptly when its change is consumed by
the intended parent/candidate branch. Do not retain an open PR merely as evidence.
Do not create a separate remediation PR merely to preserve a review finding when
the authorized parent candidate branch can safely accept the fix under current
writer coordination. The remediation issue is the durable finding record. A stacked
PR is justified when it provides necessary writer isolation, branch ownership, or
focused review; otherwise repair the parent candidate directly.
Because the reviewed BAMF integration trunk is not the repository default branch,
GitHub closing keywords are not sufficient closeout machinery. Operators must
explicitly verify the linked remediation issue state and close satisfied children
after their repair is accepted or consumed.

The owning parent issue/PR carries aggregate merge-readiness state, including the
fresh pinned EGM result. A later EGM or integration finding reopens a closed
remediation issue only when it proves the same original defect still exists, was
reverted, or its stated acceptance was false. A different failure mechanism,
newly exposed gap or new acceptance failure gets a new remediation issue with its
own reproduction and bounded acceptance.

**Relationship to ADR-121:** ADR-121 remains the general issue-lifecycle contract.
For remediation children, this ADR narrows ADR-121's earlier requirement that
accepted work first be integrated into reviewed unified before issue closure. A
durable verified remediation PR is sufficient to close the child issue; the parent
still cannot claim acceptance until it consumes that fix and satisfies its own
integration and EGM gates.

**Operational effect:** The open issue/PR set should approximate executable work
plus meaningful parent/integration containers. Review sweeps search a bounded current
frontier instead of repeatedly rediscovering completed defects. EGM can continue to
unlock new defects without causing the backlog to grow monotonically.

**Human ratification:** The project owner explicitly directed this lifecycle on
2026-11-02 after observing that retaining repaired children until whole-program
completion was neither sensible nor scalable.

**Status:** Accepted as the remediation issue/PR lifecycle for BAMF-0.2 and
successor Bilqis-MLX work.

## ADR-126 | 2026-11-02 | Bound integration inventory and gate PR admission

**Scope:** BAMF-0.2 implementation across Lanes A, B and C. This decision governs
open implementation-PR inventory, PR admission, blocked-candidate retirement and
queue-drain behavior. ADR-124 continues to govern active implementation WIP and
parked-branch mutation. ADR-125 continues to govern remediation lifecycle.

**Problem:** ADR-124 limits `ACTIVE` implementation work but deliberately excludes
`READY`, `WAITING`, `BLOCKED` and `TURNED_IN` items from WIP. This prevents
parked work from consuming continuous engineering capacity, but it does not bound
integration inventory. A lane can therefore satisfy its ACTIVE WIP limit while
accumulating arbitrarily many open pull requests.

Open PRs impose integration cost even when nobody is modifying them. They enlarge
the review frontier, age against the reviewed integration trunk, accumulate
conflicts, obscure merge priority, increase discovery and reconciliation work, and
encourage remediation around candidates that are not presently capable of
integration.

An implementable issue is not automatically entitled to an open pull request.
Issues define durable work and ownership. Commits preserve implementation
provenance. Pull requests are temporary integration vehicles.

**Decision:** BAMF tracks **active implementation WIP** and **open
implementation-PR inventory** as separate quantities. ADR-124's lane-local ACTIVE
ceiling remains unchanged.

The normal open implementation-PR ceiling is **three total across BAMF**, with at
most one current integration candidate for each of Lanes A, B and C. The unified
integration PR into `main` is a separate program-level container and does not
consume one of these three implementation slots. The ceiling is a maximum, not a
target. A lane does not open a PR merely because a leaf implementation is complete.

### PR admission

A new implementation PR may be opened only when all of the following are true:

- an implementation-PR slot is available;
- the candidate has a durable owning issue and implementation head;
- every hard prerequisite required for its current integration boundary is
  consumable;
- the candidate has synchronized with the reviewed integration trunk when its
  contract requires synchronization;
- its scoped acceptance and affected verification are green;
- no known Blocker or Major owned by the candidate remains unresolved;
- no existing open PR already owns the same integration delta;
- opening the PR creates a credible path to integration rather than durable
  parking.

Implementation may continue on an authorized branch without an open PR. Completion
of a leaf does not override PR admission.

### Blocked and waiting work

A branch, commit, issue and verification receipt are sufficient to preserve blocked
or waiting implementation.

An implementation PR that becomes materially blocked by another owner or by an
external prerequisite SHOULD be closed after its exact head and continuation
trigger are preserved. Reopen the PR or create a new integration vehicle when the
trigger is satisfied.

A long-lived open `WAITING` or `BLOCKED` PR requires an explicit exception that
identifies why an open PR is required instead of durable branch/issue custody, the
blocking condition, the exact resume trigger, the authority for retaining the PR,
and the expiry condition. Review convenience and historical provenance are not
sufficient exceptions.

### Remediation and EGM

ADR-125 remains controlling. A review finding may receive a durable remediation
issue without receiving another PR. Repair the authorized parent candidate directly
when writer coordination permits. A stacked remediation PR is justified only when
independent writer custody, branch ownership, necessary review isolation or another
concrete integration constraint requires it. Once consumed, merge or close it
promptly.

Fresh pinned EGM remains a merge-readiness gate. Do not create or retain additional
PR inventory merely to obtain separate EGM receipts for individual repairs.
Complete the known engineering and remediation queue first, stabilize the
candidate, then obtain fresh exact-head EGM for the whole merge candidate.

### Drain mode

If open BAMF implementation-PR inventory exceeds the normal ceiling, BAMF enters
**DRAIN** mode automatically.

While DRAIN is active:

- no new implementation PR may be opened unless it replaces another PR that is
  closed in the same operation or carries an explicit owner-authorized exception;
- new implementation work may proceed only when it does not increase open PR
  inventory;
- priority goes to merging, consuming, repairing in place, closing, superseding or
  directly unlocking existing integration candidates;
- decomposition and issue creation may continue when they clarify durable
  ownership.

DRAIN ends when live open implementation-PR inventory is at or below the normal
ceiling. The PRs open at adoption are transitional grandfathered inventory only;
grandfathering permits them to drain, not to reproduce.

### Mechanical enforcement

Repository-declared flow state is not sufficient evidence of compliance. The BAMF
flow-control checker MUST reconcile its machine-readable ledger against live GitHub
state.

The live gate fails when an open BAMF implementation PR is absent from the ledger,
the ledger retains a closed or merged PR as open inventory, a newly admitted PR
violates DRAIN, a non-grandfathered `WAITING` or `BLOCKED` open PR lacks its
required retention exception, or multiple PRs claim an unapproved integration
surface.

CI MUST run the live reconciliation. During the initial drain epoch, the current
open implementation PR set is explicitly grandfathered so existing candidates can
merge or close; the global overage itself does not block the very merges needed to
reduce it. No new implementation PR is grandfathered automatically.

### Operational effect

Issue decomposition may remain fine-grained without producing matching PR
cardinality.

**Issues optimize ownership and specification. Commits optimize provenance and
reversibility. PRs optimize integration.**

**Relationship to ADR-124:** ADR-124 continues to limit simultaneous branch
mutation. Its definition of ACTIVE WIP is unchanged. This ADR adds a separate bound
on integration inventory.

**Relationship to ADR-125:** ADR-125 continues to govern remediation closeout and
parent-owned aggregate EGM. This ADR adds admission and inventory controls that
prevent remediation artifacts from recreating the same queue growth elsewhere.

**Human ratification:** The project owner explicitly directed this decision on
2026-11-02 after reviewing ADR-124/125 and requiring both a new ADR and stronger
mechanical enforcement.

**Initial drain attempt (reversed):** The first implementation temporarily
closed 17 parked `WAITING` PRs after preserving their branch/head/issue/resume
custody. This was an incorrect interpretation of DRAIN. The project owner clarified
that existing candidates must remain open while pinned EGM, remediation and
merge-readiness work proceeds. All 17 PRs were reopened at their original exact
heads; the implementation inventory returned to the 19 adoption-time candidates,
all of which remain grandfathered for this drain epoch. See the owner clarification
below.

**Status:** Accepted as the controlling BAMF-0.2 integration-inventory and PR
admission policy.

### ADR-126 Clarification | 2026-11-02 | Drain through EGM and merge, not bulk closure

**Owner clarification:** DRAIN means stop admitting new implementation PRs and reduce
existing inventory by satisfying its merge requirements, including fresh pinned EGM,
repairing candidates in place, and merging eligible candidates. It does **not** mean
closing every PR whose flow state is `WAITING`.

A PR awaiting required EGM review or other merge-readiness evidence is still an
actionable integration candidate. EGM review is a merge prerequisite, not a reason
to close the PR. Keep such candidates open while the authorized EGM/repair/merge
process is active. Do not close a PR solely to make the inventory number smaller or
to make the checker report NORMAL.

Close a parked PR only when it is genuinely superseded, duplicate, no longer
selected for integration, materially blocked with no active EGM/merge path, or
otherwise explicitly directed by the project owner. Preserve its exact head,
branch, issue and resume trigger before closure.

The bulk closure of 17 `WAITING` PRs performed during the first ADR-126
implementation on 2026-11-02 was an incorrect interpretation and was reversed.
All 17 PRs were reopened at their original heads. The existing 19 implementation
PRs are the one-time grandfathered drain inventory; the normal ceiling of three
still blocks new admission. The drain proceeds through EGM, repair and merge, not
through summary closure. This correction supersedes any contrary initial-drain
description in the first implementation of ADR-126.
## ADR-127 | 2026-11-03 | EGM review episodes are bounded, persistent, and root-cause routed

**Scope:** BAMF-0.2 implementation and merge-readiness review. This decision
governs how fresh-context Goldfish review is counted, invalidated, repeated, and
terminated across repair commits. ADR-125 continues to govern remediation
lifecycle and parent-owned aggregate EGM. ADR-126 continues to govern PR
inventory and drain behavior.

**Problem:** BAMF pins Google Elephant-Goldfish Model commit
`b3a35956759bf7f024af2ff061b2e0b44b438e4c` for reviewer/persona
reproducibility. That historical review-loop implementation repeats until zero
findings or explicit human halt. In BAMF practice, a whole-candidate review could
find one new Major, cause a repair and new exact head, then begin another
apparently fresh review cycle with no durable episode counter. Exact-head
reproducibility therefore interacted with repair churn as an accidental liveness
bug: changing the candidate revision could erase the operational history of how
many whole-candidate review rounds had already occurred.

The same failure pattern appears when mechanical proof gaps, shared-contract
defects, or unstable parent assumptions are repeatedly handed back to Goldfish as
if each were a new local semantic question. This spends fresh-context review on
facts that deterministic tooling or one canonical owner can settle, and can turn
review into an expanding remediation tree rather than a bounded merge-readiness
gate.

**Decision:** Preserve the pinned `b3a359...` checkout for historical
reproducibility of reviewer personas and standards, but do not inherit its
unbounded termination behavior as BAMF orchestration policy.

One merge-candidate lineage owns one persistent EGM review episode across ordinary
repair commits. The episode identity and round count survive exact-head changes
that repair findings from that same lineage. A new Git SHA does not reset the
episode.

The default episode cap is **five complete whole-candidate Goldfish rounds**.
One complete round with no unsettled Blocker/Major and no requested reviewer
missing or failed is sufficient for BAMF implementation merge readiness. At the
five-round cap, or when review churn is detected, automatic Goldfish review stops.
The candidate returns to design or requires explicit human authority to continue.
Rewriting, rebasing, merge-forwarding, or otherwise changing target bytes does not
silently mint another episode.

**Churn** exists when a later blocking finding reverses or materially conflicts
with a repair made to satisfy an earlier finding at the same ownership locus, or
when successive rounds repeatedly move the same contract boundary instead of
converging. Churn is a design/control signal, not a reason to consume an unlimited
number of additional reviewers.

### Finding basis and ownership

Every Blocker/Major must identify at least one blocking basis:

- a violated named requirement, invariant, or authority;
- a concrete in-scope failure scenario; or
- a missing required ownership, interface, or acceptance seam whose absence
  prevents correct implementation.

A reviewer preference, speculative future feature, or generalized desire for
additional future-proofing is not blocking by itself.

Before repair, classify the finding locus as:

- `TARGET_LOCAL`;
- `SHARED_CONTRACT`;
- `PARENT_INTEGRATION`;
- `AUTHORITY_GAP`; or
- `MECHANICAL_PROOF`.

Target-local defects may be repaired at the candidate. Shared-contract,
parent-integration, and authority defects are promoted to their canonical owner;
affected descendants pause rather than independently encoding competing local
repairs. If multiple late findings share one root premise or canonical owner,
promote one systemic finding and treat only the impacted subtree as stale.

### Proof routing

Use the cheapest proof mechanism capable of establishing the invariant.
Traceability, schema shape, counts, contract mirrors, source census, dependency
readiness, file/ABI identity, and other mechanically decidable facts belong in
validators, tests, or focused audits before Goldfish. A `MECHANICAL_PROOF`
finding closes through deterministic red/green proof and does not require a fresh
Goldfish round solely because its implementation changed.

Goldfish remains the review mechanism for adversarial semantic ambiguity, hidden
ownership, unsafe integration behavior, cross-boundary failure modes, and
implementation-readiness questions that deterministic proof cannot establish.

When the same mechanically recognizable defect class appears repeatedly, encode
that lesson in executable validation rather than paying fresh review cost every
time.

### Semantic staleness

Review applicability is invalidated by semantic impact, not arbitrary byte drift.
Classify candidate changes as:

- `NONSEMANTIC`: prose, formatting, bookkeeping, receipt/link cleanup. Existing
  review remains applicable.
- `MECHANICAL_CONFORMANCE`: machine-checkable traceability, mirror, census,
  schema, or identity repair. Deterministic proof is required; full fresh EGM is
  not required solely for this change.
- `LOCAL_SEMANTIC`: meaning or behavior changes inside one owned boundary.
  Re-review that scope.
- `DEPENDENCY_SEMANTIC`: consumed authority, interface, or source meaning
  changed. Re-review only impacted consumers.
- `ARCHITECTURE`: ownership, decomposition, or topology changed. Return the
  affected scope to design before implementation review resumes.

An unrelated reviewed-unified advance does not by itself stale a parked
candidate.

### Durable episode evidence

The owning issue records the episode ID, monotonic round count, latest reviewed
head, unresolved finding IDs/loci, and current disposition. That state survives
agent turnover and context compaction. Historical EGM receipts remain valid
provenance under the method/tool pin recorded when they were produced; this ADR
does not retroactively relabel them.

**Relationship to ADR-125:** ADR-125 already makes the parent candidate the owner
of aggregate EGM and prevents every remediation child from retaining its own
review queue. ADR-127 adds a finite review budget and root-cause routing to that
parent-owned aggregate review.

**Relationship to ADR-126:** ADR-126 drains integration inventory through EGM,
repair, and merge rather than bulk closure. ADR-127 prevents EGM itself from
becoming an unbounded reason that grandfathered integration candidates never
leave DRAIN.

**Human ratification:** On 2026-11-03 the project owner explicitly challenged the
absence of an ADR for this governance change. This entry records the controlling
decision rather than leaving the behavior only in agent instructions and an
execution guide.

**Status:** Accepted as the controlling BAMF-0.2 EGM convergence and review-episode
policy.

## ADR-128 | 2026-11-04 | Expand independent BAMF throughput and distinguish writer continuity from locks

**Status:** Accepted by direct owner instruction on 2026-11-04. Amends the
concurrency ceilings in ADR-124 and ADR-126; leaves their dependency, review,
source-gold, actual mutation safety and merge-authority requirements intact.

**Problem:** The original three-open-PR cap and one-candidate-per-lane expectation
serialized independent agents. Hosted CI also fetched mutable global GitHub PR
inventory and failed unrelated change sets when its live count/ledger timing
diverged. Separately, compacted agents sometimes treated the prior agent's
`ACTIVE` issue, worktree, branch or checkpoint as an exclusive lock held by a
different agent, declining to resume their own in-flight issue.

**Decision:** Permit up to **twelve** open BAMF implementation PRs overall, with
no per-lane PR cap; permit up to **six** simultaneous `ACTIVE` items in each lane.
Within those bounds, independent issue-scoped branches/worktrees and agent
writers can make progress concurrently. Hosted quality CI checks the static
flow-control schema/state but does not perform a live
GitHub PR-inventory reconciliation. The operator still performs the `--live`
inventory check at actual PR admission and resolves tracked-state drift then.
Where that optional live endpoint is unavailable (for example local TLS failure),
an alternative authenticated GitHub read is sufficient; network failure or
brief ledger lag does not itself prohibit opening an otherwise qualified PR.

**Compaction continuity:** A context compaction, handoff, unchanged `ACTIVE`
ledger item, previous agent identity, checkpoint comment or recorded worktree
does **not** grant another actor exclusive ownership of an issue. Recover on
the same preserved branch/worktree; inspect working-tree changes, local HEAD,
remote head and any actual concurrent writer before changing shared paths.
When a successor really is continuing the same work epoch with unchanged Git
state, it may continue without reacquiring the issue or inventing a lease.
Checkpoint comments and WIP ledgers are not atomic locks. Independent branches
on the same issue may exist, but they must not write to the same branch or
shared file concurrently without explicit coordination. An observed competing
process or unexpected remote mutation requires reconciliation before writing;
the mere existence of another worktree or previous agent name does not.

**Executable continuity receipt:** `scripts/bamf/writer_handoff.py` emits a
versioned JSON handoff bearing issue, execution epoch, canonical worktree path,
branch, local HEAD, upstream, exact live remote HEAD and content-sensitive dirty
worktree fingerprint. The resumed worker verifies that snapshot before editing;
matching state is `CONTINUATION_MATCH`, not a requirement to acquire the issue
again. A mismatch requires a targeted reconciliation of that field; neither
stale handoff nor tool/network failure establishes someone else's ownership.
Live remote verification is required for a positive match. A matching snapshot
does not grant exclusive process-level lock ownership, so actual concurrent
writers still require coordination.

**Preserved boundaries:** No forced pushes; no overwrite of another writer's
uncommitted work; no self-merge, bypass of scoped verification/EGM, or automatic
neural-training/optimizer/checkpoint mutation. PR-count and WIP expansions are
throughput permissions, not proof that a specific candidate is ready to merge.

**Implementation:** `AGENTS.md`, `docs/tasks/bamf-0.2/README.md`, the
flow-control policy, hosted `.github/workflows/quality.yml`, and focused tests.

## ADR-129 | 2026-11-04 | Passing verification remains valid until its dependency surface changes

**Status:** Accepted by direct owner instruction on 2026-11-04.

**Problem:** Several repository suites now cost roughly 10-15 minutes or more.
Agents and hosted CI have been rerunning them at branch/PR/agent boundaries even
when no intervening change could affect the behavior those suites established.
This consumes scarce execution time and serializes parallel work without adding
evidence.

**Decision:** Treat a successful test receipt as reusable evidence bound to its
exact tested head, suite identity and environment. A later candidate must rerun
that suite only when the diff since the tested head intersects the suite's actual
dependency surface: implementation code, fixtures/goldens, tests, generators,
dependencies, relevant runtime configuration, or the harness itself. Agent
handoff/compaction, PR metadata, governance/docs changes, flow-control policy,
unrelated CI orchestration, and merge commits carrying only such changes do not
invalidate behavioral suites. Where only a narrow dependency changed, run the
smallest affected check rather than the broad suite.

**Evidence rule:** If a prior pass is reused, record `TEST_EVIDENCE_REUSED`, the
prior tested SHA, current candidate SHA, comparison range and why no invalidating
path changed. Fresh broad verification remains mandatory when dependency impact
cannot be bounded, the prior receipt is missing/incomplete/untrustworthy, an
environment dependency changed, or the owner explicitly requests it.

**Hosted implementation:** `quality.yml` classifies the diff before expensive
verification and skips broad semantic/custody suites when their dependency
surface is untouched. Static governance/docs/architecture checks may still run.
Manual workflow dispatch intentionally requests a fresh run. The exhaustive
semantic workflow is no longer triggered merely because `quality.yml` changed.

**Application to ADR-128/PR #822:** The concurrency, compaction-handoff and CI
governance changes do not modify Bilqis semantic, Factory, custody, neural, source,
fixture or runtime behavior. Existing passing expensive-suite evidence therefore
remains applicable; this change requires only lightweight structural/workflow
validation, not another broad test campaign.

## ADR-130 | 2026-11-05 | Gate scope expansion, not decomposition

**Status:** Accepted by direct owner instruction on 2026-11-05.

**Problem:** ADR-127 can stop an EGM loop only after substantial work has already
been spent. But treating issue/branch creation itself as the waste would recreate
the opposite failure: giant tickets, serialized execution, slow turn-in, late
failure discovery, and poor parallelism. BAMF's recursive decomposition exists to
avoid exactly that.

**Decision:** Distinguish **decomposition** from **scope expansion**. A child that
inherits a strict subset of already-authorized required acceptance and adds no new
obligation may be given its own issue, branch/worktree, and PR whenever that improves
parallelism, failure locality, review isolation, turn-in speed, or information yield.
Its minimal receipt names the parent, exact inherited clauses, and
`new_acceptance=false`. It does not need to prove that creating the child is itself
a present blocker.

Only a delta that cannot be traced to existing required acceptance is scope
expansion. Before spending on that delta, record in at most 120 words the current
delivery, named requirement/blocker, concrete consequence of deferral, and cheapest
adequate next step; classify it `PROCEED`, `PARK`, or `DROP`. `PROCEED` means the
new obligation is required for current delivery/correctness/safety. `PARK` preserves
only a small pointer until selected. `DROP` ends spend.

New remediation issue bodies should remain concise (about 250 words or less by
default), pointing to inherited/versioned authority under ADR-118. Crossing 3
commits, 3 touched files, or 250 net changed lines is a **scope-drift tripwire**, not
a command to absorb the child back into its parent. Re-check clause traceability:
if all work is still inherited, continue and decompose again when useful; only the
untraceable delta requires expansion authority. Discovery of a second independent
problem gets the same classification.

EGM remains a merge-readiness tool for already-authorized scope. It may discover a
real defect, but cannot by itself convert a peripheral improvement into a new project
obligation. This rule suppresses net-new scope creep while preserving aggressive
decomposition as a throughput strategy.

**Diagnostic spend is also governed:** a manually constructed end-to-end probe is
not exempt merely because it is not called a test. Repeating an expensive probe with
unchanged relevant code and inputs adds no evidence and should reuse the prior
result. Repeated parameter exploration must amortize invariant setup in one process.
After two unsuccessful full-cost attempts under the same hypothesis, further
end-to-end execution pauses until a cheaper staged/profiled diagnostic changes the
evidence. Compaction must preserve in-flight probe status to prevent duplicate runs.

## ADR-131 | 2026-11-05 | Expensive qualification diagnosis follows decision precedence and preserves full authority at the boundary

**Status:** Accepted by direct owner instruction on 2026-11-05 after the #708 C05
source-owned acceptance witness required 1768.874 seconds and returned only a
generic rejection.

**Problem:** A logically single acceptance assertion can hide a large qualification
workload. The #708 C05 witness currently spans 6 fresh-target cases, 24 fresh
same-grade cases and 43 fixed-school cases. Its present construction performs 73
instrument compilations, another parent and candidate compilation for each case,
and 146 parent/candidate solves before the test can report acceptance. When an early
retention predicate already determines rejection, eagerly paying the remaining
cohort cost adds no diagnostic evidence. Worse, a generic Boolean rejection after a
multi-minute run forces another expensive execution merely to learn which predicate
failed.

**Decision:** Expensive acceptance/retention diagnosis must follow the production
decision's rejection precedence. Evaluate the cheapest decisive predicate first and
stop when its result already fixes the production outcome. For C05 this means
testing the exact fresh-target cohort first; only positive target gain justifies
fresh same-grade evaluation, and only a surviving same-grade result justifies the
fixed-school screen. The diagnostic may reuse the exact production source rows,
candidate state, solver semantics and policy inputs, but remains explicitly
**non-authorizing**. It must not issue a Factory retention evaluation, accepted
generation, or equivalent production authority. The full owner-controlled screen
remains the sole acceptance authority and runs at the final stable boundary after a
cheaper diagnostic has demonstrated a relevant repair.

**Cost discipline:** Invariant setup is hoisted and reused within one process where
semantics permit: source compilation, Factory/model construction, bundle loading,
custody validation and other unchanged setup must not be rebuilt per seed, case,
parent/candidate comparison or diagnostic stage merely for convenience. Before a
multi-minute witness is launched, the operator should account for case count,
repeated compilation/setup passes and solve count, then split mechanically separable
cost from semantic proof. This extends ADR-129's evidence-reuse rule and ADR-130's
diagnostic-loop budget from rerun prevention to the internal structure of a single
expensive witness.

**Observability:** Every expensive rejection path must report the exact rejection
reason and enough stage timing/score evidence to determine the next bounded
diagnostic. A multi-minute witness that returns only `accepted = false` or an
equivalent generic assertion is not an acceptable debugging interface. Repair that
observability before repeating the same execution family.

**Preserved boundaries:** This ADR does not weaken C05, alter retention thresholds,
replace source-qualified evidence with synthetic fixtures, or authorize acceptance
from a partial screen. It changes the development and diagnostic path only. The
final production acceptance witness remains complete and authoritative.

## ADR-132 | 2026-11-05 | Long local commands detach from interactive agent sockets and notify the operator

**Status:** Accepted by direct owner instruction on 2026-11-05.

**Problem:** Some legitimate BAMF qualification, EGM, neural and integration tasks
cannot always be reduced below several minutes. Holding an interactive execution
socket open while such a command runs consumes platform resources, degrades service
quality, and encourages agents to sit in a polling loop rather than yield cleanly.
The repository therefore needs a durable asynchronous handoff for local computation,
not merely a request that agents "wait less."

**Decision:** Five minutes is the interactive socket ceiling. Any local command that
could plausibly exceed it is launched detached with
`scripts/bamf/detached_long_run.py`. The launcher gives the child an independent
session, closes interactive stdin, writes a durable PID file, combined stdout/stderr
log and machine-readable completion receipt, and on macOS emits a desktop
notification with the `Glass` sound when the command exits. The initiating agent
verifies launch only, reports the artifact paths and continuation instruction, then
ends its turn. It does not hold the chat/tool socket open and does not poll.

After the notification, the human returns control to an agent. That agent reads the
completion receipt and log, reconciles the result against current Git/worktree state
and continues from the recorded outcome. The detached command is computation, not a
background agent: it may not make unapproved external/public/destructive decisions,
self-merge, or infer authority from successful exit.

**Failure semantics:** Missing receipt, stale PID, command crash, notification
failure, or ambiguous external side effect is not success. Reconcile the durable log
and target state before retry. The five-minute boundary does not justify detaching an
interactive command that requires human input or credentials mid-run; such work must
be redesigned or explicitly handled at its interaction boundary.

**Implementation:** Root `AGENTS.md` plus
`scripts/bamf/detached_long_run.py`. This ADR composes with ADR-129 evidence reuse,
ADR-130 diagnostic-loop budgeting and ADR-131 precedence-ordered qualification.

## ADR-133 | 2026-11-05 | Foundation learning accepts taught acquisition; fixed generalization gates wait for maturity

**Status:** Accepted by direct owner correction on 2026-11-05; measurement semantics refined by ADR-134.

**Problem:** The repository repeatedly reintroduced conventional held-out and
generalization requirements while Bilqis still had a tiny semantic inventory. This
conflicted with the intended developmental curriculum and with the architecture's
deliberate use of exact retrieval, memoization, caches, motif memory and rote learning.
It also turned foundation integration witnesses into premature transfer tests.

**Decision:** The current stage is FOUNDATION_ACQUISITION. Teacher-forced gold may be
present in teaching and integration witnesses. The same specimen may be taught and
replayed. Exact memorization, cache retrieval, memoized procedures and learned memory
are valid successful mechanisms. Foundation acceptance may use
TEACHER_FORCED_ACQUISITION, EXACT_TAUGHT_RECALL or
TAUGHT_COMPOSITION_REPLICATION. It does not require a held-out specimen, independent
source family, fresh episode, unseen filler or novel composition.

Generalization, transfer and independence tests remain useful instruments, but they are
not live acceptance gates. ADR-134 clarifies that BAMF-0.2 alpha should measure them
continuously as non-authorizing competence-frontier telemetry rather than leaving them
dormant. Any later fixed novelty or held-out gate requires explicit human admission.

**Structural enforcement:** The machine authority is
`docs/specifications/developmental_evidence_policy.json`. Root guidance, SPEC-0001,
BAMF-0.2, C05 and C16 carry the FOUNDATION_EVIDENCE_POLICY_ACTIVE marker.
`scripts/check_factory_architecture.py` validates the policy and those markers so a
later edit cannot silently restore premature generalization as a foundation gate.

**Still enforced:** Source correctness, rights, semantic identity, custody, rollback,
protected-retention limits and human neural-update authority remain active. This ADR
changes developmental evidence maturity, not those safety or provenance boundaries.

## ADR-134 | 2026-11-05 | Alpha advancement follows earned complexity; novelty is measured, not gated

**Status:** Accepted by direct owner correction on 2026-11-05. This refines ADR-097
and ADR-133 for BAMF-0.2 alpha.

**Problem:** Treating held-out or generalized performance as a separate pass/fail gate
misrepresents Bilqis's developmental training regime. The system intentionally builds a
large explicit semantic memory through repetition, retrieval, composition and gradual
curriculum growth rather than learning from trillions of stochastic examples. Exact
repetition therefore remains useful evidence even when a specimen has been seen many
times. The curriculum's rising semantic breadth and composition complexity already
create increasing difficulty.

**Decision:** BAMF-0.2 alpha advancement uses the success ratio at the learner's current
earned complexity. Previously shown examples count fully. Training and evaluation pools
may grow incrementally or logarithmically as the curriculum expands. Generalization,
transfer and novelty remain continuously measured, but no held-out, fresh-family or
novel-composition result may independently veto retention, promotion or graduation.
Candidate retention also does not require an immediate target-score increase from every
optimizer step. Non-destructive intermediate updates may accumulate. The existing
teacher-owned no-gain retirement remains responsible for abandoning strategies that
repeatedly fail to produce useful learning.

Novelty diagnostics should begin with small meaning-preserving changes such as surface
name substitutions, then increase role changes, relation polarity changes, composition
depth, distractors and semantic distance. Record pass/failure ratios by complexity and
variation distance and report the first region where competence breaks down. This
competence frontier is more useful during alpha than a binary generalization gate.

**Interpretation:** A correct answer may come from exact memory, cache retrieval,
memoized procedure, learned weights, deterministic composition or another authorized
route. Familiarity does not invalidate the answer. A later fixed held-out/generalization
gate requires a new explicit human decision.

**Structural enforcement:** docs/specifications/developmental_evidence_policy.json
sets generalization_status=MEASURE_ONLY, keeps novelty non-authorizing, and defines
alpha advancement as CURRENT_EARNED_COMPLEXITY_SUCCESS_RATIO.
scripts/check_factory_architecture.py validates these fields and the active
FOUNDATION_EVIDENCE_POLICY_ACTIVE markers.

## ADR-135 | 2026-11-05 | Detached long runs execute from digest-pinned source snapshots

**Status:** Accepted by direct owner instruction on 2026-11-05 while the #708/#709
acceptance witness was active.

**Problem:** ADR-132 detached long work from the interactive socket but still executed
the command and any later subprocesses from the live mutable worktree. A long parent
process could therefore import one version of a module, then spawn a clean child after
an agent edited the same worktree, causing source and destination arms of one witness
to execute different code. Avoiding edits by convention is not concurrency control.

**Decision:** Every new detached long run must first materialize a complete source
snapshot of its requested worktree, excluding only non-source/runtime-cache roots such
as `.git`, `.local`, virtual environments, bytecode caches and `node_modules`. The
launcher verifies that the source digest is stable across the copy and that the copied
tree has the same digest, rejects source symlinks that escape the worktree, then starts
the detached worker from the copied runner inside that snapshot. The command executes
with the snapshot as cwd, so recursively spawned relative-path Python processes inherit
the same source image even while development continues in the original worktree.

The receipt records original worktree, snapshot path, source digest and snapshot
digest. The worker re-verifies the snapshot before command execution and again after
the command. If the command mutates its own source snapshot, the run fails even when
the command itself returned zero. Run-local logs, receipts and PIDs remain outside the
snapshot. Snapshot isolation is the concurrency mechanism; promises not to edit the
live worktree are not.

**Transition:** A detached process already launched under the v1 runner cannot be
redirected into a snapshot without changing its execution environment mid-witness.
Such an in-flight v1 run keeps its relevant source surface frozen until completion;
all newly launched runs use the v2 snapshot contract.

## ADR-136 | 2026-11-07 | Semantic artifact authority is pathless and portable

**Status:** Accepted by direct owner correction on 2026-11-07 while resolving the
#697 B13.5 capped-review multi-release replay finding.

**Problem:** B13 accepted-generation feature replay carried the correct immutable
Atlas bundle/release/source identities but still required a caller-supplied local
`artifact_path`. That makes a host pathname participate in historical authority,
prevents one argument from naming multiple historical releases, and makes exact
replication brittle when custody is copied to another machine or mounted under a
different root.

**Decision:** Filesystem paths are storage placement, never semantic identity or
authority. Portable receipts and accepted historical lineage bind immutable
content/source identities. A machine-local artifact resolver may translate those
identities to whatever local path currently contains the bytes, but that location
is below the authority boundary and is not part of the semantic receipt. Every
resolved Atlas artifact must still pass the existing registered A01 source pin and
exact bundle, release and source-bundle identity checks before use.

B13 historical replay must resolve each generation's own source identity rather
than reuse one caller path across the lineage. Copying an accepted run and its
required immutable source custody to a different root or machine must reproduce
the same accepted-generation feature receipt and content identity. Missing,
substituted, corrupted or unregistered source content fails closed.

**Scope:** This does not transfer A02/#399 authority into B13, authorize new
semantic admission, or change neural state. Reuse existing content-addressed/Data
Plane storage primitives where they fit; do not create a second path-as-authority
registry under another name.

## ADR-137 | 2026-11-08 | Separate design review, implementation proof, drift, and integration

**Status:** Accepted by direct owner instruction on 2026-11-08 after reviewing the
project's recent BAMF execution history and the intended Elephant-Goldfish Model
lifecycle.

**Problem:** BAMF had gradually repurposed fresh EGM Goldfish review into a
post-implementation merge-readiness loop. That mixed four different questions:
whether a design was ready to implement, whether the implementation behaved
correctly, whether the implementation still matched the approved design, and whether
the exact candidate was ready for integration. The overlap caused repeated broad
review and test cycles, consumed expensive evidence after its relevant fact was
already established, and encouraged agents to rerun work after context changes rather
than reuse valid receipts.

The same execution history also showed a language-quality problem. Bilqis is an
ML/runtime, provenance, lifecycle, and state-consistency project, but descriptions of
ordinary correctness work sometimes borrowed terminology from unrelated technical
domains. Automated systems and human reviewers may classify work partly from the
language used to describe it. Inaccurate framing can therefore cause benign work to
be misclassified, producing avoidable warnings, latency, resource consumption, and
workflow interruption. The project needs descriptions that are both technically
exact and faithful to the actual domain.

**Decision:** BAMF now uses the lifecycle

`DESIGN -> EGM REVIEW -> IMPLEMENT -> VERIFY -> DRIFT -> PREMERGE -> HUMAN REVIEW`.

EGM review is a pre-implementation design/specification gate. Goldfish review the
design using only the personas and standards appropriate to the unresolved design
questions. In particular, Implementation Readiness evaluates whether a plan can be
executed without unresolved design choices; it is not a finished-code review rubric.
`EGM-Pending`, `EGM-Passed`, and `EGM-Failed` therefore describe design-review
state. Historical uses of those labels under the earlier convention remain
provenance and are not rewritten.

Implementation correctness is established through claim-first differential
verification. Before running a check, identify the claim, changed surface, prior
evidence, reason that evidence no longer settles the claim, and the cheapest next
proof. Escalate from deterministic checks to focused regressions, affected owner
tests, dependency-closure integration tests, expensive witnesses, and finally the
premerge aggregate gate only while relevant uncertainty remains. Passing evidence is
reused until a change can plausibly invalidate the assumptions on which it depends.
Agent turnover, elapsed time, issue bookkeeping, or equivalent branch movement do not
by themselves invalidate proof.

When implementation becomes behaviorally stable, compare the approved design with
the code that implements it. Drift analysis is bounded to the approved design,
implementation surfaces, and directly affected shared contracts. Differences are
classified as implementation defects, design drift, design evolution, documentation
staleness, or no drift. A code repair that restores the already-approved design uses
focused engineering verification; only a genuine design change returns the affected
design scope to EGM.

Integration uses the minimum sufficient evidence set that makes the current decision
defensible. Expensive witnesses are terminal proofs for requirements that cheaper
evidence cannot establish, not ordinary debugging loops. Broad aggregate verification
runs at an actual integration boundary and is reused when its exact assumptions
remain valid.

**Language discipline:** New issues, specifications, implementation plans, review
assignments, findings, test descriptions, commits, pull requests, handoffs, and
receipts should describe the software relationships actually being evaluated:
component ownership, canonical sources of truth, provenance, lineage, state and
identity consistency, lifecycle transitions, validation order, acceptance and
publication, retry/recovery behavior, compatibility, reproducibility, design
fidelity, concrete mismatched inputs, and deterministic proof.

Describe the expected relationship, observed relationship, exact difference, smallest
material consequence, and evidence directly. Existing code symbols, schemas, issue
identifiers, and externally defined terms remain verbatim where necessary; surrounding
prose explains their actual software role. This changes wording and process routing,
not correctness requirements.

**Structural enforcement:** `AGENTS.md` and
`docs/tasks/bamf-0.2/EGM_EXECUTION.md` carry the canonical lifecycle. Lane A/B/C
execution entrypoints delegate to it. `scripts/verify_bamf_0_2_contracts.py` checks
the lifecycle marker and design-first EGM rule, and its focused regression protects
the cutover. Existing differential-test receipts, dependency mapping, diagnostic-loop
budgets, precedence-ordered diagnosis, and snapshot-pinned detached execution remain
the proof-economy mechanisms for implementation work.

## ADR-138 | 2026-11-11 | MLX verification is resource-bounded; planner budgets are not allocator guarantees

**Status:** Accepted by direct owner instruction after the 2026-11-11 #354
qualification run exhausted host memory and swap.

**Observed incident:** The #354 differential leaf gate launched pytest-xdist with
four persistent workers. The selected dependency cone was MLX-capable and included
model, optimizer, custody, serialization, gradient, and full-model-adjacent tests.
During the run macOS repeatedly reported that the system had run out of memory,
Activity Monitor showed extreme Python memory accounting, xdist workers died, and
the 96 GiB M3 Ultra reached approximately **65.2 GiB used swap**.

Fresh-process inspection of installed MLX 0.31.1 established the mechanism:
`mx.set_cache_limit(0)` returned a previous default free-buffer cache limit of
`97,925,254,348` bytes, and `mx.set_memory_limit(1 GiB)` returned the same
previous default memory limit. That is about **91.2 GiB per process**. Four
unconstrained MLX-capable xdist workers therefore permitted about **364.8 GiB** of
aggregate MLX-managed demand before ordinary Python memory, the operating system,
other applications, or concurrent workstreams were counted. Exact instantaneous
attribution among live tensors, allocator cache, compressed memory, and swap is not
required to establish the failure: the parallel worker topology admitted demand far
beyond host capacity and the host demonstrably exhausted memory and swap.

**Decision for verification:** MLX-capable tests are serialized unless a future
harness proves and enforces a safe aggregate memory budget. Agents set
`BILQIS_TEST_WORKERS=1` and must not use pytest `-n > 1` for any selected suite
that imports MLX directly or can reach MLX transitively through BAMF model, optimizer,
custody, serialization, gradient, or full-model owners. Long-lived MLX test
processes disable the free-buffer cache with `mx.set_cache_limit(0)` and
`mx.clear_cache()`, or use the repository memory-policy context where appropriate.
Parallel MLX becomes lawful only when every worker has an explicit applied memory
policy and the sum of worker limits plus host headroom fits the machine.

Detached execution under ADR-132/135 is orthogonal to resource safety. A detached
process may still exhaust the host. Before launching an expensive MLX witness,
inspect current swap/memory pressure and concurrent MLX-heavy jobs. Do not overlap
full-model witnesses by default. System out-of-memory warnings, near-saturated swap,
OOMs, or memory-pressure worker deaths invalidate the run; preserve the receipt/log,
terminate the owned process group when needed to protect the host, diagnose the root
cause, and do not rerun the unchanged workload.

**Decision for production training:** The production operator remains one sovereign
MLX writer. `runtime/operating_loop.py` enters `training_memory_policy(mx)`, which
sets the MLX free-buffer cache limit to zero for the long-running trainer; therefore
the specific four-process cache multiplication that caused this incident is not an
expected production topology.

However, C08's current **48 GiB trainer envelope is an analytical planning budget,
not a hard allocator guarantee**. The planner uses it to choose/reject
microbatches, but current production execution does not enforce a corresponding
`mx.set_memory_limit(48 GiB)`, and the implemented C08 MLX telemetry/OOM
restore-and-retry machinery is not yet connected around the production candidate
gradient execution seam. Until those runtime controls are wired and verified,
agents must describe 48 GiB as a planned envelope, not a measured or enforced peak.

Before the first durable successor training run is treated as resource-qualified,
the disposable/current-production execution path must record actual MLX active,
cache, and peak memory together with process/system memory pressure and swap delta,
compare them with the C08 estimate, and prove that any OOM follows the retained-state
restore/retry contract rather than destabilizing the host or student. This resource
qualification does not authorize an agent to start or resume the human-owned durable
trainer.
## ADR-139 | 2026-11-11 | Expensive verification uses fail-fast staged preflight before full execution

**Status:** Accepted by direct owner instruction on 2026-11-11 after issue #374
repeatedly spent full Factory/MLX execution time before exposing cheap fixture and
test-contract defects.

**Problem:** A long-running test can contain three different kinds of work: cheap
contract validation, production-fixture setup, and the expensive computation that
actually requires MLX or a full model. When these are bundled into one opaque test,
a trivial defect at the end can consume the full cost of the expensive phase before
the developer learns anything useful. During #374, one real-Factory witness ran for
about 25 minutes before a missing observation-fixture field failed. The next ran for
about 27 minutes before a stale authority-digest assertion failed, even though the
neural path had already completed. Both failures could have been detected without
paying the full neural cost.

**Decision:** Expensive verification is an ordered pipeline. The repository uses the
following stages whenever a test or witness contains a multi-minute Factory, MLX,
full-model, or equivalent expensive phase.

1. **Repository-static preflight.** At integration/turn-in boundaries, run every
   applicable neural-inert quality/static gate before mounted real-fixture or
   full-model work. Governance, documentation, source/authority scanners,
   changed-file quality, and other deterministic repository checks belong here.
   A cheap static failure discovered after expensive execution is a harness-ordering
   defect and must be moved ahead of the expensive stage before another rerun.
2. **Cheap contracts.** Run focused neural-inert checks for imports, fixture shape,
   deterministic invariants, assertion semantics, and other preconditions that do
   not require the expensive output.
3. **Real-fixture preflight.** When production artifacts or custody matter, use the
   real artifact/configuration and the same shared setup as the full witness. Execute
   every cheap production operation through the immediate boundary before the
   expensive call, including applicable accepted-runtime, custody, generation,
   feature-authentication, target, route, observation, and resource-plan checks.
   Stop before the expensive computation itself.
4. **Expensive execution.** Start the full witness only after every required earlier
   stage succeeds. Preserve the exact production acceptance path for facts that
   genuinely depend on the expensive computation.

The staged runner must enforce this ordering and abort on the first failure. A
required preflight may not pass because pytest skipped the case. The runner must
verify that required external artifacts, runtime state, and custody inputs exist and
are usable, and it must distinguish `passed`, `failed`, and `skipped/not-run` rather
than treating process exit code zero as sufficient proof.

**Aggregate selection:** A test module that declares
`BILQIS_LEAF_GATE_POLICY = "DETACHED_ONLY"` is not part of default aggregate test
discovery. Such witnesses run only through explicit targeted execution or their
dedicated detached harness, where their artifact, resource, mutation, and receipt
contracts can be enforced. Broad premerge verification must not accidentally repay
or bypass a separately governed expensive witness.

**Shared-path requirement:** Preflight and full witness share setup, fixture, and
assertion helpers wherever semantics permit. A hand-copied lightweight imitation is
not sufficient because it can drift from the expensive path. Cheap preflight should
reach the actual seam immediately before the expensive call, or use an explicit seam
that proves equivalent production inputs and checks. Expensive-output-specific
assertions remain in the final witness, but every assertion contract that can be
tested synthetically should also have a focused cheap regression.

**Failure learning:** If a full-cost run discovers a banal fixture, import,
precondition, or assertion-contract defect, repairing that defect is not enough. Add
or strengthen an earlier stage so the same defect class fails before expensive
execution on the next run. This converts diagnostic history into a durable test
boundary instead of relying on agent memory.

**Execution and authority:** ADR-132 still governs commands that can exceed five
minutes. The complete staged pipeline runs detached from a digest-verified source
snapshot, emits stage markers into its durable log, stops immediately on failed
preflight, notifies the operator on exit, and is never polled from chat. Preflight is
diagnostic and non-authorizing. Only the complete production witness can satisfy an
acceptance requirement that depends on the expensive computation. This ADR composes
with ADR-129 evidence reuse, ADR-130 diagnostic-loop budgeting, ADR-131
precedence-ordered diagnosis, ADR-132 detached execution, and ADR-137 claim-first
verification.

## ADR-140 | 2026-11-11 | M3 Ultra verification concurrency is bounded per job, not serialized host-wide

**Status:** Accepted by direct owner instruction on 2026-11-11 after C08 turn-in
needlessly waited behind other bounded MLX verification jobs.

**Context:** ADR-138 correctly diagnosed the 2026-11-11 OOM incident as an
unbounded aggregate-allocation failure. Four MLX-capable xdist workers each inherited
a roughly host-sized default allocator/cache allowance. The resulting rule was too
coarse when applied as host-wide serialization. Independent detached jobs with
explicit limits differ from unconstrained xdist workers inside one runner. The M3
Ultra is expected to execute multiple bounded jobs concurrently.

**Decision:** MLX-capable pytest remains single-worker within one runner unless that
runner proves an aggregate budget. Independent MLX/full-model jobs may run
concurrently on the M3 Ultra when every job applies a memory/cache policy. Their
configured aggregate ceilings must leave host headroom. Another bounded MLX job is
not a blocker. Agents must not insert a host-wide wait merely to avoid concurrency.

Current swap occupancy is an observation, not an automatic veto. Launch decisions
use applied job limits and actual physical-memory pressure/headroom. Refuse or stop
work when a participating job is unbounded. Do the same when configured aggregate
ceilings exceed safe host capacity or the OS reports memory-pressure/OOM symptoms.
Preserve per-job RSS/wall guards and detached receipts. One job can then be contained
without serializing unrelated bounded work.

This ADR supersedes only ADR-138's host-wide no-overlap interpretation. ADR-138's
measured OOM incident, single-worker default inside a runner, cache containment,
explicit memory limits, and production-trainer distinction remain in force.

## ADR-141 | 2026-11-12 | Verification test suites have a two-hour wall-clock ceiling

**Status:** Accepted by direct owner instruction on 2026-11-12 after the C06 #379
turn-in showed that a leaf-development witness had absorbed later system
qualification and ran for about 9 hours 51 minutes before a whole-school rejection.

**Problem:** ADR-129, ADR-137 and ADR-139 already require evidence reuse,
claim-first differential verification and fail-fast staged preflight. ADR-132 governs
detached execution for commands that can exceed five minutes. Those controls reduce
waste and protect the agent session, but they do not set an absolute wall-clock
limit. A test can therefore remain technically lawful while still consuming most of
a working day, delaying review and mixing unrelated system qualification into
ordinary development feedback.

**Decision:** No agent may launch or require a test suite, verification command,
hosted verification workflow, witness, or composed verification run whose planned or
expected wall-clock duration exceeds **2 hours**. Two hours is an absolute ceiling,
not a target. Normal leaf development and turn-in should use checks that complete in
seconds to minutes whenever the claim permits it.

Before launch, use prior receipts, selected-test scope, stage timings, or another
concrete estimate to bound the expected duration. If the bound is unknown or can
exceed two hours, the run is not ready to start. Split it into claim-specific stages
that each stay within the ceiling and emit durable receipts. Arbitrary time slicing
does not satisfy this rule: every stage must prove an independently meaningful claim
and have explicit inputs plus a resumable or terminal result.

If an agent-launched test reaches two hours without completing, stop or contain the
owned process at the next safe boundary. Preserve its partial log and receipt, and
record the result as incomplete or over-budget rather than PASS. Diagnose the
expensive stage and convert any discovered fixture, assertion, ownership or contract
failure into a cheaper deterministic regression before another attempt. Still-valid
passing evidence remains reusable and must not be repaid solely because a session
resumed, a branch moved equivalently, or time elapsed.

Detached execution, snapshot isolation, bounded MLX concurrency and operator
observation do not waive the ceiling for tests. Whole-system qualification that
cannot be made meaningful within two hours is not an ordinary test gate. Redesign it
as bounded staged qualification, or hand it to the human operator as a separately
authorized non-test training or production exercise. A multi-stage qualification may
span more than two hours in aggregate only when each stage is independently bounded,
interpretable and receipted; it may not disguise one opaque monolithic test behind
restarts.

Historical test evidence from runs longer than two hours remains valid provenance and
is not erased by this decision. This ADR changes future verification posture, not the
historical record. Only a new owner-ratified ADR amendment may raise or remove the
two-hour ceiling.

**Relationship to existing decisions:** ADR-137 still governs claim-first proof and
evidence reuse. ADR-139 still governs fail-fast staging. ADR-132 still requires
detached execution for sufficiently long commands. ADR-138 and ADR-140 still govern
MLX memory and concurrency. ADR-141 adds the wall-clock ceiling above those controls.

