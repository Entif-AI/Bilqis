# Model Forensics Capability Explorer rendered acceptance evidence

Issue #1131 redesigns `VIEW-D-003`. Development began from unified baseline
`df57fe448af9c79db8f9a6a2704564baec7e4c84`; final integration and rendered
acceptance were refreshed against unified baseline
`a68961296b9ae4dc40b8813b2b91fd1633453c73`.

All screenshots use the repository's checked-in Capability Explorer fixture. They
are rendered interface evidence only and do not represent live learner state.
The `after-fixture-live-dark.png` capture intentionally exercises the visual
mechanics of a `LIVE` lens while the source remains explicitly marked as the
synthetic fixture; it is not evidence that a live learner was observed.

| File | Purpose |
| --- | --- |
| `before-dark.png` | Baseline Capability Explorer composition before the redesign. |
| `after-dark-comfortable-1440.png` | Redesigned dossier, dark/comfortable at desktop width. |
| `after-light-compact-1440.png` | Redesigned dossier, light/compact at desktop width. |
| `after-dark-comfortable-390.png` | Narrow dark-mode recomposition at 390 px. |
| `after-light-compact-320.png` | Compact light-mode recomposition at 320 px. |
| `after-fixture-live-dark.png` | Fixture-backed live-lens visual posture, explicitly identified as fixture data. |
| `after-rtl-text-spacing-320.png` | RTL, expanded line/letter/word spacing, reduced-motion pass at 320 px. |
| `after-defensive-unavailable.png` | Service-source failure state with no fixture fallback. |
| `browser-result.json` | Machine-readable browser acceptance receipt. |

The comparison checks the issue-owned hierarchy: exact capability identity and
state first, aligned NOW/TOP/Total/Debt/Retention/Eligibility/Qualification/Source
measurements second, and a flatter document-like chronology below. Evidence and
raw provenance remain available through progressive disclosure, while exact
evidence records can hand off to the owning Evidence destination. The visible
copy also states the epistemic boundary that chronology and declared
relationships do not establish inferred causes.

The browser acceptance pass reported zero document-level horizontal overflow at
1440, 390, and 320 px across dark/light and comfortable/compact variants. Axe
reported zero WCAG 2.2 A/AA violations on all four primary variants. The
RTL/text-spacing/reduced-motion pass also remained within the 320 px viewport,
and the interaction journey verified exact evidence inspection, the full Evidence
handoff, historical lens changes, declared dependency navigation, keyboard
section focus, and fail-closed service behavior.
