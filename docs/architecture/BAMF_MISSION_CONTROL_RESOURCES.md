# BAMF Model Forensics Resources (GUI15)

Issue: #1070
Parent: #1047
Surface: read-only Electron renderer over accepted Model Forensics CP03/CP04 contracts

## Operator contract

The Resources view answers a narrower question than the Model Forensics home: **where is the measured resource budget going, how did it change, and what exact evidence is available for a spike?** It is not a performance-policy engine and it is not evidence of learning quality.

The view keeps four semantic classes visually and structurally distinct:

1. **Measured values** are direct recorded observations.
2. **Configured limits/budgets** are policy or configuration values and are not measured peaks.
3. **Derived values** are deterministic transforms of accepted values, such as steps/minute multiplied by 60.
4. **Forecasts/estimates** are explicitly labeled estimates and never promoted into measured evidence.

Missing values remain `UNAVAILABLE`. A category is never rendered as zero merely because the current Model Forensics contract does not expose it.

## Accepted live projection boundary

At GUI15 implementation time, `bilqis.bamf.mission-control.resource-sample/v1` exposes only:

- `memory_used_bytes`;
- `memory_budget_bytes`;
- `disk_used_bytes`;
- `step_rate_per_minute`.

GUI15 consumes those fields literally through the accepted CP03 `resource` family. It derives an hourly step rate only when `step_rate_per_minute` is present. It does **not** reinterpret disk used as disk reserve, nor aggregate memory as MLX allocation, cache, optimizer state, gradients, activation memory, or Engram memory.

The current rich diagnostic fixture demonstrates the intended view contract for metrics whose live producers are not yet represented by CP03. The fixture is conspicuously labeled and is not evidence that those producers exist.

## Decomposition rule

When category measurements exist, GUI15 sums only categories whose values are explicitly present. It compares that measured subtotal with the aggregate unified-memory value.

If the subtotal is lower than the aggregate, the difference is displayed as **unallocated / uninstrumented remainder**. Unknown categories stay unknown. The UI must not distribute the remainder across categories or infer a complete decomposition.

This makes the accounting identity inspectable without pretending instrumentation coverage is stronger than it is.

## Timeline and correlation

Resource samples are first-class inspectable records. The rich fixture associates selected samples with exact episode, batch, checkpoint, source/preparation workload, and expansion/refinement identities. Live CP03 samples carry only the exact source/evidence/receipt references that the accepted record metadata supplies; GUI15 preserves those references without assigning unsupported correlation classes.

The highest-memory fixture sample is marked as a spike using both text/structure and styling, never color alone. Selecting a sample opens the global inspector with its stable resource identity and available correlation details.

## Historical comparison

Historical comparison is an exact read-only CP03 query. The operator supplies a concrete generation number. GUI15 does not invent a generation catalog and does not infer `current - 1`.

Historical mode never creates a live CP04 subscription. In live mode, CP04 `resource.*` events trigger only a new CP03 `resource` query. Other event families do not refresh the Resources view.

## Throughput is not learning

Accepted optimizer steps/hour, batching density, wall time, and memory use are resource facts. They do not imply retained improvement. GUI15 contains no success label derived from throughput and no scheduler, batch-policy, hardware-scaling, or training mutation control.

## Verification surfaces

- `apps/mission-control/tests/resources-view.test.mjs`
  - literal fixture metrics;
  - measured/configured/estimate separation;
  - aggregate/decomposition remainder reconciliation;
  - live missing-category honesty;
  - exact spike correlation fixture;
  - explicit historical generation binding;
  - resource-only event refresh;
  - no historical subscription;
  - read-only query shape.
- `apps/mission-control/electron/tests/renderer-protocol.test.cjs`
  - GUI15 assets remain inside the renderer allowlist.
- `apps/mission-control/tests/shell-state.test.mjs`
  - resource objects route back to the Resources owner surface.

Final integration remains governed by #1047/GUI21. GUI15 does not add a resource producer, mutate Rosetta Core, or create an Akasha/provider dependency.
