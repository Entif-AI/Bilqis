# Bilqis MLX

## BAMF-0.2 unified execution base — 2026-10-28

This branch starts from the current Factory implementation and keeps that Factory
code authoritative for runtime, trainer, scheduler, teacher, retention, admission,
and controller behavior. Do not reintroduce newer `main` controller logic merely
because `main` has advanced. BAMF work changes those surfaces only through an
explicit BAMF issue that is implemented and verified against this branch.

The shared BAMF planning contract is [BAMF-0.2](docs/architecture/BAMF_0_2.md),
including `ADR-BAMF02-004`, and
its recursively decomposed workstack under [docs/tasks/bamf-0.2](docs/tasks/bamf-0.2/README.md).
The New Ithkuil semantic source is the imported SKOS corpus under `lib/ithkuil/`,
including its content-addressed test policy and ingestion Skill. These planning and
semantic assets do not by themselves alter the existing Prometheus student or
authorize neural updates.

`codex/bamf-unified-base-20261028` is a **living reviewed integration trunk**, not
a frozen museum branch. The three implementation lanes are:

- Lane A semantics/factory: `codex/bamf02-a-semantics`
- Lane B neural architecture: `codex/bamf02-b-neural`
- Lane C runtime/integration: `codex/bamf02-c-runtime`

Before each implementing issue begins, its lane branch fetches and merges the
current `origin/codex/bamf-unified-base-20261028`, records the unified SHA it
consumed, resolves any conflicts, and verifies the affected seam before making
issue-owned edits. Lanes do not merge `main` or sibling lanes directly. When an
issue satisfies its owned acceptance, its lane pushes and opens a PR back into the
unified trunk for human sign-off; the issue never authorizes self-merging that PR.
Accepted cross-lane work becomes available to the other lanes through the next
issue-boundary sync from unified.

**Portable artifact authority:** host-local filesystem paths are storage placement,
not semantic identity or authority. BAMF receipts and historical source replay must
bind immutable content/source identities and remain valid when the same custody is
copied to another machine or mounted under a different root. A local resolver may
use paths internally to find bytes, but callers must not supply a pathname as the
authority for accepted historical lineage; resolved content must still pass its
own source-pin and digest checks. See ADR-136.

## BAMF-0.2 GitHub Project dashboard contract — 2026-11-03

The `BAMF-0.2 Execution` GitHub Project is an observability surface. It does not
own execution state, EGM state, issue state, dependency authority, or merge
readiness. Repository issues and labels, ADRs, the BAMF task registry,
flow-control records, dependency evidence, and execution receipts remain
authoritative.

- `BAMF-Leaf` is a one-time structural projection of the current BAMF leaf set for
  dashboard filtering. Do not add automatic leaf-label synchronization or treat
  the Project as the source of leaf identity.
- EGM state is read from the canonical issue labels `EGM-Pending`, `EGM-Failed`,
  `EGM-Mitigation`, and `EGM-Passed`. Do not duplicate EGM state in a Project
  field or encode it in PR status tokens.
- Project views, charts, and filters may summarize authoritative repository state.
  They must not create a competing workflow state machine.
- Project `Status` is not issue-close authority. Keep the Project workflow that
  closes an issue merely because `Status` becomes `Done` disabled.
- For a bounded implementing issue, once its accepted implementation PR is
  confirmed merged into the owning reviewed integration target and the issue's
  acceptance/EGM obligations are satisfied, close the issue as `completed`
  immediately. Do not leave merged work open for later bookkeeping cleanup.
- BAMF implementation PRs commonly merge into the reviewed unified trunk rather
  than the repository default branch, so do not rely on GitHub's default linked-PR
  auto-close behavior. The closeout operator must read back the merge and close
  the owning issue explicitly. A later regression may reopen that issue or create
  a new one.
- Group/integration parents remain open while their own aggregate acceptance,
  child, hold, or remediation scope is unresolved, even when one scoped child or
  structural PR has merged.

## Mandatory development structure discipline — 2026-10-29

**This rule is a development interruption contract, not a repository-wide cleanup
order.** Whenever an agent encounters an already-oversized project-authored code
file, or causes one to cross the trigger while working, it MUST stop the current
task before continuing ordinary feature work.

