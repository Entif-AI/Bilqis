import test from "node:test";
import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import {
  applyShellPreferences,
  constrainInspectorWidth,
  INSPECTOR_MIN_WIDTH,
  inspectorWidthForDestination,
  loadShellPreferences,
  saveShellPreferences,
  toggleRailPreference,
  withInspectorWidthPreference,
} from "../renderer/shell-preferences.mjs";
import {
  contextHelpMarkup,
} from "../renderer/foundation/primitives.mjs";
import {
  formatRelativeUnixSeconds,
  temporalMarkup,
} from "../renderer/foundation/temporal.mjs";
import { createTranslator } from "../renderer/foundation/i18n.mjs";
import { constrainRouteToLaunchMode } from "../renderer/foundation/bootstrap-controller.mjs";

const source = (relative) => readFileSync(
  new URL(`../renderer/${relative}`, import.meta.url),
  "utf8",
);

function fakeStorage(initial = {}) {
  const values = new Map(Object.entries(initial));
  return {
    getItem: (key) => values.get(key) ?? null,
    setItem: (key, value) => values.set(key, value),
    snapshot: () => Object.fromEntries(values),
  };
}

test("rail collapse is one persistent shell preference independent of route state", () => {
  const storage = fakeStorage();
  const expanded = loadShellPreferences(storage);
  assert.deepEqual(expanded, { rail: "expanded", inspectorWidths: {} });
  const collapsed = toggleRailPreference(expanded);
  assert.deepEqual(collapsed, { rail: "collapsed", inspectorWidths: {} });
  saveShellPreferences(storage, collapsed);
  assert.deepEqual(storage.snapshot(), {
    "bilqis.mc.rail": "collapsed",
    "bilqis.mc.inspectorWidths": "{}",
  });
  assert.deepEqual(loadShellPreferences(storage), collapsed);
  const root = { dataset: {} };
  applyShellPreferences(root, collapsed);
  assert.equal(root.dataset.rail, "collapsed");
});

test("inspector widths are destination-local and constrained by usable primary width", () => {
  const storage = fakeStorage();
  let preferences = loadShellPreferences(storage);
  preferences = withInspectorWidthPreference(preferences, "learning", 448);
  preferences = withInspectorWidthPreference(preferences, "school", 224);
  saveShellPreferences(storage, preferences);
  const restored = loadShellPreferences(storage);
  assert.equal(inspectorWidthForDestination(restored, "learning"), 448);
  assert.equal(inspectorWidthForDestination(restored, "school"), 224);
  assert.notEqual(
    inspectorWidthForDestination(restored, "learning"),
    inspectorWidthForDestination(restored, "school"),
  );
  assert.equal(constrainInspectorWidth(120), INSPECTOR_MIN_WIDTH);
  assert.equal(constrainInspectorWidth(999, {
    viewportWidth: 1200,
    railWidth: 180,
  }), 532);
});

test("context help is one keyboard-reachable described control with a future docs slot", () => {
  const markup = contextHelpMarkup({
    label: "About run context",
    description: "Explains the run context.",
    testId: "shell-help-run-context",
  });
  assert.match(markup, /<button[^>]*aria-describedby="shell-help-run-context-content"/);
  assert.match(markup, /aria-label="About run context"/);
  assert.match(markup, /role="tooltip"/);
  assert.match(markup, />\?<\/span>/);
  assert.doesNotMatch(markup, /<a\b/);

  const documented = contextHelpMarkup({
    label: "About run context",
    description: "Explains the run context.",
    testId: "shell-help-run-context",
    docs: { href: "https://github.com/Entif-AI/Bilqis-MLX", label: "Read documentation" },
  });
  assert.doesNotMatch(documented, /<a\b/);
  assert.match(documented, /data-docs-slot="project-github"/);
  assert.match(documented, /data-docs-href="https:\/\/github\.com\/Entif-AI\/Bilqis-MLX"/);
  assert.throws(
    () => contextHelpMarkup({
      label: "Unsafe",
      description: "Unsafe link.",
      testId: "shell-help-unsafe",
      docs: { href: "javascript:alert(1)", label: "Unsafe" },
    }),
    /CONTEXT_HELP_DOCS_URL_INVALID/,
  );
});

