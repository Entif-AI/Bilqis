---
version: alpha
name: Bilqis Mission Control
description: Calm scientific workstation for inspecting and operating the Bilqis learner with progressive disclosure, evidence-first semantics, and defensive-state clarity.
colors:
  primary: "#7CC8EA"
  on-primary: "#071117"
  canvas: "#0B0D10"
  surface-1: "#111418"
  surface-2: "#171B20"
  surface-3: "#1E242A"
  border: "#303841"
  border-strong: "#53616D"
  text: "#F2F5F7"
  text-muted: "#B0BAC2"
  text-faint: "#858F98"
  healthy: "#78C89D"
  attention: "#D6AB62"
  danger: "#E1848D"
  historical: "#C4A873"
  info: "#8AAFE0"
  focus: "#BCE9FA"
  light-primary: "#176B8D"
  light-on-primary: "#FFFFFF"
  light-canvas: "#F4F6F7"
  light-surface-1: "#FFFFFF"
  light-surface-2: "#EDF1F3"
  light-surface-3: "#E2E8EB"
  light-border: "#C5CED4"
  light-border-strong: "#7A8994"
  light-text: "#182027"
  light-text-muted: "#52616B"
  light-text-faint: "#6B7881"
  light-healthy: "#276B4A"
  light-attention: "#7D581C"
  light-danger: "#983B46"
  light-historical: "#6F5630"
  light-info: "#315E8B"
  light-focus: "#0E5775"
typography:
  display:
    fontFamily: "ui-sans-serif, system-ui, -apple-system, BlinkMacSystemFont, Segoe UI, sans-serif"
    fontSize: 30px
    fontWeight: 650
    lineHeight: 1.1
    letterSpacing: -0.02em
  title:
    fontFamily: "ui-sans-serif, system-ui, -apple-system, BlinkMacSystemFont, Segoe UI, sans-serif"
    fontSize: 26px
    fontWeight: 650
    lineHeight: 1.15
    letterSpacing: -0.015em
  section:
    fontFamily: "ui-sans-serif, system-ui, -apple-system, BlinkMacSystemFont, Segoe UI, sans-serif"
    fontSize: 20px
    fontWeight: 650
    lineHeight: 1.2
    letterSpacing: -0.01em
  subsection:
    fontFamily: "ui-sans-serif, system-ui, -apple-system, BlinkMacSystemFont, Segoe UI, sans-serif"
    fontSize: 16px
    fontWeight: 650
    lineHeight: 1.3
  body-lg:
    fontFamily: "ui-sans-serif, system-ui, -apple-system, BlinkMacSystemFont, Segoe UI, sans-serif"
    fontSize: 16px
    fontWeight: 400
    lineHeight: 1.5
  body-md:
    fontFamily: "ui-sans-serif, system-ui, -apple-system, BlinkMacSystemFont, Segoe UI, sans-serif"
    fontSize: 14px
    fontWeight: 400
    lineHeight: 1.5
  body-sm:
    fontFamily: "ui-sans-serif, system-ui, -apple-system, BlinkMacSystemFont, Segoe UI, sans-serif"
    fontSize: 13px
    fontWeight: 400
    lineHeight: 1.45
  label:
    fontFamily: "ui-sans-serif, system-ui, -apple-system, BlinkMacSystemFont, Segoe UI, sans-serif"
    fontSize: 12px
    fontWeight: 600
    lineHeight: 1.3
    letterSpacing: 0.01em
  caption:
    fontFamily: "ui-sans-serif, system-ui, -apple-system, BlinkMacSystemFont, Segoe UI, sans-serif"
    fontSize: 12px
    fontWeight: 400
    lineHeight: 1.4
  data:
    fontFamily: "ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, monospace"
    fontSize: 13px
    fontWeight: 500
    lineHeight: 1.35
    fontFeature: "'tnum' 1, 'lnum' 1"
  metric:
    fontFamily: "ui-sans-serif, system-ui, -apple-system, BlinkMacSystemFont, Segoe UI, sans-serif"
    fontSize: 24px
    fontWeight: 650
    lineHeight: 1.1
    fontFeature: "'tnum' 1, 'lnum' 1"
rounded:
  none: 0px
  sm: 6px
  md: 8px
  lg: 12px
  full: 999px
