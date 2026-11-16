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

function esc(value) {
  return String(value).replace(/[&<>"']/g, character => ({
    "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;",
  })[character]);
}

function docsMarkup(docs) {
  if (docs === null || docs === undefined) return "";
  if (!docs || typeof docs !== "object" ||
      typeof docs.href !== "string" ||
      !docs.href.startsWith("https://github.com/") ||
      typeof docs.label !== "string" ||
      docs.label.length === 0) {
    throw new TypeError("CONTEXT_HELP_DOCS_URL_INVALID");
  }
  return `<span class="ui-context-help__docs" data-docs-slot="project-github" data-docs-href="${esc(docs.href)}">${esc(docs.label)}</span>`;
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

export function contextHelpMarkup({ label, description, testId: id, docs = null }) {
  if (!label || !description) throw new TypeError("CONTEXT_HELP_COPY_REQUIRED");
  const detailId = `${id}-content`;
  return `<span class="ui-context-help" ${testIdAttribute(id)}><button type="button" class="ui-context-help__trigger" aria-label="${esc(label)}" aria-describedby="${detailId}" ${testIdAttribute(id, "trigger")}><span aria-hidden="true">?</span></button><span id="${detailId}" class="ui-context-help__content" role="tooltip" popover="manual" ${testIdAttribute(id, "content")}><span>${esc(description)}</span>${docsMarkup(docs)}</span></span>`;
}
