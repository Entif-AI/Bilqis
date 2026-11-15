import test from "node:test";
import assert from "node:assert/strict";
import fs from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";
import {
  authorizationPhrase,
  buildPreviewRequest,
  buildSubmitRequest,
  contextConflicts,
  parseParameters,
} from "../../renderer/operate/operate-model.mjs";
import { renderOperateMarkup } from "../../renderer/operate/operate-view.mjs";
import { operateT } from "../../renderer/operate/operate-messages.mjs";
import { assertUniqueTestIds, collectTestIds } from "../../renderer/foundation/test-hooks.mjs";
import { renderCurrentView } from "../../renderer/foundation/current-view.mjs";
import { createShellState, inspect, openSelectionOwner } from "../../renderer/shell-state.mjs";

const ROOT = path.resolve(path.dirname(fileURLToPath(import.meta.url)), "../..", "renderer");

const context = Object.freeze({
  runId: "real-run", generation: 4, generationManifest: "2".repeat(64),
  topologyId: "6".repeat(64), factoryRelease: "4".repeat(64),
  semanticRelease: "5".repeat(64), recordId: "operator-view:real-run:4", mode: "LIVE",
});

function target(overrides = {}) {
  return Object.freeze({
    target_ref: `command-target:${"a".repeat(64)}`,
    run_id: "real-run", generation: 4, generation_manifest_sha256: "2".repeat(64),
    topology_sha256: "6".repeat(64), factory_release_sha256: "4".repeat(64),
    semantic_release_sha256: "5".repeat(64), source_identity: "source:fixture",
    ...overrides,
  });
}

function preview({ mutation = true, request = null, targetValue = target() } = {}) {
  const wrapped = request ?? buildPreviewRequest({
    action: "resume", dryRun: !mutation, parameters: [], context, now: 100,
  });
  return Object.freeze({
    operation_id: `operation:${"b".repeat(64)}`,
    request: wrapped.request,
    action: wrapped.request.action,
    target_ref: targetValue.target_ref,
    target: targetValue,
    consequence: Object.freeze({ mutation: mutation ? "MUTATING" : "NONE", neural_mutation_permitted: mutation }),
  });
}

test("GUI17 parses only admitted CP05 scalar parameters", () => {
  assert.deepEqual(parseParameters('{"minutes":30,"verify_source":true}'), [
    { key: "minutes", value: 30 },
    { key: "verify_source", value: true },
  ]);
  assert.throws(() => parseParameters('{"shell":"rm -rf /"}'), /GUI17_PARAMETER_UNSUPPORTED:shell/);
  assert.throws(() => parseParameters('{"minutes":{"nested":1}}'), /GUI17_PARAMETER_SCALAR_REQUIRED:minutes/);
  assert.throws(() => parseParameters("[1]"), /GUI17_PARAMETERS_OBJECT_REQUIRED/);
});

test("preview is never human authorization and final mutation reuses the exact reviewed identity", () => {
  const staged = buildPreviewRequest({ action: "resume", dryRun: false, parameters: [], context, now: 123 });
  assert.equal(staged.request.human_authorized, false);
  const reviewed = preview({ request: staged, mutation: true });
  const submitted = buildSubmitRequest(reviewed);
  assert.equal(submitted.expectedTargetRef, reviewed.target_ref);
  assert.equal(submitted.request.request_id, staged.request.request_id);
  assert.equal(submitted.request.idempotency_key, staged.request.idempotency_key);
  assert.equal(submitted.request.human_authorized, true);
  assert.equal(authorizationPhrase(reviewed), "AUTHORIZE RESUME");
});

test("dry-run and read-only consequences never acquire human authorization", () => {
  const staged = buildPreviewRequest({ action: "resume", dryRun: true, parameters: [], context, now: 124 });
  const submitted = buildSubmitRequest(preview({ request: staged, mutation: false }));
  assert.equal(submitted.request.dry_run, true);
  assert.equal(submitted.request.human_authorized, false);
});

test("known generation or release drift blocks authorization while fixture context is never promoted to authority", () => {
  const changed = preview({ targetValue: target({ generation: 5, semantic_release_sha256: "9".repeat(64) }) });
  assert.deepEqual(contextConflicts(context, changed).map((item) => item.label), ["generation", "semantic release"]);
  assert.deepEqual(contextConflicts({ ...context, runId: "fixture-run", recordId: "operator-view:fixture-run:7" }, changed), []);
});

