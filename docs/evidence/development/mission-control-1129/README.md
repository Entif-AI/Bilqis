# Mission Control Home rendered acceptance evidence

Issue #1129 redesigns `VIEW-D-001` from the unified baseline
`dc9b881e20b8c825042e4697e60f396264d16156`.

The images use the repository's `referenceHomeProjection()` fixture. They are
rendered evidence only. They do not represent live learner state.

| File | Purpose |
| --- | --- |
| `before.png` | Baseline Home at the unified SHA above. |
| `after.png` | Redesigned Home, dark theme, comfortable density. |
| `after-light.png` | Redesigned Home, light theme, comfortable density. |
| `after-compact.png` | Redesigned Home, dark theme, compact density. |
| `after-narrow.png` | Redesigned Home at a 720 px viewport. |

The comparison checks the issue's presentation contract: the five-state status
band, severity-driven attention order, untruncated Current Work values,
chronological Learning Pulse, compact School Snapshot, and collapsed Health
Details. The narrow rendering also checks that the primary regions recompose into
one column without changing evidence or priority.
