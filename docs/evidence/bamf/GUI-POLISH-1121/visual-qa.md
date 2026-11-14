# GUI polish #1121 visual QA

## Intent

This pass repairs the owner-facing BAMF-0.2 Mission Control layout before trainer evaluation. It does not expand into the generalized BAMF-0.3 production-polish scope tracked by #1114.

The visual review used both the checked-in browser preview harness and the native Electron window. The browser harness was used to navigate every primary destination under one fixed viewport and measure shell geometry; the Electron application was then launched at its real 1440 × 920 default window for visual confirmation.

## Before-state observations

At a 1673 × 837 browser viewport on the owner GUI integration branch before this patch:

| View / measure | Before |
| --- | ---: |
| Home rail width | 176 px |
| Non-Home rail width | 220 px |
| Home context-bar height | 135 px |
| Non-Home context-bar height | 150 px |
| Common non-Home H1 | 64 px |
| Common non-Home inline page gutter | 88 px |
| School document-level horizontal overflow | 1021 px |
| Teacher rail height on long page | ~3210 px |
| Salience rail height on long page | ~5326 px |
| Command utility on long pages | pushed below viewport |

The Home dashboard also allowed short state values such as `UNAVAILABLE` to break across lines because its metric rows were flexible and the value column used `overflow-wrap:anywhere`.

## Root causes found during screenshot-driven review

1. `home/home.css` changed shared shell geometry only on Mission Control, including a 176 px rail.
2. `capability/dossier.css` and `frame-explorer.css` contained unscoped `.context-bar` / `.context-actions` rules even though those stylesheets are loaded globally.
3. Shared `.view-host` padding and title scale were tuned like a sparse landing page rather than a dense operator console.
4. School had an internal matrix scroller, but its ancestors could still grow to the matrix's max-content width.
5. The rail participated in full document height instead of remaining viewport-bound.
6. Corrections, Evidence, and SÍ SÉ SON referenced legacy CSS variables that were not defined by the active visual token surface, causing browser declarations to be dropped.
7. Teacher strategy cards used three metric columns and flex history rows inside cards that were too narrow for the content.

## After-state browser measurements

After the patch, the same 1673 × 837 browser pass produced:

| View | Rail | Header | H1 | Inline gutter | Page X overflow |
| --- | ---: | ---: | ---: | ---: | ---: |
| Mission Control | 184 px | 84 px | 42 px | 30 px | 0 px |
| School | 184 px | 84 px | 48 px | 48 px | 0 px |
| Capability Explorer | 184 px | 84 px | 48 px | 48 px | 0 px |
| Learning | 184 px | 84 px | 48 px | 48 px | 0 px |
| Atlas | 184 px | 84 px | 48 px | 48 px | 0 px |
| Model | 184 px | 84 px | 48 px | 48 px | 0 px |
| Memory | 184 px | 84 px | 48 px | 48 px | 0 px |
| Teacher | 184 px | 84 px | 48 px | 48 px | 0 px |
| SÍ SÉ SON | 184 px | 84 px | 48 px | 48 px | 0 px |
| Corrections | 184 px | 84 px | 48 px | 48 px | 0 px |
| Lineage | 184 px | 84 px | 48 px | 48 px | 0 px |
| Resources | 184 px | 84 px | 48 px | 48 px | 0 px |
| Evidence | 184 px | 84 px | 48 px | 48 px | 0 px |

The rail measured exactly the viewport height on every destination, and the Command utility remained at the bottom of the viewport on long School, Teacher, SÍ SÉ SON, Corrections, and Model pages.

## Native 1440 × 920 review

The Electron app was launched from this worktree at its default 1440 × 920 window size. Mission Control, School, and Teacher were manually inspected after the browser matrix pass.

Observed:
- navigation width remains stable between views;
- top chrome remains aligned and substantially shorter;
- School's wide matrix is contained inside its own data surface rather than widening the window;
- Home state values remain whole rather than breaking mid-token;
- Teacher's roster cards use two metric columns and bounded history rows, removing the remaining card-level horizontal creep;
- long pages keep the Command control visible in the rail.

## Automated regression guards

`apps/mission-control/tests/layout-contract.test.mjs` protects the structural pieces that caused the regression:
- shared rail ownership and sticky viewport geometry;
- no Home rail-width override;
- no unscoped Capability/Frame context-bar ownership;
- bounded shared page/title geometry;
- Home value-column behavior;
- School internal scroll containment;
- Teacher card containment;
- compatibility aliases for legacy visual tokens.

The browser/native checks remain the primary proof for the visual outcome; these source-level tests are guardrails against reintroducing the known causes.
