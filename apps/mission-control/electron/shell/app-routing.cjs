"use strict";

function appUriArgument(argv = []) {
  return Array.isArray(argv)
    ? argv.find((value) => typeof value === "string" && value.startsWith("bilqis://")) ?? null
    : null;
}

async function rendererHashForAppUri(raw, {
  loadAppUriModule = () => import("../../renderer/interactions/app-uri.mjs"),
} = {}) {
  const module = await loadAppUriModule();
  return module.appUriToHash(raw);
}

module.exports = {
  appUriArgument,
  rendererHashForAppUri,
};
