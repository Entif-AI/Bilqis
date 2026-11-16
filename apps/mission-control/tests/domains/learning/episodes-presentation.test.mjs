import test from "node:test";
import assert from "node:assert/strict";
import fs from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";
import { EPISODE_FIXTURES, EPISODE_STAGES } from "../../../renderer/episodes/episode-fixture.mjs";
import {
  episodeMarkupForTest,
  LEARNING_TABS,
} from "../../../renderer/episodes/episode-view.mjs";
import { replayPanel } from "../../../renderer/episodes/episode-replay-view.mjs";
import { t as fixtureT } from "../../../renderer/episodes/episode-view-shared.mjs";
import { assertUniqueTestIds, collectTestIds } from "../../../renderer/foundation/test-hooks.mjs";
import { t } from "../../../renderer/foundation/i18n.mjs";

const here = path.dirname(fileURLToPath(import.meta.url));
const rendererRoot = path.resolve(here, "../../../renderer");

test("learning episode UI uses affirmative evidence copy and contains no hidden-activation narrative labels", () => {
  const source = [
    "episodes/episode-view.mjs", "episodes/episode-model.mjs", "episodes/episode-fixture.mjs",
  ].map((name) => fs.readFileSync(path.join(rendererRoot, name), "utf8")).join("\n").toLowerCase();
  for (const forbidden of [
    "thought replay", "hidden reasoning", "natural-language reasoning", "operatoractionrequest",
  ]) assert.equal(source.includes(forbidden), false, forbidden);
  const markup = episodeMarkupForTest().toLowerCase();
  for (const phrase of [
    "read-only", "does not prove", "not proof", "no durable outcome is claimed",
    "no commit or rollback claim",
  ]) assert.equal(markup.includes(phrase), false, phrase);
});

test("learning transaction markup follows target narrative hierarchy with stable unique hooks", () => {
  const markup = episodeMarkupForTest("episode-record:fixture:retained-44239", 3);
  assert.equal(assertUniqueTestIds(markup), true);
  const hooks = new Set(collectTestIds(markup));
  for (const id of [
    "learning-view", "learning-heading", "learning-episode-selector", "learning-transaction-summary",
    "learning-target-capability", "learning-parent-generation", "learning-lifecycle",
    "learning-stage-target", "learning-stage-detail", "learning-stage-evidence",
    "learning-comparison-table", "learning-outcome-proof", "learning-forensics",
    "learning-candidate-inspect", "learning-tabs", "learning-tab-transaction",
    "learning-tab-lifecycle", "learning-tab-comparison", "learning-tab-outcome",
  ]) assert.equal(hooks.has(id), true, id);

  assert.equal((markup.match(/role="tablist"/g) ?? []).length, 1);
  assert.equal((markup.match(/role="tab"/g) ?? []).length, 4);
  assert.deepEqual(LEARNING_TABS.map((tab) => tab.id), [
    "transaction", "lifecycle", "comparison", "outcome",
  ]);
  assert.match(markup, /data-learning-tab="transaction"[^>]*aria-selected="true"/);
  assert.match(markup, /data-learning-panel="transaction"[^>]*data-test-id="learning-panel-transaction"/);
  assert.match(markup, /data-learning-panel="lifecycle"[^>]*hidden/);
  assert.doesNotMatch(markup, /type="range"/);
  assert.match(markup, /aria-current="step"/);
  assert.equal((markup.match(/aria-current="step"/g) ?? []).length, 1);
});

test("switching Learning tabs preserves the selected transaction identity", () => {
  const markup = episodeMarkupForTest(
    "episode-record:fixture:interference-reject",
    4,
    "comparison",
  );
  assert.match(markup, /data-learning-tab="comparison"[^>]*aria-selected="true"/);
  assert.match(markup, /data-learning-panel="comparison"[^>]*data-test-id="learning-panel-comparison"/);
  assert.match(markup, /<option value="episode-record:fixture:interference-reject" selected/);
  assert.equal((markup.match(/role="tablist"/g) ?? []).length, 1);
});

test("learning replay uses a bounded selector and progressively disclosed stage evidence", () => {
  const markup = episodeMarkupForTest("episode-record:fixture:interference-reject", 4);
  assert.match(markup, /<select[^>]+data-test-id="learning-episode-selector"/);
  assert.doesNotMatch(markup, /data-episode-id=/);
  assert.match(markup, /<details class="episode-evidence-disclosure"[^>]+data-test-id="learning-stage-evidence"/);
  assert.match(markup, /data-test-id="learning-stage-evidence-protected-0"/);
  assert.match(markup, /data-test-id="learning-stage-evidence-protected-1"/);
  assert.equal(markup.includes("candidate:fixture:interference-reject"), true);
});

