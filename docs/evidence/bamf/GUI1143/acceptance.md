# GUI1143 · Model Forensics redesign integrated acceptance

Issue: #1143
Parent design authority: #1124
Unified base at final acceptance: `2dac4d9273af2a0fe6a0161352c21e295ddfbc39`

## Result

The redesigned Model Forensics application passes the integrated closeout gate across all fourteen destinations. The final pass reconciles the target atlas with the current-state inventory, removes stale shell surfaces that had no target-state owner, enforces stable test-hook selection, closes cross-leaf accessibility and responsive-layout defects, and records whole-app rendered evidence instead of relying on leaf-local unit tests alone.

The closeout changed presentation and testability only where the integrated application proved a defect. It does not change BAMF semantic authority, trainer policy, source-gold behavior, model state, or mutation authority.

## Integrated defects repaired

- Browser journeys no longer select application UI by visible text, ARIA/localized labels, CSS classes, DOM hierarchy, or incidental attributes. Exact semantic `data-test-id` hooks or intentional `data-test-id^=` namespaces are the selector contract.
- The production shell no longer mounts the retired global fixture-provenance/demo/catalog surface. Fixture posture remains owned by destinations that actually need it. The visual-language catalog remains reference/test material.
- Operate now has an explicit integrated current-view route instead of falling through to a stale catalog path.
- Static shell copy, the document title, shell accessible labels, Historical School copy, and the remaining catalog provenance literal use localization keys.
- Memory definition-list markup now keeps supplemental descriptions inside the corresponding `dd`; the comparison scroller is keyboard-focusable and named.
- Operate no longer declares a false ARIA list around action buttons.
- Skip navigation moves focus to the main workspace without corrupting the hash route.
- Learning and SÍ SÉ SON contain wide analytical content inside their owned surfaces at responsive widths instead of widening the document.
- Corrections and Evidence no longer repeat the shell destination title and summary inside the content body.
- The Learning stylesheet was decomposed after the repository structural trigger: 230 / 180 / 141 / 94 LoC production modules, with 190 / 98 LoC companion test modules.
- GUI1135 received an append-only legacy-trainer authority annotation so the integrated repository authority gate is green.

## Atlas and inventory reconciliation

The closeout contract mechanically checks all current top-level component IDs against `INFORMATION_ATLAS.md`, all fourteen current views against the fourteen target `VIEW-D-*` destinations, and every target component for an explicit current-substrate disposition or new-target declaration.

The final atlas records two previously implicit outcomes:

- `CUR-COMP-009` is removed from the production shell; destination-local fixture/reference posture survives only where it has a target owner.
- `CUR-COMP-014` is merged into `COMP-D-007 · Global inspector`; exact deep-link behavior remains without a separate permanent shell surface.

The Capability evidence seam and Frame Compiler subcomponents now name their source dispositions individually instead of leaving current inventory entries unmatched.

All `FLOW-D-*` and `CON-D-*` references used by the design bundle resolve to their governing registers.

## Automated proof

`npm run verify:leaf` passes on the final working tree:

- development structure: PASS, 0 violations
- governance integrity: PASS, 0 violations
- changed-file smell audit: 0 new findings
- legacy-trainer authority: PASS
- legacy-trainer authority tests: 7/7 PASS
- BAMF flow control: PASS
- BAMF flow-control tests: 15/15 PASS
- differential leaf gate: policy skip for this presentation-only change set
- Model Forensics renderer: 368/368 PASS
- Electron security: 53/53 PASS
- Python bridge: 6/6 PASS
- `git diff --check`: PASS

The dedicated closeout contract contributes eight integrated assertions for selector discipline, shell-target ownership, current-to-target inventory closure, target disposition completeness, destination parity, flow/constraint reference integrity, shell localization, and skip-navigation behavior.

## Whole-app browser acceptance

Command:

```sh
BILQIS_PLAYWRIGHT_MODULE=/Users/emilie/Code/mission-control/node_modules/playwright \
BILQIS_AXE_MODULE=/Users/emilie/Code/mission-control/node_modules/axe-core/axe.min.js \
BILQIS_CHROME_PATH='/Applications/Google Chrome.app/Contents/MacOS/Google Chrome' \
node apps/mission-control/tests/browser/closeout-check.cjs
```

The exact renderer is served under its production CSP. Axe is served from the same local origin; the CSP is not weakened for testing.

PASS matrix:

- dark + comfortable desktop: 14/14 destinations
- dark + compact desktop: 14/14 destinations
- light + comfortable desktop: 14/14 destinations
- light + compact desktop: 14/14 destinations
- light + compact at 390 × 844 CSS px: 14/14 destinations
- WCAG 2.0 A/AA, 2.1 A/AA, and 2.2 AA axe rules: zero violations in the matrix
- duplicate owned test IDs: zero
- document-level horizontal overflow: zero
- browser page errors: zero
- keyboard journey: PASS
- expanded-copy + RTL responsive stress: PASS
- forced-colors + reduced-motion representative render: PASS
- Chromium accessibility tree: 914 nodes; `main`, `navigation`, and `heading` roles present; School destination name present

Twenty-nine screenshots were captured and hashed. The machine receipt is `docs/evidence/bamf/GUI1143/browser-result.json`.

## Human visual fence

The final rendered application was inspected across the fourteen desktop destinations plus representative responsive and forced-colors states.

The application now reads as one instrument rather than a collection of independently styled leaves: the shell owns the single destination introduction, analytical destinations use tables/dossiers/graphs with local overflow, action emphasis stays subordinate outside Operate, and defensive states remain visually distinct without taking over the canvas. Corrections and Evidence were adjusted during this pass because their duplicated internal page intros made the integrated application look stitched together even though their leaf tests were green.

No remaining rendered state observed in the final pass requires a redesign repair under the anti-pattern gallery, visual-composition specification, or shared style guide.

## Accepted limitations

- The integrated browser bridge provides the accepted operator snapshot and intentionally rejects unsupported service queries. Capability, Atlas, and Evidence therefore exercise truthful defensive/unavailable states in the whole-app matrix; their richer positive states remain covered by their dedicated leaf fixtures and tests.
- The 390px viewport is a deliberate reflow stress width, not a claim that the Electron window should normally operate at that physical width.
- The accessibility proof uses axe, keyboard interaction, forced-colors/reduced-motion rendering, and Chromium's accessibility tree. It is not a recorded native VoiceOver usability session.
- Browser evidence is fixture/read-only. It performs no trainer mutation and proves no neural-learning outcome.
- The environment's BIOS Work Stack helper could not execute because the required container runtime was unavailable. The structural interruption was nevertheless honored before turn-in, and the durable feature worktree remained the recovery boundary.

No merge was performed.

## Legacy-trainer authority pointer

The legacy-trainer reference above describes a documentation gate. Current
adaptation authority remains `codex/337-replay-349-20261026`, worktree
`/Users/emilie/Code/.worktrees/bilqis-mlx/337-replay-349-20261026`, run
`/Users/emilie/Code/.worktrees/bilqis-mlx/337-replay-349-20261026/runs/microspenics-349-replay`. This UI acceptance record does not select trainer
policy or change that authority.

Static authority annotation (2026-11-15): the canonical preserved adaptation
source above is the source specified by `AGENTS.md`. This clarification repairs
the static source-reference check only; it does not assert a new live inspection
or change the recorded GUI1143 evidence.