spacing:
  half: 4px
  xs: 8px
  sm: 12px
  md: 16px
  lg: 24px
  xl: 32px
  xxl: 48px
  gutter-min: 24px
  gutter-max: 48px
  control-comfortable: 36px
  control-compact: 32px
  row-comfortable: 44px
  row-compact: 36px
components:
  button-primary:
    backgroundColor: "{colors.primary}"
    textColor: "{colors.on-primary}"
    typography: "{typography.body-md}"
    rounded: "{rounded.sm}"
    padding: 8px
    height: "{spacing.control-comfortable}"
  button-secondary:
    backgroundColor: "{colors.surface-2}"
    textColor: "{colors.text}"
    typography: "{typography.body-md}"
    rounded: "{rounded.sm}"
    padding: 8px
    height: "{spacing.control-comfortable}"
  input:
    backgroundColor: "{colors.surface-1}"
    textColor: "{colors.text}"
    typography: "{typography.body-md}"
    rounded: "{rounded.sm}"
    padding: 8px
    height: "{spacing.control-comfortable}"
  status:
    backgroundColor: "{colors.surface-2}"
    textColor: "{colors.text}"
    typography: "{typography.label}"
    rounded: "{rounded.full}"
    padding: 8px
    height: 32px
  panel:
    backgroundColor: "{colors.surface-1}"
    textColor: "{colors.text}"
    rounded: "{rounded.md}"
    padding: 16px
  inspector:
    backgroundColor: "{colors.surface-1}"
    textColor: "{colors.text}"
    rounded: "{rounded.none}"
    padding: 16px
---

# Bilqis Mission Control Design System

## Overview

Mission Control is a **calm scientific workstation**: the screen equivalent of a high-end benchtop laboratory instrument with the editorial clarity of a well-composed scientific figure. It exists to help a technically sophisticated operator inspect a learning system, compare evidence, understand uncertainty, and take deliberate action under normal, historical, partial, stale, and failure conditions.

The interface is an instrument, not a marketing surface. It should feel quiet, exact, legible, and trustworthy. Information density is welcome when the task requires it, but density must be earned by hierarchy and progressive disclosure. The default view of a screen should reveal the operator's current context, the purpose of the destination, the primary working surface, and the next meaningful action. Forensic depth belongs behind inspection, disclosure, or deliberate navigation.

The product must not resemble cyberpunk terminal theater, a generic SaaS dashboard, a consumer settings application, or a wall of bordered diagnostics. Decorative complexity is a defect. A screenshot should still make compositional sense before the viewer reads any text.

Design decisions follow five priorities, in order:

1. **Truthful state.** Never improve appearance by weakening evidence, uncertainty, defensive-state, authority, or mutation semantics.
2. **Readable task hierarchy.** The user's task must dominate implementation metadata.
3. **Progressive disclosure.** Show enough to act; reveal enough to investigate; preserve everything needed for forensics.
4. **Accessible resilience.** Keyboard, assistive technology, zoom, reflow, reduced motion, localization expansion, and failure states are part of the design.
5. **Visual restraint.** Whitespace, typography, alignment, and tonal hierarchy should do most of the work.

The canonical human-facing companion is `docs/architecture/mission-control-design/STYLE_GUIDE.md`. Normative composition and Home-view rules are in `docs/architecture/mission-control-design/VISUAL_COMPOSITION_SPEC.md`. The structural map is `docs/architecture/mission-control-design/INFORMATION_ATLAS.md`; cross-view behavior is in `docs/architecture/mission-control-design/FLOWS.md`; exact screenshot-derived failure examples are preserved in `docs/architecture/mission-control-design/ANTI_PATTERN_GALLERY.md`; literal parent-requirement coverage is tracked in `docs/architecture/mission-control-design/REQUIREMENT_TRACE.md`. Parent redesign authority and the running deficiency ledger live in GitHub issue #1124.

## Colors

The dark theme is neutral graphite, not blue-gray soup. Surfaces differ primarily by luminance and role. The cool primary accent is scarce: it marks selection, focus-adjacent emphasis, and deliberate interaction, not decoration. Semantic colors communicate health, warning, invalidity, historical context, and information only when paired with text, shape, iconography, pattern-free structure, or another non-color cue.

The light theme mirrors semantic roles rather than merely inverting the dark theme. Both themes must preserve the same hierarchy and WCAG 2.2 AA contrast obligations.

Color rules:

