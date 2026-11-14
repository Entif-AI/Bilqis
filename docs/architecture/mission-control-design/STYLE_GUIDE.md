# Bilqis Mission Control style guide

Status: human-facing design constitution
Parent authority: GitHub issue #1124
Normative token source: `apps/mission-control/DESIGN.md`
Constraint trace: `CONSTRAINT_REGISTER.md`
Exact screenshot-derived examples: `ANTI_PATTERN_GALLERY.md`

## The object we are designing

Mission Control is a **calm scientific workstation**. Imagine a high-end benchtop research instrument whose display has been composed by someone who also knows how to lay out a good scientific figure. The operator is technically sophisticated, but sophistication is not permission to make every screen look like a terminal dump.

The product should feel:

- exact without being brittle;
- dense when the task requires density, not everywhere by default;
- quiet enough that a warning actually has visual weight;
- trustworthy under partial, stale, historical, and failed conditions;
- fast to scan in two seconds, deep enough to investigate for twenty minutes.

The product should not feel like cyberpunk set dressing, a generic SaaS metric dashboard, a consumer preference panel, or a stack of debugging cards that accidentally became a desktop application.

## The design hierarchy

When a screen is opened, the eye should find these layers in order:

1. **Where am I?** Persistent shell context and destination identity.
2. **What is this for?** One concise operator-facing purpose and current posture.
3. **What is the work?** The dominant table, graph, form, timeline, comparison, or command surface.
4. **What supports that work?** Filters, local status, summary measures, and relevant guidance.
5. **What can I inspect?** Secondary analysis, comparison, history, and related objects.
6. **What is the exact evidence?** Receipts, hashes, provenance, raw payloads, and implementation diagnostics.

Lower layers may become primary when the destination itself is Evidence or Operate. Progressive disclosure is task-relative, not a rule that raw information is always hidden.

## Composition before decoration

Before adding a border, badge, card, shadow, stripe, color, or icon, ask whether spacing, alignment, typography, ordering, and disclosure can solve the problem.

Use cards only for genuinely independent stateful objects. Ordinary document sections do not need a rectangle. A panel may own a border because it is a distinct operational region; a heading-plus-table usually does not need another box around it.

One screenshot should make compositional sense before the viewer reads any text. If every region has equal visual weight, the composition has failed even if every individual control is technically consistent.

## Palette

The canonical values live in `DESIGN.md`. The operating rules are:

- graphite surfaces form a quiet luminance ladder;
- the cool primary accent is scarce and means interaction/selection, not “interesting”;
- semantic colors mark health, attention, danger/invalidity, historical context, and information;
- color is always paired with text, shape, marker, border treatment, iconography, or another non-color cue;
- light mode preserves the same hierarchy instead of naively inverting dark mode;
- focus and selection remain distinguishable;
- gradients, glows, neon, decorative stripes, and wallpaper-like patterns are out.

Scarcity is part of meaning. If every panel is blue, blue stops communicating anything.

## Typography

Typography is semantic.

- **Display**: rare page-level moments only.
- **Title**: normal destination title.
- **Section / subsection**: hierarchy inside the working surface.
- **Body**: explanations, guidance, ordinary values.
- **Label / caption**: concise metadata, table headers, status support.
- **Data**: hashes, IDs, receipts, code, raw payloads, exact addresses.
- **Metric**: a small number of genuinely primary quantitative readings.

Sentence case is the default. Short state tags and eyebrows may use uppercase when scan speed benefits. Paragraph-length uppercase copy is prohibited.

Do not make everything bold. If a screen requires bold type on nearly every line to establish hierarchy, the layout has failed.

No ordinary readable UI text is smaller than 12px. Density modes may reduce padding and row height; they do not erase type hierarchy or turn prose into microprint.

## Exact values and truncation

Meaning wins over geometry.

Never silently collapse an operator-significant semantic value into a fragment such as:

- `AWAITING_RECO...`
- `paired-screen:so...`
- `BOOLEAN F...`

Resolve pressure in this order:

1. recompose or widen;
2. wrap at semantic boundaries;
3. progressively disclose;
4. provide an explicit full-value inspection affordance.

Long hashes and machine digests may use a documented middle ellipsis when the exact value is one action away and available to assistive technology.

## Spacing and alignment

Use the 8px rhythm with a 4px half-step from `DESIGN.md`.

Related items sit closer together than unrelated items. Empty space is not unused screen real estate; it is the main way the workstation tells the eye which things belong together.

Controls sharing a row must share a deliberate baseline or centerline. “Almost aligned” is a defect because it makes an otherwise precise interface feel improvised.

Responsive layouts recompose. They do not squeeze a wide desktop design until labels wrap into accidental two-line buttons and values disappear.

## Shell and navigation

The shell earns permanent space only with information that matters across destinations.

Run identity, time posture, freshness, and genuinely global command context belong there. Secondary topology, Factory, semantic release, lease, coverage, and resource facts may be available through a compact disclosure instead of occupying every screen at all times.

Navigation is an information architecture, not a vertical dump of every implemented view. The current fourteen destinations remain addressable, but visual grouping should be derived from the atlas and recurring operator workflows.

Selection must be unmistakable without making the selected nav button the loudest rectangle in the application.

## Controls

Canonical controls share geometry, focus treatment, disabled treatment, and pressed semantics. Their roles remain visibly distinct:

- navigate;
- filter;
- group;
- compare;
- export/copy;
- inspect;
- primary action;
- destructive or mutating action;
- status.

A horizontal row of identical dark rectangles with different verbs is not an action hierarchy.

Comfortable density must actually be comfortable. Compact mode is for deliberate high-density inspection and must remain readable and operable.

## Tables, matrices, and dense analytical surfaces

