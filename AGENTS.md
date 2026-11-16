# Bilqis MLX | Agent operating rules

## BAMF-0.2 unified-base contract — 2026-10-28

The BAMF workstreams use this branch as their common base. Its executable authority
is the current Factory branch `codex/337-replay-349-20261026`. Preserve that runtime,
trainer, scheduler, teacher, retention, admission, and controller logic unless the
active BAMF issue explicitly owns a change to it. Do not merge or copy newer `main`
controller code into this branch simply to catch up with `main`.

<!-- BAMF02:LEGACY-TRAINER-AUTHORITY:20261107 -->
### Legacy trainer adaptation authority — 2026-11-07

When any issue, remediation, EGM review, compatibility task, or worklog needs to
inspect or adapt behavior from the **latest legacy trainer**, the sole current
adaptation oracle is the preserved Factory replay worktree and run below:

- worktree: `/Users/emilie/Code/.worktrees/bilqis-mlx/337-replay-349-20261026`
- branch: `codex/337-replay-349-20261026`
- run: `/Users/emilie/Code/.worktrees/bilqis-mlx/337-replay-349-20261026/runs/microspenics-349-replay`

Run `python3 -B scripts/check_legacy_trainer_authority.py --live` before using
legacy behavior as an implementation or review premise. Record that receipt in the
issue/PR worklog when the legacy trainer materially informs the change.

Prometheus remains valid **historical evidence about the Prometheus lineage only**.
`runs/codex-0001-prometheus`, the root `npm start`/`verify` convenience commands,
and Prometheus-specific ADR observations are not the latest legacy-trainer
adaptation source. Do not infer current legacy trainer policy, resume shape,
teacher behavior, scheduler behavior, or compatibility expectations from
Prometheus when implementing BAMF or another successor. Historical Prometheus
mentions must be labeled as historical/non-authoritative for adaptation rather
than presented as the current legacy baseline.

The BAMF architecture, including `ADR-BAMF02-004`, and issue hierarchy live in
`docs/architecture/BAMF_0_2.md` and `docs/tasks/bamf-0.2/`. The imported New Ithkuil/SKOS source lives under
`lib/ithkuil/` with its ingestion Skill and fingerprinted test policy. Treat those
assets as source/planning inputs until a BAMF implementation issue wires them into
the executable Factory. Current Prometheus-specific operating rules below remain
binding for the existing student; BAMF successor work must express new behavior in
grade-neutral Factory terms rather than hard-code a future grade letter. The
historical Grade-B cadence below applies to the existing Prometheus lineage, not
the BAMF successor. BAMF work follows `ADR-BAMF02-004`: a functional recursive
Factory with source-qualified typed rules and grade-neutral admission and teaching.
These are implementation requirements, not proof that the new runtime exists.

The unified branch is the reviewed integration trunk and remains live throughout
BAMF execution. Lane A's historical integration branch is
`codex/bamf02-a-semantics`, Lane B's is `codex/bamf02-b-neural`, and Lane C's is
`codex/bamf02-c-runtime`. Independent issue-scoped branches/worktrees may coexist
within each lane. **One writer means one independently mutating writer per branch
and shared file at a time, not one agent per lane or one agent for the lifetime
of an issue.** Coordinate shared integration changes through the relevant owner.
Before a feature's integration turn-in, consume the current
`origin/codex/bamf-unified-base-20261028`, record the unified SHA consumed,
resolve conflicts, and run the smallest affected verification. Do not merge
`main` or a sibling lane directly. Keep implementation and review state on the
owning issue and branch until
the work is truly ready to merge. Do not use a draft pull request as a queue marker
or review-state surrogate.

EGM labels describe **design/specification review state only**. Add `EGM-Pending`
when a fresh design review is pending, replace it with `EGM-Passed` after a complete
design PASS, or with `EGM-Failed` while a material design finding remains unresolved.
Use `EGM-Mitigation` only for bounded work created specifically to resolve a design
review finding before implementation. Ordinary implementation commits do not
invalidate `EGM-Passed`; a semantic design amendment invalidates only the affected
review scope unless it changes the architecture.

### Differential verification and expensive-test reuse — 2026-11-04

Use two verification tiers. During ordinary leaf development, run
`npm run verify:leaf`. Its test selector uses `BILQIS_TEST_BASE_REF`, the last local
passing leaf receipt, or `HEAD^1` in that order; it never uses
`BILQIS_QUALITY_BASE_REF` as a test-impact boundary. The quality base may remain
distant when structural governance needs historical debt/regression comparison.

`npm run test:changed` first bounds work to direct owner tests from the near-head
diff. Pytest-testmon may refine that bounded set when its dependency database is
warm. Pytest-xdist may parallelize only work that is known to be neural-inert and
non-MLX; MLX-capable verification is governed by the resource-containment rules
below. On a cold database the same bounded tests seed testmon data for later edits. Testmon never
turns a partial cache into permission to collect the whole repository. Passing leaf
and pre-merge gates write ignored receipts under
`.local/test-gate/`. If the exact HEAD plus working-tree fingerprint has already
passed the same gate, do not rerun it merely because an agent resumed, compacted,
changed issue pages, or reached another checkpoint. The gate reports the prior pass
as reused. Set `BILQIS_TEST_FORCE=1` only when there is a concrete reason to discard
that proof.


### Verification wall-clock ceiling — 2026-11-12

No agent-launched test suite, verification command, hosted workflow, witness, or
composed verification run may have a planned or expected wall-clock duration above
**2 hours**. The two-hour value is an absolute ceiling, not a target. Ordinary leaf
development and turn-in should use checks that finish in seconds to minutes whenever
the claim permits it.

Before launch, bound the expected duration from prior receipts, selected tests, or
staged estimates. If the bound is unknown or can exceed two hours, do not launch the
run. Split it into claim-specific stages that each remain within the ceiling and
produce durable receipts. Do not evade the rule with arbitrary time slicing: each
stage must have an independently meaningful claim, explicit inputs, and a resumable
or terminal result. Detached execution, snapshot isolation, or operator observation
does not waive the ceiling for a test.

If an agent-launched test reaches two hours without completing, stop or contain the
owned process at the next safe boundary, preserve the partial log/receipt, and
classify the run as incomplete or over-budget rather than PASS. Turn the discovered
seam into a cheaper deterministic regression before another attempt. Reuse
still-valid passing evidence under the rules above instead of repaying an expensive
proof.

Whole-system qualification that cannot be made meaningful inside this ceiling is
not an ordinary test gate. Redesign it as bounded staged qualification, or hand it to
the human operator as a separately authorized non-test run. Historical test evidence
from runs longer than two hours remains provenance and is not invalidated. Only a
new owner-ratified ADR amendment may change this ceiling.

### MLX verification resource containment — 2026-11-11

Treat any process as **MLX-capable** when it imports `mlx`, constructs or evaluates
MLX arrays, loads a BAMF parameter/optimizer tree, executes a neural forward/backward
path, serializes full MLX state, or runs a full-model/custody witness that can reach
those owners transitively. Within one test runner, MLX-capable verification is
**single-worker by default**. Set `BILQIS_TEST_WORKERS=1`. Do not invoke pytest with
`-n > 1` unless that runner enforces an explicit aggregate memory budget. This is not
a host-wide serialization rule. Independent bounded MLX jobs on the M3 Ultra may
overlap when each job applies a memory/cache policy. Their configured aggregate
limits must leave host headroom. Another bounded MLX job is not a reason to wait.

The reason is measured, not hypothetical. On the 96 GiB M3 Ultra with MLX 0.31.1,
a fresh process reported both the default MLX memory limit and free-buffer cache
limit as `97,925,254,348` bytes, about **91.2 GiB per process**. Four unconstrained
xdist workers therefore admit about **364.8 GiB** of aggregate MLX-managed demand
before Python, the OS, other applications, or other test sessions are counted. On
2026-11-11 an `-n 4` BAMF verification run drove macOS into repeated
out-of-memory warnings and approximately **65.2 GiB of swap usage**. Detaching a
command protects the agent socket; it does not make that command resource-safe.

Long-lived MLX test processes must disable the free-buffer cache with
`mx.set_cache_limit(0)` / `mx.clear_cache()`, or enter the repository's
`training_memory_policy(mx)` when that policy is semantically appropriate. If the
selected test runner cannot guarantee that policy in every MLX-capable worker, run
the relevant tests serially and narrowly rather than launching an unbounded broad
parallel suite. Independent processes may overlap when every process has an applied
memory limit/cache policy and their configured aggregate upper bound fits the host
with headroom.

Before any expensive MLX launch, inspect current memory pressure and the bounds on
active MLX-heavy processes. Do not serialize because another bounded witness is
active. High swap occupancy is also not a veto while physical-memory headroom remains
healthy. Refuse a new launch if a participating job lacks an applied bound. Also
refuse when configured aggregate ceilings exceed safe host capacity or the OS reports
actual memory-pressure/OOM symptoms. A memory-pressure dialog, swap-exhaustion event,
OOM, or worker death under memory pressure is a **failed verification run**. Preserve
its evidence, contain the owned process group, diagnose the allocation mechanism,
and do not rerun the same workload unchanged.

The production BAMF trainer remains one sovereign MLX writer. Its current
`training_memory_policy` disables MLX's free-buffer cache, which prevents this
specific multi-process cache explosion. The C08 **48 GiB** value is nevertheless a
planning envelope, not a proven hard allocator ceiling: do not describe the trainer
as capped at 48 GiB unless runtime allocator limits, live MLX telemetry, and the
production OOM restore/retry path are wired and verified on the actual execution
path. Never use a test-harness memory accident as evidence that production training
is safe, and never use the analytical planner alone as proof of measured peak RAM.

Run `npm run verify:premerge` only at an actual integration/turn-in boundary or when
a change can invalidate broad prior evidence. That gate executes the repository's
existing aggregate runner. A new source/configuration change,
failed test, changed dependency/toolchain, or altered test policy can invalidate the
prior broad receipt; prose-only progress and unchanged code cannot. Install the
optional accelerator dependencies with `python3 -m pip install -e '.[test]'`.

Open the lane-to-unified PR only after the candidate is otherwise ready to merge:
the design review is complete, required differential evidence is green or validly
reused, required detached witnesses are reconciled, design-to-code drift is
reconciled, and every applicable pre-PR gate is green or validly reused. Open it ready
for human review, not as a draft work queue. PR-hosted checks are the final integration
gate. A hosted repair invalidates only evidence whose assumptions changed; if the
repair changes approved design semantics, return only that affected design scope to
EGM. Existing historical/draft PRs remain provenance and need not be closed or
recreated solely to adopt this policy. No issue authorizes self-merge.
After accepted work lands on unified, the next issue in every lane repeats the
sync-in step so reviewed cross-lane interfaces arrive early.

## BAMF-0.2 flow control and parked-PR discipline — 2026-11-02

BAMF execution distinguishes **implementation WIP** from review, dependency and
authority inventory. The normal ceiling is **six `ACTIVE` implementation leaves per
lane** (owner-directed concurrency expansion, 2026-11-04). `READY`, `WAITING`,
`BLOCKED` and `TURNED_IN` do not count as active WIP. Parallelism is welcomed
when independent branch/worktree writers have disjoint ownership; integration
and shared-file mutation still follow verified single-writer coordination.

**Compaction and resumed-agent ownership (2026-11-04):** A conversation or
worker context compaction is **not** a competing writer, a new issue claimant,
or a lease-loss event. An `ACTIVE` ledger item, prior agent name, checkpoint
comment, historical worktree, or in-flight issue assignment is not a live lock.
Resume on the exact preserved issue/branch/worktree after inspecting `git status`,
current branch HEAD, remote ref, relevant checkpoint/handoff and actual competing
process/writer evidence. An unchanged remote ref plus the same preserved
worktree/continuation is positive continuity evidence. Do **not** refuse to
continue merely because the earlier context or another agent identifier appears
as the recorded owner. Do **not** start another agent or fresh issue branch solely
because the context compacted. If a different live writer truly owns the same
mutable branch/path, coordinate or isolate work; do not overwrite its edits.
When ownership is genuinely ambiguous, name the concrete conflicting live
writer/ref or uncommitted collision rather than asserting a phantom lock.

**Required handoff payload:** Before a planned compaction or agent transfer,
run `python3 -B scripts/bamf/writer_handoff.py emit --issue <ISSUE> --epoch
<STABLE-EPOCH> --worktree <WORKTREE>` and carry the **complete JSON output** in
the compacted handoff, including issue, epoch, exact worktree, branch, local HEAD,
upstream and remote HEAD, and worktree-dirty fingerprint. Save that JSON as a
local file for `python3 -B scripts/bamf/writer_handoff.py verify --payload
<HANDOFF-JSON-FILE> --worktree <WORKTREE>` when resuming. A
`CONTINUATION_MATCH` proves the preserved Git snapshot still matches and permits
resuming **without inventing a new issue claim**. The verifier reads the real
upstream ref and fingerprints modified/untracked files. On mismatch, inspect
the changed facts and reconcile, not automatically refuse the issue. Network
failure is `UNVERIFIED`, not evidence of a competing agent. The JSON is a
continuity receipt, **not a distributed lock**: it cannot prove that another
process will not begin writing later. Maintain actual per-branch/shared-path
coordination during ongoing edits.

