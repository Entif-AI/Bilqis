import test from "node:test";
import assert from "node:assert/strict";
import fs from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";

const here = path.dirname(fileURLToPath(import.meta.url));
const rendererRoot = path.resolve(here, "../renderer");
const source = (name) => fs.readFileSync(path.join(rendererRoot, name), "utf8");

test("shared shell owns stable rail and dense page geometry", () => {
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
  assert.match(shell, /\.view-host h1\s*\{[^}]*font-size:\s*var\(--type-display\)/s);

  assert.doesNotMatch(home, /grid-template-columns:\s*176px/);
  assert.doesNotMatch(dossier, /^\.context-bar\s*\{/m);
  assert.doesNotMatch(dossier, /^\.context-actions\s*\{/m);
  assert.doesNotMatch(frames, /^\s*\.context-bar\s*\{/m);
  assert.doesNotMatch(frames, /^\s*\.context-actions\s*\{/m);
});

test("dense values and wide School data stay inside their owning surfaces", () => {
  const home = source("home/home.css");
  const school = source("school/school.css");
  const teacher = source("teacher/teacher.css");

  assert.match(home, /grid-template-columns:minmax\(0,1fr\) max-content/);
  assert.match(home, /\.home-metric-card dd[^}]*white-space:nowrap/s);
  assert.match(school, /\.school-panel\s*\{[^}]*min-width:\s*0[^}]*overflow:\s*hidden/s);
  assert.match(school, /\.matrix-scroll\s*\{[^}]*min-width:\s*0[^}]*width:\s*100%[^}]*overflow:\s*auto/s);
  assert.match(teacher, /\.strategy-card\s*\{[^}]*min-width:\s*0[^}]*overflow:\s*hidden/s);
  assert.match(teacher, /\.strategy-roster\s*\{[^}]*repeat\(2, minmax\(0, 1fr\)\)/s);
  assert.match(teacher, /\.strategy-metrics\s*\{[^}]*repeat\(2, minmax\(0, 1fr\)\)/s);
});

test("operator typography and explanatory surfaces use the shared visual language", () => {
  const tokens = source("visual-tokens.css");
  const shell = source("shell.css");
  const school = source("school/school-view.mjs");
  const teacher = source("teacher/teacher-view.mjs");
  const salience = source("salience/salience-view.mjs");
  const corrections = source("corrections/corrections-view.mjs");
  const evidence = source("evidence/evidence-markup.mjs");

  for (const [token, value] of [
    ["--type-label", "11px"], ["--type-body", "14px"],
    ["--type-section", "18px"], ["--type-display", "28px"],
  ]) assert.match(tokens, new RegExp(token + ":\\s*" + value));
  assert.match(shell, /\.context-bar\[data-context="empty"\][^}]*grid-template-columns:\s*minmax\(300px, 1fr\) auto/s);
  assert.match(shell, /\.context-actions\s*\{[^}]*flex-wrap:\s*nowrap[^}]*align-items:\s*flex-end/s);
  assert.match(shell, /\.context-facts\[hidden\]\s*\{\s*display:\s*none/s);
  assert.match(shell, /\.ui-glossary\s*\{/);
  for (const markup of [school, teacher, salience, corrections, evidence]) {
    assert.match(markup, /class="ui-glossary"/);
  }
  assert.match(evidence, /QUERY UNAVAILABLE/);
  assert.doesNotMatch(evidence, /QUERY ERROR/);
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