- `{colors.canvas}` / `{colors.light-canvas}` are the application substrate.
- Surface levels are for true layering or grouping, not alternating every row for decoration.
- `{colors.primary}` is the interaction/selection accent; it is never a general-purpose highlight color.
- `{colors.healthy}`, `{colors.attention}`, `{colors.danger}`, `{colors.historical}`, and `{colors.info}` are semantic roles, never standalone meaning.
- Borders are structural. If a grouping is already clear from spacing and surface tone, omit the border.
- Do not use gradients, glows, decorative diagonal stripes, neon effects, or patterned wallpaper for state.
- Focus uses `{colors.focus}` / `{colors.light-focus}` and remains visibly distinct from selection.

## Typography

Typography is semantic rather than globally flattened. The hierarchy uses modest steps so dense technical information can coexist with clear headings without turning the workspace into a poster or a terminal dump.

- **Display** is reserved for the highest-level page moment when a destination genuinely needs it. It is not repeated inside cards.
- **Title** is the ordinary destination title.
- **Section** and **subsection** establish hierarchy inside the working surface.
- **Body** roles carry explanation and operator guidance.
- **Label** and **caption** carry concise metadata, table headings, badges, and secondary explanations. No ordinary readable UI text is smaller than 12px.
- **Data** is monospace and reserved for machine identifiers, hashes, receipts, code, raw payloads, exact addresses, and similar values where character identity matters.
- **Metric** is used only for a small number of primary quantitative readings. It is not a license to enlarge every number.

Sentence case is the default. Uppercase is allowed for short state tags and compact eyebrows where scanning benefits, not for prose or long labels. Bold is scarce: use weight to establish hierarchy, not to compensate for weak composition.

Density modes may change spacing, row height, and optional detail exposure; they must not collapse the semantic type hierarchy or make important text smaller.

Never silently truncate operator-significant values such as strategy, intent, capability, action, state, or reason. Prefer reflow, layout recomposition, disclosure, or an explicit full-value inspection affordance. Middle ellipsis is acceptable only for long machine identifiers when the full exact value remains one action away and available to assistive technology.

## Layout

Mission Control uses a responsive workstation layout, not a fixed dashboard grid. The shell establishes persistent context and navigation; the workspace adapts to the task.

Spacing follows an 8px base rhythm with a 4px half-step. Related content is closer together than unrelated content. Empty space is semantic structure, not wasted capacity.

Primary layout rules:

- Keep shell chrome proportional to the task. Context that is not useful across destinations moves behind disclosure.
- A destination begins with purpose and state, then its primary working surface. Do not stack four explanatory banners before the work begins.
- Siblings in the same horizontal row share an intentional baseline or centerline.
- Responsive behavior recomposes. It does not merely squeeze desktop rows until text wraps or truncates.
- Default prose measure should remain readable; long explanatory copy should not span the full workstation width.
- Wide analytical surfaces own their horizontal scroll. The document itself should not drift horizontally.
- Wide tables use sticky headers where useful and sticky identity columns when horizontal comparison would otherwise destroy orientation.
- Table column groups and optional secondary measures should be progressively disclosed rather than exposing every possible field simultaneously.
- Comfortable mode must feel comfortable. Compact mode increases density without changing semantic hierarchy. The legacy `terminal` display preference is retired by the shared-foundation redesign; persisted `terminal` values migrate deterministically to `compact` so there are exactly two supported density modes.

### Composition authority

`VISUAL_COMPOSITION_SPEC.md` governs canvas/surface separation, when a region earns a card, visible containment depth, unequal hierarchy, alignment/proximity, shell-chrome restraint, interaction-role differentiation, responsive recomposition, and the Home-view composition contract. A bounded surface placed on the application canvas must remain visibly distinct from the canvas in dark and light themes; same-fill card-on-canvas treatment is not acceptable.

The default disclosure ladder is:

1. shell context;
2. view summary and state;
3. primary working detail;
4. secondary analysis;
5. inspection / forensics / raw provenance.

## Elevation & Depth

Mission Control is primarily flat. Depth comes from tonal layers, spacing, and occlusion rather than shadows.

- The canvas is the substrate. A bounded card/panel placed directly on canvas must use a visibly distinct surface treatment; it may not dissolve into the canvas and rely on radius or hover to reveal its edge.
- Persistent shell regions and primary working surfaces may use adjacent surface tones.
- Independent stateful objects may use a bounded panel treatment.
- A section is not automatically a card.
- Shadows are reserved for genuinely floating layers such as dialogs or transient popovers.
- The global inspector may be visually separated from the workspace because it is an independent inspection plane, but it must not obscure required focus or critical task context.
- Do not use shadows to make every container look clickable.

