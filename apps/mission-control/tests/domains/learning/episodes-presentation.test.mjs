import test from "node:test";
import assert from "node:assert/strict";
import fs from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";
import { EPISODE_FIXTURES, EPISODE_STAGES } from "../../../renderer/episodes/episode-fixture.mjs";
import { episodeMarkupForTest } from "../../../renderer/episodes/episode-view.mjs";
import { assertUniqueTestIds, collectTestIds } from "../../../renderer/foundation/test-hooks.mjs";
import { t } from "../../../renderer/foundation/i18n.mjs";

const here = path.dirname(fileURLToPath(import.meta.url));
const rendererRoot = path.resolve(here, "../../../renderer");

test("learning episode UI is read-only evidence replay and contains no hidden-activation narrative labels", () => {
  const source = [
    "episodes/episode-view.mjs", "episodes/episode-model.mjs", "episodes/episode-fixture.mjs",
  ].map((name) => fs.readFileSync(path.join(rendererRoot, name), "utf8")).join("\n").toLowerCase();
  for (const forbidden of [
    "thought replay", "hidden reasoning", "natural-language reasoning", "operatoractionrequest",
  ]) assert.equal(source.includes(forbidden), false, forbidden);
  assert.equal(episodeMarkupForTest().toLowerCase().includes("read-only"), true);
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
    "learning-candidate-inspect",
  ]) assert.equal(hooks.has(id), true, id);

  const summaryAt = markup.indexOf('data-test-id="learning-transaction-summary"');
  const lifecycleAt = markup.indexOf('data-test-id="learning-lifecycle"');
  const comparisonAt = markup.indexOf('data-test-id="learning-comparison"');
  const outcomeAt = markup.indexOf('data-test-id="learning-outcome-proof"');
  assert.equal(summaryAt < lifecycleAt && lifecycleAt < comparisonAt && comparisonAt < outcomeAt, true);
  assert.doesNotMatch(markup, /type="range"/);
  assert.match(markup, /aria-current="step"/);
  assert.equal((markup.match(/aria-current="step"/g) ?? []).length, 1);
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
      assert.ok(t(stage.detailKey));
      assert.equal(Object.hasOwn(stage, "detail"), false);
    }
  }
  for (const key of [
    "learning.view.title", "learning.selector.label", "learning.summary.eyebrow",
    "learning.lifecycle.title", "learning.comparison.title", "learning.outcome.eyebrow",
  ]) assert.ok(t(key));
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
