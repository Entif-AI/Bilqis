# BAMF Model Forensics Operate (GUI17)

Issue: #1072
Parent: #1047
Command owner: CP05 / #1053 over C11 / #384

## Purpose

GUI17 is the explicit Model Forensics mutation zone. It does not create a second BAMF operator, command language, trainer, scheduler, or shell. It exposes the command semantics already admitted by CP05 and C11 through the fixed GUI20 Electron boundary.

Observation destinations remain read-only. Only the Operate controller may call the renderer command APIs `requestDryRun`, `requestCommand`, and `fetchReceipt`; a source-level boundary test enforces that invariant.

## Supported actions

GUI17 reflects the CP05/C11 action vocabulary literally:

- `create` — mutating, with read-only preflight and optional final dry-run;
- `owner-launch` — mutating, with read-only preflight and optional final dry-run;
- `resume` — mutating, with read-only preflight and optional final dry-run;
- `status` — read-only;
- `checkpoint-verify` — read-only;
- `admission-lease` — mutating through the existing admitted lease operation;
- `stop` — mutating; targets one exact active create/resume/owner-launch operation and uses the trainer's existing SIGINT boundary after lineage and process-identity checks;
- `pause` — visibly unavailable because CP05/C11 does not expose pause semantics.

The GUI does not translate arbitrary text into a shell command. Parameters are a bounded JSON object whose keys and scalar values must match the CP05/C11 admitted parameter surface.

## Review and authorization lifecycle

The user flow is deliberately two-phase for mutation:

1. **Select an admitted action and explicit parameters.**
2. **Preflight.** GUI17 sends an `OperatorActionRequestV2` with `human_authorized=false` through the reserved GUI20 dry-run IPC channel. CP05 resolves the exact action-specific `CommandPlan` and target without admitting, persisting, or dispatching the operation.
3. **Review exact target and consequence.** The view shows the resolved command target, run identity where available, generation, generation manifest, topology, Factory and semantic release identities, source identity, admission policy, resource inputs, expected postcondition, and an explicit `MUTATING` versus `NONE` consequence.
4. **Deliberate authorization.** Mutating actions require the operator to type `AUTHORIZE <ACTION>`. The controller enforces that phrase independently of the button-disabled state.
5. **Submit the reviewed intent.** The final request reuses the exact request identity and idempotency key from preview, changes only the authorization bit where mutation is permitted, and carries the exact reviewed `expectedTargetRef` outside the semantic request payload.
6. **CP05 re-preflights immediately before admission.** If the current authoritative target no longer matches the reviewed target ref, CP05 persists a rejection and does not reserve dispatch or launch a worker.
7. **Readback.** GUI17 retains the operation identity and reads CP05's durable receipt/postcondition state. CP04 `operator.action.state` events cause readback only; they never create a new submit. A successfully accepted owner launch/resume also seeds the exact operation identity used by Stop.

This design makes preview a review aid rather than an authorization token. The actual mutation owner remains CP05/C11.

## Stale-context behavior

For a real non-fixture Model Forensics context, GUI17 also compares any known shell run/generation/generation-manifest/topology/Factory/semantic identities with the CP05 preview target. A mismatch blocks authorization in the renderer and tells the operator to refresh and preflight again.

The CP05 `expectedTargetRef` check remains the authoritative stale-target guard. Renderer comparison is defense in depth and operator feedback, not command authority.

The current GUI01 illustrative `fixture-run` OperatorView is never promoted into command authority. Fixture shell identity is ignored for stale-target comparison; the CP05 preflight target remains authoritative.

## Idempotency and lost acknowledgement

A fresh preflight creates one request identity and one idempotency key. Double-click or repeated controller submission while `SUBMITTING` is suppressed locally, and CP05 still supplies durable idempotency underneath.

If the final command call loses its acknowledgement, GUI17 enters `LOST_ACK`. It does **not** retry `requestCommand`. The only permitted next step is readback by the retained `operation:<sha256>` identity through `fetchReceipt`. If CP05 cannot yet reconcile the operation, the UI says `OUTCOME_UNKNOWN`; another readback may be requested later without creating a second effect.

`OUTCOME_UNKNOWN` is an unresolved evidence state, not a terminal failure and not permission to retry. CP05 may resolve the original operation to `COMPLETED` only from authoritative effect evidence, or to `FAILED_BEFORE_EFFECT` only from authoritative no-effect evidence with exact pre-effect learner identity. An unavailable process-identity probe is itself unresolved evidence and must keep the operation `OUTCOME_UNKNOWN`; only a positively dead or identity-mismatched recorded process permits reconciliation to proceed.

