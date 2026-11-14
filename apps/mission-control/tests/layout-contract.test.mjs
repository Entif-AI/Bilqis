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
  assert.match(shell, /\.view-host h1\s*\{[^}]*clamp\(30px, 2\.6vw, 42px\)/s);

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

  for (const token of [
    "--text-sm", "--text-md", "--text-lg", "--heading-sm", "--heading-md", "--heading-lg",
  ]) assert.match(tokens, new RegExp(token + ":"));
  assert.match(shell, /\.ui-glossary\s*\{/);
  for (const markup of [school, teacher, salience, corrections, evidence]) {
    assert.match(markup, /class="ui-glossary"/);
  }
  assert.match(evidence, /QUERY UNAVAILABLE/);
  assert.doesNotMatch(evidence, /QUERY ERROR/);
});

test("legacy domain styles resolve through the active visual token surface", () => {
  const tokens = source("visual-tokens.css");
  for (const token of [
    "--surface", "--surface-raised", "--line", "--line-strong", "--text-xs", "--font-mono",
  ]) assert.match(tokens, new RegExp(token.replace("--", "--") + ":"));
});