**Passing-test evidence reuse (2026-11-04):** Do **not** rerun a passing test
suite merely because a new agent resumed, a PR was opened/updated, a branch was
rebased onto an equivalent reviewed head, or time passed. A passing run remains
valid until a later change can plausibly invalidate what it proved. Determine
invalidation from the diff since the exact tested head and the suite's dependency
surface: production code, fixtures/goldens, tests themselves, generators, runtime
dependencies, build/test harnesses, or environment/configuration consumed by that
suite. Documentation, governance prose, issue/PR bookkeeping, flow-control limits,
handoff metadata, and unrelated workflow orchestration do **not** invalidate
semantic/neural/custody suites by themselves. If no invalidating change exists,
reuse the prior exact-head passing receipt and record `TEST_EVIDENCE_REUSED` with
the tested head and comparison range instead of spending 10-15+ minutes rerunning
it. Run the **smallest newly affected check only** when a change has a narrow
surface. Escalate to a broad/expensive suite only when its dependency closure was
actually touched, the prior run was incomplete/failed/untrustworthy, or a human
explicitly requests fresh verification. A merge commit is not automatic
invalidation; inspect what it introduced.

**Scope-expansion gate, not a decomposition gate (2026-11-05):** New issues,
branches/worktrees, and PRs are intentionally cheap coordination primitives when
they partition **already-authorized required scope**. Do not force independently
deliverable work back into a large parent merely because the parent could absorb
it. Prefer decomposition when it improves parallelism, turn-in latency, failure
locality, review isolation, or early information.

Classify proposed work before implementation:

- `DECOMPOSE`: a strict subset of an existing issue/spec's required acceptance,
  adding no new obligation. Record the parent plus exact inherited clause(s) and
  `new_acceptance=false`. This may create its own issue, branch/worktree, and PR
  without proving that decomposition itself is a new blocker.
- `EXPAND`: any obligation, correctness criterion, cleanup, architecture change,
  or review demand that cannot be traced to existing required acceptance. Before
  spending on that delta, write at most **120 words** naming `delivery`,
  `required_by`, `defer_failure`, and `cheapest_next`, then choose
  `PROCEED | PARK | DROP`.
  - `PROCEED`: the expansion is required for current delivery/correctness/safety.
  - `PARK`: useful, but current delivery does not require it; preserve only a tiny
    note/backlog pointer until explicitly selected.
  - `DROP`: duplicate, speculative, cosmetic, or peripheral; spend nothing.

For new remediation issues, keep the GitHub body **under about 250 words by
default** and point to inherited/versioned authority under ADR-118. If a bounded
child/helper grows past **3 commits, 3 touched files, or 250 net changed lines**, or
reveals a second independent problem, perform a **scope-drift audit** before more
work. If every obligation still maps to inherited required clauses, keep going and
split again when useful; do not collapse it back into the parent. Only the
untraceable delta is `EXPAND` and must pass the expansion gate. Never run EGM to
create scope for an expansion that current delivery does not require.

**Diagnostic-loop budget (2026-11-05):** Differential test selection does not
authorize unbounded bespoke probes. Treat any live Factory/MLX/full-model witness,
large inline Python diagnostic, or end-to-end acceptance reconstruction as
**expensive execution**. Do not rerun the same probe against unchanged relevant
code/inputs; reuse its result. After one exploratory inline probe, move repeated
diagnosis into a named focused test/helper or parameterized diagnostic so setup and
results are reproducible. If varying seeds/hyperparameters/cases, sweep them in one
process and hoist invariant Factory/model/bundle setup rather than cold-starting the
whole stack once per variant. After **two unsuccessful full-cost witness attempts**
for the same hypothesis, stop the end-to-end loop and isolate/profile the failing
stage before another full witness. A compaction handoff must state whether an
expensive probe is still running so the successor does not launch a duplicate.
Acceptance-scale witnesses belong at a stable boundary after cheaper evidence has
changed; they are not the ordinary inner debugging loop.

**Staged fail-fast verification for expensive tests (ADR-139):** Treat every
expensive test or witness as an ordered pipeline. Do not make a multi-minute MLX,
Factory, full-model, or end-to-end run the first place that fixture, import,
precondition, or assertion-contract errors can surface.

1. At an integration/turn-in boundary, run every applicable neural-inert repository
   quality/static gate **before** mounted real-fixture or full-model execution. This
   includes governance, docs, source/authority scanners, changed-file quality, and
   other deterministic checks that do not depend on expensive model output. A late
   static failure is a pipeline-order defect; repair the early gate before another
   expensive rerun.
2. Run cheap contract checks next. Cover imports, fixture shape, deterministic
   invariants, assertion semantics, and other neural-inert behavior with focused
   tests that complete quickly.
3. Run a real-fixture preflight next when the final witness depends on external
   artifacts, accepted custody, source state, runtime configuration, or other
   production inputs. Use the same source paths and shared setup helpers as the
   full witness. Execute every cheap production step through the immediate boundary
   before the expensive call, then stop before the expensive computation begins.
4. Treat an unexpected skip as preflight failure. A required real-fixture preflight
   must verify that its artifact, runtime, and custody inputs exist and are usable;
   pytest exit code zero is insufficient when the required case was skipped.
5. Chain the stages in one runner or command so failure stops the pipeline. The
   expensive phase may start only after every required preflight stage succeeds.
   Do not rely on an agent remembering that a separate preflight was supposed to
   run first.
6. Share setup and assertion helpers between the preflight and full witness. Do not
   maintain a simplified imitation that can drift away from the production path.
7. Keep expensive-output assertions in the final witness, but give every invariant
   that can be proved without the expensive output a cheap contract test first.
   If a long run discovers a banal fixture, import, precondition, or assertion
   defect, add or strengthen the earlier stage before rerunning the expensive test.

Aggregate repository discovery must not silently schedule a witness that declares
`BILQIS_LEAF_GATE_POLICY = "DETACHED_ONLY"`. Those files are excluded from the
default aggregate runner and remain runnable only by an explicit targeted command or
their dedicated detached witness harness. This keeps broad premerge verification
from repaying separately accepted expensive evidence or bypassing witness-specific
resource/receipt controls.

The staged path is diagnostic and non-authorizing. Only the complete production
witness can satisfy acceptance that actually depends on the expensive computation.
If the full command can plausibly exceed five minutes, the complete staged pipeline
still follows the detached-run rules below, including snapshot isolation, durable
receipts, desktop notification, and no chat polling. Stage logs must identify which
stage failed so the next run does not repeat already-settled expensive work.

**Precedence-ordered diagnosis for expensive qualification gates (ADR-131):** When
an acceptance or retention decision has ordered rejection predicates, diagnosis
must evaluate the cheapest decisive predicate first and stop as soon as that result
already determines rejection. Do not eagerly run later cohorts, whole-school
screens, or other lower-priority gates merely to rediscover a decision that an
earlier predicate has already fixed. Keep this diagnostic path **non-authorizing**:
it may reuse the exact production source rows, candidate, solver semantics and
policy inputs, but it must not mint the production acceptance/retention authority.
Only the full production owner may do that at the final acceptance boundary.

Hoist and reuse invariant source compilation, Factory/model construction, bundle
loading, custody validation and other setup within one diagnostic process whenever
the tested semantics allow it. Before launching a multi-minute witness, account for
its case count, repeated compilation/setup passes and parent/candidate solve count;
if those costs can be separated without weakening the invariant, separate them.
Any expensive rejection path must expose the exact rejection reason plus useful
stage timing/score evidence. A multi-minute witness that reports only `accepted =
false` is insufficient diagnostic observability and must be repaired before the
same execution family is repeated. The final authoritative witness still runs in
full once a cheaper diagnostic has demonstrated a relevant repair and the candidate
is otherwise stable.

**Five-minute socket ceiling for chunky local work (ADR-132):** If a local command
could plausibly run longer than five minutes, do not keep an interactive agent/tool
socket open waiting for it. Launch it with
`python3 -B scripts/bamf/detached_long_run.py launch ... -- <command>` so the child
continues in its own session, writes a combined log plus machine-readable completion
receipt, and sends a macOS desktop notification with sound when it exits. Before
detaching, the launcher must copy a digest-verified source snapshot of the current
worktree and run the worker plus all relative-path subprocesses from that snapshot.
Concurrent edits to the original worktree must therefore be invisible to the run.
The receipt records source/snapshot digests, and any mutation of the snapshot by the
detached command itself fails the run. Do not replace this isolation with a convention
that agents merely promise not to edit shared files. A detached run launched under the
older v1 runner cannot be retrofitted safely while it is executing; keep its imported
source surface frozen until it exits. The
controlling agent may remain connected only long enough to verify that the detached
worker launched and its PID/receipt paths exist. It must then yield the turn, report
the exact log/receipt paths, and tell the human what continuation message to send
after the notification. **Do not poll the detached job from chat.** A successor
reads the receipt and log after the human returns, reconciles the result, and only
then decides the next action. Interactive execution remains appropriate for work
expected to finish comfortably below five minutes.

Every lane-owned BAMF implementation leaf or open lane PR must be represented in that lane's
machine-readable state under `docs/tasks/bamf-0.2/flow-control/`. Before substantive
branch mutation, the operator must run `python3 -B scripts/check_bamf_flow_control.py`
and ensure the intended leaf is `ACTIVE`. An already-`ACTIVE` leaf remains active
when its own agent context resumes; compaction does not require changing state,
acquiring the same issue again, or asking the owner for reauthorization.
A `WAITING` or `BLOCKED` item must record its
specific resume trigger. Parked work must **not** be merge-forwarded, rebased, fully
revalidated, sent for fresh exact-head review, or otherwise refreshed merely because
unified advanced. First confirm that its recorded resume trigger actually occurred,
then update the lane state to `ACTIVE`, then sync/revalidate once as required by the
leaf contract.

Prioritize completing near-to-merge work without serializing independent,
dependency-ready leaves. A seventh simultaneous `ACTIVE` item requires a
machine-readable lane exception naming its reason, approving owner and expiry condition.
Human review, design review, dependency acceptance and other parked gates remain real
obligations; classifying them as non-WIP means **freeze until the gate changes**,
not ignore them.

<!-- BAMF02:DESIGN-VERIFY-DRIFT-LIFECYCLE:20261108 -->
### Design review, implementation proof, drift, and integration are separate gates

Use one mechanism for one question:

1. **EGM design review** asks whether the issue/specification is correct, complete,
   understandable, and actionable before implementation.
2. **Engineering verification** asks whether the implementation behaves correctly.
3. **Design drift analysis** asks whether the finished implementation still matches
   the approved design.
4. **Integration verification** asks whether the exact candidate is ready to turn in
   against the reviewed integration branch.

A result from one gate does not stand in for another. A passing test suite does not
prove design fidelity. A clean EGM review does not prove runtime behavior. A clean
drift report does not replace tests. A premerge result does not retroactively repair
an underspecified design.

The detailed procedure is
`docs/tasks/bamf-0.2/EGM_EXECUTION.md`.

### Domain-precise language is part of execution quality

Bilqis is an ML/runtime, provenance, lifecycle, and state-consistency project.
Describe work using those relationships directly.

This matters operationally as well as stylistically. Automated systems and human
reviewers may classify work partly from the terminology used to describe it. Benign
ML/runtime work phrased with vocabulary imported from unrelated technical domains can
be misclassified, which can create avoidable warnings, latency, resource consumption,
and workflow interruption. Precise domain wording improves classification and
comprehension without changing the engineering requirement.

Use language centered on:

- component ownership and canonical sources of truth;
- provenance and lineage;
- state and identity consistency;
- lifecycle transitions;
- validation order;
- acceptance and publication;
- retry, recovery, and cold-read behavior;
- compatibility and reproducibility;
- design-to-code fidelity;
- invalid or mismatched inputs;
- deterministic proof.

This applies to issue titles and bodies, specifications, implementation plans,
review assignments, findings, test names and descriptions, commit messages, pull
request descriptions, handoffs, and durable receipts.

Describe the concrete state relationship rather than inventing a second conceptual
frame. For example:

> The prepared candidate identity must include every field whose value is published
> as part of that candidate. Changing one of those fields after preparation must
> change the identity or cause publication validation to reject the mismatch.

Existing code symbols, schema names, issue identifiers, and externally defined terms
remain verbatim where necessary. Surrounding prose should explain their actual
software role.

A finding should state the expected relationship, observed relationship, exact
difference, smallest material consequence, and proof. Severity comes from the effect
on required behavior, not rhetorical intensity.

### EGM is a pre-implementation design gate

Run pinned EGM on the issue/specification or design artifact before substantive
implementation begins. The review target is the design artifact, not the finished
code.

Use each pinned persona only for its declared purpose:

- Comprehension checks whether the design is understandable and self-contained.
- Design/Structural review checks architecture, decomposition, interfaces, ownership,
  and failure handling.
- Codebase Details checks whether the design accurately describes existing code and
  reuse surfaces.
- Implementation Readiness checks whether the implementation plan is executable
  without unresolved design choices.

Use the minimum reviewer set needed to resolve the actual design uncertainty. Do not
run every persona by default.

Fresh Goldfish receive only the design/specification, the selected persona and
standard, and the codebase context genuinely required to evaluate claims made by the
design. They do not receive the implementation conversation, prior reviewer
conclusions, Session Minutes, unrelated postmortems, or answers the design itself is
expected to explain.

Resolve the complete known design finding set before broad re-review. Re-review only
the semantically affected design scope unless architecture, ownership, decomposition,
or a shared foundation changed. Machine-checkable corrections use deterministic proof
rather than another full review.

