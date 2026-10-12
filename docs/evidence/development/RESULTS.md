# Developmental continuation: U6 -> U7E -> U7F

**Status:** A single semantically initialized, cumulative neural student has
progressed to a *new selected* checkpoint at AdamW step **13,848**. The
training workflow advances the same learned weights and optimizer state,
instead of beginning a new randomly initialized student. This is capability
development, **not scientific attribution**, and the live development
dashboard can inform teaching.

## Active continuity

- U6 parent: 13,400 optimizer updates, SHA256
  248a82ac92005f7b245751d6ea211d8296189de797f702349451f74383d75799.
- U7E: 640 exploratory continuation updates were attempted. The best
  non-destructively selected successor occurred at 128 updates
  (step **13,528**), checkpoint SHA256
  39167cec6000873938ac8afefad333db092756f9fe42bca9737f93bf1b3bb5e5.
- U7F: strengthened previous-competency rehearsal and distillation with
  20/32 old-skill training examples, and continued from U7E step 13,528.
  A first attempt of 384 updates disclosed valuable capabilities alongside
  some variation declines and selected no successor because its initial
  per-family tolerance rule was excessively rigid. It did not overwrite U7E.
  An append-only v0.2 teaching pass recovered that better demonstrated
  functionality from the **same inherited U7E checkpoint**, trained 320
  additional updates, and selected step **13,848**.
- **Active checkpoint** SHA256
  8752457dc6fec2ced061ee206bcec4b9473d8270347515ba8bf98f22b5c2c174.
  Model-state SHA256
  e1e91bf22e2ddc4791f5004879b60ba7f17783521493fc444c83e8a6dfc35d68.
  AdamW-state SHA256
  f50cd801e7ff11fe0b7bd44f1c694580c87d9757b64bcdf98f166b8744f10618.
  Semantic registry remains **113 unchanged token identities**. The verified
  local binary is held separately at
  ~/Code/bilqis-learner-custody/active-u7f-13848.pt. No neural binary
  is committed to this repository.

The selected neural lineage contains **448 additional retained optimizer
updates after U6**, not 1,344: exploration after rejected checkpoints is
preserved as development evidence but is not the live student's state.

## Real capability readbacks

| Functional task | Before: U6 | After: active U7F |
| --- | ---: | ---: |
| Original provenance vs supersession diagnostic | 4/10 | **7/10** |
| Both correct on a fixed 184-pair direct+chain event-link dashboard | 33/184 | **75/184** |
| Boolean primitive accuracy | 26/26 | **26/26** |
| Historical U4 evidence composition | 50/128 | **61/128** |
| Historical U4 varied | 81/128 | **87/128** |
| Historical U0 composite | 74/128 | 72/128 |
| Historical U5 varied | 174/320 | 153/320 |
| Historical U6 varied | 213/320 | 205/320 |

The new event-link evaluation comprises paired **changing-link worlds**:
only the link kind changes, while the question and event facts stay fixed.
Both answers must be correct for the pair to count. The actual model
inference (not a deterministic oracle substituted at runtime) improved
from 33 to 75 jointly correct pairs, with 47 individual pair gains and
5 pair regressions in the fixed development dashboard.

### One concrete neural behavior change

The model receives two worlds with otherwise identical events and the
same question, DERIVED_FROM(E1,E0).

| Only world link | Exact finite oracle | Before (U6 neural) | After (U7F neural) |
| --- | --- | --- | --- |
| DERIVED_FROM(E1,E0) | TRUE | TRUE | TRUE |
| SUPERSEDES(E1,E0) | FALSE | TRUE | **FALSE** |

That is a genuine newly learned distinction for this recorded example,
not postprocessed teacher logic. Other same-family examples still fail.
For example, direct DEPENDENCY both-correct remains 0/20 in the selected
development dashboard; the original lineage diagnostic is 7/10, **not**
10/10. The student has not reached broad compositional mastery.

## Explicit development tradeoff

The improvement is **not free**: U5 varied scores are lower by 21/320
(6.6 percentage points), U6 varied by 8/320 (2.5 points) and U0 composite
by 2/128 (1.6 points). U4 evidence composition improved by 11/128
and the small critical link diagnostic by 3/10, while the broader event
contrast-pair skill gained 42/184. The selected checkpoint reflects a
practical capability-first compromise with transparent losses, not a claim
that every old task improved.

## What future work must do next

1. Continue from the **active** U7F step-13,848 model, with its optimizer,
   rather than U6 or randomly initialized weights. The fail-closed Python
   entrypoint is bilqis_active.load_active(), bound to the
   versioned docs/development/ACTIVE_LEARNER.json manifest.
2. Target the stubborn proof-premise DEPENDENCY distinction, U5 set/function/
   graph variations and hard event compositions. Produce contrastive examples
   that reuse already acquired operators and pre-structured semantic geometry.
3. Preserve old competence by rehearsal/distillation and select the best
   **overall functioning student**, acknowledging that temporary local
   tradeoffs can be justified for meaningful net capability gains.
4. Permit sourced pretrained teacher/embedding transfer when it improves
   performance, while maintaining unambiguous semantic identity and oracle
   authority. Do not impose scratch-only controls as a developmental rule.

The complete per-step DEV dashboard and two run-local checkpoints remain
ignored in the preserved local runs/ directories; this public summary
intentionally excludes proprietary, binary or personal-system payloads.
Development owner: #108. All historical negative U7B/C/D evidence remains
unchanged. No PR was merged and no curriculum Stage A-F was claimed complete.
