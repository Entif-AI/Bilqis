# BAMF Admin Main Frame CP07 disposable acceptance

CP07 joins the existing CP01–CP06 surfaces without granting Admin Main Frame
ownership of a learner, optimizer, checkpoint, or source record. The acceptance
tests use only temporary directories and a fixture-scoped generation-zero C11
creation. They do not train a model or launch a production learner.

## Verified integration paths

`test_cp07_process.py` starts the Python CP01 entrypoint as a separate process,
attaches through the Unix socket with a non-Electron client, and queries a CP06
SQLite index with bounded CP03 requests. It authenticates a disposable accepted
BAMF generation, binds its exact run/generation/optimizer identities into a
partial CP02 snapshot, and adds explicitly fixture-backed capability and episode
records for cross-link traversal. The test checks current and historical/as-of
queries, crashes an independent client and the control-plane process, verifies
the run pointer remains unchanged, and reconnects to the same accepted run.
Deleting or corrupting the CP06 index makes queries fail closed without hiding
the healthy learner. Rebuilding from the same source records reproduces the
literal bounded query results. The historical domain records in this test are
fixtures, not a claim of production historical-record extraction.

`test_cp07_events.py` joins a CP03 snapshot to live CP04 delivery, sends typed
lesson, candidate, capability, and resource samples, disconnects a client, and
replays the retained interval using an exact cursor. CP06 ingests each verified
payload with its envelope and deduplicates retransmission. A lagging projection
reports `STALE`; an expired or restarted stream requires a fresh snapshot. The
publisher in this test is the explicit CP02 fixture adapter, not an automatic
learner event hook.

`test_native_source.py` exercises the production-source boundary directly. It
starts from the accepted BAMF pointer, authenticates the exact content-addressed
manifest, acceptance binding, run identity, teacher state and native outbox for
each generation, then walks the v3 parent-manifest plus parent-acceptance chain
without scanning for convenient files. Current `BAMF_C16_3_ACCEPTED` events are
validated against the persisted C03 teacher-visit identity and the portable copy
of its independently source-issued content-addressed visit receipt before they
become CP02 episode, candidate, capability and resource records. C03 still issues
the original receipt at selection time. Before B13 publishes a successor carrying
that portable receipt, B13 requires the original C03 receipt from the live source
authority and then seals both the exact successor generation authority and a
portable digest of the accepted teacher-state sidecar. Historical CP06 verifies
that teacher-state digest directly from run-local content-addressed artifacts;
the full B13 historical readers additionally verify the complete successor
generation authority. CP06 can therefore validate the copied receipt inside
accepted custody without treating the deterministic receipt marker itself as
proof of issuance and without reaching the workstation shared data plane. Generic
`BAMF_CANDIDATE_REJECTED` journal rows remain a live
projection only: they are authenticated against their deterministic event identity,
the independent data-plane rejection authority/receipt, and the C03-issued visit
receipt before CP04 delivery. Only the supported
`bilqis.bamf.c16.3-rejection/v2` contract is projected; other valid B13 rejection
schemas are authenticated and ignored. Rejections remain visible live without
pretending they advanced the learner generation, but they are deliberately excluded
from portable CP06 reconstruction because current B13 run artifacts do not carry an
independently authenticated portable rejection-decision anchor.

The portable teacher-state anchor applies to every newly accepted successor that
can carry C03 custody. Ordinary retained successors use exact acceptance schemas
v9/v10; motif-allocation successors use anchored motif schemas v11/v12. The
historical v6/v8 motif schemas remain readable by B13 for compatibility, but CP06
does not promote an unanchored historical C03 receipt into portable authority.