- **File trigger:** a project-authored code file with **more than 360 lines of
  code** (`>360 LoC`). Preserve the complete active task context in **@Entif Work
  Stack**, pause that task, and refactor the encountered production file into
  cohesive imported submodules. Refactor its companion tests along the same
  ownership seams. If code moves to `new_method.py`, its focused tests move to
  `test_new_method.py`. Continue the interruption until the original production
  file **and every companion test file are each under 240 LoC** (`<240`). Commit
  the refactor normally on the already-active feature branch, then resume the
  preserved Work Stack task.
- **Directory trigger:** a directory containing **18 or more direct
  project-authored code files** (`>=18`), excluding child directories and
  third-party/external libraries. Preserve the active task in Work Stack, then
  reorganize **that one offending directory only** into cohesive subdirectories
  until the originally offending directory contains **no more than 12 direct code
  files** (`<=12`). Do **not** recursively inspect or clean the newly created
  subdirectories during the same interruption. Commit the reorganization on the
  current branch and resume the preserved task.
- **Organic scope:** repair one encountered offender at a time. Do not launch a
  recursive repository sweep merely because another oversized file or directory
  probably exists. A later offender is handled when ordinary work encounters it.
- **Governance integrity:** agents MUST NOT raise these thresholds, weaken the
  checks, expand/grandfather a quality baseline, add exclusions, or rewrite the
  rule merely to make a violation disappear. A change to this contract requires
  explicit human ratification. Mechanical checks complement the encounter-time
  agent duty; passing CI does not erase an encountered violation.

## CONTROLLING USER CORRECTION — 2026-10-23: factory specs are not semantic-root tickets

Issue #150 is a factory-architecture epic. Its decomposition exists to make the
factory able to accept future source-qualified semantic roots and capabilities
without redesigning generic runtime machinery. Do **not** create one specification
or GitHub issue per future semantic root merely to populate the workstack. Leaf
specifications own reusable factory invariants, ownership boundaries, migration
seams, compatibility boundaries, or proofs. A particular semantic root belongs in
this corpus only when it exposes a genuinely reusable missing factory mechanism.
Future curriculum/root selection remains separate curriculum work.

## Issue #150 page-local execution

A fresh execution session reads root `README.md` and `AGENTS.md` once before
source mutation. After bootstrap, ordinary leaf execution follows one GitHub
issue page at a time: read only the bookmarked leaf, its live page gate and
amendments, its named direct prerequisites, and its declared files. Do not
hydrate parent issue #150, the full workstack manifest, or all execution
receipts during ordinary leaf execution.

The issue number is the durable bookmark. Git commits and GitHub receipts are
durable execution state; model context is cache. `FACTORY_DEPENDENCY_BLOCKED`
is a staleable observation on an incomplete page: recheck only its named direct
prerequisites, with no same-page amendment required just to reevaluate the
dependency state. Keep a healthy warm model session across cold page boundaries;
do not start a new expensive session solely for isolation. Record the transient
current page in the active handoff or issue checkpoint, never in durable
architecture prose. See [the ticket-navigation record](docs/architecture/11_FACTORY_TICKET_NAVIGATION_20261023.md)
and [the grooming decisions](docs/architecture/12_FACTORY_GROOMING_DECISIONS_20261024.md).

## CONTROLLING USER CORRECTION — 2026-10-23: full U7C Grade B

The active Prometheus curriculum now admits the complete direct-U7C Boolean set:
`B.NOT`, `B.AND`, `B.OR`, `B.XOR`, `B.IMPLIES`, `B.IFF`, plus derived
`B.COMPOSITE` and `B.IDBOOLOPS`. These are direct typed Boolean-AST lessons, not
world-model lessons. Grade B remains nongating developmental debt while Grade C is
the progression frontier. **ADR-094 replaces the old one-B-candidate-per-five cap
with a bounded grade-turn cadence:** after at most four completed non-B training
turns, B receives one contiguous pass over every currently imperfect admitted B
capability, then yields for four more non-B turns before another B pass can occur.
Do not narrow Prometheus back to a historical reduced Boolean profile, and do not
add Boolean mastery as a Grade-C prerequisite.

## CONTROLLING USER CORRECTION — 2026-10-22: foundations before worlds