test("Operate markup keeps pause unavailable while exposing stop through the command boundary", () => {
  const markup = renderOperateMarkup({
    action: "status", dryRun: false, parametersText: "{}", phase: "IDLE",
    preview: null, inspection: null, conflicts: [], error: null, authorization: "",
  }, { mutationAllowed: true });
  assert.match(markup, /Command boundary/);
  assert.match(markup, /data-operate-action="pause"[\s\S]*?disabled/);
  assert.doesNotMatch(markup, /data-operate-action="stop"[\s\S]*?disabled/);
  assert.deepEqual(parseParameters('{"operation_id":"operation:' + "a".repeat(64) + '"}'), [
    { key: "operation_id", value: "operation:" + "a".repeat(64) },
  ]);
  assert.match(markup, /Owner commands are dispatched only from this reviewed command workspace/);
  assert.match(markup, /data-operate-action="stop"[\s\S]*?data-posture="destructive"/);
});

test("Operate target markup is tabbed, localized, stable-hooked, and free of danger theater", () => {
  const markup = renderOperateMarkup({
    action: "status", dryRun: false, parametersText: "{}", phase: "IDLE",
    preview: null, inspection: null, conflicts: [], error: null, authorization: "",
  }, { mutationAllowed: true });
  assert.equal(assertUniqueTestIds(markup), true);
  const hooks = new Set(collectTestIds(markup));
  for (const hook of [
    "operate-view", "operate-heading", "operate-boundary", "operate-catalog", "operate-workflow", "operate-tabs",
    "operate-request", "operate-request-parameters", "operate-request-preview",
    "operate-panel-preflight", "operate-panel-outcome", "operate-action-status", "operate-action-pause",
  ]) assert.equal(hooks.has(hook), true, hook);
  assert.match(markup, new RegExp(operateT("operate.title")));
  assert.match(markup, /operate-stage-tabs/);
  assert.doesNotMatch(markup, /operate-sequence/);
  assert.doesNotMatch(markup, /repeating-linear-gradient|MUTATION ZONE/);
});

test("Operate uses one top-level four-stage tabset instead of rendering the full workflow as one long sequence", () => {
  const markup = renderOperateMarkup({
    action: "status", dryRun: false, parametersText: "{}", phase: "IDLE",
    preview: null, inspection: null, conflicts: [], error: null, authorization: "",
  }, { mutationAllowed: true });
  assert.match(markup, /role="tablist"/);
  for (const stage of ["request", "preflight", "authorization", "outcome"]) {
    assert.match(markup, new RegExp(`data-operate-stage="${stage}"`));
    assert.match(markup, new RegExp(`id="operate-panel-${stage}"[\\s\\S]*role="tabpanel"`));
  }
  assert.doesNotMatch(markup, /class="operate-sequence"/);
});

test("Operate route paint synchronously replaces stale prior-route content before its controller activates", () => {
  const previousDocument = globalThis.document;
  const shell = { dataset: {} };
  const domain = {
    hidden: true,
    innerHTML: '<section><h2>Evidence</h2><p>Reference fixture catalog</p></section>',
  };
  const summary = { textContent: "Evidence summary" };
  globalThis.document = {
    querySelector(selector) {
      return { "#shell": shell, "#domain-view": domain, "#view-summary": summary }[selector] ?? null;
    },
  };
  try {
    renderCurrentView(
      { view: "operate", mutationAvailable: true, context: { mode: "LIVE", fixture: false } },
      { mutationAllowed: true },
      () => {}, {}, () => {}, () => {}, null, null,
    );
    assert.equal(domain.hidden, false);
    assert.match(domain.innerHTML, /data-test-id="operate-route-pending"/);
    assert.doesNotMatch(domain.innerHTML, /Evidence|Reference fixture/i);
    assert.notEqual(summary.textContent, "Evidence summary");
  } finally {
    globalThis.document = previousDocument;
  }
});

