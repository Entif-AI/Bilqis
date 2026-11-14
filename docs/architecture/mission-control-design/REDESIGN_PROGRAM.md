# Mission Control surgical redesign program

Parent: [#1124](https://github.com/Entif-AI/Bilqis-MLX/issues/1124)

This file is the execution index for the redesign leaves. The issue bodies remain the unit of implementation authority. The order below minimizes shared-surface churn and lets each leaf reuse the design/test/i18n foundations established before it.

## Gate 0 · Design authority complete

Before UI implementation:

- `apps/mission-control/DESIGN.md`
- `STYLE_GUIDE.md`
- `CONSTRAINT_REGISTER.md`
- `INFORMATION_ATLAS.md`
- `FLOWS.md`
- parent issue #1124 with deficiency ledger

No leaf should reinterpret these artifacts independently. If implementation discovers a contradiction, update the authority/deficiency record first.

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

- #1129 · Mission Control overview
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

1. reread `DESIGN.md`, style guide, relevant CON-D and atlas/flow IDs;
2. capture the current micro-surface as before evidence;
3. make the smallest coherent redesign;
4. tokenize touched copy;
5. add/migrate touched `data-test-id` hooks/tests;
6. perform the local WCAG 2.2 AA review;
7. run only affected tests plus unavoidable hooks;
8. capture after evidence in required modes/states;
9. append newly discovered deficiency to #1124;
10. turn in the leaf without opportunistically redesigning unrelated views.

Adjacent refinement inside the touched surface is authorized when it directly improves conformance with the design constitution. Expanding the touched surface itself requires a ticket/atlas rationale.