**2026-10-22 follow-up — progression with Boolean debt:** NOT and AND may be
introduced and revisited, but their mastery must not gate Grade C. C keeps its
designed prerequisites and COUNT → NUMBER → SUCCESSOR → ADD → SUB progression;
it does not gain a B.NOT/B.AND prerequisite. Carry unresolved A/B debt through
the existing explicit debt-admission path and cumulative assessment. Do not wait
for Boolean perfection or label that debt graduation. Current issue numeric scope
starts at 0..3 and remains capped at 4. See ADR-088.

**Teach what a concept is through fundamentals the student already understands.**
The course is **logic and basic cognitive algebra → mathematics → physics**, with
selective New Ithkuil Lexicon Chapters **2, 3 and 6** supplying concepts when their
foundations make them expressible. This is a **narrow staircase built exclusively
upon its foundations**: each step adds one small semantic distinction, explicitly
constructed from earlier understood ingredients. Show that construction in the
actual lessons; a prerequisite label or a correct Python oracle is insufficient.
Start with positive identification; then use context and contrasts where useful.

**We are not building tiny world models at this stage.** Do not substitute event
lookup, before/after-state classification, extra distractors or longer worlds for
concept formation. Occurrence/commencement/termination event prototypes are a
historical detour, not the next curriculum. Preserve their receipts, token meanings,
checkpoints and own AdamW; do not continue those lessons by default. Do not treat
source order, the provisional D–O map, or availability of an easy generator as
pedagogical readiness. Transfer checks should test the taught construction at the
current step, not demand untaught cognitive machinery.

**Current work:** Prometheus now has A, the complete direct-U7C Grade B roster,
and the designed C foundation sequence admitted. Continue COUNT → NUMBER →
SUCCESSOR → ADD → SUB at the current bounded numeric scope. Unresolved A/B skills
remain cumulative debt and teaching targets; Boolean mastery must not gate C access. Teach the actual numeric constituents as each C stage opens.
Physics and further lexical admissions wait for their conceptual ingredients.
Use small lessons, cheap observations and the existing teacher/factory/retention
owners. See ADR-087/088 and HANDOFF.md for exact state and the next action. Canonical
training boundaries and the issue-owned two-run/100-GB exception remain unchanged.

Source-oracled MLX training for a compositional semantic transformer. **This is the one active repository:** `~/Code/bilqis-mlx`. **The repository and its implementation are public.** Repository-owned code, tests, architecture, specifications, evidence, and ordinary handoffs may be published directly; still-protected source authorities such as `IPR-0220` remain protected unless separately released. The human operator owns ordinary and long-running neural training. During trainer repair, the user's standing authorization also permits agents to run short, explicitly finite trainer tests against the current student when needed to reproduce and verify failures. Those bounded repair runs must preserve the student and its own AdamW, may not reset or replace the canonical lineage, and are not authority for unattended or open-ended training.

The former Bilqis implementations are preserved as pinned, read-only source dependencies under `vendor/legacy-v16/`. They are not separate runtime repositories. The native historical bootstrap checkpoint and inherited teacher state live in the ignored `vendor/legacy-v16/runs/`. The current model, its matching AdamW, learning history, champions and soups live under ignored `runs/`. None of those binaries are committed to Git.

## Live training cockpit

![Bilqis live training dashboard showing a two-row run cockpit above candidate evaluation, sentinel and teacher telemetry, system qualification state, and per-capability curriculum mastery.](docs/evidence/diagnostics/images/bilqis-dashboard-prometheus.png)

*A live Bilqis training run in the operator dashboard. The cockpit summarizes runtime and whole-student progress while the panes expose candidate retention, sentinel and teacher evidence, qualification state, and curriculum mastery at a glance.*

## Keep training the existing student

**Operator recovery:** hard stops should identify the failed predicate, state what remains safe, and give a concrete neural-inert next step. See the [`Bilqis Operator Field Manual`](docs/operations/OPERATOR_FIELD_MANUAL.md). Do not hand-edit `state.json` or replace checkpoint/AdamW evidence to bypass a guard.

