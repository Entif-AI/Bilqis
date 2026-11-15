import test from "node:test";
import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import {
  CACHED_OPERATOR_VIEW_KEY,
  cacheOperatorView,
  defensiveBannerMarkup,
  defensiveState,
  defensiveStateForConnection,
  defensiveStateForError,
  defensiveStateIds,
  loadCachedOperatorView,
} from "../renderer/foundation/defensive-state.mjs";
import {
  createShellState,
  inspect,
  navigate,
  withDefensiveState,
} from "../renderer/shell-state.mjs";

const context = JSON.parse(
  readFileSync(new URL("../fixtures/operator-view-v1.json", import.meta.url), "utf8"),
);

function fakeStorage() {
  const values = new Map();
  return {
    getItem: (key) => values.get(key) ?? null,
    setItem: (key, value) => values.set(key, value),
    values,
  };
}

test("GUI19 defensive vocabulary covers every required distinct failure posture", () => {
  assert.deepEqual(defensiveStateIds(), [
    "loading", "progressive", "empty", "stale", "partial", "offline", "denied",
    "revoked", "unavailable", "incompatible-version", "timeout", "duplicate-action",
    "session-restarting", "service-restarting", "historical-unavailable",
    "malformed-payload", "unsupported-payload", "outcome-unknown",
  ]);
  const labels = new Map(defensiveStateIds().map((id) => [id, defensiveState(id).label]));
  assert.notEqual(labels.get("denied"), labels.get("revoked"));
  assert.notEqual(labels.get("unavailable"), labels.get("empty"));
  assert.notEqual(labels.get("outcome-unknown"), labels.get("timeout"));
});

test("only a verified live snapshot can expose mutation", () => {
  const live = defensiveStateForConnection("healthy", {
    snapshotAvailable: true,
    snapshotSource: "service",
  });
  assert.equal(live.mutationAllowed, true);
  assert.equal(live.historical, false);
  for (const state of [
    "stale", "disconnected", "service-restarting", "incompatible-version",
    "unauthorized", "timeout", "unavailable",
  ]) {
    const profile = defensiveStateForConnection(state, {
      snapshotAvailable: true,
      snapshotSource: "service",
    });
    assert.equal(profile.mutationAllowed, false, state);
    assert.equal(profile.historical, true, state);
  }
});

test("offline and restart transitions preserve investigation context without pretending live", () => {
  const selected = inspect(navigate(createShellState(context), "school"), {
    kind: "capability",
    id: "B.AND",
  });
  const offline = withDefensiveState(selected, defensiveStateForConnection("disconnected", {
    snapshotAvailable: true,
    snapshotSource: "cache",
  }));
  assert.equal(offline.view, "school");
  assert.deepEqual(offline.selected, selected.selected);
  assert.equal(offline.context.mode, "HISTORICAL");
  assert.equal(offline.context.freshness, "DISCONNECTED");
  assert.equal(offline.mutationAvailable, false);

  const restarted = withDefensiveState(offline, defensiveStateForConnection("healthy", {
    snapshotAvailable: true,
    snapshotSource: "service",
  }));
  assert.equal(restarted.view, "school");
  assert.deepEqual(restarted.selected, selected.selected);
  assert.equal(restarted.context.mode, "LIVE");
  assert.equal(restarted.mutationAvailable, true);
});

test("cached verified snapshot is bounded UI evidence and malformed cache fails closed", () => {
  const storage = fakeStorage();
  cacheOperatorView(storage, context, 123);
  assert.equal(storage.values.has(CACHED_OPERATOR_VIEW_KEY), true);
  assert.deepEqual(loadCachedOperatorView(storage), { cachedAt: 123, operatorView: context });

  storage.setItem(CACHED_OPERATOR_VIEW_KEY, "{bad json");
  assert.equal(loadCachedOperatorView(storage), null);
  storage.setItem(CACHED_OPERATOR_VIEW_KEY, JSON.stringify({ schema: "wrong", cachedAt: 123, operatorView: context }));
  assert.equal(loadCachedOperatorView(storage), null);
});

test("defensive banner exposes inspection and mutation posture in text, not color alone", () => {
  const offline = defensiveState("offline", { snapshotAvailable: true, snapshotSource: "cache" });
  const html = defensiveBannerMarkup(offline);
  assert.match(html, /Offline/);
  assert.match(html, /Cached verified snapshot/);
  assert.match(html, /Mutation unavailable/);
  assert.match(html, /data-reconnect/);
  assert.match(html, /data-test-id="foundation-reconnect"/);
});

test("renderer-facing contract errors classify malformed and unsupported payloads distinctly", () => {
  assert.equal(
    defensiveStateForError(new TypeError("MISSION_CONTROL_OPERATOR_VIEW_INVALID:run"), { snapshotAvailable: true }).id,
    "malformed-payload",
  );
  assert.equal(
    defensiveStateForError(new TypeError("MISSION_CONTROL_OPERATOR_VIEW_SCHEMA_UNSUPPORTED"), { snapshotAvailable: true }).id,
    "unsupported-payload",
  );
});
