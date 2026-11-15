# GUI1139 Lineage redesign acceptance evidence

Issue: #1139

Implementation commit: `674c6f87b9ddbc153c8a95f4ba7ef02364fa9f7a`

Original unified baseline: `df57fe448af9c79db8f9a6a2704564baec7e4c84`

## Target/current reconciliation

The accepted-generation and comparison semantics were retained while the current
Lineage presentation was consciously migrated against VIEW-D-011:

- CUR-COMP-1101 accepted lineage: transformed from equal generation cards plus a
  separate edge list into one branch-preserving lineage graph with a complete
  accessible table equivalent;
- CUR-COMP-1104 exact generation node: transformed into a document-style immutable
  dossier with aligned custody facts, progressive manifest/source detail, exact deep
  link and exact CP03 query identity;
- CUR-COMP-1102 comparison: transformed into endpoint controls plus literal
  Before / After / State / Source tables; no winner, progress or quality synthesis
  was introduced;
- CUR-COMP-1103 rejected-candidate boundary: retained semantically and reduced to a
  restrained non-lineage boundary state rather than a peer panel;
- CUR-COMP-1104.6 historical missing branch: transformed into the explicit
  COMP-D-1105 unavailable state. The current lineage is no longer rendered behind a
  missing historical request.

Exact manifest, parent, checkpoint, receipt, transition, capability and source
identities remain fixture/domain data. Human-facing Lineage copy is resolved through
stable localization keys. The shared generation-comparison adapter translates the
same semantic row keys rather than depending on presentation strings.

## Local proof before final unified reconciliation

- Focused Lineage + Electron renderer-protocol: 22/22 pass.
- Affected Lineage / interactions / renderer-protocol after shared compare repair:
  31/31 pass.
- Accessibility, layout, domain-context, Lineage and renderer-protocol slice:
  49/49 pass.
- Mission Control: 346/346 pass.
- Electron security: 53/53 pass.
- Python Mission Control bridge: 6/6 pass.
- Development structure: pass, zero violations.
- Governance integrity: pass, zero violations.
- Changed-file code-smell delta: zero new findings.
- Retained-authority policy checks and tests: pass.
- BAMF flow-control policy and tests: pass.
- Differential leaf gate: policy skip for this UI-only change set.
- `git diff --check`: pass.

The first full Mission Control pass exposed one cross-view compatibility seam: the
global generation-comparison adapter still consumed the previous human `label` /
`reason` row shape. The adapter was migrated to Lineage semantic keys and the same
localization catalog; the final full Mission Control pass is 346/346.

## Comparative rendered evidence

Rendered through the checked-in Mission Control preview harness using isolated local
ports 8773 (exact baseline) and 8774 (redesign).

### Exact baseline, dark comfortable, current accepted generation

- Baseline: `df57fe448af9c79db8f9a6a2704564baec7e4c84`.
- Viewport: 1440 x 900 CSS px.
- Domain height: 3364.52 px.
- Document height: 3753 px.
- Document width: 1425 px, below the 1440 px viewport.
- Observed composition: five equal generation cards in an auto-fit row, a separate
  transition list, an always-expanded two-column manifest tile grid, comparison
  source text embedded inside State/availability, and a dashed rejected-candidate
  peer panel.

### Redesign, dark comfortable, same current accepted generation

- Viewport: 1440 x 900 CSS px.
- Domain height: 3655.97 px.
- Document height: 4044 px.
- Document width: 1425 px, below the 1440 px viewport.
- Accepted generations form an actual parent/child branch tree. The recovery fork
  leaves generation 44238 rather than reading as another equally spaced card.
- The complete table equivalent remains present and independently navigable.
- The generation dossier exposes primary custody facts first; full manifest/source
  fields and exact query detail are progressive disclosures.
- Generation comparison has explicit Dimension / Before / After / State / Source
  columns and retains literal no-winner language.
- Manifest and dimension-diff tables own local horizontal overflow at wide size
  rather than widening the document.

### Light compact, 390 px, exact historical generation 44238

- Viewport: 390 x 844 CSS px.
- Domain height: 4466.97 px.
- Document height: 5219 px.
- Document width: 375 px, below the 390 px viewport.
- Historical generation 44238 is visibly pinned; other accepted nodes remain
  orientation-only. The only enabled generation selectors are the graph and table
  representations of that exact generation.
- Every wide analytical surface owns overflow locally:
  - lineage graph: 322 px client / 863 px scroll width;
  - accepted-lineage table: 324 / 860 px;
  - manifest/source table: 324 / 1626 px;
  - dimension diff: 324 / 1582 px;
  - capability diff: 324 / 1040 px.
- No document-level horizontal overflow occurred.

### Historical generation unavailable

- Requested generation: 999999.
- Viewport: 390 x 844 CSS px.
- Domain height: 417 px.
- Document width: 375 px.
- The view renders only the explicit historical-unavailable boundary.
- Accepted-lineage and generation-dossier components are absent; current generation
  data is not substituted behind the missing historical request.

## Accessibility and visual-system checks

- Stable unique `lineage-*` hooks cover the workspace, graph, graph nodes, complete
  table, dossier, manifest disclosure, comparison endpoints/tables, rejected boundary
  and historical-unavailable state.
- Existing browser navigation already selects the Lineage destination through the
  stable shell `data-test-id`; no Lineage-owned UI test relies on visible-text or
  hierarchy selectors.
- Selected, rejected, historical, missing, unavailable and regression states use
  structural/text cues in addition to semantic color.
- Wide analytical surfaces use local scroll regions and sticky identity columns.
- Exact 64-character identities use bounded middle ellipsis only where the exact
  value remains immediately available through the element title and accessible name;
  dossier custody values remain full text.
- Compact density, 980 px and 720 px recomposition, visible focus, reduced-motion and
  forced-colors treatment are explicit.
- Runtime remains vanilla HTML/CSS/JavaScript inside the existing Electron/CSP
  boundary.

Final exact unified/head identities and hosted verification are recorded after the
last unified reconciliation.
