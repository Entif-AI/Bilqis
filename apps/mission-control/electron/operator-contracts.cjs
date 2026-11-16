"use strict";

const ACTION_REQUEST = "bilqis.bamf.mission-control.operator-action-request/v2";
const ACTION_RECEIPT = "bilqis.bamf.mission-control.operator-action-receipt/v2";
const PREVIEW_REQUEST = "bamf.gui17.command-preview-request/v1";
const SUBMIT_REQUEST = "bamf.gui17.command-submit-request/v1";
const PREVIEW = "bilqis.bamf.control-plane.command-preview/v1";
const INSPECTION = "bilqis.bamf.control-plane.command-inspection/v1";
const PUBLIC_TARGET = "bilqis.bamf.control-plane.command-target-public/v1";

const ACTIONS = new Set([
  "create", "resume", "owner-launch", "status", "checkpoint-verify",
  "admission-lease", "pause", "stop",
]);
const STATES = new Set([
  "ACCEPTED", "PENDING", "COMPLETED", "REJECTED", "FAILED", "OUTCOME_UNKNOWN",
]);
const MODES = new Set(["read-only", "dry-run", "mutating"]);
const COVERAGE = new Set(["COMPLETE", "PARTIAL", "UNKNOWN", "NOT_APPLICABLE"]);
const AUTHORITY = new Set(["SOURCE_AUTHORITATIVE", "MEASURED", "DERIVED", "INFERRED"]);
const PARAMETER_KEYS = new Set([
  "model_topology", "atlas_release_manifest", "run_id", "run_seed",
  "learning_rate", "adam_beta1", "adam_beta2", "adam_eps", "weight_decay",
  "atlas_admission_scope", "admission_policy", "minutes", "steps_per_visit",
  "max_visits", "source_prefetch_workers", "batch_size", "reserve_gib",
  "autonomous_curriculum", "verify_source", "timing_trace", "flash_mode",
  "source_teaching_enrichment", "admit_next_grade_with_debt", "operation_id",
]);
const PYTHON_WHITESPACE_ONLY = /^[\u0009-\u000d\u001c-\u0020\u0085\u00a0\u1680\u2000-\u200a\u2028\u2029\u202f\u205f\u3000]+$/u;

function invalid(reason) {
  const error = new TypeError(`BAMF_GUI17_OPERATOR_CONTRACT_INVALID:${reason}`);
  error.code = "BAMF_GUI17_OPERATOR_CONTRACT_INVALID";
  throw error;
}

function exactKeys(value, keys) {
  return value && typeof value === "object" && !Array.isArray(value) &&
    Object.keys(value).length === keys.length && keys.every((key) => key in value);
}

function isName(value) {
  return typeof value === "string" && value.length > 0 &&
    !PYTHON_WHITESPACE_ONLY.test(value) && !value.includes("\n");
}

function isDigest(value) {
  return typeof value === "string" && /^[0-9a-f]{64}$/.test(value);
}

function nullableDigest(value) {
  return value === null || isDigest(value);
}

function nullableName(value) {
  return value === null || isName(value);
}

function wireInt(value) {
  return Number.isSafeInteger(value) && value >= 0;
}

function scalar(value) {
  return value === null || typeof value === "string" || typeof value === "boolean" ||
    (typeof value === "number" && Number.isFinite(value));
}

function validateMeta(meta) {
  const keys = [
    "record_id", "run", "materialized_at", "observed_at", "as_of", "coverage",
    "authority", "source_refs", "evidence_refs", "receipt_refs",
  ];
  if (!exactKeys(meta, keys) || meta.run !== null || !isName(meta.record_id) ||
      !wireInt(meta.materialized_at) ||
      (meta.observed_at !== null && !wireInt(meta.observed_at)) ||
      (meta.as_of !== null && !wireInt(meta.as_of)) ||
      !COVERAGE.has(meta.coverage) || !AUTHORITY.has(meta.authority)) invalid("META");
  for (const key of ["source_refs", "evidence_refs", "receipt_refs"]) {
    if (!Array.isArray(meta[key]) || !meta[key].every(isName) ||
        new Set(meta[key]).size !== meta[key].length) invalid(`META_${key}`);
  }
  return meta;
}

function validateActionRequest(value) {
  const keys = [
    "schema_version", "meta", "request_id", "idempotency_key", "action",
    "parameters", "dry_run", "human_authorized", "requested_at",
  ];
  if (!exactKeys(value, keys) || value.schema_version !== ACTION_REQUEST ||
      !isName(value.request_id) || !isName(value.idempotency_key) ||
      !ACTIONS.has(value.action) || !Array.isArray(value.parameters) ||
      typeof value.dry_run !== "boolean" || typeof value.human_authorized !== "boolean" ||
      !wireInt(value.requested_at)) invalid("ACTION_REQUEST");
  validateMeta(value.meta);
  const seen = new Set();
  for (const parameter of value.parameters) {
    if (!exactKeys(parameter, ["key", "value"]) || !PARAMETER_KEYS.has(parameter.key) ||
        !scalar(parameter.value) || seen.has(parameter.key)) invalid("ACTION_PARAMETER");
    seen.add(parameter.key);
  }
  return value;
}

