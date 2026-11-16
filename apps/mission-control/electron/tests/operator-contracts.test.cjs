"use strict";

const test = require("node:test");
const assert = require("node:assert/strict");
const {
  PREVIEW_REQUEST_SCHEMA,
  SUBMIT_REQUEST_SCHEMA,
  validateInspection,
  validateOperationRef,
  validatePreview,
  validatePreviewRequest,
  validateReceipt,
  validateSubmitRequest,
} = require("../operator-contracts.cjs");
const {
  OPERATION_ID, TARGET_REF, actionRequest, inspection, preview, receipt,
} = require("./_operator-fixture.cjs");

test("GUI17 preview accepts only exact non-authorized CP05 v2 requests", () => {
  const request = actionRequest();
  assert.equal(validatePreviewRequest({
    schemaVersion: PREVIEW_REQUEST_SCHEMA,
    request,
  }).request, request);
  assert.throws(() => validatePreviewRequest({
    schemaVersion: PREVIEW_REQUEST_SCHEMA,
    request: { ...request, human_authorized: true },
  }), /PREVIEW_AUTHORIZATION_FORBIDDEN/);
  assert.throws(() => validatePreviewRequest({
    schemaVersion: PREVIEW_REQUEST_SCHEMA,
    request: { ...request, schema_version: "v1" },
  }), /ACTION_REQUEST/);
});

test("GUI17 submit binds one exact CP05 request to its reviewed target", () => {
  const request = actionRequest({ humanAuthorized: true });
  assert.equal(validateSubmitRequest({
    schemaVersion: SUBMIT_REQUEST_SCHEMA,
    expectedTargetRef: TARGET_REF,
    request,
  }).request, request);
  assert.throws(() => validateSubmitRequest({
    schemaVersion: SUBMIT_REQUEST_SCHEMA,
    expectedTargetRef: "command-target:stale",
    request,
  }), /SUBMIT_REQUEST/);
});

test("GUI17 admits an exact operation identity only as a typed action parameter", () => {
  const request = actionRequest({
    action: "stop",
    parameters: [{ key: "operation_id", value: OPERATION_ID }],
  });
  assert.equal(validatePreviewRequest({
    schemaVersion: PREVIEW_REQUEST_SCHEMA,
    request,
  }).request.parameters[0].value, OPERATION_ID);
});

test("GUI17 public preview and inspection reject path-shaped or malformed projections", () => {
  assert.equal(validatePreview(preview()).target_ref, TARGET_REF);
  assert.equal(validateInspection(inspection()).receipt.operation_id, OPERATION_ID);
  assert.equal(validateInspection(inspection()).logs.stdout_tail, "trainer ready\n");
  assert.throws(
    () => validateInspection({
      ...inspection(),
      logs: { stdout_tail: "x".repeat(4097), stderr_tail: null },
    }),
    /LOG_TAIL/,
  );
  assert.equal(validateReceipt(receipt()).state, "ACCEPTED");
  assert.equal(validateOperationRef(OPERATION_ID), OPERATION_ID);
  assert.throws(() => validatePreview({
    ...preview(),
    target: { ...preview().target, run_dir: "/private/run" },
  }), /PUBLIC_TARGET/);
  assert.throws(() => validateInspection({
    ...inspection(),
    receipt: { ...inspection().receipt, operation_id: "operation:bad" },
  }), /ACTION_RECEIPT/);
  assert.throws(() => validatePreview({
    ...preview(),
    preflight: {
      ...preview().preflight,
      optimizer_hyperparameters: { learning_rate: 0.001, betas: [0.9, 0.99], eps: 1e-8, weight_decay: 0.01, shell: "/bin/sh" },
    },
  }), /OPTIMIZER/);
  assert.throws(() => validateInspection({
    ...inspection(),
    postcondition: { kind: "authoritative-readback", inspection: { run_dir: "/private/run" } },
  }), /POSTCONDITION_INSPECTION/);
});
