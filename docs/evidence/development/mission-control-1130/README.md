# Admin Main Frame School rendered acceptance evidence

Issue #1130 redesigns `VIEW-D-002` from unified baseline
`b621e1bb3195fe739a1916e32d46c7b605b5e510`.

All images use the repository's checked-in School and curriculum fixtures. They are
rendered interface evidence only and do not represent live learner state.

| File | Purpose |
| --- | --- |
| `before-matrix-dark.png` | Baseline capability matrix and dependency view. |
| `before-curriculum-dark.png` | Baseline curriculum topology and dossier composition. |
| `after-matrix-dark.png` | Redesigned matrix and dependency peers, dark/comfortable. |
| `after-matrix-light-compact.png` | Redesigned matrix, light/compact. |
| `after-matrix-narrow.png` | Redesigned matrix at a 390 px viewport. |
| `after-curriculum-dark.png` | Redesigned curriculum topology and equivalent table, dark/comfortable. |
| `after-curriculum-light-compact.png` | Redesigned curriculum view, light/compact. |
| `after-curriculum-narrow.png` | Redesigned curriculum view at a 390 px viewport. |

The comparison checks the issue-owned presentation contract: grouped matrix
headers, visible score denominators, sticky capability identity, explicit local
horizontal overflow, distinct filter/group/column/export roles, simultaneous
graph and equivalent-table representations, full semantic labels, and a flatter
selected-node dossier.

Browser reflow checks used the actual renderer modules and CSS. Both matrix and
curriculum views reported no document-level horizontal overflow at 320 px in
light/compact mode. A second 320 px pass combined compact density, RTL direction,
and increased line (`1.5`), letter (`.12em`), and word (`.16em`) spacing; both
views again reported no document-level horizontal overflow. Reduced-motion and
forced-colors behavior remain covered by the shared Admin Main Frame contract and
School CSS media queries.
