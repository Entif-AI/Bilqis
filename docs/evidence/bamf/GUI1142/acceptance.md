# GUI1142 Operate redesign acceptance evidence

Issue: #1142

Implementation commit: `0c4fd5d2e993ccfb9bed27ea1391f610fe30f989`

Original unified baseline: `7b79ef85b1b7fad87918066b8ca2e048ddc24936`

## Target/current reconciliation

The existing GUI17 command semantics were retained. The redesign changes presentation,
localization, testability, and interaction continuity without changing CP05 authority:

- exact action and scalar parameter contract retained;
- read-only preflight remains mandatory before submission;
- mutating submission still requires the exact typed authorization phrase;
- stale target drift still blocks authorization and cannot silently rebind;
- duplicate submit remains suppressed;
- lost acknowledgement still never retries the command;
- outcome-unknown remains unresolved until authoritative receipt readback;
- Pause remains unavailable and Stop retains exact active-operation identity.

The old four-column action-card wall and patterned mutation/error treatment were
replaced by a compact action list plus a sequential request -> preflight ->
authorization -> receipt/readback composition. Mutation receives exceptional visual
salience only at the authorization boundary.

## Local proof before final unified reconciliation

- Focused Operate/controller/boundary/renderer-protocol: 24/24 pass.
- Model Forensics: 336/336 pass.
- Electron security after locked dependency install: 53/53 pass.
- Python Model Forensics bridge: 6/6 pass.
- Development structure: pass, zero violations.
- Governance integrity: pass, zero violations.
- Changed-file code-smell delta: zero new findings.
- BAMF retained-authority policy checks and tests: pass.
- BAMF flow-control and tests: pass.
- Differential leaf gate: policy skip for this UI-only change set.
- `git diff --check`: pass.

The first Electron-security attempt failed before relevant assertions because the
fresh worktree did not yet contain the locked `ajv` dependency. `npm ci
--ignore-scripts` installed the repository lockfile tree (19 packages, 0
vulnerabilities); the exact same security command then passed in full.

## Comparative rendered evidence

Rendered with the checked-in Model Forensics renderer through local preview servers.
Port 8760 was already owned by the active #1128 worktree and was left untouched;
GUI1142 used isolated ports 8771 (exact baseline) and 8772 (redesign).

### Exact baseline, dark comfortable, mutating Resume review

- Baseline: `7b79ef85b1b7fad87918066b8ca2e048ddc24936`
- Viewport: 1487 x 755 CSS px.
- Domain height: 1707.97 px.
- Document height: 2096 px.
- Document width: 1472 px, below the 1487 px viewport.
- Observed composition: patterned `MUTATION ZONE`, eight equal action cards, separate
  request/preflight/authorization panels, patterned mutation consequence, and no
  explicit pending receipt stage.

### Redesign, dark comfortable, same mutating Resume review

- Viewport: 1487 x 755 CSS px.
- Domain height after final catalog compaction: 1973.78 px.
- Document height: 2362 px.
- Document width: 1472 px, below the 1487 px viewport.
- Action catalog is a two-column list rather than card wall.
- Exact request, preflight, authorization, and pending receipt/readback are one
  numbered vertical sequence.
- Target facts use aligned label/value rows; resource profile is disclosed rather
  than permanently expanded.
- Only the mutating authorization stage receives exceptional tonal emphasis.
- No repeating-pattern danger treatment remains.

### Light compact, 390 px stale-target review

- Viewport: 390 x 844 CSS px.
- Domain height: 3352.38 px.
- Document height: 4089 px.
- Document width: 375 px, below the 390 px viewport.
- Action list recomposes to one column.
- Exact identities wrap without truncation or document-level horizontal overflow.
- Generation and semantic-release conflicts render adjacent to the preflight facts.
- Authorization is visibly blocked and explains the recovery action.

### Lost acknowledgement

- Viewport: 1440 x 900 CSS px.
- Domain height: 1924.78 px.
- Document height: 2313 px.
- Document width: 1425 px, below the 1440 px viewport.
- Receipt stage states that acknowledgement was lost, retains exact operation
  identity, explicitly refuses blind retry, and exposes only reconciliation.

### Historical / defensive command-unavailable posture

- Viewport: 1440 x 900 CSS px.
- Domain height: 1338.19 px.
- Document height: 1726 px.
- Document width: 1425 px, below the 1440 px viewport.
- Live-context warning is explicit.
- Preflight control is visibly disabled, matching the controller's fail-closed
  behavior rather than appearing actionable.

## Accessibility and visual-system checks

- Operate-owned copy resolves through stable message keys.
- Stable unique `operate-*` test hooks cover the command sequence and controls.
- Focus-visible treatment is explicit.
- Compact density and the shell's 980 px transition are supported.
- A 720 px narrow reflow rule recomposes facts, stages, and lifecycle.
- Reduced-motion and forced-colors treatment are explicit.
- Semantic state and mutation posture are not conveyed by color alone.
- Retired terminal-density behavior and decorative repeating gradients are absent.

Final exact unified/head identities and hosted verification are recorded after the
last unified reconciliation.
