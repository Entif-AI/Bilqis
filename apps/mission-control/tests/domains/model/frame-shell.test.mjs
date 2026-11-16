import test from "node:test";
import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import { mountFrameExplorer } from "../../../renderer/frames/frame-explorer.mjs";
import { createFrameShell } from "../../../renderer/frames/frame-shell.mjs";

const page = JSON.parse(readFileSync(new URL("../../../fixtures/frame-inspections-v1.json", import.meta.url)))[1];

function harness(t, { fixture = true } = {}) {
  const previous = { document: globalThis.document, window: globalThis.window };
  t.after(() => Object.assign(globalThis, previous));
  const element = () => ({ hidden: true, value: "7", innerHTML: "", textContent: "", replaceChildren() {}, addEventListener() {} });
  const parts = new Map([
    '[data-test-id="model-frame-results"]',
    '[data-test-id="model-frame-request-state"]',
    '[data-test-id="model-frame-generation"]',
  ].map(key => [key, element()]));
  const host = { ...element(), querySelector: key => parts.get(key) };
  const nodes = new Map([
    ['[data-test-id="model-frame-workspace-host"]', host],
    ['[data-test-id="shell-model-subnav"]', element()],
  ]);
  globalThis.document = { querySelector: key => nodes.get(key), querySelectorAll: () => [] };
  let resolve; let queries = 0;
  globalThis.window = { bamfMissionControl: { querySnapshot: () => { queries += 1; return new Promise(done => { resolve = done; }); } } };
  const originalContext = { runId: fixture ? "fixture-run" : "production-run", generation: 7, mode: "LIVE", freshness: "FRESH", fixture };
  let state = { view: "model", modelSection: "frames", selected: null, context: originalContext, mutationAvailable: true };
  let defense = { id: "live", mutationAllowed: true, historical: false };
  const shell = createFrameShell({ getState: () => state, setState: next => { state = next; }, getDefense: () => defense,
    render() {}, refresh() {}, onInspect() {}, fixtureSupport: fixture ? { mountFrameExplorer } : null });
  return { shell, host, originalContext, state: () => state, set: next => { state = next; }, defend: next => { defense = next; }, queries: () => queries, finish: () => resolve?.(structuredClone(page)) };
}

test("production Frames fail closed without loading fixture explorer data", t => {
  const production = harness(t, { fixture: false });
  production.shell.beforeRender(); production.shell.afterRender();
  assert.equal(production.queries(), 0);
  assert.equal(production.state().context, production.originalContext);
  assert.match(production.host.innerHTML, /model-frame-production-unavailable/);
  assert.match(production.host.innerHTML, /Frame compiler detail unavailable/);
  assert.doesNotMatch(production.host.innerHTML, /ILLUSTRATIVE FIXTURE|fixture-run|current fixture|historical fixture/i);
});

test("reconnect discards the old return context and pending frame response", async t => {
  const fixture = harness(t);
  fixture.shell.beforeRender(); fixture.shell.afterRender();
  fixture.shell.reset();
  const nextContext = { ...fixture.originalContext, generation: 99 };
  fixture.set({ ...fixture.state(), mutationAvailable: false, context: nextContext });
  fixture.defend({ id: "loading", mutationAllowed: false, historical: true });
  fixture.shell.beforeRender(); fixture.shell.afterRender();
  fixture.finish(); await Promise.resolve(); await Promise.resolve();
  assert.equal(fixture.state().context, nextContext);
  assert.equal(fixture.state().mutationAvailable, false);
});

test("exit after a reconnect restores the new context and current defensive availability", async t => {
  for (const id of ["live", "denied", "stale"]) {
    await t.test(id, t => {
      const fixture = harness(t);
      fixture.shell.beforeRender(); fixture.shell.reset();
      const verified = { ...fixture.originalContext, generation: 99 };
      fixture.set({ ...fixture.state(), context: verified, mutationAvailable: id === "live" });
      fixture.defend({ id, mutationAllowed: id === "live", historical: id !== "live" });
      fixture.shell.beforeRender();
      fixture.set({ ...fixture.state(), context: { ...verified, generation: 6 }, mutationAvailable: false, view: "school" });
      fixture.shell.beforeRender();
      assert.equal(fixture.state().context, verified);
      assert.equal(fixture.state().mutationAvailable, id === "live");
    });
  }
});

test("reconnect without a valid snapshot cannot resurrect an earlier context", t => {
  const fixture = harness(t);
  fixture.shell.beforeRender(); fixture.shell.reset(); fixture.set(null);
  fixture.defend({ id: "denied", mutationAllowed: false, historical: false });
  fixture.shell.beforeRender(); fixture.shell.afterRender();
  assert.equal(fixture.state(), null);
});
