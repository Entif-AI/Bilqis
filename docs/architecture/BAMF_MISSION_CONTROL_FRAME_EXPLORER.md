# GUI08 Frame Compiler Explorer

Issue: #1063. Parent: #1047. Baseline: reviewed unified
`bd181b3b7cae23e7e94af1a7784e2deb4b02944f`. Dependencies #1056,
#1057 and #1051 are closed. IPR-0220 and the human-only student boundary apply.

## Outcome and ownership

Add a read-only Frame Compiler Explorer beneath Model in the existing Electron
shell. The operator arrives from a frame selection and asks how the recorded
source constituents became neural positions, and what was visible at a prediction
frontier. Preserve the twelve top-level destinations; frame objects belong to Model.
First show the inspected generation and fixture provenance, then packing metrics,
then selectable examples and progressively disclosed exact identities/codec fields.

The current accepted Electron adapter returns a literal CP02 OperatorView fixture;
CP03 has bounded frame summary queries but FrameCompileReceipt does not contain
constituents, compiler version, codec fields or visibility maps. GUI08 therefore
ships an explicitly fixture-backed view, as #1047 permits. It does not claim a live
compiler producer or close GUI21. Keep fixture access in Electron main's accepted
adapter; renderer uses only the existing querySnapshot IPC and never imports data
from disk, shells out, or calls a trainer. No new IPC channel or policy mutation.

## Inspection contract

Use a GUI08-specific, versioned fixture inspection envelope, separate from CP02's
unchanged summary schema. A request has schemaVersion, runId, generation (exact
nonnegative integer) and mode (current/historical). Only fixture-run generations
7 and 6 exist. Missing exact identities return MISSING with no substitution.
The response carries the exact request, state, fixture provenance, a bounded list
of examples, and coverage. Each example binds a receipt ID, frame ID, source ID,
generation manifest, compiler version/digest, source/compiled digests, positions,
and optional measured preparation cost, expansion count/passes and sidecar bytes.
Nullable details render Unavailable, including metrics whose source is incomplete.

Each position records an index, path (FAST/PARTIAL/EXTENDED/ATOMIC), frame schema,
tag, occurrence identity, optional literal fallback reason, sidecar reference,
codec field entries, and constituent records. Each constituent carries source
order, atom text, role, occurrence index, canonical semantic ID, source reference,
and its recorded earliest legal frontier. Fields carry their own earliest legal
frontier. Unknown visibility remains Unknown, never inferred from source order.
This is a display contract, not new canonical semantics or a compiler algorithm.

Validate request/response structure, bounded lengths/counts, exact identities,
unique source order/position indexes and safe numeric domains at the main boundary
and renderer consumer. Render all receipt text as escaped text. Validate all
received values before deriving counts. Do not accept arbitrary paths or methods.

## Interactions and reconciliation

The fixture selector exposes generation 7/current and 6/historical explicitly.
Switching updates the whole-shell historical posture and exact context together;
the previous selection, expansion and frontier reset so old details cannot survive
a context change. Async response identity/epoch checks discard superseded results.
Opening a frame deep link selects its exact ID; missing IDs remain missing.

An example selector and native details/summary expansion reconstruct constituent
identities in source order. A frontier selector marks future-illegal constituents
and codec fields and hides their contents, including raw receipt disclosure; the
recorded full-source metrics are explicitly separate from the frontier lens.
Show literal path/reason and exact sidecar/compiler identities only when recorded
and visible. Future-illegal fields cannot leak through a raw JSON panel.

Selected-example metrics and aggregate metrics over the returned examples share
one derivation: N = constituent count; F = position count; N/F; FAST/F; counts of
PARTIAL, EXTENDED, ATOMIC; summed recorded expansion counts/passes and sidecar bytes.
Missing operands yield Unavailable rather than zero. Label aggregate scope and
coverage. Measured CPU/preparation cost is displayed only if explicitly recorded.
Compression metrics do not establish learned semantic competence.

The four-constituent/one-position case is a literal illustrative fixture, not a
claim that production causal-prefix compilation removes raw atom positions.
Production compile_prefix preserves atom positions and adds closure positions;
GUI08 must not reinterpret its stats as this illustrative codec packing ratio.

## Failure and accessibility

Render loading, empty, missing, unavailable, denied, stale, partial and error states
explicitly; retain no stale details after a failed/context-changing query. Label all
fixture content even when the CP01 connection is healthy. Reuse existing theme,
density, status styles and reduced-motion behavior. Native labeled selects,
buttons, details, table captions and non-color legality labels support keyboard
operation. Wrap long identities and locally scroll wide tables at narrow widths.

