# #1453 Mission Control observer CPU profile

The production native Mission Control path now caches accepted BAMF projection state separately from the live trainer-observation overlay. A trainer heartbeat no longer reauthenticates accepted history, reprojects rejection evidence, or cold-loads the numerical student.

`scripts/bamf/mission_control_observer_profile.py` is the rerunnable profile. `1453-observer-profile.json` records the measured values and the explicit CPU budgets.

## Budgets

The accepted budgets are fractions of one CPU core:

- idle Home recovery: at most 1%;
- nominal live observation at the trainer's 1 Hz heartbeat: at most 2%;
- worst-case observation changes at the CP04 4 Hz scan ceiling: at most 5%.

The committed receipt measured 0.073%, 0.050%, and 0.165%, respectively. All three budgets pass.

## Attribution

On the current accepted `aspirant` run, an uncached full 14-family native round used about 1.10 s CPU. The cold-path breakdown was approximately:

- authenticated history: 203 ms CPU;
- accepted-record projection: 392 ms CPU;
- rejection-ledger and SQLite authentication: 556 ms CPU;
- live observation overlay: 1.1 ms CPU;
- catalog construction: below 0.1 ms CPU.

After the first authenticated build, a complete 14-family round used about 4.7 ms CPU. Serializing all 14 query pages used about 3.2 ms CPU. A warm Run-family query used about 1.5 ms CPU.

The disposable live-observation fixture measured about 0.27 ms CPU for a changed Run query and 0.15 ms for a changed CP04 refresh. An unchanged CP04 check used about 0.02 ms CPU. Twenty observation updates caused zero accepted-history reauthentications and zero cold student loads.

SQLite remains part of cold rejection-evidence authentication. It is no longer paid on unchanged or observation-only refreshes after the accepted catalog is cached. CP04 event subscription blocks between records; the profile measures the refresh work separately from that wait.

Home is event-driven for trainer observations. It refreshes the Run family for `run.trainer.observed` events and uses a 2 s safety timer for recovery/status. CP04 checks native changes at the service's 0.25 s subscription heartbeat. The trainer's default observation heartbeat is 1 s.
