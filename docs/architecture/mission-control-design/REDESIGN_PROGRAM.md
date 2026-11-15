# Admin Main Frame surgical redesign program

Parent: [#1124](https://github.com/Entif-AI/Bilqis-MLX/issues/1124)

This file is the execution index for the redesign leaves. The issue bodies remain the unit of implementation authority. The order below minimizes shared-surface churn and lets each leaf reuse the design/test/i18n foundations established before it.

## Gate 0 · Design authority complete

Before UI implementation:

- `apps/mission-control/DESIGN.md`
- `STYLE_GUIDE.md`
- `VISUAL_COMPOSITION_SPEC.md`
- `CONSTRAINT_REGISTER.md`
- `INFORMATION_ATLAS.md`
- `CURRENT_STATE_UI_INVENTORY.md`
- `FLOWS.md`
- `ANTI_PATTERN_GALLERY.md`
- `REQUIREMENT_TRACE.md`
- parent issue #1124 with deficiency ledger
- explicit human ratification of the aesthetics, palette, component-library posture, and other locked design rules in #1124

No runtime UI leaf begins before that ratification. Merged documentation is not itself proof that the named agreement gate occurred.

No leaf should reinterpret these artifacts independently. If implementation discovers a contradiction, update the authority/deficiency record first. `INFORMATION_ATLAS.md` governs **what the redesigned UI should contain**. `CURRENT_STATE_UI_INVENTORY.md` governs **what existing substrate must be consciously reconciled**. A current node must be retained, transformed, merged, moved, or removed; current presence does not imply target survival.

## Tier 1 · Shared foundations

### #1126 · Canonical primitives, status grammar, i18n and test-hook foundation
Why first: every later leaf needs the same string/token/test-hook and primitive rules. Keep this deliberately small; it is not a component-framework rewrite.

### #1127 · Shell context, navigation, destination header and defensive chrome
Depends on: #1126.
Why early: shell geometry and IA define the usable viewport inherited by every destination.

### #1128 · Global inspector, time lens, compare, pins, annotations and deep-link investigation
Depends on: #1126; coordinate with #1127.
Why early: these cross-view planes are reused by every domain leaf and carry exact identity semantics.

## Tier 2 · Primary learning / overview surfaces

These may proceed in parallel after the relevant Tier 1 shared contracts are stable.

- #1129 · Admin Main Frame overview
- #1130 · School capability matrix, dependency graph and curriculum atlas
- #1131 · Capability Explorer dossier and chronology
- #1132 · Learning candidate transaction and retention replay

Rationale: these are the most frequent operator path from “what is happening?” to “what learned?” to “show me exact capability/episode evidence.”

## Tier 3 · Representation / mechanism surfaces

May proceed in parallel after #1126/#1128. #1134 must preserve frame-context custody.

- #1133 · Semantic Atlas identity and derived-similarity separation
- #1134 · Model neural runtime and Frame Compiler Explorer
- #1135 · Engram Memory atlas and generation comparison

Rationale: these surfaces are dense and diagnostic; they benefit from shared table/status/disclosure primitives proven in Tier 2 without becoming prerequisites for the basic overview path.

## Tier 4 · Decision / correction surfaces

- #1136 · Teacher strategy evidence and measured comparison
- #1137 · SÍ SÉ SON salience evidence and routing rationale
- #1138 · Corrections blast radius and requalification

Rationale: all three require careful epistemic visual separation between observation, derived comparison/aggregation, and authority.

## Tier 5 · Provenance / resource / action surfaces

- #1139 · Lineage accepted generations and literal diffs
- #1140 · Resources budget evidence, timeline and historical comparison
- #1141 · Evidence query, provenance inspection and origin return
- #1142 · Operate request, preflight, authorization and reconciliation

Rationale: these are exactness-heavy surfaces. Evidence and Operate are allowed to expose more forensic detail because that detail is their task. #1142 must remain fail-closed and should integrate only after shared status/identity patterns are stable.

## Tier 6 · Whole-application closeout

### #1143 · Integrated WCAG, i18n, test-hook and visual acceptance

Runs once after all prior leaves integrate. This is the requested whole-app pass; it must not be pulled forward as a repeated ritual after every leaf.

## Per-leaf execution cadence

For each issue:

1. reread `DESIGN.md`, style guide, `VISUAL_COMPOSITION_SPEC.md`, exact anti-pattern gallery, target atlas, current-state inventory, and relevant CON-D/FLOW-D IDs;
2. enumerate the target nodes owned by the issue and map the relevant current inventory nodes to **retain / transform / merge / move / remove** dispositions;
3. capture the current micro-surface as before evidence;
4. implement the smallest coherent target-state redesign, removing current atoms that have no target-state job rather than preserving them by inertia;
5. sweep the entire owned micro-surface and convert **all** human-facing copy in that surface to localization tokens, not only lines edited for layout;
6. sweep the entire owned micro-surface's UI tests and migrate **all element selection** to exact/prefix `data-test-id` hooks, not only selectors incidentally touched by the visual diff;
7. perform the local WCAG 2.2 AA review;
8. run only affected tests plus unavoidable hooks;
9. capture after evidence in required modes/states;
10. append newly discovered deficiency to #1124;
11. make additional conformance refinements beyond the ticket's enumerated defects when they are discovered through `DESIGN.md` / style-guide review, including refinements not previously noticed; coordinate rather than suppress a refinement when it overlaps another leaf's active ownership.

The ticket describes the minimum known work, not a maximum. Agents are explicitly authorized by #1124 to improve additional defects they discover in the course of conforming the application to the design constitution. Keep those additions evidence-driven, preserve behavior, record newly discovered deficiencies in #1124, and avoid conflicting simultaneous edits to a surface another leaf actively owns.
