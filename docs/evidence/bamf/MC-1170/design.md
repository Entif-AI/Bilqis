# Live observed trainer telemetry (#1170)

## Outcome and authority

Issue #1170 owns immediate Mission Control visibility before accepted generation 1.
Baseline: reviewed unified `2c8cda55d1344626bc6c6f11d9b5db5836a36604`.
This change adds observations, never retention, teacher, selection, optimizer,
publication or training authority. No real student is started by verification.
Accepted CP07 records and C03 publication remain the durable truth plane.

## Producer and lifecycle

Add `runtime/bamf_operator/telemetry.py`, a standard-library-only observer.
The human-authorized `operate_bamf` owns it inside the existing operator lock.
Each visit gets a random observation ID before custody/source preparation begins.
A context manager emits preparation, selection, training, retention, publishing,
and terminal states. Preserve the existing text progress callback verbatim.
Optional structured callbacks carry fields directly from their owning functions;
never parse text. Candidate training currently executes one logical update, so its
step horizon is 1. Publish a completed step only after the existing update returns.
Retention emits completed/total capability or cohort assessments from both foundation
and adaptive paths, including the current capability and parent/candidate role.
Completion means completed assessments, not a promise that an early rejection ran
all remaining work. Actual acceptance is reported only after publication returns.
A decision accepted before publication remains provisional/publishing.

The observer atomically replaces `trainer-observed.json` in the run directory.
It retains at most 8 visit snapshots, coalescing repeated progress within each visit.
Each snapshot has schema, observation ID, monotonically increasing revision, PID,
wall timestamp, monotonic elapsed milliseconds, accepted parent manifest digest,
visit index, capability (nullable), phase, candidate step/horizon (nullable),
retention completed/total (nullable), retention subject/role (nullable), outcome,
and measured process CPU seconds, resident bytes and disk free bytes when available.
Missing measurements stay null; C08 plans are never presented as measured RAM.
A background heartbeat updates elapsed/resources every second during long calls.
Serialize heartbeat and phase writes with one lock. Stop/join heartbeat on exit.
An exception or interruption leaves an interrupted observation, then propagates.
Telemetry filesystem failures disable that observation without changing training.
The file is disposable and never enters accepted checkpoint identity or custody.

## Control-plane projection and reconnect

Add an additive CP02 `TrainerObservation` record in `contracts/trainer.py` and
register its schema. Use explicit `posture=OBSERVED`, measured/partial RecordMeta,
parent RunRef as context only, observation ID/revision, phase/outcome and nullable
progress/resource fields. No accepted generation or retained step is synthesized.
Add it to the existing CP03 RUN family. Exclude it from every historical/as-of/
generation-bound query, including RECORD and link lookup paths. Regenerate the
checked-in schema bundle. Old schemas remain unchanged.

Add `control_plane/observed/` to read a bounded (64 KiB) atomic snapshot. Malformed,
wrong-run or unknown-parent observations are ignored independently of accepted
projection. Match the parent digest to authenticated history; old accepted parents
remain valid context for terminal observations after publication. Mark a nonterminal
snapshot disconnected if its process is gone or its heartbeat is older than 10s.
Do not turn process liveness into accepted-state authority.

`native_query_catalog` includes these records for current queries.
`refresh_native_events` publishes changed observations through existing CP04
`run.trainer.observed` envelopes. Track at most 8 latest observation revisions per
service separately from accepted-event identities. Existing broker retention (256)
and client queues (64) remain bounded. Initial/reconnected current queries recover
latest posture even after service restart or cursor eviction. The existing 0.25s
subscription refresh sees atomic snapshots; no terminal text is read.

## Home and current work

Use the RUN query and existing subscription. Refresh RUN on the new event; after
checkpoint/run acceptance refresh the affected Home families so durable counts
advance once from accepted records. Observations never increment retained metrics.
Show latest current observation in Current Work, including observed badge, phase,
capability, candidate step/horizon, retention progress/subject, elapsed and measured
resource values. Keep accepted generation and optimizer step visibly separate.
Rejected/held/interrupted visits remain observed history without accepted advance.
Historical views suppress observations even if a faulty source supplies them.
Disconnected posture says disconnected/last observed rather than active progress.
Guard asynchronous loads by activation epoch so old live responses cannot populate
historical/other-run contexts. Reconnect refreshes current pages before resubscription.

## Verification and stop condition