**Curriculum factory authority:** [`SPEC-0001`](docs/specifications/0001_GENERATIVE_CURRICULUM_FACTORY.md) defines the mandatory end state for semantics-to-grade compilation, release, admission, developmental routine/promotion assessment, repository structure and extension. [`Authority convergence`](docs/architecture/10_CURRICULUM_AUTHORITY_CONVERGENCE_20261019.md) records the current source hierarchy, resolved architecture, known conflicts and migration order. The production rule is **no factory release, no grade**. New grades are declarative factory instances; handwritten grade-specific runtime paths are nonconforming. Generalization and novelty are measured during BAMF-0.2 alpha but do not independently gate graduation or retention. A later fixed held-out/generalization gate requires explicit human admission. Issue #150 decomposes the factory cutover into reusable architecture leaves, not one ticket per future semantic root. The execution packet is [`TASK-0001`](docs/tasks/0001_IMPLEMENT_GENERATIVE_CURRICULUM_FACTORY.md).

**FOUNDATION_EVIDENCE_POLICY_ACTIVE:** Current BAMF foundation work optimizes for acquisition and retention of taught semantics. Teacher-forced gold, exact specimen replay, exact memorization, cache retrieval and memoized procedures are valid current-stage mechanisms. Previously shown examples count toward the current earned-complexity success ratio. Fresh episodes, independent source families and novel compositions are measured as non-authorizing diagnostics that locate the competence breakdown frontier. They are not current acceptance gates. The machine-readable authority is [developmental_evidence_policy.json](docs/specifications/developmental_evidence_policy.json).

**Championship authority:** [Championship lifecycle specification](docs/specifications/0002_CHAMPIONSHIP_LIFECYCLE_V1.md) governs curriculum-boundary resets, capability champions, defended title succession, advisory rights and frozen soup eligibility. Normal examinations establish earned capability roles before graduation, including on fresh runs. Flash continues to defer title qualification.

**Historical research horizon (2026-10-20; sequencing superseded by ADR-087):** The next curriculum-design horizon is a **provisional, revisable Grades D–O map**, beginning with the official New Ithkuil Lexicon **Chapter 1 (Roots Associated with Grammatical Functions)** and **Chapter 2 (Common States and Acts)**. The existing Curriculum Registry / `Grade Tranches` ordering is **not** ordering authority for this work, although its source, semantic and contextual information remains useful evidence. Researchers must build and retain a candidate pool materially larger than the 144 D–O slots, order candidates by prerequisite closure, semantic slope, compositional leverage and downstream unlock value rather than PDF/root order, and keep pedagogical rank/grade metadata outside canonical source CSVs. Source ingestion must preserve stem/Specification distinctions, examples, exclusions, caveats and reproducible provenance. Proposed D–O assignments remain **PROPOSED / NOT ADMITTED** until the normal semantic-authority and factory-release gates admit them. The human-only neural-update boundary is unchanged.


```bash
cd ~/Code/bilqis-mlx
npm run train -- --dry-run --resume --verify-source
npm run train -- --human-run --resume --minutes 90
```

The first command is **read-only** and reports blockers. The second is the ordinary human-operated training path. Under the standing repair authorization above, an agent may use the same `--human-run` gate only for a deliberately small debugging session with an explicit finite `--minutes` and/or `--max-visits` budget, then inspect the committed result before continuing. Both paths use the default `runs/school-mlx-v1` and the internal historical oracle files. No `--legacy-code-root` flag, another checkout or checkpoint clone is needed. The actual progress and optimizer step always come from the latest `runs/school-mlx-v1/state.json`, not from dated documentation.

Optional source-owned lessons can be enabled with `--source-teaching-enrichment` when the admitted factory release declares them. The historical `--boolean-association-bridge` flag remains an alias; each source adapter supplies and independently checks its own supplemental constructions.

**Hard stop or cryptic code?** Start with the [Bilqis Operator Field Manual](docs/operations/OPERATOR_FIELD_MANUAL.md), then query the living catalog directly: `python3 -m bilqis_mlx.cli explain CODE`. The source-derived atlas is available through `python3 -B scripts/operations/operator_contract_audit.py --lookup CODE`. New operator-visible failures must use the typed error control plane in [`SPEC-0004`](docs/specifications/0004_TYPED_ERROR_CONTROL_PLANE.md); raw exception strings and opaque numeric guards are migration debt and may not grow.

