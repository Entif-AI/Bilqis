# Model Forensics redesign requirement trace

Parent authority: GitHub issue #1124
Purpose: literal trace from the controlling user instruction to durable artifacts and execution gates.

This file exists because the first design-authority assembly preserved the spirit of #1124 while missing several literal requirements. It is the checklist that prevents a second drift.

## Trace matrix

| ID | Controlling requirement | Durable implementation / owner | Status |
| --- | --- | --- | --- |
| REQ-D-001 | Write design/aesthetic rules and a broader style guide derived from the failures but generalized beyond them. | `STYLE_GUIDE.md`, `DESIGN.md`, `ANTI_PATTERN_GALLERY.md` | SATISFIED |
| REQ-D-002 | Create `DESIGN.md` matching the Google Labs standard and internal guidance. | `apps/mission-control/DESIGN.md`; Google linter is required in validation. | SATISFIED |
| REQ-D-003 | Build a hierarchical atlas beginning with app-shell segments, descending through views and components. | `INFORMATION_ATLAS.md` is the target-state shell + 14-view anatomy; `CURRENT_STATE_UI_INVENTORY.md` separately preserves the current renderer substrate. | REPAIRED AGAIN AFTER D-029 |
| REQ-D-004 | The atlas is a readable tree view, not only prose hierarchy. | One Mermaid `flowchart TB` per shell/view in `INFORMATION_ATLAS.md`; cross-view flows remain separate. | REPAIRED AGAIN AFTER D-029 |
| REQ-D-005 | Each component charts its intended constituents plus treatment, interaction, and effect below it rather than stopping at subsystem-sized labels. | Target components/subcomponents are charted in flowcharts; the detailed register records information, treatment, interaction, effect, and source disposition. | REPAIRED AGAIN AFTER D-029 |
| REQ-D-006 | Use the current design to formulate the redesign artifacts without confusing current presence with target intent. | `CURRENT_STATE_UI_INVENTORY.md` preserves current truth; `INFORMATION_ATLAS.md` decides what the new UI intends to show. | REPAIRED AGAIN AFTER D-029 |
| REQ-D-007 | Keep cross-view flows separate so the main tree does not become spaghetti. | `FLOWS.md`, FLOW-D-001..018. | SATISFIED |
| REQ-D-008 | Use the current design as substrate; do not throw away the prior multi-agent work. | Constraint register, atlas, program, and all child leaves preserve behavior/code by default. | SATISFIED |
| REQ-D-009 | Maintain a running GitHub issue as durable deficiency storage while assembling artifacts. | #1124 comments D-001 onward. | SATISFIED |
| REQ-D-010 | Decompose work into targeted surgical micro-redesigns. | #1126..#1143; `REDESIGN_PROGRAM.md`. | SATISFIED |
| REQ-D-011 | Preserve existing tests/code as much as possible. | CON-D-030 and every child shared contract. | SATISFIED |
| REQ-D-012 | Run only the smallest tests relevant to each targeted alteration. | CON-D-030/031; per-leaf shared contract; final integrated pass separated. | SATISFIED |
| REQ-D-013 | Agents continuously consult style guide and `DESIGN.md`. | Every child issue shared contract plus `REDESIGN_PROGRAM.md`. | SATISFIED |
| REQ-D-014 | Agents may make spec-conformance refinements outside explicitly enumerated ticket defects. | CON-D-052; corrected `REDESIGN_PROGRAM.md`; child shared contract. | REPAIRED |
| REQ-D-015 | Review each micro-view for WCAG 2.2 AA incrementally. | CON-D-010; every child shared contract. | SATISFIED |
| REQ-D-016 | Run whole-app accessibility/visual acceptance once, after all redesign leaves land. | #1143 only; program Tier 6. | SATISFIED |
| REQ-D-017 | Convert all human-facing text strings to replacement/localization tokens during the redesign. | CON-D-026; each shell/view leaf sweeps its entire owned surface; #1143 proves global residue is zero. | REPAIRED |
| REQ-D-018 | All application UI tests use exact or intentional-prefix `data-test-id` selectors, never text/DOM/class/ID/incidental attrs. | CON-D-027/028; each leaf sweeps every UI selector in its owned surface; #1143 proves global conformance. | REPAIRED |
| REQ-D-019 | Every exact `data-test-id` identifies one rendered element; groups use a documented prefix. | CON-D-028; style guide Testing Hooks; #1143 uniqueness check. | SATISFIED AS TARGET |
| REQ-D-020 | Agree on aesthetics, palette, design-library choices before going further. | #1124 section now explicitly marked proposed; CON-D-053 blocks runtime implementation. | **PENDING HUMAN RATIFICATION** |
| REQ-D-021 | Codify the agreed decisions and the user's instructions verbatim in the parent issue. | User instruction is verbatim in #1124; proposed rules are codified but cannot become “locked” until REQ-D-020 is ratified. | PARTIAL / GATED |
| REQ-D-022 | Use prior screenshot failures as exact examples. | `ANTI_PATTERN_GALLERY.md` restores every exact example recoverable from durable repository/#1124 evidence. | PARTIAL: SOURCE GAP |
| REQ-D-023 | Do not limit good/bad-design guidance to the approximately 100 observed failures. | `DESIGN.md`, `STYLE_GUIDE.md`, constraints generalize structural positive rules. | SATISFIED |
| REQ-D-024 | The atlas must recurse below subsystem-sized target components until the intended UI no longer contains a separately meaningful element/control/state/interaction/effect below the node. | CON-D-054; target flowcharts and register in `INFORMATION_ATLAS.md`; **no fixed maximum depth**. | REPAIRED AGAIN AFTER D-032 |
| REQ-D-025 | The atlas describes **everything intended to show up or operate in the new UI**, not everything that happens to exist in the current renderer. | `INFORMATION_ATLAS.md` target authority + `CURRENT_STATE_UI_INVENTORY.md` migration evidence. | SATISFIED |
| REQ-D-026 | Mermaid atlas diagrams use readable left-to-right flowchart style rather than mind-map or top-to-bottom rendering. | 15 separate `flowchart LR` diagrams in `INFORMATION_ATLAS.md`. | SATISFIED |
| REQ-D-027 | Current UI atoms with no target purpose are removed instead of preserved as target components. | Target exclusion section and CON-D-057/058. | SATISFIED |
| REQ-D-028 | The standalone `B` mark has no target-state job and is removed from the redesigned shell. | `INFORMATION_ATLAS.md`, `STYLE_GUIDE.md`, `DESIGN.md`, CON-D-057. | SATISFIED |
| REQ-D-029 | The atlas authoring model itself must be recursive and may not impose a hidden one-tier or N-tier ceiling. | `INFORMATION_ATLAS.md` now contains recursive target descendants through the depth actually required; CON-D-059. | SATISFIED |
| REQ-D-030 | Codify the dashboard-specific and general visual-design recommendations as implementation-grade authority rather than leaving them in chat. | `VISUAL_COMPOSITION_SPEC.md`; CON-D-060..088; DESIGN.md/style-guide references. | SATISFIED |
| REQ-D-031 | Ensure simple visual physics such as canvas/card separation are explicit and testable. | CON-D-060..062 plus the spec surface hierarchy and acceptance checklist. | SATISFIED |