function validateReceipt(value) {
  const keys = [
    "schema_version", "meta", "request_id", "request_sha256", "operation_id", "state",
    "acknowledged_at", "target_ref", "postcondition_ref", "error_ref",
  ];
  if (!exactKeys(value, keys) || value.schema_version !== ACTION_RECEIPT ||
      !isName(value.request_id) || !isDigest(value.request_sha256) ||
      !/^operation:[0-9a-f]{64}$/.test(value.operation_id) || !STATES.has(value.state) ||
      !wireInt(value.acknowledged_at) || !/^command-target:[0-9a-f]{64}$/.test(value.target_ref) ||
      !nullableName(value.postcondition_ref) || !nullableName(value.error_ref)) invalid("ACTION_RECEIPT");
  validateMeta(value.meta);
  return value;
}

function validateTarget(value) {
  const keys = [
    "schema", "target_ref", "run_id", "run_seed", "run_identity_sha256", "generation",
    "generation_manifest_sha256", "optimizer_step", "candidate_identity_sha256",
    "factory_release_sha256", "semantic_release_sha256", "topology_sha256",
    "acceptance_sha256", "source_identity",
  ];
  if (!exactKeys(value, keys) || value.schema !== PUBLIC_TARGET ||
      !/^command-target:[0-9a-f]{64}$/.test(value.target_ref) || !nullableName(value.run_id) ||
      (value.run_seed !== null && !wireInt(value.run_seed)) ||
      (value.generation !== null && !wireInt(value.generation)) ||
      (value.optimizer_step !== null && !wireInt(value.optimizer_step)) ||
      !nullableName(value.source_identity)) invalid("PUBLIC_TARGET");
  for (const key of [
    "run_identity_sha256", "generation_manifest_sha256", "candidate_identity_sha256",
    "factory_release_sha256", "semantic_release_sha256", "topology_sha256", "acceptance_sha256",
  ]) if (!nullableDigest(value[key])) invalid(`PUBLIC_TARGET_${key}`);
  return value;
}

function validateResourceProfile(value) {
  const keys = [
    "source_prefetch_workers", "batch_size", "reserve_gib", "minutes",
    "steps_per_visit", "max_visits",
  ];
  if (!exactKeys(value, keys) || !keys.every((key) => scalar(value[key]))) {
    invalid("RESOURCE_PROFILE");
  }
}

function finiteNumber(value) {
  return typeof value === "number" && Number.isFinite(value);
}

function validateOptimizer(value) {
  if (value === null) return;
  if (!exactKeys(value, ["learning_rate", "betas", "eps", "weight_decay"]) ||
      !finiteNumber(value.learning_rate) || !Array.isArray(value.betas) ||
      value.betas.length !== 2 || !value.betas.every(finiteNumber) ||
      !finiteNumber(value.eps) || !finiteNumber(value.weight_decay)) invalid("OPTIMIZER");
}

function validatePreflight(value) {
  const keys = [
    "kind", "result", "admission_policy", "optimizer_hyperparameters",
    "source_prefetch_workers", "generation_manifest_sha256", "ready_for_training",
    "neural_updates", "resource_profile",
  ];
  if (!exactKeys(value, keys) || !nullableName(value.kind) || !nullableName(value.result) ||
      !nullableName(value.admission_policy) ||
      !scalar(value.source_prefetch_workers) || !nullableDigest(value.generation_manifest_sha256) ||
      (value.ready_for_training !== null && typeof value.ready_for_training !== "boolean") ||
      !scalar(value.neural_updates)) invalid("PREFLIGHT");
  validateOptimizer(value.optimizer_hyperparameters);
  validateResourceProfile(value.resource_profile);
}

function validateConsequence(value) {
  if (!exactKeys(value, ["mutation", "neural_mutation_permitted"]) ||
      !new Set(["NONE", "MUTATING"]).has(value.mutation) ||
      typeof value.neural_mutation_permitted !== "boolean") invalid("CONSEQUENCE");
}

