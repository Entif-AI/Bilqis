"use strict";

const test = require("node:test");
const assert = require("node:assert/strict");

const { assertRendererSourceSafe } = require("../renderer-boundary.cjs");

test("renderer source guard accepts bridge-only application code", () => {
  const source = `
    const status = await window.bamfMissionControl.status();
    document.querySelector("#status").textContent = status.state;
  `;
  assert.equal(assertRendererSourceSafe(source, "safe.js"), true);
});

test("renderer source guard rejects Electron, filesystem, process and require escapes", () => {
  const hostile = [
    ["const fs = require('fs')", "COMMONJS_REQUIRE"],
    ["import { ipcRenderer } from 'electron'", "ELECTRON_IMPORT"],
    ["import fs from 'node:fs'", "FILESYSTEM_IMPORT"],
    ["import { exec } from 'child_process'", "PROCESS_IMPORT"],
    ["const cwd = process.cwd()", "PROCESS_GLOBAL"],
  ];

  for (const [source, reason] of hostile) {
    assert.throws(
      () => assertRendererSourceSafe(source, "hostile.js"),
      new RegExp(`BAMF_GUI20_RENDERER_PRIVILEGE_IMPORT:${reason}`),
    );
  }
});
