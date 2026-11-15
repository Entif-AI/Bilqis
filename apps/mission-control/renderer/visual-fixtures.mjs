export const VISUAL_FIXTURES = Object.freeze({
  live: { mode: "LIVE", freshness: "FRESH", state: "healthy", labelKey: "foundation.fixture.live" },
  unknown: { mode: "LIVE", freshness: "UNKNOWN", state: "unknown", labelKey: "foundation.fixture.unknown" },
  historical: { mode: "HISTORICAL", freshness: "FRESH", state: "historical", labelKey: "foundation.fixture.historical" },
  stale: { mode: "LIVE", freshness: "STALE", state: "stale", labelKey: "foundation.fixture.stale" },
  denied: { mode: "LIVE", freshness: "FRESH", state: "denied", labelKey: "foundation.fixture.denied" },
  invalidEvidence: { mode: "LIVE", freshness: "FRESH", state: "invalid", labelKey: "foundation.fixture.invalidEvidence" },
});

export const VISUAL_REGRESSION_CASES = Object.freeze(
  ["dark", "light"].flatMap((theme) =>
    Object.keys(VISUAL_FIXTURES).map((fixture) => Object.freeze({ theme, fixture })),
  ),
);

export function visualFixtureNames() {
  return Object.keys(VISUAL_FIXTURES);
}
