import test from "node:test";
import assert from "node:assert/strict";
import fs from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";
import { renderAtlasDomain, ensureAtlasOverview, invalidateAtlasRequests } from "../renderer/atlas/atlas-controller.mjs";
import { renderCurrentView } from "../renderer/foundation/renderer-ui.mjs";
import { activateDomainViews } from "../renderer/foundation/domain-controller.mjs";

const here = path.dirname(fileURLToPath(import.meta.url));
const rendererRoot = path.resolve(here, "../renderer");

function mountOwner(t) {
  const previous = { document: globalThis.document, window: globalThis.window, FormData: globalThis.FormData };
  t.after(() => Object.assign(globalThis, previous));
  const forms = Object.fromEntries(['[data-test-id="atlas-search-form"]', '[data-test-id="atlas-abi-form"]'].map(key => [key, {
    handlers: {}, values: { semanticId: "fixture:semantic", bank: "0", row: "1" },
    addEventListener(event, callback) { this.handlers[event] = callback; },
  }]));
  const element = () => ({ innerHTML: "", hidden: false, textContent: "", dataset: {},
    querySelectorAll: () => [], querySelector: key => forms[key] ?? null });
  const nodes = new Map(["#shell", "#domain-view", "#domain-context-boundary", "#visual-catalog", "#view-summary", "#model-nav", "#domain-context-note"].map(key => [key, element()]));
  globalThis.document = { querySelector: key => nodes.get(key), querySelectorAll: () => [] };
  globalThis.FormData = class { constructor(form) { this.form = form; } get(key) { return this.form.values[key]; } };
  let resolve; let calls = 0;
  const pending = new Promise(done => { resolve = done; });
  globalThis.window = { bamfMissionControl: { query: () => { calls += 1; return pending; } } };
  let state = { view: "atlas", selected: null, context: { runId: "fixture-run", generation: 7, mode: "LIVE", semanticRelease: "1".repeat(64) } };
  const owner = {
    render() {
      if (state.view !== "atlas") invalidateAtlasRequests();
      renderCurrentView({ ...state, modelSection: "frames" }, { id: "live", historical: false }, () => {});
      const context = state.context;
      if (state.view === "atlas") renderAtlasDomain(window.bamfMissionControl, context, () => state.view === "atlas" && state.context === context);
    },
    ensureAtlasOverview() {
      const context = state.context;
      return ensureAtlasOverview(window.bamfMissionControl, context, () => state.view === "atlas" && state.context === context);
    },
  };
  owner.render();
  return { owner, host: nodes.get("#domain-view"), forms,
    navigate(view) { state = { ...state, view }; owner.render(); },
    changeContext() { state = { ...state, context: { ...state.context, generation: 6 } }; owner.render(); },
    finish() { resolve({ schema: "bamf.gui07.query-error/v1", accepted: false, reason: "delayed fixture" }); },
    calls: () => calls,
  };
}

test("real Atlas overview/search/ABI handlers cannot repaint Frames or School after navigation", async t => {
  for (const operation of ["overview", "search", "abi"]) {
    for (const destination of ["model", "school"]) {
      await t.test(`${operation} -> ${destination}`, async t => {
        const fixture = mountOwner(t);
        const form = fixture.forms[operation === "search" ? '[data-test-id="atlas-search-form"]' : '[data-test-id="atlas-abi-form"]'];
        const completion = operation === "overview" ? fixture.owner.ensureAtlasOverview()
          : form.handlers.submit({ preventDefault() {}, currentTarget: form });
        assert.match(fixture.host.innerHTML, /data-test-id="atlas-request-loading"/);
        fixture.navigate(destination);
        if (destination === "model") assert.equal(fixture.host.hidden, true);
        const destinationMarkup = fixture.host.innerHTML;
        fixture.finish(); await completion;
        assert.equal(fixture.host.innerHTML, destinationMarkup);
        const calls = fixture.calls();
        fixture.navigate("atlas"); await fixture.owner.ensureAtlasOverview();
        assert.ok(fixture.calls() > calls, "a discarded unfinished load can be retried");
      });
    }
  }
});

