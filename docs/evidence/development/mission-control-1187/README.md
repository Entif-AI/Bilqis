# Mission Control issue #1187 — Model usability evidence

## Authority

- Issue: `#1187 Mission Control UX implementation | Model`
- Branch: `codex/1187-mc-model-20261115`
- Initial reviewed-unified base: `12ff747f92c2b60cd6066174c6eb025f863e003c`
- Required shared dependencies #1181 and #1182 were confirmed merged and ancestral to the base before implementation.
- Prior Model authorities #1134 and #1143 were read before repair.

## Implemented contract

- `Neural` and `Frames` remain the sole peer mode layer; no nested Model tabs were introduced.
- Model deep links now preserve the selected peer section and fixture diagnostic mode.
- Production Neural queries the accepted `neural` family for the exact current or historical context and renders only `NeuralRuntimeSample` fields plus authoritative RecordMeta times.
- Production Frames fail closed with an affirmative unavailable state and never mount or query the fixture Frame Explorer.
- Fixture-only Neural/Frame diagnostics, labels, generations, and help copy are loaded only through explicit fixture launch support.
- Fixture Neural current/historical generations align with the route-visible reference generations 7/6.
- Contextual help uses the shared primitive for topology/runtime, measured-vs-derived posture, CCGQA, AttnRes, refinement, instrumentation, Frame concepts, controls, frontier, and provenance.
- Dense CCGQA, AttnRes, and refinement receipts use progressive disclosure.
- Source observation/materialization times use the shared temporal primitive only when actual source timestamps exist.
- The prohibited defensive sentence about packing and semantic competence was removed; explanatory copy is affirmative and mechanism-focused.

## Focused verification

The bounded owner/regression ring is intentionally limited to the affected Model and shell contracts.

- 68 focused Node tests passed across shell routing/bootstrap, Model domain ownership, Neural production/fixture rendering, Frame Explorer/Frame shell, and renderer protocol boundaries.
- `npm run mission-control:production-boundary:test` passed with the production renderer dependency graph fixture-free.
- Legacy Model visual witness passed dark/light, comfortable/compact, 1440/390/320, RTL + text-spacing, reduced motion, local table overflow, and accessibility checks after a 320px heading/help reflow repair.
- `python3 -B scripts/check_module_size.py --changed-from review-source/codex/bamf-unified-base-20261028` passed.
- `python3 -B scripts/quality/check_governance_integrity.py --base-ref review-source/codex/bamf-unified-base-20261028` passed.
- `git diff --check` passed.
- Full-shell production/fixture rendered journey passed six variants under `output/playwright/1187/`: production and fixture launch at 1440 dark/comfortable, 1440 light/compact, and 390 light/compact. Every variant reported zero Axe A/AA violations, no document overflow, exactly two Model peer controls, and no nested tablist.
- The full-shell journey also proved desktop collapsed-rail + resized-inspector geometry, narrow modal inspector behavior, production Frame zero fixture queries, production Neural accepted-sample timestamps/authority, fixture Neural gen6 historical route rehydration, and the cold `Frames gen6 -> reload -> Neural current gen7 -> Frames gen6` provenance transition.

No aggregate repository suite was run because the changed dependency surface is bounded to Mission Control Model/shell/protocol behavior.
