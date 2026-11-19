# BAMF-0.3 C14.4 asynchronous swarm contributions

Issue #559 adds an untrusted remote contribution boundary to the continuing BAMF school. It does not create a second school, a distributed optimizer, or a remote admission authority.

## Authority boundary

A remote worker receives a frozen work manifest and may return signed evidence or a learned candidate. The worker never receives writable canonical-school custody. A valid worker signature authenticates the returned bytes and the worker's declared environment; it does not make a learning claim true and it does not authorize state mutation.

Every manifest binds the retained generation, semantic/source release, capability, deterministic seed and partition, resource envelope, model implementation identity, topology identity, worker-runtime identity, rights scope, contribution class, expected artifact type, acceptance contract, expiry and replay identity.

Only `PUBLIC_FIXTURE` and `PUBLIC_DERIVED` material is eligible for this public/remote boundary. `PRIVATE_REAL` and `UNCLASSIFIED` inputs fail closed before dispatch/admission.

## Signed receipt and replay

The worker receipt signs:

- manifest digest;
- worker public key and environment identity;
- artifact type, digest and declared parameter scope;
- claimed score;
- claimed examples, steps, elapsed seconds and payload bytes;
- completion time.

The resource counters are authenticated worker claims, not independent metering. Payload bytes are locally checkable. The manifest's MLX identity must match the signed worker environment's MLX version. Canonical acceptance never relies on the worker's claimed score.

After cryptographic verification and current-school identity checks, the canonical coordinator atomically consumes the manifest replay identity in a durable create-once replay store owned directly by the canonical run directory. The caller cannot substitute ephemeral replay custody. A fresh coordinator process reconstructs consumed replay identities from that store; replay does not become legal after restart.

## Non-neural contributions

Evaluation, curriculum/counterexample, motif-candidate and regression evidence may be independently evaluated without changing canonical neural state. Before evaluation, the manifest must still match the current B13 generation, source release, implementation identity and topology, and its capability assignment must equal the canonical evaluation target. The independent canonical evaluator supplies the evidence digest and pass/fail result. A worker score cannot override that result or a required retention outcome.

## Learned contributions

The first learned contribution class is deliberately narrow: a bounded `ADAPTER_DELTA` manifest must return an exact canonical C12 cognitive-package wire artifact. Arbitrary dense updates remain fail closed because C14.4 defines no aggregation law.

The learned path is:

```text
signed remote receipt
  -> exact worker MLX identity check
  -> exact current B13 generation / source / implementation / topology check
  -> exact manifest capability / canonical target match
  -> canonical C12 package decode and exact binding check
  -> durable run-owned replay claim
  -> current A12/C09 source-rights clearance
  -> disposable C12 delta application
  -> current Factory-owned C05 retention/admission screen
  -> exact C05 policy-digest match to the remote manifest
  -> B13 atomic PACKAGE_IMPORT publication, only when C05 accepted
```

C14.4 does not expose an arbitrary `canonical_admitter` callback. The existing C12/C05/B13 owners remain the only route by which a learned remote candidate can become canonical state.

A learned manifest's score threshold is fixed to zero because C14.4 does not invent a second numeric acceptance rule beside C05. Its `acceptance.contract_digest` must instead equal the exact C05 policy digest that adjudicated the candidate, and `requires_retention` must be true.

If C05 rejects the candidate, no B13 publication is attempted. Rejection may leave protocol evidence such as the replay claim and decision receipt, but it cannot mutate canonical neural weights, optimizer state, motif allocation, semantic activation or teacher history.

## Opportunistic dispatch

`dispatch_eligible_work` is deterministic and optional. With no available remote workers it returns no assignments and local school operation continues unchanged. Swarm availability therefore cannot become a prerequisite for ordinary local learning. The public synthetic worker fixture receives only canonical manifest bytes plus its bounded artifact/signing inputs; it has no canonical run-directory argument or writable school handle.

## Scope and non-goals

C14.4 does not define cryptocurrency or incentive economics, global synchronous SGD, trust-by-membership, private-source publication, or C08.4 tightly coupled multi-device execution. It also does not claim independently measured remote resource usage from a signed worker declaration.
