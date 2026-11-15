# #1238 candidate identity binding: DESIGN / EGM receipt

## Authority and review boundary

Issue [#1238](https://github.com/Entif-AI/Bilqis-MLX/issues/1238) is the implementation
authority for reusing the complete raw-v2 `CandidateState` numerical identity after
one immutable-state proof. The reviewed branch is
`codex/1238-candidate-identity-binding-20261115` from unified base
`cde85fe91e251b65f844befffcd3e2f3f0f47ea3`.

The design review used Google Elephant-Goldfish Model at the exact pinned commit
`b3a35956759bf7f024af2ff061b2e0b44b438e4c`. Fresh Goldfish contexts read the
actual EGM design/codebase/readiness personas and standards, the live issue,
the current repository source, and `docs/evidence/bamf/ISSUE1238/design.md`.
They did not receive authority to modify production code or run a learner.

Final reviewed design SHA-256:
`2a428a9449ecd2ff80b166647b77b1622067f2f73834b7270602811d44ca57e0`.

## Findings that changed the design

The first review found two Blockers and several Majors. The design was repaired
before implementation:

- MLX 0.32.4 exposes a zero-copy NumPy `__array__` path in addition to Python
  buffer/DLPack/state paths. The guard now capability-probes and covers every
  runtime-provided zero-copy export, plus the exact mutation-slot inventory.
- Motif C05 resolved one transaction twice. The contract now requires one exact
  resolved `CandidateState` through C05, decision, acceptance and B13.
- The binding and bindability registries now use `id(state)` plus weak-reference
  identity checks and callback-safe cleanup; ordinary weak-key hashing is not
  assumed for frozen candidate/optimizer records.
- The complete current production `candidate_identity_digest(...)` census is
  classified in the design rather than deferred to implementation.
- Fresh genesis, cold genesis and cold non-genesis verification now make the
  first bind itself the single full-content proof instead of verify-then-rehash.
- The retained environments differ: native documentation targets MLX 0.32.4,
  while current hosted quality/release installs 0.31.1. Support is therefore
  capability-gated rather than version-string-gated, with canonical hashing as
  the correctness fallback when the optimization cannot be installed.
- Step/visit metrics now have exact field names, counter ownership and sink
  boundaries in existing `FactoryCandidateStep.realized_cost` and resource
  observations.
- The runtime barrier's correctness boundary is explicit. It protects supported
  Bilqis/MLX paths and poisons bindings on live slot drift; it does not claim to
  sandbox hostile in-process native code, pre-captured original C descriptors,
  debugger/raw-pointer writes or transient bypass-and-restore monkeypatching.
  A repository audit found zero production captures of those descriptors or
  raw-pointer/`ctypes` candidate writes outside the proposed guard owner.

## Final EGM result

- **Design Critic:** PASS. No remaining Blocker/Major after the explicit threat
  boundary, pre-BINDABLE guard-install requirement, caller-owned UNBINDABLE rule
  and descriptor/raw-write audit gate.
- **Codebase Details:** PASS. No remaining Blocker/Major from the original
  `__array__`/export, motif continuity, registry, callsite census, target scope,
  telemetry, cold-proof or MLX-version findings.
- **Implementation Readiness:** no Blocker/Major. Its one Nit was a wording
  contradiction about canonical byte reads; the final design keeps raw-v2 bytes
  in `identity.py` and uses the saved original MLX state bridge only for storage
  metadata/currentness.

This satisfies the required `DESIGN -> EGM REVIEW` gate. It is not implementation
proof, drift review, premerge proof or merge authorization.

## Preserved ownership boundaries

- #1169 remains the canonical raw-v2 identity format and byte contract.
- #1231 retains live visit/step currentness ownership.
- #1237 retains persisted B13 parent/child hydration ordering.
- No persistent human learner, durable student mutation or self-merge occurred
  during design review.