If successive rounds keep moving the same design boundary, stop the loop and redesign
that boundary before spending another broad review.

Historical EGM comments and labels created under the former implementation-review
convention remain provenance. Do not rewrite them. Apply the new semantics to new
state transitions after this cutover.

### Implementation verification is claim-first and differential

During implementation, begin each verification action with the question it must
answer. Prefer the cheapest sufficient proof and widen only while relevant uncertainty
remains.

Use this escalation order unless the requirement itself demands a later tier:

1. deterministic/static check;
2. focused regression;
3. directly affected owner tests;
4. dependency-closure integration tests;
5. hardware/full-model/end-to-end witness;
6. premerge aggregate gate.

The existing differential verification, passing-evidence reuse, diagnostic-loop
budget, precedence-ordered diagnosis, and detached-run rules in this file remain
controlling.

Do not rerun passing evidence without a concrete invalidation. Do not use a broad
suite as the ordinary mechanism for discovering a local defect. When many failures
appear together, determine whether they share one root cause before creating separate
remediation work.

When repeated manual judgment is needed to choose tests, improve the dependency map,
validator, focused contract test, or receipt so future selection becomes mechanical.

### Post-implementation drift is the fidelity gate

When implementation is behaviorally stable, compare the approved design with the code
that implements it. Use EGM drift detection for this phase, not Implementation
Readiness.

Bound drift analysis to the approved design, its implementation surfaces, and directly
affected shared contracts. Do not scan unrelated designs merely because a tool can do
so.

Classify a material difference as:

- `IMPLEMENTATION_DEFECT`: code does not implement the approved design;
- `DESIGN_DRIFT`: code contains a semantic choice not represented in the approved
  design;
- `DESIGN_EVOLUTION`: implementation exposed a real requirement or constraint that
  requires a design amendment;
- `DOCUMENTATION_STALE`: descriptive text is outdated without a material design
  disagreement;
- `NO_DRIFT`.

Repair implementation defects with focused engineering verification. A genuine design
change returns only the affected design scope to EGM. A repair that restores the
already-approved design does not require a whole-design review.

### Integration turn-in

Run `npm run verify:premerge` only at an actual integration boundary and only when no
reusable valid receipt already covers the relevant state.

Before opening a PR require:

- completed design review;
- no unresolved required implementation defect;
- required differential evidence green or validly reused;
- required detached evidence green or validly reused;
- drift reconciled;
- required current-unified synchronization completed;
- stable candidate head.

Hosted PR checks are the final integration gate. Reproduce hosted failures at the
smallest useful scope, repair them, and rerun only evidence whose assumptions changed.

The objective is not maximum test volume. The objective is the **minimum sufficient
evidence set that makes the current decision defensible**.

### Remediation artifacts are a working set, not an archive

Keep a remediation issue open until its exact recorded defect has been reproduced,
repaired, covered by a regression, verified on a durable PR/head, **and the accepted
implementation has actually merged into its intended integration branch**. A green
or review-ready PR/head is evidence that the repair is code-complete, not that the
issue lifecycle is complete. Final parent integration or sibling work may remain
outstanding, but the remediation issue closes only after merge readback proves its code landed.

Keep a remediation PR in draft only while its own scoped implementation or known
Blocker/Major repair is incomplete. Parent-level design-review or integration work is not a reason for
draft status. Mark the PR ready when its own acceptance is satisfied; merge or close it
promptly once its change is consumed by the intended parent/candidate branch.
Closed issues and merged PRs remain provenance and should not remain in the active
queue just to preserve history once the merge-backed close condition is satisfied.

If later verification, drift analysis, or integration proves the **same original
defect** still exists, reopen the remediation issue. If it exposes a different
mechanism, newly unlocked gap, or new acceptance failure, create a new issue. The
owning parent issue/PR carries aggregate implementation and integration readiness;
EGM labels remain design-review state.
Prefer repairing a remediation issue directly on the approved parent candidate
branch when writer ownership and review isolation allow it. Do not create a separate
PR merely to preserve the finding; the issue already provides the durable defect
record. Use a stacked remediation PR only when branch ownership, concurrent-writer
isolation, or focused review requires it, and merge/close that PR promptly once its
bounded repair is consumed.
Because BAMF PRs normally merge into reviewed integration branches rather than the
repository default branch, GitHub closing keywords may not retire linked issues.
After the remediation PR is consumed by and merged into its intended integration
branch, explicitly read back the merge and issue state, then close the remediation
issue; do not assume `Closes #N` changed issue state.

The repository checker can validate declared state, WIP counts, required resume
triggers and explicit exceptions. It cannot observe an unrecorded remote mutation or
an agent merely reading a branch. Updating lane state before mutation therefore
remains an operator duty. **The ledger is scheduling state, never a distributed
mutex.** See `ADR-124` and
`docs/tasks/bamf-0.2/README.md`.

## BAMF-0.2 GitHub Project dashboard role — 2026-11-03

The `BAMF-0.2 Execution` GitHub Project is a read-model and dashboard. It may
summarize repository state, but it does not own execution state, EGM design-review
state, issue state, dependency readiness, or merge readiness. The repository issues
and labels, ADRs, BAMF task registry, flow-control records, dependency evidence, and
execution receipts remain the controlling sources.

- Treat `BAMF-Leaf` as a one-time structural projection of the current BAMF leaf
  set for Project filtering. Do not build automatic leaf-label synchronization or
  infer leaf identity from Project membership.
- Use the canonical issue labels `EGM-Pending`, `EGM-Failed`, `EGM-Mitigation`,
  and `EGM-Passed` for EGM design-review state. Do not add a duplicate Project EGM
  field or use
  PR status tokens as a second EGM state machine.
- Project views, filters, charts, and insights may derive from authoritative
  labels and issue/PR state. They must remain observational.
- Project `Status` does not close issues. Keep the Project workflow that
  closes an issue merely because `Status` becomes `Done` disabled.
- For a bounded implementing issue, a verified accepted merge into its owning
  reviewed integration target is the normal repository closeout boundary once
  the issue's acceptance and design-review obligations are satisfied. Close that issue as
  `completed` immediately after merge readback; do not accumulate merged zombie
  issues for later cleanup.
- BAMF implementation PRs commonly target the reviewed unified trunk rather than
  the repository default branch. Do not assume GitHub's default linked-PR
  auto-close will fire; the closeout operator must explicitly close the owning
  issue after verifying the merge. Regressions may reopen the issue or create a
  new one.
- Do not close a group/integration parent merely because one scoped child,
  mitigation, or structural PR merged. The parent closes only when its own
  aggregate acceptance, child, hold, and remediation gates are satisfied.

## BAMF-0.2 integration inventory and PR admission — 2026-11-02

ADR-126 separates active implementation WIP from **open implementation-PR
inventory**. The 2026-11-04 owner amendment raises the normal BAMF
implementation-PR ceiling from three to **twelve total**. There is **no one-PR-per-lane
restriction**: independent, correctly owned, reviewed integration candidates may
coexist in a lane. The unified integration PR into `main` is a separate program
container. The ceiling applies to inventory, never to number of agents allowed to
prepare independent work.

Before opening a BAMF implementation PR, inspect the available live inventory.
The following reconciler is **advisory**, not a hard admission gate:

`python3 -B scripts/check_bamf_flow_control.py --live`

If the live API is unavailable, fails TLS/authentication, or reports a ledger
timing mismatch, record the limitation, check actual PR state using another
available GitHub interface, and proceed when the independent candidate gates
are satisfied. Never make other agents' remote PR activity a hosted-CI failure
or a reason to abandon an in-flight issue.

PR admission targets an available slot (up to twelve), a durable issue/head, consumable hard
prerequisites, required current-unified synchronization, green scoped verification,
no known candidate-owned Blocker/Major, and no existing PR that already owns the
same integration delta.

If live implementation inventory exceeds the ceiling, BAMF is in **DRAIN** mode.
Do not open another implementation PR unless it replaces a PR closed in the same
operation or the flow-control policy carries an explicit owner-approved exception.
New implementation work may proceed on approved branches/issues without
increasing PR inventory.

EGM labels describe design-review state and do not serve as a PR queue. PRs are
integration vehicles. Do not keep an implementation PR open solely to represent
`EGM-Pending`, `EGM-Failed`, or `EGM-Mitigation`; issue labels preserve design
review state, while implementation proof, drift, and premerge readiness come from
their durable receipts. An active merge or remediation-delivery attempt may still use
a PR.

The flow-control checker reconciles the ledger against live GitHub state. An open
implementation PR that is explicitly represented in the ledger counts even when
its stacked parent PR has already closed. **CI runs the static policy and regression
suite only**; CI must not fail an otherwise valid PR because another agent
opened or closed a PR before the shared ledger caught up. Live reconciliation
remains a local/operator admission check, not a repository-wide CI bottleneck.

PR #741 is the temporary control-plane exception for implementing ADR-126 itself.
It is not BAMF feature inventory, and its exception expires when PR #741 merges or
closes. Do not generalize that exception by branch name or reuse it for later work.

## Context-window protection for repository census commands — 2026-11-02

Treat full-repository inventory commands as high-cost diagnostics, not routine
preflight. Do not dump unbounded `git worktree list --porcelain`, `git branch -a`,
broad `gh pr list`, or repository-wide search output into model context when the task
concerns a specific issue, PR, branch, SHA or worktree. Query that exact surface
first.

For ownership or collision checks, filter the inventory to the relevant branch or
path, or compute compact counts and candidate summaries. Run a full census only for
cleanup, ownership audits, collision investigation or systemwide reconciliation. If
raw census output is required, redirect it to a temporary file and inspect targeted
excerpts. Do not replay the full inventory into later turns, and do not repeat an
unchanged full census during normal issue or PR preflight.

## BAMF-0.2 successor outcome and admission lease — 2026-10-28

For the BAMF-0.2 successor, evaluate complete-system capability outcomes across
exact retrieval, declared deterministic computation, learned memory, neural
prediction and their compositions equally. Apply the same grade-neutral Factory,
teacher, retention and evaluation policy to every admitted grade, without
grade-letter-specific quotas or priority. Preserve source-gold, prerequisites,
whole-school retention, checkpoint/optimizer custody and the
sovereign MLX writer. These rules do not change an existing student or #324.

New semantic releases default to staging. A human-started BAMF run may authorize
continued source-valid expansion only through an explicit persisted admission
lease and the existing Factory/admission owner. First live adoption requires the
BAMF successor's disposable C16 ([#382](https://github.com/Entif-AI/Bilqis-MLX/issues/382)) source, custody and retained-learning
witness: a source-valid acquired or retained taught target under the active developmental evidence policy, preserved cumulative retention, complete
rejection rollback and equivalent cold-resume output and next update. This witness
precedes the operator's first persistent student start. Historical #324 comparison
is not its prerequisite. Only the human operator starts, resumes or stops the
durable student.
The policy is specified here; it is not yet an executable admission implementation.

## CONTROLLING USER CORRECTION — 2026-10-27: no developmental generalization

Bilqis is still a tiny developmental student learning a narrow semantic inventory.
**Do not schedule, require, or infer fresh GENERALIZATION assessment during current
training or graduation.** Routine assessment and fixed promotion remain the active
developmental lifecycle. Historical generalization cohorts, readers, enums, and
research fixtures remain compatibility evidence only; they do not authorize live
generation, graduation gating, teacher-miss injection, or score comparison. A future
generalization regime requires a new explicit human admission after the student reaches
an appropriate maturity boundary. Ordinary grade/stage movement is never promotion
authority; only the scheduler's actual grade-exam epoch advance can open promotion.

**FOUNDATION_EVIDENCE_POLICY_ACTIVE:** During the current FOUNDATION_ACQUISITION
stage, teacher-forced gold may be visible to the learning or integration witness.
Exact replay of a taught specimen is valid evidence. Exact memorization, cache lookup,
memoized procedures and learned memory all count as successful acquisition. Do not
require a held-out specimen, independent source family, fresh episode, unseen filler or
novel composition for foundation acceptance. During BAMF-0.2 alpha, still measure
novelty continuously by perturbing surface identity, role binding, relation polarity,
composition depth and semantic distance. Those novelty results are diagnostic only and
must not independently veto retention, promotion or graduation. Advancement uses the
success ratio at the current earned complexity, and previously shown examples count.
Preserve source correctness, rights, custody, rollback and protected-retention checks.
Do not turn evaluation purity into a substitute acceptance gate.

## CONTROLLING USER CORRECTION — 2026-10-23: #150 decomposes factory mechanics, not roots

The #150 micro-spec corpus is primarily an architecture/execution decomposition of
the reusable curriculum factory. It is **not** a request to open a specification or
GitHub issue for every future semantic root, capability, New Ithkuil item, or grade
candidate. A leaf is justified by one reusable factory invariant, ownership boundary,
migration seam, compatibility boundary, or focused proof. Future semantic roots are
inputs the factory must be able to accept later. Root-specific curriculum work remains
separate unless a root reveals a genuinely missing reusable factory primitive.

## CONTROLLING USER CORRECTION — 2026-10-23: full U7C Grade B