## Implementation and proof

Own GUI08 contract/fixture support under apps/mission-control, pure metric and
visibility derivation, a small renderer module and styles, narrow adapter/validator
integration, frame owner routing and Model mounting. No learner, source, ABI,
compiler, CP02 schema or CP03 query semantics change.

Red/green Node tests prove 4 -> 1 exact expansion, all paths and literal reasons,
aggregate reconciliation, hidden future contents (including codec/ref fields),
missing detail/unknown cost, two compiler versions, wrong historical identity,
malformed data and markup escaping. Main-bridge tests prove request validation,
exact fixture identity and no broker/command invocation. Existing shell/security
tests cover compatibility. Browser/Electron inspection verifies keyboard expansion,
frontier changes, historical treatment, dark/light and narrow rendering. Run bounded
repository quality/differential checks, ABI verification and scoped EGM drift before
opening a ready PR to current unified. Human review/merge is the final boundary.

## Exact wire and transition specification

All objects below have exactly the listed keys; strings are nonempty, at most
512 Unicode characters; collections at most 32 examples, 64 positions/example,
64 constituents/position and 32 fields/position. Counts/frontiers are safe
nonnegative integers; digests are 64 lowercase hexadecimal characters. Nullable
means explicit JSON null, never an omitted key. All example and source-order IDs
are unique in their containing collection. The response is limited to 256 KiB.

- Request: `{schemaVersion: "bamf.gui08.frame-query/v1", runId, generation,
  mode: "current" | "historical"}`. Current requires generation 7; historical
  accepts an exact generation. The fixture adapter recognizes only fixture-run
  generations 6 and 7. All other exact identities return MISSING.
- Page: `{schemaVersion: "bamf.gui08.frame-page/v1", request, state, coverage,
  provenance: "ILLUSTRATIVE_FIXTURE", operatorView, examples}`. State is one of
  PRESENT, EMPTY, MISSING, UNAVAILABLE, DENIED, STALE, PARTIAL, UNKNOWN, ERROR.
  Coverage is COMPLETE, PARTIAL, UNKNOWN. Non-data states have no examples.
  operatorView is a validated CP02 OperatorView for exactly request.runId and
  request.generation, or null on MISSING/UNAVAILABLE/DENIED/UNKNOWN/ERROR.
- Example: `{receiptId, frameId, sourceId, generationManifest, compiler,
  sourceDigest, compiledDigest, positions, expansionCount, expansionPasses,
  sidecarBytes, preparationMs}`. Compiler is null or `{version, digest}`.
  Positions and the four measurements are nullable; preparationMs may be a
  nonnegative finite number. Digests identify the literal fixture only.
- Position: `{index, path, schema, tag, occurrenceId, visibleAt, reason,
  sidecarRef, fields, constituents}`. Paths are FAST, PARTIAL, EXTENDED, ATOMIC.
  schema/tag/occurrenceId/reason/sidecarRef and visibleAt are nullable. Indexes
  are contiguous from zero. Fields are null or `{name, value, visibleAt}` arrays;
  value is text. Constituents are `{sourceOrder, atom, role, occurrenceIndex,
  semanticId, sourceRef, visibleAt}`. sourceOrder is contiguous across the example.
  visibleAt is a nullable frontier; all other constituent fields are required.

Frontier p means exactly the first p source atoms are eligible for inspection;
domain 0..N, inclusive, initially N. A recorded visibleAt <= p is legal.
Null visibleAt means Unknown and contents stay hidden at every frontier. The
position's visibleAt gates all its metadata, references and field access; a field
also requires its own visibleAt <= p. Constituents are independently gated by
their own visibleAt. Hidden rows show only an ordinal and Future-illegal/Unknown.
The view has no raw JSON disclosure. Example identity and compiler/digests are
receipt-level provenance, outside the frontier lens, labeled as such. Metrics
are full-source receipt metrics, never a statement of what entered a prefix.

N and F are unavailable when positions are null; otherwise N=sum constituents,
F=positions.length. Ratios are unavailable when F=0. Aggregate N/F and FAST/F
use summed numerators/denominators, not averaged ratios. All counts derive from
the same positions. A missing operand in any selected scope makes that aggregate
metric unavailable (never a partial sum presented as total). Expansion count and
passes are literal recorded totals per example; aggregate labels say sum, without
implying sequential/global pass count. Preparation cost aggregate is likewise a
sum only when every example has measured cost. Empty scope has no ratios.

