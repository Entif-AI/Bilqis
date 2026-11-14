# Mission Control Visual Composition & Home View Specification

Status: proposed design authority for Mission Control redesign  
Parent authority: GitHub issue #1124  
Canonical machine-readable design system: `apps/mission-control/DESIGN.md`  
Target UI anatomy: `INFORMATION_ATLAS.md`  
Current renderer migration inventory: `CURRENT_STATE_UI_INVENTORY.md`  
Human style guide: `STYLE_GUIDE.md`

## 1. Purpose

This specification converts the Mission Control visual-design critique into implementation-grade rules.

It governs two related things:

1. **application-wide composition practice**: hierarchy, canvas/surface separation, containment, typography, spacing, interaction semantics, responsiveness, accessibility, content economy, and use of visualizations; and
2. **the Mission Control Home view**: the exact information hierarchy and adaptive composition used to answer the operator's first questions about the learner.

The intended result is not a generic SaaS dashboard and not a collage of individually polished components. It is a **calm scientific workstation** whose composition makes the operator's next question visually obvious.

A screenshot should remain intelligible before the viewer reads the copy. The eye should understand:

- what is background canvas;
- what is a primary working surface;
- what is an independent object or stateful unit;
- what is interactive;
- what is status;
- what is secondary;
- what deserves attention now.

The UI MUST feel like one composition, not eight unrelated cards laid on a wallpaper.

Normative terms `MUST`, `SHOULD`, and `MAY` are used deliberately.

---

## 2. Existing visual tokens remain authoritative

This spec does not replace the palette or type system already codified in `DESIGN.md`.

### 2.1 Dark theme

| Role | Token | Value |
| --- | --- | --- |
| Canvas | `colors.canvas` | `#0B0D10` |
| Surface 1 | `colors.surface-1` | `#111418` |
| Surface 2 | `colors.surface-2` | `#171B20` |
| Surface 3 | `colors.surface-3` | `#1E242A` |
| Border | `colors.border` | `#303841` |
| Strong border | `colors.border-strong` | `#53616D` |
| Primary interaction | `colors.primary` | `#7CC8EA` |
| Text | `colors.text` | `#F2F5F7` |
| Muted text | `colors.text-muted` | `#B0BAC2` |
| Faint text | `colors.text-faint` | `#858F98` |

### 2.2 Light theme

| Role | Token | Value |
| --- | --- | --- |
| Canvas | `colors.light-canvas` | `#F4F6F7` |
| Surface 1 | `colors.light-surface-1` | `#FFFFFF` |
| Surface 2 | `colors.light-surface-2` | `#EDF1F3` |
| Surface 3 | `colors.light-surface-3` | `#E2E8EB` |
| Border | `colors.light-border` | `#C5CED4` |
| Strong border | `colors.light-border-strong` | `#7A8994` |
| Primary interaction | `colors.light-primary` | `#176B8D` |
| Text | `colors.light-text` | `#182027` |
| Muted text | `colors.light-text-muted` | `#52616B` |
| Faint text | `colors.light-text-faint` | `#6B7881` |

### 2.3 Typography

The existing semantic scale remains authoritative:

- destination title: 26px / 650;
- section heading: 20px / 650;
- subsection heading: 16px / 650;
- body large: 16px;
- body default: 14px;
- body small: 13px;
- labels/captions: 12px minimum;
- machine data: 13px monospace with tabular/lining numerals;
- primary metric: 24px / 650, used sparingly.

The system font stack in `DESIGN.md` remains the runtime choice. This specification changes **how the roles are composed**, not the font family.

---

## 3. Composition constraints

### CON-D-060 · Canvas and working surfaces MUST be visibly distinct

The application canvas is a substrate, not a card color.