test("fixture deep-link posture keeps Operate unavailable even when the defensive shell is otherwise healthy", () => {
  const previousDocument = globalThis.document;
  const shell = { dataset: {} };
  const domain = { hidden: true, innerHTML: "stale" };
  const summary = { textContent: "stale" };
  globalThis.document = {
    querySelector(selector) {
      return { "#shell": shell, "#domain-view": domain, "#view-summary": summary }[selector] ?? null;
    },
  };
  try {
    renderCurrentView(
      { view: "operate", mutationAvailable: false, context: { mode: "LIVE", fixture: true } },
      { mutationAllowed: true },
      () => {}, {}, () => {}, () => {}, null, null,
    );
    assert.match(domain.innerHTML, /data-route-state="unavailable"/);
    assert.match(domain.innerHTML, /inspection-only/);
  } finally {
    globalThis.document = previousDocument;
  }
});

test("Operate defensive posture makes preflight visibly unavailable", () => {
  const markup = renderOperateMarkup({
    action: "status", dryRun: false, parametersText: "{}", phase: "IDLE",
    preview: null, inspection: null, conflicts: [], error: null, authorization: "",
  }, { mutationAllowed: false, detail: "Historical inspection only." });
  assert.match(markup, /data-test-id="operate-unavailable"/);
  assert.match(markup, /data-operate-preview[^>]*disabled/);
  assert.match(markup, /Historical inspection only\./);
});

test("Operate mutating review gives authorization exceptional salience without changing target binding", () => {
  const reviewed = preview();
  const markup = renderOperateMarkup({
    action: "resume", activeStage: "authorization", dryRun: false, parametersText: "{}", phase: "REVIEW",
    preview: reviewed, inspection: null, conflicts: [], error: null, authorization: "",
  }, { mutationAllowed: true });
  assert.match(markup, /data-posture="mutating"/);
  assert.match(markup, /data-test-id="operate-authorization"/);
  assert.match(markup, /data-test-id="operate-authorization-target"/);
  assert.match(markup, new RegExp(reviewed.target_ref.replace(/[.*+?^${}()|[\]\\]/g, "\\$&")));
  assert.match(markup, /AUTHORIZE RESUME/);
});

test("Operate supplies contextual help across request, preflight, authorization, and outcome stages", () => {
  const reviewed = {
    ...preview(),
    preflight: { resource_profile: { reserve_gib: 100 }, admission_policy: "staged" },
  };
  const states = [
    [{ action: "resume", activeStage: "request", dryRun: true, parametersText: "{}", phase: "IDLE", preview: null, inspection: null, conflicts: [], error: null, authorization: "" }, ["catalog", "dry-run"]],
    [{ action: "resume", activeStage: "preflight", dryRun: false, parametersText: "{}", phase: "REVIEW", preview: reviewed, inspection: null, conflicts: [], error: null, authorization: "" }, ["preflight", "target-binding", "resource-profile"]],
    [{ action: "resume", activeStage: "authorization", dryRun: false, parametersText: "{}", phase: "REVIEW", preview: reviewed, inspection: null, conflicts: [], error: null, authorization: "" }, ["authorization", "mutation-boundary"]],
    [{ action: "resume", activeStage: "outcome", dryRun: false, parametersText: "{}", phase: "LOST_ACK", preview: reviewed, inspection: null, conflicts: [], error: null, authorization: "" }, ["unknown-outcome", "reconciliation"]],
  ];
  for (const [state, hooks] of states) {
    const markup = renderOperateMarkup(state, { mutationAllowed: true });
    for (const hook of hooks) assert.match(markup, new RegExp(`data-test-id="operate-help-${hook}-trigger"`), hook);
  }
});

test("Operate outcome uses shared relative and exact temporal markup for authoritative operation times", () => {
  const reviewed = preview({ request: buildPreviewRequest({
    action: "status", dryRun: false, parameters: [], context, now: 1_700_000_000_123,
  }), mutation: false });
  const markup = renderOperateMarkup({
    action: "status", activeStage: "outcome", dryRun: false, parametersText: "{}", phase: "TERMINAL",
    preview: reviewed, conflicts: [], error: null, authorization: "",
    inspection: {
      operation_id: "operation:" + "b".repeat(64), request: reviewed.request,
      receipt: {
        state: "COMPLETED", acknowledged_at: 1_700_000_003_456, target_ref: reviewed.target_ref,
        postcondition_ref: "postcondition:1", error_ref: null,
        meta: { record_id: "receipt:1", observed_at: 1_700_000_004_567, as_of: 1_700_000_004_567, materialized_at: 1_700_000_005_678 },
      },
      postcondition: { kind: "status" }, logs: null,
    },
  }, { mutationAllowed: true });
  for (const [hook, value] of [
    ["requested", "1700000000.123"], ["acknowledged", "1700000003.456"], ["observed", "1700000004.567"],
    ["as-of", "1700000004.567"], ["materialized", "1700000005.678"],
  ]) {
    assert.match(markup, new RegExp(`data-source-unix-seconds="${value}"[^>]*data-test-id="operate-time-${hook}"`), hook);
  }
  assert.match(markup, /Exact UTC:/);
});

