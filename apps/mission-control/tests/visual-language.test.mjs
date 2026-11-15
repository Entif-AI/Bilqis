import test from "node:test";
import assert from "node:assert/strict";
import fs from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";
import { renderComponentCatalog } from "../renderer/component-catalog.mjs";
import { DENSITIES, THEMES, loadDisplaySettings, saveDisplaySettings } from "../renderer/settings.mjs";
import { semanticStateInventory, statusBadge, evidenceValue } from "../renderer/visual-language.mjs";
import { VISUAL_REGRESSION_CASES, visualFixtureNames } from "../renderer/visual-fixtures.mjs";
import { CONTROL_ROLES, SURFACE_LEVELS, controlClass, disclosureMarkup, panelMarkup, stateMarkup, surfaceClass } from "../renderer/foundation/primitives.mjs";
import { createTranslator, formatMessage } from "../renderer/foundation/i18n.mjs";
import { assertUniqueTestIds, collectTestIds, duplicateTestIds, testId, testIdAttribute } from "../renderer/foundation/test-hooks.mjs";

const here = path.dirname(fileURLToPath(import.meta.url));
const rendererRoot = path.resolve(here, "../renderer");

function fakeStorage(initial = {}) {
  const values = new Map(Object.entries(initial));
  return {
    getItem: (key) => values.get(key) ?? null,
    setItem: (key, value) => values.set(key, value),
    snapshot: () => Object.fromEntries(values),
  };
}

test("semantic inventory covers every GUI02 state with non-color markers", () => {
  const expected = [
    "healthy", "attention", "invalid",
    "held", "unavailable", "denied", "unknown", "stale", "partial",
    "proposed", "accepted", "attempted", "reconciled",
    "live", "historical",
  ];
  assert.deepEqual(semanticStateInventory(), expected);
  for (const state of expected) {
    const html = statusBadge(state);
    assert.match(html, new RegExp('data-state="' + state + '"'));
    assert.doesNotMatch(html, /data-test-id=/);
    assert.match(html, /<span aria-hidden="true">.+<\/span>/);
  }
  assert.match(statusBadge("healthy", "", { testId: "foundation-status-healthy" }), /data-test-id="foundation-status-healthy"/);
});

test("measured/inferred and source/derived carry independent textual and structural cues", () => {
  const measuredSource = evidenceValue("91%", "measured", "source");
  const inferredDerived = evidenceValue("≈ 91%", "inferred", "derived");
  assert.match(measuredSource, /data-evidence="measured"/);
  assert.match(measuredSource, /data-authority="source"/);
  assert.match(measuredSource, /Measured/);
  assert.match(measuredSource, /Source-authoritative/);
  assert.match(inferredDerived, /data-evidence="inferred"/);
  assert.match(inferredDerived, /data-authority="derived"/);
  assert.match(inferredDerived, /Estimated \/ inferred/);
  assert.match(inferredDerived, /Learned \/ derived/);
});

test("component catalog includes every required common treatment", () => {
  const html = renderComponentCatalog();
  for (const marker of [
    "metric-tile", "status-badge", "provenance-chip", "run-identity", "trend",
    "comparison-card", "alert", "state-surface", "ui-disclosure", "graph-legend",
    "historical-banner",
  ]) assert.match(html, new RegExp(marker));
});

test("theme and density settings persist only in UI-local keys", () => {
  const storage = fakeStorage();
  saveDisplaySettings(storage, { theme: "light", density: "terminal" });
  assert.deepEqual(loadDisplaySettings(storage), { theme: "light", density: "compact" });
  assert.deepEqual(Object.keys(storage.snapshot()).sort(), ["bilqis.mc.density", "bilqis.mc.theme"]);
  assert.deepEqual(THEMES, ["dark", "light"]);
  assert.deepEqual(DENSITIES, ["comfortable", "compact"]);
});

test("visual regression fixtures cover required safety postures", () => {
  assert.deepEqual(
    visualFixtureNames(),
    ["live", "unknown", "historical", "stale", "denied", "invalidEvidence"],
  );
  assert.equal(VISUAL_REGRESSION_CASES.length, 12);
  assert.deepEqual(
    new Set(VISUAL_REGRESSION_CASES.map(({ theme }) => theme)),
    new Set(["dark", "light"]),
  );
  for (const fixture of visualFixtureNames()) {
    assert.equal(VISUAL_REGRESSION_CASES.filter((entry) => entry.fixture === fixture).length, 2);
  }
});