- Dark theme canvas MUST use `colors.canvas`; ordinary independent working surfaces MUST NOT use the same fill.
- Light theme canvas MUST use `colors.light-canvas`; ordinary independent working surfaces MUST NOT use the same fill.
- A primary independent panel placed directly on canvas SHOULD normally use Surface 1.
- A stateful or interactive region inside Surface 1 MAY use Surface 2.
- Surface 3 is reserved for a genuine third layer, selected inset region, or strongly separated local state; it is not a zebra-striping color.
- A bounded card MUST remain visually separable from its parent at 100% zoom in both themes.
- If tonal difference alone is not sufficiently legible, add a structural border. Do not solve separation with a drop shadow.
- A nested bounded surface MUST NOT use the same fill as its parent. If it cannot justify a distinct layer, remove the inner container.

**Acceptance:** no major card/panel may visually dissolve into the canvas or its parent surface.

### CON-D-061 · Cards are independent objects, not default layout primitives

A section does not become a card merely because it has a heading.

Use a bounded card/panel only when the region is at least one of:

- an independently selectable object;
- an independently stateful object;
- a separately actionable unit;
- a persistent comparison object;
- a defensive state requiring containment;
- a floating/overlay plane;
- a bounded object whose internal geometry would otherwise become ambiguous.

Ordinary grouping SHOULD use:

- proximity;
- shared alignment;
- section headings;
- whitespace;
- subtle rules;
- table structure;
- tonal region changes.

A dashboard grid of same-size rounded rectangles is not the default composition.

### CON-D-062 · Visible containment depth is deliberately shallow

- A major working region SHOULD have at most one obvious bounded-container layer in the normal reading path.
- A card-inside-card treatment requires an explicit independent state/interaction reason.
- Three visible nested bounded rectangles are a design defect unless a documented exception proves that each boundary carries distinct semantics.
- When two nested boundaries have the same role, delete the inner one and use spacing.

### CON-D-063 · Visual hierarchy MUST be unequal

The interface MUST visibly answer: **what matters most right now?**

- Primary working content gets the strongest area, contrast, or typographic emphasis.
- Secondary analysis is quieter.
- Tertiary metadata is available but does not compete with the task.
- Sections MUST NOT receive equal visual weight merely because they are siblings in the DOM or atlas.
- A warning/regression region MAY become more prominent than an otherwise primary region when operational state warrants it.
- Healthy/empty secondary regions SHOULD contract or quiet themselves rather than retain full visual weight.

Symmetry is not a higher priority than meaning.

### CON-D-064 · Proximity and whitespace precede borders

Spacing is semantic.

Use the existing rhythm:

- 4px half-step for very close label/value relationships;
- 8px for tightly related inline/stacked controls;
- 12–16px for internal component rhythm;
- 24px for separation between major related groups;
- 32–48px for strong section/canvas separation where the viewport permits.

Rules:

- content with the same meaning is closer than content with different meaning;
- headings MUST bind visually to the content they name;
- unrelated panels MUST NOT appear connected merely because their margins collapse;
- adding a border because spacing is poor is not an acceptable fix.

### CON-D-065 · The view uses a coherent alignment grid

- Major regions SHOULD share column edges.
- Repeated value columns SHOULD align.
- Controls in a row MUST share intentional baselines or centerlines.
- Major regions SHOULD derive from a small number of column spans rather than arbitrary widths.
- A desktop destination SHOULD normally use no more than two primary content columns at once.
- Wide tables are allowed to break the prose grid, but they own their overflow locally.
- Alignment SHOULD remain visible when one sibling is absent.

### CON-D-066 · Persistent shell chrome is subordinate to the task

Before the operator reaches the primary work, the shell may expose only context that genuinely affects the current destination.

The shell MUST NOT become a stack of:

1. nav;
2. context strip;
3. utility strip;
4. explanation strip;
5. oversized destination title;
6. then finally the work.

Specific rules:

- context and investigation controls stay compact;
- inactive utilities do not demand button-level visual weight;
- destination headers use ordinary Title hierarchy, not hero/display treatment;
- secondary shell facts live behind disclosure;
- the main task SHOULD begin within the first normal viewport on supported desktop layouts.

### CON-D-067 · Interaction roles MUST look different before the copy is read

Navigation, filtering, state, actions, and links are different roles.

The visual grammar MUST distinguish:

- navigation destination;
- local peer tab;
- filter;
- segmented mode selection;
- primary action;
- secondary action;
- destructive action;
- object/deep link;
- status badge;
- read-only datum.