CP04 now refreshes that authenticated native source before subscription and on
the heartbeat path. The first successful read establishes the service-local
snapshot frontier; only later accepted/rejected native facts become live deltas.
The custody layer's deliberate pointer-change rejection is treated as a transient
read race and retried on the next heartbeat, while every other authentication
failure remains fail-closed. Native event identity is retained for the owning
candidate event and deterministic child identities are derived for its episode,
capability and resource projections. The accepted visit's native resource
observation carries the actual configured C08 memory budget, measured filesystem
usage and optimizer-step/wall-time inputs for a derived step rate. It deliberately
does not relabel C08's peak estimate as measured memory use; that field remains
`UNKNOWN`, making the CP02 resource record `PARTIAL` rather than synthetic.

CP06 also exposes `rebuild_from_bamf()`. The full CP02 tuple is materialized from
authenticated native artifacts before the existing atomic temporary-index swap,
so a failed ancestor/acceptance validation cannot destroy an already usable
projection. The acceptance witness deletes and rebuilds the disposable database,
compares the resulting historical/current records, and proves that tampering an
ancestor acceptance fails while the prior CP06 index remains readable. A dedicated
regression makes any shared-data-plane access raise during rebuild; accepted C16.3
history still reconstructs from copied run custody alone even when rejection rows
exist in the event journal.

`test_cp07_commands.py` invokes C11's accepted dry-run and human-gated genesis
code within the existing disposable test context. It admits one generation-zero
creation through CP05, uses the production command manager and durable worker
fact sequence, simulates a lost acknowledgement, reconciles the operation by ID,
and verifies terminal receipt/postcondition and its CP04 reference. A repeated
request and service restart never dispatch a second effect. The resulting
generation and optimizer step are both zero. The test uses a deterministic
fixture launcher instead of spawning a production trainer process.

## Standalone query attachment

The Python entrypoint accepts an optional `--projection-db PATH` alongside
`--run-dir` and `--socket`. The database must already be a valid CP06 index
created from accepted CP02 records. Each query reopens that index, so deletion,
corruption, and an operator-triggered rebuild are visible without restarting
the service. The option does not create a new source of truth, reconstruct
missing receipts, or silently create a fresh empty index.

Example for an existing local disposable projection:

```sh
python3 -m bilqis_mlx.control_plane \
  --run-dir /path/to/disposable-run \
  --socket /path/to/cp.sock \
  --projection-db /path/to/projection.sqlite3
```

## Remaining production acceptance boundaries

The production-source adapter now demonstrates automatic CP04 publication for
the current accepted C16.3 visit/candidate/capability/resource path and for live,
independently authenticated C16.3 rejection events, plus CP06 reconstruction from
portable authenticated accepted BAMF run custody. The CP07 fixture obtains its visit through
the production C03 selection owner and derives the successor through the production
C03 successor owner; it no longer seeds a teacher-visit receipt by hand. Generic
B13 rejection receipts outside the supported C16.3 schema remain outside this CP02
projection. Rejected C16.3 facts are not reconstructed by portable CP06 until an
owner-authenticated rejection anchor exists inside portable B13 custody. Two narrower
data-contract limitations remain explicit rather than being filled with synthetic values:

1. Native C16.3 accepted/rejection artifacts do not carry an authenticated
   wall-clock visit interval. CP02 therefore uses the accepted generation as a
   source-owned logical materialization coordinate and marks those episode,
   candidate and capability projections `PARTIAL`; it does not claim a measured
   wall-clock timestamp.
2. The accepted BAMF bundle does not presently expose a semantically unambiguous
   one-to-one source for all three CP02 `GenerationManifest/v1` digest fields, so
   that family still carries an explicit `UNKNOWN` marker. Native resource records
   now expose only facts the accepted visit actually owns: configured memory budget,
   measured disk usage and derived step rate. Unified memory use remains `UNKNOWN`
   until an authenticated allocator measurement exists.

Those limitations remain visible data-contract debt rather than hidden fixture
coverage. They do not substitute for or weaken the two CP07 production-source
acceptance claims above. #1055 remains open until the exact candidate is
independently reviewed and the accepted PR is merged into the reviewed unified
target under the normal human-merge closeout policy.
