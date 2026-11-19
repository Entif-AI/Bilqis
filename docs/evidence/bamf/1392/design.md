# Bound MLX allocator recovery to one Factory candidate

[#1392](https://github.com/Entif-AI/Bilqis-MLX/issues/1392) owns this repair. The reviewed starting baseline is `204a5f4769189b1dd9d334f1b7a85b4133a48110`, which already includes `main` at `5bf4092d8478bf68d6e0f3a886b55e7995c9e62f`.

## Problem and scope

The native Factory candidate calls B11 gradients and B12 AdamW admission without a caller for the existing C08 recovery transition. An MLX allocator error can escape the candidate horizon and end the operator command. The repair gives the same logical step one retry at a genuinely smaller partition, preserves accepted B13 custody, and lets the operator consider the next lawful READY target after exhaustion. Source contracts, learning rate, topology, teacher learning, C05 retention, and publication authority remain governed by their existing owners.

An operator-wide retry would repeat source planning and could target a different delivery. An in-place optimizer rollback would duplicate B12's transaction ownership. Reusing the prepared delivery and B12's out-of-place candidate keeps both transitions at their existing authority boundaries.

## Candidate execution

1. `_batch/factory_candidate_training.py` binds accepted currentness, compiles the source delivery once, and delegates the provisional step to `_batch/candidate/step.py`. `factory_candidate_components.py` caps the first partition at the smallest C08 size that covers the actual logical delivery. The memory budget can reduce that cap further.
2. `_batch/candidate/retry.py` holds shallow MLX descriptors for the exact pre-step numerical trees. It covers B11 gradient evaluation, B12 admission, and provisional terminal motif staging. It catches `RuntimeError`. Classification requires a full match against `\[malloc\] Unable to allocate [0-9]+ bytes\.`, or a message starting with `[METAL] Command buffer execution failed: ` and containing `kIOGPUCommandBufferCallbackErrorOutOfMemory`. Every other exception propagates.
3. After unwinding the failed attempt, the candidate owner reads MLX memory telemetry, clears the free-buffer cache, and starts the existing `RetryState`. It supplies `handle_oom` with the failed plan, fresh OOM receipt, original ordered resource rows, unchanged topology and budget, and a restoration callback. The callback refreshes accepted and source currentness, checks manifest and execution-generation binding, and compares the live pre-step model, AdamW moments and counts against the held snapshot digest. C08 validates the authenticated delivery and computes the next smaller partition over the same ordered rows and seed. At one row or after a second OOM, C08 returns `EXHAUSTED`.
4. The candidate step emits realized delivery evidence only after success. Failed executions return no candidate transaction. On exhaustion the whole provisional horizon is discarded, including any earlier provisional optimizer steps and motif work.

## Operator disposition

`bamf_operator/session.py` catches only the typed C08 exhaustion and returns the selected target plus its failure and restoration receipts. `_session_visit.py` publishes `BAMF_CANDIDATE_RESOURCE_REJECTED` through the existing B13 rejection writer, authenticating the C03 visit under the accepted pointer lock. Its distinct event cannot become ordinary retention, HOW, or cadence feedback.

`_session_execution.py` holds that capability for the current command and returns to the normal disk, deadline, and priority boundaries. The C03 selector skips the held capability after requalifying the lawful ranked offers. It can select an independent authorized option and leaves correction and procedure-repair dispositions intact. A qualified frontier reduced to resource holds ends with the durable resumable `RESOURCE_HOLD` status. Cold resume starts with an empty command-local hold set.

## Implementation sequence and files

1. **Candidate replay.** Create `runtime/_batch/candidate/{__init__,step,retry}.py` and move prepared-step execution and its cache authentication into that owner. Modify `runtime/_batch/factory_candidate_{training,components}.py` to keep the existing step entry point and select the effective first plan. Modify `runtime/_batch/atlas_memory_retry.py` to expose `CandidateMemoryExhausted(RetryState)` and `to_record()`. Extract the existing raw numerical stream into `optimizer_snapshot_digest(optimizer, optimizer_step)` in `learning/_retention/_atlas_candidate/identity.py`. Keep the wire digest identical. Exercise C08 transitions and mutation/currentness rejection before enabling scheduler handling.
2. **Operator containment.** Modify `runtime/bamf_operator/{session,_session_visit,_session_execution}.py` to translate exhaustion into `BamfPreparedVisit("RESOURCE_REJECTED", ...)`, then `ResourceRejectedVisit(capability)` after journaling. Modify `runtime/_custody/bamf_bundle/publication/events.py` so `record_bamf_rejection` validates `bilqis.c08.candidate-resource-rejection/v1` through the same C03 visit checks and emits the distinct resource event. The payload carries the failure and restoration receipts, ordered row IDs, capability, visit identity and selected policy. Thread `resource_holds: frozenset[str]` through `runtime/_teacher/priority/{foundation_teacher_owner,accepted_priority_visit}.py` to exclude held names only from already qualified teaching choices. Modify `runtime/bamf_operator/session_parts/stop_receipt.py` to map `RESOURCE_HOLD` to `RESUME_AFTER_RESOURCE_RECOVERY` with the accepted parent available.
3. **Verification.** Add `runtime/tests/batch/factory/test_factory_candidate_oom.py` and `runtime/tests/operator/session/test_bamf_operator_resource_continuation.py`. Extend the C08 contract tests and `runtime/tests/teacher/priority/test_priority_repair_local_holds.py`. Run staged source/custody preflight and the tests below before opening the review PR. No production files are deleted.

## Proof obligations

- Inject MLX OOM in the native candidate path against pinned disposable source and B13 custody. Verify the same prepared batch, row order, source digest, accepted manifest, execution generation and optimizer seed on the smaller partition.
- Verify a successful retry produces one provisional optimizer proof. Verify a second OOM and first-attempt exhaustion at one row have no further retry. Check the exact cold-loaded accepted pointer, weights, optimizer moments and counts, teacher, and motif allocation after exhaustion.
- Verify the typed B13 resource event and normal stop receipt. Exercise scheduler continuation to a second qualified target and the no-peer stop. Show disk protection still runs and the resource event cannot consume ordinary retention or teacher feedback.
- Verify that stale source/custody and non-allocator errors propagate. Exercise the existing C08 and B13 crash-publication tests.

The fault injection establishes control flow and custody on disposable state. Sustained hardware pressure and changes in retained learning are unmeasured.
