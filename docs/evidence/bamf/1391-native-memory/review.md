# Design review — #1391

Pinned EGM: `b3a35956759bf7f024af2ff061b2e0b44b438e4c`.
Reviewer: fresh GPT-6.1 Terra, High reasoning, Codebase Details persona,
Implementation Readiness standard. Review performed before production changes.

Initial finding: Major, preserve portable entry-point tests when introducing lazy
MLX import. Design step 4 now specifies class-local no-op memory contexts for
existing mocked visits, real policy with fake MLX in focused tests, and real MLX
in hardware tests. Affected-scope re-review: PASS, zero unresolved Blockers/Majors.

Implementation scope audit: two production files; additional existing test edits
only isolate their mocked visits from MLX. All edits trace to #1391 acceptance;
no new acceptance obligations. Existing policy implementation remains unchanged.

Red: 2 failed / 3 passed on baseline 71a00bb90, both failures observed cache
987654 instead of zero during native operator ownership.
Green: 5 focused tests passed; 2 native MLX normal/exception tests passed on m3-ultra.
Hardware witness uses a disposable Linear model and native MLX AdamW inside the
real operator coordinator with visit/source/storage boundaries doubled. It proves
cache policy and live-array preservation, not full BAMF learning or publication.

Post-implementation fresh GPT-6.1 Terra High scoped review: NO_DRIFT;
no substantive implementation defect. Native hardware cases ran (2 passed,
zero skipped). Live legacy authority on m3-ultra: PASS, Factory branch
`codex/337-replay-349-20261026`, head
`d84d2ab9e2d79817c131ef7e0d4ec0d574e57b32`, generation 24254.
Local check could not resolve the remote-only authority path; remote live check
is the applicable receipt.

Next qualification: 36 differential test files, static gates first, single MLX
worker, test-only 8 GiB allocator bound and existing no-free-cache policy in every
Python child. Expected 20–45 minutes; hard failure after 80 minutes. This does
not claim the production trainer has an 8 GiB allocator cap.

Requested main intake exposed a 391-line rejection projection test. The
mandatory structure interruption split unchanged test assertions into projection
(232 lines), genesis (57 lines), and shared fixtures (115 lines). Twelve focused
cases passed before import-only cleanup. Local Work Stack interruption completed;
full leaf qualification includes the changed test files. This is inherited
structure compliance for the requested main merge, not a trainer semantic change.

Leaf v1 receipt: FAIL, 143 passed / 61 failed / 1 collection error; source
snapshot unmutated. Static structure, governance, smell, trainer-authority,
invariant-transfer and flow-control stages passed. Failure census: 52 stale
`run_authority.binding.storage_root` patches, moved session helper imports/patches,
and a cold-resume double missing `run_authority`. These boundaries were removed or
moved in the consumed baseline, independently of the memory-context change.
Repair scope: migrate affected test doubles to current owners and remove obsolete
storage-root substitutions. Preserve all runtime behavior and assertions. This
implements inherited #1391 acceptance requiring existing resume/publication tests
green; no new acceptance obligation. First focused repair checks: 18 + 7 passed.

Additional focused verification after fixture migration: 16/16 operator observed,
mentor, championship, publication, metrics and throughput cases passed in 5.04s.
Combined repair checks total 41 passing cases. Production memory implementation
has not changed. Differential selection now includes 72 files because shared
fixture repair invalidates its direct test consumers. Leaf v2 is a fresh snapshot;
v1 evidence remains preserved and its 143 passing cases are historical evidence.

Leaf v2: 388 passed, 1 failed, 58 subtests passed; snapshot unmutated.
Remaining failure was the cold-resume double call expectation omitting the
existing `run_authority=None` argument. Corrected the literal expected call;
production behavior remains unchanged. Static gates passed again. No third
unchanged broad diagnostic run: first prove this exact assertion locally on
m3-ultra, then consume current unified before the integration boundary.

Resume assertion repair: 2 passed in 26.26s on m3-ultra. Current unified
`204a5f4769189b1dd9d334f1b7a85b4133a48110` consumed at merge head
`249d541d066aa708917cd22da98e4dffa0194e0e`; only ledger conflict, preserving
both issue entries. Native memory coordinator files unchanged by intake. Intake
changes readout, retention, priority and model validation assumptions, so affected
integration proof must run again. Production design review/NO_DRIFT remains valid.