## Known source gap

#1124 refers to an approximately 100-item screenshot review from the originating conversation. The current public repository contains durable visual-QA measurements, owner-rejection findings, and several exact screenshot-derived strings/failure classes, but it does not contain the original complete chat-only image set/itemized ~100-entry ledger.

The redesign authority therefore:

1. preserves every exact example that can be grounded in durable current evidence;
2. explicitly records that the durable corpus is incomplete;
3. does **not** invent the missing items or pretend a compressed category list is equivalent;
4. treats any recovered original screenshot evidence as append-only input to `ANTI_PATTERN_GALLERY.md` and #1124.

## Implementation gate

Runtime Model Forensics redesign work, beginning with #1126, is blocked until **REQ-D-020** is explicitly ratified by the human operator in durable project authority.

Ratification should cover, at minimum:

- calm scientific workstation as the north star;
- dark-first graphite palette with equivalent light theme and one scarce cool interaction accent;
- semantic status colors never acting alone;
- whitespace/typography/alignment/tonal depth before borders/shadows;
- modest radii and pills only where shape carries meaning;
- 8px rhythm with 4px half-step;
- semantic typography and 12px minimum ordinary readable UI text;
- no silent semantic truncation;
- task-first progressive disclosure;
- atlas-derived navigation grouping;
- one application-wide status grammar;
- restrained mechanical motion;
- existing vanilla HTML/CSS/JS runtime retained;
- external systems such as Carbon used only as references unless Architecture separately approves dependency adoption.