The active Prometheus curriculum now admits the complete direct-U7C Boolean set:
`B.NOT`, `B.AND`, `B.OR`, `B.XOR`, `B.IMPLIES`, `B.IFF`, plus derived
`B.COMPOSITE` and `B.IDBOOLOPS`. These are direct typed Boolean-AST lessons, not
world-model lessons. Grade B remains nongating developmental debt while Grade C is
the progression frontier. **ADR-116 supersedes ADR-094's full-pass allocation:**
after at least four progression-frontier candidate visits, B may receive one
candidate visit. Rotate earned B visits across every currently imperfect admitted
B capability in canonical order. This keeps full U7C B in circulation while
holding B candidate/retention-test effort to at most 20% of the B+C lane.
**ADR-117 makes this a role-based factory contract:** B and C are only the current
Prometheus instantiation of `bounded_debt_grade_id` and
`progression_priority_grade_id`. Future grade appends must derive those roles from
the actual debt-bearing prior grade and newly appended frontier rather than carry
literal B/C identity forward.
Do not narrow Prometheus back to a historical reduced Boolean profile, and do not
add Boolean mastery as a Grade-C prerequisite.

## CONTROLLING USER CORRECTION — 2026-10-22: foundations before worlds

**2026-10-22 follow-up — progression with Boolean debt:** NOT and AND may be
introduced and revisited, but their mastery must not gate Grade C. C keeps its
designed prerequisites and COUNT → NUMBER → SUCCESSOR → ADD → SUB progression;
it does not gain a B.NOT/B.AND prerequisite. Carry unresolved A/B debt through
the existing exact-boundary debt-admission path and cumulative assessment. Do not wait
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

## Current canonical operator binding (2026-10-17)

This repository's authoritative working root is `~/Code/bilqis-mlx`. The old codex and Chat-On-Steroids worktree paths are historical provenance, not current operator instructions. The active teacher/student code is `bilqis_mlx/`, the historical source-oracle and policy inputs are pinned under `vendor/legacy-v16/`, the actual student and its AdamW are under ignored `runs/school-mlx-v1/`, and all old experimental state is retained without making it an active runtime dependency. Human-run alone may update live neural state. See `README.md` and `docs/operations/CANONICAL_REPOSITORY_AND_RELEASE_20261017.md` for the current tested command, storage and release procedures. Conflicting older location or command examples below are superseded; source-semantic identity, cumulative whole-student graduation and protection requirements remain binding.

Authority: user's latest directives, protected `IPR-0220`, `ADR.md`, and approved issue #1. **This repository and its implementation are public.** Code, tests, architecture, ordinary implementation notes, and project handoffs may be published directly. Protected source material remains protected unless separately released; refer to it publicly only by opaque authority ID such as `IPR-0220`, without copying private-only text, credentials, attachments, or private repository URLs.

### MANDATORY DEVELOPMENT STRUCTURE INTERRUPTION CONTRACT — 2026-10-29

This is an always-on development rule. It applies when an agent **encounters** an
existing violation during ordinary work as well as when the agent **causes** a
violation. It is intentionally local and interrupt-driven, not a recursive debt
sweep.

1. **Code-file trigger and Work Stack preservation:** If a project-authored code
   file is **>360 LoC**, immediately pause the work that led to the encounter.
   Record **all current working context** for that task in **@Entif Work Stack**
   before doing more feature work. The same interruption is mandatory if an edit
   would cause a file to cross `>360 LoC`.
2. **Mirrored file remediation:** Refactor the offending production file into
   cohesive imported submodules until the original file is **<240 LoC**. Refactor
   every companion test file along the same module boundaries until **each
   companion test file is also <240 LoC**. Production/test ownership must mirror:
   moving a method to `new_method.py` moves its focused tests to
   `test_new_method.py`.
3. **Branch and resume semantics:** The structural refactor remains on the
   already-active feature branch because the encountered code is presumed germane
   to that work. Commit the refactor as a normal coherent change. After the
   offender satisfies the remediation target, mark the interruption complete in
   Work Stack and resume the preserved original task.
4. **Directory trigger:** If an agent encounters a directory containing **>=18
   direct project-authored code files**, excluding directories themselves and
   third-party/external libraries, preserve the current task in Work Stack and
   reorganize **only that offending directory** into thoughtful subdirectories
   until the original directory has **<=12 direct code files**.
5. **No recursive cleanup cascade:** During that directory interruption, do not
   recursively inspect or reorganize the newly created subdirectories merely to
   hunt for more debt. Resume the preserved task. Handle another file/directory
   offender only when it is encountered organically in later normal work. If an
   individual oversized file is directly encountered while performing the current
   repair, it becomes the next single interruption after the current one reaches a
   committed, resumable state.
6. **No governance laundering:** Never raise the `>360`, `<240`, `>=18`, or
   `<=12` thresholds, weaken enforcement, add exclusions, expand/grandfather a
   quality baseline, or rewrite governance merely to make a violation or CI result
   disappear. Existing debt is evidence to remediate when encountered, not
   permission to normalize more debt. Any change to this contract requires
   explicit human ratification.
7. **Mechanical enforcement is necessary but not sufficient:** commit hooks,
   local checks, Codex/ChatGPT execution, and CI must enforce every deterministic
   part of this contract that their surface can actually observe. A hook or CI job
   cannot prove which files an agent read, so **encounter-time interruption remains
   an agent duty even when repository-state checks are green**. Do not claim that
   CI detected a read it could not observe.

**MANDATORY AUTHORITY-CONVERGENCE CONTRACT:** Read [`docs/architecture/10_CURRICULUM_AUTHORITY_CONVERGENCE_20261019.md`](docs/architecture/10_CURRICULUM_AUTHORITY_CONVERGENCE_20261019.md) before changing curriculum semantics, execution profiles, source bindings, answer modalities, factory release identity, assessment scope, championship dependencies, New Ithkuil ingestion, telemetry inventory, or the factory migration plan. Preserve source roles: direct user decisions and current normative specs govern; the Ledger normalizes; the Curriculum Registry and Ithkuil corpus provide evidence/provenance; roadmaps and research seeds guide sequencing; historical releases remain compatibility evidence. Do not silently promote a historical experiment into current architecture or collapse a recorded conflict into implementation.

**MANDATORY CURRICULUM FACTORY CONTRACT:** Read [`docs/specifications/0001_GENERATIVE_CURRICULUM_FACTORY.md`](docs/specifications/0001_GENERATIVE_CURRICULUM_FACTORY.md) before changing semantics, source construction, lessons, grades, assessment lifetime, admission, graduation, curriculum runtime, or documentation architecture. The factory is the only permitted production route from admitted semantics to an executable grade: **no factory release, no grade**. New grades must be declarative factory instances and must not add canonical `live_grade_*`, `grade_*_trainer`, grade-specific scheduler/evaluator/dashboard branches, or alternative runtime paths. Unit/contract tests belong beside their owning packages; top-level tests are integration/system only. SPEC-0001 requires the generic runtime cutover, A/B/C migration, routine/promotion developmental assessment, and synthetic Grade Z extensibility test. Generalization and novelty are measured in alpha but are not fixed advancement gates; any later fixed held-out/generalization gate requires explicit human admission.

**ISSUE #150 MICRO-SPEC EXECUTION BOUNDARY:** Read [`SPEC-0005`](docs/specifications/0005_FACTORY_MICROSPEC_WORKSTACK.md) and [`TASK-0003`](docs/tasks/0003_FACTORY_CLOSURE_CODEX_RUN_PROTOCOL.md) for the workstack/executor contract. Each fresh execution session reads root `README.md` and `AGENTS.md` once before source mutation, then bootstraps only the authorities needed for its current bounded work. After bootstrap, ordinary leaf execution is page-local: the issue number is the durable bookmark, and the executor reads only that leaf, its live page gate/amendments, its named direct prerequisites, and its declared files. `FACTORY_DEPENDENCY_BLOCKED` is a staleable observation; recheck only the named direct prerequisites, without requiring a same-page amendment merely to reevaluate dependency state. Do not hydrate parent issue #150, the full manifest, all receipts, or a global ready set during ordinary leaf execution. Git and GitHub receipts are durable state; model context is cache. Keep healthy warm sessions across cold page boundaries and do not start a new expensive session solely for isolation. Put transient current-page state in the active handoff or issue checkpoint, never durable architecture prose. A leaf still requires exact dependencies, bounded read/write surfaces, named symbols, compatibility invariants, focused verification, and stop/block rules. Do not rediscover architecture by broad exploration or create root-by-root tickets merely to make the graph larger.

**MANDATORY CHAMPIONSHIP CONTRACT:** Read [`docs/specifications/0002_CHAMPIONSHIP_LIFECYCLE_V1.md`](docs/specifications/0002_CHAMPIONSHIP_LIFECYCLE_V1.md) before changing admission, champions, soups, mentor references, comparison gates or retirement. Capability titles are defended independently with fresh incumbent/contender inference over current questions plus the capability's surviving title battery; cached neural predictions never adjudicate a title. A max score on one same-grade capability is sufficient to open that capability's title fight. Every `(capability, unordered checkpoint pair)` may settle exactly once for the lifetime of the run; no changed score, cohort, battery or later ownership permits a rematch. Active title ownership is grade-isolated: the checkpoint's retained-update origin grade must equal the capability grade, and legacy cross-grade owners are archived/inactivated rather than grandfathered. One actual takeover may trigger exactly one non-recursive same-grade fan-out screen for sibling titles, skipping already-settled pairs. Stagnation quarantine is capability-local teaching/scheduling authority and MUST NOT blanket-disable championship processing for other completely measured capabilities. Teaching geography is separate from title geography: every active maxed capability role contributes one direct source-gold-gated advisory vote to lessons in any admitted grade; non-max roles contribute zero direct role votes; frozen soups remain a separate aggregate adviser with full same-grade base votes and the existing diluted foreign-grade voice. Bind all active championship-derived advice to one unchanged holistic school identity; **any identity mismatch archives and clears every active champion and every active soup together before advice or defense**, while preserving the causal student+own AdamW, immutable history and settled-match ledger. Flash and candidate retention remain separately governed.

**Retention default (ADR-048, 2026-10-17):** Regular human-run training/resume and read-only preflight use source-oracled parent/challenger retention without an opt-in flag. Do not prescribe the former `--experimental-retention` switch in new commands. `--no-retention` requires a separate explicitly selected run directory and must fail closed for an existing protected lineage; never silently disable student/AdamW custody because an operator omitted an option. This operational default does not prove complete cumulative neural retention or graduate the student through a source release.

**Candidate retention (ADR-054 through ADR-057, refined by ADR-079 and ADR-100):** Read docs/specifications/0003_CANDIDATE_RETENTION_GRADE_NET_V1.md before altering admission. The target fresh probe must always improve. Preserve grade/school aggregate non-regression and bounded capability tradeoffs together. Protected-capability loss budgets are proportional to the capability's actual paired-question count, using the configured reference-probe rate (`mature_max_loss / probe_each`, or the MAIN developmental reference allowance where applicable), never a fixed raw-answer ceiling. A protected loss above that scaled budget rejects even when aggregate totals improve; losses within budget may trade against larger gains when fresh lesson-grade, fixed lesson-grade, active school-grade and whole-school gates pass. Mature debt is a grade-level net ledger derived from successive fixed-frontier grade deltas; never carry row/capability debt across changing cohorts. Debt at 2+ answers schedules one complete same-grade repair pass; that grade may receive at most one debt-repair pass per school sweep before the scheduler yields. Debt may reach 4, but a candidate that increases a mature grade beyond 4 total debt rejects. Holding or reducing pre-existing debt remains admissible. Never use a historical checkpoint as the candidate parent. B.OR/B.XOR fixed-row flips remain diagnostic-only in the late-stage regime. The saved frontier exam must match the current retained parent SHA and native AdamW step exactly or admission fails closed. Retain the intact parent and own AdamW on rejection.

**Teacher exploration (ADR-101):** `EXPLORE` means a genuinely novel effective strategy, not merely a low-support policy or another draw from the existing archive. Low-support health is `UNCERTAIN`. Sustained rejection pressure may mint bounded fresh effective challengers only from the existing approved knob vocabulary and archive limits; behaviorally equivalent aliases do not count as exploration. Persist the selection reason so later review can distinguish mutation from ordinary archive rotation.

**Teacher cooldown (ADR-102):** Same-student retirement is temporary and checkpoint-local, but repeated exhaustion must survive unrelated student advances. Promote an effective policy into durable capability cooldown only after it reaches the existing four-unretained-attempt limit on two distinct student checkpoints for the same capability/scope. Cool it for eight subsequent visits to that capability, not global visits; expiry decays one failed epoch and a retention clears the cooldown immediately. Exact cooldown filters both contextual and vNext-canary selection. Same-grade siblings receive only the bounded `0.025`-per-sibling, `0.05`-max ranking penalty and are never banned by sibling evidence. `EXHAUSTED` in the dashboard must correspond to this selector-visible cooldown state.

**Frontier catch-up (ADR-103):** Raw capability-count fairness must not starve a newly introduced highest grade. In ordinary cross-grade MAIN sweeps only, if the newest active grade's mean score across currently introduced/eligible semantics is below the median active-semantic score, give it enough separately assessed MAIN passes to target about 25% of sweep visits: `ceil(non_frontier_semantics / (3 * frontier_semantics))`, minimum one. Stop the extra passes at/above the median. Never let catch-up replace promotion sweeps, recovery, mature-debt repair, or explicit debt cadence. Compact operator presentation must explicitly label active promotion sweeps as `SWEEP GRADUATION <grade>`.