## Shapes

The shape language is engineered but not harsh. Small radii soften controls and independent panels without turning every object into a pill.

- Small controls and inputs use `{rounded.sm}`.
- Independent panels may use `{rounded.md}`.
- Larger radii are rare and need a compositional reason.
- Fully rounded geometry is reserved for compact statuses, tags, or segmented controls whose shape communicates category/state.
- Ordinary buttons are not pills by default.
- Tables, structural regions, and shell boundaries do not need rounded corners merely because cards elsewhere have them.
- Icons, borders, and shapes must remain legible in forced-colors mode.

## Components

Mission Control evolves by refining canonical primitives inside the existing vanilla HTML/CSS/JavaScript application. The redesign does not migrate to an external runtime UI framework.

### Shell context

The shell shows context useful across destinations. Secondary topology, factory, semantic, resource, and provenance facts are disclosed deliberately when their persistent presence would dominate the viewport. Empty, bootstrap, live, historical, stale, offline, denied, and incompatible states share one status grammar.

### Navigation

Primary navigation exposes destinations according to task/domain groups derived from the information atlas. Selection is clear without becoming the loudest rectangle on screen. Labels do not collapse into ambiguous initials at ordinary supported widths.

The navigation rail does not reserve permanent space for a standalone logo glyph. The current `B` mark is excluded from the target UI because it carries no operator task, state, or navigation meaning. Product identity is conveyed through quiet text and application/window context.

### Buttons and actions

Primary, secondary, tertiary, destructive, filtering, grouping, export, and navigation actions are visually distinct by role. A row of unrelated dark rectangles is not an action hierarchy. Controls share height, baseline, focus treatment, disabled treatment, and pressed semantics.

### Status and badges

A status has a concise human-readable label, a non-color structural cue, and optional explanation. The application must not invent a new badge grammar in each view. Status text must not truncate into meaningless fragments.

### Tabs and segmented controls

Tabs switch peer views within one task context. Filters alter visible subsets. Segmented controls select one mode. These roles must not be styled interchangeably. Selection state is explicit in semantics and visuals.

### Panels and cards

Use a card only for an independent object or stateful unit. Use sections and whitespace for ordinary grouping. Avoid rectangle-inside-rectangle compositions. Card headers align labels, states, and actions with a shared geometry.

### Tables

Tables are analytical instruments. They provide concise headers, sort state, persistent orientation, visible local overflow affordance, and accessible equivalents for non-tabular relationships. Do not repeat “Sort by” in every header. Do not clip group labels or semantic values.

### Inspector

The inspector reveals exact selected-object detail and actions without turning every destination into a forensic dump. It provides owner navigation, evidence navigation, pin/compare/annotation actions where supported, full values for any abbreviated machine identity, and clear return/focus behavior.

### Guidance and disclosure

Guidance lives next to the concept it explains. Do not use giant glossary ribbons. Define unfamiliar terms at first meaningful use and provide an accessible disclosure/help path for deeper explanation. Essential guidance must not depend on hover alone.

### Defensive states

Loading, progressive, empty, stale, partial, offline, denied, revoked, unavailable, incompatible-version, timeout, duplicate-action, restarting, malformed, unsupported, and outcome-unknown states remain semantically distinct. Defensive presentation is calm and actionable, not alarmist decoration.

## Do's and Don'ts

