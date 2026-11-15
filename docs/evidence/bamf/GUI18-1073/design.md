# GUI18 global investigation interaction design

Authority: issue #1073, additive child of #1047. Baseline:
`origin/codex/bamf-unified-base-20261028` at
`17f003eb1b1b000db6d24efaad7547ac24603e12`.

GUI18 owns Admin Main Frame interaction state and operator-local metadata. It does
not add learner, source, teacher, optimizer, admission, semantic, or evidence
authority.

## Product acceptance

Issue #1073 requires one connected investigation grammar across Admin Main Frame:

- one explicit run/generation lens across compatible views;
- historical failure in one view must stay local and must not restore other views
  to current;
- exact generation and candidate comparison, plus compatible capability,
  strategy, and source/release comparison where literal evidence exists;
- cross-highlighting only from relationships already present in evidence;
- persistent operator pins with no learner mutation;
- stable app URIs that preserve exact run, generation, and object identity;
- operator annotations with author, time, scope, and an explicit
  non-authoritative posture;
- keyboard-accessible time and compare controls.

## Feature constraint register

### CON-D-001 · shell context is the time authority

Source: `shell-state.mjs`, `deep-link.mjs`, GUI05 historical-lens behavior.

Classification: mandatory. Ownership: shared Design/Architecture.

The existing shell context already owns run, generation, mode, historical pin,
and immutable projection identities. GUI18 extends that state. It does not create
a second time store. Changing the time lens changes `state.context` once, then
all context-aware controllers receive the same value.

### CON-D-002 · historical state is inspection-only

Source: GUI01 defensive state and GUI05 `historicalPinned`.

Classification: mandatory. Ownership: shared.

An explicit historical lens sets `mode=HISTORICAL`,
`historicalPinned=true`, clears unresolved projection pins to `UNKNOWN`, and
keeps mutation unavailable. A later healthy reconnect must not clear an explicit
historical pin. Offline defensive history must still return to live after a
healthy reconnect when no user pin exists.

### CON-D-003 · a view may be unavailable without changing the lens

Source: issue #1073 and existing partial/unavailable visual language.

Classification: mandatory. Ownership: Design.

If a view cannot reconstruct the selected generation from its accepted data
surface, it renders `UNAVAILABLE` or `PARTIAL` for that view. It does not
substitute current data and does not mutate the shell lens.

### CON-D-004 · relationships must be literal

Source: issue #1073, GUI05 evidence doctrine, existing School/Memory/Episode
fixtures.

Classification: mandatory. Ownership: shared.

Cross-highlighting uses explicit identifiers already present in the selected
record or accepted fixture. No relation follows from similar names, labels,
family membership, score movement, or visual proximity.

### CON-D-005 · compare is descriptive

Source: issue #1073 and existing Lineage/Memory/Teacher comparison models.

Classification: mandatory. Ownership: Design.

Comparison preserves each side's identity and denominator. Incompatible
dimensions render `UNAVAILABLE` with the literal reason. No overall winner,
ranking, normalization, or causal interpretation is synthesized.

### CON-D-006 · pins and annotations are operator-local metadata

Source: issue #1073 and the existing localStorage display-setting pattern.

Classification: mandatory. Ownership: Design.

Pins and annotations use a versioned renderer-local record in localStorage.
They never enter CP02, CP03, source records, learner state, or command surfaces.
Annotation author is a local operator label, not an inferred account identity.

### CON-D-007 · the renderer keeps its privilege boundary

Source: GUI20 Electron security boundary.

Classification: mandatory. Ownership: Architecture.

GUI18 adds no filesystem, shell, process, network, clipboard, or arbitrary IPC
privilege. Stable external app URIs are parsed in the main process and converted
to the existing trusted `bamf-mc://app/index.html#...` renderer route. The
renderer origin does not change.

### CON-D-008 · current shell geometry stays the visual center

Source: issue mock-up and existing shell.

Classification: preferred. Ownership: Design.

Run/generation remains the top context. Investigation controls sit directly
below it. The existing inspector remains the object-action surface. GUI18 does
not add a second permanent side rail that competes with the inspector.

### CON-D-009 · keyboard and narrow layouts are first-class

Source: issue #1073 and existing GUI01 accessibility contract.

Classification: mandatory. Ownership: Design.