Do not make all of these dark rounded rectangles.

Pills are reserved for states/tags/segmented controls where the shape carries category or selection meaning. Ordinary buttons are not pills by default.

### CON-D-068 · Typography establishes structure before boxes do

- Destination titles use the `title` role, not `display`, unless a rare screen has a genuine editorial reason.
- Section titles use `section`.
- Local subheads use `subsection`.
- Ordinary explanatory text uses body roles.
- Machine identifiers use `data`.
- Primary metrics use `metric` only when the number is genuinely one of the few values the operator should perceive immediately.
- All-caps is limited to short state labels/eyebrows.
- Weight is not used to compensate for weak composition.
- Metadata SHOULD use 12–13px roles but MUST remain legible and contrast-compliant; “subtle” is not permission to become faint gray noise.

### CON-D-069 · Numeric information uses comparison-friendly typography

- Tabular numerals are required for aligned metrics, tables, timelines, and comparable deltas.
- Units and denominators remain visible.
- Delta sign and semantic state are not conveyed by color alone.
- Large metric typography is reserved for a small number of true headline readings.
- Do not make every number a KPI tile.

### CON-D-070 · Semantic color is sparse and redundant

The palette remains predominantly neutral.

Semantic colors MAY communicate:

- healthy;
- attention;
- danger/invalidity/regression;
- historical context;
- informational state.

But they MUST be paired with text, icon/shape, structure, or another non-color cue.

Large areas of saturated semantic color are prohibited in normal state. The operator should notice semantic color because it is rare.

### CON-D-071 · Focus is intentionally visible

Keyboard focus MUST remain visibly different from:

- selection;
- hover;
- semantic status;
- active navigation.

Focus may briefly interrupt the aesthetic. Invisible or “tastefully faint” focus is a defect.

### CON-D-072 · Responsive behavior recomposes instead of squeezing

The design MUST be reviewed as a composition at:

- wide desktop;
- medium desktop / narrow laptop;
- the existing ≤980px shell transition;
- high zoom / reflow equivalent;
- long-localized-copy stress;
- relevant RTL layout.

Rules:

- the rail MUST NOT collapse destination names to ambiguous initials;
- two-column work becomes one column according to semantic priority, not DOM accident;
- tables keep local overflow and orientation;
- controls may wrap or regroup rather than truncate;
- the global inspector MUST NOT reduce the remaining workspace below a usable width without switching to an overlay/full-width treatment;
- localization expansion MUST NOT destroy semantic hierarchy.

### CON-D-073 · Content is edited, not merely displayed

Every visible sentence pays rent.

- Remove helper copy that repeats what a heading, state, or layout already says.
- Prefer concise operator language over implementation terminology.
- Do not show explanatory prose permanently when a small disclosure can hold it.
- Do not show raw implementation exceptions as primary copy.
- Do not add a label simply to make a component look complete.

### CON-D-074 · Microvisualizations are allowed only when perception beats reading

A sparkline, micro-bar, or tiny trend visualization MAY be used when:

- direction or shape matters more than a single exact number;
- the compared samples are genuinely comparable;
- the time/scope basis is explicit;
- exact values remain accessible;
- the visualization is not decorative.

Do not add a chart merely to make a dashboard look like a dashboard.

### CON-D-075 · Motion communicates state change, not personality

Motion is restrained and mechanical.

Use it only to:

- reveal/hide a region;
- move focus/inspection planes;
- show state transition;
- preserve spatial continuity.

Respect reduced motion. No bouncing, glowing, sweeping, or decorative animation.

---

## 4. Home view contract

### 4.1 Job of the Home view

Within roughly two seconds, an operator should be able to answer:

1. Is the learner running?
2. Is it learning?
3. Is it regressing?
4. Is it blocked?
5. Is anything invalid?
6. What is it doing right now?
7. What, if anything, requires my attention?

Home is not the place for complete diagnostics. It is the place for **situation awareness and next investigation**.

### CON-D-076 · Home status band uses five state questions

The compact status band MUST contain:

- **Running**
- **Learning**
- **Regression**
- **Blocked**
- **Invalidity**

