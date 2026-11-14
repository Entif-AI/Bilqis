# Mission Control redesign constraint register

Status: governed redesign input
Parent authority: GitHub issue #1124
Canonical visual authority: `apps/mission-control/DESIGN.md`

This register records constraints that a redesign leaf must preserve. It is not a backlog and it does not transfer semantic ownership from the source authorities named below.

## Register

| ID | Constraint | Strength | Source / trace | Design consequence |
| --- | --- | --- | --- | --- |
| CON-D-001 | Mission Control is an owner-operated inspection and bounded-operation surface, not an independent source of learner truth. | MUST | `README.md`; BAMF architecture; renderer state model | Presentation may simplify, group, or disclose evidence, but must not manufacture authority or collapse source/derived distinctions. |
| CON-D-002 | Mutating learner actions remain behind CP05/Operate preflight, exact target binding, explicit human authorization, and receipt/readback. | MUST | `docs/architecture/BAMF_MISSION_CONTROL_OPERATE.md`; `renderer/operate/*` | Visual redesign may clarify the sequence but must not make mutation look equivalent to ordinary navigation or observation. |
| CON-D-003 | Operate is unavailable without a fresh verified live command context. There is no offline mutation queue. | MUST | `BAMF_MISSION_CONTROL_ACCESSIBILITY_DEFENSIVE_UX.md` §§ Offline and restart semantics; `renderer/foundation/renderer-ui.mjs` | Historical/offline posture must remain obvious and mutation affordances disabled until fresh context is proven. |
| CON-D-004 | Loading, progressive, empty, stale, partial, offline, denied, revoked, unavailable, incompatible-version, timeout, duplicate-action, restarting, malformed/unsupported payload, historical-unavailable, and outcome-unknown are distinct states. | MUST | `BAMF_MISSION_CONTROL_ACCESSIBILITY_DEFENSIVE_UX.md` | One status grammar may unify treatment, but states may not be visually or semantically collapsed. |
| CON-D-005 | Outcome unknown must never be rendered as failed or completed without authoritative readback. | MUST | Accessibility/defensive UX contract; Operate lifecycle | Error styling and copy must preserve epistemic uncertainty. |
| CON-D-006 | A UI/service restart is not learner failure. | MUST | Accessibility/defensive UX contract | Startup/restart treatment must state which boundary is unavailable rather than implying learner death. |
| CON-D-007 | Keyboard operation, named landmarks, skip link, visible focus, live-region announcements, inert hidden inspector, roving navigation, and graph keyboard operation are existing behavior contracts. | MUST | `BAMF_MISSION_CONTROL_ACCESSIBILITY_DEFENSIVE_UX.md` | Surgical redesigns extend these behaviors and must not regress them. |
| CON-D-008 | Complex graph relationships require an accessible equivalent representation. | MUST | School accessibility contract | Graph visual refinement cannot remove the relationship table or equivalent nonvisual representation. |
| CON-D-009 | Reduced motion and forced-colors behavior are existing contracts. | MUST | Accessibility/defensive UX contract | Motion and state cues must remain usable under both preferences. |
| CON-D-010 | WCAG 2.2 AA review is performed on every touched micro-surface; full-app conformance is run once after all leaves integrate. | MUST | User instruction; issue #1124 | Each ticket includes local accessibility acceptance rather than deferring accessibility to a final cleanup. |
| CON-D-011 | The runtime UI remains vanilla HTML/CSS/JavaScript during this redesign. | MUST | Issue #1124 design lock | External design systems may be references, not runtime framework migrations. Dependency adoption is Architecture-owned. |
| CON-D-012 | Mission Control operates inside Electron with a bounded renderer bridge and CSP. | MUST | `renderer/index.html`; security tests | Redesign may not require remote assets, unsafe inline scripts, or broader renderer privileges. |
| CON-D-013 | Fixture/reference data must remain visibly distinguishable from live accepted telemetry. | MUST | Current renderer and fixture contracts; bootstrap repair `f5f7561f` | Never make richer fixture-backed diagnostic surfaces appear to be live learner state. |
| CON-D-014 | Missing telemetry is not zero and is not learner failure. | MUST | Bootstrap, Resources, accessibility/defensive UX | Use unavailable/unknown/partial states rather than synthesized numeric defaults. |
| CON-D-015 | Historical context is inspection-only and must preserve exact generation identity. | MUST | GUI18 interaction model; accessibility contract | Time-lens styling must remain distinct from live state; mutation stays unavailable. |
| CON-D-016 | Cross-view selected-object identity is stable across run, generation, kind, and ID. | MUST | `renderer/interactions/model.mjs` | Inspector, compare, pins, annotations, and deep links must not visually imply identity equivalence when context differs. |
| CON-D-017 | Operator annotations are local, non-authoritative metadata. | MUST | `renderer/interactions/view.mjs` | Notes must be visually useful without acquiring evidence/source styling. |
| CON-D-018 | The global inspector is an independent inspection plane with focus-return behavior. | MUST | `index.html`; accessibility contract | Redesign may resize/recompose it, but must preserve discoverable close/return behavior and exact detail access. |
| CON-D-019 | Theme supports dark and light modes; density supports comfortable and compact modes. | MUST | Existing settings and issue #1124 | Modes alter presentation, not semantic hierarchy or meaning. Comfortable must remain genuinely comfortable. |
| CON-D-020 | No ordinary readable UI text should be below 12px; monospace is for machine identity/raw technical data. | MUST | `DESIGN.md` | Dense metadata cannot be solved by shrinking prose into illegibility. |
| CON-D-021 | Operator-significant semantic values may not be silently truncated. | MUST | Issue #1124; screenshot deficiency corpus | Recompose, wrap, disclose, or provide an explicit full-value affordance. Hashes may use documented middle ellipsis only with exact value immediately available. |
| CON-D-022 | Shell chrome must expose only context useful across destinations. | MUST | Issue #1124; current shell audit D-003 | Topology/factory/semantic/resource facts move behind deliberate disclosure when they crowd the task surface. |
| CON-D-023 | Primary navigation currently exposes 14 destinations; grouping must be derived from the application atlas and operator tasks, not arbitrary aesthetic categories. | MUST | Current `DESTINATIONS`; issue #1124 | IA changes require atlas/flow evidence and must preserve direct destination access. |
| CON-D-024 | View summaries currently carry important epistemic boundaries and may not be deleted merely because they are technical. | MUST | `renderer/foundation/current-view.mjs` | Rewrite for operator-first language and progressive disclosure while preserving the underlying claim boundary. |
| CON-D-025 | One application-wide status grammar replaces per-view ornamental variants without collapsing domain-specific states. | MUST | `visual-language.mjs`; issue #1124 | Shared primitives should encode label + structural/non-color cue + optional explanation. |
| CON-D-026 | Every human-facing string touched by redesign becomes a stable localization token with explicit parameters. | MUST | User instruction; issue #1124 | No sentence-fragment concatenation. Machine identifiers remain data. Layout must tolerate expansion and prefer logical CSS properties. |
| CON-D-027 | Every application element touched by UI tests receives a stable unique `data-test-id`; intentional groups use a documented prefix. | MUST | User instruction; issue #1124 | Affected tests migrate away from visible text, DOM hierarchy, classes, element IDs, localized strings, and incidental attributes. |
| CON-D-028 | Exact `data-test-id` values identify one rendered element only. | MUST | User instruction | Repeated rows need prefix/group conventions or identity-suffixed IDs, not duplicate exact IDs. |
| CON-D-029 | Functional `data-*` attributes may continue to carry runtime semantics but are not substitutes for the test-hook namespace. | SHOULD | Current renderer architecture | Keep behavior data and test identity separate so tests do not couple to implementation mechanics. |
| CON-D-030 | Existing tests and implementation are preserved as much as possible; each leaf runs the smallest claim-appropriate verification set. | MUST | User instruction; AGENTS differential verification rules | Avoid whole-app retesting and broad rewrites during local redesigns. |
| CON-D-031 | Test runs expected to exceed two hours must be split into meaningful resumable stages; normal leaf verification should finish in seconds/minutes. | MUST | `AGENTS.md` verification ceiling | Design verification plans must remain bounded. |
| CON-D-032 | Current fixture-preview bootstrap repair is regression-sensitive. | MUST | commit `f5f7561f`; Mission Control fixture harness | Design work that touches renderer bootstrap or preview must retain fixture bridge/cache-busting/syntax protections. |
| CON-D-033 | Renderer CSP currently permits only self-hosted scripts/styles/assets and no network connections. | MUST | `renderer/index.html` CSP | Typography/iconography choices must work without external CDNs or runtime font fetches. |
| CON-D-034 | Wide analytical surfaces own their overflow; the document/shell must not drift horizontally. | MUST | `DESIGN.md`; screenshot corpus | Tables/matrices use local scroll, sticky orientation, column grouping/disclosure where appropriate. |
| CON-D-035 | Navigation, filtering, grouping, export, mutation, and status are distinct interaction roles. | MUST | `DESIGN.md`; screenshot corpus | Shared control primitives may normalize geometry, but visual hierarchy must preserve role. |
| CON-D-036 | The design reference is a calm scientific workstation, not cyberpunk terminal theater, a generic SaaS dashboard, or a consumer settings app. | MUST | issue #1124; `DESIGN.md` | When no narrower rule applies, choose the composition that best resembles a precise benchtop research instrument and scientific figure. |
| CON-D-037 | Whitespace, alignment, typography, and tonal layers carry hierarchy before borders, shadows, patterns, or decoration. | MUST | `DESIGN.md` | A section is not automatically a card. Nested bordered rectangles require a specific structural reason. |
| CON-D-038 | Motion is brief, mechanical, and explanatory; nonessential motion collapses under reduced-motion. | MUST | `DESIGN.md` | No bounce, glow, overshoot, or decorative animation. |
| CON-D-039 | The global DESIGN.md is agent-readable visual authority; the style guide may be more explanatory but cannot contradict its normative tokens or core prose. | MUST | Google DESIGN.md spec; issue #1124 | Changes that alter the aesthetic constitution update both artifacts intentionally. |
| CON-D-040 | Cross-view flows are documented separately from the hierarchy atlas to prevent the atlas from becoming an unreadable relationship graph. | MUST | User instruction | Atlas nodes own composition; `FLOWS.md` owns navigation/state/relationship paths by node ID. |
| CON-D-041 | The Electron renderer uses only the frozen `window.bamfMissionControl` capability membrane; it has no raw Node, filesystem, shell/process, credential, or unrestricted IPC authority. | MUST | `apps/mission-control/electron/README.md`; preload/renderer-boundary contracts | Design work may not demand new renderer privilege merely to simplify UI implementation. Any dependency/capability change is Architecture-owned. |
| CON-D-042 | The renderer is served from the bounded `bamf-mc://app` origin with context isolation/sandboxing, Node/webviews disabled, and external navigation/window/permission denial. | MUST | Electron security contracts | UI assets and interactions remain compatible with the existing local-only security envelope. |
| CON-D-043 | Supported window geometry extends down to the current Electron minimum; responsive states must remain legible and operable there. | MUST | Electron main/window contracts; current shell breakpoints | A redesign must test recomposition at the supported minimum rather than only polished wide screenshots. |
| CON-D-044 | Current <=980px shell behavior hides navigation labels and leaves initials, which conflicts with the redesign rule against ambiguous collapsed labels. | MUST-RESOLVE | `renderer/shell.css`; issue #1124 navigation rule | The shell redesign leaf must replace this behavior with a legible responsive navigation treatment; do not perpetuate initials as the target state. |
| CON-D-045 | Current historical/offline styling and tests use repeating-gradient/striped cues, which conflict with the redesign prohibition on decorative gradients/striped wallpaper. | MUST-RESOLVE | `renderer/shell.css`; `visual-language.test.mjs`; issue #1124 | Replace the treatment and its focused tests together while preserving non-color historical/defensive distinction. |
| CON-D-046 | Current display settings include a terminal density in addition to comfortable/compact; the redesign constitution treats terminal-like density as non-default and final support must be an explicit design decision rather than accidental inheritance. | MUST-RESOLVE | `renderer/settings.mjs`; `visual-tokens.css`; issue #1124 | Do not silently delete or normalize the mode. Resolve its intended support in the shared-primitives/shell leaf and test the decision. |
| CON-D-047 | Live CP04 event delivery is selective effect plumbing: Home, Resources, and Operate react to different admitted event families. | MUST | event-stream architecture; renderer controllers | Visual state refresh must not imply that every event refreshes every view or that event arrival changes source authority. |
| CON-D-048 | Entering the Model frame fixture surface temporarily installs an exact fixture context and disables mutation; leaving restores the saved shell context and invalidates stale frame responses. | MUST | frame shell/controller contracts | Model redesign must preserve this context-custody boundary and make fixture posture legible. |

## Leaf checklist

Every redesign child issue must cite the relevant CON-D IDs and state:

1. atlas node(s) touched;
2. preserved authority/state semantics;
3. affected localization tokens;
4. affected test IDs and migrated tests;
5. WCAG 2.2 AA criteria reviewed for the micro-surface;
6. defensive states exercised;
7. responsive/theme/density variants exercised;
8. smallest verification commands;
9. before/after rendered evidence;
10. any new deficiency discovered and appended to #1124.
