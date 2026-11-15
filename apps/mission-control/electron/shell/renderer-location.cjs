"use strict";

const RENDERER_SCHEME = "bamf-mc";
const RENDERER_HOST = "app";
const RENDERER_ORIGIN = `${RENDERER_SCHEME}://${RENDERER_HOST}`;
const RENDERER_ENTRY_URL = `${RENDERER_ORIGIN}/index.html`;

const RENDERER_SCHEME_PRIVILEGES = Object.freeze({
  standard: true,
  secure: true,
  supportFetchAPI: true,
  codeCache: true,
});

function registerRendererSchemePrivileges(protocol) {
  if (!protocol || typeof protocol.registerSchemesAsPrivileged !== "function") {
    throw new TypeError("BAMF_GUI20_PROTOCOL_REQUIRED");
  }
  protocol.registerSchemesAsPrivileged([{
    scheme: RENDERER_SCHEME,
    privileges: { ...RENDERER_SCHEME_PRIVILEGES },
  }]);
}

function normalizedRendererDocument(raw) {
  if (typeof raw !== "string" || raw.length === 0) {
    return null;
  }
  try {
    const value = new URL(raw);
    if (value.protocol !== `${RENDERER_SCHEME}:` || value.hostname !== RENDERER_HOST ||
        value.username || value.password || value.port || value.search ||
        value.pathname !== "/index.html") {
      return null;
    }
    value.hash = "";
    return value.href;
  } catch (_error) {
    return null;
  }
}

function requireTrustedRendererUrl(raw) {
  const normalized = normalizedRendererDocument(raw);
  if (normalized === null) {
    const error = new Error("BAMF_GUI20_RENDERER_URL_UNTRUSTED");
    error.code = "BAMF_GUI20_RENDERER_URL_UNTRUSTED";
    throw error;
  }
  return normalized;
}

function rendererEntryUrl(hash = "") {
  if (hash === "") return RENDERER_ENTRY_URL;
  if (typeof hash !== "string" || hash.length > 8192 ||
      !hash.startsWith("#/view/") || hash.includes("\n")) {
    throw new TypeError("BAMF_GUI18_RENDERER_HASH_INVALID");
  }
  return RENDERER_ENTRY_URL + hash;
}

module.exports = {
  RENDERER_ENTRY_URL,
  RENDERER_HOST,
  RENDERER_ORIGIN,
  RENDERER_SCHEME,
  RENDERER_SCHEME_PRIVILEGES,
  normalizedRendererDocument,
  registerRendererSchemePrivileges,
  rendererEntryUrl,
  requireTrustedRendererUrl,
};