`Current work` MUST NOT occupy one of these five slots because Current Work already has a dedicated section and is an object/context, not a peer system condition.

Each status shows:

- concise human-readable state;
- non-color cue;
- exact inspect/drill-through affordance only if an owning object exists.

The five statuses form one horizontal band on wide desktop. They are not five independent cards.

### CON-D-077 · Current Work is a focused task region

Current Work shows only what the learner is actively doing:

- target capability;
- strategy;
- candidate intent;
- source family;
- assessment posture;
- exact candidate/episode drill-through when available.

It SHOULD be one coherent region with aligned label/value structure.

It MUST NOT restate general health metrics.

### CON-D-078 · Actionable Attention changes prominence with severity

Actionable Attention is not geometrically democratic with Current Work.

**Healthy / no actionable concern:**
- show a quiet, compact empty/healthy state;
- do not preserve a large empty card.

**Attention present:**
- show prioritized items with kind, reason, owning object, and exact navigation;
- use attention semantics without saturating the whole panel.

**Regression, invalidity, or hard blocker:**
- Actionable Attention becomes the dominant Home region through order, width, tonal separation, or heading emphasis;
- Current Work remains available but becomes secondary.

The layout therefore adapts to operational meaning rather than preserving a fixed equal-card grid.

### CON-D-079 · Learning Pulse is chronology first, chart second

Learning Pulse shows:

- recent accepted/rejected learning events;
- timestamp;
- short outcome;
- exact object link.

A small learning-direction sparkline MAY appear when the underlying samples are genuinely comparable and its scope is explicit.

The sparkline MUST NOT replace the event chronology or exact values.

### CON-D-080 · School Snapshot remains a compact analytical table

School Snapshot uses a real table/grid, not capability cards.

Minimum visible columns:

- Capability
- Now
- Best
- Delta
- Debt
- Retention
- Status

Rules:

- capability identity stays visible;
- rows drill through to Capability Explorer;
- numerals align;
- semantic values are not silently truncated;
- if horizontal overflow is needed, the snapshot owns it locally.

### CON-D-081 · Health Details is collapsed by default

The four supporting health families are:

- Learning health;
- Curriculum health;
- Runtime health;
- System health.

They MUST NOT render as four permanent top-level dashboard cards in normal Home state.

They live behind a clear **Health details** disclosure, collapsed by default.

A severe underlying condition may surface into the five-state status band or Actionable Attention without requiring the disclosure to be opened.

### CON-D-082 · Home canvas composition uses sections before cards

Default wide-desktop composition:

1. compact learner-status band;
2. primary decision row:
   - Current Work;
   - Actionable Attention;
3. secondary analysis row:
   - Learning Pulse;
   - School Snapshot;
4. collapsed Health Details disclosure.

Composition rules:

- the status band may be a borderless/low-boundary tonal region;
- Current Work and Actionable Attention may use distinct Surface 1 panels because they are independent operational units;
- Learning Pulse and School Snapshot SHOULD be grouped by alignment/spacing and MAY use surfaces only where needed for clear ownership;
- Health Details SHOULD read as a disclosure/section, not a large permanent card;
- the canvas MUST remain visually visible between major regions;
- cards/panels MUST use a fill distinct from the canvas;
- nested cards inside these regions are prohibited unless a child is independently stateful/actionable.

### CON-D-083 · Home prominence adapts but reading order stays predictable

Wide desktop default:

- Current Work is primary when the system is healthy.
- Actionable Attention is secondary when empty/healthy.
- When serious attention exists, Actionable Attention becomes primary and may precede Current Work.

Narrow/reflow order:

1. status band;
2. whichever of Actionable Attention / Current Work is currently primary;
3. the other;
4. Learning Pulse;
5. School Snapshot;
6. Health Details.

Adaptive prominence MUST NOT make keyboard/focus order nonsensical. DOM/order strategy must preserve a coherent accessible sequence.

### CON-D-084 · Time Lens means epistemic context, not reporting window

The global Time Lens shows:

- `Current` verified context; or
- an exact historical generation.