**Current reduced-B implementation is compatibility state, not the target factory abstraction.** Existing human-run history still contains reduced/minimal B release identities and resume behavior. Preserve those receipts and compatibility paths. New factory work must represent the AND/IFF experiment as a declarative execution profile over canonical B, using the same Boolean source providers with narrowed operator and answer domains. Do not extend the minimal-B release/provider lineage as new architecture. The target is described in the authority-convergence record and `docs/architecture/09_EXECUTABLE_CURRICULUM_CLOSURE.md`.

## Resume the isolated issue #340 experiment

The issue #340 trial is isolated under `~/Code/bilqis-mlx-retention-lab`. Its protected historical recovery baseline remains `bundles/best-8355-a03fa6317bd4` (SHA `cda606f9...`, native AdamW step 230184, old cohort evidence 287/291), but the **current continuing causal student is now step 230200**, SHA `c714ef49...`, after one retained C.DIV update. The canonical `~/Code/bilqis-mlx/runs/school-mlx-v1/` bundle remains read-only evidence and is never used as the live pointer. The current scheduler is ordered Grade-C prefix revalidation at **Grade A RECOVERY_1**. The evolved experimental teacher and matching native AdamW are retained.

The championship epoch began empty at the explicit baseline rebase, but it is no longer empty: later intact source-scored evidence has earned 19 active capability-best roles and frozen A/B/C soup votes. The rebased baseline itself still has zero automatic teaching votes. Commit `a041b01` restores fresh source-oracled routine examinations at every MAIN/RECOVERY boundary while keeping promotion/graduation attempts separate, repairs S3 across explicit rebase lineages and fresh paired cohorts, and activates per-human-command stagnation containment without waiving graduation debt. Historical cohorts, champions, soups and checkpoint receipts remain immutable evidence; old fixed-cohort scores must not be treated as directly comparable to newly drawn routine cohorts.

When that containment exhausts all healthy work and every remaining quarantined mastery debt belongs to one grade, the trainer enters an explicit sole-grade rehabilitation pass instead of stopping only to repeat the same recovery pattern on the next command. It re-admits only the recorded debt capabilities; no debt is passed, forgiven or assigned a synthetic score, and fixed-frontier preservation remains in force. Exams sampled while debt was withheld remain partial evidence for championship authority even if rehabilitation begins after scoring. Mixed-grade deferred debt still stops for review under the existing behavior.

For the current issue #340 B recovery, repeated stagnation containment is itself obstructing rehabilitation after the long misinformed-teacher period. The next **human-owned** resume may therefore activate a persisted B-only grace window for 100,000 retained optimizer steps. During that window the system still detects and records stagnation, but does not quarantine B; all retention/preservation and mastery rules remain active, and other grades keep normal containment. The first command that creates the lease uses `--stagnation-grace-grade B --stagnation-grace-steps 100000`; later resumes inherit the recorded absolute deadline and must not reset it merely by omitting or repeating the options.

```bash
cd ~/Code/bilqis-mlx-retention-lab
npm run train -- --dry-run --resume --verify-source --run-dir ./runs/issue-340-mentor-epoch-trial
npm run train -- --human-run --resume --minutes 15 --run-dir ./runs/issue-340-mentor-epoch-trial
```

The baseline rebase is already complete and receipted; do **not** rerun it before the next trial. The human alone starts the **last** command after the dry-run reports no blockers. As of 2026-10-18 04:30 EDT, the exact dry-run above reports `blockers: []` and performs no neural updates. The next trial tests fresh-cycle learning, paired S3 retention evidence, subperfect championship guidance, and automatic temporary containment of repeatedly failed recovery capabilities while preserving the exact student+own-AdamW lineage. Preserve both original and experimental runs.

**Retention is the default for every training launch and resume.** The former `--experimental-retention` opt-in is no longer needed (older commands remain accepted for compatibility). Existing protected student/AdamW lineages keep their recorded policy and cannot be resumed without retention. To deliberately run the older, unprotected teaching path for an **independent** experiment, supply `--no-retention` with a distinct explicit `--run-dir`; this cannot turn off protection for `runs/school-mlx-v1/`. An opt-out is never inferred from an omitted flag. Retention rejects locally non-improving candidates and preserves matching AdamW; whole-student regressions can still occur.

