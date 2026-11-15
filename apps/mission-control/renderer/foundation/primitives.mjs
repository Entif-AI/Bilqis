import { testIdAttribute } from "./test-hooks.mjs";

export const SURFACE_LEVELS = Object.freeze(["canvas", "surface-1", "surface-2", "surface-3"]);
export const CONTROL_ROLES = Object.freeze([
  "navigate", "filter", "group", "compare", "export", "inspect", "primary", "mutate", "status",
  "mode", "peer-tab", "secondary", "tertiary", "destructive", "link", "read-only",
]);

function enumValue(value, allowed, label) {
  if (!allowed.includes(value)) throw new TypeError(`${label}:${value}`);
  return value;
}

export function surfaceClass(level = "surface-1", { bounded = false } = {}) {
  enumValue(level, SURFACE_LEVELS, "SURFACE_LEVEL_INVALID");
  if (level === "canvas" && bounded) throw new TypeError("CANVAS_SURFACE_CANNOT_BE_BOUNDED");
  return `ui-surface ui-${level}${bounded ? " ui-surface--bounded" : ""}`;
}

export function controlClass(role = "inspect") {
  enumValue(role, CONTROL_ROLES, "CONTROL_ROLE_INVALID");
  return `ui-control ui-control--${role}`;
}

export function panelMarkup({ title, body, testId: id, level = "surface-1", bounded = false, classes = "" }) {
  return `<section class="${surfaceClass(level, { bounded })} ui-panel${classes ? ` ${classes}` : ""}" ${testIdAttribute(id)}><h3>${title}</h3>${body}</section>`;
}

export function disclosureMarkup({ summary, body, testId: id }) {
  return `<details class="ui-disclosure" ${testIdAttribute(id)}><summary>${summary}</summary><div class="ui-disclosure__body">${body}</div></details>`;
}

export function stateMarkup({ title, detail, testId: id, kind = "empty" }) {
  if (!["empty", "error"].includes(kind)) throw new TypeError(`STATE_PRIMITIVE_INVALID:${kind}`);
  return `<div class="ui-state ui-state--${kind}" ${testIdAttribute(id)} role="${kind === "error" ? "alert" : "status"}"><strong>${title}</strong>${detail ? `<span>${detail}</span>` : ""}</div>`;
}