test("terminal outcomes stay structurally distinct without relying on color", () => {
  const retained = episodeMarkupForTest("episode-record:fixture:retained-44239");
  const rejected = episodeMarkupForTest("episode-record:fixture:interference-reject");
  const pending = episodeMarkupForTest("episode-record:fixture:reconciliation-pending");
  assert.match(retained, /data-outcome="retained"/);
  assert.match(retained, />Retained</);
  assert.match(rejected, /data-outcome="rejected"/);
  assert.match(rejected, /data-test-id="learning-rollback-table"/);
  assert.match(rejected, /✓/);
  assert.match(pending, /data-outcome="unknown"/);
  assert.match(pending, />Unknown</);
});

test("learning fixture narrative copy is localized by stable message keys", () => {
  for (const stage of EPISODE_STAGES) {
    assert.match(stage.labelKey, /^learning\.stage\./);
    assert.ok(t(stage.labelKey));
  }
  for (const episode of EPISODE_FIXTURES) {
    for (const stage of episode.stages) {
      assert.match(stage.detailKey, /^learning\./);
      assert.ok(fixtureT(stage.detailKey));
      assert.equal(Object.hasOwn(stage, "detail"), false);
    }
  }
  for (const key of [
    "learning.view.title", "learning.selector.label", "learning.summary.eyebrow",
    "learning.lifecycle.title", "learning.comparison.title", "learning.outcome.eyebrow",
    "learning.tab.transaction", "learning.tab.lifecycle", "learning.tab.comparison",
    "learning.tab.outcome",
  ]) assert.ok(t(key));
});

test("Learning contextual help covers selector, provenance, transaction, lifecycle, comparison, resources and retention", () => {
  const markup = episodeMarkupForTest();
  for (const id of [
    "learning-help-selector", "learning-help-provenance", "learning-help-transaction",
    "learning-help-lifecycle", "learning-help-comparison", "learning-help-resources",
    "learning-help-retention",
  ]) assert.match(markup, new RegExp('data-test-id="' + id + '"'));
});

test("Learning renders shared temporal context only when an authoritative stage time exists", () => {
  const base = EPISODE_FIXTURES[0];
  const timed = {
    ...base,
    stages: base.stages.map((stage, index) => (
      index === 0 ? { ...stage, observedAt: 1794725520 } : stage
    )),
  };
  const timedMarkup = replayPanel(timed, 0);
  assert.match(timedMarkup, /<time[^>]*data-source-unix-seconds="1794725520"/);
  assert.doesNotMatch(replayPanel(base, 0), /<time\b/);
});

test("Learning fixtures remain launch-owned and production does not import episode fixtures", () => {
  const renderer = fs.readFileSync(path.join(rendererRoot, "renderer.mjs"), "utf8");
  const fixtureSupport = fs.readFileSync(path.join(rendererRoot, "fixture-support.mjs"), "utf8");
  const current = fs.readFileSync(path.join(rendererRoot, "foundation/current-view.mjs"), "utf8");
  const learningMessages = fs.readFileSync(
    path.join(rendererRoot, "foundation/messages/learning.mjs"), "utf8",
  );
  assert.match(renderer, /launchMode === "fixtures"\s*\? await import\("\.\/fixture-support\.mjs"\)\s*:\s*null/);
  assert.match(renderer, /createProductionLearningController/);
  assert.match(fixtureSupport, /renderEpisodesView/);
  assert.match(current, /state\.context\.fixture !== true/);
  assert.match(current, /domain\.innerHTML = ""/);
  assert.doesNotMatch(renderer, /episode-fixture\.mjs/);
  assert.doesNotMatch(learningMessages, /learning\.fixture\./);
  assert.doesNotMatch(learningMessages, /44238|44239|REFERENCE FIXTURES/);
});

test("learning CSS modules preserve canvas separation, responsive recomposition, and diagnostic restraint", () => {
  const css = [
    "episodes-foundation.css", "episodes-lifecycle.css",
    "episodes-comparison.css", "episodes-responsive.css",
  ].map((name) => fs.readFileSync(path.join(rendererRoot, "episodes", name), "utf8")).join("\n");
  assert.match(css, /\.episode-summary\s*\{[^}]*background:\s*var\(--surface-1\)/s);
  assert.match(css, /@media \(max-width: 720px\)/);
  assert.match(css, /:root\[data-density="compact"\]/);
  assert.match(css, /@media \(prefers-reduced-motion: reduce\)/);
  assert.doesNotMatch(css, /repeating-linear-gradient/);
  assert.doesNotMatch(css, /data-density="terminal"/);
});
