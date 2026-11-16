# BAMF-0.2 operator observation commands

Status: **C11.3 read-only cockpit/runbook plus C16.1a create/resume and C16.3
persistent BAMF dispatch are implemented**. `--human-run --resume` is the explicit
human start boundary for an accepted lineage. A staged lineage enters the BAMF-native
operator directly. An accepted `atlas-release` lineage first runs the restart-safe
C07 flywheel; FIXED_POINT, WAITING_FOR_EVIDENCE, IMPLEMENTATION_UNCOVERED and
LEASE_REQUIRED preserve already-authorized learning and continue into the operator,
while ambiguous HELD remains a hard stop. This document never authorizes an agent to
start the durable student on the human's behalf. Full C11.3 closure still requires
accepted production qualification of the operator-status observation producer plus
the current C07/C10 parent receipts described below.

## Read-only cockpit

Use the exact run directory. The existing watcher reads saved state and complete
journal records; it does not acquire the trainer lock or update the student,
optimizer, teacher, admission lease or journal.

```sh
npm run dashboard -- --run-dir /absolute/path/to/run --once
npm run dashboard -- --run-dir /absolute/path/to/run --once --atlas-details
npm run dashboard -- --run-dir /absolute/path/to/run --atlas-details
```

The first two commands render one snapshot. The third follows the journal until
interrupted. `--atlas-details` expands the BAMF observation panel when a compatible
observation is present. It does not make a historical run a BAMF run. A fresh
subprocess test exercises the expanded snapshot against a disposable journal and
checks its bytes, modification time and directory contents remain unchanged.

The two-row main cockpit keeps its existing metric owners. The additional Atlas
panel shows the complete declared source-eligible denominator, source-held and
implementation-uncovered counts, ready/staged counts, active concepts and banks.
Expansion shows admitted/exposed/qualified counts, atoms per frame, fallback,
expansion and motif-hit fractions, plasticity mode, memory use/budget, and exact
source/model/evaluator/rights/census digests. A source-qualified implementation
hole remains in the denominator. Source-held concepts remain a separate count.
The status counts form a disjoint partition of the declared eligible census.

The learning line reads existing SchoolTelemetry GREW and retained-step counters.
Ten retained steps with no measured capability change display GREW +0. Staging,
retention, measured gain, debt, perfect mastery and transfer remain separate.
Missing debt, mastery and transfer measurements explicitly say NOT MEASURED.
This reader does not schedule fresh generalization, confer promotion authority,
or introduce a grade-specific teaching policy.

## Observation receipt

The reader accepts `bilqis.bamf.operator-status/v1` under saved-state key
`bamf_operator_status`, or an append-only journal event named
`BAMF_OPERATOR_STATUS_OBSERVED` with a `receipt` object. This remains a presentation
boundary: no accepted production owner currently emits this exact status schema.
B13/A12/C05 and C10 now expose their own accepted custody/evaluation/projection
receipts, but the cockpit must not synthesize an operator-status receipt from them
without an explicit producer contract. The reader validates schema, complete
nonnegative coverage counts, source/model/evaluator/rights/census SHA256 syntax and
finite observations before replacing the last valid view.
A malformed journal observation leaves that view intact and the watcher reports
the failure through its existing log channel.

Structural validation does not verify the referenced source release, producer,
checkpoint, evaluator or rights artifact. Actual source/custody owners must issue
and qualify these observations before production use. The current tests use
explicit synthetic receipts and do not establish producer acceptance or learning;
the presence of integrated B13/A12/C05/C10 owners does not change that boundary.

## Preflight, launch and resume boundary

C16.1a/#542 owns the human-facing persistent v2 lifecycle over the generation-zero
boundary documented in `BAMF_0_2_FIRST_STUDENT.md`. Run these commands from the
repository root in an environment with the project's Python dependencies installed.
A fresh dry-run requires the complete foundation identity but does not create the
target directory:

```sh
npm run train -- --dry-run --model-topology configs/models/bamf-0.2.json \
  --source-run-dir /absolute/path/to/accepted-source-run \
  --atlas-release-manifest /absolute/path/to/manifest.json \
  --run-dir /absolute/path/to/new-bamf-run --run-id example-run --run-seed 543 \
  --learning-rate 0.0007 --adam-beta1 0.88 --adam-beta2 0.97 \
  --adam-eps 1e-7 --weight-decay 0.03 --source-prefetch-workers 0
```

Expected: exit **0** with JSON schema `bilqis.bamf.operator-lifecycle/v1`, result
`READY_TO_CREATE`, `ready_for_training: false`, `neural_updates: 0`, and the exact
run identity, topology, source-qualified Atlas identity, optimizer hyperparameters,
and prefetch setting. Dry-run replays the source/Factory and Atlas foundation
authority but publishes no generation and performs no optimizer update.

