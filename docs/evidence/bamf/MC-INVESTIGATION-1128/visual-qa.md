# MC-INVESTIGATION-1128 visual QA

Issue: #1128

Baseline: `490e86e1a284fd03c3824e0bce656d658df0052c`

## Acceptance setup

The baseline and candidate were served through the repository's existing Mission Control preview bridge and inspected in the same connected Chrome browser. A fresh localhost origin was used for the candidate after baseline inspection so the browser could not reuse the baseline ES-module graph or stylesheets.

The exercised deep link selected exact object context:

`capability / B.AND / fixture-run / generation 7`

The preview bridge is inspection-only and therefore rendered historical posture, which is useful for this leaf because #1128 must preserve historical/inspection semantics and withhold mutation authority.

## Baseline finding

The baseline investigation plane permanently exposed more chrome than the target composition calls for. Time controls and forensic/deep-link identity occupied the investigation surface rather than behaving as subordinate disclosure. Inspector identity/detail hierarchy was comparatively flat.

Baseline browser capture receipt: `7883864c-635f-4218-989e-676a89f28e10`.

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

### Layout containment

At the connected desktop viewport:

- `innerWidth`: 1684 px
- document scroll width: 1669 px
- body scroll width: 1669 px
- no page-level horizontal overflow was introduced by the investigation plane or Inspector
- Inspector width: 420 px

## Runtime defect caught during QA

Author CSS initially overrode the browser's native closed-`details` hiding behavior for both the Time form and Inspector forensic children. This caused closed disclosures to retain layout and, in Inspector, caused action overlap. The candidate now carries explicit closed-state rules:

- `.investigation-time:not([open]) form { display: none; }`
- `.inspector-forensics:not([open]) > :not(summary) { display: none; }`

Both rules were rechecked in the real browser and are covered by layout-contract tests.

## Visual acceptance

The candidate satisfies the #1128 composition intent in the exercised desktop/historical state: investigation is subordinate to destination work, exact context remains recoverable, unsupported comparisons remain explicit, and local operator metadata remains visibly non-authoritative.