Treat tables as instruments.

- use concise headers;
- expose sort state without repeating “Sort by” in every heading;
- keep identity columns visible when horizontal comparison would otherwise destroy orientation;
- use sticky headers when vertical scan length warrants it;
- let the table own horizontal overflow and make that overflow discoverable;
- disclose optional secondary columns instead of exposing every possible field simultaneously;
- preserve denominators and units;
- never clip family/group labels into meaningless fragments;
- keep exact evidence available without forcing it into every row.

A wide table is allowed to be wide. The page is not allowed to become accidentally wide.

## Status and defensive states

Mission Control has one visual grammar for state:

1. concise human-readable label;
2. a non-color structural cue;
3. optional explanation or recovery action.

Domain states remain distinct even when they share the grammar. Empty is not unavailable. Denied is not revoked. Partial is not stale. Outcome unknown is not failed.

Defensive presentation should be calm and actionable. Alarmist decoration is counterproductive in an operator workstation because it makes every exception look equally catastrophic.

## Guidance

Guidance belongs next to the concept it explains.

Prefer:

- a short first-use expansion;
- one sentence of nearby helper text;
- an accessible disclosure for deeper explanation;
- a link/jump to exact evidence when appropriate.

Avoid giant glossary strips stretching across the application. Essential guidance may not exist only on hover.

Operator language comes first. Implementation language may follow at inspection depth.

Every view should quickly answer:

1. What am I looking at?
2. Why does it matter?
3. What can I do here?
4. What state is it in?

## Inspector, compare, pins, annotations, and evidence

The inspector is the global path from summary to exact object detail. It may expose ownership, evidence, pinning, comparison, and annotation, but it should not turn every destination into a permanent forensic wall.

Compare is context-sensitive. A comparison across different run/generation/kind identities must state that mismatch rather than visually implying equivalence.

Pins preserve exact object context. Notes are explicitly non-authoritative operator metadata. Evidence remains the destination for literal provenance and payload inspection.

## Operate

Operate should feel like crossing a deliberate boundary.

The sequence is:

1. choose an action;
2. enter exact parameters;
3. run read-only preflight;
4. review target and consequence;
5. authorize the exact reviewed mutation when required;
6. observe receipt/readback;
7. reconcile uncertainty instead of guessing.

Mutation may be visually serious without becoming theatrical. The strongest visual emphasis belongs at the moment where a human is binding themselves to an exact reviewed consequence.

## Accessibility

WCAG 2.2 AA is an input to every leaf, not a final polish stage.

Preserve and extend the existing keyboard/focus/live-region/graph-equivalence/reduced-motion/forced-colors behavior. For each touched micro-surface, review the applicable criteria including:

- keyboard reachability and order;
- visible focus and Focus Not Obscured;
- accessible names, roles, descriptions, and state;
- text and non-text contrast;
- non-color state cues;
- target size;
- 200%/400% zoom, reflow, and text spacing;
- hover/focus-disclosed content;
- reduced motion;
- error identification and recovery;
- screen-reader reading order;
- equivalent representation for complex visualization.

## Internationalization

Every human-facing string in a redesign leaf's owned micro-surface moves behind a stable localization key during that leaf, including copy not otherwise changed for layout. The final application target is complete Mission Control human-copy coverage, not “only whatever happened to be edited.”

Do not concatenate translated sentence fragments. Pass variables as named parameters. Do not translate machine identifiers, source-authoritative values, CSS tokens, or test IDs.

Design for string expansion. Prefer logical CSS properties so future RTL does not require architectural surgery.

## Testing hooks

`data-test-id` is a dedicated test namespace.

- exact IDs point to one rendered element;
- groups use documented prefixes;
- IDs are semantic, stable, nonlocalized, and independent of DOM order or copy;
- functional `data-*` attributes remain implementation state, not test selectors;
- every UI test that selects rendered elements in the leaf's owned micro-surface migrates off text, classes, element IDs, DOM ancestry, localized strings, and incidental attributes, even if that selector was not otherwise touched by the visual change.

## Motion

Motion is mechanical and brief, generally 100–180ms for direct feedback. Use it only to clarify relationship, state change, panel arrival, or focus movement.

Nothing bounces, overshoots, glows, or drifts merely to make the UI feel alive. Under `prefers-reduced-motion`, nonessential motion disappears.

## Comparative acceptance

A redesign leaf is not complete because automated tests pass.

Acceptance requires before/after rendered evidence showing that the touched surface improved:

- task hierarchy;
- composition and alignment;
- state clarity;
- responsive behavior;
- dark/light equivalence;
- comfortable/compact density;
- accessibility;
- localization resilience;
- test-hook discipline;
- defensive-state behavior.

The final whole-app pass happens once after the surgical leaves integrate.

## Anti-pattern gallery

The screenshot failures that triggered this program are concrete evidence, not the limit of the guide. `ANTI_PATTERN_GALLERY.md` preserves the recoverable exact examples and their owning rules. The list below is only the compact mnemonic:

- clipped semantic values and meaningless ellipses;
- group names truncated into fragments;
- shell chrome consuming the task;
- four layers of bordered rectangles;
- tiny metadata everywhere;
- giant pseudo-glossary ribbons;
- all-caps prose;
- indiscriminate bold;
- decorative pattern noise;
- raw implementation exceptions as primary copy;
- unrelated actions styled identically;
- wide tables with invisible overflow;
- every possible column displayed at once;
- repeated verbose sort labels;
- same-row controls with mismatched vertical geometry;
- per-view reinvention of cards, statuses, tabs, and filters.

The positive rule beneath all of them is simpler: **show the operator the right thing at the right depth, with enough visual restraint that meaning remains the loudest signal.**
