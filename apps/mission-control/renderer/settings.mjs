export const THEMES = Object.freeze(["dark", "light"]);
export const DENSITIES = Object.freeze(["comfortable", "compact"]);

const LEGACY_DENSITY_ALIASES = Object.freeze({ terminal: "compact" });

function allowed(value, choices, fallback) {
  return choices.includes(value) ? value : fallback;
}

function density(value) {
  return allowed(LEGACY_DENSITY_ALIASES[value] ?? value, DENSITIES, "comfortable");
}

export function loadDisplaySettings(storage) {
  return {
    theme: allowed(storage?.getItem("bilqis.mc.theme"), THEMES, "dark"),
    density: density(storage?.getItem("bilqis.mc.density")),
  };
}

export function saveDisplaySettings(storage, settings) {
  storage?.setItem("bilqis.mc.theme", allowed(settings.theme, THEMES, "dark"));
  storage?.setItem("bilqis.mc.density", density(settings.density));
}

export function cycleSetting(value, choices) {
  const index = choices.indexOf(value);
  return choices[(index + 1 + choices.length) % choices.length];
}

export function applyDisplaySettings(root, settings) {
  root.dataset.theme = allowed(settings.theme, THEMES, "dark");
  root.dataset.density = density(settings.density);
}
