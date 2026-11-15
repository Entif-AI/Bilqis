# MC-INVESTIGATION-1128 visual QA

Issue: #1128

Exact comparative baseline: `df57fe448af9c79db8f9a6a2704564baec7e4c84`

The acceptance baseline is the exact unified integration head consumed by the final candidate. An earlier exploratory rendering at `490e86e1a284fd03c3824e0bce656d658df0052c` informed implementation but is not used as final comparative evidence.

## Acceptance setup

The exact baseline and candidate were served through the repository's existing Admin Main Frame preview bridge and captured through one reusable headless Chrome DevTools session. Separate localhost origins prevented browser module/style caching from mixing baseline and candidate state. The candidate was also exercised interactively through the connected desktop browser for Inspector, pin, note, compare, and deep-link behavior.

The exercised deep link selected exact object context:

`capability / B.AND / fixture-run / generation 7`

The ordinary preview bridge supplies a disconnected/inspection posture. A bounded alternate bridge for rendering only returned `healthy`, `serviceLive: true`, and `learnerReady: true` while serving the same checked-in fixture snapshot so the verified-live presentation could be exercised without invoking a trainer, control-plane mutation, or neural update.

## Rendered acceptance matrix

| Artifact | Base/head | Theme | Density | Viewport | Posture | Layout result |
| --- | --- | --- | --- | ---: | --- | --- |
| `baseline-df57fe44-dark-comfortable-1440.png` | exact baseline `df57fe44` | dark | comfortable | 1440 × 1100 | baseline/disconnected | 1425 px document width; no page overflow |
| `after-dark-comfortable-live-1440.png` | candidate | dark | comfortable | 1440 × 1100 | verified-live rendering fixture | `Current · generation 7`; 1425 px document width; no page overflow |
| `after-dark-comfortable-historical-1440.png` | candidate | dark | comfortable | 1440 × 1100 | explicit historical generation 6 + disconnected defense | `Historical · generation 6`; mutation unavailable; no page overflow |
| `after-light-compact-defensive-1440.png` | candidate | light | compact | 1440 × 1100 | disconnected defensive | 1425 px document width; no page overflow |
| `after-dark-comfortable-defensive-760.png` | candidate | dark | comfortable | 760 × 1100 | disconnected defensive | 745 px document width; no page overflow |
| `after-light-compact-defensive-390.png` | candidate | light | compact | 390 × 1100 | disconnected defensive | 375 px document width; no page overflow |

The exact historical rendering showed the defensive banner `Offline`, `Last verified snapshot · inspection only`, and `Mutation unavailable`. The verified-live rendering showed `Live service`, `Current verified snapshot`, and `Operator mutation contract available`. These are fixture-backed presentation checks, not claims of a production learner state.

## Baseline finding

The baseline investigation plane permanently exposed more chrome than the target composition calls for. Time controls and forensic/deep-link identity occupied the investigation surface rather than behaving as subordinate disclosure. Inspector identity/detail hierarchy was comparatively flat.

The checked-in exact-base capture is `baseline-df57fe44-dark-comfortable-1440.png`.

## Candidate observations

### Subordinate investigation toolbar

- Toolbar height observed at approximately 50 px in the connected desktop viewport.
- Time is represented by a compact `Time / Current · generation 7` disclosure.
- Closed Time disclosure computes `display: none` for its form; controls do not consume layout until requested.
- Persistent tool labels are terse counts: `Compare · 0/2`, `Pins · 0`, and `Notes · 0`.
- No permanent app URI/deep-link block is rendered in the toolbar.

### Inspector hierarchy and exact identity

- Inspector presents summary evidence first: object class, posture, and evidence posture.
- `Exact identity and details` is a closed disclosure by default.
- Closed forensic children compute `display: none`; Inspector actions begin below the disclosure without overlap.
- Opening forensics reveals exact run, generation, object class, exact ID, and the exact deep link.
- The selected deep link rendered as `bilqis://run/fixture-run/generation/7/capability/B.AND` and wraps rather than ellipsizing.

### Operator metadata

- Pinning the selected object changed the action to `Unpin exact object` and the toolbar to `Pins · 1`.
- Adding a note changed the toolbar to `Notes · 1`.
- The saved note visibly retained the exact target `capability · B.AND · fixture-run · generation 7`.
- The note carried the explicit marker `Operator note · non-authoritative` and local-operator metadata rather than presenting itself as source evidence or learner state.

### Compare semantics

- Setting both comparison sides changed the toolbar to `Compare · 2/2`.
- Comparing the selected capability reference to itself did not fabricate comparable facts. The workspace explicitly rendered `Unavailable` with the reason `The selected capability references do not expose a common literal fact set.`
- Compare state therefore remains literal and adapter-bounded rather than manufacturing false equivalence or a winner.

### Layout containment and responsive behavior

The exact acceptance captures measured:

- 1440 px viewport → 1425 px document/body scroll width
- 760 px viewport → 745 px document/body scroll width
- 390 px viewport → 375 px document/body scroll width
- no page-level horizontal overflow in any rendered variant
- light/compact and dark/comfortable both preserve the investigation hierarchy and terse toolbar labels
- the Inspector remains a side plane at desktop width and the investigation surface reflows rather than truncating exact identities at narrow widths

## Runtime defect caught during QA

Author CSS initially overrode the browser's native closed-`details` hiding behavior for both the Time form and Inspector forensic children. This caused closed disclosures to retain layout and, in Inspector, caused action overlap. The candidate now carries explicit closed-state rules:

- `.investigation-time:not([open]) form { display: none; }`
- `.inspector-forensics:not([open]) > :not(summary) { display: none; }`

Both rules were rechecked in the real browser and are covered by layout-contract tests.

## Visual acceptance

The candidate satisfies the #1128 composition intent across the exercised exact-base comparison, dark/light themes, comfortable/compact densities, 1440/760/390 responsive widths, verified-live rendering, explicit historical lens, and disconnected defensive posture. Investigation remains subordinate to destination work; exact context is recoverable without permanent URI chrome; unsupported comparisons remain explicit; and local operator metadata remains visibly non-authoritative.
