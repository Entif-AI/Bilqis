export const RAIL_STATES = Object.freeze(["expanded", "collapsed"]);

const RAIL_STORAGE_KEY = "bilqis.mc.rail";

function railState(value) {
  return RAIL_STATES.includes(value) ? value : "expanded";
}

export function loadShellPreferences(storage) {
  return Object.freeze({ rail: railState(storage?.getItem(RAIL_STORAGE_KEY)) });
}

export function saveShellPreferences(storage, preferences) {
  storage?.setItem(RAIL_STORAGE_KEY, railState(preferences?.rail));
}

export function toggleRailPreference(preferences) {
  return Object.freeze({
    rail: railState(preferences?.rail) === "expanded" ? "collapsed" : "expanded",
  });
}

export function applyShellPreferences(root, preferences) {
  root.dataset.rail = railState(preferences?.rail);
}