Use red/green focused tests for atomic bounded producer snapshots, heartbeat,
exception/publication lifecycle, real optional callback propagation, retention early
exit/progress, malformed/wrong-parent input, current-vs-historical catalog selection,
CP04 reconnect/replay/coalescing, and Home active/accepted/rejected/held/disconnected/
historical states. Exercise the real session coordinator with disposable mocked
owners, never start a student. Run existing affected owner tests and renderer tests.
Use static gates before any expensive execution. Review design with pinned EGM
`b3a35956759bf7f024af2ff061b2e0b44b438e4c`, reconcile drift, then required leaf and
premerge gates. Bound each launch from selected scope; detach anything plausibly
above five minutes. Open a ready PR only after required evidence is green or validly
reused. No merge or issue closure before human acceptance/merge readback.

## Precise implementation contract (review amendment)

The following details resolve the initial readiness findings and govern the prose
above. `resident_bytes` means **measured peak RSS**, named `peak_rss_bytes` in wire
records (macOS `getrusage` bytes; Linux KiB converted to bytes), never current RAM.

### Snapshot and state machine

Top-level JSON: `{schema: 'bilqis.bamf.trainer-observed/v1', visits: [...]}`.
Each visit serializes `observation_id` (UUID), `revision` (positive integer),
`process_id`, `run_id`, `parent_manifest_sha256`, `visit_index`, `observed_at`
(Unix milliseconds), `elapsed_ms`, `capability_id`, `phase`, `outcome`,
`candidate_optimizer_step`, `candidate_step`, `candidate_horizon`,
`retention_completed`, `retention_total`, `retention_subject`, `retention_role`,
`cpu_seconds`, `peak_rss_bytes`, `disk_free_bytes`. Nullable values start null.
The producer obtains run_id/current manifest_sha256 by reading bamf-state.json
before preparation; these are untrusted observational context, not authentication.
If pointer reading fails, retain a local interrupted observation with null context;
the CP reader excludes it. Once the accepted parent loads, bind its real run_id,
manifest digest and retained optimizer step; do not overwrite the accepted pointer.
The reader requires exact run_id and parent digest in authenticated_history.

Phases: PREPARING -> SELECTING -> TRAINING -> RETENTION -> PUBLISHING -> COMPLETED.
PREPARING starts before `_execution_context`. SELECTING begins before selection;
TRAINING begins after selection with capability, candidate_step=0,
candidate_horizon=1, candidate_optimizer_step=parent step. After execution returns,
step=1 and candidate optimizer step=transaction parent step+update_steps.
RETENTION begins before evaluation. PUBLISHING means accepted decision pending
publication. COMPLETED is terminal. Outcome is RUNNING until COMPLETED, then one of
ACCEPTED, REJECTED, HELD, ACTION_REQUIRED, INTERRUPTED. HELD/ACTION_REQUIRED occur
on selection hold; REJECTED only after rejection recording returns; ACCEPTED only
after accept_and_publish returns. Exceptions including publication failure produce
INTERRUPTED and propagate. Hold/rejection cannot enter PUBLISHING. Clear retention
fields on PREPARING/SELECTING/TRAINING; initialize them on RETENTION. Keep completed
training and retention figures through PUBLISHING/COMPLETED for inspection.
Each update is one lock-protected complete snapshot; heartbeat changes only
revision/time/elapsed/resources. Never overwrite phase data from a stale heartbeat.

### Progress units

`retention_completed/retention_total` count **solver assessments**, not cases.
Foundation plans 2 * len(capability_order), parent then candidate per capability.
Adaptive plans 2 * len(cohorts), parent then candidate per cohort. Emit start with
completed unchanged plus subject and role; increment only after that assessment
returns. On early exit retain completed < total and report terminal rejection.
Literal foundation two-capability assertions: start 0/4 parent A; after parent
1/4; after candidate 2/4; next parent starts 2/4. Early rejection after A stays 2/4.
Adaptive two-cohort assertions are equivalent, subject=cohort ID/kind. No per-case
fraction is claimed. This is the truthful bounded progress measure required by #1170.

### Liveness and bounded delivery

`TrainerObservation` adds `connection_state` LIVE | DISCONNECTED | FINISHED.
Terminal outcomes always FINISHED. For nonterminal snapshots evaluate PID existence
and wall-clock heartbeat age on **every** service refresh, even unchanged revision.
Missing PID, age >10 seconds, or timestamp >5 seconds in future yields DISCONNECTED.
Permission-denied PID probes mean unknown process liveness; heartbeat age still
controls. PID reuse cannot refresh a dead producer's timestamp; random observation
identity separates sessions and the 10-second expiry bounds a reused-PID window.
This is observed freshness, never proof of process or accepted identity authority.
CP04 event identity includes observation ID, revision and derived connection_state.
Track the last emitted pair per observation in an eight-entry service dictionary;
a LIVE -> DISCONNECTED change therefore emits once without file modification.
Fresh CP03 reads recompute liveness too. Broker gap behavior stays unchanged.

