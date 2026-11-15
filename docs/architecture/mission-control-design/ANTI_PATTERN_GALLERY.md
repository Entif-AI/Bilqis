# Admin Main Frame screenshot-derived anti-pattern gallery

Status: exact-example evidence companion to \`STYLE_GUIDE.md\`
Parent authority: GitHub issue #1124
Durable source: \`docs/evidence/bamf/GUI-POLISH-1121/visual-qa.md\` plus the screenshot-derived deficiencies preserved in #1124

## Evidence integrity

#1124 instructs the redesign to use the failures found in the prior screenshots as **exact examples** while generalizing beyond them. The earlier style guide compressed those failures into a short category list. That compression lost useful specificity.

This file restores the exact screenshot-derived defects that are currently durable in the public repository record. #1124 also refers to an approximately 100-item screenshot review from the originating conversation. The original chat-only screenshots/itemized ledger are not presently checked into this repository, so this file does **not** pretend the durable subset below is the full original corpus. The missing durable capture is itself a tracked redesign deficiency.

Future screenshot review findings should be appended here with:

- exact view and viewport;
- exact visible failure;
- why the failure harms the operator;
- governing positive rule;
- owning atlas node / redesign leaf;
- before/after evidence reference when available.

## Exact examples

### AP-D-001 · Shell width changed between destinations

- Exact observed failure: Admin Main Frame rail measured **176 px** while non-Home destinations measured **220 px** at the same viewport.
- Why it failed: navigation caused the entire workspace to jump horizontally.
- Rule: persistent shell geometry must be stable at a given viewport.
- Owner: SHELL-D-001 / COMP-D-001 / #1127.

### AP-D-002 · Context chrome consumed different vertical space by destination

- Exact observed failure: Home context bar measured **135 px** while non-Home measured **150 px** before the first repair.
- Why it failed: the task surface moved vertically between destinations and the shell felt assembled from separate pages.
- Rule: shell context is persistent infrastructure, not view-local decoration.
- Owner: COMP-D-002 / #1127.

### AP-D-003 · Landing-page typography crowded out operator work

- Exact observed failure: common non-Home destination H1s rendered at **64 px**.
- Why it failed: a dense technical workstation spent premium vertical space announcing the page instead of exposing the work.
- Rule: destination titles orient; they do not perform a hero moment.
- Owner: COMP-D-005 / #1127.

### AP-D-004 · Page gutters wasted working width

- Exact observed failure: common non-Home inline page gutter measured **88 px**.
- Why it failed: tables and evidence were compressed while unused margin dominated the frame.
- Rule: whitespace is semantic structure, not an automatic luxury margin.
- Owner: COMP-D-005 plus each view / #1127 and destination leaves.

### AP-D-005 · School made the whole document wide

- Exact observed failure: School produced approximately **1021 px** of document-level horizontal overflow even though the matrix had its own intended scroller.
- Why it failed: the operator lost global orientation and the shell itself became horizontally unstable.
- Rule: wide analytical surfaces own their overflow; the document does not.
- Owner: VIEW-D-002 / COMP-D-201 / #1130.

### AP-D-006 · Long pages stretched the navigation rail with the document

- Exact observed failure: Teacher rail reached roughly **3210 px** and SÍ SÉ SON roughly **5326 px**; the Command utility was pushed below the viewport.
- Why it failed: global navigation became dependent on content length.
- Rule: persistent shell controls remain viewport-bound.
- Owner: COMP-D-001 / #1127.

### AP-D-007 · \`UNAVAILABLE\` broke mid-token

- Exact observed failure: Home allowed short semantic states such as \`UNAVAILABLE\` to wrap/break because the value column used \`overflow-wrap:anywhere\`.
- Why it failed: a state token became visually ambiguous to save a few pixels.
- Rule: operator-significant semantic values are never sacrificed to geometry.
- Owner: VIEW-D-001 / #1129.

### AP-D-008 · Domain CSS silently mutated global shell chrome

- Exact observed failure: Capability Explorer and Frame Explorer contained unscoped \`.context-bar\` / \`.context-actions\` rules while their stylesheets were globally loaded.
- Why it failed: entering one destination changed shared shell presentation.
- Rule: shared shell primitives have one owner; destination CSS cannot redefine them by accident.
- Owner: #1126 / #1127.

### AP-D-009 · Undefined visual variables caused dropped declarations

- Exact observed failure: Corrections, Evidence, and SÍ SÉ SON referenced legacy CSS variables absent from the active token surface.
- Why it failed: browser fallback behavior silently altered intended presentation.
- Rule: canonical design tokens are explicit, finite, and mechanically checkable.
- Owner: #1126 plus #1137/#1138/#1141.

### AP-D-010 · Teacher cards packed more information than their geometry could support

- Exact observed failure: strategy cards used three metric columns plus flex history rows inside cards too narrow for the content.
- Why it failed: comparison density became visual compression rather than useful information density.
- Rule: a comparison surface earns width; do not force a dashboard-card grid when the information wants a table or fewer columns.
- Owner: VIEW-D-008 / #1136.

### AP-D-011 · A nominal type system was not an actual invariant

- Exact observed failure: after a “shared type scale” pass, domain stylesheets still declared many independent literal font sizes.
- Why it failed: token names existed, but rendered typography still drifted by view.
- Rule: design-system rules must be observable invariants, not vocabulary layered over exceptions.
- Owner: #1126 and all destination leaves.

### AP-D-012 · Empty shell facts still consumed layout

- Exact observed failure: the no-snapshot context header retained an empty context-facts column, wrapping \`No verified snapshot\` awkwardly while leaving unused horizontal space.
- Why it failed: absent information still dictated geometry.
- Rule: defensive/empty states recompose; they do not reserve phantom content.
- Owner: COMP-D-002 / STATE-D-004 / #1127.

### AP-D-013 · Same-row controls did not share a baseline

- Exact observed failure: selectors, freshness pills, and buttons occupied visibly different vertical positions in one horizontal row.
- Why it failed: the interface looked improvised despite individually valid controls.
- Rule: siblings in a row share deliberate geometry and alignment.
- Owner: #1126 / #1127.

### AP-D-014 · “Scientific visual language” components still spoke different visual dialects

- Exact observed failure: the metric tile and comparison card used different markup and numeric-emphasis grammars even while presented as one reusable catalog.
- Why it failed: the catalog demonstrated inconsistency rather than a component system.
- Rule: reusable primitives share structure before variants add meaning.
- Owner: #1126.

### AP-D-015 · Zero page overflow was mistaken for visual acceptance

- Exact observed failure: earlier acceptance claimed normalization after all views reached zero document-level X overflow and shared geometry, yet owner screenshots still showed inconsistent hierarchy, baselines, cards, and density.
- Why it failed: layout metrics proved containment, not composition quality.
- Rule: automated geometry is a guardrail; comparative rendered review decides visual acceptance.
- Owner: every leaf and #1143.

### AP-D-016 · Inline glossary strips became another layer of chrome

- Exact observed failure: explanatory surfaces added to dense domains solved missing definitions by placing glossary-like material directly into the main reading path.
- Why it failed: help became persistent visual mass and competed with the work.
- Rule: contextual guidance is local and progressively disclosed; do not build giant pseudo-glossary ribbons.
- Owner: style guide; applicable destination leaves.

### AP-D-017 · Implementation failure leaked into operator copy

- Exact observed failure: Evidence exposed \`api.query is not a function\`.
- Why it failed: the operator saw an implementation exception instead of the actual operational condition.
- Rule: operator language first; implementation detail belongs at forensic depth.
- Owner: VIEW-D-013 / #1141.

### AP-D-018 · \`AWAITING_RECO...\` destroyed the state

- Exact screenshot-derived example preserved by #1124: \`AWAITING_RECO...\`.
- Why it failed: truncation removed the semantic distinction the operator needed.
- Rule: widen, wrap, disclose, or provide exact-value inspection before truncating semantic state.

### AP-D-019 · \`paired-screen:so...\` destroyed an identity

- Exact screenshot-derived example preserved by #1124: \`paired-screen:so...\`.
- Why it failed: a meaningful object/strategy/identity label became an arbitrary prefix.
- Rule: semantic identity is not decorative text.

### AP-D-020 · \`BOOLEAN F...\` destroyed a capability/family label

- Exact screenshot-derived example preserved by #1124: \`BOOLEAN F...\`.
- Why it failed: a family/group label ceased to orient the user.
- Rule: grouping labels must remain whole enough to carry meaning.

### AP-D-021 · Too many nested bordered rectangles flattened hierarchy

- Exact failure class preserved by #1124: repeated card/panel/border nesting, in some screenshots reaching roughly four visible containment layers.
- Why it failed: every region shouted “separate object,” so actual hierarchy disappeared.
- Rule: spacing, alignment, typography, and tonal layers come before borders.

### AP-D-022 · Tiny metadata proliferated instead of being prioritized

- Exact failure class preserved by #1124: dense views used very small metadata across large portions of the frame.
- Why it failed: everything became technically present but nothing was comfortably readable.
- Rule: ordinary readable UI copy stays at or above the design minimum; density reduces space before it erases legibility.

### AP-D-023 · Unrelated actions looked interchangeable

- Exact failure class preserved by #1124: filtering, grouping, export, destructive/mutating, and navigation actions appeared as similar dark rectangles.
- Why it failed: verb text carried the entire action hierarchy.
- Rule: role is visible before the label is read.

### AP-D-024 · Wide analytical surfaces hid the existence of more columns

- Exact failure class preserved by #1124: wide tables had local overflow but weak or invisible scroll affordance.
- Why it failed: information existed off-screen without a clear cue that the surface continued.
- Rule: local overflow must be discoverable and preserve orientation.

### AP-D-025 · Too many columns were exposed simultaneously

- Exact failure class preserved by #1124: dense matrices displayed secondary fields by default simply because they existed.
- Why it failed: comparison width and scan speed collapsed.
- Rule: expose the columns required for the current analytical question; disclose secondary columns deliberately.

### AP-D-026 · Sort controls repeated verbose instructional copy

- Exact failure class preserved by #1124: headers repeated phrases equivalent to “Sort by …” rather than exposing concise column identity plus sort state.
- Why it failed: interaction chrome outweighed the data.
- Rule: table controls stay terse and stateful.

## Generalization rule

These examples are evidence, not a finite blacklist. An agent must ask what structural mistake produced the visible failure and apply the positive rule to analogous surfaces even when the new defect is not one of the examples above.