test("temporal primitive localizes relative and full time without inventing missing source time", () => {
  const nowMs = Date.UTC(2026, 10, 15, 7, 0, 0);
  const unixSeconds = Math.floor((nowMs - (8 * 60 * 1000)) / 1000);
  assert.equal(
    formatRelativeUnixSeconds(unixSeconds, { nowMs, locale: "en-US" }),
    "8 minutes ago",
  );
  const markup = temporalMarkup({
    unixSeconds,
    nowMs,
    locale: "en-US",
    testId: "resources-time-sample",
  });
  assert.match(markup, /<time[^>]*datetime="2026-11-15T06:52:00\.000Z"/);
  assert.match(markup, /aria-describedby="resources-time-sample-detail"/);
  assert.match(markup, />8 minutes ago</);
  assert.match(markup, /role="tooltip"/);
  assert.match(markup, /2026/);

  const fractional = temporalMarkup({
    unixSeconds: unixSeconds + 0.321,
    nowMs,
    locale: "en-US",
    testId: "resources-time-fractional",
  });
  assert.match(fractional, /datetime="2026-11-15T06:52:00\.321Z"/);
  assert.match(fractional, new RegExp(`data-source-unix-seconds="${unixSeconds}\\.321"`));

  const unavailable = temporalMarkup({
    unixSeconds: null,
    nowMs,
    locale: "en-US",
    testId: "resources-time-unavailable",
  });
  assert.doesNotMatch(unavailable, /<time\b/);
  assert.match(unavailable, /Time unavailable/);

  for (const [index, sentinel] of [0, -1].entries()) {
    const sentinelMarkup = temporalMarkup({
      unixSeconds: sentinel,
      nowMs,
      locale: "en-US",
      testId: `resources-time-sentinel-${index}`,
    });
    assert.doesNotMatch(sentinelMarkup, /<time\b/);
    assert.match(sentinelMarkup, /Time unavailable/);
  }
});

test("shared shell has no permanent command trigger and exposes a global keyboard palette hint", () => {
  const html = source("index.html");
  assert.doesNotMatch(html, /id="palette-trigger"/);
  assert.doesNotMatch(html, /data-test-id="shell-command-trigger"/);
  assert.match(html, /id="primary-nav"[^>]*aria-keyshortcuts="Control\+K Meta\+K"/);
  assert.match(html, /data-test-id="shell-command-shortcut-hint"/);
  assert.match(html, /id="rail-toggle"[^>]*data-test-id="shell-rail-toggle"/);
});

test("fixture provenance is launch-owned and cannot be promoted by a deep-link flag", () => {
  const route = {
    view: "memory",
    context: {
      runId: "fixture:claimed",
      generation: 9,
      mode: "LIVE",
      fixture: true,
    },
  };
  assert.equal(constrainRouteToLaunchMode(route, "production").context.fixture, false);
  assert.equal(constrainRouteToLaunchMode({ ...route, context: { ...route.context, fixture: false } }, "fixtures").context.fixture, true);
  const bootstrap = source("foundation/bootstrap-controller.mjs");
  assert.match(bootstrap, /if \(!fixtureMode\) cacheOperatorView/);
  assert.match(bootstrap, /!fixtureMode && operatorView === null/);
  assert.match(bootstrap, /mutationAvailable: fixtureMode \? false/);
});

test("production launch strips fixture object selections and evidence origins before routing", () => {
  const route = {
    view: "learning",
    context: {
      runId: "fixture:gui05", generation: 9, mode: "LIVE", fixture: true,
    },
    selected: { kind: "candidate", id: "candidate:fixture:leak" },
    evidenceOrigin: {
      selected: { kind: "episode", id: "episode-record:fixture:leak" },
    },
  };
  const production = constrainRouteToLaunchMode(route, "production");
  assert.equal(production.context.fixture, false);
  assert.equal(production.selected, null);
  assert.equal(production.evidenceOrigin, null);

  const fixture = constrainRouteToLaunchMode(route, "fixtures");
  assert.deepEqual(fixture.selected, route.selected);
  assert.deepEqual(fixture.evidenceOrigin, route.evidenceOrigin);
});

test("production launch strips fixture-looking selection even without a context payload", () => {
  assert.deepEqual(
    constrainRouteToLaunchMode({
      view: "learning",
      selected: { kind: "episode", id: "episode-record:fixture:retained-44239" },
    }, "production"),
    { view: "learning", selected: null },
  );
});