function validatePostcondition(value) {
  if (value === null) return;
  if (!value || typeof value !== "object" || Array.isArray(value) || !nullableName(value.kind)) {
    invalid("POSTCONDITION");
  }
  const allowed = new Set(["kind", "before", "after", "target", "inspection", "admission_epoch", "cli_exit"]);
  if (!Object.keys(value).every((key) => allowed.has(key))) invalid("POSTCONDITION_FIELDS");
  for (const key of ["before", "after", "target"]) if (key in value) validateTarget(value[key]);
  if ("inspection" in value) {
    const keys = [
      "generation", "generation_manifest_sha256", "optimizer_step",
      "candidate_identity_sha256", "factory_release_sha256",
      "semantic_release_sha256", "topology_sha256", "acceptance_sha256",
    ];
    const inspection = value.inspection;
    if (!inspection || typeof inspection !== "object" || Array.isArray(inspection) ||
        !Object.keys(inspection).every((key) => keys.includes(key))) {
      invalid("POSTCONDITION_INSPECTION");
    }
    if ("generation" in inspection && inspection.generation !== null && !wireInt(inspection.generation)) {
      invalid("POSTCONDITION_INSPECTION_GENERATION");
    }
    if ("optimizer_step" in inspection && inspection.optimizer_step !== null && !wireInt(inspection.optimizer_step)) {
      invalid("POSTCONDITION_INSPECTION_OPTIMIZER_STEP");
    }
    for (const key of keys.filter((name) => name.endsWith("_sha256"))) {
      if (key in inspection && !nullableDigest(inspection[key])) invalid(`POSTCONDITION_INSPECTION_${key}`);
    }
  }
  if ("admission_epoch" in value && !scalar(value.admission_epoch)) invalid("POSTCONDITION_EPOCH");
  if ("cli_exit" in value && !scalar(value.cli_exit)) invalid("POSTCONDITION_EXIT");
}

function validateProjection(value, schema, receiptRequired) {
  const keys = [
    "schema", "operation_id", "request", "action", "mode", "target", "target_ref",
    "expected_postcondition", "consequence", "preflight", "receipt", "postcondition", "logs",
  ];
  if (!exactKeys(value, keys) || value.schema !== schema ||
      !/^operation:[0-9a-f]{64}$/.test(value.operation_id) || !ACTIONS.has(value.action) ||
      (value.mode !== null && !MODES.has(value.mode)) || !nullableName(value.expected_postcondition)) {
    invalid("PROJECTION");
  }
  validateActionRequest(value.request);
  if (value.target === null) {
    if (value.target_ref !== null) invalid("PROJECTION_TARGET");
  } else {
    validateTarget(value.target);
    if (value.target_ref !== value.target.target_ref) invalid("PROJECTION_TARGET_REF");
  }
  validateConsequence(value.consequence);
  validatePreflight(value.preflight);
  if (receiptRequired) validateReceipt(value.receipt);
  else if (value.receipt !== null) invalid("PREVIEW_RECEIPT");
  validatePostcondition(value.postcondition);
  if (value.logs !== null) {
    if (!exactKeys(value.logs, ["stdout_tail", "stderr_tail"])) invalid("LOGS");
    for (const key of ["stdout_tail", "stderr_tail"]) {
      const tail = value.logs[key];
      if (tail !== null && (typeof tail !== "string" || tail.length > 4096)) invalid("LOG_TAIL");
    }
  }
  return value;
}

function validatePreviewRequest(value) {
  if (!exactKeys(value, ["schemaVersion", "request"]) || value.schemaVersion !== PREVIEW_REQUEST) {
    invalid("PREVIEW_REQUEST");
  }
  const request = validateActionRequest(value.request);
  if (request.human_authorized) invalid("PREVIEW_AUTHORIZATION_FORBIDDEN");
  return value;
}

function validateSubmitRequest(value) {
  if (!exactKeys(value, ["schemaVersion", "expectedTargetRef", "request"]) ||
      value.schemaVersion !== SUBMIT_REQUEST ||
      !/^command-target:[0-9a-f]{64}$/.test(value.expectedTargetRef)) invalid("SUBMIT_REQUEST");
  validateActionRequest(value.request);
  return value;
}

function validateOperationRef(value) {
  if (typeof value !== "string" || !/^operation:[0-9a-f]{64}$/.test(value)) {
    invalid("OPERATION_REF");
  }
  return value;
}

module.exports = {
  ACTION_REQUEST,
  ACTION_RECEIPT,
  COMMAND_INSPECTION_SCHEMA: INSPECTION,
  COMMAND_PREVIEW_SCHEMA: PREVIEW,
  PREVIEW_REQUEST_SCHEMA: PREVIEW_REQUEST,
  SUBMIT_REQUEST_SCHEMA: SUBMIT_REQUEST,
  validateActionRequest,
  validateInspection: (value) => validateProjection(value, INSPECTION, true),
  validateOperationRef,
  validatePreview: (value) => validateProjection(value, PREVIEW, false),
  validatePreviewRequest,
  validateReceipt,
  validateSubmitRequest,
};