Fixture generation 7: `frame:quad-fast` has four atoms in one FAST position;
`frame:mixed-fallback` has four atoms across PARTIAL/EXTENDED/ATOMIC positions;
`frame:detail-missing` has null positions/compiler/measurements. First two sum to
N=8,F=4,N/F=2,FAST/F=1/4; full three-example scope reports unavailable metrics
where the missing example prevents a total. Generation 6 has the quad alone and
a distinct compiler version/digest. Each generation has a complete literal CP02
operator fixture, derived from operator-view-v1.json with generation-bound record
and run digest fields explicitly changed. Main validates this context and all
example generationManifest fields against it; renderer installs that exact
context using normalizeContext, then applies mode based on the exact request.

Renderer owns a fixture generation selector inside Model. A new query immediately
clears details, selected example/frontier and the previous inspector. Loading and
failed queries leave the last verified global context intact and explicitly label
the requested target locally; context changes only with validated response data.
Use a monotonically increasing request epoch and exact request comparison. A late
response cannot overwrite a newer target. Frame links use the existing route
`#/view/model?kind=frame&id=<encoded-id>`; they preserve current shell context,
as existing GUI01 links do, and do not purport to encode historical context.
Selecting a missing frame never silently selects another. Same-view rerenders
preserve the existing controls; mounting/unmounting invalidates query epochs.

Concrete files: renderer/frames/frame-contract.mjs owns shared validators and constants;
renderer/frames/frame-model.mjs owns pure metrics/visibility; renderer/frames/frame-explorer.mjs
owns rendering and async interactions; renderer/frame-explorer.css owns styles;
fixtures/frame-inspections-v1.json owns literal fixture pages. Extend the accepted
adapter snapshot dispatcher for this exact request, using an Electron-main-only
fixture selector. Inject the frame validators in main.cjs alongside the existing
OperatorView validator; accepted-contracts.cjs dispatches responses by schema and
rejects unsupported variants. Renderer imports validators, never fixture data.
Existing preload/IPC validation remains in force. Tests live in the existing
tests and electron/tests directories; production compiler modules stay untouched.

Presentation clarification: aggregate metrics use a native collapsed disclosure
after the selected example, so unavailable totals do not displace the primary
inspection controls. Missing positions disable the frontier selector. Closing
the shell inspector preserves the mounted frame selection and frontier.

## Current-unified integration amendment

Unified `55e7ae289c1dee6ee6bfb080526f24e33b8f30cc` adds School, Episodes and
Neural Runtime renderers. Preserve these owners unchanged. Model now has two
native buttons, Neural Runtime and Frame Compiler Explorer, selecting one domain
section at a time. Default to Neural Runtime to preserve unified behavior; a frame
deep link selects the frame section and a neural deep link selects Neural Runtime.
Closing an inspector and changing theme/density preserve the selected Model
section. Section switches clear the prior inspector and dispose pending frame
requests; other destinations preserve their upstream render paths. Never display
neural fixture telemetry inside the frame section's inspected context.

Before first entering Frames, retain the exact normalized shell context. On
leaving Frames (another Model section or destination), restore that context before
paint and dispose the frame mount. Re-entering Frames saves the then-current
context and queries an exact fixture generation again. School, Episodes and
Neural Runtime already own independent fixture datasets; show a persistent
shell-owned note immediately above their domain host: "Independent illustrative
fixture: this view uses its own declared provenance and is not bound to the shell
run/generation." Preserve their internal run/generation labels. This expressly
prevents the global context from claiming their unrelated fixture identities.
Test historical Frames -> Neural Runtime -> School and back: frame context is
restored, unrelated views show the independent-provenance note, pending frame
queries cannot overwrite them, and frame links still select Frames.

The Electron custom-protocol asset allowlist must explicitly include the three
frame .mjs modules and frame-explorer.css. Keep fixture JSON main-only and continue
denying it through the renderer protocol. Add a contract test that every HTML
script/stylesheet and local JS import in the allowlist resolves to another allowed
asset, so source-import tests cannot miss an unloadable packaged renderer.
This is required integration scope inherited from #1063 and GUI20, with no new
compiler, source, learner or mutation behavior.

Structure-gate integration: group the three GUI08 JavaScript modules in
`renderer/frames/`, retaining their single owners and updating imports and exact
protocol paths. This keeps the renderer root below its code-file trigger without
moving unrelated domain modules. CSS remains in the shared stylesheet directory.

