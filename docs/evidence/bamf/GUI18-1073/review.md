# GUI18 implementation review

Issue: #1073. Branch:
`codex/1073-gui18-global-interactions-20261113`.

Status: `LOCAL_ACCEPTANCE_PASSED_PENDING_HOSTED_VERIFICATION`.

## Scope reviewed

GUI18 adds a shell-owned global investigation layer without extending control-plane
authority:

- exact current/historical generation lens;
- explicit return to a verified current service snapshot;
- generation, candidate, capability, strategy, and identity comparison adapters;
- evidence-only cross-highlighting;
- versioned operator-local pins and annotations;
- exact `bilqis://` app URIs mapped back to the trusted Admin Main Frame renderer;
- inspector actions and keyboard-accessible investigation controls.

The implementation follows the locked Option A design in
`docs/evidence/bamf/GUI18-1073/design.md`: one investigation strip beneath the
existing run/generation context plus the existing object inspector.

## Authority and evidence boundaries

- The existing shell context remains the only time authority.
- Explicit historical selection sets `historicalPinned`; defensive offline
  history does not.
- A historical view with no exact reconstruction stays locally
  `UNAVAILABLE`. It does not substitute current data and does not change the
  global lens.
- `Use verified current` is enabled only after a healthy service snapshot has
  been observed. Cached or historical state cannot manufacture current truth.
- Compare adapters emit literal facts and explicit unavailable/incompatible
  dimensions. They do not rank, normalize, or synthesize a winner.
- Cross-highlighting consumes only explicit object relationships supplied by
  owning views.
- Pins and annotations remain renderer-local metadata. Annotation records carry
  `LOCAL_OPERATOR`, timestamp, exact target, scope, and
  `OPERATOR_NOTE_NON_AUTHORITATIVE`.
- External app URIs are validated in the main process and converted to a hash on
  the existing trusted `bamf-mc://app/index.html` document. No external
  document becomes a renderer origin.

## Browser findings and repairs

The interactive preview caught three defects that unit tests did not expose.

### Defensive history was becoming sticky

Observed:

1. The disconnected defensive state correctly downgraded a live context to
   `HISTORICAL`.
2. `buildDeepLink` serialized that transient mode as `mode=HISTORICAL`.
3. Reconnect reparsed the URL and treated the transient state as explicit user
   historical intent.

Repair:

`buildDeepLink` now encodes `HISTORICAL` only when
`context.historicalPinned` is true. Defensive history with no explicit pin is
encoded as `LIVE`. A regression test proves reconnect can restore live context.

### Inspector and investigation controls occupied the same pixels

Observed:

The fixed 390 px inspector covered the annotation form and later covered tool
tabs after the investigation strip narrowed.

Repair:

The shell records inspector open/closed posture. The investigation strip reserves
the inspector width, switches to a compact two-row layout whenever the inspector
is open, and stacks annotations in one column. At narrow widths the reserved
margin collapses.

### Newly inspected objects left GUI18 actions stale

Observed:

Inspecting a candidate updated the inspector but did not rerender the GUI18
action state, so compare buttons remained disabled from the prior selection.

Repair:

Inspector open/close and evidence-selection paths now rerender the interaction
controller immediately after updating the inspector.

## Browser acceptance

Connected Chrome proof exercised the implementation rather than only static
markup.

### Synchronized time lens

- Entering generation `44238` from School produced the exact route
  `generation=44238&mode=HISTORICAL`.
- School rendered `UNAVAILABLE` because its checked-in matrix has no exact
  generation snapshot.
- Navigating to Memory preserved the same lens and reconstructed the exact
  `g44238` memory fixture.
- A healthy service reconnect made `Use verified current` available without
  changing the historical lens.
- Activating it returned Memory to generation `7`, `LIVE`, with the verified
  manifest restored and the route rewritten to the current lens.

### Compare

- Capability compare: B.AND vs B.NOT rendered literal School facts with no
  winner synthesis.
- Candidate compare: retained vs interference-rejected candidates preserved
  challenger and committed state separately. The browser showed target
  committed `12/12` vs `8/12` and protected committed `48/48` vs
  `48/48`.
- Generation compare: generation 44238 vs recovery generation 44240 rendered
  exact accepted lineage differences, including retention disposition, teacher
  epoch, topology version/digest, and recovery state.

### Cross-highlighting

Hovering B.AND highlighted exactly:

- B.AND as selected;
- B.NOT as prerequisite;
- B.OR and B.IFF as dependents.

No other object was highlighted. These are the relationships literally encoded
by the School fixture.

### Pins and annotations

- B.NOT was pinned with exact run and generation identity.
- The pin remained after closing and reopening the preview tab.
- A non-authoritative operator note remained after restart with author,
  timestamp, scope, and exact target.
- After the inspector-layout repair, a second note was entered and saved through
  real browser input while the inspector remained open.

### Deep links and layout

- The selected object exposed the exact
  `bilqis://run/fixture-run/generation/7/capability/B.NOT` URI.
- Unit/security tests validate external URI parsing and trusted internal route
  conversion.
- A wide generation comparison scrolls inside
  `.investigation-table-wrap`; the page itself has no horizontal overflow:
  document width 1398 px at a 1412 px viewport.

The checked-in replay is
`apps/mission-control/tests/browser/global-interactions-journey.mjs` and
returns `GUI18_BROWSER_JOURNEY_PASS` when executed by the repository browser
harness.

## Final local verification

The feature commit `c6070b4a0e0ba961c08b90569c5bd705a0b48ebd` was composed
with unified `cde4bf7e7b1aa605d901149bbc6e619dbf8f4ada`, which added
GUI17 Operate and the current GUI22 School/Curriculum Atlas surfaces. The only
merge conflicts were the shared stylesheet list and renderer controller
initialization; both features were retained. The composed `renderer.mjs` is 357
lines, below the 360-line structural interruption threshold.

Exact composed-tree receipts:

- GUI18 + GUI17 + GUI22 focused seam: 60/60 PASS;
- full Admin Main Frame renderer: 259/259 PASS;
- Electron security: 51/51 PASS;
- Python Electron bridge: 6/6 PASS;
- Admin Main Frame Python: 80/80 PASS;
- development structure: 0 violations;
- governance integrity: 0 violations;
- BAMF flow control: PASS, tests 15/15;
- static adaptation-source authority gate: PASS, tests 7/7;
- `git diff --check`: PASS;
- `git diff --cached --check`: PASS.

The repository `verify:leaf` wrapper was also exercised against the exact
current unified base. The earlier pre-merge attempt compared against the original
fork point and therefore selected GUI17 learner/projection tests from the 15
newly consumed unified commits; those imports require MLX and are not GUI18's
change surface. The final scoped invocation set both
`BILQIS_TEST_BASE_REF` and `BILQIS_QUALITY_BASE_REF` to
`origin/codex/bamf-unified-base-20261028`. The differential planner then
reported `mode=skip`, `changed=35`, because GUI18 changes only
JavaScript/CJS/CSS/docs paths, and the wrapper completed PASS with the full
259/259 renderer and 51/51 + 6/6 security/bridge suites. No MLX or learner
execution was required.

## Review decision

The interaction architecture remains aligned with #1073 and the existing
Admin Main Frame authority model. No control-plane schema or learner mutation is
required. Local acceptance and the scoped leaf wrapper are complete; only remote
fencing and hosted verification remain before human merge review.
