"use strict";

const TARGET_REF = `command-target:${"a".repeat(64)}`;
const OPERATION_ID = `operation:${"b".repeat(64)}`;

function meta(name = "gui17:request:1") {
  return {
    record_id: name,
    run: null,
    materialized_at: 100,
    observed_at: 100,
    as_of: 100,
    coverage: "COMPLETE",
    authority: "DERIVED",
    source_refs: ["authority:human-operator"],
    evidence_refs: [],
    receipt_refs: [],
  };
}

function actionRequest({
  requestId = "gui17-request-1",
  idempotencyKey = "gui17-idem-1",
  action = "resume",
  dryRun = false,
  humanAuthorized = false,
  parameters = [],
} = {}) {
  return {
    schema_version: "bilqis.bamf.mission-control.operator-action-request/v2",
    meta: meta(`gui17:${requestId}`),
    request_id: requestId,
    idempotency_key: idempotencyKey,
    action,
    parameters,
    dry_run: dryRun,
    human_authorized: humanAuthorized,
    requested_at: 100,
  };
}

function publicTarget() {
  return {
    schema: "bilqis.bamf.control-plane.command-target-public/v1",
    target_ref: TARGET_REF,
    run_id: "fixture-run",
    run_seed: 7,
    run_identity_sha256: "1".repeat(64),
    generation: 4,
    generation_manifest_sha256: "2".repeat(64),
    optimizer_step: 12,
    candidate_identity_sha256: "3".repeat(64),
    factory_release_sha256: "4".repeat(64),
    semantic_release_sha256: "5".repeat(64),
    topology_sha256: "6".repeat(64),
    acceptance_sha256: "7".repeat(64),
    source_identity: "source:fixture",
  };
}

function preflight() {
  return {
    kind: "preflight",
    result: "READY_TO_RESUME",
    admission_policy: "staged",
    optimizer_hyperparameters: null,
    source_prefetch_workers: 2,
    generation_manifest_sha256: "2".repeat(64),
    ready_for_training: false,
    neural_updates: 0,
    resource_profile: {
      source_prefetch_workers: 2,
      batch_size: null,
      reserve_gib: null,
      minutes: null,
      steps_per_visit: null,
      max_visits: null,
    },
  };
}

function consequence(mutating = true) {
  return { mutation: mutating ? "MUTATING" : "NONE", neural_mutation_permitted: mutating };
}

function preview(request = actionRequest()) {
  return {
    schema: "bilqis.bamf.control-plane.command-preview/v1",
    operation_id: OPERATION_ID,
    request,
    action: request.action,
    mode: request.dry_run ? "dry-run" : "mutating",
    target: publicTarget(),
    target_ref: TARGET_REF,
    expected_postcondition: request.dry_run ? "resume-preview" : "operator-run-completed",
    consequence: consequence(!request.dry_run),
    preflight: preflight(),
    receipt: null,
    postcondition: null,
    logs: null,
  };
}

function receipt(request = actionRequest({ humanAuthorized: true }), state = "ACCEPTED") {
  return {
    schema_version: "bilqis.bamf.mission-control.operator-action-receipt/v2",
    meta: {
      ...meta(`cp05:${OPERATION_ID}:${state.toLowerCase()}`),
      source_refs: ["authority:c11-bamf-operator"],
      evidence_refs: [TARGET_REF],
    },
    request_id: request.request_id,
    request_sha256: "8".repeat(64),
    operation_id: OPERATION_ID,
    state,
    acknowledged_at: 101,
    target_ref: TARGET_REF,
    postcondition_ref: null,
    error_ref: null,
  };
}

function inspection(request = actionRequest({ humanAuthorized: true }), state = "ACCEPTED") {
  return {
    ...preview(request),
    schema: "bilqis.bamf.control-plane.command-inspection/v1",
    receipt: receipt(request, state),
    logs: { stdout_tail: "trainer ready\n", stderr_tail: null },
  };
}

module.exports = {
  OPERATION_ID,
  TARGET_REF,
  actionRequest,
  inspection,
  preview,
  publicTarget,
  receipt,
};
