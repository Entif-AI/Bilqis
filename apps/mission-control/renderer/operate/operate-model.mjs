export const PREVIEW_REQUEST_SCHEMA = "bamf.gui17.command-preview-request/v1";
export const SUBMIT_REQUEST_SCHEMA = "bamf.gui17.command-submit-request/v1";
export const ACTION_REQUEST_SCHEMA = "bilqis.bamf.mission-control.operator-action-request/v2";

const ALLOWED_PARAMETERS = new Set([
  "model_topology", "atlas_release_manifest", "run_id", "run_seed",
  "learning_rate", "adam_beta1", "adam_beta2", "adam_eps", "weight_decay",
  "atlas_admission_scope", "admission_policy", "minutes", "steps_per_visit",
  "max_visits", "source_prefetch_workers", "batch_size", "reserve_gib",
  "autonomous_curriculum", "verify_source", "timing_trace", "flash_mode",
  "source_teaching_enrichment", "admit_next_grade_with_debt", "operation_id",
]);

export const OPERATE_ACTIONS = Object.freeze([
  Object.freeze({ id: "create", supported: true, mutation: true, dryRun: true }),
  Object.freeze({ id: "owner-launch", supported: true, mutation: true, dryRun: true }),
  Object.freeze({ id: "resume", supported: true, mutation: true, dryRun: true }),
  Object.freeze({ id: "status", supported: true, mutation: false, dryRun: false }),
  Object.freeze({ id: "checkpoint-verify", supported: true, mutation: false, dryRun: false }),
  Object.freeze({ id: "admission-lease", supported: true, mutation: true, dryRun: false }),
  Object.freeze({ id: "pause", supported: false, mutation: false, dryRun: false }),
  Object.freeze({ id: "stop", supported: true, mutation: true, dryRun: false }),
]);

export const OPERATE_STAGES = Object.freeze([
  "request", "preflight", "authorization", "outcome",
]);

export function actionSpec(action) {
  return OPERATE_ACTIONS.find((item) => item.id === action) ?? null;
}

function scalar(value) {
  return typeof value === "string" || typeof value === "boolean" ||
    (typeof value === "number" && Number.isFinite(value));
}

export function parseParameters(text) {
  let parsed;
  try {
    parsed = JSON.parse(text || "{}");
  } catch (_error) {
    throw new TypeError("GUI17_PARAMETERS_JSON_INVALID");
  }
  if (!parsed || typeof parsed !== "object" || Array.isArray(parsed)) {
    throw new TypeError("GUI17_PARAMETERS_OBJECT_REQUIRED");
  }
  const result = [];
  for (const [key, value] of Object.entries(parsed)) {
    if (!ALLOWED_PARAMETERS.has(key)) throw new TypeError(`GUI17_PARAMETER_UNSUPPORTED:${key}`);
    if (!scalar(value)) throw new TypeError(`GUI17_PARAMETER_SCALAR_REQUIRED:${key}`);
    result.push(Object.freeze({ key, value }));
  }
  return Object.freeze(result.sort((left, right) => left.key.localeCompare(right.key)));
}

function requestIdentity(action, context, now) {
  const run = context?.runId && context.runId !== "fixture-run" ? context.runId : "cp05-target";
  const stem = `gui17:${action}:${run}:${now}`;
  return Object.freeze({ requestId: `${stem}:request`, idempotencyKey: `${stem}:operation` });
}

export function buildPreviewRequest({ action, dryRun, parameters, context, now = Date.now() }) {
  const spec = actionSpec(action);
  if (!spec?.supported) throw new TypeError("GUI17_ACTION_UNAVAILABLE");
  if (!Number.isSafeInteger(now) || now < 0) throw new TypeError("GUI17_TIME_INVALID");
  if (dryRun && !spec.dryRun) throw new TypeError("GUI17_DRY_RUN_UNAVAILABLE");
  const identity = requestIdentity(action, context, now);
  const recordId = `${identity.requestId}:record`;
  return Object.freeze({
    schemaVersion: PREVIEW_REQUEST_SCHEMA,
    request: Object.freeze({
      schema_version: ACTION_REQUEST_SCHEMA,
      meta: Object.freeze({
        record_id: recordId,
        run: null,
        materialized_at: now,
        observed_at: now,
        as_of: now,
        coverage: "COMPLETE",
        authority: "DERIVED",
        source_refs: Object.freeze(["authority:human-operator"]),
        evidence_refs: Object.freeze([]),
        receipt_refs: Object.freeze([]),
      }),
      request_id: identity.requestId,
      idempotency_key: identity.idempotencyKey,
      action,
      parameters,
      dry_run: Boolean(dryRun),
      human_authorized: false,
      requested_at: now,
    }),
  });
}

export function buildSubmitRequest(preview) {
  if (!preview?.target_ref || !preview?.request) throw new TypeError("GUI17_PREVIEW_REQUIRED");
  const mutating = preview.consequence?.mutation === "MUTATING";
  return Object.freeze({
    schemaVersion: SUBMIT_REQUEST_SCHEMA,
    expectedTargetRef: preview.target_ref,
    request: Object.freeze({ ...preview.request, human_authorized: mutating }),
  });
}

const CONTEXT_FIELDS = Object.freeze([
  ["runId", "run_id", "run"],
  ["generation", "generation", "generation"],
  ["generationManifest", "generation_manifest_sha256", "generation manifest"],
  ["topologyId", "topology_sha256", "topology"],
  ["factoryRelease", "factory_release_sha256", "Factory release"],
  ["semanticRelease", "semantic_release_sha256", "semantic release"],
]);

export function contextConflicts(context, preview) {
  if (!context || !preview?.target || preview.action === "create") return Object.freeze([]);
  if (context.runId === "fixture-run" || String(context.recordId ?? "").includes("fixture")) {
    return Object.freeze([]);
  }
  const conflicts = [];
  for (const [contextKey, targetKey, label] of CONTEXT_FIELDS) {
    const expected = context[contextKey];
    const actual = preview.target[targetKey];
    if (expected !== null && expected !== undefined && expected !== "UNKNOWN" &&
        actual !== null && actual !== undefined && expected !== actual) {
      conflicts.push(Object.freeze({ label, expected, actual }));
    }
  }
  return Object.freeze(conflicts);
}

export function terminalReceipt(state) {
  return new Set([
    "COMPLETED", "REJECTED", "FAILED", "FAILED_BEFORE_EFFECT",
  ]).has(state);
}

export function operateStageAvailable(state, stage) {
  if (!OPERATE_STAGES.includes(stage)) return false;
  if (state?.activeStage === stage) return true;
  if (stage === "request") return true;
  if (stage === "preflight") {
    return Boolean(state?.preview) || state?.phase === "PREVIEWING";
  }
  if (stage === "authorization") return Boolean(state?.preview);
  return Boolean(state?.inspection) || new Set([
    "SUBMITTING", "PENDING", "TERMINAL", "LOST_ACK", "OUTCOME_UNKNOWN", "RECONCILING",
  ]).has(state?.phase);
}

export function authorizationPhrase(preview) {
  return preview?.consequence?.mutation === "MUTATING"
    ? `AUTHORIZE ${String(preview.action).toUpperCase()}` : "";
}

export function initialOperateState() {
  return Object.freeze({
    action: "status",
    activeStage: "request",
    dryRun: false,
    parametersText: "{}",
    phase: "IDLE",
    preview: null,
    inspection: null,
    conflicts: Object.freeze([]),
    error: null,
    authorization: "",
  });
}
