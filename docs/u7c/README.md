# U7C: corrected English-only spiral continuation

Stacked on draft PR #112 at exact base 2e1d6bb4c1111463724f66016f6c349ceef6f843.
All U7B and earlier frozen evidence remains unchanged. This successor starts
from the accepted after-U6.pt state and preserved AdamW step 13,400; the
failed U7B step 13,656 is excluded as a parent.

Run-01 is preserved as a superseded, pre-gradient exploratory freeze. Its
source tree was edited to implement a user-requested English teacher correction
before any training, and its original source hashes therefore no longer match
the resulting implementation. It is **not** a reproducible completed epoch.

Run-02 is the corrected immutable freeze and the sole authorized U7C training
epoch. It uses 12 current-stage / 4 fresh prior / 8 old-new composition /
8 DEV-targeted weakness examples per 32-row step. Its root AND/OR cases have
balanced outcomes per gate and 75%-accurate operator+single-arm baselines,
rather than U7B's perfectly predictive operator-only shortcut. Paired
same-world perturbation witnesses are retained separately from training.

Kev receives **English prose only**. Its 3 candidate descriptions include
concrete generated example worlds and questions, contrasted without gold
answers. The native inference transport necessarily serializes choices as a
request object, but no typed ABI, grammar JSON, oracle gold or numeric teacher
embeddings/probabilities is placed in the teacher's natural-language context.
All candidate identities, gold answers and typed compilation remain internal.
Review is an explicit valid option. No EG2 calls occur for these known
definitions.

The old varied/composite diagnostics are adaptive DEV and can steer the
teacher and training weights. Fresh final material remains absent from the
training executor and opens once after training. Frozen critical DEV retention
is measured at 16-step boundaries. The run must stop early if primitive
correctness drops below 24/26, historical U4 composites below 42/128,
U4 varied below 73/128, U0 composites below 66/128, or lineage below 4/10.

Frozen preflight, test targets, and all exact source hashes are preserved under
docs/evidence/u7c/run-02. The model continuation commands are:

    python3 -m bilqis_u7c.run train
    python3 -m bilqis_u7c.run evaluate
    python3 -m bilqis_u7c.run replay

Training emits exact per-update examples, categories, DEV weakness hashes,
retention checks and native Kev traces. Replay reruns the complete gradient
sequence from step 13,400 without repeat Kev calls and verifies predictions
after the single final evaluation.

Versioned successor admission rule: require bilqis_u7c.grammar.audit_cohort
to pass independent-oracle, non-overlap, gate-balanced, operand-conditioned
baseline and paired-arm checks on both TRAIN and the future final cohort before
any gradients. Do not reuse the old bilqis_spiral.sampler.cross_case or
bilqis_teacher.grammar.compile_exercise as fresh shortcut-safe generators;
they deliberately remain unchanged only for historical replay. The stable
policy identity is u7c-english-balanced-1, frozen under the run-02 source hash.
The existing repository-root FEATURE_LOG.md belongs to U7B and is not a U7C
working-state file. U7C follows branch/issue-scoped checkpoint receipts.

Run-02 stopped after 32 gradients at 13,432 due to critical U4 composite and
lineage retention failure. Its 288-row balanced cross final improved only
161 to 162, and the separately scored 144 pre-frozen causal triples were
correct in full only 9 to 10 times. The result is negative; the literal
prior 256-update budget was a cap, not a license to override the stop gate.
