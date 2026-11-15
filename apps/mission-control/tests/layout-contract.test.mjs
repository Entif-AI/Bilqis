import test from "node:test";
import assert from "node:assert/strict";
import fs from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";

const here = path.dirname(fileURLToPath(import.meta.url));
const rendererRoot = path.resolve(here, "../renderer");
const source = (name) => fs.readFileSync(path.join(rendererRoot, name), "utf8");
const teacherCss = () => [
  "teacher/teacher.css",
  "teacher/teacher-core.css",
  "teacher/teacher-detail.css",
  "teacher/teacher-comparison.css",
].map(source).join("\n");

test("shared shell owns stable grouped navigation and compact destination geometry", () => {
  const tokens = source("visual-tokens.css");
  const shell = source("shell.css");
  const home = source("home/home.css");
  const dossier = source("capability/dossier.css");
  const frames = source("frame-explorer.css");

  assert.match(tokens, /--rail-width:\s*184px/);
  assert.match(tokens, /--page-gutter:/);
  assert.match(shell, /grid-template-columns:\s*var\(--rail-width\) minmax\(0, 1fr\) 0/);
  assert.match(shell, /\.rail\s*\{[^}]*position:\s*sticky[^}]*height:\s*100vh[^}]*overflow-y:\s*auto/s);
  assert.match(shell, /\.view-host\s*\{[^}]*max-width:\s*none[^}]*var\(--page-gutter\)/s);
  assert.match(shell, /\.destination-header h1\s*\{[^}]*font-size:\s*var\(--type-title\)/s);
  assert.match(shell, /\.nav-group-label\s*\{/);
  assert.match(shell, /@media \(max-width:\s*980px\)[\s\S]*#primary-nav\s*\{[^}]*overflow-x:\s*auto/s);
  assert.doesNotMatch(shell, /#primary-nav button::first-letter/);
  assert.doesNotMatch(shell, /font-size:\s*0/);

  assert.doesNotMatch(home, /grid-template-columns:\s*176px/);
  assert.doesNotMatch(dossier, /^\.context-bar\s*\{/m);
  assert.doesNotMatch(dossier, /^\.context-actions\s*\{/m);
  assert.doesNotMatch(frames, /^\s*\.context-bar\s*\{/m);
  assert.doesNotMatch(frames, /^\s*\.context-actions\s*\{/m);
});

test("shell target anatomy removes redundant chrome and keeps secondary context disclosed", () => {
  const html = source("index.html");
  const shell = source("shell.css");
  const ui = source("foundation/renderer-ui.mjs");
  const interactions = source("foundation/static-interactions.mjs");

  assert.doesNotMatch(html, /brand-mark/);
  assert.match(html, /id="system-context-disclosure"[^>]*class="context-disclosure"/);
  assert.match(html, /id="view-settings-disclosure"[^>]*class="context-disclosure"/);
  assert.doesNotMatch(html, /id="run-selector"/);
  assert.doesNotMatch(html, /id="generation-selector"/);
  assert.match(html, /data-test-id="shell-destination-header"/);
  assert.match(ui, /DESTINATION_GROUPS\.map/);
  assert.match(ui, /testIdAttribute\("nav", "destination", id\)/);
  assert.match(ui, /shell\.context\.factExact/);
  assert.equal(ui.includes('aria-label="${esc(accessible)}"'), true);
  assert.doesNotMatch(interactions, /generation-selector/);
  assert.doesNotMatch(shell, /repeating-linear-gradient/);
  assert.doesNotMatch(shell, /font-size:\s*0/);
});

test("investigation plane keeps forensic identity in the inspector and toolbar controls subordinate", () => {
  const html = source("index.html");
  const view = source("interactions/view.mjs");
  const css = source("interactions/interactions.css");
  const shell = source("shell.css");

  assert.match(html, /id="inspector-forensics"[^>]*data-test-id="investigation-inspector-forensics"/);
  assert.match(html, /id="inspector-deep-link-value"[^>]*data-test-id="investigation-inspector-deep-link-value"/);
  assert.match(html, /id="copy-deep-link"[^>]*data-test-id="investigation-inspector-copy-deep-link"/);
  assert.match(view, /data-test-id="investigation-time-toggle"/);
  assert.match(view, /data-test-id="investigation-open-compare"/);
  assert.match(view, /data-test-id="investigation-open-pins"/);
  assert.match(view, /data-test-id="investigation-open-notes"/);
  assert.doesNotMatch(view, /buildAppUri|Exact app URI|investigation-link/);
  assert.match(css, /\.investigation-time form\s*\{[^}]*position:\s*absolute/s);
  assert.match(css, /\.investigation-time:not\(\[open\]\) form\s*\{\s*display:\s*none;\s*\}/);
  assert.match(css, /\.pin-list li,[\s\S]*border-bottom:\s*1px solid var\(--border\)/);
  assert.doesNotMatch(css, /\.pin-list article|\.annotation-list article/);
  assert.doesNotMatch(css, /text-overflow:\s*ellipsis/);
  assert.match(shell, /\.inspector-deep-link code\s*\{[^}]*overflow-wrap:\s*anywhere[^}]*white-space:\s*normal/s);
  assert.match(shell, /\.inspector-forensics:not\(\[open\]\) > :not\(summary\)\s*\{\s*display:\s*none;\s*\}/);
});

test("operator values and wide School data stay inside their owning surfaces", () => {
  const home = source("home/home.css");
  const school = source("school/school.css");
  const teacher = teacherCss();
  const salience = source("salience/salience.css");

  assert.match(home, /\.home-current dd[^}]*overflow-wrap:\s*anywhere/s);
  assert.match(home, /\.home-school-table-wrap[^}]*overflow:\s*auto/s);
  assert.doesNotMatch(home, /text-overflow:\s*ellipsis/);
  assert.doesNotMatch(home, /\.home-metric-card/);
  assert.match(school, /\.school-panel\s*\{[^}]*min-width:\s*0[^}]*overflow:\s*hidden/s);
  assert.match(school, /\.matrix-scroll\s*\{[^}]*min-width:\s*0[^}]*width:\s*100%[^}]*overflow:\s*auto/s);
  assert.match(teacher, /\.teacher-table-wrap\s*\{[^}]*min-width:\s*0[^}]*width:\s*100%[^}]*overflow:\s*auto/s);
  assert.match(teacher, /\.teacher-detail-grid,/);
  assert.match(teacher, /\.teacher-comparison-controls\s*\{/);
  assert.match(salience, /\.salience-table-wrap\s*\{[^}]*min-width:\s*0[^}]*width:\s*100%[^}]*overflow:\s*auto/s);
});

