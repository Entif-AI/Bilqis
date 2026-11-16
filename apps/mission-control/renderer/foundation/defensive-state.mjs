import { t } from "./i18n.mjs";
import { testIdAttribute } from "./test-hooks.mjs";

export const CACHED_OPERATOR_VIEW_KEY = "bilqis.mc.cached-operator-view/v1";
const CACHE_SCHEMA = "bilqis.mission-control.cached-operator-view/v1";

const profiles = {
  live: ["foundation.defensive.live.label", "foundation.defensive.live.description", "status", "FRESH", true, true],
  loading: ["foundation.defensive.loading.label", "foundation.defensive.loading.description", "status", "UNKNOWN", false, false],
  progressive: ["foundation.defensive.progressive.label", "foundation.defensive.progressive.description", "status", "UNKNOWN", false, true],
  empty: ["foundation.defensive.empty.label", "foundation.defensive.empty.description", "status", "FRESH", false, true],
  stale: ["foundation.defensive.stale.label", "foundation.defensive.stale.description", "status", "STALE", false, true],
  partial: ["foundation.defensive.partial.label", "foundation.defensive.partial.description", "status", "STALE", false, true],
  offline: ["foundation.defensive.offline.label", "foundation.defensive.offline.description", "alert", "DISCONNECTED", false, true],
  denied: ["foundation.defensive.denied.label", "foundation.defensive.denied.description", "alert", "DISCONNECTED", false, true],
  revoked: ["foundation.defensive.revoked.label", "foundation.defensive.revoked.description", "alert", "DISCONNECTED", false, true],
  unavailable: ["foundation.defensive.unavailable.label", "foundation.defensive.unavailable.description", "alert", "UNKNOWN", false, false],
  "incompatible-version": ["foundation.defensive.incompatibleVersion.label", "foundation.defensive.incompatibleVersion.description", "alert", "DISCONNECTED", false, true],
  timeout: ["foundation.defensive.timeout.label", "foundation.defensive.timeout.description", "alert", "STALE", false, true],
  "duplicate-action": ["foundation.defensive.duplicateAction.label", "foundation.defensive.duplicateAction.description", "alert", "FRESH", false, true],
  "session-restarting": ["foundation.defensive.sessionRestarting.label", "foundation.defensive.sessionRestarting.description", "status", "STALE", false, true],
  "service-restarting": ["foundation.defensive.serviceRestarting.label", "foundation.defensive.serviceRestarting.description", "status", "STALE", false, true],
  "historical-unavailable": ["foundation.defensive.historicalUnavailable.label", "foundation.defensive.historicalUnavailable.description", "alert", "UNKNOWN", false, true],
  "malformed-payload": ["foundation.defensive.malformedPayload.label", "foundation.defensive.malformedPayload.description", "alert", "UNKNOWN", false, true],
  "unsupported-payload": ["foundation.defensive.unsupportedPayload.label", "foundation.defensive.unsupportedPayload.description", "alert", "UNKNOWN", false, true],
  "outcome-unknown": ["foundation.defensive.outcomeUnknown.label", "foundation.defensive.outcomeUnknown.description", "alert", "STALE", false, true],
  unknown: ["foundation.defensive.unknown.label", "foundation.defensive.unknown.description", "status", "UNKNOWN", false, true],
};

function makeProfile(id, snapshotAvailable = false, snapshotSource = "none") {
  const raw = profiles[id] ?? profiles.unknown;
  const [labelKey, descriptionKey, role, freshness, mutationAllowed, inspectWhenSnapshot] = raw;
  const inspectionAllowed = snapshotAvailable && inspectWhenSnapshot;
  const historical = id !== "live" && snapshotAvailable;
  return Object.freeze({
    id,
    label: t(labelKey),
    description: t(descriptionKey),
    role,
    freshness,
    mutationAllowed: mutationAllowed && snapshotAvailable,
    inspectionAllowed,
    historical,
    snapshotAvailable,
    snapshotSource,
    reconnectAvailable: new Set([
      "offline", "stale", "timeout", "session-restarting", "service-restarting",
      "unavailable", "unknown",
    ]).has(id),
  });
}

