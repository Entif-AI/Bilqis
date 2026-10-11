# U7 spiral consolidation: frozen 12/4/8/8 successor

This exploratory successor is stacked on U5/U6 draft PR #110 at commit
e1e014b7bfee29f1a39976140b0c72eb69dbf8b2. It does not rewrite U6
checkpoints, original generators, or historical prediction inventories.
The frozen successor is at docs/evidence/spiral-u7/run-01.
Its parent learner has a recorded 13,400-step AdamW state.

Each 32-example batch contains:

| Category | Count | Generation and controls |
| --- | ---: | --- |
| Current U6 | 12 | Existing U6 TRAIN examples after excluding frozen evaluation identities |
| Fresh prior U0–U4 | 4 | New calls to the canonical old generator, without replacement and with all ancestor identities excluded |
| Old/new semantic composition | 8 | Four U5 and four U6 compositions, each with independently checked contrasts proving that perturbing either inherited U1–U3 or new typed operand changes the answer |
| Weak-skill reinforcement | 8 | New oracle-checked family-specific old/new variants, at least two older and two recent per batch, maximum three from a family |

The previous run's repeatedly inspected varied and composite probes are
classified as DEV for weakness adaptation. Every 16 optimizer updates, the
weak-skill weights refresh from measured current DEV error and deterioration
from the U6 starting DEV accuracy. Weights have a nonzero floor and a cap.
Both old and recent families receive reinforcement. The final cohort never
feeds DEV selection or the optimizer.

A distinct final evaluation cohort of 448 varied/composite cases was generated
and locked before optimizer updates. None shares an identity with any parent
training/evaluation example or successor training candidate. Its first
before/after score is computed only after training. This is an exploratory
single-opening cohort, not preregistered unbiased scientific evidence.

The frozen run contains 1,888 new training identities, 256 causally checked
old/new comparison witnesses, 448 final examples, DEV starting scores,
parent source/checkpoint hashes and locked category policy.

To verify the sampler without running training:

    python3 -m unittest discover -s tests -p test_spiral.py -v

The optional bounded continuation is:

    python3 -m bilqis_spiral.run train --run docs/evidence/spiral-u7/run-01
    python3 -m bilqis_spiral.run evaluate --run docs/evidence/spiral-u7/run-01
    python3 -m bilqis_spiral.run replay --run docs/evidence/spiral-u7/run-01

Training writes an exclusive per-step exposure log with exact category counts,
row identities, semantic families, weak-skill weights/policy hashes, loss,
gradient norm and token counts. Checkpoints preserve student and AdamW state.
Replay starts from the original U6 parent and recomputes every training update.

Current state: policy and cohorts frozen; no successor training or claimed U7
neural improvement; no merge.
