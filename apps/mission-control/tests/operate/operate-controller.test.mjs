import test from "node:test";
import assert from "node:assert/strict";
import { createOperateController } from "../../renderer/operate/operate-controller.mjs";

function fakeHost() {
  const handlers = new Map();
  const actionButtons = new Map();
  const stageHandlers = new Map();
  const stageButtons = new Map();
  for (const action of ["create", "owner-launch", "resume", "status", "checkpoint-verify", "admission-lease", "pause", "stop"]) {
    const button = {
      dataset: { operateAction: action },
      addEventListener(type, handler) { if (type === "click") actionButtons.set(action, handler); },
    };
    actionButtons.set(`${action}:element`, button);
  }
  for (const stage of ["request", "preflight", "authorization", "outcome"]) {
    const button = {
      dataset: { operateStage: stage },
      addEventListener(type, handler) {
        if (type === "click") stageHandlers.set(stage, handler);
      },
      focus() {},
    };
    stageButtons.set(stage, button);
  }
  const tabs = {
    querySelectorAll(selector) {
      if (["[data-operate-stage]", "[role=tab]"].includes(selector)) return [...stageButtons.values()];
      return [];
    },
  };
  const control = (selector) => ({
    addEventListener(type, handler) { handlers.set(`${selector}:${type}`, handler); },
  });
  return {
    hidden: false,
    innerHTML: "",
    querySelectorAll(selector) {
      if (selector === "[data-operate-action]") return [...actionButtons.entries()].filter(([key]) => key.endsWith(":element")).map(([, value]) => value);
      if (selector === "[data-operate-reconcile]") return [];
      return [];
    },
    querySelector(selector) {
      if (selector === '[data-test-id="operate-tabs"]') return tabs;
      const stageMatch = selector.match(/^\[data-operate-stage="([^"]+)"\]$/);
      if (stageMatch) return stageButtons.get(stageMatch[1]) ?? null;
      return control(selector);
    },
    clickAction(action) { actionButtons.get(action)?.({ currentTarget: actionButtons.get(`${action}:element`) }); },
    clickStage(stage) { stageHandlers.get(stage)?.({ currentTarget: stageButtons.get(stage) }); },
    changeDryRun(value) { handlers.get("[data-operate-dry-run]:change")?.({ currentTarget: { checked: value } }); },
    typeParameters(value) { handlers.get("[data-operate-parameters]:input")?.({ currentTarget: { value } }); },
    typeAuthorization(value) { handlers.get("[data-operate-authorization]:input")?.({ currentTarget: { value } }); },
  };
}

const context = Object.freeze({
  runId: "fixture-run", generation: 7, generationManifest: "1".repeat(64),
  topologyId: "4".repeat(64), factoryRelease: "2".repeat(64),
  semanticRelease: "3".repeat(64), recordId: "operator-view:fixture-run:7", mode: "LIVE",
});
const defense = Object.freeze({ mutationAllowed: true, historical: false });

function previewFor(wrapper, overrides = {}) {
  const mutation = !wrapper.request.dry_run && !new Set(["status", "checkpoint-verify"]).has(wrapper.request.action);
  return {
    schema: "bilqis.bamf.control-plane.command-preview/v1",
    operation_id: `operation:${"b".repeat(64)}`,
    request: wrapper.request,
    action: wrapper.request.action,
    mode: mutation ? "mutating" : wrapper.request.dry_run ? "dry-run" : "read-only",
    target: {
      schema: "bilqis.bamf.control-plane.command-target-public/v1",
      target_ref: `command-target:${"a".repeat(64)}`,
      run_id: "live-run", run_seed: 1, run_identity_sha256: "1".repeat(64),
      generation: 4, generation_manifest_sha256: "2".repeat(64), optimizer_step: 12,
      candidate_identity_sha256: "3".repeat(64), factory_release_sha256: "4".repeat(64),
      semantic_release_sha256: "5".repeat(64), topology_sha256: "6".repeat(64),
      acceptance_sha256: "7".repeat(64), source_identity: "source:fixture",
    },
    target_ref: `command-target:${"a".repeat(64)}`,
    expected_postcondition: "operator-run-completed",
    consequence: { mutation: mutation ? "MUTATING" : "NONE", neural_mutation_permitted: mutation },
    preflight: { resource_profile: {}, admission_policy: "staged" },
    receipt: null, postcondition: null,
    ...overrides,
  };
}