test("operator typography and explanatory surfaces use the shared visual language", () => {
  const tokens = source("visual-tokens.css");
  const shell = source("shell.css");
  const school = source("school/school-view.mjs");
  const teacher = [
    source("teacher/teacher-view.mjs"),
    source("teacher/teacher-roster-view.mjs"),
    source("teacher/teacher-comparison-view.mjs"),
    source("teacher/teacher-fidelity-view.mjs"),
  ].join("\n");
  const salience = [
    source("salience/salience-view.mjs"),
    source("salience/salience-observation-view.mjs"),
    source("salience/salience-aggregation-view.mjs"),
    source("salience/salience-routing-view.mjs"),
  ].join("\n");
  const corrections = source("corrections/corrections-view.mjs");
  const evidence = source("evidence/evidence-markup.mjs");

  for (const [token, value] of [
    ["--type-label", "12px"], ["--type-body", "14px"],
    ["--type-section", "20px"], ["--type-display", "30px"],
  ]) assert.match(tokens, new RegExp(token + ":\\s*" + value));
  assert.match(shell, /\.context-bar\s*\{[^}]*display:\s*flex[^}]*justify-content:\s*space-between/s);
  assert.match(shell, /\.context-disclosure\s*\{[^}]*position:\s*relative/s);
  assert.match(shell, /\.context-popover\s*\{[^}]*position:\s*absolute/s);
  assert.match(shell, /\.context-facts\s*\{[^}]*repeat\(3, minmax\(140px, 1fr\)\)/s);
  assert.doesNotMatch(shell, /\.selector\s*\{/);
  assert.match(shell, /\.ui-glossary\s*\{/);
  assert.match(school, /class="ui-glossary"/);
  assert.doesNotMatch(salience, /class="ui-glossary"/);
  assert.match(salience, /salience-axis-guide/);
  assert.doesNotMatch(corrections, /class="ui-glossary"/);
  assert.doesNotMatch(teacher, /class="ui-glossary"/);
  assert.match(teacher, /teacher-glossary/);
  assert.doesNotMatch(evidence, /class="ui-glossary"/);
  assert.match(source("evidence/evidence-messages.mjs"), /Query unavailable/);
  assert.doesNotMatch(evidence, /QUERY ERROR/);
});

test("shared primitive layer preserves canvas separation and canonical density modes", () => {
  const tokens = source("visual-tokens.css");
  const components = source("components.css");
  const settings = source("settings.mjs");
  assert.match(components, /\.ui-canvas\s*\{[^}]*background:\s*var\(--canvas\)/s);
  assert.match(components, /\.ui-surface-1\s*\{[^}]*background:\s*var\(--surface-1\)/s);
  assert.match(components, /\.ui-surface-2\s*\{[^}]*background:\s*var\(--surface-2\)/s);
  assert.match(components, /\.ui-surface-3\s*\{[^}]*background:\s*var\(--surface-3\)/s);
  assert.match(components, /\.ui-panel\s*\{/);
  assert.match(components, /\.ui-table-wrap\s*\{/);
  assert.match(components, /\.ui-disclosure\s*\{/);
  assert.match(components, /\.ui-state--error\s*\{/);
  assert.match(components, /\.ui-control--mode\s*\{/);
  assert.match(components, /\.ui-control--peer-tab\s*\{/);
  assert.match(components, /\.ui-control--secondary\s*\{/);
  assert.match(components, /\.ui-control--tertiary\s*\{/);
  assert.match(components, /\.ui-control--destructive\s*\{/);
  assert.match(components, /\.ui-control--link\s*\{/);
  assert.match(components, /\.ui-control--read-only\s*\{/);
  assert.match(components, /\.ui-control--navigate\s*\{[^}]*border-inline-start/s);
  assert.match(components, /\.ui-control--export\s*\{[^}]*text-decoration/s);
  assert.match(components, /\.ui-control--compare\s*\{[^}]*double/s);
  assert.match(components, /\.ui-control--mode\s*\{[^}]*box-shadow/s);
  assert.match(components, /\.metric-tile \.evidence-value \.value,[\s\S]*\.comparison-card \.evidence-value \.value\s*\{[^}]*var\(--type-metric\)/);
  assert.match(components, /\.ui-control--read-only[^\n]*:hover\s*\{[^}]*var\(--surface-2\)/s);
  assert.match(components, /aria-pressed="true"/);
  assert.match(components, /data-align="numeric"/);
  assert.match(components, /forced-colors:\s*active/);
  assert.match(settings, /\["comfortable",\s*"compact"\]/);
  assert.doesNotMatch(tokens, /data-density="terminal"/);
});

test("domain CSS cannot invent additional rendered text sizes", () => {
  const cssFiles = [];
  const visit = (dir) => {
    for (const entry of fs.readdirSync(dir, { withFileTypes: true })) {
      const full = path.join(dir, entry.name);
      if (entry.isDirectory()) visit(full);
      else if (entry.name.endsWith(".css")) cssFiles.push(full);
    }
  };
  visit(rendererRoot);
  for (const file of cssFiles) {
    let css = fs.readFileSync(file, "utf8");
    if (path.basename(file) === "shell.css") {
      css = css
        .replace(/#inspector-close[^}]*\}/g, "")
        .replace(/\.palette-heading button[^}]*\}/g, "")
        .replace(/\.brand div, #primary-nav button, \.utility-button span[^}]*\}/g, "")
        .replace(/#primary-nav button::first-letter[^}]*\}/g, "");
    }
    assert.doesNotMatch(
      css,
      /font-size:\s*(?:\d|\.\d|clamp\()/,
      path.relative(rendererRoot, file) + " introduces a literal text size",
    );
  }
});

test("legacy domain styles resolve through the active visual token surface", () => {
  const tokens = source("visual-tokens.css");
  for (const token of [
    "--surface", "--surface-raised", "--line", "--line-strong", "--text-xs", "--font-mono",
  ]) assert.match(tokens, new RegExp(token.replace("--", "--") + ":"));
});
