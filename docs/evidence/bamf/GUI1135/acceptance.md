# GUI1135 · Engram Memory redesign acceptance

Issue: #1135  
Target: VIEW-D-007 / COMP-D-701..705 / COMP-D-733  
Flow: FLOW-D-010  
Initial design baseline: `df57fe448af9c79db8f9a6a2704564baec7e4c84`

## Result

The Memory destination now reads as one analytical retained-memory instrument rather than five equal-weight motif cards. Operational telemetry leads, exact retained identity is browsable in a table, the selected motif opens as a document-like dossier, generation change is aligned as literal state/delta evidence, and the rejected-candidate boundary is visually subordinate while remaining explicit. Retrieval telemetry remains non-authoritative: no view text promotes hit rate, gate use, or allocation into semantic truth or learned capability.

## Current-state reconciliation

| Current surface | Target disposition |
| --- | --- |
| Summary card | Transform into a compact aligned metric band with receipts behind disclosure. |
| Page summary / motif cards | Merge into one page navigator plus stable-identity slot table with local overflow. |
| Motif inspector card | Transform into a dossier with identity/address, use, parameter/correction, and progressively disclosed provenance/relations. |
| Generation comparison card | Transform into one aligned Created / Removed / Held / Requalified table plus numeric delta band. |
| Rejected candidate card | Reduce to a restrained dashed proof surface that explicitly states candidate-local status. |
| Historical fallback | Replace the whole current-memory view with an exact historical-unavailable state when retained detail does not exist. |
| Human-facing Memory literals | Move to stable `memory.*` i18n keys with explicit parameters. |
| Incidental selectors | Add unique `memory-*` `data-test-id` hooks while retaining functional data attributes only for behavior. |

## Comparative rendered evidence

The repository-local `apps/mission-control/tests/browser/memory-check.mjs` harness uses only Node built-ins and the installed Chrome DevTools Protocol. It renders the exact starting commit and the current worktree, sets exact CSS viewports, captures full-page screenshots, and writes `output/browser/1135/browser-result.json`.

Evidence:

- `output/browser/1135/before-dark-comfortable-1440.png`
- `output/browser/1135/after-dark-comfortable-1440.png`
- `output/browser/1135/after-light-compact-1440.png`
- `output/browser/1135/after-dark-comfortable-390.png`
- `output/browser/1135/after-light-compact-320.png`
- `output/browser/1135/after-rtl-text-spacing-reduced-motion-320.png`
- `output/browser/1135/after-historical-unavailable-320.png`
- `output/browser/1135/browser-result.json`

Browser assertions across the six current-state variants:

- no document-level horizontal overflow at 1440, 390, or 320 CSS pixels;
- analytical tables own their horizontal overflow at 390 and 320 instead of widening the document;
- all owned `data-test-id` values are unique;
- read-site receipts and provenance/relations remain closed by default;
- every explicit Memory control/link measured by the browser is at least 24 CSS px in both dimensions where target-size rules apply;
- RTL + expanded text spacing + reduced-motion emulation remains document-overflow-free at 320px;
- the historical-unavailable variant contains no current Memory summary or atlas.

## Accessibility and defensive-state review

- **Keyboard / focus:** page controls, motif selection, generation selection, disclosure controls, and related-record links use native `button`, `select`, `summary`, and `a` semantics. The owned surface supplies a visible `:focus-visible` outline.
- **Names / roles / state:** page navigation has an explicit accessible label; selected motif buttons expose `aria-pressed`; tables use header cells; progressive evidence uses `details` / `summary`.
- **Non-color cues:** Present / Active / Held / Rejected / Comparison use text plus symbols/border grammar. Created / Removed / Held / Requalified comparison rows use distinct structural borders in addition to palette.
- **Reflow:** the document remains within 320 CSS px. Wide analytical data scrolls only inside its named local table regions.
- **Text spacing / RTL:** exact 320px browser proof with expanded letter/word spacing and RTL remains within the document viewport. A failing-before run exposed the fixture label's `white-space: nowrap`; removing that forced minimum fixed the overflow.
- **Target size:** browser measurement initially found 21px-tall related-record links. The final surface gives those explicit actions a 24px minimum; the exact-browser check now reports zero undersized owned targets.
- **Reduced motion:** the surface introduces no animation and the exact-browser variant runs with `prefers-reduced-motion: reduce`; the stylesheet also retains a reduced-motion rule.
- **Historical / unavailable:** missing historical detail fully substitutes the current surface rather than borrowing current retained-memory state.
- **Fixture posture:** detailed motif telemetry remains explicitly `REFERENCE FIXTURE · READ ONLY`; the accepted CP03 MemorySnapshot limitation is stated without warning-card domination.

## Structural interruption

The first redesign pass grew `memory.css` to 531 LoC, triggering the mandatory AGENTS.md structure interruption. The task state was preserved before further feature work. The stylesheet was split along the rendered ownership seams:

- `memory-core.css`: 175 LoC
- `memory-atlas.css`: 171 LoC after the 24px action-target repair
- `memory-evidence.css`: 190 LoC
- `memory.css`: 3 ordered imports
- companion `memory-view.test.mjs`: 233 LoC

The structural seam passed 21/21 focused Memory/protocol tests plus `DEVELOPMENT_STRUCTURE_CHECK OK` before feature work resumed. The interruption was committed at `d935bbe2d18834a1bb378894dd7ca000dc002222`.

## Authority and semantic invariants

- Stable memory identity remains the full motif key digest, not a page/row coordinate.
- Address, allocation state, source eligibility, correction/requalification, optimizer participation, and receipt identities remain literal fixture values.
- Memory retrieval and gate-use telemetry do not become source truth, semantic authority, or learned-success claims.
- Rejected candidate evidence never becomes committed retained-memory allocation.
- Generation comparison reports literal changes and numeric deltas only; it does not name a winner or infer causality.
- Related capability, learning-episode, and Evidence actions are navigation only. They do not mutate memory state.

## Reproduction

```sh
BILQIS_MEMORY_BASE_REF=df57fe448af9c79db8f9a6a2704564baec7e4c84 \
  node apps/mission-control/tests/browser/memory-check.mjs
```

## Final current-unified reconciliation

Before turn-in, #1135 consumed current unified `a68961296b9ae4dc40b8813b2b91fd1633453c73`. The only manual merge conflict was the shared foundation i18n registry after the upstream investigation redesign moved peer message bundles under `foundation/messages/`; the resolution preserves the complete incoming registry and adds the Memory message catalog without restoring retired paths. The Electron asset allowlist and its exact test merged both sets of assets cleanly.

Reconciled head: `8087d26556ebbebdf9488c136881abe2a1286349`

Fresh reconciled proof:

- focused Memory + accessibility + layout + renderer-protocol seam: **39/39 PASS**
- exact Chrome/CDP browser qualification: **7/7 variants PASS**
- `verify:leaf`: **PASS**
  - Mission Control renderer: **352/352 PASS**
  - Electron security: **53/53 PASS**
  - Python bridge: **6/6 PASS**
  - development structure, governance integrity, legacy trainer authority, and BAMF flow control: PASS
- `git diff --check`: PASS

The first post-merge `verify:leaf` attempt exposed a stale local dependency install: current source already declared `ajv@8.20.0`, while this worktree lacked `node_modules/ajv`. An offline, no-save install restored the declared dependency without changing `package.json` or `package-lock.json`; the exact rerun then passed completely. This was an execution-environment repair, not a product-code change.
