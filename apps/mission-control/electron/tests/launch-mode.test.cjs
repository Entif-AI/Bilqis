"use strict";

const test = require("node:test");
const assert = require("node:assert/strict");

const {
  FIXTURES,
  PRODUCTION,
  launchModeArgument,
  launchModeFromArguments,
  resolveMissionControlMode,
} = require("../launch-mode.cjs");

test("Mission Control defaults to production and admits only explicit fixture mode", () => {
  assert.equal(resolveMissionControlMode(), PRODUCTION);
  assert.equal(resolveMissionControlMode(""), PRODUCTION);
  assert.equal(resolveMissionControlMode(PRODUCTION), PRODUCTION);
  assert.equal(resolveMissionControlMode(FIXTURES), FIXTURES);
  assert.throws(() => resolveMissionControlMode("demo"), /BAMF_MISSION_CONTROL_MODE_INVALID/);
});

test("renderer launch argument preserves one exact startup mode", () => {
  assert.equal(launchModeArgument(PRODUCTION), "--bamf-mc-mode=production");
  assert.equal(launchModeArgument(FIXTURES), "--bamf-mc-mode=fixtures");
  assert.equal(launchModeFromArguments(["electron"]), PRODUCTION);
  assert.equal(
    launchModeFromArguments(["electron", "--bamf-mc-mode=fixtures"]),
    FIXTURES,
  );
  assert.throws(
    () => launchModeFromArguments([
      "--bamf-mc-mode=production",
      "--bamf-mc-mode=fixtures",
    ]),
    /BAMF_MISSION_CONTROL_MODE_AMBIGUOUS/,
  );
});
