import test from "node:test";
import assert from "node:assert/strict";
import fs from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";
import {
  MANUAL_KEYBOARD_SCENARIO,
  isActivationKey,
  nextRovingIndex,
} from "../renderer/foundation/accessibility.mjs";

const here = path.dirname(fileURLToPath(import.meta.url));
const rendererRoot = path.resolve(here, "../renderer");
const source = (name) => fs.readFileSync(path.join(rendererRoot, name), "utf8");

test("keyboard roving semantics cover arrows, Home, End, Enter and Space", () => {
  assert.equal(nextRovingIndex(1, "ArrowDown", 4), 2);
  assert.equal(nextRovingIndex(0, "ArrowUp", 4), 3);
  assert.equal(nextRovingIndex(2, "Home", 4), 0);
  assert.equal(nextRovingIndex(1, "End", 4), 3);
  assert.equal(nextRovingIndex(1, "Tab", 4), 1);
  assert.equal(isActivationKey("Enter"), true);
  assert.equal(isActivationKey(" "), true);
  assert.equal(isActivationKey("Escape"), false);
});

test("focus return preserves an unkeyed invoking control while it remains connected", async () => {
  const { focusToken, restoreFocus } = await import("../renderer/foundation/accessibility.mjs");
  let focused = false;
  const invokingControl = {
    dataset: {},
    id: "",
    isConnected: true,
    focus() { focused = true; },
  };
  const token = focusToken(invokingControl);
  assert.equal(typeof token, "object");
  assert.equal(restoreFocus({ querySelector() { return null; } }, token), true);
  assert.equal(focused, true);
});

test("manual keyboard journey covers shell, School, inspector, graph, palette and offline mutation boundary", () => {
  assert.equal(MANUAL_KEYBOARD_SCENARIO.length >= 7, true);
  const scenario = MANUAL_KEYBOARD_SCENARIO.join("\n");
  for (const phrase of ["Skip to main content", "School", "Global inspector", "Escape", "dependency graph", "Control+K", "Operate is disabled"]) {
    assert.match(scenario, new RegExp(phrase.replace("+", "\\+")));
  }
});

test("static shell exposes named landmarks, skip navigation, dedicated announcements and focus-safe overlays", () => {
  const html = source("index.html");
  assert.match(html, /class="skip-link" href="#main-content"/);
  assert.match(html, /<main id="main-content"[^>]*tabindex="-1"/);
  assert.match(html, /id="defensive-banner"[^>]*aria-live="polite"[^>]*aria-atomic="true"/);
  assert.match(html, /id="announcer"[^>]*aria-live="polite"/);
  assert.match(html, /id="inspector"[^>]*role="dialog"[^>]*aria-labelledby="inspector-title"[^>]*inert/);
  assert.match(html, /id="inspector-splitter"[^>]*role="separator"[^>]*tabindex="-1"/);
  assert.match(html, /id="inspector-splitter"[^>]*aria-valuemin="160"[^>]*aria-valuemax="720"[^>]*aria-valuenow="360"/);
  assert.match(html, /id="inspector-forensics"[^>]*>\s*<summary data-i18n="shell\.inspector\.forensics"/s);
  assert.match(html, /id="copy-deep-link"[^>]*data-test-id="investigation-inspector-copy-deep-link"/);
  assert.match(html, /<dialog id="command-palette"[^>]*aria-labelledby="palette-title"/);
  assert.match(html, /id="primary-nav"[^>]*aria-keyshortcuts="Control\+K Meta\+K"/);
  assert.match(html, /data-test-id="shell-command-shortcut-hint"/);
  assert.match(html, /data-test-id="shell-rail-toggle"/);
  assert.doesNotMatch(html, /data-test-id="shell-command-trigger"/);
});

test("renderer entrypoint remains syntactically loadable after shell composition changes", async () => {
  await import("../renderer/renderer.mjs").then(
    () => assert.fail("renderer entrypoint should require a browser runtime"),
    (error) => assert.doesNotMatch(String(error), /SyntaxError|already been declared/),
  );
});

test("global inspector recomposes desktop shell instead of reserving investigation-strip margin", () => {
  const ui = source("foundation/renderer-ui.mjs");
  const shell = source("shell.css");
  const interactions = source("interactions/interactions.css");
  assert.match(ui, /dataset\.inspector = open \? "open" : "closed"/);
  assert.match(shell, /\.shell\[data-inspector="open"\][^{]*\{[^}]*grid-template-columns:/s);
  assert.doesNotMatch(interactions, /\.shell\[data-inspector="open"\] \.investigation-strip/);
});

test("focus is visibly retained and reduced-motion plus forced-colors modes are explicit", () => {
  const css = `${source("visual-tokens.css")}\n${source("shell.css")}\n${source("components.css")}`;
  assert.match(css, /:focus-visible\s*\{[^}]*outline:/s);
  assert.doesNotMatch(css, /focus-visible[^\{]*\{[^}]*outline:\s*none/s);
  assert.match(css, /@media \(prefers-reduced-motion:\s*reduce\)/);
  assert.match(css, /@media \(forced-colors:\s*active\)/);
  assert.match(css, /overflow-wrap:\s*anywhere/);
  assert.match(css, /\.visual-catalog\[hidden\]\s*\{\s*display:\s*none/);
});

test("School graph remains keyboard interactive while exposing an equivalent relationship table", () => {
  const school = source("school/school-view.mjs");
  assert.match(school, /role="group" aria-label="\$\{t\("school\.dependency\.aria"\)\}"/);
  assert.match(school, /school\.dependency\.caption/);
  assert.match(school, /testIdAttribute\("school", "dependency", "graph"\)/);
  assert.match(school, /testIdAttribute\("school", "dependency", "table"\)/);
  assert.match(school, /aria-sort=/);
  assert.match(school, /nextRovingIndex/);
  assert.match(school, /isActivationKey/);
  assert.match(school, /aria-pressed=/);
});

test("renderer blocks Operate unless verified live context is re-established and preserves offline inspection", () => {
  const renderer = [
    source("renderer.mjs"),
    source("foundation/bootstrap-controller.mjs"),
    source("foundation/renderer-ui.mjs"),
    source("foundation/current-view.mjs"),
    source("foundation/i18n.mjs"),
    source("foundation/messages/shell.mjs"),
  ].join("\n");
  assert.match(renderer, /id === "operate" && !state\.mutationAvailable/);
  assert.match(renderer, /loadCachedOperatorView/);
  assert.match(renderer, /cacheOperatorView/);
  assert.match(renderer, /Inspection-only evidence retained/);
  assert.match(renderer, /establishSnapshot\(\{ preserveRoute: true \}\)/);
});

test("startup reports service learner telemetry and trainer stages without live fixture substitution", () => {
  const bootstrap = source("foundation/bootstrap-controller.mjs");
  const current = source("foundation/current-view.mjs");
  const ui = source("foundation/renderer-ui.mjs");
  const i18n = [source("foundation/i18n.mjs"), source("foundation/messages/shell.mjs")].join("\n");
  const html = source("index.html");
  for (const label of ["Local control plane", "Learner discovery", "Mission Control telemetry", "Trainer"]) {
    assert.match(i18n, new RegExp(label));
  }
  assert.match(bootstrap, /telemetry-pending/);
  assert.match(ui, /foundation\.bootstrap\.telemetryPending\.label/);
  assert.match(i18n, /Learner ready · telemetry starting/);
  assert.match(i18n, /reference fixtures use the explicit fixture launch mode/);
  assert.doesNotMatch(html, /fixture:prometheus-disposable/);
});