**Teacher evolutionary search (ADR-104, amended by ADR-115):** When sustained rejection pressure (4+) has no active retained current-context recipe, use bespoke hereditary exploration rather than archive roulette. Breed from retained same-capability evidence first, matching diagnostic/champion context when available, then retained same-grade ancestry, then grade/global reward fallbacks. Mutate one effective knob at a time. Fresh children remain capability-local until they retain; after actual retention, a numeric-scope revision in the same release family may retry that proven policy for the same capability as a fresh challenger, but old-scope reward/context evidence is never copied forward. Teacher vNext may not override a fresh child or portable retained challenger on that bounded trial. `UNCERTAIN` means genuinely under-observed across exact/capability/grade/global evidence, not merely new to one tuple. The live strategy population scales with active curriculum size: `max(48, 24 * active_capabilities)` effective strategies live, with `max(8, 2 * active_capabilities)` active at a time (bounded by live capacity). Rebalance by retaining proven strategies first and giving young unretained policies bounded probation ahead of older unretained strategies. Retire old weak strategies from live selection without deleting historical evidence. Historical nominal archive size must not prevent new effective invention.

**Retention-first pressure control (ADR-115):** Sustained rejection pressure makes hereditary exploration available; it does not make every pressure visit exploratory. A current-scope active policy with actual retention evidence runs before another child is minted. Existing same-student failure retirement remains the bound: after four unretained or no-target-gain uses on that checkpoint, the effective policy leaves the active set and pressure breeding resumes. In live-population ranking, any retained effective strategy outranks unproven newborn grace. Newborn grace ranks only within the unretained population, so a stream of one-shot children cannot evict proven recipes. Cross-phase retained ancestry still seeds a new child when the current context has no active retained recipe. This changes teacher selection only; retention, plasticity, source, custody and mature-debt gates do not change.

**Retention-surface support and bounded-debt effort (ADR-116/ADR-117):** Candidate construction spends generic fresh retention-support steps on the surfaces that can directly veto admission: the lesson grade and latest active progression frontier. When the verified fragile-replay channel already preserves B.OR/B.XOR, generic support must not reserve duplicate slots for those same capabilities. Earlier-grade rehearsal remains owned by the teacher's `old` policy. The scheduler itself is grade-ID agnostic: after `non_debt_turns_per_run` candidate visits to the configured progression-priority grade, the configured bounded-debt grade receives one candidate visit, rotating canonically across its imperfect debt. Current Prometheus instantiates that as four C visits per one B visit. Durable counters are `bounded_debt_visits` and `priority_visits_since_bounded_debt`; B-named counters are legacy read-only migration inputs. On a debt-bearing factory grade append, derive the bounded-debt role from the latest prior grade represented in the carried debt and the priority role from the newly appended grade; preserve the cadence value. A clean append clears stale debt roles. This changes training allocation and construction only, never the retention gates themselves.

**Adaptive teacher evolution (ADR-107):** Exhausting the legacy effective policy lattice must not terminate invention. After ordinary one-knob hereditary mutation cannot produce novelty, refine exactly one retained parent's controllable numeric gene locally: integer `old`, positive `lr`, or `distill`, always inside the historical knob envelope and with deterministic bounded quantization. Keep `depth`/`contrast` categorical until runtime semantics become genuinely graded; keep unavailable `preview` out of effective identity. Record append-only realized-action ecology from delivered teacher-action receipts and attach realized novelty to bespoke births. Realized novelty may break otherwise-equal exploration/ancestry ties but never counts as retention, reward, or permission to weaken source/custody/preservation/frontier gates. Historical policies remain immutable.

**Retention-starvation plasticity (ADR-108):** Keep ordinary retention gates unchanged until one capability has gone 32 consecutive attempts without retention, or 16 when it belongs to the newest grade or current introduction stage. Then, only if the active capability strictly gains, allow at most `-1` same-grade net, one answer beyond ordinary per-protected-cap loss tolerance, `-1` fixed-grade net, `-1` active-grade frontier net, and `-1` whole-school frontier net. Fragile replay, source/custody/semantic identity, no-target-gain rejection, and mature-grade debt hard limit remain hard. A retained candidate resets the starvation counter and closes plasticity on the next visit. Emit explicit telemetry for activation and any waived ordinary rejection reason; never call temporary regression repaired merely because the candidate retained.

**Progression-frontier allocation (ADR-109, amended by ADR-117):** The ADR-103 roughly-one-quarter frontier visit floor persists while any currently introduced semantic in the newest progression-priority grade remains imperfect. Reaching or exceeding the school median does not end priority; only actual mastery/advancement does. Keep the existing `ceil(non_frontier_semantics / (3 * frontier_semantics))` bounded MAIN-pass formula and minimum one pass. Historical B/C receipts that predate role-neutral debt counters may neural-inertly rehydrate the canonical ADR-094 bounded-B / progression-C policy when the saved policy is missing/null. New role-neutral receipts must never infer B/C from grade names: an explicit null remains null, and append transitions derive roles from factory topology plus carried debt. This changes scheduling allocation only; promotion, retention and mature-debt repair remain unchanged.

**School-wide plasticity trigger (ADR-110):** ADR-108 local starvation remains active, but plasticity also activates after 24 committed teacher visits without any retained/provisional candidate when the current capability's latest exam accuracy is strictly below the unweighted mean accuracy of all valid capabilities in the latest whole-school exam. Count every committed teacher visit once, reset the global counter on any committed retention, and give each semantic one vote regardless of exam cohort size. Missing current-capability score evidence, equality/above-mean score, promotion sweeps, or non-training stages do not qualify through the global path. This expands only plasticity eligibility; ADR-114 now governs active-plasticity trade valuation while the hard safety/debt gates remain unchanged. Emit trigger provenance, drought count/threshold, current score and school mean in plasticity telemetry.

**Normalized plasticity trade utility (ADR-114; supersedes ADR-108 raw loss caps):** Once plasticity is active, compare candidate tradeoffs by one-vote-per-capability normalized quadratic mastery debt, not raw correct-answer loss. For accuracy `a`, debt is `1-a` and energy is `(1-a)^2`; candidate utility is the sum of `E_before-E_after`. Strict target gain remains mandatory. Same-grade and complete paired-protection utility must both be positive before plasticity can waive a raw regression. Negative fixed-grade, active-frontier, or whole-frontier raw deltas may be waived only when that exact surface has per-capability paired scores and positive utility; missing detailed scores fail closed. Fragile replay, source/custody/semantic identity and mature-grade debt remain hard. When plasticity first changes admissibility, retry an eligible pre-plasticity target-gaining near miss under fresh source scoring before endlessly breeding new pressure challengers. Emit per-surface utility telemetry.

**Promotion retry course-correction (ADR-111):** A failed promotion sweep must persist its imperfect sweep capabilities and exact scores as the retry blocker baseline. The same promotion scope may retry only after ordinary sweep-entry eligibility is met and the unweighted mean accuracy of those blockers is strictly better than at the failed attempt; a changed student hash or retention elsewhere is not enough. Clear the baseline on successful semantic introduction, actual promotion, or an authorized next-grade boundary. This gates retry timing only and does not lower 92% entry, 87% hysteresis, retention, promotion, source/custody, mature-debt, ADR-094 B-share, or ADR-109 frontier-allocation rules.

**Full Grade B default and migration (ADR-112):** Full canonical U7C Grade B (`NOT`, `AND`, `OR`, `XOR`, `IMPLIES`, `IFF`, `COMPOSITE`, `IDBOOLOPS`) is the default operator profile. The old AND/IFF kernel is explicit-only via `--reduced-grade-b` / `--minimal-grade-b`; do not silently narrow a normal run. A known historical reduced-B receipt must neural-inertly expand to full B on default resume even when C is already active: preserve student+native AdamW, add newly restored B semantics as carried mastery debt, invalidate stale assessment/championship authority, and return scheduling to the newest progression frontier. Never fabricate mastery for restored semantics.

**Severity-weighted frontier recovery (ADR-113):** In progression-priority recovery, keep the weakest up-to-three frontier semantics but weight actual visit count by deficit below the unweighted whole-school capability mean. Give every imperfect frontier semantic one maintenance visit plus one extra visit per additional 10 percentage points below the mean, capped at six visits in one recovery queue, interleaved by ranked capability. Weighted duplicates belong only in the executable `queue`; `first_recovery` must remain the unique ordered capability set for stagnation control. This changes training allocation only; exam frequency, B debt cadence, promotion, plasticity, mature-debt, retention, source and custody rules remain unchanged.

**Integer scope + weakness identity (ADR-105):** Compact operator telemetry must show `INTROOT 0...N` from the current durable `numeric_maximum`, and profile-adoption events must refresh that scope live. Champion-directed weakness discovery may collapse repeated occurrences of the same exact source-row ID to one target because source lesson draws can repeat specimens. Do not relax downstream weakness-target identity validation: duplicate target IDs from any other path remain a hard conflict.

**GRAD + Grade-C numeric staircase (ADR-106):** `GRAD` means `distinct grades reached . unique successful promotion frontiers . promotion-sweep attempts`, shown as current execution / lifetime. The first coordinate is idempotent by grade. The second is idempotent by actual grade/introduction frontier: mature-grade revalidation, repeated boundary receipts, or returning to an already-admitted later grade may add attempts but must not mint another graduation success. Canonical Grade C enters at integer scope `0...4`, then after each fully mastered C boundary advances exactly one root through `0...10`; scope 10 is terminal for C. This staircase is canonical and does not require the legacy `--numeric-staircase` flag. A one-shot `numeric-0-10` C receipt with no `numeric_scope_final_maximum` is a migration signature: when C next becomes active, rebind neural-inertly to `0...4`, set terminal 10, preserve the student and own AdamW, and resume. Do not rewind a legitimate C@10 receipt carrying terminal-scope lineage. Do not invent Grade D if the executable curriculum does not yet contain it.

**Staged grade qualification and championship changes (ADR-055/057/058, superseded where SPEC-0002 revision 7 differs):** Do not spend the fixed school frontier on candidates that fail their target or regress their fresh lesson-grade panel. Late-stage whole-school candidate scoring is permitted only after those cheap stages and reuses the exact immutable cohort plus reconstructed parent predictions. Champion succession is a separate proof and follows SPEC-0002's capability-local defended-title flow; do not restore the older complete-grade/cross-origin takeover gate, repeat a settled pair, preserve cross-grade title owners, let unrelated quarantine suppress a valid contender, or carry live champion/soup authority across holistic school-identity drift.

**B.OR/B.XOR candidate replay (ADR-049 as refined by ADR-057):** Reuse only verified fixed whole-school source-gold rows and never feed those exam identities as preservation lessons. Before a complete fixed school frontier exists, parent-correct replay regressions remain the older item-level veto. Once the complete frontier exists, replay flips are diagnostics/teacher evidence only; late-stage admission is governed by nonregressing lesson-grade, active-grade and whole-school aggregates.

**Fragile-semantic rehearsal + unchanged-exam reuse (ADR-056/057):** Prefer fresh OR/XOR siblings matching fixed-row truth pattern + operand kinds + universe size, fall back to the same operand shape and then truth pattern, and never block training merely because one exact sibling was not sampled. Fixed exam IDs never enter preservation lessons. A scheduled exam may reuse a prior result only for an identical retained SHA/AdamW step/cohort/rubric/scope/graph with zero retained pending updates. The #340 baseline/championship rule remains unchanged.

**Longitudinal diagnostic correction (ADR-050):** Count a student checkpoint only once in a comparable same-scope learning trajectory even when full-school exams repeat with identical optimizer step and model identity. Validate all underlying exam/outbox/cohort records and preserve the raw audit ledger; a changed student hash at the same step, backward step, or divergent evidence still fails closed. Display the actual history error instead of interpreting unavailable S3 observations as proof of no retention problems. This affects diagnostic reporting only and cannot change the teacher, student or AdamW.

**Sole-grade mastery-debt rehabilitation (2026-10-18):** Temporary stagnation containment still removes repeatedly failed capabilities from ordinary teaching/evaluation for the remainder of the containment episode and never forgives mastery debt. If healthy work is exhausted and **all remaining quarantined required debt belongs to one grade**, the trainer may continue the same human command by explicitly re-admitting **only those recorded debt capabilities** into recovery. This is rehabilitation, not mastery: it must not synthesize scores, permit promotion from partial evidence, weaken fixed-frontier preservation, or erase the historical quarantine evidence. An examination that was sampled while capabilities were withheld remains a partial examination for championship/soup authority even if rehabilitation releases the debt after scoring. Any end-of-run warning whose withholding was overridden must say so rather than falsely claiming the capability remains withheld. Mixed-grade deferred debt retains the existing review/re-entry behavior; do not silently generalize this override into a new mixed-grade policy.

**Issue #340 B rehabilitation grace (2026-10-18):** The user's latest directive supersedes active B quarantine during this damaged-representation recovery episode. A human operator may explicitly activate a **100,000 retained-optimizer-step B-only stagnation grace** on resume. While that persisted grace is active, stagnation diagnostics and would-have-quarantined evidence continue to be recorded, but the quarantine actuator must not withhold B capabilities. A/C and other grades retain ordinary containment. Candidate retention, fixed-frontier preservation, fresh routine evaluation, mastery debt, promotion and graduation requirements are unchanged. The grace survives command restarts by being stored in the run receipt, expires by absolute optimizer step, and must not silently renew or reset its deadline. Only an explicit human-owned run option may create or renew such a grace.

