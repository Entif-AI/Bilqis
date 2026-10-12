# Replay the trained semantic microscope

[#103](https://github.com/Entif-AI/Bilqis/issues/103) consumes the exact #102 model
from [PR #104](https://github.com/Entif-AI/Bilqis/pull/104). It adds no training,
semantic primitives or learned explanation interface. Package version 0.3.0;
microscope/fixture versions 0.1.0; underlying alpha semantics unchanged.

From this worktree, one fresh-process command replays and verifies the frozen story:

```sh
.venv/bin/python -m bilqis_alpha.microscope --run runs/alpha/epoch-01 --verify docs/evidence/alpha/microscope/replay.json
```

Use `--json` for complete canonical inputs, role/binder identities, logits,
probabilities, formal results, exact semantic deltas, selection/explanation
provenance, split memberships, pinned hashes and resource receipts. Human display
and generic typed JSON describe the same canonical input; they are not separately
trained comparison arms. Reordered evidence has the same canonical identity,
compiled tokens and live prediction, even when that prediction is wrong.

The microscope includes all 15 pre-training known boundary fixtures, five validated
single-factor changes (role assignment, negation, scope, one evidence addition and
one removal), named heldout compositions and the first observed heldout miss by
frozen corpus ID. This gallery deliberately preserves wrong model answers. All
5,135 original neural results remain available in #102's full raw evidence.

The scope pair NOT(EXISTS R) / EXISTS(NOT R) gives a visible, correctly learned
FALSE→TRUE response. The mutual-relation EXISTS fixture was actually excluded
from TRAIN. Role reversal and conflicting evidence also expose weak behavior;
their formal change does not imply the model recognized it.

The candidate-path witness deliberately replaces R(a,b) with R(b,a) in
`R(a,b) OR NOT R(b,a)`. Its relation identity and intermediate oracle consequence
are wrong, while the final oracle remains TRUE. This is an **independently
evaluated candidate**, never an attributed network choice. Both final inputs get
actual neural inference. Neural intermediate relation decisions are MISSING:
this architecture exposes final logits only. An unsupported implication path is
rejected before inference, separately from UNKNOWN. The regression checker also
catches an injected UNKNOWN→FALSE label and restores the reference; this is formal
validation, not neural self-repair.

No inference result is read out of the frozen replay receipt. Replay always loads
the real checkpoint, checks its file/state and initializer/source bindings, runs
inference, then compares outputs at absolute logit/probability tolerance 1e-6.
Wrong, absent or untrained replacements reject. A missing local binary is an
explicit blocker; follow [ALPHA.md](ALPHA.md) to install the pinned environment
and regenerate the bounded source lineage. Repository policy keeps model binaries
in the ignored `runs/` directory; raw neural text evidence is committed.

The alpha demonstrates partial learning and a reproducible microscope. It does
not establish reliable general reasoning, full #80/#86 semantics, an initializer
advantage, CPU/GPU parity, native low-bit efficiency or SYS-01 acceptance. The next
small experiment remains the atomic directed-relation/sparse-evidence diagnostic
recorded in #102's report, outside this completed batch.
