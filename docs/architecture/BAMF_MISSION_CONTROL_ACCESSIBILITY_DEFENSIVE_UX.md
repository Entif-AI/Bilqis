# BAMF Mission Control GUI19 accessibility and defensive-state contract

GUI19 makes keyboard, assistive-technology, stale/offline, partial-data, and
failure behavior part of the Mission Control foundation. It extends GUI01,
GUI02, GUI04, and GUI20; it does not create a second application state model,
control-plane transport, or command authority.

## Accessibility contract

The renderer provides a skip link, named landmarks, visible `:focus-visible`
focus, a dedicated live-region announcer, a labelled non-modal inspector, and a
modal keyboard command palette. Hidden inspector controls are `inert`, so an
off-screen drawer cannot remain in the tab order. Primary navigation and
palette choices support arrow/Home/End movement in addition to ordinary Tab.
Enter and Space activate interactive graph nodes.

The School dependency graph is an interactive `group`, not an image that hides
its descendants from the accessibility tree. Each node carries an explicit
name and pressed/selection state. The exact same selected prerequisite and
dependent identities are rendered in a captioned table immediately after the
graph. Sort headers expose `aria-sort`, and filters expose `aria-pressed`.

Critical run/release identity wraps instead of being permanently clipped.
Reduced-motion disables nonessential transitions and animations, and a
forced-colors rule preserves structural boundaries. Density modes remain native
button-driven settings and therefore keep keyboard and accessibility semantics.

## Defensive-state vocabulary

The renderer keeps these states distinct:

- loading;
- progressive;
- empty;
- stale;
- partial;
- offline;
- denied;
- revoked;
- unavailable;
- incompatible-version;
- timeout;
- duplicate-action;
- session-restarting;
- service-restarting;
- historical-unavailable;
- malformed-payload;
- unsupported-payload;
- outcome-unknown.

Each state has an explicit textual label and explanation, a status/alert role,
and a non-color visual treatment. Empty never means unavailable. Denied never
means empty. Revoked is distinct from both denied and unavailable. Outcome
unknown never becomes failed or completed without a proven receipt/postcondition.

Startup uses the same defensive vocabulary but exposes progress as a four-step text
sequence: control plane, learner discovery, Mission Control telemetry, and trainer.
Assistive technology receives the same progression through the existing polite live
region. A healthy learner with no operator projection is `progressive`, not `live`,
`offline`, or failed. The UI exposes the bounded technical error code when a startup
boundary fails.

## Offline and restart semantics

A verified OperatorView may be cached only as renderer inspection evidence. The
cache is schema-tagged, bounded, and revalidated through the accepted OperatorView
contract before use. When live service context is unavailable, retained evidence
is globally marked HISTORICAL / inspection-only and freshness is explicit.

`Operate` is disabled unless a fresh verified service snapshot has re-established
the live command context. There is no offline mutation queue. Reconnect creates a
fresh control-plane session and fresh snapshot before mutation becomes available.
The current view and selected object are preserved across offline/restart/reconnect
when their identities remain safe to retain.

A UI/service restart is not interpreted as learner failure. The renderer only
reports the control-plane posture it can prove.

## Manual keyboard scenario

Use this representative journey after any shell/navigation change:

1. Press Tab until **Skip to main content** is focused. Activate it and confirm
   focus moves to the workspace.
2. Shift+Tab back to Primary navigation. Use ArrowDown to reach **School** and
   press Enter.
3. Tab into the capability matrix. Activate **B.AND**. Confirm the Global
   inspector opens and its close control receives focus.
4. Press Escape. Confirm the inspector closes and focus returns to the invoking
   School control.
5. Tab to the dependency graph. Use ArrowRight/ArrowDown between nodes and Space
   to inspect one. Confirm the relationship table exposes the same selected
   prerequisite/dependent identities.
6. Press Control+K (Command+K on macOS). Use arrows to choose a destination and
   Escape to close the palette.
7. Exercise an offline/service-restarting fixture. Confirm the banner states
   inspection-only posture, the existing investigation remains visible, and
   **Operate** is disabled until Reconnect obtains a fresh verified snapshot.

The automated `accessibility.test.mjs` and `defensive-state.test.mjs` suites lock
these semantics at the renderer-contract level. The renderer protocol security
suite also locks every allowlisted module/style needed by the keyboard journey.

## Boundaries

GUI19 does not claim universal WCAG conformance. A dedicated conformance review
with target assistive technologies remains separate work. GUI19 does not add
remote/public control, offline mutation, trainer/file access from the renderer,
or Akasha/provider-specific implementation.