Time selection, compare slots, pinning, annotation entry, and investigation
panel navigation use native controls. Focus remains visible. Controls wrap or
collapse on narrow layouts without horizontal page overflow.

### CON-D-010 · repository structure limits apply

Source: `AGENTS.md`.

Classification: mandatory. Ownership: Architecture.

Do not grow `renderer.mjs` past 360 lines. New GUI18 logic belongs under a
cohesive `renderer/interactions/` package. Keep modules small enough that the
shell remains readable.

## Interaction designs considered

### Option A · investigation strip under the context bar

The shell adds a compact, persistent strip below the run/generation header. It
contains the exact time lens, compare status, pin count, annotation count, and a
button that opens an in-flow investigation panel. The existing inspector gains
Pin, Compare, and Annotate actions for the selected object.

Strengths:

- one visible axis from run to generation to investigation state;
- no new overlay competing with the inspector;
- compare and time controls remain keyboard reachable before domain content;
- narrow layouts can wrap the strip into two rows;
- implementation fits the current shell state and domain-controller ownership.

Cost: the strip consumes modest vertical space on every destination.

### Option B · permanent right investigation dock

A second right-side dock owns Compare, Pins, and Notes while the inspector floats
inside it.

Strength: comparison remains visible beside domain content.

Rejected because it creates two right-side ownership models, reduces usable
width for dense tables, and makes the current inspector contract harder to
preserve at 760–980 px widths.

### Option C · contextual ribbon plus bottom watch tray

Each domain exposes local compare actions. A collapsible tray at the bottom owns
pins and notes.

Strength: low default chrome.

Rejected because global investigation state becomes spatially fragmented. The
user must infer whether a local comparison changed the global lens. It also
duplicates controls across views and weakens the issue requirement for one
connected grammar.

## Decision

Implement Option A.

The shell remains the state owner. GUI18 adds one investigation strip and one
bounded panel. The inspector provides object actions. Domain views expose only
stable object descriptors and literal relationship descriptors.

## State contract

GUI18 adds a pure interaction state beside the existing shell fields:

```text
interaction:
  compare:
    left: stable object ref | null
    right: stable object ref | null
  highlight:
    origin: stable object ref | null
    related: stable object refs[]
  panel: closed | compare | pins | annotations
```

A stable object ref contains:

```text
kind
id
runId
generation
label?
details?
relations?
```

`relations` is optional and contains only explicit `{kind,id,relation}`
tuples supplied by the owning view. Cross-highlighting never derives additional
relations.

Pins and annotations persist separately because they are operator metadata.
Every stored target records kind, ID, run ID, and generation. An annotation also
records:

```text
annotationId
target
author = LOCAL_OPERATOR
createdAt
scope = OBJECT | GENERATION
body
authority = OPERATOR_NOTE_NON_AUTHORITATIVE
```

The store is bounded. Invalid or unsupported stored versions fail closed to an
empty operator store.

## Time lens

The current generation selector becomes an exact numeric generation lens rather
than a fixture-only select. The visible current generation remains a suggested
value. Selecting another generation:

1. validates a nonnegative safe integer;
2. updates the shell context to that generation;
3. sets historical mode and the explicit historical pin;
4. clears generation-dependent projection identities to `UNKNOWN`;
5. disables mutation;
6. rerenders every active compatible controller with the same context.

Returning to current must be an explicit action against a freshly verified live
snapshot. GUI18 does not manufacture current projection pins from a historical
view.

Known fixture behavior:

- Capability can reconstruct its declared fixture generations.
- Memory can reconstruct only generations present in its memory fixtures.
- Lineage can identify declared accepted-generation fixture nodes.
- Resources already performs bounded exact historical queries.
- Evidence already queries exact run/generation.
- School's checked-in matrix has no generation-indexed snapshots. Under an
  explicit historical lens, it must label the matrix unavailable as an exact
  reconstruction instead of showing current fixture values as historical.
- Other fixture-backed domains follow the same rule unless their fixture declares
  the selected generation.

## Compare contract

The investigation panel owns two explicit slots. Pinning a compare side captures
the selected object and its exact context at that moment.

Supported adapters:

- generation vs generation: reuse `compareGenerations`;
- candidate vs candidate: compare literal episode candidate fields and preserve
  rejected challenger state separately from committed parent state;
- capability vs capability: compare literal capability facts when both objects
  expose a compatible fact set; otherwise show incompatible dimensions;
