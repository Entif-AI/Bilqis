### U7B falsifier for #38: perfect operator-only label baseline (2026-10-11)

U7B inherited a generator setting root AND when both operands are TRUE and OR when both are FALSE. It passed independent oracle, type/codec and two-arm counterfactual tests, yet a predictor reading only the root operator scores 1,024/1,024 cross TRAIN and 120/120 cross final. Neural cross-final rose 28/120 → 110/120 while already-frozen untrained counterfactual-sibling correctness fell 1,496/2,048 → 266/2,048. The apparent gain does not establish learned composition.

Add this falsifier to the future pre-training auditor: operator/shape-only and operand-blind baselines, gate × operand truth × gold contingency tables and independently split/frozen sibling checks. A perfect structural cue must block integrity acceptance even with disjoint world IDs and formally active operands. This run is marked FAILED_PERFECT_ROOT_OPERATOR_LABEL_SHORTCUT, with no post-unblinding corpus repair or replacement training run.

Detailed execution: https://docs.google.com/document/d/1O0lxmLU7Jc49An-nh2YNpi-GkniLBFjf6pDN-PgGDh8/edit (R-08 / U7B). Draft PR and immutable evidence: https://github.com/Entif-AI/Bilqis/pull/112 ; `docs/evidence/u7b/RESULTS.md` and `run-01/shortcut-audit.json.gz`.
