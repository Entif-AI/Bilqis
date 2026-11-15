"use strict";

const PRODUCTION = "production";
const FIXTURES = "fixtures";
const ARGUMENT_PREFIX = "--bamf-mc-mode=";
const MODES = Object.freeze(new Set([PRODUCTION, FIXTURES]));

function resolveMissionControlMode(raw = undefined) {
  const mode = raw === undefined || raw === "" ? PRODUCTION : String(raw);
  if (!MODES.has(mode)) {
    throw new TypeError("BAMF_MISSION_CONTROL_MODE_INVALID");
  }
  return mode;
}

function launchModeArgument(mode) {
  return ARGUMENT_PREFIX + resolveMissionControlMode(mode);
}

function launchModeFromArguments(argv = []) {
  const values = argv
    .filter((value) => typeof value === "string" && value.startsWith(ARGUMENT_PREFIX))
    .map((value) => value.slice(ARGUMENT_PREFIX.length));
  if (values.length === 0) return PRODUCTION;
  if (values.length !== 1) throw new TypeError("BAMF_MISSION_CONTROL_MODE_AMBIGUOUS");
  return resolveMissionControlMode(values[0]);
}

module.exports = {
  ARGUMENT_PREFIX,
  FIXTURES,
  PRODUCTION,
  launchModeArgument,
  launchModeFromArguments,
  resolveMissionControlMode,
};
