"use strict";

const test = require("node:test");
const assert = require("node:assert/strict");

const {
  appUriArgument,
  rendererHashForAppUri,
} = require("../shell/app-routing.cjs");
const {
  RENDERER_ENTRY_URL,
  rendererEntryUrl,
} = require("../shell/renderer-location.cjs");

test("app URI argument detection ignores unrelated command-line values", () => {
  assert.equal(
    appUriArgument(["electron", ".", "--trace", "bilqis://run/r/generation/7/capability/B.AND"]),
    "bilqis://run/r/generation/7/capability/B.AND",
  );
  assert.equal(appUriArgument(["electron", ".", "https://example.test/"]), null);
});

test("validated app URI becomes an exact trusted renderer hash", async () => {
  const hash = await rendererHashForAppUri(
    "bilqis://run/run%3Aalpha/generation/7/capability/B.AND",
  );
  assert.equal(
    hash,
    "#/view/capability?kind=capability&id=B.AND&run=run%3Aalpha&generation=7&mode=HISTORICAL",
  );
  assert.equal(
    rendererEntryUrl(hash),
    RENDERER_ENTRY_URL + "#/view/capability?kind=capability&id=B.AND&run=run%3Aalpha&generation=7&mode=HISTORICAL",
  );
});

test("invalid external URI cannot produce a renderer destination", async () => {
  assert.equal(await rendererHashForAppUri("https://evil.example/"), null);
  assert.throws(
    () => rendererEntryUrl("https://evil.example/"),
    /BAMF_GUI18_RENDERER_HASH_INVALID/,
  );
  assert.throws(
    () => rendererEntryUrl("#/other/route"),
    /BAMF_GUI18_RENDERER_HASH_INVALID/,
  );
});