Integration qualification chains static quality, aggregate collection preflight,
affected tests, Node/security and the existing premerge aggregate. Existing runner
excludes DETACHED_ONLY witnesses. Discovery: 1,186 files / ~5,500 unittest methods.
Expected 45–90 minutes using the measured 18-minute leaf and repository qualification
estimates as inputs; entire composed run fails after 115 minutes. Test-only 8 GiB
allocator bound remains applied to every Python child. No whole-system PASS is
claimed until terminal receipts are reconciled.

Integration v1 stopped at the error field manual check before test collection.
The native test's inline synthetic exception was counted as a raw error site.
The test now creates the exception once and verifies that the operator
propagates the same instance. Regenerating the catalog produces no diff.
The v1 snapshot mutation guard passed.

Integration v2 passed static quality. Its collection preflight incorrectly used
pytest discovery for the unittest aggregate, which bypassed verified SKOS bundle
reuse and attempted to import the optional PDF extractor. The source snapshot
passed its mutation check. Preflight now uses the aggregate's own selection and
loader. The real loader also exposed four PyTorch import errors in the shared
test interpreter. Installing PyTorch 2.15.0 in a separate test dependency directory
resolved them. On the v2 source snapshot the corrected preflight loaded 5,076
unittest cases with zero import errors and verified the unchanged SKOS bundle.

Integration v3 passed the governance, architecture, documentation and error
catalog checks but stopped at the code smell check. The harness used a mutable
module-level list for its import paths. Replacing it with a tuple passed the
staged smell and structure checks. No test ran and the snapshot stayed intact.

Integration v4 passed static quality and aggregate import preflight (5,076
cases, zero import errors). Affected tests reported 368 passed and 21 failed.
Twenty failures hit the default 100 GiB reserve during disposable custody
writes on a host with 97 GiB available. The profile ordering test stopped
before visiting for the same reason. Three test files now pass an explicit
fixture reserve. The production default and reserve enforcement are unchanged.
The exact 21 failed case IDs passed on the same host in 17.23 seconds,
including eight subtests. The v4 snapshot mutation guard passed.

V5 passed 389 affected tests, 465 Node tests, 67 Node security tests and
the Python security stage. The full aggregate reported 103 failures/errors.
The unchanged 204a5f47 control reported 260 failures/errors with 37 matching
test identities and outcomes. Disk availability differed near the 100 GiB
reserve, so this comparison does not establish zero regressions. Both runs
passed their snapshot mutation guards.

Unified df0e73942 adds native allocator retry and visit holds. The merge
preserves that scheduler behavior inside the cache policy scope. The harness
now applies its test-only allocator bound on first MLX core import, which
addresses the unrelated import-isolation failure exposed by v5.

V6 passed static quality and loaded 5,077 aggregate cases without import
errors. Affected tests reported 390 passes and one failure. The routing double
for an empty selection lacked the holds field now consumed by allocator retry.
The fixture now supplies an empty holds tuple. The v6 mutation guard passed.
Unified 418dd5ad replaced the old championship fixture with evidence checks
at the accepted successor boundary. The merge preserves those checks and
keeps the isolated visit double independent of MLX startup. The combined
route, native cache, allocator continuation, and championship tests passed
25 cases on m3-ultra against the merged candidate.

V7 at b8c482b3 passed static quality, import preflight (5,082 cases and zero
load errors), 395 affected tests with 58 subtests, 465 Node tests, 67 Node
security tests and nine Python security tests. Snapshot integrity passed.
The premerge aggregate reported 4,705 passes, 36 failures/errors and 277
skips. All 36 failure/error records match the unchanged 204a5f47 control
by test identity, result type and normalized terminal error. The control
reported 260 failures/errors. The two runs used different unified revisions
and resource conditions, so this comparison describes observed matches on
the tested branch, independent of any assumption about a current green aggregate.

Consumed unified 92299b7c at 371f07c5. On that merge head, 59 focused cases
and 15 subtests covering factory release identity, admission, cold resume,
championship, allocator continuation and native cache ownership passed on
m3-ultra. The subsequent receipt and runner edits are administrative.
The aggregate remains red on the last full run. The #1391 PR is prepared
locally and remains unopened under the repository pre-PR gate.
