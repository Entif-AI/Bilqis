"use strict";

const fs = require("node:fs");
const path = require("node:path");
const vm = require("node:vm");

const PRELOAD = path.join(__dirname, "..", "preload.cjs");

function loadSandboxedPreload(ipcRenderer, argv = []) {
  const source = fs.readFileSync(PRELOAD, "utf8");
  let exposed;
  const contextBridge = {
    exposeInMainWorld(name, api) {
      exposed = { name, api };
    },
  };
  const context = vm.createContext({
    process: Object.freeze({ argv: Object.freeze([...argv]) }),
    require(specifier) {
      if (specifier !== "electron") {
        throw new Error(`SANDBOX_PRELOAD_REQUIRE_DENIED:${specifier}`);
      }
      return { contextBridge, ipcRenderer };
    },
  });
  vm.runInContext(source, context, { filename: PRELOAD });
  return exposed;
}

module.exports = { loadSandboxedPreload };
