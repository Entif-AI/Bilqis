"use strict";

const LAUNCH_MODE_PRODUCTION = "production";
const LAUNCH_MODE_FIXTURES = "fixtures";
const FIXTURE_LAUNCH_FLAG = "--mission-control-fixtures";
const PRELOAD_MODE_PREFIX = "--bilqis-mission-control-mode=";

function normalizeLaunchMode(value) {
  return value === LAUNCH_MODE_FIXTURES
    ? LAUNCH_MODE_FIXTURES
    : LAUNCH_MODE_PRODUCTION;
}

function resolveLaunchMode(argv = []) {
  return Array.isArray(argv) && argv.includes(FIXTURE_LAUNCH_FLAG)
    ? LAUNCH_MODE_FIXTURES
    : LAUNCH_MODE_PRODUCTION;
}

function preloadModeArgument(mode) {
  return PRELOAD_MODE_PREFIX + normalizeLaunchMode(mode);
}

module.exports = {
  FIXTURE_LAUNCH_FLAG,
  LAUNCH_MODE_FIXTURES,
  LAUNCH_MODE_PRODUCTION,
  PRELOAD_MODE_PREFIX,
  normalizeLaunchMode,
  preloadModeArgument,
  resolveLaunchMode,
};
