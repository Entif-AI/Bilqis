import {
  currentResourceFixture,
  historicalResourceFixture,
} from "./resource-fixture.mjs";

export function referenceResourceState() {
  return Object.freeze({
    current: currentResourceFixture(),
    comparison: historicalResourceFixture(),
    comparisonState: "PRESENT",
  });
}

export const RESOURCE_FIXTURE_SUPPORT = Object.freeze({
  referenceState: referenceResourceState,
  historicalProfile: historicalResourceFixture,
});