test("shell interactions make context popovers exclusive and reset only changed primary destinations", () => {
  const interactions = source("foundation/static-interactions.mjs");
  const renderer = source("renderer.mjs");
  const rendererUi = source("foundation/renderer-ui.mjs");
  assert.match(interactions, /system-context-disclosure/);
  assert.match(interactions, /view-settings-disclosure/);
  assert.match(interactions, /other\.removeAttribute\("open"\)/);
  assert.match(interactions, /event\.key\s*!==\s*"Escape"/);
  assert.match(interactions, /owner\.dataset\.popupDismissed\s*=\s*"true"/);
  assert.match(rendererUi, /button\[data-view\]:not\(:disabled\)/);
  assert.match(renderer, /lastRenderedView\s*!==\s*nextView/);
  assert.match(renderer, /resetPrimaryScroll/);
  assert.match(renderer, /behavior:\s*"auto"/);
});

test("shell group labels are concise and contextual help copy remains localized", () => {
  const t = createTranslator();
  assert.equal(t("shell.nav.group.overviewLearning"), "Curriculum");
  assert.equal(t("shell.nav.group.representationMechanisms"), "Semantics");
  assert.equal(t("shell.nav.group.decisionCorrection"), "Strategies");
  assert.equal(t("shell.nav.group.provenanceOperations"), "Records");
  for (const key of [
    "shell.help.run.description",
    "shell.help.nav.curriculum.description",
    "shell.help.nav.semantics.description",
    "shell.help.nav.strategies.description",
    "shell.help.nav.records.description",
  ]) {
    assert.ok(t(key).length > 20, key);
  }
});

test("shared CSS gives rail, help, temporal, and context controls explicit accessible treatments", () => {
  const shell = source("shell.css");
  const components = source("components.css");
  const tokens = source("visual-tokens.css");
  assert.match(tokens, /--rail-collapsed-width:/);
  assert.match(shell, /:root\[data-rail="collapsed"\]/);
  assert.match(shell, /\.nav-group \+ \.nav-group/);
  assert.match(shell, /\.context-disclosure > summary[^}]*align-items:\s*center/s);
  assert.match(shell, /\.context-disclosure > summary[^}]*background:\s*var\(--surface-2\)/s);
  assert.match(shell, /\.shell\[data-inspector="open"\][^{]*\{[^}]*grid-template-columns:[^}]*var\(--inspector-width/s);
  assert.match(shell, /@media \(max-width:\s*980px\)[\s\S]*\.shell\[data-inspector="open"\][^{]*\{[^}]*grid-template-columns:\s*minmax\(0, 1fr\)/);
  assert.match(shell, /@media \(max-width:\s*980px\)[\s\S]*\.shell\[data-inspector="open"\] \.inspector\s*\{[^}]*grid-column:\s*auto[^}]*position:\s*fixed[^}]*\}[\s\S]*\.inspector\s*\{[^}]*width:\s*min\(92vw, 480px\)/s);
  assert.match(components, /\.ui-context-help__trigger/);
  assert.match(components, /\.ui-context-help__content:popover-open/);
  assert.match(components, /\.ui-temporal__detail:popover-open/);
  assert.match(components, /@media \(forced-colors:\s*active\)/);
}
);

test("inspector splitter has pointer and keyboard resize paths with persistent destination width", () => {
  const html = source("index.html");
  const interactions = source("foundation/static-interactions.mjs");
  const inspector = source("foundation/inspector-controller.mjs");
  assert.match(html, /id="inspector-splitter"[^>]*role="separator"[^>]*aria-orientation="vertical"/);
  assert.match(html, /aria-valuemin="160"/);
  assert.match(interactions, /pointerdown/);
  assert.match(interactions, /pointermove/);
  assert.match(interactions, /ArrowLeft/);
  assert.match(interactions, /ArrowRight/);
  assert.match(interactions, /Home/);
  assert.match(interactions, /End/);
  assert.match(inspector, /inspectorWidthForDestination/);
  assert.match(inspector, /withInspectorWidthPreference/);
  assert.match(inspector, /saveShellPreferences\(window\.localStorage, shellPreferences\)/);
});