test("real Atlas handlers keep the newest request's outcome", async t => {
  const fixture = mountOwner(t);
  const requests = [];
  globalThis.window.bamfMissionControl.query = () => new Promise((_resolve, reject) => requests.push(reject));
  const search = fixture.forms['[data-test-id="atlas-search-form"]'];
  const abi = fixture.forms['[data-test-id="atlas-abi-form"]'];
  const older = search.handlers.submit({ preventDefault() {}, currentTarget: search });
  const newer = abi.handlers.submit({ preventDefault() {}, currentTarget: abi });
  requests[1](new Error("newest request outcome")); await newer;
  requests[0](new Error("obsolete request outcome")); await older;
  assert.match(fixture.host.innerHTML, /newest request outcome/);
  assert.doesNotMatch(fixture.host.innerHTML, /obsolete request outcome/);
});

test("real Atlas completion cannot publish a result from the prior context", async t => {
  const fixture = mountOwner(t);
  const completion = fixture.owner.ensureAtlasOverview();
  fixture.changeContext();
  const markup = fixture.host.innerHTML;
  fixture.finish(); await completion;
  assert.equal(fixture.host.innerHTML, markup);
});

test("the domain activation owner binds Atlas completion to the current shell state", async t => {
  const fixture = mountOwner(t);
  let state = { view: "atlas", context: { runId: "fixture-run", generation: 7, mode: "LIVE", semanticRelease: "1".repeat(64) } };
  activateDomainViews({ state, getState: () => state, defense: { id: "live" }, api: window.bamfMissionControl,
    homeController: { async activate() {}, async deactivate() {} }, onInspect() {} });
  assert.match(fixture.host.innerHTML, /data-test-id="atlas-request-loading"/);
  state = { ...state, view: "school" };
  renderCurrentView(state, { id: "live" }, () => {});
  const markup = fixture.host.innerHTML;
  fixture.finish(); await new Promise(resolve => setImmediate(resolve));
  assert.equal(fixture.host.innerHTML, markup);
});

test("production shell routes completed GUI domains into the real view host", () => {
  const index = fs.readFileSync(path.join(rendererRoot, "index.html"), "utf8");
  const renderer = fs.readFileSync(path.join(rendererRoot, "renderer.mjs"), "utf8");
  const current = fs.readFileSync(path.join(rendererRoot, "foundation/current-view.mjs"), "utf8");
  const activation = fs.readFileSync(path.join(rendererRoot, "foundation/domain-controller.mjs"), "utf8");
  const capability = fs.readFileSync(path.join(rendererRoot, "capability/app.mjs"), "utf8");

  assert.match(
    index,
    /<section id="view-host" class="view-host"[\s\S]*<section id="domain-view" class="domain-view"/,
  );

  assert.match(renderer, /createHomeController\(window\.bamfMissionControl\)/);
  assert.match(renderer, /createCapabilityExplorer\(/);
  assert.match(renderer, /activateDomainViews\(\{/);
  assert.match(renderer, /homeController, resourceController, operateController/);
  assert.match(renderer, /capabilityExplorer/);

  assert.match(activation, /state\?\.view === "mission-control"/);
  assert.match(activation, /homeController\.activate/);
  assert.match(activation, /state\?\.view === "atlas"/);
  assert.match(activation, /renderAtlasDomain/);
  assert.match(activation, /state\?\.view === "capability"/);
  assert.match(activation, /capabilityExplorer\?\.update/);
  assert.match(capability, /new DossierController/);

  for (const [view, owner] of [
    ["model", "renderNeuralView"],
    ["memory", "renderMemoryView"],
    ["lineage", "renderLineageView"],
    ["evidence", "renderEvidenceView"],
  ]) {
    assert.match(current, new RegExp('state\\.view === "' + view + '"'));
    assert.match(current, new RegExp(owner + '\\('));
  }
});