test("CSS supplies non-color cues without decorative patterns or retired terminal density", () => {
  const css = ["visual-tokens.css", "components.css", "shell.css"]
    .map((name) => fs.readFileSync(path.join(rendererRoot, name), "utf8"))
    .join("\n");
  assert.match(css, /border-style:\s*dashed/);
  assert.match(css, /border-style:\s*double/);
  assert.match(css, /border-style:\s*dotted/);
  assert.doesNotMatch(css, /repeating-linear-gradient/);
  assert.doesNotMatch(css, /data-density="terminal"/);
  assert.doesNotMatch(css, /\.catalog[^\{]*\{[^}]*overflow-x:\s*scroll/);
});

test("dark and light themes expose the same semantic token surface", () => {
  const css = fs.readFileSync(path.join(rendererRoot, "visual-tokens.css"), "utf8");
  for (const token of ["--canvas", "--surface-1", "--border", "--text", "--text-muted", "--healthy", "--attention", "--invalid", "--historical"]) {
    assert.equal(css.split(token).length - 1 >= 2, true, token + " missing from one theme");
  }
});

test("shared primitive grammar encodes surface depth and action roles without changing semantics", () => {
  assert.deepEqual(SURFACE_LEVELS, ["canvas", "surface-1", "surface-2", "surface-3"]);
  assert.deepEqual(CONTROL_ROLES, [
    "navigate", "filter", "group", "compare", "export", "inspect", "primary", "mutate", "status",
    "mode", "peer-tab", "secondary", "tertiary", "destructive", "link", "read-only",
  ]);
  assert.equal(surfaceClass("surface-2"), "ui-surface ui-surface-2");
  assert.equal(surfaceClass("surface-2", { bounded: true }), "ui-surface ui-surface-2 ui-surface--bounded");
  assert.throws(() => surfaceClass("canvas", { bounded: true }), /CANVAS_SURFACE_CANNOT_BE_BOUNDED/);
  assert.equal(controlClass("mutate"), "ui-control ui-control--mutate");
  assert.equal(controlClass("mode"), "ui-control ui-control--mode");
  assert.equal(controlClass("peer-tab"), "ui-control ui-control--peer-tab");
  assert.equal(controlClass("secondary"), "ui-control ui-control--secondary");
  assert.equal(controlClass("tertiary"), "ui-control ui-control--tertiary");
  assert.equal(controlClass("destructive"), "ui-control ui-control--destructive");
  assert.equal(controlClass("link"), "ui-control ui-control--link");
  assert.equal(controlClass("read-only"), "ui-control ui-control--read-only");
  const ordinaryPanel = panelMarkup({ title: "Panel", body: "Body", testId: "foundation-test-panel" });
  assert.match(ordinaryPanel, /ui-panel/);
  assert.doesNotMatch(ordinaryPanel, /ui-surface--bounded/);
  assert.match(panelMarkup({ title: "Bounded", body: "Body", testId: "foundation-test-bounded", bounded: true }), /ui-surface--bounded/);
  assert.match(disclosureMarkup({ summary: "More", body: "Detail", testId: "foundation-test-disclosure" }), /<details/);
  assert.match(stateMarkup({ title: "Unavailable", detail: "No data", testId: "foundation-test-state", kind: "error" }), /role="alert"/);
  assert.throws(() => controlClass("mystery"), /CONTROL_ROLE_INVALID/);
});

test("foundation localization uses stable keys and named parameters", () => {
  const translate = createTranslator();
  assert.equal(translate("foundation.catalog.historical.detail", { generation: 7 }), "Inspection only · generation 7 · not live learner state");
  assert.equal(translate("shell.nav.group.overviewLearning"), "Curriculum");
  assert.equal(translate("shell.nav.group.representationMechanisms"), "Semantics");
  assert.equal(translate("shell.nav.group.decisionCorrection"), "Strategies");
  assert.equal(translate("shell.nav.group.provenanceOperations"), "Records");
  assert.equal(translate("shell.context.generationHistorical", { generation: 7 }), "As of generation 7");
  assert.equal(translate("shell.context.freshness.connected"), "CONNECTED");
  assert.equal(translate("shell.context.value.notStarted"), "NOT STARTED");
  assert.equal(translate("shell.context.factExact", { label: "Topology", value: "abc" }), "Topology: abc");
  assert.equal(translate("investigation.time.historical", { generation: 7 }), "Historical · generation 7");
  assert.equal(translate("investigation.panel.compare", { count: 2 }), "Compare · 2/2");
  assert.equal(translate("investigation.notes.marker"), "Operator note · non-authoritative");
  assert.equal(translate("shell.inspector.copyDeepLink"), "Copy deep link");
  assert.match(translate("shell.destination.mission-control.purpose"), /Learner health/);
  assert.equal(formatMessage("{count} rows", { count: 3 }), "3 rows");
  assert.throws(() => translate("foundation.unknown"), /I18N_KEY_UNKNOWN/);
  assert.throws(() => formatMessage("Generation {generation}"), /I18N_PARAMETER_MISSING/);
});

test("dedicated test-hook namespace is semantic and exact ids are unique", () => {
  assert.equal(testId("foundation", "status", "healthy"), "foundation-status-healthy");
  assert.equal(testIdAttribute("foundation", "panel"), 'data-test-id="foundation-panel"');
  assert.throws(() => testId("Foundation", "bad id"), /TEST_ID_INVALID/);
  const markup = renderComponentCatalog();
  const ids = collectTestIds(markup);
  assert.equal(ids.length > 10, true);
  assert.deepEqual(duplicateTestIds(markup), []);
  assert.equal(assertUniqueTestIds(markup), true);
  assert.throws(() => assertUniqueTestIds('<i data-test-id="same"></i><b data-test-id="same"></b>'), /TEST_ID_DUPLICATE:same/);
});
