import test from "node:test";
import assert from "node:assert/strict";
import fs from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";
import {
  teacherComparisonStateForTest, teacherMarkupForTest,
} from "../../renderer/teacher/teacher-view.mjs";
import { assertUniqueTestIds, collectTestIds } from "../../renderer/foundation/test-hooks.mjs";
import { t } from "../../renderer/foundation/i18n.mjs";

const here = path.dirname(fileURLToPath(import.meta.url));
const rendererRoot = path.resolve(here, "../../renderer");
const teacherCss = () => [
  "teacher/teacher.css",
  "teacher/teacher-core.css",
  "teacher/teacher-detail.css",
  "teacher/teacher-comparison.css",
].map((name) => fs.readFileSync(path.join(rendererRoot, name), "utf8")).join("\n");

test("teacher target markup uses one top-level tab layer and one active panel", () => {
  const markup = teacherMarkupForTest();
  assert.equal(assertUniqueTestIds(markup), true);
  const ids = new Set(collectTestIds(markup));
  for (const id of [
    "teacher-view",
    "teacher-heading",
    "teacher-tabs",
    "teacher-tab-roster",
    "teacher-tab-comparison",
    "teacher-tab-fidelity",
    "teacher-panel-roster",
    "teacher-panel-comparison",
    "teacher-panel-fidelity",
    "teacher-roster",
    "teacher-roster-scroll",
    "teacher-strategy-detail",
    "teacher-strategy-inspect",
  ]) assert.equal(ids.has(id), true, id);

  assert.equal((markup.match(/role="tablist"/g) ?? []).length, 1);
  assert.equal((markup.match(/role="tab"/g) ?? []).length, 3);
  assert.match(markup, /teacher-tab-roster[^>]+aria-selected="true"/);
  assert.doesNotMatch(markup, /<section class="teacher-comparison"/);
  assert.doesNotMatch(markup, /<section class="teacher-fidelity"/);
  assert.match(markup, /<table class="teacher-roster-table">/);
  assert.match(markup, /<section class="teacher-strategy-detail"/);
  assert.doesNotMatch(markup, /class="strategy-card"/);
  assert.doesNotMatch(markup, /class="fidelity-card"/);
  assert.doesNotMatch(markup, /class="ui-glossary"/);
});

test("teacher tab panels preserve roster and comparison interaction grammars", () => {
  const state = teacherComparisonStateForTest();
  const roster = teacherMarkupForTest(
    state.selectedStrategyId, state.selectedStrategyIds, state.scope, "roster",
  );
  const comparison = teacherMarkupForTest(
    state.selectedStrategyId, state.selectedStrategyIds, state.scope, "comparison",
  );
  assert.match(roster, /class="teacher-strategy-select"[^>]+aria-pressed=/);
  assert.match(roster, /<a href="#\/view\/learning\?/);
  assert.match(roster, /class="teacher-state"/);
  assert.match(comparison, /class="teacher-compare-strategy"[^>]+aria-pressed=/);
  assert.match(comparison, /<select data-compare-scope/);
  assert.match(comparison, new RegExp(state.scope.value.replace(".", "\\.")));
});

test("teacher comparison and fidelity remain aligned descriptive evidence without ranking", () => {
  const comparison = teacherMarkupForTest(undefined, undefined, undefined, "comparison");
  const fidelity = teacherMarkupForTest(undefined, undefined, undefined, "fidelity");
  assert.match(comparison, /<table class="teacher-comparison-table"/);
  assert.match(fidelity, /<table class="teacher-fidelity-table"/);
  assert.match(comparison, /Comparison presents measured outcomes/);
  assert.match(fidelity, /Observational only/);
  assert.match(fidelity, /read-only fidelity evidence/);
  for (const forbidden of ["winner", "rank #", "recommended", "trophy"]) {
    assert.equal((comparison + fidelity).toLowerCase().includes(forbidden), false, forbidden);
  }
});

test("teacher projection limitation and metric guidance are progressive disclosures", () => {
  const markup = teacherMarkupForTest(undefined, undefined, undefined, "fidelity");
  assert.match(markup, /<details class="teacher-projection"/);
  assert.match(markup, /<details class="teacher-glossary"/);
  assert.doesNotMatch(markup, /<div class="ui-glossary"/);
});

test("teacher owned human copy resolves through stable i18n keys", () => {
  for (const key of [
    "teacher.view.title",
    "teacher.roster.title",
    "teacher.detail.outcomes",
    "teacher.comparison.title",
    "teacher.fidelity.title",
    "teacher.tabs.roster",
    "teacher.help.strategy.body",
    "teacher.help.metrics.body",
    "teacher.help.comparison.body",
    "teacher.help.fidelity.body",
    "teacher.help.provenance.body",
    "teacher.help.mutation.body",
    "teacher.projection.summary",
    "teacher.inspector.role",
  ]) assert.ok(t(key));
});

test("teacher CSS is table-oriented, responsive, compact-aware, and free of retired decoration", () => {
  const css = teacherCss();
  assert.match(css, /\.teacher-table-wrap\s*\{[^}]*overflow:\s*auto/s);
  assert.match(css, /\.teacher-roster-table,/);
  assert.match(css, /font-variant-numeric:\s*tabular-nums/);
  assert.match(css, /\.teacher-tabs\s*\{/);
  assert.match(css, /\.teacher-tab\[aria-selected="true"\]/);
  assert.match(css, /:root\[data-density="compact"\]/);
  assert.match(css, /@media \(max-width: 980px\)/);
  assert.match(css, /@media \(prefers-reduced-motion: reduce\)/);
  assert.doesNotMatch(css, /repeating-linear-gradient/);
  assert.doesNotMatch(css, /data-density="terminal"/);
  assert.doesNotMatch(css, /\.strategy-roster\s*\{[^}]*repeat\(2,/s);
});
