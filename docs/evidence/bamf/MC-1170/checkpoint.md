# #1170 implementation checkpoint

The feature starts from reviewed unified `2c8cda55d1344626bc6c6f11d9b5db5836a36604`.
It adds a bounded atomic observed trainer snapshot, one-second measured heartbeat,
optional retention assessment progress, additive observed CP02 records/current-only
CP03 queries/CP04 events, and Home progress with bounded snapshot recovery.
Accepted generation and optimizer coordinates remain owned by authenticated custody.

Pinned EGM `b3a35956759bf7f024af2ff061b2e0b44b438e4c` Implementation Readiness
review initially found five Majors. The precise-contract and automatic-recovery
amendments resolved all five; the fresh-context reviewer returned PASS.
Post-implementation review found two defects: parent-linked observations disappeared
on successor publication, and parallel Home queries could straddle publication.
Both were reproduced and repaired with focused regression tests. The reviewer
confirmed both repairs and found no further material drift; an additional explicit
snapshot-frontier retry case remains to add before final qualification.

Observed verification before current-unified intake:

- 82 existing Mission Control Python tests passed.
- 18 existing control-plane event/query/reconnect tests passed.
- 379 renderer tests passed; 53 Electron checks and 8 Python bridge tests passed.
- Focused observed contracts, producer/lifecycle, retention callbacks, and Home tests
  passed. Native custody tests passed 18/19 after making disposable fixture reserve
  explicit; the last case then passed separately after the same fixture repair.
- Static quality gates passed. Two inherited metadata defects were repaired:
  regenerated error catalog/manual and an explicit canonical source annotation in
  GUI1143's acceptance note. These do not claim a fresh legacy-trainer inspection.
- Disposable browser fixture rendered at 1440px and 390px. The narrow document width
  was exactly 390px; screenshots remain under ignored `.local/1170/`.

Scope audit: the change exceeds three files/250 lines because the inherited outcome
crosses trainer, retention, typed transport, and renderer owners. Every production
change maps to #1170's required acceptance; `new_acceptance=false`. Fixture reserve
zero applies only to disposable NativeSourceFixture publications and preserves
explicit overrides. Production reserve and training authority are unchanged.

Unified advanced during work, including candidate-horizon, retention batching/cache,
and source-prefetch changes. Consume current unified next, reconcile those actual
owner contracts, amend/review affected design assumptions, then run affected proof.
Leaf/premerge qualification and final current-unified readback remain outstanding.
No PR, merge, issue closure, real student start, or persistent optimizer update has
been performed by this work.

## Reconciled intake

Merge `1111a7eb` consumes unified `406e30c65c257230b50259d678ed4e1e2a880f14`.
The final design amendment and scoped drift review passed. Telemetry now follows
actual multi-step candidate horizons and cache-aware foundation assessment counts.
The explicit snapshot mismatch/retry and actual successor-publication observation
cases pass. Post-intake proof is 28 native/observed tests, 382 renderer tests,
53 Electron tests and 8 Python bridge tests. Broad gates remain pending.
