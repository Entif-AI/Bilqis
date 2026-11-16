# #1140 Resources — implementation readiness review

- Mode: REVIEW; target: issue #1140, its referenced Resources design bundle and the amended implementation plan supplied by the coordinating agent.
- Baseline: `dada27e8b1776e0fb7917c61bd8df141a210f93a`; design bundle merge `de03612e30f467bcef9d595aec7a032614a5f332` is an ancestor. PR #1145 is merged; #1124 records explicit human ratification on 2026-11-14 23:38 UTC.
- Pinned reviewer: `/Users/cr8s/Code/bamf02-egm-b3a359` at `b3a35956759bf7f024af2ff061b2e0b44b438e4c`; `agents/implementation_readiness.md` and `resources/document_standards/implementation-readiness-standard.md`.
- Result: **PASS for the amended Resources design scope**, with 0 blockers and 0 major findings remaining. This is a design readiness judgment, not implementation, visual, accessibility, drift, or integration proof.

## Decisions reviewed

1. Transform the six current Resources components into the target hierarchy: compact observed/budget/forecast summary and local semantic disclosure; decomposition table; compute and length analytical tables; timeline sample table; exact-generation comparison form/table. Retain the current metric facts intentionally in the summary or analytical tables; do not infer unavailable telemetry. Show fixture versus live/historical provenance and preserve the throughput-is-not-learning boundary.
2. Reconciliation uses signed `aggregate - measured sum`. COMPLETE requires a finite aggregate, every category PRESENT with a finite value, and an exactly zero remainder. A finite aggregate with unknown categories or a nonzero signed remainder is PARTIAL. An absent aggregate is UNAVAILABLE. A negative remainder is explicitly category overage; never clamp it or disguise it as reconciled.
3. Keep CP03 read-only queries, bounded exact-generation selection and CP04 resource-only live refresh. Empty input is invalid, not generation zero. Show the exact requested generation and distinguish empty, pending, unavailable/failure and successful comparison states. Monotonic context/current/comparison epochs prevent stale responses from overwriting newer context or intent. Preserve the comparison draft, caret/focus, and disclosure state across repaint. Historical context does not subscribe to live events.
4. Timeline samples expose exact available identities and accepted references through the existing inspector; send raw values to the inspector and escape only at the rendering boundary. Temporal association is not causal attribution. Preserve source, evidence and receipt reference identities without inventing their type or missing related records.
5. Localize all Resources-owned human-facing copy, including inspector labels, using stable tokens with explicit parameters. Machine identifiers remain literal. A local resource catalog must be included in the Electron finite asset allowlist and its dependency-closure expectations. Add unique `data-test-id` hooks and migrate all UI-test locators for this surface, retaining functional data attributes separately.
6. The design uses aligned tabular values, explicit units and denominators, local table overflow, non-color state cues, visible focus, responsive reflow and readable canvas/surface separation in dark/light and comfortable/compact modes. No chart is required when a table carries the available evidence.

## Required implementation and proof checklist

- Update `resource-model.mjs`, `resource-view.mjs`, `resource-controller.mjs`, `resources.css`, Resources-local messages and relevant Resources tests; include new renderer assets in the finite Electron manifest and its test expectations. Coordinate any shared inspector/catalog change with its owner.
- Record the retain/transform/merge/move/remove disposition of relevant current inventory descendants against `COMP-D-1201..1206`; show all target constituents, including exact references and evidence-strength notes.
- Use red/green focused tests for complete, partial, unavailable, zero, unknown-category and negative-remainder decomposition; exact comparison generation including blank, zero, invalid, pending, failure, success and out-of-order responses; current/context switch races; refresh filtering, historical no-subscription, draft/focus/disclosure preservation, literal inspector identities, unavailable vs zero, and semantics/units. Test hook uniqueness and packaging closure where affected.
- Exercise keyboard/focus, names/roles/state, contrast and non-color cues, target size, zoom/reflow/text spacing, reduced motion, and error recovery; check live, historical and defensive states across dark/light, comfortable/compact and responsive layouts.
- Produce comparative rendered evidence; run smallest affected tests, then required leaf/integration gates at their applicable boundaries. Reconcile implementation-to-design drift separately. Newly discovered design deficiencies belong in #1124.

## Scope and limitations

This review assesses the supplied amendment and issue/design authority. It does not establish that the implementation exists, that every runtime interaction has been exercised, or that the design is visually accepted. The above lifecycle and presentation rules are part of the reviewed amendment; a materially different implementation requires affected-scope review.