It MUST NOT use labels such as `Last 24h` as the global time lens. A rolling reporting window may exist locally inside a trend/chronology control, but it is not the global epistemic context.

### CON-D-085 · Home shell chrome is deliberately compressed

On Home, persistent shell chrome MUST remain visibly subordinate to learner state.

- global context bar: one compact row at wide widths;
- investigation toolbar: terse utility controls, not large button cards;
- destination header: compact title + one concise operator-purpose sentence;
- no additional explanatory banner in the normal verified-live state;
- the learner status band SHOULD appear quickly after the header.

### CON-D-086 · Home avoids equal-weight rectangle wallpaper

At healthy wide-desktop state:

- the main canvas SHOULD NOT show a matrix of same-size rounded cards;
- the first viewport SHOULD contain no more bounded regions than necessary to express independent operational units;
- Health Details is not counted because it is collapsed;
- the status band is a single compositional unit, not five cards;
- a section with no independent state/action SHOULD remain unboxed.

### CON-D-087 · Home remains useful without color

In grayscale / forced colors / color-insensitive inspection, the operator must still distinguish:

- healthy;
- attention;
- regression;
- blocked;
- invalid;
- selected;
- focused;
- disabled;
- historical.

Text, shape, iconography, borders, position, and semantic labeling provide redundant cues.

### CON-D-088 · Home must pass the two-second composition test

A comparative screenshot of the Home view passes only if an informed operator can identify, without reading every label:

- overall learner posture;
- the current primary task/work;
- whether urgent attention exists;
- where recent learning activity lives;
- where curriculum/capability context lives;
- where deeper health detail is available.

If every region has equal visual weight, the test fails.

---

## 5. Surface hierarchy rules

The following is the default visual stack.

| Layer | Typical role | Dark | Light | Border / shadow rule |
| --- | --- | --- | --- | --- |
| Canvas | application substrate | `#0B0D10` | `#F4F6F7` | no border; never a “card” |
| Surface 1 | primary independent work unit | `#111418` | `#FFFFFF` | border optional when tonal edge is clear |
| Surface 2 | selected/inset/stateful subregion | `#171B20` | `#EDF1F3` | structural border MAY reinforce boundary |
| Surface 3 | rare third plane / strong local state | `#1E242A` | `#E2E8EB` | use sparingly |
| Floating plane | inspector/popover/dialog | appropriate surface | appropriate surface | occlusion + border; shadow allowed only if it conveys floating depth |

### 5.1 Non-negotiable canvas/card separation

A bounded region placed on canvas MUST be perceivable as a separate surface through fill and/or structural border.

Prohibited:

- canvas-colored card on canvas distinguished only by radius;
- Surface 1 card inside Surface 1 card with only a border-radius change;
- a dark card whose boundary disappears until hover;
- using shadow as the only edge in the default dark theme;
- four adjacent panels whose fills/borders are so similar that the canvas disappears entirely.

The canvas must remain perceptible as negative space around and between independent work units.

### 5.2 Background continuity

Not every region needs a different fill.

Use one continuous canvas for the page and introduce surfaces only where a semantic boundary exists.

If the page begins to look like a quilt of slightly different gray rectangles, remove surfaces and restore continuous canvas.

---

## 6. Typography and content hierarchy

### 6.1 Type-role discipline

Home should normally use:

- one destination `title`;
- section headings for Current Work, Actionable Attention, Learning Pulse, School Snapshot, Health Details;
- body-md for most operator-facing values/help;
- label/caption for metadata/status qualifiers;
- data role for exact machine identifiers only;
- metric role for at most a few readings whose magnitude is itself the primary message.

### 6.2 Metadata

Metadata is secondary, not disposable.

Do not make large regions of the interface depend on 12px faint-gray text. If metadata is required to interpret the value correctly, it must remain comfortably legible.

### 6.3 Copy economy

Examples of copy that should disappear when redundant:

- “Click to inspect” under an obviously linked object;
- “Current status” above a status already labeled by context;
- repeated “Sort by …” phrases in column headers;
- long explanatory sentences permanently attached to self-explanatory controls.

Use local disclosure for deeper explanation.

---