- **Do** make the primary task obvious before exposing secondary implementation detail.
- **Do** preserve exact evidence, uncertainty, and authority boundaries even when simplifying presentation.
- **Do** use whitespace, alignment, typography, and tonal contrast before adding another border.
- **Do** recompose responsive layouts instead of squeezing desktop rows.
- **Do** let dense tables own their scroll and preserve orientation with sticky headers/identity columns where useful.
- **Do** provide a visible path from summary to exact forensic detail.
- **Do** use one application-wide status grammar.
- **Do** keep help local and progressive.
- **Do** prefer native HTML semantics and use WAI-ARIA Authoring Practices where native semantics are insufficient.
- **Do** verify WCAG 2.2 AA on each touched micro-surface during redesign.
- **Do** sweep each redesign leaf's entire owned micro-surface and convert all human-facing strings in that surface to localization tokens with parameterized variables.
- **Do** sweep each redesign leaf's UI tests for its owned micro-surface and migrate all rendered-element selection to stable, unique `data-test-id` hooks.
- **Don't** truncate semantic values into fragments such as `AWAITING_RECO...`, `paired-screen:so...`, or `BOOLEAN F...`.
- **Don't** display persistent shell facts merely because the data exists.
- **Don't** use decorative diagonal stripes, gradients, glow, or texture as status language.
- **Don't** style filters, navigation, export, grouping, and destructive actions as equivalent buttons.
- **Don't** create glossary ribbons that require horizontal reading across the viewport.
- **Don't** use all-caps prose or long all-caps labels.
- **Don't** compensate for weak hierarchy by making everything bold.
- **Don't** nest bordered rectangles by default.
- **Don't** expose raw implementation exceptions as primary operator copy.
- **Don't** allocate persistent chrome to decorative brand marks that carry no operator information or action.
- **Don't** use text, CSS classes, DOM hierarchy, element IDs, localized strings, or unrelated attributes as application test selectors after a micro-surface has been migrated.
- **Don't** run a whole-application visual/WCAG audit after every micro-redesign; validate the touched surface and run the final integrated audit once all leaves land.

## Progressive Disclosure

The interface must remain useful to both fast operators and forensic investigators without forcing both modes into the same visual layer.

- Level 1: context that affects every destination.
- Level 2: destination purpose, current state, and primary action.
- Level 3: working detail required to perform the task.
- Level 4: secondary analysis and comparison.
- Level 5: exact receipts, raw payloads, provenance chains, hashes, and technical diagnostics.

A lower level may surface immediately when it is itself the destination's primary task, as in Evidence or Operate. Progressive disclosure is about task relevance, not hiding data indiscriminately.

## Accessibility

WCAG 2.2 AA is the redesign baseline. Each micro-redesign reviews the criteria applicable to its surface, including keyboard operation, visible focus, Focus Not Obscured, target size, names/roles/descriptions, contrast, non-color state cues, zoom/reflow/text spacing, reduced motion, error/recovery guidance, hover/focus content behavior, and equivalent alternatives for complex visualizations.

The existing `docs/architecture/BAMF_MISSION_CONTROL_ACCESSIBILITY_DEFENSIVE_UX.md` behavior contract remains authoritative where it already defines keyboard, focus, live-region, defensive-state, graph-equivalence, reduced-motion, or forced-colors behavior. The redesign extends that contract; it does not silently replace it.

## Internationalization

Every human-facing string in a micro-surface owned by a redesign leaf moves behind a stable localization token during that leaf, whether or not the line was otherwise edited for layout. By final acceptance, no Mission Control human-facing application copy remains outside the localization boundary except explicitly documented machine/source data. Do not build complete sentences by concatenating translated fragments. Variables are explicit parameters. Machine identifiers and source-authoritative values remain data rather than translation keys.

Layouts must tolerate realistic string expansion. Prefer logical CSS properties so future RTL support is not structurally blocked. Test hooks, CSS tokens, object identities, and localization keys are separate namespaces.

## Testing Hooks

Application UI tests target rendered application elements only through exact `[data-test-id="foo"]` selectors or intentional groups through `[data-test-id^="foo-prefix-"]`.

Every exact test ID identifies one rendered element. Test IDs are stable, semantic, nonlocalized, and independent of copy, CSS class, DOM ancestry, visual order, ARIA label, or element ID. Each micro-redesign audits every Mission Control UI test that selects elements in its owned surface, not merely the assertions changed by the visual diff. Final integrated acceptance verifies that all Mission Control application UI element selection conforms globally.

## Motion

Motion is mechanical and brief. Interactive feedback should generally complete within roughly 100–180ms and should clarify a relationship, state transition, or focus change. Nothing bounces, overshoots, glows, or moves merely to appear lively. `prefers-reduced-motion` collapses nonessential motion.

## Evaluation

A micro-redesign is not visually accepted because its tests pass. It is complete only when comparative rendered evidence demonstrates that the touched surface satisfies task hierarchy, composition, responsive behavior, accessibility, localization resilience, test-hook discipline, defensive states, and the relevant component rules above.

The final whole-application acceptance occurs after all decomposed redesign leaves integrate. Parent authority: GitHub issue #1124.