**Candidate-feedback strategy learning (ADR-051, amended ADR-080):** For retention-protected lessons, rejected trials must teach both contextual selection and the inherited strategy bandit from the already source-grounded causal outcome rather than a zero-valued retained-training delta. Contextual UCB uses the inherited teacher's `0.6` exploration scale. Preserve phase-specific outcome statistics, but repeated `NO_MEASURABLE_TARGET_GAIN` debt is additionally tracked across MAIN / RECOVERY_1 / RECOVERY_2 for the same capability + curriculum scope + policy. That shared debt divides the exploration contribution by `1 + streak`; do not substitute another arbitrary additive penalty. A no-target-gain trial also repays inherited-bandit optimism with forward-only negative selection credit at least equal in magnitude to the inherited exploration contribution for that policy, while preserving any stronger measured retention/interference penalty. Any measurable target gain immediately resets the shared debt even when another retention reason later rejects the candidate. Preserve historical teacher statistics, `teacher_reward` meaning, and phase-local diagnostic records; expose `teacher_selection_reward` separately on new events. Never permanently ban a policy, rewrite historical UCB records, or promote rejected weights/native AdamW. Legacy independent no-retention lessons retain their prior bandit reward.

**Current 2026-10-17 scheduler/strain correction:** Rank recovery's weakest *up to three imperfect* capabilities across the complete cumulative introduced-and-graduated assessment pool, never only the active grade and never padding with perfect skills. Avoid redundant MAIN optimizer trials for already-perfect targets using source-oracled prechecks; keep full cumulative exams and normal grade admission/revalidation. For trial weight geometry, keep the actual epoch-start model fixed and compare against the highest-scoring comparable **whole-student** checkpoint. Ratchet the latter only after strictly improved cumulative same-scope examination via `advance_peaks`; ties, local candidate acceptance and grade-soup refresh never ratchet. Keep candidate scoring against the pre-transaction reference, preserve mismatched semantic/tensor identity as not measured, and make the geometric signal advisory to the teacher and diagnostics. Never overwrite actual student or AdamW from these comparisons.

**Three-lane execution boundary (ADR-063):** The current protected trainer may use at most two spawned host-side source-preparation workers plus one sovereign MLX/student lane. Worker inputs must exclude model parameters, optimizer state, writable run paths, checkpoint/student authority, teacher state and scheduler state. Workers may only prepare deterministic source material for exact future step identities; stale or mismatched packets fail closed. MLX inference/training, AdamW, retention admission, teacher credit, scheduling, exams and persistence remain serialized. Keep `--source-prefetch-workers 0` as the serial control. Do not generalize this into parallel neural candidates or concurrent MLX without a new user decision and proof.

**Ternary fallback boundary (ADR-064):** If the human decides the present FP32 recovery lacks meaningful growth, the next major experiment is a separate ternary-from-scratch lineage. Do not warm-start FP32 weights, copy AdamW, inherit active titles/soups as teaching authority, or rewrite the FP32 run in place. First hold the six-layer/width-384 topology and source/curriculum/evaluation contract constant so weight representation is the main changed variable. Record latent precision, ternary quantizer/scales/rounding, activation precision, optimizer/init and export semantics; preserve exact hashable ternary codes used for evaluation. A later widened or canonical BitNet-style architecture is a separate experiment.

**Binary lesson structural coverage (ADR-065):** For source rows with explicit `operand_truths`, preserve every source-valid active-connective pattern in each optimizer batch before old-grade rehearsal allocation may consume the remainder. Do not let adaptive `old` pressure erase part of the current connective's truth table. Record required/delivered semantic-pattern counts. During B lessons, Boolean association bridge rows must use the active B connective; B.NOT uses one opaque source proposition and binary connectives use two. Broad untargeted bridge utilities may retain random binary-operator sampling. Do not reinterpret this structural minimum as permission to override teacher learning-rate/distill/depth/contrast policy, oracle gold, exams, scheduling, retention or custody.

## Current priority: prototype-first experimentation (ADR-041)

The user's 2026-10-17 correction sets the operating standard: one person, a $50/month budget, and rapid trials of novel learning/self-optimization strategies. Build the smallest working experiment, run a cheap bounded trial, inspect learning and earlier-skill retention, then keep, revise or discard it. Reuse the existing typed AST, generator, trainer and checkpoint owners. Prefer working behavior and short observations over new qualification infrastructure, diagrams or reports.

For exploratory trials, defer independent outcome attestations, causal attribution, matched research baselines, exhaustive finite/family qualification, externally reviewed source manifests and completion of a generic cutover framework. These are not prerequisites for trying an idea. Check the sources and answers needed for the chosen small slice; run focused tests for bugs that could invalidate or damage that trial. Report observations plainly; “promising in this trial” is a useful result. Before adding a gate, identify the concrete wrong answer, lost state or wasted run it prevents; otherwise defer it. This supersedes older assistant-imposed research gates for exploration, including the qualification-first next actions in ADR-038 through ADR-040 and earlier handoffs.

Preserve real-student/own-AdamW recovery, stable token meanings, answer correctness, teacher ownership and disk protection. The human owns ordinary and long-running actual training. The user's standing repair authorization permits agents to run short, explicitly finite trainer sessions on the current student when necessary to reproduce or verify a trainer defect; use a bounded `--minutes` and/or `--max-visits`, preserve the existing student and own AdamW, inspect the committed boundary afterward, and never convert that permission into unattended/open-ended training, reset, replacement, or a bypass of trainer safeguards. Use isolated disposable models for broader agent-run learning trials. Actual new-grade integration still needs correct catalog/output bindings and the existing recovery path; unknown meanings must not become training gold. The ten questions guide useful choices without requiring a publication dossier for every experiment. Existing qualification modules are optional tools, not the next development objective. Do not add a bypass to the actual trainer or claim that documentation changes have removed executable checks.

