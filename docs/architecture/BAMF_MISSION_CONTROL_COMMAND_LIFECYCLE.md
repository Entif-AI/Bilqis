# BAMF Mission Control CP05 command lifecycle

CP05 is a guarded command gateway over the accepted C11 BAMF operator. It does
not own training, scheduling, admission policy, checkpoint custody, or learner
state. C11 remains the action owner and keeps the existing --human-run
boundary.

## Request and target identity

CP05 uses operator-action-request/v2 and operator-action-receipt/v2.
Version 2 permits a pre-run request for fresh creation and records explicit
human authorization. Version 1 remains unchanged and run-bound.

The service resolves an exact target before it accepts a mutating command. The
target records the canonical run directory and every available accepted
identity: run, generation, manifest, optimizer step, candidate, Factory
release, semantic release, topology, acceptance binding, and source identity.
Fresh create uses the deterministic C11 dry-run preview. It does not invent a
generation manifest or acceptance binding before those records exist.

The idempotency key identifies one semantic effect within one control-plane
command store. The request ID identifies one submission. CP05 normalizes the
effect across request IDs and timestamps. Reusing an idempotency key for a
different effect or reusing a request ID for a different operation fails
before dispatch.

## Durable fact sequence

The command store is outside the target run directory. Fresh create therefore
cannot be contaminated by control-plane bookkeeping. The store writes
immutable JSON facts with file and directory fsync:

1. submission and request-ID binding
2. preflight result
3. accepted command plan and ACCEPTED receipt
4. dispatch reservation
5. detached-worker PID
6. worker result and postcondition
7. terminal receipt

The accepted plan is durable before CP05 starts any mutating process. Once the
dispatch reservation exists, CP05 never starts that operation again. This is
an exactly-once admission decision with an at-most-once effect dispatch. It
does not claim impossible exactly-once execution across process failure.

## Execution and readback

Read-only status and checkpoint verification complete in the service process.
Dry-run create and resume use the existing C11 dry-run path and never start the
worker.

A mutating command starts one detached CP05 worker. The worker rereads the
accepted plan, verifies the target again, and then invokes the existing C11
CLI. The worker adds --human-run only when the request carries explicit human
authorization. Arbitrary command-line arguments are not accepted.

Successful process exit is not sufficient for a COMPLETED receipt. The worker
reads accepted BAMF state after execution and writes a postcondition record.
The terminal receipt binds the original request digest, operation ID, resolved
target, postcondition, and receipt references.

Admission-lease preflight is read-only. CP05 validates the enrollment request
against the accepted run, topology, and semantic release before acceptance.
The current C11 resume path can enroll a supplied admission scope even during
its nominal dry-run path, so CP05 never uses that path for lease preflight.
The actual lease command remains the accepted C11 --human-run --resume
operation.

## Restart and ambiguous outcomes

The detached worker writes to the durable operation store, not to service
memory. A service or GUI restart can recover the operation by ID.

The CP01 service also publishes every command receipt it returns as the CP04
`operator.action.state` event family. Those events are a disposable delivery
projection only. Durable command facts and authoritative BAMF readback remain
the recovery source, so replay loss or service restart cannot alter command
disposition.

Recovery only reads facts and authoritative BAMF state. It never respawns an
operation that has a dispatch reservation. If readback proves the requested
postcondition, CP05 writes COMPLETED. If the worker is still live, the receipt
is PENDING. If execution may have happened but no postcondition can be proved,
the receipt is OUTCOME_UNKNOWN.

A target change between acceptance and worker execution fails before C11 is
invoked. A failure to create the C11 subprocess is also a terminal failure.
After C11 starts, a nonzero exit can represent a partial effect. CP05 therefore
requires readback before it calls the operation complete and does not convert
an ambiguous process failure into a false FAILED claim.

## Supported action mapping

create, resume, and owner-launch use the accepted C11 lifecycle. status uses
the accepted C11 inspection surface. checkpoint-verify uses lightweight
accepted-generation inspection. admission-lease uses the existing accepted
lease operation after read-only validation.

CP05 reports pause as unavailable. Stop is supported only for an exact active
create/resume/owner-launch operation whose trainer process was launched under CP05
custody. Before SIGINT, CP05 rechecks the accepted lineage and the recorded process
identity so a stale PID cannot become stop authority. An interrupted trainer exit
records the authoritative interrupted postcondition and leaves the last accepted
checkpoint as the resume point. CP05 does not expose a generic remote process kill
or manufacture pause semantics.