The default admission policy is `staged`. An actual create requires the same
foundation fields plus the explicit human gate:

```sh
npm run train -- --human-run --model-topology configs/models/bamf-0.2.json \
  --source-run-dir /absolute/path/to/accepted-source-run \
  --atlas-release-manifest /absolute/path/to/manifest.json \
  --run-dir /absolute/path/to/new-bamf-run --run-id example-run --run-seed 543 \
  --learning-rate 0.0007 --adam-beta1 0.88 --adam-beta2 0.97 \
  --adam-eps 1e-7 --weight-decay 0.03
```

This publishes B13 generation zero at optimizer step `0` and returns `CREATED`; it
still does not enter the learner. The Atlas manifest must be a canonical,
source-pinned release manifest. Normal creation uses an absent or empty target. An
exact fresh-create retry may converge the narrowly defined durable B13 pre-seal/sealed
genesis evidence; arbitrary BAMF or legacy custody is never overwritten or coerced.

To enroll the new lineage in the C07 `atlas-release` admission policy, add both the
explicit policy and a versioned lease request:

```sh
npm run train -- --human-run --model-topology configs/models/bamf-0.2.json \
  --source-run-dir /absolute/path/to/accepted-source-run \
  --admission-policy atlas-release --atlas-admission-scope /absolute/path/to/enrollment-request.json \
  --atlas-release-manifest /absolute/path/to/manifest.json \
  --run-dir /absolute/path/to/new-bamf-run --run-id example-run --run-seed 543 \
  --learning-rate 0.0007 --adam-beta1 0.88 --adam-beta2 0.97 \
  --adam-eps 1e-7 --weight-decay 0.03
```

The scope file is request data, not authority. The lifecycle validates its known
lineage/topology/Atlas fields before publication, publishes generation zero through
B13, then obtains an opaque C09 capability from `AcceptedRuntimeHost` and asks the
C07 owner to persist and read back the exact lease against accepted run custody.
The CLI never receives or constructs a raw source-authority registry. Generation-zero
publication and C07 persistence remain sequential existing transactions: if the
post-genesis lease check fails, no `atlas-release` current reference is installed;
the lawful generation-zero run remains staged rather than being counterfeited as
admitted.

Ordinary resume derives saved settings from accepted custody and performs no neural update:

```sh
npm run train -- --dry-run --resume --run-dir /absolute/path/to/bamf-run
```

Expected: `READY_TO_RESUME` with the saved run id/seed, topology, Atlas identity,
optimizer hyperparameters, and effective admission policy. Explicit topology,
run-id, seed, optimizer, Atlas-manifest, or policy overrides must equal the saved
values or fail before writes. Ordinary resume takes no scope. Historical v1 state
is not coerced to v2.

If the target has BAMF-v2 lifecycle evidence but no accepted pointer, `--resume`
rejects `BAMF_OPERATOR_INTERRUPTED_GENESIS_REQUIRES_CREATE_RETRY` without mutating
recovery state. Repeat the original fresh create command with the same identity and
optimizer inputs; B13 performs the only authorized exact-genesis recovery.

A staged accepted run may complete its **first** C07 v2 enrollment later, still
without entering the learner:

```sh
npm run train -- --human-run --resume --run-dir /absolute/path/to/bamf-run \
  --admission-policy atlas-release \
  --atlas-admission-scope /absolute/path/to/enrollment-request.json
```

Expected: `ENROLLED`, `ready_for_training: false`, and `neural_updates: 0`. The
scope remains non-authoritative request data; C07 derives the persisted lease from
accepted B13/C09 custody. A second unequal request is an explicit-renewal case and
is rejected by this first-enrollment surface.

Existing trainer help can also be inspected without a neural update:

```sh
npm run train -- --help
```

### Persistent human start and resource custody controls

The real persistent start command is the same resume shape proven by C16.3. Keep the
protected disk reserve at its production default and bound the first operational
session explicitly when desired:

```sh
npm run train -- --human-run --resume --run-dir /absolute/path/to/bamf-run \
  --minutes 90 --reserve-gib 100 --max-visits 1
```

`--reserve-gib` defaults to `100`; do not lower it merely to make a witness pass.
`--minutes` defaults to `90` and is the wall-clock session bound consumed by the
persistent BAMF operator.
`--max-visits 1` is a bounded first-start choice, not a permanent policy. Omitting
`--max-visits` leaves the session bounded by the human-selected time budget and disk
reserve. On an accepted `atlas-release` lineage the command first runs the authorized
C07 admission flywheel. If that flywheel returns a safe non-integrity terminal, the
same command then cold-loads the current accepted generation into the C16.3 BAMF
operator. An ambiguous `HELD` status stops before learning. Use `--dry-run --resume`
when only inspection is intended.

