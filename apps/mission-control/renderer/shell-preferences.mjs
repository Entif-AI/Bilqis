export const RAIL_STATES = Object.freeze(["expanded", "collapsed"]);
export const INSPECTOR_MIN_WIDTH = 160;
export const INSPECTOR_DEFAULT_WIDTH = 360;
export const INSPECTOR_PRIMARY_MIN_WIDTH = 480;
export const INSPECTOR_SPLITTER_WIDTH = 8;

const RAIL_STORAGE_KEY = "bilqis.mc.rail";
const INSPECTOR_STORAGE_KEY = "bilqis.mc.inspectorWidths";

function railState(value) {
  return RAIL_STATES.includes(value) ? value : "expanded";
}

function inspectorWidths(value) {
  if (!value || typeof value !== "object" || Array.isArray(value)) return Object.freeze({});
  return Object.freeze(Object.fromEntries(Object.entries(value).filter(([destination, width]) =>
    typeof destination === "string" && destination.length > 0 &&
    Number.isFinite(width) && width >= INSPECTOR_MIN_WIDTH,
  )));
}

function parseInspectorWidths(raw) {
  if (typeof raw !== "string" || raw.length === 0) return Object.freeze({});
  try {
    return inspectorWidths(JSON.parse(raw));
  } catch {
    return Object.freeze({});
  }
}

export function loadShellPreferences(storage) {
  return Object.freeze({
    rail: railState(storage?.getItem(RAIL_STORAGE_KEY)),
    inspectorWidths: parseInspectorWidths(storage?.getItem(INSPECTOR_STORAGE_KEY)),
  });
}

export function saveShellPreferences(storage, preferences) {
  storage?.setItem(RAIL_STORAGE_KEY, railState(preferences?.rail));
  storage?.setItem(
    INSPECTOR_STORAGE_KEY,
    JSON.stringify(inspectorWidths(preferences?.inspectorWidths)),
  );
}

export function toggleRailPreference(preferences) {
  return Object.freeze({
    rail: railState(preferences?.rail) === "expanded" ? "collapsed" : "expanded",
    inspectorWidths: inspectorWidths(preferences?.inspectorWidths),
  });
}

export function applyShellPreferences(root, preferences) {
  root.dataset.rail = railState(preferences?.rail);
}

export function inspectorWidthForDestination(preferences, destination) {
  return inspectorWidths(preferences?.inspectorWidths)[destination] ?? INSPECTOR_DEFAULT_WIDTH;
}

export function constrainInspectorWidth(
  width,
  {
    viewportWidth = Number.POSITIVE_INFINITY,
    railWidth = 0,
    primaryMinWidth = INSPECTOR_PRIMARY_MIN_WIDTH,
    splitterWidth = INSPECTOR_SPLITTER_WIDTH,
  } = {},
) {
  const requested = Number.isFinite(width) ? width : INSPECTOR_DEFAULT_WIDTH;
  const finiteMaximum = Number.isFinite(viewportWidth)
    ? Math.max(
      INSPECTOR_MIN_WIDTH,
      Math.floor(viewportWidth - railWidth - primaryMinWidth - splitterWidth),
    )
    : Number.POSITIVE_INFINITY;
  return Math.min(Math.max(Math.round(requested), INSPECTOR_MIN_WIDTH), finiteMaximum);
}

export function withInspectorWidthPreference(preferences, destination, width) {
  if (typeof destination !== "string" || destination.length === 0) return preferences;
  return Object.freeze({
    rail: railState(preferences?.rail),
    inspectorWidths: inspectorWidths({
      ...preferences?.inspectorWidths,
      [destination]: Math.max(INSPECTOR_MIN_WIDTH, Math.round(width)),
    }),
  });
}