function receipt(request, state = "ACCEPTED") {
  return {
    schema_version: "bilqis.bamf.mission-control.operator-action-receipt/v2",
    meta: { record_id: "cp05:fixture", run: null, materialized_at: 101, observed_at: 101, as_of: 101, coverage: "COMPLETE", authority: "DERIVED", source_refs: [], evidence_refs: [], receipt_refs: [] },
    request_id: request.request_id, request_sha256: "8".repeat(64), operation_id: `operation:${"b".repeat(64)}`,
    state, acknowledged_at: 101, target_ref: `command-target:${"a".repeat(64)}`, postcondition_ref: null, error_ref: null,
  };
}

function inspection(request, state = "COMPLETED") {
  return { ...previewFor({ request }), schema: "bilqis.bamf.control-plane.command-inspection/v1", receipt: receipt(request, state), postcondition: { kind: "fixture" } };
}

test("mutating GUI17 command cannot submit without exact typed human authorization", async () => {
  const calls = [];
  const api = {
    async requestDryRun(wrapper) { calls.push(["preview", wrapper]); return previewFor(wrapper); },
    async requestCommand(wrapper) { calls.push(["command", wrapper]); return receipt(wrapper.request); },
    async fetchReceipt(_id) { return inspection(calls.at(-1)[1].request); },
    subscribeEvents() { return () => {}; },
  };
  const host = fakeHost();
  const controller = createOperateController(api);
  await controller.activate(context, { target: host, defense });
  host.clickAction("resume");
  host.changeDryRun(false);
  await controller.preview();
  await controller.submit();
  assert.equal(calls.filter(([kind]) => kind === "command").length, 0);
  host.typeAuthorization("AUTHORIZE RESUME");
  await controller.submit();
  assert.equal(calls.filter(([kind]) => kind === "command").length, 1);
  assert.equal(calls.find(([kind]) => kind === "command")[1].request.human_authorized, true);
});

test("double submit is suppressed while one acknowledged command is in flight", async () => {
  let release;
  let commandCalls = 0;
  let finalRequest = null;
  const api = {
    async requestDryRun(wrapper) { return previewFor(wrapper); },
    requestCommand(wrapper) {
      commandCalls += 1;
      finalRequest = wrapper.request;
      return new Promise((resolve) => { release = () => resolve(receipt(wrapper.request)); });
    },
    async fetchReceipt() { return inspection(finalRequest); },
    subscribeEvents() { return () => {}; },
  };
  const host = fakeHost();
  const controller = createOperateController(api);
  await controller.activate(context, { target: host, defense });
  host.clickAction("status");
  await controller.preview();
  const first = controller.submit();
  const second = controller.submit();
  assert.equal(commandCalls, 1);
  release();
  await Promise.all([first, second]);
  assert.equal(commandCalls, 1);
});

test("lost acknowledgement never retries and reconciliation reaches authoritative terminal state", async () => {
  let commandCalls = 0;
  let lastRequest = null;
  const api = {
    async requestDryRun(wrapper) { lastRequest = wrapper.request; return previewFor(wrapper); },
    async requestCommand() { commandCalls += 1; throw Object.assign(new Error("transport lost"), { code: "LOST_ACK" }); },
    async fetchReceipt() { return inspection(lastRequest, "COMPLETED"); },
    subscribeEvents() { return () => {}; },
  };
  const host = fakeHost();
  const controller = createOperateController(api);
  await controller.activate(context, { target: host, defense });
  host.clickAction("status");
  await controller.preview();
  await controller.submit();
  assert.equal(controller.currentState().phase, "LOST_ACK");
  assert.equal(commandCalls, 1);
  await controller.reconcile();
  assert.equal(controller.currentState().phase, "TERMINAL");
  assert.equal(commandCalls, 1);
});

test("stale real shell context blocks mutation before requestCommand", async () => {
  let commandCalls = 0;
  const realContext = { ...context, runId: "live-run", recordId: "operator-view:live", generation: 3 };
  const api = {
    async requestDryRun(wrapper) { return previewFor(wrapper); },
    async requestCommand() { commandCalls += 1; throw new Error("should not execute"); },
    subscribeEvents() { return () => {}; },
  };
  const host = fakeHost();
  const controller = createOperateController(api);
  await controller.activate(realContext, { target: host, defense });
  host.clickAction("resume");
  host.changeDryRun(false);
  await controller.preview();
  assert.equal(controller.currentState().phase, "STALE_CONTEXT");
  host.typeAuthorization("AUTHORIZE RESUME");
  await controller.submit();
  assert.equal(commandCalls, 0);
});