test("Operate primary error copy remains human-readable without exposing GUI error codes", () => {
  const markup = renderOperateMarkup({
    action: "status", activeStage: "request", dryRun: false, parametersText: "{", phase: "ERROR",
    preview: null, inspection: null, conflicts: [], authorization: "",
    error: { code: "GUI17_PARAMETERS_JSON_INVALID", message: "Parameters must be valid JSON." },
  }, { mutationAllowed: true });
  assert.match(markup, /Parameters must be valid JSON/);
  assert.doesNotMatch(markup, /GUI17_/);
});

test("Operate owned human copy resolves through stable message keys", () => {
  for (const key of [
    "operate.title", "operate.catalog.title", "operate.request.preview", "operate.preflight.title",
    "operate.authorization.title", "operate.receipt.reconcile", "operate.announce.unknown",
  ]) assert.equal(typeof operateT(key), "string");
});

test("Operate CSS is tabbed, responsive, compact-aware, focus-visible, and pattern-free", () => {
  const css = fs.readFileSync(path.join(ROOT, "operate", "operate.css"), "utf8");
  assert.match(css, /\.operate-stage-tabs\s*\{/);
  assert.match(css, /\.operate-stage-tab\[aria-selected="true"\]/);
  assert.match(css, /\.operate-action\[data-posture="destructive"\]/);
  assert.match(css, /data-density="compact"/);
  assert.match(css, /@media \(max-width:\s*980px\)/);
  assert.match(css, /@media \(max-width:\s*720px\)/);
  assert.match(css, /prefers-reduced-motion/);
  assert.match(css, /forced-colors/);
  assert.match(css, /focus-visible/);
  assert.doesNotMatch(css, /repeating-linear-gradient/);
  assert.doesNotMatch(css, /data-density="terminal"/);
});

test("Operate inspection surfaces bounded trainer log tails for owner diagnosis", () => {
  const markup = renderOperateMarkup({
    action: "status", activeStage: "outcome", dryRun: false, parametersText: "{}", phase: "TERMINAL",
    preview: null, conflicts: [], error: null, authorization: "",
    inspection: {
      operation_id: "operation:" + "a".repeat(64),
      receipt: { state: "FAILED", error_ref: "command-error:1:abc" },
      logs: { stdout_tail: "last good step\n", stderr_tail: "trainer exploded safely\n" },
    },
  }, { mutationAllowed: true });
  assert.match(markup, /Trainer log tail/);
  assert.match(markup, /trainer exploded safely/);
  assert.match(markup, /last good step/);
});

test("operation inspector identities route back to Operate", () => {
  const operatorView = {
    active_capability_id: "B.EXAMPLE", learner_state: "READY", stage: "ASSESS_MAIN",
    related_record_ids: [], schema_version: "bilqis.bamf.mission-control.operator-view/v1",
    meta: {
      as_of: 1, authority: "DERIVED", coverage: "COMPLETE", evidence_refs: [],
      materialized_at: 1, observed_at: 1, receipt_refs: [], record_id: "operator-view:test",
      source_refs: [],
      run: {
        candidate_identity_sha256: "2".repeat(64), factory_release_sha256: "2".repeat(64),
        generation: 1, generation_manifest_sha256: "1".repeat(64), run_id: "run-test",
        run_identity_sha256: "4".repeat(64), semantic_release_sha256: "3".repeat(64),
        topology_sha256: "4".repeat(64),
      },
    },
  };
  const selected = inspect(createShellState(operatorView), { kind: "operation", id: "operation:1" });
  assert.equal(openSelectionOwner(selected).view, "operate");
});
