"use strict";

const test = require("node:test");
const assert = require("node:assert/strict");
const fs = require("node:fs");
const path = require("node:path");

const {
  LAUNCH_MODE_FIXTURES,
  LAUNCH_MODE_PRODUCTION,
  normalizeLaunchMode,
  preloadModeArgument,
  resolveLaunchMode,
} = require("../../shell/launch-mode.cjs");

test("Admin Main Frame launch mode defaults closed to production", () => {
  assert.equal(resolveLaunchMode([]), LAUNCH_MODE_PRODUCTION);
  assert.equal(resolveLaunchMode(["electron", "main.cjs"]), LAUNCH_MODE_PRODUCTION);
  assert.equal(resolveLaunchMode(["--mission-control-fixture"]), LAUNCH_MODE_PRODUCTION);
  assert.equal(normalizeLaunchMode(undefined), LAUNCH_MODE_PRODUCTION);
  assert.equal(normalizeLaunchMode("anything-else"), LAUNCH_MODE_PRODUCTION);
});

test("fixture mode requires the exact launch-time flag", () => {
  assert.equal(
    resolveLaunchMode(["electron", "main.cjs", "--mission-control-fixtures"]),
    LAUNCH_MODE_FIXTURES,
  );
  assert.equal(preloadModeArgument(LAUNCH_MODE_FIXTURES),
    "--bilqis-mission-control-mode=fixtures");
  assert.equal(preloadModeArgument("unexpected"),
    "--bilqis-mission-control-mode=production");
});

test("package scripts expose distinct production and fixture launch commands", () => {
  const pkg = JSON.parse(fs.readFileSync(path.resolve(__dirname, "../../../../../package.json"), "utf8"));
  assert.equal(pkg.scripts["mission-control"], "electron apps/mission-control/main.cjs");
  assert.equal(
    pkg.scripts["mission-control:fixtures"],
    "electron apps/mission-control/main.cjs --mission-control-fixtures",
  );
});

test("main process owns launch mode for adapter, window, and renderer protocol", () => {
  const main = fs.readFileSync(path.resolve(__dirname, "../../../main.cjs"), "utf8");
  assert.match(main, /resolveLaunchMode\(process\.argv\)/);
  assert.match(main, /launchMode === LAUNCH_MODE_FIXTURES[\s\S]*FixtureControlPlaneAdapter/);
  assert.match(main, /createMissionControlWindow\(\{[\s\S]*launchMode,/);
  assert.match(main, /registerMissionControlProtocol\(\{[\s\S]*launchMode,/);
});