**Numeric staircase (ADR-044, superseding ADR-043's experiment-only disposition):** The user asked to pause C and warm-start the latest complete student at **0..3**. Human `--resume --numeric-staircase` enrolls COUNT → NUMBER → SUCCESSOR → ADD → SUB at 0..3, then progresses to the final 0..4 profile when the current foundation earns expansion; MUL and DIV become eligible at 0..4, not at 0..3. Subsequent resumes detect the saved mode. Reuse existing AST/generator and atomic generation/outbox owners; preserve exact weights, own AdamW, teacher, champions, soups and previous enrollment. All 227 embedding rows stay allocated. New scope exams carry fresh identities; older mastery is historical. Wider unresolved mistakes remain deferred. The experiment stops at 4 (`numeric_scope_final_maximum=4`); 5..10 and a neural undefined-answer primitive remain later work. Earlier 0..5/0..6 plans are historical, not active instructions. The canonical Prometheus run is still on 0..3 and has not yet graduated to 0..4. Normal updates remain human-operated; the bounded trainer-repair exception above does not authorize open-ended autonomous training.

**Current C pilot (ADR-042):** Native C catalog readback is packaged at `semantics/numeric_registry_v1.json` (227 tokens; original 222 rows preserved). With `BILQIS_INTEGER_MAX=10`, actual saved-run preflight reports no blockers. C's human pilot uses source/correctness/custody checks, without the external-review dossier. The existing historical A/B compatibility owner selects the parent contract; C stores `grade_c_parent_course_digest` for later resumes. A disposable current-run copy passed admission, pointer-crash recovery and repeated resume with no optimizer steps. See `README.md` for the exact worktree/run command. Human-only actual training remains binding.

**Implementation context:** Source `f14b90d` has 466 passing tests and 2 skips; the prior documentation checkpoint is `b79dcea`. The generic cutover planner has no executor, and outcome comparison is unused by the live trainer. These unfinished optional components do not block a disposable learning experiment. See `HANDOFF.md` for the next small slice and real-student boundary.

## READ FIRST: protected curriculum-remediation authority

**Mandatory for every agent and every handoff:** Resolve the current `IPR-0220` remediation authority when the execution environment is authorized to access it, together with the user's five original bad-lesson signals, adaptive-teacher noninterference, spiral retention, and all primitive/lesson/grade/test changes (`ADR-027`, `IPR-0220`). Read the active public issue, linked public source evidence, and most recent checkpoint before proposing implementation. **Every handoff, compaction brief, implementation-issue checkpoint, and agent-to-agent task packet MUST include** the opaque `IPR-0220` authority ID when materially relevant, source branch and verified HEAD, completed/provisional work, unresolved coverage/learning risks, incident IDs, actual human-student boundary and next permitted action. **Publication boundary:** this repository and implementation are public, so no screened public projection is required for repository-owned implementation details. Do not copy private-only source text, credentials, attachments, or private repository URLs from protected authorities into tracked public artifacts unless the user separately releases that source material.

**READ BEFORE EVERY GRADE SELECTION, DESIGN, PROBE, ADMISSION OR HANDOFF:** The user's original ten-question mandate and correction are preserved **verbatim** in protected IPR-0220 issue #336, source-comment `6233567989`. Do not substitute the shorter architectural RFC for the user's words. `npm run curriculum:review -- --grade C --phase selection` and `docs/provenance/grade-reviews/<grade>.json` remain optional planning tools for the prototype. Reconsider the ten questions when selecting and refining a grade; ADR-041/042 supersede the external-review dossier as a gate for the current C pilot. The historical spreadsheet tranches are candidate provenance, **never next-grade scheduling authority**. Every chosen foundation must defend its immediate text-model usefulness, independent-source evidence, neural-versus-codec necessity, smaller alternatives, qualified earlier-grade or earlier-stage prerequisites, and specific downstream capabilities unblocked. D's historical phonology suggestion is currently **unselected** and unqualified for a text-only neural grade. Generic source/semantic qualification and human-run authorization are separate. See `ADR-036` and `docs/history/architecture/EVERGREEN_GRADE_FACTORY_PROPOSAL_20261017.md`. A structural checker does not prove its own evidence or grant admission; incomplete source review blocks the new release while existing A/B custody remains intact.

**ADR-037: positive identity before contextual interpretation.** User's follow-up is preserved in protected issue #336 comment `6234081376`. Identification defines a primitive positively through previously established prerequisites, never by listing adjacent meanings it excludes; contextual association retrieves plausible applicable meanings and disambiguation narrows them using progressively wider evidence. The three families are non-exhaustive and do not require three executable methods per mathematical primitive. Grade review v2 makes their **planning dispositions** explicit (`DEFERRED`, `FOUNDATIONAL`, `REQUIRES_QUALIFIED_IMPLEMENTATION`), and must not self-approve the last disposition. Preserve the singular typed catalog/AST and independent tests; do not manufacture language lessons to satisfy a future-state interface.

**Evidence-first writing in every artifact and message:** Lead with observations, supported mechanisms, decision-relevant uncertainty, and concrete next actions. Use concise, affirmative prose in conversations, GitHub issues, ADRs, handoffs, incident reports, documentation, and code comments. Preserve actual safety rules, authority limits, source requirements, and consequential evidence gaps. Remove speculative rebuttals to unmade claims, irrelevant counterfactuals, and defensive qualifiers that add confusion.

**Immediate BIOS incident duty:** Upon a material bug, near miss, student regression, evidence/provenance gap, misleading readiness claim, repeated anti-pattern, or user correction exposing a reusable failure, invoke BIOS `references/runtime/FAILURE_INTELLIGENCE.md` and its **Post-Mortem Logger** (`references/vendor/entif-postmortem-logger/ENTRYPOINT.md`) **at discovery, not after a fix or feature closeout**. Freeze evidence, separate observation/hypothesis, search the canonical Entif Post-Mortem Ledger for the same incident/root cause, file or enrich without duplicates, and **read back the native Sheet** before calling it logged. Include incident ID and applicable controls in the issue and handoff. Current: `PM-2026-10-16-001`, `RC-083`, `RC-084`, `PAT-066`; earlier teacher override: `PM-2026-10-14-014`. ADR/README notes alone do not count as PM logging.

**ADR-028: composition-first semantic architecture:** The user's latest direction replaces one-off grade/test implementations and invented `SemanticLaw` labels with a code-resident, single-authority typed semantic AST bound to the **original Curriculum Registry semantic/lesson IDs and immutable 222-token ABI**. Deconstruct the ten cited GitHub implementations and applicable external symbolic libraries into independent, source-traceable behavioral contracts; build inspectable higher-order compositions (curry/partial/lift), reuse independently verified methods, and prove unsupported laws/world translations before admission. See `docs/history/architecture/04_COMPOSITION_AND_UPSTREAM_REUSE_DECISION.md`, `05_BEHAVIORAL_CONTRACT_V1.md`, `06_UPSTREAM_SOURCE_METHOD_LEDGER.json`, ADR-028 and protected issue #336. A source-only Boolean composition slice is experimental and neither changes the human trainer/teacher nor qualifies broader semantic coverage. Carry the contract, source ledger, verified tests, remaining gaps, `PM-2026-10-16-003` and latest branch SHA into every handoff. **Do not restart the broader generic factory with more handwritten grade-specific branches.**

**ADR-029: modular ownership and typed contracts:** Grow by cohesive domain boundaries, not an ever-expanding `composition` directory or a speculative package tree. Separate canonical semantic/law definitions, pure expression composition, source adapters, and independent verification/coverage. Define machine statuses and domain outcomes once as typed enums/constants and import them in producers, consumers and tests. Do not present free-form law metadata as catalog admission. Preserve existing serialized values where required; migrate callers and delete redundant legacy entrypoints in the same verified change. See ADR-029 and `docs/architecture/08_MODULE_BOUNDARIES_AND_TYPED_RESULTS_20261016.md`.

**ADR-030: vocabulary ABI single source and independently governed merge guard:** The saved complete original model's *historical prefix* count and per-index contract are one versioned code-owned ABI manifest, not repeated literal `222` switches. Import the named historical prefix value in true compatibility checks, derive the **current** vocabulary size from its admitted graph/catalog at use sites, and never use the prefix as a future maximum. Treat archived evidence and unrelated numeric seeds separately. Run the external-expected-fingerprint ABI guard on every private feature proposal (advisory until protected branch rules are available); do not change its validator, expected fingerprint and governing release in one unreviewed patch. The user requires subagent audit of the numeric occurrence inventory before broad refactoring and actual Grade A/B diagnostic proof before any Grade C admission. See ADR-030 and protected issue #336.

**ADR-031: fixed classroom exam and practical five-warning evidence:** Each grade enrollment holds the same source-oracled exam, rubric and graduation criteria through failures and two freshly ranked weakest-three rounds; after passing, returning to that grade starts a different exam. Exact missed questions *and gold labels* remain valid supervised lessons; no sealed pool exists, and scoring inference never receives gold. Implement S1–S5 against actual checkpoint score history and source-typed offered/delivered lesson structure without requiring every individual instructional specimen ID, comprehensive future-catalog migration or testing advanced untaught compositions. Record missing evidence as `NOT_MEASURED`; reserve specimen-level causal research for later. These warnings do not stop human training or change the evolved teacher's policy. See ADR-031, `docs/evidence/diagnostics/AB_CLASSROOM_DIAGNOSTICS_20261016.md`, issue #336 comment `6215237912`, and corrected `PM-2026-10-16-006`.

## Cardinal rules for **adding or editing** semantics, lessons, grades and tests

1. **Authority before alteration:** Read `README.md`, this `AGENTS.md`, append-only `ADR.md`, current `HANDOFF.md`, `IPR-0220` and issue #336; check source/branch, writer ownership, live saved student and protected original artifacts. Separate proposal, verified source, admitted release, executed training and actual mastery. Do not silently commit an unreviewed local experimental repair as policy.
2. **Primitives: source and identity:** Search the current official New Ithkuil **grammar and lexicon** before adding or changing a primitive; verify meaning, scope, legal form, arity, operand/result types and independent oracle. Where morphology is unproven, explicitly use a scoped typed formal adapter. The Token Atlas's original token IDs are one-to-one and immutable; approved meaning changes receive a **new version plus compatible migration**, not an in-place reinterpretation or model reset. Allocate brand-new IDs only through separately admitted append-only vocabulary growth.
3. **Primitives: propagate edits:** On creation, semantic refinement or deprecation, update the canonical versioned registry/typed AST and prerequisite/dependent graph, track source/contract hashes, regenerate **affected** lesson/probe/test families and their source witnesses, and retain old release/generator receipts for already trained checkpoints. Nonsemantic editorial edits must not silently change active rubric identity; unknown or unverified semantics remain unadmitted.
4. **Lessons: dependency admission:** Before authoring a lesson, declare its stable capability ID, grade, prerequisites with **earlier demonstrated constituent mastery**, typed output/answer modes, smallest meaningful introduction, AST composition/complexity progression, legal/illegal boundaries and source authority. Never examine untaught roots or test newly composed concepts before separately teaching/assessing their required constituents.
5. **Lessons: compile, do not hand-patch:** Compile varied constructions from the approved semantic AST/DAG and source oracle, not a private Grade-B-only generator branch or fixed Q/A bank; create direct constituents, progressive compositions, decomposition/reconstruction, contrasts, inverses/metamorphic and negative cases **where semantically lawful**. Draw fresh seeded specimens per instructional visit **and optimizer step**; previous exam errors remain eligible to teach, never permanently embargoed.
6. **Lessons: coverage obligations:** Compute relevant predecessor and cross-grade semantic edges and source-valid construction families; cover *all required* types, truth cases, source-defined exceptional/boundary forms and appropriate answer modes (not just binary where a source supports numeric/native tokens). Report exact missing or unsupported edges as **coverage debt** and block only the unjustified new admission, not unrelated authorized progress. Random variety or a large item count does not prove coverage.
7. **Teaching feedback: weakness owns WHAT, policy owns HOW (ADR-083):** Persist unresolved source-verified exam mistakes across changing sampled cohorts, with semantic deduplication, correction evidence, fair exposure and visible bounded-memory eviction; do not overwrite failures merely because another exam occurred. Once a weak capability is selected, its unresolved semantic misses are first-class lesson targets, not one-shot replay garnish. Reserve those targets before generic lesson material on every optimizer batch: if all active targets fit, each remains eligible every step until corrected; if they do not fit, rotate least-exposed targets first. Derive target pressure from unresolved target count and available current-capability capacity rather than a fixed percentage or magic quota. Teacher policy controls pedagogy around the target (old rehearsal, contrast, depth, LR, guidance), not whether the target appears at all. Preserve source truth, assessment-before-teaching, retention/preservation gates and human ownership of neural updates. Measure which concepts/examples actually received visits and durable subsequent improvement.

8. **Automatic mean-stability promotion (ADR-084/093, corrected by ADR-103 and the 2026-10-26 replay decision):** Enter a canonical one-pass promotion sweep only when a fresh complete assessment puts the mean accuracy of every currently introduced semantic in the active grade at **>=92%**. Freeze that current-grade score vector. Individual semantic scores may be below 90%; the guarded quantity is the grade mean. After each semantic visit, freshly rescore that semantic and replace only its entry in the frozen/running sweep vector before recomputing the grade mean. Semantics not yet revisited retain their most recent sweep score. Continue while the running mean is **>=87%**; abort only below 87%. Bind each attempted sweep to the exact current-student checkpoint SHA plus exact introduced scope. A failed attempt cannot be re-armed by cohort flux alone; a retained student change or semantic-scope change may re-arm it. If every introduced semantic completes without crossing the 87% failure floor, open exactly one next tier automatically. Carry every still-imperfect semantic forward as explicit mastery debt. Never treat progression as championship, perfect mastery, debt clearance or permission to falsify historical scores.

9. **Teacher vNext replay authority (2026-10-26):** The post-#324 successor Factory carries the bounded Teacher vNext canary and calibrated multi-fidelity shadow ladder proven on `349-bouta-tree-fitty`. Every fourth eligible candidate may use an evidence-backed vNext selection only when compatible support is sufficient and the selected policy remains inside the current executable active strategy set; otherwise fall back to the inherited/current selector. Novel learned parameter proposals remain shadow-only. The 2/4/8/16 shadow ladder uses the calibrated step-8 stopping horizon and remains evidence unless a separate explicit authority change enables early termination. #333 remains canonical proposal -> delivery -> outcome -> cost evidence; do not restore a competing historical proposal/outcome store. These replayed policies apply to the successor Factory only and must not mutate the frozen #324 v3 control.
10. **Teacher owns its learned policy:** Preserve teacher state, observations and policy selections. Supply verified instructional choices and evidence for prerequisite reinforcement; **do not force a fixed old/new lesson mix or override its selected strategy** on an assistant hypothesis. The recent up-to-25% Grade B prerequisite sample is an **unratified local experiment**, not a reusable requirement. Each active maxed capability role may advise across grades with one direct source-gold-gated vote; non-max roles contribute zero direct role votes. Frozen grade soups remain a separate aggregate voice with the existing same-grade base vote and foreign-grade dilution. All direct and soup advice remains teacher-`distill`-scaled and bounded; it never changes oracle gold, independent exams, scheduler selection, the causal student identity, or AdamW.
11. **Grades: sweep imperfect grades before global recovery:** Admit roughly 6–9 similarly leveled prerequisite-compatible capabilities. Run the complete currently introduced `MAIN` sequence for **every currently imperfect eligible admitted grade** in canonical wrapped order, skipping grades already at 100% on fresh cumulative evidence. Only after that ordinary imperfect-grade sweep is exhausted may the scheduler run at most **two fresh weakest-three rounds over the complete eligible cumulative pool**, allowing consecutive selection of a still-weak skill. **C-frontier exception (ADR-094):** when B is explicitly nongating debt and C owns progression, do not inject one weakest B capability into C recovery. Count completed grade-level training queues instead. After no more than four completed non-B turns, enter B `MAIN` for one canonical pass over every currently imperfect admitted B capability, then reset the B cadence and require four more non-B turns before another B pass. This guarantees real B practice without letting B monopolize the run. Grade B remains developmental learning territory: no repeated-recovery failure, low score, or no-progress window for B may quarantine it or actuate a STAGNATION_REVIEW_REQUIRED exit. Preserve B diagnostic evidence and mastery debt; C and other grades retain independent containment (ADR-086). After round two, reset the ordinary sweep and resume progression. Record and restore each grade's stage frontier, and do not score unintroduced future-stage concepts while teaching another grade. **Clean graduation/mastery** still requires 100% on the current grade at one entire FP32 student+own AdamW plus the ordered A→...→current Billy Madison qualification and cumulative same-checkpoint 100%. The replayed progression path separately uses 92% entry / 87% continuation hysteresis while carrying every imperfect semantic as mastery debt; that path does not mint a champion, clear debt or claim graduation. Preserve grade champs, grade-vote multiplicity and original checkpoints.
12. **Tests: common rules, independent scoring:** Generate instruction and examination from the **same independently source-oracled semantic rules** with versioned seeds, AST/source/generator digests and corpus hashes. Sample varied positive/negative/invalid/contrastive witnesses consistent with source laws and support the capability's legitimate answer types; avoid artificial label balance that conceals semantics. No permanent sealed teaching exclusions. Never expose gold to inference; score every admitted capability on one intact checkpoint with its own AdamW, and compare challengers to incumbents only on **the identical sampled cohort** for promotion.
13. **Diagnostics: activate the user's five warnings:** Continuously observe (i) repetitive model-answer collapse separate from gold distribution; (ii) chance/lag with actual class baselines; (iii) transient reward vs durable learning; (iv) disconnected semantics/prerequisite defects; (v) unnecessarily complicated introductions. Require negative-control fixtures, per-capability/grade evidence, causal alternatives, teacher-readable diagnosis, observable follow-up and explicit `NOT MEASURED` when unknown. Merely rendering a dashboard or passing synthetic tests is **not** detection, intervention or neural mastery.
14. **Generated release and mutation-proof:** Property-test addition **and semantic editing** of a synthetic primitive, introduction of an unfamiliar dependent grade, inverse/counterexample coverage, typed result changes, intentionally missing sources/oracles, changing cohorts, mistake-queue starvation, and allowed temporary forgetting. Check affected-family regeneration, valid old receipt readback, no secret holdout, adaptive-teacher noninterference and source fail-closed behavior before any human-run recommendation.
15. **Custody and operator boundary:** Preserve the complete FP32 student, *its matching native AdamW*, teacher history, 222 historical token IDs, immutable grades/source manifests, student/grade champions, 100 GiB disk reserve and exact recovered state. Agents may run source/dry-run/disposable-model checks, **never** invoke actual `--human-run`, overwrite original checkpoints or change the human trainer's policy merely to quiet an alarm. Only the human starts or resumes real neural updates.
16. **Proof and handoff:** For every primitive/lesson/grade/test edit record source→typed AST/prerequisite→generated teaching/tests→coverage matrix→independent gold proof→five-signal telemetry→actual versioned release and disposable tests. Report what was observed versus unverified, track blockers without inventing authority, file BIOS incidents immediately, keep issue #336 and exact Git/issue/PM refs in **every handoff**, and do not claim future-proofing or real learning from green mock tests.

## Existing project invariants (still binding)

- **Foundational, not optional:** every Bilqis token ID has exactly one human-interpretable pasigraphy catalog identity/function, and every cataloged token maps back to that one ID. Keep **every** token accounted for in the native Bilqis Curriculum Registry sheet until at least the end of New Ithkuil training. Fail preflight on missing, duplicate, swapped, untraceable or silently altered tokens. Syntax/grammar operators count as interpretable semantic functions, not opaque filler. Historical IDs are frozen; historic descriptor coverage does not claim New Ithkuil conformance.
- **Living-ledger correction:** a new spreadsheet description cannot invalidate, restart or silently rename a trained checkpoint. Each model retains its pinned semantic contract. Stage revisions in `Token Mapping Reviews`; review and approve under recorded authority before adopting a new version. The user delegated the current 222-token semantic crosswalk adjudication to the assistant in protected IPR-0220 comment `6187168824`; this does not approve speculative equivalence, certified NI morphology, new training, or historical identity changes. Only block *new* admissions on unresolved identity conflicts; a meaning change needs new instruction. `registry_versions` governs runtime reconciliation; the strict historical atlas comparator is not a training gate.
- **Immediate language-conformance gate:** the current `Token Mapping Reviews!A1:P223` carries delegated source-grounded *scoped semantic* dispositions for all 222 tokens in `mapping-review/20261015-d`, preserving vC in `Token Mapping Reviews vC Snapshot`. This does **not** certify 222 exact NI lexemes or legal wordforms. Before new lessons, grade-rubric release, or neural-training launch, compile and independently verify NI grammar/case/morphology for composable forms and retain typed formal adapters where NI lacks a proven operation. The existing student remains on `legacy-source/v1`. See ADR-010 and `docs/provenance/NI_SEMANTIC_ADJUDICATION_VD_20261015.md`.
- **Original scoped user override (ADR-013), superseded in examination method by ADR-022:** the user accepted the six source-defined Grade A predicates and the historical 144+72 evidence inventory, which remains immutable. The subsequent user directive removes permanent question embargoes for live instruction and assessment: newly sampled oracle-checked constructions of those same six typed operations are teachable after each assessment. The new assessment still requires all 72 sampled items at one intact checkpoint and a 100% result. This does not certify New Ithkuil morphology or authorize new roots or grades. Only a human may invoke `--human-run` and update the real model.
- **ADR-025 approved typed Grade B:** The subsequent user instructed the agent to continue authoring and integrating the next grade without further human-stage approval. Only the six existing source-typed Boolean operators over learned Grade A identity/parent/link operands are admitted as B; these preserve the legacy token graph, exact A course seal, no invented roots and no uncertified NI morphology. The new cumulative A+B grade rubric has 12 sampled oracle-confirmed binary items per capability, 144 total at one complete checkpoint. Full source-bound witness construction is mandatory before migration. On human `--resume` after an A champion is verified, automatically extend the existing run to B, preserving model+own AdamW, teacher, previous grades, immutable states and same-cohort frontier custody. An unfinished A run must be resumable even if B source qualification fails. Source code/test changes do not give agents permission to initiate real student neural updates. See `docs/evidence/grades/GRADE_B_LIVE_CONSTRUCTORS_20261015.md`.
- **ADR-025 event-lineage safety:** Source-verified initialization, A→B admission, provisional training visits, same-cohort exam and capability-best publication use an immutable generation-bound event outbox written with the state; replay missing JSONL entries by verified ID/payload on human resume rather than repeating model/AdamW updates. A lesson selected from another grade's weakest-three recovery credits the grade of the *capability taught* in teacher stats, while retaining the separately reported active scheduler grade. Grade-best events credit the completed exam grade, even after an immediate B→A replay transition.
- **ADR-081 state data plane:** Current and per-generation School50 state files are tiny immutable Merkle-DAG pointers backed by the workstation-shared SQLite/WAL data plane. Do not reintroduce full-copy JSON generations or recursively embed archival history into the live receipt. Large logical fields must use content-addressed objects/shards; unchanged fields share references. Immutable model/soup SHA proofs may be reused only through the stat-bound data-plane verification cache; any file identity/stat change forces rehash. `BILQIS_DATA_PLANE` explicitly overrides the durable workstation database location.
- **ADR-082 hot/cold runtime boundary:** Treat the data plane as an addressable database rather than eagerly reconstructing the whole logical receipt for narrow work. Prefer field-selective reads. Subshard high-churn teacher-miss data below capability granularity while retaining compatibility with old DAG nodes. `events.jsonl` remains append-only evidence, while hot event-ID membership/payload/count queries use the shared SQLite tail index instead of rescanning the ledger. Active bundles/soups/cohorts belong in the hot run namespace; historical evidence may live in shared content-addressed archival storage and be hydrated on demand, but logical pointers/digests and exact historical readback must remain valid.
- **ADR-136 portable artifact authority:** Filesystem paths are locators, never semantic identities or authority. Accepted BAMF lineage and other portable receipts must bind immutable content/source identities and reproduce after custody is copied to a different host or root. Resolution may use machine-local paths below the authority boundary, but callers may not authenticate historical state by supplying a pathname. Re-resolved bytes must satisfy the same registered source pins, content digests and exact identity checks before use.
- **ADR-026 historical repair, superseded by ADR-031:** Grade B source-oracled lessons and live exams share constructors; neither may create a permanent item embargo. Preserve earlier still-wrong, source-verified examples across exams until a direct post-visit or cohort recheck establishes correction. Rerank the full eligible pool after each weakest-three round. The earlier **unratified** 24-item/capability truncation and automatic up-to-25% Grade B prerequisite injection were retired from the active trainer during the classroom merge. Current replay is exposure-aware and derives capacity from the actual batch classes and remaining visit steps; the inherited teacher policy still selects the lesson strategy. Actual human-run B acquisition and A recovery remain unproven. See ADR-031, `docs/evidence/diagnostics/AB_CLASSROOM_DIAGNOSTICS_20261016.md`, and historical `docs/evidence/diagnostics/GRADE_B_REGRESSION_FORENSICS_20261016.md`.
- Search the current official `ithkuil.net` grammar **and** lexicon before suggesting any novel semantic primitive. Verify scope, stems, and composition, not superficial word similarity. Entif/Rosetta or Metacognitive Atlas novelty remains a research hypothesis until NI coverage is exhausted.
- **Curriculum is a New Ithkuil specification conformance suite:** compose meanings from registered tokens using source-attested lexicon and grammar rules; test both legal and illegal constructions, decomposition and reconstruction, contrastive cases, independently mastered prerequisites and retention. Do not invent NI equivalents or substitute the nearest English analogy. External conceptual roots may be curated; the dialect constraint can relax only after the NI regimen completion gate, not before.
- **Current D–O curriculum-research authority (2026-10-20):** For the next twelve provisional grades, mine the tracked New Ithkuil Lexicon Chapter 1 and Chapter 2 source corpus broadly and independently of its printed root order. Treat the current `Grade Tranches` ordering as non-authoritative while retaining its high-value semantic/source/context evidence. Do not stop at 144 semantics: preserve a substantially larger near-term candidate pool plus explicit deferrals so later researchers can reproduce inclusion, rejection and reorder decisions. A root is not automatically one Bilqis capability; preserve material Stem and BSC/CTE/CSV/OBJ distinctions and identify hidden composition/prerequisite burden before assigning a capability. Grade candidates by the smallest justified semantic slope from mastered A/B/C, independent witnessability, answer-modality burden, compositional reuse and future unlock value. Keep every grade/rank/teaching-order field out of canonical source CSVs; curriculum placement belongs in a separate worksheet/curriculum-definition/issue layer. D–O assignments and any future protected issues are **PROPOSED / NOT ADMITTED** until the normal semantic-identity and factory-release gates admit them, and later evidence may reorder earlier proposals. Source-corpus integration must retain examples, exclusions, scope notes, caveats and reproducible source loci rather than flattening lexicon prose to one-word English glosses.
- Start by reading `README.md`, this file, `ADR.md`, `HANDOFF.md` and current issue/branch. Before editing shared root docs, reread each, apply narrow concurrent-safe updates, and inspect the diff. `ADR.md` is append-only; `HANDOFF.md` is current-state only.
- Keep historical FP32 student, its original AdamW, frozen semantic graph/token IDs, old worktrees and candidate archives unchanged. New Ithkuil semantics are versioned mappings/new nodes, **never rewrites of old primitives**.
- Old `G##` and `B##` are archived capability aliases. New grades are A, B, C... with approximately 6–9 similar-level capabilities each. Grade mastery requires one intact same-checkpoint model+optimizer at 100% on its complete grade rubric.
- Complete an ordinary full introduced-capability pass for each currently imperfect eligible grade before global recovery. Once that sweep is exhausted, run no more than two freshly ranked weakest-three recovery rounds across the complete eligible cumulative pool, then reset the sweep and resume ordinary grade progression. Do not insert two recovery rounds after every individual grade, do not collapse MAIN back to one active letter while another imperfect grade is due, and do not schedule a third weakest-three round before another ordinary sweep. Under ADR-024/061, ordered graduation/revalidation targets and the cumulative same-checkpoint 100% gate remain unchanged. An earlier champion checkpoint casts one vote per represented grade; during a backward replay, all already-graduated grade champions are eligible teachers regardless of letter. Soups are frozen teachers, not trainable students.
- **Flash mode does not suspend the grade state machine (ADR-060/061):** at each scheduled assessment boundary it still runs a fresh cumulative routine scheduler assessment, follows the same complete imperfect-grade sweep before the two global recovery rounds, and may then resume the next sweep. Flash may skip candidate/incumbent championship competition, title/soup movement and promotion qualification, but it may not reopen one grade indefinitely. If scheduler-only evidence finds the whole admitted curriculum perfect, leave the real `ASSESS_*` debt in place and require a non-flash authoritative qualification exam. Dashboard text must distinguish actual title movement, denied/no movement, capability-best observations and mere fresh samples; never label a fresh sample `CHAMPION SAVED` unless an actual title movement receipt supports that claim.
- Never test untaught roots or compose tests before separate prerequisite mastery in earlier grades. Teach appropriate binary and finite typed answers. Source attest all lessons and independent oracles; if evidence is absent, block advancement rather than guessing.
- Admit no grade examination with unapproved source tokens, semantic forms, or world sizes. Live Grade A uses the same six user-accepted direct predicates with reproducible fresh, balanced 72-item cohorts drawn from source-checked constructors. Source/oracle hashes, 222-token graph prefix, complete FP32 student and matching AdamW remain mandatory. The frozen 144+72 historical records are read-only evidence and do not govern the live question sample.
- Vocabulary grows by append-only, separately attested token allocations. The 222-token parent has no fixed semantic ceiling. The 330 Semantic Bridges records are research candidates, not 330 approved new tokens or learned roots. Support atomic, composite and hybrid meanings (including lexicalized concepts); do not collapse roots, syntax, tokens, lessons or mastered skills into one count.
- Agent-run dry-runs, tests, read-only parity, dashboard/status, and safe fixture experiments are authorized. **No agent-run neural optimizer updates to actual Bilqis students.** The experimental trainer requires a deliberate `--human-run` in the human's terminal; only the operator may initiate/continue the actual model, with exclusive lock, source verification and immutable own-AdamW checkpoints.
- Reuse six-panel School50 and stable npm commands. Protect disk headroom; no recursive cleanup of `~/Code`, no archive deletion, no model binaries in Git. Backup only explicit source paths with external readback evidence.
- **Forward-compatible School50 metrics (ADR-016):** Keep the six named panels but make their event/measurement schema grade-neutral. Preserve step, model, rubric, partition and teacher-source provenance; display first/latest/best, gains and cross-grade retention without mixing checkpoints. Optional independent sentinels, semantic construction probes and teacher-only soup metrics must be real and source-bound before presenting values; missing dimensions are NOT MEASURED or OFF, not manufactured from source-training rewards. Dashboard code cannot mutate the actively running human student or teacher. See `docs/architecture/SCHOOL50_TELEMETRY_V1_20261015.md`.
- **Dashboard presentation contract:** Keep the compact BILQIS cockpit as a two-row heading/value instrument and treat display space as a salience budget, not a telemetry dump. Render each fact in one best owner: global run/cumulative coordinates in the cockpit, curriculum-local evidence in CURRICULUM. Preserve underlying telemetry when removing duplicated or dead presentation; do not restore retired panels/footer merely to repeat information available elsewhere.
- **Resource stops (ADR-017):** Disk free bytes, protective reserve, and estimated next complete checkpoint are an explicit telemetry contract. Report `DISK_RESERVE_REACHED` normally and durably rather than letting the guard silently abort an otherwise healthy student. Never reduce the 100 GiB default reserve or delete saved complete model/own-AdamW bundles to prolong a run without the user's separately scoped decision.
- **Capability bests (ADR-018):** The user now authorizes real-time supersession of unreferenced candidate bundles. The best score for each capability can be below perfect, and one whole checkpoint can own several best slots. Keep current student, grade champions, capability bests and their AdamW intact. Score before archiving; do not retain every visit. A bounded working recovery snapshot is separate from a candidate champion. Prune only after durable pointer promotion and verified custody.
- **AST-first curriculum scaling (ADR-014):** Compile the native Registry's typed semantics, prerequisites, sources, states and grade relationships into deterministic construction and probe plans. Fix recurring *classes* of narrow lessons via reusable mathematical/grammar constructors, counterexamples, metamorphic contrasts and out-of-sample tests rather than hand-patching individual questions. Keep historical alias, research seed, draft, source-attested and admitted-release states distinct; a compiled/proposed lesson never alone authorizes neural updates or alters the frozen Grade A exam. `npm run curriculum:plan` is neural-inert and reads a connector-refreshed snapshot.
- **MANDATORY predecessor pedagogical parity (ADR-019, updated by ADR-022):** Before designing any new curriculum, answer-caste adapter, exam or teacher scheduler, read the original PyTorch School50 code and v10-v16 repair ledger. Teach typed answers and contrasts where the actual admitted semantic ABI permits. The historical train/development/sealed partitions are preserved only as versioned evidence; live generated Grade A questions have no permanent embargo. Research-only numeric direct answers and `npm run curriculum:parity` do not by themselves authorize their admission into Grade A.
- **Native semantic-token output (ADR-020):** A source-attested direct answer must train both its typed answer and its actual catalog token ID under a full-vocabulary tied-embedding output head. Preserve TRUE/FALSE contrasts as additional supervised views. The current 4-way numeric head is not the output ceiling; reject stale heads after append-only vocabulary growth. This research bridge is not a released multi-token decoder or authorization to train the real student.
- **Bounded integer semantics and generated tests (ADR-021):** `BILQIS_INTEGER_MAX` is the single active integer *teaching/test-input* bound (default 3; source-attested through 100), not a token-vocabulary limit. Build lesson and test specimens from typed AST operators and verified mathematical/Boolean laws, not one-off example inventories. Training samples may vary by seed each pass; generated test suites must remain fixed until explicitly rebuilt with `npm run curriculum:tests -- --regenerate-tests=type:integer`. The type-dependency registry rebuilds all Number-dependent suites (including Boolean results and inverse laws) but never unrelated suites or the frozen historical Grade A rubric. Reject stale scope/artifacts during assessment; see the generated-test contract doc.
- Run tests, inspect diffs, confirm writer coordination and push only a private feature branch with remote readback. Do not force-push, mutate main, or publish protected algorithms.
