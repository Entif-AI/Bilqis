import fs from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";

const here = path.dirname(fileURLToPath(import.meta.url));
const rendererRoot = path.resolve(here, "../renderer");
const entry = path.join(rendererRoot, "renderer.mjs");
const fixtureName = /(?:^|[-_.])fixture(?:s)?(?:[-_.]|$)/i;

function staticImports(source) {
  const imports = [];
  const pattern = /(?:^|\n)\s*import\s+(?:[^"'()]*?\s+from\s+)?["']([^"']+)["']/g;
  for (const match of source.matchAll(pattern)) imports.push(match[1]);
  return imports;
}

function resolveLocal(owner, specifier) {
  if (!specifier.startsWith(".")) return null;
  const resolved = path.resolve(path.dirname(owner), specifier);
  return fs.existsSync(resolved) && fs.statSync(resolved).isFile() ? resolved : null;
}

function relative(file) {
  return path.relative(rendererRoot, file).split(path.sep).join("/");
}

function isFixtureModule(file) {
  return relative(file).split("/").some((part) => fixtureName.test(part));
}

function productionGraph() {
  const queue = [entry];
  const visited = new Set();
  const edges = [];
  while (queue.length) {
    const file = queue.shift();
    if (visited.has(file)) continue;
    visited.add(file);
    const source = fs.readFileSync(file, "utf8");
    for (const specifier of staticImports(source)) {
      const target = resolveLocal(file, specifier);
      if (!target) continue;
      edges.push([file, target]);
      if (!visited.has(target)) queue.push(target);
    }
  }
  return { visited, edges };
}

const { visited, edges } = productionGraph();
const violations = [...visited].filter(isFixtureModule).sort();
if (violations.length) {
  for (const file of violations) {
    const incoming = edges
      .filter(([, target]) => target === file)
      .map(([owner]) => relative(owner))
      .sort();
    console.error(`PRODUCTION_FIXTURE_IMPORT ${relative(file)} <- ${incoming.join(", ")}`);
  }
  console.error(`MISSION_CONTROL_PRODUCTION_IMPORT_BOUNDARY_FAIL violations=${violations.length}`);
  process.exitCode = 1;
} else {
  console.log(`MISSION_CONTROL_PRODUCTION_IMPORT_BOUNDARY_OK modules=${visited.size}`);
}