```bash
npm run status
npm run dashboard
npm run diagnostics -- --run-dir ./runs/school-mlx-v1
```

**Candidate retention net-grade correction (ADR-054):** A target gain never justifies a larger within-grade loss. Every admitted capability in that grade is checked on a complete equal-size fresh paired panel, which must improve strictly in aggregate. When the current grade has a saved matching whole-grade exam cohort, its fixed score must not regress either. For example, B.XOR +1 versus B.IFF -1 and B.IMPLIES -1 is a rejection, not a retained improvement. See docs/specifications/0003_CANDIDATE_RETENTION_GRADE_NET_V1.md. No previous student optimizer steps are rolled back by this prospective rule.

**Staged scoring refinement (ADR-055/057):** Check the candidate's target first and reject immediately if it makes no gain. Fill only still-missing fresh capabilities in its lesson grade next. Before a complete fixed school frontier exists, keep the original stricter positive-grade/protected-item guards. Once a complete fixed frontier exists, late-stage retention becomes aggregate: the fresh lesson grade, fixed lesson grade, active school grade and whole-school fixed total may tie but must not regress; individual rows/capabilities may trade errors. The saved frontier must belong to the exact current retained parent SHA and native AdamW step; stale-parent frontier evidence fails closed. Protected and OR/XOR item regressions remain diagnostics rather than late-stage vetoes. Champion scoring is separate and unchanged.

The source-backed Grade C staircase teaches established counting, number, successor, addition and subtraction operations on gradually expanded domains before introducing multiplication and division. New semantics enter an append-only native registry. The vocabulary size is graph-bound, not permanently 222 tokens. A/B retention is assessed on the same whole student; individual best champions and frozen grade soups remain distinct from live student promotion. **Automatic stability promotion (ADR-084/093, corrected by ADR-103 and the 2026-10-26 replay decision)** uses deliberate hysteresis rather than a hair-trigger 90% loop: a fresh introduced-grade mean must reach at least 92% to start a promotion sweep, and the running stitched sweep may fluctuate down to 87% before aborting. A failed sweep is bound to the exact student checkpoint plus introduced semantic scope, so a new cohort cannot re-arm the same unchanged student; a retained student change or scope expansion may. The scheduler freezes the threshold-crossing score vector and makes one canonical pass over the introduced semantic set. After each semantic visit, only that semantic's fresh authoritative score replaces its prior sweep score before the grade mean is recomputed. Unswept semantics retain their most recent sweep scores. A successful sweep opens exactly one next semantic stage or grade while carrying every imperfect semantic as mastery debt. This progression does not mint a champion or substitute for 100% clean graduation.

**Factory 349 replay decision (2026-10-26):** the post-#324 successor Factory deliberately carries forward the bounded Teacher vNext canary, calibrated 2/4/8/16 multi-fidelity shadow ladder with the step-8 stopping horizon, same-student/scope promotion-attempt latch, and 92/87 promotion hysteresis from `349-bouta-tree-fitty`. These were operator-proven control-loop improvements, not abandoned experiments. Port them through current Factory/#333 owners rather than restoring obsolete duplicate proposal/outcome authorities. The frozen #324 v3 executable and manifest remain immutable controls and do not absorb these changes retroactively.

**Capability championships:** Titles are capability-local, grade-isolated and defended, not historical high-water trophies. After a title field is cleared, an empty capability slot stays vacant until one same-grade checkpoint reaches at least 66% on that capability (8/12 on the current exams); its first defense battery is exactly the questions it got right on that threshold-crossing exam. A later contender that improves the current same-grade comparison or reaches the capability ceiling earns one lifetime title fight against that incumbent checkpoint for that capability; both checkpoints infer again, and cached model answers never decide the belt. The same checkpoint pair never rematches for that capability. A successful takeover may trigger one non-recursive same-grade sweep for sibling title fights. Quarantine of another capability does not suppress a complete source-valid title challenge. Title ownership and title challenges never cross grades. Teaching advice is a separate contract. See [`SPEC-0002`](docs/specifications/0002_CHAMPIONSHIP_LIFECYCLE_V1.md).