- strategy vs strategy: reuse `strategyComparison` on an explicit shared scope;
- source/release revisions: render exact identity differences only when both
  selected objects contain source/release identity.

Different object classes return an explicit `INCOMPATIBLE_KIND` result. Missing
facts stay unavailable.

## Cross-highlighting

The global interaction controller applies `data-global-highlight` only to DOM
objects whose stable `data-object-kind` and `data-object-id` match the selected
ref or an explicit relation supplied by that ref.

Initial adapters cover relationships already present in current fixtures:

- School capability prerequisites/dependents;
- Memory slot capability and episode references;
- Episode capability, candidate, checkpoint, source-revision, and evidence refs;
- Capability dossier related objects;
- Lineage generation/checkpoint identities.

If a relation target is not present in the active DOM, no placeholder is
invented.

## Stable app URI

Canonical external form:

```text
bilqis://run/<encoded-run>/generation/<generation>/<kind>/<encoded-id>
```

The parser accepts only the declared `bilqis:` scheme, a nonblank run ID, a
nonnegative safe generation, and known object kinds. It produces the same
internal route contract used by `deep-link.mjs`.

The Electron main process registers the protocol only for app routing. Incoming
URIs are normalized, converted to a trusted renderer hash, and delivered to the
existing Admin Main Frame window. Invalid URIs are ignored. The app never
navigates the renderer to the external URI itself.

Internal hash links continue to work and remain the browser-test surface.

## Defensive states

- Invalid generation input: keep the prior lens and announce the validation
  error.
- Historical view unsupported: show local unavailable/partial state. Keep the
  global lens unchanged.
- Compare side missing: render an empty-slot instruction.
- Incompatible compare kinds: show both identities and
  `INCOMPATIBLE_KIND`; do not coerce.
- Missing compare dimension: show `UNAVAILABLE` for that row.
- Corrupt operator metadata: discard the invalid payload and start an empty
  local store.
- Duplicate pin: preserve one canonical pin.
- Annotation with blank body: do not persist it.
- Annotation storage failure: keep the investigation usable and report that the
  note was not saved.
- Deep-link parse failure: leave the current trusted route unchanged.
- Cross-highlight target absent from current DOM: no effect.

## Accessibility and responsive behavior

- The investigation strip is a named `nav`/region with native buttons,
  inputs, and tabs.
- Compare sides have explicit Left and Right labels. Color is never the sole
  side marker.
- Time input exposes its exact generation value and an Apply action.
- Pin and annotation controls expose the selected object ID in their accessible
  names.
- Annotations use a labeled textarea. Saving returns focus to the annotation
  list or inspector action.
- Cross-highlighting uses outline/border and a textual inspector relation list,
  not color alone.
- At narrow widths the strip wraps. The investigation panel becomes a single
  column and comparison rows stack.
- Reduced-motion and forced-colors behavior follows existing shell rules.

## Verification

No GUI18 acceptance requires MLX or learner execution.

Focused tests must prove:

- one time-lens update changes shell context once and remains historical across
  compatible views;
- unsupported history does not mutate the shell context;
- generation comparison preserves exact literal changes and incompatibility;
- candidate comparison distinguishes challenger from committed parent state;
- only explicit relationships become highlight targets;
- pins round-trip through localStorage and reject corrupt versions;
- annotations retain target, author, timestamp, scope, and non-authoritative
  marker;
- canonical `bilqis://` URI round-trips to the exact internal route;
- invalid external URIs cannot navigate the renderer;
- time/compare controls have native keyboard semantics;
- renderer protocol allowlist includes GUI18 modules;
- existing defensive reconnect and GUI05 historical-pin tests remain green.

After focused verification, run `npm run bamf:test`,
`npm run bamf:security:test`, the Admin Main Frame Python owner tests,
structure/governance checks, and `npm run verify:leaf`. Re-fence current unified
before turn-in. Open the PR only after the final candidate is ready for human
review.

## Design lock

Status: `DESIGN_LOCKED`.

No Product scope question is blocking. The architecture implication is bounded:
GUI18 needs controlled main-process app-URI routing plus renderer-local
interaction state. No control-plane schema change is required for the first
accepted slice. If implementation discovers that a claimed historical view
requires new authoritative data, that view must remain unavailable rather than
expanding GUI18 into a producer/schema issue.