Latest-unified integration (`7d681427c8a3cb95352cf8179ba0b85dceea180e`)
adds Semantic Atlas and its separate CP03 query bridge. Preserve that query method
and its validators alongside the GUI08 snapshot variant; do not redirect Atlas
queries into fixture snapshots. Preserve both stylesheets and Atlas renderer.
The combined shell crosses the file-size trigger. Extract the existing Atlas
controller state/functions and School/Atlas/Neural/Episodes dispatch unchanged
into `renderer/views/domain-views.mjs`. Its constructor receives getState,
onInspect and getModelSection callbacks; it returns render and
ensureAtlasOverview. Inspector updates remain shell-owned. This module owns domain
dispatch, while renderer.mjs retains context/navigation/inspection and the frame
mount lifecycle. Add its exact protocol asset and dependency-closure coverage.
Before dispatching any destination, determine the Model section from selection
and run the frame mount/dispose transition, restoring any prior context before
another view constructs markup or requests data. Model's frame section keeps the
upstream domain host hidden; other sections retain their existing behavior.
Validate preserved query behavior with existing adapter/Atlas tests, and repeat
the scoped Frames -> Neural -> School transition proof. No source or learner
semantics change; this refactor satisfies the repository's size gate.

Shared-host async control: the extracted domain owner gives every Atlas overview,
search and ABI request a monotonically increasing epoch plus the exact normalized
context reference captured before loading. A result may update state/markup only
when its epoch is current, the destination is still Atlas and the context is the
same. Starting a newer request supersedes the older one. Rendering any other
destination invalidates outstanding epochs and resets an unfinished Atlas load to
idle for a later visit. This prevents pending Atlas work from repainting Frames,
School or Neural Runtime. A context change resets Atlas-derived state before a
fresh query. Test delayed completion after navigation, context change and a newer
request; these controls prevent shared-host corruption introduced at composition.

Scope audit: delivery is the composed GUI08 on current unified; required_by is
exact context/async custody and mandatory structure gates; defer_failure is stale
Atlas completion replacing a newly selected domain; cheapest_next is a shared
epoch/context guard at the extracted domain owner with focused negative tests.
PROCEED within required integration scope; retain other Atlas query semantics.

Final integration amendment, superseding the preceding extraction locations:
unified `eabc6758074296e5e767adbb9a43423b175cb2f3` supplies GUI19's
foundation/renderer-ui.mjs and atlas/atlas-controller.mjs, plus Memory/Teacher
domains. Reuse those owners and delete the now-redundant views/domain-views.mjs.
Keep the incoming shell's reconnect/cache, defensive-state, announcements, focus
restoration, palette and keyboard behavior. Put GUI08's mount/context lifecycle in
frames/frame-shell.mjs with getState, setState, render, refresh and onInspect
callbacks. It supplies beforeRender/afterRender hooks: select the Model section,
restore/dispose before incoming chrome/domain dispatch, then mount the fixture
view after dispatch. Store modelSection in shell UI state; frame snapshots disable
mutation availability and retain the original context/mutation posture for return.
Section controls remain keyboard-native, and exact frame/neural links choose their
section. Incoming renderer-ui owns the read-only Model section switch and explicit
independent-fixture note; frame data still crosses the validated snapshot channel.

Move the already-reviewed Atlas epoch guards onto atlas/atlas-controller.mjs's
existing overview/search/ABI handlers. Each render/overview call receives an
isActive callback bound to the exact current context reference and Atlas view.
Context rebinding invalidates old epochs; leaving Atlas explicitly invalidates
unfinished requests and resets loading to idle. Reuse its existing query calls.
Retarget owner-level delayed-response tests to these actual handlers, including
School/Frames host preservation, context changes, retries and request precedence.
Keep all upstream asset paths; append only GUI08 assets to the exact allowlist.
The shell context and inspector continue escaping receipt-derived values.

Reconnect control: frame-shell also receives getDefense and exports reset. At the
start of every establishSnapshot attempt, reset disposes pending frame queries
and discards the saved return context without restoring it. The shell disables
mutation for the pending attempt. Frame hooks do not capture/mount while defense
is loading. A successful or cached/failed reconnect installs its own validated
context and defensive profile first; a later frame mount captures that new context.
On exit, restore only that saved context and derive mutation availability from the
latest defensive profile, never a saved boolean. Preserve the chosen Model section
across the reconnect. Old frame responses cannot replace new snapshot state.
Test pending, denied/cached and successful reconnects, exit posture and late frame
response disposal. A reconnect without any valid snapshot leaves no restorable
frame context and keeps mutation unavailable.

Publication-sync note: unified `5df83f69a4fb07b6c39dea47868934bc0d8e0e62`
adds Home/Evidence activation via foundation/domain-controller.mjs. Preserve those
owners and pass its Atlas activation a getState callback so the existing reviewed
view/context guard reads current shell state rather than a captured state value.
The snapshot variant and new event/query validators coexist unchanged; retain
compacted identity labels with escaping and accessible full-identity attributes.
