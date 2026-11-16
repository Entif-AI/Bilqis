import test from "node:test";
import assert from "node:assert/strict";
import fs from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";

const ROOT = path.resolve(path.dirname(fileURLToPath(import.meta.url)), "../..", "renderer");

function sources(dir) {
  return fs.readdirSync(dir, { withFileTypes: true }).flatMap((entry) => {
    const target = path.join(dir, entry.name);
    return entry.isDirectory() ? sources(target) : entry.name.endsWith(".mjs") ? [target] : [];
  });
}

test("only the Operate controller can invoke renderer command submission surfaces", () => {
  const offenders = sources(ROOT).filter((file) => {
    if (file.endsWith(path.join("operate", "operate-controller.mjs"))) return false;
    return /\.requestCommand\s*\(|\.requestDryRun\s*\(|\.fetchReceipt\s*\(/.test(fs.readFileSync(file, "utf8"));
  });
  assert.deepEqual(offenders, []);
});

test("long command identities remain contained inside the shared inspector", () => {
  const css = fs.readFileSync(path.join(ROOT, "shell.css"), "utf8");
  assert.match(css, /\.inspector-heading > div \{ min-width: 0; \}/);
  assert.match(css, /\.inspector h2 \{[^}]*overflow-wrap: anywhere;/);
  assert.match(css, /\.inspector-heading > button \{ flex: 0 0 auto; \}/);
});
