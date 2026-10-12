# BILQIS-ALPHA-02 — frozen semantic microscope

Uses #102's actual checkpoint SHA-256
`002cffcfbdf44eec2e509704d5a530bb134d655919ec129f46eeffda6b99a3eb`.
Implementation code: `26733370c2b7d896904c03e83dcb5850fde2bd64`.
Microscope/fixture 0.1.0, package 0.3.0, alpha semantic and initializer versions
unchanged. No additional training was performed.

Fresh-process verification reproduces **20 cases: 7 correct, 13 wrong**, and one
unsupported implication path rejected before inference. All 15 pre-training named
boundaries are retained; additional rows cover evidence addition/removal, the
first observed heldout miss by corpus ID and a wrong-candidate final-verdict witness.
Five independently validated single-factor interventions preserve unrelated fields.
43 local test methods pass, with zero failures/errors/skips. Numerical replay
tolerance is absolute 1e-6 for logits and probabilities. `replay.json` contains the
complete canonical states, live logits/probabilities, oracle answers, source bindings,
semantic deltas and split evidence; `transcript.txt` is the readable rendering.

The scope pair is informative: NOT(EXISTS R) changes from untrained TRUE (wrong)
to trained FALSE (correct), while EXISTS(NOT R) remains correctly TRUE. The named
mutual-relation EXISTS heldout is correctly TRUE **both before and after training**;
that particular cell does not establish acquired transfer. Overall heldout macro
accuracy improves from 31.2% to 45.5%, but the full-domain and named failures remain
too broad for a reliable reasoning/generalization claim.

Role reversal leaves the neural prediction UNKNOWN for both TRUE and FALSE cases.
Adding refutation changes the oracle TRUE→CONFLICT, while the trained model changes
UNKNOWN→TRUE: the semantic delta is genuine, the neural response is wrong. The first
heldout miss predicts TRUE when the oracle is UNKNOWN. These are visible failures,
not omitted or repaired by the oracle.

The wrong candidate interprets R(a,b) as R(b,a) inside an OR expression. Formal
relation outcomes change TRUE→FALSE; the unchanged downstream NOT term is TRUE;
both final formal verdicts are TRUE. Relation identity/consequence are scored wrong
despite the matching terminal verdict. This is a separately evaluated candidate,
not an inferred network decision. Actual neural inference on both final inputs is
UNKNOWN, also wrong. The network's intermediate relation interface is explicitly
MISSING, not fabricated.

Reordered evidence preserves canonical identity, codec tokens, oracle and live
prediction. Generic typed JSON is an information-matched alternate display, not a
trained causal comparator. An injected UNKNOWN→FALSE label is demonstrably detected
and restored in formal validation; no neural self-repair is claimed.

A read-only pre-step audit also finds identical initial embedding rows for the
source and target role tokens. Operator features encode role membership and
sensitivity, but this coarse initializer does not separate every individual role
row. AST/codec role identities remain distinct. The relation to weak binding is an
**untested hypothesis**, not an established cause. Full role/geometry qualification
remains #81/#62/#28; see `role-geometry-audit.json`. A next epoch could test that narrow
distinction while holding the already exposed domain and budget fixed. It was not
executed here.

All #102 limitations remain: one seed/two objects/four heldout shapes, no independent
SEALED worlds or cold human oracle audit, no trained IID/generic attribution arm,
no full COGAL/Rosetta/mathematical freeze, no MPS/native-low-bit qualification and
no SYS-01 acceptance. This batch ends with partial learned behavior and a replayable,
failure-visible alpha, not entry into the full developmental program.

Postflight protocol/provenance correction: the full 1,024-case HELDOUT plane was
scored after the final checkpoint, but K09 and K10 share heldout patterns and were
also in intermediate KNOWN diagnostic probes at steps 0–1,536. They never entered
optimizer batches or an adaptive teacher, and no tuning followed their results.
The claim of strictly final-only heldout inference does not apply to those two
fixtures. Training-composition isolation remains intact; this is exploratory,
already exposed evidence. See `protocol-audit.json`.

The four-state tables preceded evaluator implementation. The complete named-vector
artifact was assembled before training, after evaluator code existed, with explicit
expected labels rather than generated evaluator outputs. An extra raw-evidence test
was added after training. The frozen metadata's blanket before-implementation wording
overstates chronology and is corrected by the append-only audit. There was no cold
human/specification-independent audit; no input, label, split or checkpoint changed.

Exact fresh-process command and checkpoint-location policy: [MICROSCOPE.md](../../../MICROSCOPE.md).
