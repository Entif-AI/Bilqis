import test from "node:test";
import assert from "node:assert/strict";
import { readdirSync, readFileSync } from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";
import { DESTINATIONS } from "../renderer/shell-state.mjs";

const here = path.dirname(fileURLToPath(import.meta.url));
const repo = path.resolve(here, "../../..");
const browserRoot = path.join(here, "browser");
const read = relative => readFileSync(path.join(repo, relative), "utf8");

const atlas = read("docs/architecture/mission-control-design/INFORMATION_ATLAS.md");
const inventory = read("docs/architecture/mission-control-design/CURRENT_STATE_UI_INVENTORY.md");
const flows = read("docs/architecture/mission-control-design/FLOWS.md");
const constraints = read("docs/architecture/mission-control-design/CONSTRAINT_REGISTER.md");
const design = read("apps/mission-control/DESIGN.md");
const styleGuide = read("docs/architecture/mission-control-design/STYLE_GUIDE.md");
const composition = read("docs/architecture/mission-control-design/VISUAL_COMPOSITION_SPEC.md");
const antiPatterns = read("docs/architecture/mission-control-design/ANTI_PATTERN_GALLERY.md");

function ids(source, pattern) {
  return new Set(Array.from(source.matchAll(pattern), match => match[1]));
}

function browserJourneyFiles(directory = browserRoot) {
  return readdirSync(directory, { withFileTypes: true }).flatMap(entry => {
    const target = path.join(directory, entry.name);
    if (entry.isDirectory()) return browserJourneyFiles(target);
    return entry.name.endsWith(".mjs") || entry.name.endsWith(".cjs") ? [target] : [];
  });
}

test("browser journeys select application UI only through stable test hooks", () => {
  const files = browserJourneyFiles();
  const bannedApis = /\.getBy(?:Role|Text|Title|Label|Placeholder|AltText|TestId)\s*\(/g;
  const contentSelectors = /\.filter\s*\(\s*\{\s*has(?:Text)?\s*:/g;
  const literalLocators = /\.locator\s*\(\s*(['"])(.*?)\1\s*\)/g;

  for (const file of files) {
    const name = path.relative(browserRoot, file);
    const source = readFileSync(file, "utf8");
    assert.doesNotMatch(source, bannedApis, `${name} uses a content/ARIA selector`);
    assert.doesNotMatch(source, contentSelectors, `${name} filters a locator by rendered content`);
    for (const match of source.matchAll(literalLocators)) {
      assert.match(
        match[2],
        /^\[data-test-id(?:=|\^=)/,
        `${name} locator must use an exact or intentional data-test-id prefix: ${match[2]}`,
      );
    }
  }
});

test("production shell contains only target-state global surfaces", () => {
  const index = read("apps/mission-control/renderer/index.html");
  const rendererUi = read("apps/mission-control/renderer/foundation/renderer-ui.mjs");
  const currentView = read("apps/mission-control/renderer/foundation/current-view.mjs");

  for (const retired of [
    "domain-context-boundary",
    "domain-context-note",
    "demo-actions",
    "visual-catalog",
  ]) {
    assert.doesNotMatch(index, new RegExp(retired), `${retired} survived in the production shell`);
  }
  assert.doesNotMatch(rendererUi, /renderDemoActions|demoObjects/);
  assert.doesNotMatch(currentView, /renderComponentCatalog/);
  assert.match(index, /data-test-id="shell-main-content"/);
  assert.match(index, /data-test-id="shell-view-host"/);
});

test("all current top-level UI components have a target disposition", () => {
  const currentComponents = ids(inventory, /^### (CUR-COMP-\d{3,4})\b/gm);
  assert.ok(currentComponents.size > 40, "current component inventory unexpectedly small");
  for (const component of currentComponents) {
    assert.match(atlas, new RegExp(`\\b${component}\\b`), `${component} has no target disposition`);
  }

  const currentViews = ids(inventory, /^## (CUR-VIEW-\d{3})\b/gm);
  assert.equal(currentViews.size, 14);
  for (const current of currentViews) {
    const target = current.replace("CUR-VIEW-", "VIEW-D-");
    assert.match(atlas, new RegExp(`^## ${target}\\b`, "m"), `${current} has no target view`);
  }
  assert.match(inventory, /^## CUR-SHELL-001\b/m);
  assert.match(atlas, /^## SHELL-D-001\b/m);
});

test("every target component declares its migration disposition or new-target status", () => {
  const headings = Array.from(atlas.matchAll(/^#### (COMP-D-\d{3,4})\b/gm));
  assert.ok(headings.length > 60, "target component register unexpectedly small");
  for (let index = 0; index < headings.length; index += 1) {
    const start = headings[index].index;
    const end = headings[index + 1]?.index ?? atlas.length;
    const block = atlas.slice(start, end);
    assert.match(
      block,
      /\*\*Current substrate \/ disposition:\*\*|New explicit target component/,
      `${headings[index][1]} lacks migration disposition`,
    );
  }
});

test("runtime destination set and atlas view set remain one-to-one", () => {
  const atlasViews = ids(atlas, /^## (VIEW-D-\d{3})\b/gm);
  assert.equal(atlasViews.size, 14);
  assert.equal(DESTINATIONS.length, 14);
  assert.deepEqual(
    DESTINATIONS.map(([id]) => id),
    [
      "mission-control", "school", "capability", "learning",
      "atlas", "model", "memory", "teacher", "salience", "corrections",
      "lineage", "resources", "evidence", "operate",
    ],
  );
});

test("flow and constraint references resolve against their authority registers", () => {
  const definedFlows = ids(flows, /^## (FLOW-D-\d{3})\b/gm);
  assert.equal(definedFlows.size, 18);
  const flowRefs = ids(`${design}\n${atlas}`, /\b(FLOW-D-\d{3})\b/g);
  for (const ref of flowRefs) assert.ok(definedFlows.has(ref), `${ref} is not defined in FLOWS.md`);

  const definedConstraints = ids(constraints, /^\| (CON-D-\d{3}) \|/gm);
  assert.ok(definedConstraints.size >= 88);
  const constraintRefs = ids(
    `${design}\n${atlas}\n${styleGuide}\n${composition}\n${antiPatterns}\n${flows}`,
    /\b(CON-D-\d{3})\b/g,
  );
  for (const ref of constraintRefs) {
    assert.ok(definedConstraints.has(ref), `${ref} is not defined in CONSTRAINT_REGISTER.md`);
  }
});

test("static production-shell copy is routed through localization keys", () => {
  const index = read("apps/mission-control/renderer/index.html");
  assert.match(index, /<title data-i18n="shell\.documentTitle"><\/title>/);
  assert.match(index, /data-i18n-aria-label="shell\.domainView\.aria"/);
  assert.doesNotMatch(index, /(?<!i18n-)aria-label="[A-Za-z]/);

  const currentView = read("apps/mission-control/renderer/foundation/current-view.mjs");
  assert.doesNotMatch(currentView, />Historical School lens</);
  assert.doesNotMatch(currentView, />UNAVAILABLE</);
  assert.doesNotMatch(currentView, /The checked-in School matrix has no exact snapshot/);
});

test("skip navigation moves focus without corrupting the hash route", () => {
  const interactions = read("apps/mission-control/renderer/foundation/static-interactions.mjs");
  assert.match(interactions, /\[data-test-id="shell-skip-main"\]/);
  assert.match(interactions, /\[data-test-id="shell-main-content"\]/);
  assert.match(interactions, /main\.focus\(\{ preventScroll: true \}\)/);
  assert.match(interactions, /event\.preventDefault\(\)/);
});
