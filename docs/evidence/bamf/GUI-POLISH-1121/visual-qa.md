# GUI polish #1121 visual QA

## Intent

This pass repairs the owner-facing BAMF-0.2 Admin Main Frame layout before trainer evaluation. It does not expand into the generalized BAMF-0.3 production-polish scope tracked by #1114.

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

1. `home/home.css` changed shared shell geometry only on Admin Main Frame, including a 176 px rail.
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
| Admin Main Frame | 184 px | 84 px | 42 px | 30 px | 0 px |
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

The Electron app was launched from this worktree at its default 1440 × 920 window size. Admin Main Frame, School, and Teacher were manually inspected after the browser matrix pass.

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

## Second visual-language pass after owner review

Owner screenshot review after the first pass showed that shell stability was necessary but not sufficient. The remaining defect was presentation entropy across domain views:

- too many independently invented font sizes;
- controls and text in the same horizontal row did not share a stable visual baseline;
- dense data surfaces exposed raw machinery without nearby explanations;
- Teacher packed too many strategy cards into one row;
- wide surfaces needed stronger local scroll affordances;
- Evidence surfaced the implementation exception `api.query is not a function` instead of operator-facing disconnected-state language.

The follow-up pass therefore added a shared operator type scale, normalized control/body line height, shared 22 px domain headings, row-centered header/notice geometry, local scrollbar gutters, and compact in-context glossaries for School, Teacher, SÍ SÉ SON, Corrections, and Evidence. Teacher's strategy roster is now two columns at the 1440 px owner viewport rather than a three/four-card squeeze.

Fresh-origin browser review at 1440 × 920 confirmed:

| View | Domain H2 | Page X overflow | Explanatory glossary |
| --- | ---: | ---: | --- |
| School | 22 px | 0 px | present |
| Teacher | 22 px | 0 px | present |
| SÍ SÉ SON | n/a | 0 px | present |
| Evidence | 22 px | 0 px | present |
| Corrections | 22 px | 0 px | present |

At the same viewport, Teacher's strategy roster computed as two equal columns of approximately 578 px each. Evidence's disconnected preview now reports `Evidence queries are unavailable while the local evidence service is disconnected.` instead of exposing the missing `api.query` method.

The layout-contract suite now also guards the shared type tokens, two-column Teacher roster, explanatory surfaces, and the Evidence `QUERY UNAVAILABLE` presentation contract.

## Third pass after owner rejection of the second acceptance claim

The owner supplied two fresh screenshots after the second pass and rejected the claim that the visual language had been normalized. That rejection was correct. The screenshots exposed failures that the earlier measurements did not detect:

- the nominal type scale was not a real invariant because domain CSS still declared many literal sizes;
- the no-snapshot context header still reserved an empty context-facts column, forcing `No verified snapshot` into ugly multi-line wrapping while leaving unused horizontal space;
- selectors, pills, and buttons occupied different vertical positions inside the same horizontal row;
- the Scientific Visual Language catalog still used different card grammars and different numeric-emphasis sizes;
- successful containment and zero page overflow were insufficient acceptance criteria for visual coherence.

The third pass replaced the compatibility-heavy scale with four actual rendered roles:

| Role | Size | Intended use |
| --- | ---: | --- |
| label | 11 px | metadata, badges, dense tables |
| body | 14 px | prose, controls, ordinary values |
| section | 18 px | local section headings |
| display | 28 px | destination headings and primary numeric emphasis |

All Admin Main Frame domain CSS now resolves through these roles. A regression test recursively scans every renderer stylesheet and rejects new literal rendered text sizes. The only literal sizes left in `shell.css` are non-content exceptions: 28 px close icons, the responsive `font-size: 0` nav-hiding technique, and its 14 px first-letter fallback.

The context header now has separate verified and empty-state geometry. In the empty state, the unused facts surface is hidden and the header becomes a single 72 px row. At 1266 px:

- `No verified snapshot` remains one line;
- `Generation unavailable` remains one line;
- Run / As of selectors, freshness, Density, and Theme share one bottom control baseline;
- page-level horizontal overflow is 0 px.

In verified state at the same 1266 px width, identity and controls occupy the first row and all eight context facts occupy one compact second row. Header height is 111 px rather than the earlier 150 px. At 1440 px the verified header is 88 px.

The Scientific Visual Language catalog now uses the same header/value geometry for both metric cards. At 1295 px both primary values begin at the same vertical coordinate and both use the 28 px display role. The catalog heading is also 28 px with 14 px supporting copy rather than another independent heading scale.

Full destination-matrix browser verification at 1266 × 920 showed:

- every primary destination uses exactly `11px / 14px / 18px / 28px`;
- every primary destination has 0 px document-level horizontal overflow;
- every destination title occupies one 29 px line;
- verified context height is 111 px across the matrix.

At 1440 × 920, the same matrix retains the four-size type system, 0 px page overflow, a one-line 28 px destination title, and an 88 px verified context header. The native Electron app was relaunched at its real 1440 × 920 window after the third-pass changes for direct visual confirmation.

The previous second-pass statement that the visual language was normalized is superseded by this section.
