"use strict";

const FORBIDDEN_RENDERER_PATTERNS = Object.freeze([
  [/(^|[^\w])require\s*\(/m, "COMMONJS_REQUIRE"],
  [/\bfrom\s+["']electron["']/m, "ELECTRON_IMPORT"],
  [/\bimport\s*\(\s*["']electron["']\s*\)/m, "ELECTRON_DYNAMIC_IMPORT"],
  [/\bfrom\s+["'](?:node:)?fs(?:\/[^"']*)?["']/m, "FILESYSTEM_IMPORT"],
  [/\bimport\s*\(\s*["'](?:node:)?fs(?:\/[^"']*)?["']\s*\)/m, "FILESYSTEM_DYNAMIC_IMPORT"],
  [/\bfrom\s+["'](?:node:)?child_process["']/m, "PROCESS_IMPORT"],
  [/\bimport\s*\(\s*["'](?:node:)?child_process["']\s*\)/m, "PROCESS_DYNAMIC_IMPORT"],
  [/\bprocess\s*\.(?:env|cwd|chdir|kill|exit|binding|mainModule)\b/m, "PROCESS_GLOBAL"],
]);

function assertRendererSourceSafe(source, label = "renderer") {
  if (typeof source !== "string") {
    throw new TypeError("BAMF_GUI20_RENDERER_SOURCE_REQUIRED");
  }
  for (const [pattern, reason] of FORBIDDEN_RENDERER_PATTERNS) {
    if (pattern.test(source)) {
      const error = new Error(`BAMF_GUI20_RENDERER_PRIVILEGE_IMPORT:${reason}:${label}`);
      error.code = "BAMF_GUI20_RENDERER_PRIVILEGE_IMPORT";
      throw error;
    }
  }
  return true;
}

module.exports = { FORBIDDEN_RENDERER_PATTERNS, assertRendererSourceSafe };