export function defensiveState(id, options = {}) {
  return makeProfile(id, Boolean(options.snapshotAvailable), options.snapshotSource ?? "none");
}

export function defensiveStateForConnection(connectionState, options = {}) {
  const key = String(connectionState ?? "unknown").toLowerCase();
  const mapped = {
    healthy: "live",
    live: "live",
    stale: "stale",
    partial: "partial",
    disconnected: "offline",
    offline: "offline",
    unauthorized: "denied",
    denied: "denied",
    revoked: "revoked",
    "incompatible-version": "incompatible-version",
    timeout: "timeout",
    "session-restarting": "session-restarting",
    "service-restarting": "service-restarting",
    unavailable: "unavailable",
  }[key] ?? "unknown";
  return defensiveState(mapped, options);
}

export function defensiveStateForError(error, options = {}) {
  const text = `${error?.code ?? ""}:${error?.message ?? ""}`.toLowerCase();
  let id = "unavailable";
  if (text.includes("schema_unsupported") || text.includes("unsupported")) id = "unsupported-payload";
  else if (text.includes("operator_view_invalid") || text.includes("malformed") || text.includes("invalid_record")) id = "malformed-payload";
  else if (text.includes("timeout") || text.includes("timed out")) id = "timeout";
  else if (text.includes("incompatible")) id = "incompatible-version";
  else if (text.includes("unauthorized") || text.includes("denied")) id = "denied";
  return defensiveState(id, options);
}

export function defensiveStateIds() {
  return Object.keys(profiles).filter((id) => id !== "live" && id !== "unknown");
}

export function defensiveCatalogMarkup() {
  return defensiveStateIds().map((id) => {
    const profile = defensiveState(id, { snapshotAvailable: true, snapshotSource: "fixture" });
    return `<div class="state-surface" data-state="${profile.id}" data-role="${profile.role}" ${testIdAttribute("foundation", "defensive", profile.id)}><strong>${profile.label}</strong><small>${profile.description}</small></div>`;
  }).join("");
}

export function defensiveBannerMarkup(profile) {
  const source = profile.snapshotAvailable
    ? profile.snapshotSource === "cache"
      ? t("foundation.defensive.snapshot.cached")
      : profile.historical
        ? t("foundation.defensive.snapshot.last")
        : t("foundation.defensive.snapshot.current")
    : t("foundation.defensive.snapshot.none");
  const mutation = profile.mutationAllowed
    ? t("foundation.defensive.mutation.available")
    : t("foundation.defensive.mutation.unavailable");
  const reconnect = profile.reconnectAvailable
    ? `<button type="button" data-reconnect data-test-id="foundation-reconnect">${t("foundation.defensive.reconnect")}</button>`
    : "";
  return `<div class="defensive-copy"><strong>${profile.label}</strong><span>${profile.description}</span><small>${source} · ${mutation}</small></div>${reconnect}`;
}

export function cacheOperatorView(storage, operatorView, cachedAt = Date.now()) {
  if (!storage || typeof storage.setItem !== "function") return;
  if (!Number.isSafeInteger(cachedAt) || cachedAt < 0) return;
  storage.setItem(CACHED_OPERATOR_VIEW_KEY, JSON.stringify({
    schema: CACHE_SCHEMA,
    cachedAt,
    operatorView,
  }));
}

export function loadCachedOperatorView(storage) {
  if (!storage || typeof storage.getItem !== "function") return null;
  const raw = storage.getItem(CACHED_OPERATOR_VIEW_KEY);
  if (typeof raw !== "string" || raw.length === 0 || raw.length > 1024 * 1024) return null;
  try {
    const parsed = JSON.parse(raw);
    if (
      parsed?.schema !== CACHE_SCHEMA ||
      !Number.isSafeInteger(parsed.cachedAt) || parsed.cachedAt < 0 ||
      !parsed.operatorView || typeof parsed.operatorView !== "object" || Array.isArray(parsed.operatorView)
    ) return null;
    return Object.freeze({ cachedAt: parsed.cachedAt, operatorView: parsed.operatorView });
  } catch (_error) {
    return null;
  }
}