The parser still accepts `--source-prefetch-workers {0,1,2}` for compatibility with
the historical operator path. The C16.3 BAMF-native operator does **not** start that
prefetch pool: C03.4 supplies the exact source-qualified priority offer and rows to
the candidate owner, so the native persistent path currently uses zero independent
prefetch workers. Do not describe that flag as an active BAMF resource knob until a
future owner explicitly composes it into the native operator.

The human start may perform retained optimizer work. It does not authorize new
source rights, a lease renewal or grade promotion by fiat; those remain with their
existing owners. C07 admission reloads accepted custody after adoption rather than
reusing stale in-memory learner/optimizer state, and C16.3 owns only serialized
composition of the existing teacher/candidate/C05/B13 owners.

`--issue-349-experiment-root` is a separate bounded experiment-custody control and
is not required for an ordinary BAMF production lineage. Do not substitute it for
B13/C07 custody or the 100 GiB reserve.

C11.2's bounded reader remains available for historical inspection. The persistent
v2 lifecycle above consumes accepted B13/C09/C07 custody and validates saved
topology/admission settings. C16.3 then enters the BAMF-native operator only from the
explicit human resume boundary. The existing 100 GiB reserve remains unchanged and
is not weakened by these commands.

The resource/rubric panel describes current Factory assessment as fresh routine,
fixed promotion and inactive generalization. Historical rubric descriptions are
labeled `Historical policy (lineage only)`; they do not select BAMF scheduling or
assessment. The launch/resume command forms, generation-zero custody, saved-policy
validation and C07 enrollment/flywheel routing are now implemented. C11.3/#524 may
still display candidate/source/delivery/debt/promotion/retention/transfer evidence
only when an accepted producer supplies it; activity or grade labels never fabricate
those observations.


## Separate operator evidence

The optional `evidence` mapping on `bilqis.bamf.operator-status/v1` provides a
read-only observation projection. Old records without it remain readable.
`--once --atlas-details` appends a complete observation report outside the fixed
terminal viewport. Redirect or scroll this snapshot to inspect every row and full
digest, even at 80x24 or with many debt/policy rows. The followed live panel remains
viewport-limited and points to that complete snapshot command. The report shows
candidate and parent SHA-256 identities, the delivered-work
receipt digest and actual delivered row count, grade debt, capability debt,
promotion-attempt count, whole-school fresh retention and learned-transfer counts
on separate lines. Each score has its own exact source and rubric digest lines.
These observations do not replace the existing retained-step or GREW owners.

The wire keys are `candidate_sha256`, `parent_sha256`, `delivered_work_sha256`,
`delivered_rows`, `grade_debt`, `capability_debt`, `promotion_attempts`,
`whole_school_fresh_retention`, `learned_transfer` and `historical_policies`.
Debt values are mappings from display labels to nonnegative counts; the reader
sorts labels for display and never gives a grade scheduling authority. Score
records contain exactly `correct`, `total`, `source_sha256` and `rubric_sha256`.
Missing observations display NOT MEASURED. Measured empty debt displays none.
Zero-total scores display NOT MEASURED and retain their source/rubric identities;
zero counts remain zero. A measured debt collection does not imply that an absent
sibling collection was measured. Historical policies are explicitly lineage only.

Labels accept 1..96 printable Unicode code points without controls or surrogates.
The existing terminal renderer uses ASCII. This panel preserves Unicode labels as
JSON Unicode escapes rather than collapsing distinct labels into question marks.
Frozen records detach the displayed view from mutable incoming mappings.
Malformed evidence rejects the complete incoming observation before replacing the
previous valid view. The detached watcher test exercises these lines and verifies
the journal bytes, modification time and directory membership stay unchanged.

These remain structurally checked supplied observations. This reader neither
verifies producer/source/evaluator authority nor fabricates measurement from
activity, retention counts or grade labels. A learned-transfer observation is not
a newly scheduled GENERALIZATION cohort or promotion authority. Current fresh
generalization remains inactive. #522's mitigation and the B13/A12/C05 launch and
custody owners are integrated in reviewed unified; they are no longer blockers for
the command surface documented here. Final #524 turn-in still must consume the C07
parent's real-path closure receipt (#380), and C10.1/#519 remains the open
producer/source-rights/evaluator qualification seam for production projection
evidence. Until those receipts exist, this runbook intentionally reports the gap
instead of manufacturing operator evidence.