**Champion and soup teaching scope:** Each active maxed capability role contributes one direct source-gold-gated advisory vote to lessons in any admitted grade; a shared checkpoint may be inferred once but still contributes one vote per qualifying role. Non-max roles contribute no direct role votes. Frozen grade soups are a separate aggregate adviser, using full base votes in their own grade and the existing diluted foreign-grade voice. All such authority is valid only inside one unchanged holistic school identity. A change to the admitted course/question inventory, semantic graph, model parameter-shape geometry or executable factory release archives and clears **all** active champions and soups before further advice or title defense; the causal student+own AdamW and immutable historical receipts remain intact.

**Three-lane source preparation (ADR-063):** Protected human training now defaults to two spawned host-side source-preparation workers plus the one sovereign MLX/student/AdamW lane. The workers may generate deterministic future lesson material but never receive model parameters, optimizer state, writable run state or championship authority; all neural inference/training, retention, teacher credit, scheduling, exams and persistence remain serialized on the main lane. Use `--source-prefetch-workers 0` for the exact serial control path. The starter release intentionally caps this option at two workers; it is not parallel MLX training.

**Fresh ternary fallback (ADR-064):** If the human judges the current FP32 recovery to have failed to produce meaningful growth, the next major experiment is a new ternary model trained from scratch, not another checkpoint rescue or post-training conversion. The first comparison keeps the current six-layer, width-384 topology and source/curriculum/evaluation contract fixed while changing the neural weight representation. The FP32 lineage remains immutable evidence; ternary gets its own run, optimizer, initialization, quantizer/export receipts and exact hashable ternary codes.

**Binary lesson structural coverage (ADR-065):** Grade-B optimizer batches now keep every source-valid operand truth pattern for the active connective represented before old-grade rehearsal can consume the remaining lesson capacity. The compositional A/C bridge also targets the connective currently being taught, including unary NOT, instead of spending adjunct examples on unrelated B operators. This changes lesson construction only; gold, exams, scheduler, retention and student/AdamW custody are unchanged.

The retention-aware teacher tests parent-versus-challenger changes and preserves recoverable best whole-student checkpoints with **their own AdamW**. **Only a strictly positive, source-oracled gain in the targeted capability can promote a candidate.** Rejected attempts still teach both the contextual teacher **and the inherited strategy-selection bandit**, using the measured causal rejection penalty rather than incorrectly reporting zero reward to the bandit. Rejection does not change the student or AdamW; recorded instructional accuracy and historical teacher rewards retain their original meanings. Graduated grades may incur a small amount of measured fixed-cohort debt while another grade learns. Debt is accumulated from each mature grade's net fixed-cohort loss and paid down by later net gains, rather than attaching durable debt to individual rows or capabilities whose cohorts change over time. At two debt answers the scheduler prioritizes one complete same-grade repair pass, including earned champions and soups, then yields to other eligible work for the remainder of that school sweep; at four, further mature-grade loss is blocked while holding or paying down existing debt remains admissible. Historical high-water checkpoints never replace the current retained parent as the candidate baseline. The active probe has a bounded size informed by that skill's current exam count, while cross-grade protection probes stay small. This provisional gate is neither perfect retention nor a graduation shortcut. Temporary forgetting remains possible, but it now has an explicit repair budget instead of an unlimited tab.

When a comparable full-school examination includes B.OR and B.XOR, candidate screening also replays their 24 source-oracled, truth-balanced fixed-cohort questions. Any newly wrong answer on these already-correct compositions rejects the trial, without evaluating all school capabilities. Teacher feedback still records the rejection. The dashboard's **LESSON%** column measures fresh instructional examples; cumulative qualification is reported separately under **GRADES & MASTERY**.

**Post-stall preservation and exam reuse (ADR-056/057):** The zero-retention run showed concentrated OR/XOR interference, so protected lessons rehearse fresh source-oracled structural siblings while excluding fixed exam identities. Exact structural matches are preferred, with graceful fallbacks rather than blocking training. The later human run proved that per-item monotonicity is also wrong for mature learning: individual mistakes may move as long as the late-stage lesson grade, active school grade and whole school do not regress. Scheduled whole-school exams on an unchanged retained checkpoint can still reuse a fully verified prior score/miss result.

