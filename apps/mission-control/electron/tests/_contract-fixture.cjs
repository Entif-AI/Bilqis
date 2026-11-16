"use strict";

function invalid(code) {
  const error = new TypeError(code);
  error.code = code;
  throw error;
}

function exactRecord(value, schemaVersion, requiredKeys, optionalKeys = []) {
  if (!value || typeof value !== "object" || Array.isArray(value) ||
      value.schemaVersion !== schemaVersion) {
    invalid("FIXTURE_CP02_RECORD_INVALID");
  }
  const allowed = new Set(["schemaVersion", ...requiredKeys, ...optionalKeys]);
  if (Object.keys(value).some((key) => !allowed.has(key))) {
    invalid("FIXTURE_CP02_RECORD_INVALID");
  }
  for (const key of requiredKeys) {
    if (typeof value[key] !== "string" || value[key].length === 0) {
      invalid("FIXTURE_CP02_RECORD_INVALID");
    }
  }
  return value;
}

function snapshotRequest(value) {
  return exactRecord(value, "cp02.snapshot.fixture/v1", ["objectRef"]);
}

function queryRequest(value) {
  return exactRecord(value, "cp03.query.fixture/v1", ["family"]);
}

function dryRunRequest(value) {
  return exactRecord(value, "cp02.dry-run.fixture/v1", ["requestId", "action"]);
}

function commandRequest(value) {
  return exactRecord(value, "cp02.command.fixture/v1", ["requestId", "action"]);
}

function publicStatus(value) {
  return exactRecord(
    value,
    "cp01.public-status.fixture/v1",
    ["state", "protocolVersion"],
    ["runId"],
  );
}

function response(method, value) {
  switch (method) {
    case "status":
      return exactRecord(value, "cp01.status.fixture/v1", ["state"], ["runId"]);
    case "snapshot":
      return exactRecord(value, "cp02.snapshot.result.fixture/v1", ["objectRef"]);
    case "query":
      return exactRecord(value, "cp03.query.result.fixture/v1", ["family"]);
    case "dryRun":
      return exactRecord(value, "cp02.dry-run.result.fixture/v1", ["state", "requestId"]);
    case "command":
      return exactRecord(value, "cp02.command.result.fixture/v1", ["state", "requestId"]);
    case "receipt":
      return exactRecord(value, "cp02.receipt.fixture/v1", ["ref"], ["verified"]);
    default:
      invalid("FIXTURE_CP02_RESPONSE_INVALID");
  }
}

function receiptRef(value) {
  if (typeof value !== "string" || !value.startsWith("receipt:")) {
    invalid("FIXTURE_CP02_RECEIPT_REF_INVALID");
  }
  return value;
}

function event(value) {
  return exactRecord(value, "cp02.event.fixture/v1", ["cursor"], ["state"]);
}

const FIXTURE_VALIDATORS = Object.freeze({
  publicStatus,
  snapshotRequest,
  queryRequest,
  dryRunRequest,
  commandRequest,
  receiptRef,
  response,
  event,
});

module.exports = { FIXTURE_VALIDATORS };