test("dry-run remains no-mutation and needs no human authorization", async () => {
  let submitted;
  const api = {
    async requestDryRun(wrapper) { return previewFor(wrapper); },
    async requestCommand(wrapper) { submitted = wrapper; return receipt(wrapper.request); },
    async fetchReceipt() { return inspection(submitted.request); },
    subscribeEvents() { return () => {}; },
  };
  const host = fakeHost();
  const controller = createOperateController(api);
  await controller.activate(context, { target: host, defense });
  host.clickAction("resume");
  await controller.preview();
  await controller.submit();
  assert.equal(submitted.request.dry_run, true);
  assert.equal(submitted.request.human_authorized, false);
});

test("accepted owner launch seeds Stop with the exact active operation identity", async () => {
  let submitted;
  const api = {
    async requestDryRun(wrapper) { return previewFor(wrapper); },
    async requestCommand(wrapper) { submitted = wrapper; return receipt(wrapper.request); },
    async fetchReceipt() { return inspection(submitted.request, "ACCEPTED"); },
    subscribeEvents() { return () => {}; },
  };
  const host = fakeHost();
  const controller = createOperateController(api);
  await controller.activate(context, { target: host, defense });
  host.clickAction("owner-launch");
  host.changeDryRun(false);
  await controller.preview();
  host.typeAuthorization("AUTHORIZE OWNER-LAUNCH");
  await controller.submit();
  host.clickAction("stop");
  assert.equal(
    controller.currentState().parametersText,
    JSON.stringify({ operation_id: `operation:${"b".repeat(64)}` }, null, 2),
  );
  host.clickAction("resume");
  assert.equal(controller.currentState().parametersText, "{}");
});

test("OUTCOME_UNKNOWN retains the exact training operation for guarded Stop", async () => {
  let submitted;
  const api = {
    async requestDryRun(wrapper) { return previewFor(wrapper); },
    async requestCommand(wrapper) { submitted = wrapper; return receipt(wrapper.request); },
    async fetchReceipt() { return inspection(submitted.request, "OUTCOME_UNKNOWN"); },
    subscribeEvents() { return () => {}; },
  };
  const host = fakeHost();
  const controller = createOperateController(api);
  await controller.activate(context, { target: host, defense });
  host.clickAction("resume");
  host.changeDryRun(false);
  await controller.preview();
  host.typeAuthorization("AUTHORIZE RESUME");
  await controller.submit();
  assert.equal(controller.currentState().phase, "PENDING");
  host.clickAction("stop");
  assert.equal(
    controller.currentState().parametersText,
    JSON.stringify({ operation_id: `operation:${"b".repeat(64)}` }, null, 2),
  );
});

test("permitted stage navigation preserves request, preview, authorization, and reconciled outcome state", async () => {
  let submitted;
  const api = {
    async requestDryRun(wrapper) { return previewFor(wrapper); },
    async requestCommand(wrapper) { submitted = wrapper; return receipt(wrapper.request); },
    async fetchReceipt() { return inspection(submitted?.request ?? controller.currentState().preview.request); },
    subscribeEvents() { return () => {}; },
  };
  const host = fakeHost();
  const controller = createOperateController(api);
  await controller.activate(context, { target: host, defense });
  host.clickAction("resume");
  host.changeDryRun(false);
  host.typeParameters('{"minutes":30}');
  await controller.preview();
  const previewIdentity = controller.currentState().preview.target_ref;
  assert.equal(controller.currentState().activeStage, "preflight");

  host.clickStage("authorization");
  host.typeAuthorization("AUTHORIZE RESUME");
  host.clickStage("request");
  assert.equal(controller.currentState().parametersText, '{"minutes":30}');
  assert.equal(controller.currentState().preview.target_ref, previewIdentity);
  assert.equal(controller.currentState().authorization, "AUTHORIZE RESUME");

  host.clickStage("authorization");
  await controller.submit();
  const outcome = controller.currentState().inspection.operation_id;
  assert.equal(controller.currentState().activeStage, "outcome");
  host.clickStage("preflight");
  host.clickStage("outcome");
  assert.equal(controller.currentState().inspection.operation_id, outcome);
  assert.equal(controller.currentState().preview.target_ref, previewIdentity);
  assert.equal(controller.currentState().parametersText, '{"minutes":30}');
  assert.equal(controller.currentState().authorization, "AUTHORIZE RESUME");
});