### Files and query contracts

1. `runtime/bamf_operator/telemetry.py` owns observer, atomic bounded snapshot,
   heartbeat and measured resources; `session.py` wires lifecycle. Optional
   `observer` keywords flow through `factory_retention_owner.py`,
   `learning/capability_retention_foundation.py` and
   `learning/capability_retention.py` to actual solver-assessment boundaries.
   Preserve existing call shape when observer is absent and all acceptance semantics.
2. `mission_control/contracts/trainer.py` owns the additive immutable record,
   numeric/null checks, posture=OBSERVED and phase/outcome/connection enums.
   `contracts/registry.py` registers it; regenerate schemas/mission-control-v1.schema.json.
3. `control_plane/observed/` validates the bounded snapshot, maps each visit to
   RecordMeta with parent RunRef, PARTIAL/MEASURED, empty receipt/evidence refs,
   source ref `trainer-observed:<observation_id>`. Record ID is
   `trainer-observed:<observation_id>:<revision>:<connection_state>`.
   `native_source.py` adds records/current snapshots and changed CP04 events;
   `event_stream.py` adds RUN_TRAINER_OBSERVED='run.trainer.observed'.
4. `mission_control/query_support.py` adds TrainerObservation to RUN and excludes
   it in matches_identity whenever mode != CURRENT OR generation/as_of/frontier_id
   is supplied. This covers RECORD, LINKS and REFERENCE via query_catalog's common
   matching function; no historical observational readback is admitted.
5. `renderer/home/home-model.mjs` selects latest observation by observed_at then
   revision (not record-ID lexical order), retains at most eight observed visits,
   and suppresses all observed data when context.mode=HISTORICAL. Preserve accepted
   counts/steps from run/episode records only. `home-controller.mjs` refreshes RUN on
   run.trainer.observed, all Home families on run/checkpoint accepted changes;
   use activation epoch and captured context on each async query completion.
   Subscribe before initial loading, then load all pages; the snapshot after
   subscription closes the initial read/subscribe race. Existing CP04 client owns
   cursor gap/reconnect; a subsequent activation reloads current RUN snapshot even
   with unchanged context. Disconnected queries/events retain last observed values
   with a disconnected badge. Do not infer freshness from operatorActive alone.
6. `home-view.mjs` plus focused `home-observed.mjs` and localized home messages show
   Current Work and bounded observed visit history alongside accepted generation/
   optimizer step. Startup with an observation renders this surface instead of the
   static first-event waiting panel. Existing accepted pulse remains accepted only.

Tests cover every clause above using deterministic clocks/PID probes and disposable
fixtures. No simulator-only proof is claimed as real optimizer or retention proof.

### Automatic recovery amendment

Source inspection found the Electron event subprocess does not automatically deliver
CP04 gaps/reconnection notifications to Home. Do not rely on an undocumented API.
Home therefore owns a **2-second bounded snapshot recovery loop** in addition to
event-driven updates. Inject schedule/cancel functions into createHomeController for
deterministic tests; cancel on deactivation/historical navigation. Serialize ticks
and coalesce concurrent refreshes. Each tick queries current RUN (including observed
posture), then compares its accepted RunContext generation/manifest with the prior
RUN page. If accepted identity changed, load all Home families. This recovers a missed
terminal observation or accepted successor even when the event process stopped and
no later event arrives. A rejected or held terminal observation needs only RUN.

On transport failure mark cached observed posture disconnected, call existing
api.connect(), resubscribe before loading all current pages, and keep retrying on
the next bounded tick if unsuccessful. Queries still include expected run_id;
responses for another run cannot become current Home posture. A single activation
epoch guards timer, reconnect, subscription and snapshot responses. Late subscriptions
are immediately unsubscribed. A fresh activation first tears down the old subscriber,
subscribes and loads snapshots, then starts the recovery loop. This changes no command
or mutation authority. Test an open Home with the terminal event discarded/evicted,
no additional events, and one recovery tick; assert terminal posture and accepted
counts recover. Also test disconnected transport then successful connect and reload,
and navigation while that reconnect is pending.
