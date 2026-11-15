# GUI05 review and scope record

- EGM pinned SHA: b3a35956759bf7f024af2ff061b2e0b44b438e4c.
- Reviewer: fresh Implementation Readiness, GPT-6.1 Terra, High reasoning.
- Target: design.md in this directory, reviewed before behavioral implementation.
- Readiness findings resolved: exact dossier shape and byte bound; CP03 request,
  public response, pagination and reference contracts; compatibility module moves;
  explicit record-bearing evidence-family selector.
- Final scoped readiness disposition: PASS, no unresolved Blocker or Major.
- The final selector correction was literal/mechanical, not a new design boundary.

## Scope audit

The implementation exceeds three files and 250 lines because one required journey
crosses CP02 facts, CP03, the accepted Electron bridge and the renderer. Every
behavior maps to #1060's dossier, literal evidence, historical state or exact
navigation clauses. No new learner acceptance is added (`new_acceptance=false`).
The contracts-directory split is mandated by the encountered >=18-file threshold.
The C01 receipt's authority-path clarification repairs the existing static gate;
it does not change C01 disposition, training semantics or source authority.

## Drift review repairs

Fresh Terra High drift review compared only design.md and its owned implementation.
It found five implementation defects: shallow main-process record validation,
noninteractive rendered reference text, missing source navigation owner, hidden
markers when no dossier matches, and later-generation episode IDs in early fixtures.
The candidate repairs each at its owning boundary. No design semantics changed.
A subsequent focused Terra High recheck reported NO_DRIFT for all five repairs.

Installing the required main-process schema validator exposed a docs-scanner defect:
its authored-document scan traversed node_modules and reported dependency README
links omitted from published packages. The focused red/green regression preserves
checking authored broken links while excluding only installed third-party modules.
This is required to run the existing gate after a normal npm install, not a waiver
for any project-authored documentation.

## Unified intake

Consumed reviewed unified 55e7ae28 during turn-in. The CP05 v2 records merge into
the same contracts owner and regenerated schema. GUI04 School, GUI06 Episodes and
GUI09 Neural Runtime remain reachable. Their domain assets were grouped without
behavior changes to keep the encountered renderer directory within its <=12-file
limit. Exact asset allowlists and tests follow those moves.

After intake: 110 CP01/CP02/CP03/bridge Python tests PASS in 2.213 seconds;
95 Node tests PASS; the keyboard/evidence/history/related-capability/offline browser
journey PASS. Python owner verification used one worker, a 1 GiB MLX allocation
limit and disabled cache; no durable learner was touched.

## Differential qualification plan

The explicit current-unified comparison selects 212 files / 1,045 test functions.
The default selector would compare committed HEAD to itself and skip Python tests;
qualification therefore pins BILQIS_TEST_BASE_REF to the consumed unified SHA.
The expected stage duration is 5–20 minutes from the selected bounded owner/fixture
set; the already-executed 110 owner tests completed in 2.213 seconds. This remains
an estimate, not a passing result. The terminal two-hour boundary stops the owned
process group and produces a nonzero incomplete result if the estimate is wrong.
Snapshot isolation, one test worker, 1 GiB per-process MLX allocation and disabled
cache apply to every inheriting Python process. This stage answers differential
compatibility only. The separate premerge/integration obligation remains pending.

## Qualification failure repair and second unified intake

The first snapshot failed during collection in 33 seconds; no source mutation
occurred. Seven errors shared a namespace collision: pytest resolved repository
`tests` as `scripts/tests`. A literal two-package regression reproduces it; enabling
pytest's namespace-package resolution repairs it (13 gate-owner tests PASS).
Two existing neural participation tests also imported helpers from their previous
owner. Their imports now name `atlas_model_participation`; the three affected cases
pass without changing numerical/runtime logic.

Consumed reviewed unified 7d681427 (GUI07). Its accepted CP03 query operation,
semantic records and bridge error projection coexist with GUI05's snapshot-query
compatibility surface. Both use one typed Python query implementation. The original
renderer reached 400 lines during intake; its sibling domain rendering now lives
in domain-views.mjs, leaving renderer.mjs at 235 lines. Both retain the same views,
callback behavior and exact asset allowlist.

Post-intake evidence: 62 Admin Main Frame and 55 control-plane Python tests PASS;
103 Node tests PASS; the GUI05 browser journey PASS. Full premerge collection
preflight imports 908 test files / 4,512 cases with zero import failures after
installing the historical Torch test dependency. This is collection evidence only.

The resource guard now installs MLX limits lazily when mlx.core is imported,
preserving tests of neural-inert imports. A subprocess regression proves both
that MLX stays unloaded until requested and that its 1 GiB/cache-zero policy applies.
All qualification repairs inherit the existing verification obligation
(`new_acceptance=false`); none adds learner, source or admission requirements.

Final shared-seam review found one navigation defect: delayed Atlas callbacks could
replace a different destination in the shared view host. The repair guards active
view rendering and binds asynchronous selection/overview results to their context.
A red/green interaction test covers semantic and ABI responses after destination
and generation changes. Fresh focused recheck reports NO_DRIFT.

Qualification v2 chains static gates, collection preflight, verify:leaf and
verify:premerge in one snapshot. Estimated completion is 15–60 minutes for the
measured 1,161 selected leaf cases and 4,512 aggregate cases; this estimate is not
acceptance evidence. The whole pipeline retains one terminal two-hour ceiling.
The notification/receipt must be reconciled before PR creation.
