# Exploratory Bilqis alpha 0.1.0

Owner: [#102](https://github.com/Entif-AI/Bilqis/issues/102), followed by
[#103](https://github.com/Entif-AI/Bilqis/issues/103). The source-audit correction
on #102 controls: CP0008 is preserved as an engineering reference.

This projection implements #80's typed terms, directed binary predicates,
equality, NOT/AND/OR and nonempty finite EXISTS/FORALL, mapped through #7.
The two-object relation domain is a finite interpretation of predicate logic,
not a new color/use ontology. Supporting and refuting evidence remain independent.
The explicitly local Belnap-Dunn truth-order evaluator preserves TRUE, FALSE,
UNKNOWN and CONFLICT. It does not select a universal logic for #80.

The registry freezes semantic identities, typed signatures, roles, prerequisites,
dual/contrast edges, four-state truth tables and source mappings. These compile
to inspectable features and a fixed DCT width transform with FP32 embedding RMS
0.02. Semantic identity and token integer allocation are separate. Aligned,
IID and semantically permuted profiles share the student topology; only aligned
receives a full alpha training cycle. Pre-step controls do not establish causal
benefit. No pretrained weights, teacher states or external embeddings enter it.

The student reuses `bilqis_ref.model.Block`, `QLinear`, batching and state hashes.
Only its alpha-local input embedding/answer identities replace the fixed CP0008
512-row ABI. Linear forward weights are ternarized and activations emulate int8;
master/optimizer weights, embeddings and answer readout remain FP32. Execution is
CPU reference arithmetic. There is no native low-bit or Apple-GPU speed claim.

Install with Python 3.13 (native macOS Torch has no `+cpu` wheel suffix):

```sh
uv venv --python 3.13 .venv
uv pip install --python .venv/bin/python -r requirements-alpha.txt
node ~/.codex/hooks/validation-output-runner.mjs -- .venv/bin/python -m unittest discover -s tests -v
```

One command trains the fixed 1,536-step, batch-32, seed-102 lineage and saves its
real checkpoint, optimizer, pre-step geometry, trajectory, raw predictions and
resource receipts. It refuses to overwrite an existing run:

```sh
.venv/bin/python -m bilqis_alpha.run train --output runs/alpha/epoch-01
```

The first 512 steps use relation/equality/negation, then all frozen TRAIN patterns
with those earlier rows retained. A saved stage checkpoint and known-case probes
make retention visible. This is a fixed schedule, not a mastery promotion claim.
DEV worlds are separated by world hash. All four HELDOUT AST shapes are excluded
from optimization. The full heldout plane was scored after training; two named
boundary fixtures with those patterns also received intermediate diagnostic probes.
The fixed training schedule never used their results. The timing deviation is
preserved in `docs/evidence/alpha/microscope/protocol-audit.json`.
The splits and exact corpus hash are frozen in `fixtures/alpha/split-manifest.json`.
The heldout plane is exploratory, already exposed by this batch, and not SEALED.

Verify every saved prediction against fresh-process inference:

```sh
.venv/bin/python -m bilqis_alpha.run verify --output runs/alpha/epoch-01
```

Machine evidence lives under `docs/evidence/alpha/`. Model and optimizer binaries
stay in the ignored local run directory under repository contribution policy.
The preserved command rebuilds them; an absent checkpoint is a replay error,
never an invitation to substitute an oracle or untrained model. Model-state
identity and replay tolerances are reported separately from file-byte identity.

The exhaustive four-state tables preceded the evaluator; the full named-vector
artifact was assembled before training with explicit contract-derived expected
strings, after evaluator code existed. An injected UNKNOWN→FALSE label is detected.
This provides a separate expectation path, not a cold human audit or a second
independent specification lineage. The append-only audit corrects the frozen
metadata's broader chronology claim. Unsupported operators, free variables,
shadowed binders, invalid roles and missing fields reject explicitly; they never
become UNKNOWN. Commutative arguments and evidence order canonicalize; the codec
is lossless over the supported domain and never includes a gold label.

Omissions retain their original owners: full ABI (#7), remaining T0–T4/proofs and
ambiguity (#80), mathematics (#85), Rosetta epistemic algebra (#84), complete
pre-language freeze (#86), full curriculum (#17/#82), Apple-GPU qualification
(#52/#64), attribution (#28/#62), and confirmatory SYS-01 (#22–#25). One seed and
four withheld shapes over two objects cannot establish broad reasoning ability,
semantic-initialization advantage, economic savings or developmental admission.
