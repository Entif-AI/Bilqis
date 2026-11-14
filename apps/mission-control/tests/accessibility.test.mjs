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
  assert.match(html, /<dialog id="command-palette"[^>]*aria-labelledby="palette-title"/);
  assert.match(html, /aria-keyshortcuts="Control\+K"/);
});

test("global investigation surface reserves inspector space while the inspector is open", () => {
  const ui = source("foundation/renderer-ui.mjs");
  const css = source("interactions/interactions.css");
  assert.match(ui, /dataset\.inspector = open \? "open" : "closed"/);
  assert.match(css, /\.shell\[data-inspector="open"\] \.investigation-strip/);
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
  assert.match(school, /role="group" aria-label="Capability prerequisite dependency graph"/);
  assert.match(school, /Equivalent table for the selected capability dependency graph/);
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
  const html = source("index.html");
  for (const label of ["Local control plane", "Learner discovery", "Mission Control telemetry", "Trainer"]) {
    assert.match(current, new RegExp(label));
  }
  assert.match(bootstrap, /telemetry-pending/);
  assert.match(ui, /Learner ready · telemetry starting/);
  assert.match(current, /fixture data is never substituted for live state/);
  assert.doesNotMatch(html, /fixture:prometheus-disposable/);
});