Longitudinal learning diagnostics must examine **distinct student checkpoints**, not count re-examinations of the same unchanged checkpoint as new learning. Repeated exams remain individually source-verified and present in the audit; genuinely changed or backward checkpoint identities still fail closed. The School50 diagnostic display must expose a history-validation failure instead of silently presenting an unavailable durability signal as “no active warnings.”

Recovery ranks the complete cumulative pool of introduced and graduated capabilities. Perfect capabilities must not pad a weakest-three recovery round. The normal teaching pass should avoid an unnecessary optimizer trial when the current student is already perfect on a fresh source-oracled target probe; whole-student examinations still recheck every admitted capability. The experimental matrix-strain signal compares parent-to-candidate weight movement against an immutable curriculum-epoch starting checkpoint and the best **comparable whole-student** high-water checkpoint. That high reference advances only on a strictly higher cumulative score recorded by the whole-student peak authority, never on ties or grade-soup refreshes. Matrix-strain diagnostics are advisory, not an automatic retention veto or replacement for examinations.

## Repository layout

| Path | Ownership |
| --- | --- |
| `bilqis_mlx/` | Active semantic engine, MLX teacher/student, training, runtime, checks and School50 telemetry |
| `vendor/legacy-v16/` | Frozen historical source oracles and teacher implementation; no new feature development |
| `vendor/legacy-v16/runs/` | Ignored original historical bootstrap checkpoint and teacher-state provenance |
| `runs/school-mlx-v1/` | Ignored active human student and its saved optimizer, source/oracle receipts and teacher history |
| `runs/archive/` | Ignored historical local safety copies pending independent external backup |
| `docs/` | Current operator contracts and historical/research records |
| `tests/` | Disposable, source-verified fixtures; no actual-student optimizer writes |
| `.github/workflows/` | Portable integrity checks and private release automation |

`BILQIS_STORAGE_ROOT` configures the default local run home. The retention trainer requires that home to remain inside this repository's `runs/` tree; its current fully tested default is `runs/school-mlx-v1/`. Store backups on a distinct, explicitly selected volume and verify them before deleting any original checkpoint; moving files between folders on the same volume does not free space.

## Checkpoint and disk maintenance

Full student and matching optimizer checkpoints are kept together. A saved state is immutable, and source-cohort graduation tests never combine best scores from different students. Routine checkpoint retirement only removes genuinely unreferenced bundle directories after commit. Unexpected files and symlinks fail closed; harmless macOS Finder metadata no longer blocks resume. Protected champions, live state, accepted whole-student peaks, frozen soup recipes and qualified sources retain explicit identity.

```bash
npm run storage:plan
# Optional, when training is inactive: losslessly compress older immutable JSON states
npm run storage:compact -- --max-files 0
```

The normal human-run stop path also performs bounded lossless compression of old state JSON. It does not delete neural weights, AdamW, original authority records or checkpoints held by a live role. See [checkpoint and release migration](docs/operations/CANONICAL_REPOSITORY_AND_RELEASE_20261017.md) for custody details. No backup script runs automatically against arbitrary external drives.

## Development and release

```bash
python3 -B -m unittest discover -s tests -q     # Apple Silicon/MLX integration suite
npm run quality:check
npm run release:check
python3 -B scripts/check_historical_abi.py
python3 -B scripts/check_semantic_boundaries.py
```

The portable Linux GitHub Actions jobs verify source, semantic ABI, release manifests, selected neural-inert tests and regression-aware code hygiene. Full neural testing is Apple Silicon only. Conventional Commits, Semantic Versioning and a dated `CHANGELOG.md` govern private releases. Tag an immutable annotated `vMAJOR.MINOR.PATCH` on a verified clean `main`; the tag workflow validates and publishes private release notes. See [contribution and release rules](CONTRIBUTING.md).

For detailed historical decision-making and source provenance, read [ADR.md](ADR.md), [AGENTS.md](AGENTS.md) and the [archived pre-consolidation README](docs/history/README_PRE_CANONICAL_20261017.md). Historical example paths in old research papers are **provenance**, not current operator commands. Protected research contracts must not be copied into public repositories.
