import {
  currentResourceFixture,
  historicalResourceFixture,
} from "./resource-fixture.mjs";

export { historicalResourceFixture };

export function referenceResourceState() {
  return Object.freeze({
    current: currentResourceFixture(),
    comparison: historicalResourceFixture(),
    comparisonState: "PRESENT",
  });
}