## 7. Interaction semantics

### 7.1 Navigation

Navigation communicates destination. It must not visually resemble:

- semantic status;
- filters;
- destructive commands;
- ordinary data tags.

### 7.2 Status

Status badges communicate state only. They do not navigate unless a separate, explicit affordance exists.

### 7.3 Links / drill-through

Exact-object drill-through SHOULD read like a relationship to another object, not like a generic command button.

### 7.4 Filters and modes

Filters change a subset. Modes change representation/peer workspace. They use different labels and selected-state grammar.

### 7.5 Actions

Primary action prominence is reserved for the next meaningful action. A screen with six visually primary buttons has no primary action.

---

## 8. Responsive and localization design cases

Each redesigned micro-surface MUST show evidence for the relevant cases:

1. wide desktop;
2. medium desktop / narrow laptop;
3. ≤980px shell transition;
4. high zoom / reflow;
5. long translated strings;
6. RTL where logical properties/order matter;
7. comfortable density;
8. compact density;
9. dark theme;
10. light theme.

Home-specific expectations:

- grouped navigation remains labeled; never initials-only;
- the status band wraps/recomposes without changing the five semantic questions;
- primary/secondary Home regions stack by operational priority;
- School Snapshot scrolls locally if necessary;
- Actionable Attention remains visible when critical;
- Health Details remains a disclosure and does not expand merely because columns collapse.

---

## 9. Accessibility design requirements

Accessibility shapes composition.

- Heading hierarchy follows visual hierarchy.
- Keyboard order follows the meaningful reading/action order.
- Focus remains visible.
- Semantic status never relies on color alone.
- Graphs/tiny visuals have text/value equivalents.
- Data tables retain accessible headers and relationships.
- Disclosure controls expose state.
- Live regions are reserved for meaningful state changes, not noisy metric churn.
- At 200% text or high zoom, critical information is not clipped.
- At reflow widths, the operator does not need two-dimensional page scrolling for ordinary content; wide analytical surfaces may scroll locally.
- Reduced motion removes nonessential transition motion.
- Forced-colors mode retains boundaries, states, controls, and focus.

---

## 10. Home state matrix

| State | Composition change |
| --- | --- |
| Verified live / healthy | Current Work leads; Attention is compact/quiet; Health Details collapsed. |
| Verified live / attention | Attention gains visual weight; status band marks relevant state; exact owner links visible. |
| Regression / invalidity / hard block | Attention becomes primary region; semantic state is explicit in status band; Current Work stays secondary but visible. |
| Startup / no learning telemetry | Normal dashboard is replaced by the dedicated startup state; absence is not rendered as failure. |
| Historical | Time Lens clearly shows exact generation; mutation unavailable; Home summaries are historical and labeled accordingly. |
| Stale / partial | Defensive state grammar indicates freshness/coverage; last verified information may remain only when clearly marked. |
| Offline / unavailable | Recovery guidance replaces unsupported live assumptions; do not synthesize empty/zero state. |

---

## 11. Visual acceptance checklist

A Home-view redesign is not visually accepted until all of the following are true.

### Composition
- Canvas is visibly distinct from bounded surfaces in dark and light themes.
- No major card disappears into the backdrop.
- No same-fill nested card structure remains.
- The page reads as one composition rather than a grid of widgets.
- Major regions share a coherent alignment grid.
- The visual hierarchy is intentionally unequal.

### Hierarchy
- Learner posture is visible first.
- Current Work and serious Attention are the dominant operational regions.
- Health Details is collapsed by default.
- Secondary analysis is quieter than primary operational state.
- Metadata does not compete with headings.

### Interaction
- Navigation, statuses, filters, links, and actions are visually distinguishable.
- Focus is unambiguous.
- No important control depends on hover alone.
- Disabled state is distinct from read-only data and unavailable state.

### Typography
- No ordinary readable UI text is below 12px.
- Tabular data uses comparison-friendly numerals.
- Machine identifiers use monospace only where character identity matters.
- Long semantic values wrap/recompose or disclose; they do not become meaningless ellipses.
- All-caps is sparse.