While ambiguity remains, CP05 rejects new effect-producing mutation against the same learner even under a different idempotency key. Admission is serialized one step earlier as well: an older same-learner mutation that is still ACCEPTED or PENDING blocks a later effect-producing mutation, so the later command cannot slip through while the older command crosses into OUTCOME_UNKNOWN. Read-only receipt/status/checkpoint inspection remains available. The only mutating exception is exact guarded Stop for the same unresolved operation, and Stop still requires fresh PID, process-identity, and learner-lineage validation.

There is no command that resets or rewrites an unresolved receipt. If available evidence can never distinguish effect from no-effect, human abandonment preserves the original `OUTCOME_UNKNOWN` operation and its immutable evidence. Any repair is a new explicitly authorized operation after the operator establishes an independently valid replacement target and completes fresh preflight; the old operation remains part of the causal record.

## Public command projection

GUI17 needed more preflight/readback detail than the ordinary CP03 catalog exposes. CP05 already owns that information in immutable command facts, so the control plane now provides two bounded read-only projections:

- `bilqis.bamf.control-plane.command-preview/v1` — an exact, non-persisting preview of the CP05 plan;
- `bilqis.bamf.control-plane.command-inspection/v1` — authoritative durable operation status plus bounded preflight and postcondition facts.

These projections explicitly omit the private run-directory path, command `argv`, worker pid, command-store path, socket/session identity, and other process details. Command inspection may include bounded stdout/stderr log tails for owner diagnosis. The Electron trust membrane validates exact public target, optimizer, resource, receipt, log-tail, and postcondition shapes before renderer delivery.

The public target projection retains only stable identities and counters needed for review: target ref, run id/seed and digest, generation and generation manifest, optimizer step, candidate/Factory/semantic/topology/acceptance digests, and source identity.

## Electron and CP01 boundary

GUI20 had already reserved the fixed IPC surface:

- `requestDryRun`;
- `requestCommand`;
- `fetchReceipt`.

GUI17 activates those existing channels instead of adding generic IPC. The accepted adapter forwards only validated GUI17 wrappers to the private Python broker, which reaches CP01 and CP05. The renderer never receives the private CP01 session, socket, run path, or executable command line.

The command package remains lazily imported so ordinary CP01 health/query/event startup does not acquire C11/runtime dependencies solely because GUI17 exists.

## Read-only and dry-run semantics

Read-only actions and final dry-runs set `human_authorized=false` and display `NO NEURAL MUTATION`. A dry-run still returns an operation receipt and postcondition through CP05, but does not dispatch mutating learner work.

Mutating actions display `MUTATION PERMITTED IF AUTHORIZED` before the human gate. GUI17 never infers that a command is safe merely because its preflight succeeded.

## Verification surfaces

- `apps/mission-control/tests/operate/operate-model.test.mjs`
  - exact request/idempotency preservation;
  - dry-run/no-authorization semantics;
  - real-context drift detection and fixture non-authority;
  - unavailable pause plus supported Stop presentation and bounded trainer-log tails;
  - operation inspector ownership.
- `apps/mission-control/tests/operate/operate-controller.test.mjs`
  - typed authorization required for mutation;
  - double-submit suppression;
  - lost acknowledgement without retry;
  - authoritative reconciliation;
  - stale context blocks submit;
  - dry-run remains non-authorized;
  - accepted owner launch seeds the exact Stop operation identity and action changes clear action-specific parameters.
- `apps/mission-control/tests/operate/operate-boundary.test.mjs`
  - no observation renderer module can invoke command IPC.
- `apps/mission-control/electron/tests/operator-contracts.test.cjs`
  - exact request, target, receipt, optimizer, preflight, and postcondition validation.
- `apps/mission-control/electron/tests/cp01-python-broker.test.cjs`
  - real private Electron-to-Python-to-CP01-to-CP05 preview/submit/readback path;
  - no private run/store/session/argv leakage.
- `bilqis_mlx/control_plane/tests/commands/test_command_lifecycle.py`
  - reviewed-target mismatch rejects before dispatch;
  - matching reviewed target preserves one-dispatch idempotency.
- `bilqis_mlx/control_plane/tests/test_command_executor.py`
  - exact active-trainer Stop sends SIGINT only after process-identity and lineage validation;
  - failed durable process custody interrupts and waits for the newly spawned trainer.
- `bilqis_mlx/control_plane/tests/test_command_transport.py`
  - public preview and durable inspection round trip over CP01.

GUI17 does not run a live learner as part of its implementation tests. The disposable CP05 integration uses the existing fake executor/launcher to prove command custody and transport without touching the operator's real learner.
