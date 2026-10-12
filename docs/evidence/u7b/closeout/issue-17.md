### U7B: causal witnesses did not prevent a curriculum shortcut (2026-10-11)

The exact 12/4/8/8 continuation completed 256 updates from U6 step 13,400. Cross-final accuracy rose 28/120 → 110/120, but AND was sampled only when both operands were TRUE and OR only when both were FALSE. A root-operator-only baseline scores 1,024/1,024 cross TRAIN and 120/120 cross final; the formal old/new NOT witnesses still change the answer. Frozen untrained sibling correctness fell 1,496/2,048 → 266/2,048. Boolean primitives fell 26/26 → 20/26; fresh U4 composites 13/32 → 2/32.

For a later #17 version, require distribution checks beyond formal causal influence: balance gate × operand truth × answer, freeze independent sibling holdouts before training and retain critical conservation as a separate promotion gate. The allocation is an implemented policy, not proven sufficient rehearsal. Preserve #111/U7 and U7B evidence. Correction requires a new version/freeze, not editing this run.

Detailed execution: https://docs.google.com/document/d/1O0lxmLU7Jc49An-nh2YNpi-GkniLBFjf6pDN-PgGDh8/edit (R-08 / U7B). Draft PR and immutable evidence: https://github.com/Entif-AI/Bilqis/pull/112 ; `docs/evidence/u7b/RESULTS.md` and `run-01/shortcut-audit.json.gz`.
