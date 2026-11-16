"use strict";

const {
  RENDERER_ENTRY_URL,
  RENDERER_ORIGIN,
  normalizedRendererDocument,
} = require("./renderer-location.cjs");

function createTrustedSender(trustedWebContents) {
  if (!trustedWebContents || !Number.isInteger(trustedWebContents.id) ||
      !trustedWebContents.mainFrame) {
    throw new TypeError("BAMF_GUI20_TRUSTED_WEB_CONTENTS_REQUIRED");
  }
  return (event) => {
    const frame = event?.senderFrame;
    return event?.sender === trustedWebContents &&
      frame === trustedWebContents.mainFrame &&
      frame?.top === frame &&
      frame?.origin === RENDERER_ORIGIN &&
      normalizedRendererDocument(frame?.url) === RENDERER_ENTRY_URL;
  };
}

function requireTrustedSender(isTrustedSender, event) {
  if (!isTrustedSender(event)) {
    const error = new Error("BAMF_GUI20_UNTRUSTED_IPC_SENDER");
    error.code = "BAMF_GUI20_UNTRUSTED_IPC_SENDER";
    throw error;
  }
}

module.exports = {
  createTrustedSender,
  requireTrustedSender,
};
