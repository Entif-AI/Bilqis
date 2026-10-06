# Bounded decision qualification

The #65 harness feeds the same owned fixture to Kev's official loopback System
One server, SemIf's native MLX library, and a small generative MLX control. Each
engine uses a separate environment. No scorer defines gold, receives SEALED
material, initializes the student, or changes promotion gates.

The frozen fixture contains 12 two-oracle finite-world decisions, five existing
curriculum-policy decisions, six explicitly typed relation-family diagnostics,
and two unlabeled review cases. Label origin, source posture, candidate IDs and
ordering, and contamination uncertainty are recorded. The source-rights registry
is the scoped #35 Phase-A disposition; it does not close Phase B.

The fixture freezes diagnostic thresholds before outcomes: local proposal score
at least 0.8 with margin at least 0.2; primary accuracy at least 0.8 over at least
20 labeled cases, with zero confident wrong/local wrong completions. These are
exploratory engineering gates, not calibrated truth confidence or SYS-01 rules.
ECE is omitted below 100 labeled items. `decision_qualification.classify` admits
only calibrated K1 and source-precision S1 as primary profiles. K3 temperature
1.0 remains diagnostic regardless of its result.

The adapter preserves native distributions and metadata, including prefix-cache
readback. Kev serializes probabilities to four decimal places; bounded rounding
error is allowed without rewriting the native distribution. Generative output
must identify a supplied candidate; invalid prose is recorded as a failed
decision rather than repaired or hidden. Model load, inference wall time, MLX
allocator memory, shared-batch amortization, and generation usage remain distinct.
Kev's API `output_tokens` counts serialized answers, not generated model tokens.

`curriculum_proposal` consumes typed scores only for already-eligible stages.
Review/unsupported/ineligible outcomes use the existing deterministic fallback;
the teacher state and promotion history remain unchanged. Relation diagnostics
are proposals, not accepted graph edges. Model output never replaces source,
ABI, collision, or oracle validation.

Use `python -m bilqis_ref.decision --help` for the common CLI. Invoke it from the
Bilqis checkout with the selected engine's Python environment. Identity files
bind exact source and model revisions. Output directories must be new; rows are
flushed incrementally so interrupted attempts remain evidence. Direct, serial,
and shared SemIf modes share the frozen checkpoint. Quantization is a separate
profile with the documented 256 MiB inactive allocator-cache policy. Quantized
peak allocation includes loading and quantizing the source checkpoint.

The generative control uses the same pinned Qwen checkpoint and MLX runtime as
SemIf, with temperature zero and a 128-token limit. This bounded control avoids
substituting the separately installed community LM Studio model for a matched
mechanism comparison. No new generative service is required.

Public qualification evidence lives under `docs/evidence/decision-qualification`.
Machine paths, process controls, launcher state, and raw host inventory remain
host-local. This setup does not authorize SYS-01 use; #22 must freeze identity,
privileges, fallback and budget before any such trial.