### Color / surfaces
- Primary accent is scarce.
- Semantic colors are redundant with non-color cues.
- Shadows are absent from ordinary cards/panels.
- Borders are structural rather than decorative.
- Canvas remains visible between independent work regions.

### Responsiveness
- No initials-only navigation.
- No document-level horizontal overflow.
- Wide analytical surfaces own their scroll.
- Long localization does not destroy grouping.
- High zoom/reflow preserves task order and critical state.

### Home-specific
- Status band is Running / Learning / Regression / Blocked / Invalidity.
- Global Time Lens is Current or exact generation, never a rolling reporting window.
- Serious Actionable Attention can outrank Current Work.
- Learning Pulse chronology remains available even when a microtrend is used.
- School Snapshot remains tabular.
- Health Details does not appear as four permanent cards.
- An operator can identify posture, current work, attention, learning activity, curriculum context, and deeper-health entry point in roughly two seconds.

---

## 12. Anti-patterns this spec explicitly forbids

- same-color canvas and cards;
- rounded rectangles used as the default grouping mechanism;
- card-inside-card-inside-card compositions;
- equal visual weight for every section;
- four “health” cards permanently occupying Home;
- a status strip containing `Current Work` as if it were a peer health condition;
- global Time Lens labels such as `Last 24h`;
- gray microcopy that is technically present but practically unreadable;
- pill proliferation;
- navigation/filter/status/action controls sharing one undifferentiated button style;
- giant destination headings;
- stacked shell chrome that delays the actual task;
- decorative charts;
- a chart without exact accessible values;
- saturation used to create drama;
- hidden focus;
- responsive squeezing instead of recomposition;
- initials-only navigation;
- raw implementation errors as operator copy;
- a dashboard that still looks like eight unrelated widgets after all text is blurred out.

---

## 13. Evaluation scenarios

### EVAL-D-001 · Healthy live Home
Given verified live context with no urgent concern, the screenshot should read:
1. learner posture;
2. current work;
3. recent learning / curriculum context;
4. optional deeper health.

Attention is present but quiet.

### EVAL-D-002 · Regression Home
Given an active regression with exact owning evidence, Actionable Attention becomes the visual priority without turning the whole screen red. The status band shows Regression clearly and the exact owner is one action away.

### EVAL-D-003 · Hard blocker Home
Given a hard blocker, Blocked becomes an explicit status. The blocker reason and owning object are visible in Attention. Current Work remains visible as context but does not outrank the blocker.

### EVAL-D-004 · Dark-theme surface separation
At 100% zoom on a typical desktop display, canvas, Surface 1, and any necessary Surface 2 region remain visually distinguishable without relying on shadows.

### EVAL-D-005 · Light-theme surface separation
The same hierarchy remains obvious in light theme; white Surface 1 does not disappear into the light canvas.

### EVAL-D-006 · Blur test
When screenshot text is blurred beyond readability, the composition still reveals:
- shell versus canvas;
- primary versus secondary regions;
- interactive/control clusters;
- major grouping;
- operational attention priority.

### EVAL-D-007 · Long-copy stress
With expanded localization strings, no critical status, capability, action, or reason is silently truncated into a meaningless fragment.

### EVAL-D-008 · Narrow/reflow Home
At narrow/reflow width, the operationally primary region appears before the secondary region, School Snapshot owns any horizontal overflow, and no global page horizontal scrolling is introduced.

---

## 14. Implementation handoff

This is a Design contract, not an implementation prescription.

Implementation leaves MUST:

1. consult this spec together with `DESIGN.md`, `STYLE_GUIDE.md`, `INFORMATION_ATLAS.md`, and `CURRENT_STATE_UI_INVENTORY.md`;
2. preserve existing authority/state semantics;
3. use the existing token roles rather than inventing local grays, radii, or type scales;
4. record retain/transform/merge/move/remove disposition for current substrate;
5. produce before/after visual evidence;
6. verify the applicable evaluation scenarios;
7. append any newly discovered contradiction/deficiency to #1124 before silently improvising.

The goal is not “make every component prettier.”

The goal is: **make the entire workstation compose itself around the operator's question.**
